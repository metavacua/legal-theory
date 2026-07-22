"""Convert a Markdown document to validated, XSLT-buildable DocBook 5.2 XML."""

import difflib
import re
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

DB_NS = "http://docbook.org/ns/docbook"
XI_NS = "http://www.w3.org/2001/XInclude"
XLINK_NS = "http://www.w3.org/1999/xlink"
XML_NS = "http://www.w3.org/XML/1998/namespace"
ET.register_namespace("", DB_NS)
ET.register_namespace("xi", XI_NS)
ET.register_namespace("xlink", XLINK_NS)


def slugify(text):
    text = text.strip().lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"\s+", "-", text)
    if not text:
        return "s"
    if re.match(r"^[0-9]", text):
        text = f"s-{text}"
    return text


def extract_title(md_path):
    with open(md_path, encoding="utf-8") as f:
        for line in f:
            m = re.match(r"^#{1,6}\s+(.*)", line)
            if m:
                return re.sub(r"[*_]", "", m.group(1)).strip()
    return Path(md_path).stem.replace("-", " ").replace("_", " ").title()


def _strip_trailing_whitespace(md_path):
    # Root cause of a real, live rendering defect (found converting
    # california-worker-misclassification-risk-analysis.md, confirmed
    # present in 223 lines across 35 corpus files): CommonMark treats a
    # line ending in 2+ trailing spaces, immediately followed by
    # another non-blank line, as a hard line break. These are copy-
    # paste artifacts in this corpus, not intentional formatting — but
    # pandoc honors them, and a hard break inside an otherwise-plain
    # paragraph makes its DocBook5 writer emit <literallayout> (a
    # preformatted, non-reflowable block) instead of <para>. html5.xsl
    # has no template for <literallayout>, so it fell through to bare,
    # unstyled text with no paragraph wrapping in the built HTML.
    # Stripping trailing whitespace before pandoc ever sees the content
    # removes the hard-break trigger at its source, rather than trying
    # to detect or work around <literallayout> after the fact.
    with open(md_path, encoding="utf-8") as f:
        text = f.read()
    return re.sub(r"[ \t]+$", "", text, flags=re.MULTILINE)


def pandoc_to_docbook_fragment(md_path):
    normalized = _strip_trailing_whitespace(md_path)
    result = subprocess.run(
        ["pandoc", "-f", "gfm", "-t", "docbook5"],
        input=normalized, capture_output=True, text=True, check=True,
    )
    return result.stdout


def wrap_fragment(fragment, xml_id, title, metadata_href):
    # Pandoc emits one or more top-level <section> elements with no
    # shared root, each carrying its own repeated xmlns declarations.
    # Strip the repeats and wrap everything in one parseable <root>.
    stripped = fragment.replace(f'xmlns="{DB_NS}" ', "").replace(
        f'xmlns:xlink="{XLINK_NS}" ', ""
    )
    wrapped = f'<root xmlns="{DB_NS}" xmlns:xlink="{XLINK_NS}">{stripped}</root>'
    root = ET.fromstring(wrapped)
    children = list(root)

    article = ET.Element(f"{{{DB_NS}}}article")
    article.set("version", "5.2")
    article.set(f"{{{XML_NS}}}id", xml_id)
    article.set(f"{{{XML_NS}}}lang", "en")

    xi_include = ET.SubElement(article, f"{{{XI_NS}}}include")
    xi_include.set("href", metadata_href)

    title_el = ET.SubElement(article, f"{{{DB_NS}}}title")
    title_el.text = title

    # A single top-level <section> whose own <title> just duplicates
    # the article title we already set: unwrap it so its children
    # become the article's direct children, matching the flatter
    # structure the hand-authored paper already uses. Multiple
    # top-level siblings have no single title to unwrap from, so they
    # stay as direct article children as-is.
    unwrapped = len(children) == 1 and children[0].tag == f"{{{DB_NS}}}section"
    if unwrapped:
        for child in list(children[0]):
            if child.tag != f"{{{DB_NS}}}title":
                article.append(child)
    else:
        for child in children:
            article.append(child)

    sanitize_xml_ids(article)
    return article, unwrapped


def sanitize_xml_ids(article):
    xml_id_attr = f"{{{XML_NS}}}id"
    for el in article.iter():
        value = el.get(xml_id_attr)
        if value and re.match(r"^[0-9]", value):
            el.set(xml_id_attr, f"s-{value}")


def split_into_fragments(article, out_dir, stem):
    sections = [c for c in article if c.tag == f"{{{DB_NS}}}section"]
    if not sections:
        return False

    # Remove metadata include if it exists (it will be managed separately for each fragment)
    for child in list(article):
        if child.tag == f"{{{XI_NS}}}include" and child.get("href", "").endswith(".meta.xml"):
            article.remove(child)
            break

    out_dir = Path(out_dir)
    frag_dir = out_dir / stem
    frag_dir.mkdir(parents=True, exist_ok=True)

    used_slugs = {}
    for i, section in enumerate(sections, start=1):
        title_el = section.find(f"{{{DB_NS}}}title")
        section_title = title_el.text if title_el is not None else ""
        base_slug = slugify(section_title)
        count = used_slugs.get(base_slug, 0)
        slug = base_slug if count == 0 else f"{base_slug}-{count}"
        used_slugs[base_slug] = count + 1

        frag_name = f"{i:02d}-{slug}.xml"
        frag_path = frag_dir / frag_name

        frag_tree = ET.ElementTree(section)
        ET.indent(frag_tree, space="  ")
        frag_tree.write(frag_path, encoding="unicode", xml_declaration=True)

        idx = list(article).index(section)
        xi_include = ET.Element(f"{{{XI_NS}}}include")
        xi_include.set("href", f"{stem}/{frag_name}")
        article.remove(section)
        article.insert(idx, xi_include)

    return True


def write_metadata(meta_path, title):
    meta_path = Path(meta_path)
    docs_dir = (REPO_ROOT / "docs").resolve()
    meta_dir = meta_path.resolve().parent
    shared_metadata_path = docs_dir / "common" / "shared-metadata.xml"

    try:
        depth = len(meta_dir.relative_to(docs_dir).parts)
        shared_href = "../" * depth + "common/shared-metadata.xml"
    except ValueError:
        # meta_dir is not under docs_dir (e.g., in a temp directory),
        # use absolute path for shared-metadata.xml
        shared_href = str(shared_metadata_path)

    escaped_title = xml_escape(title)
    content = f"""<?xml version="1.0" encoding="UTF-8"?>
<info xmlns="{DB_NS}" xmlns:dc="http://purl.org/dc/terms/" xmlns:xi="{XI_NS}">
  <dc:title>{escaped_title}</dc:title>
  <xi:include href="{shared_href}" />
</info>
"""
    meta_path.write_text(content, encoding="utf-8")


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCHEMA_PATH = REPO_ROOT / "docs" / "schema" / "docbook-corpus.rnc"
HTML5_XSL_PATH = REPO_ROOT / "docs" / "xsl" / "html5.xsl"


def validate(xml_path):
    errors = []
    wf = subprocess.run(
        ["xmllint", "--noout", "--xinclude", str(xml_path)],
        capture_output=True, text=True,
    )
    if wf.returncode != 0:
        errors.append(wf.stderr.strip())
        return errors  # schema validation is meaningless on malformed XML

    rng = subprocess.run(
        ["jing", "-c", str(SCHEMA_PATH), str(xml_path)],
        capture_output=True, text=True,
    )
    if rng.returncode != 0:
        errors.append(rng.stdout.strip() or rng.stderr.strip())
    return errors


def build_html(xml_path, out_path):
    result = subprocess.run(
        ["xsltproc", "--xinclude", str(HTML5_XSL_PATH), str(xml_path)],
        capture_output=True, text=True, check=True,
    )
    Path(out_path).write_text(result.stdout, encoding="utf-8")


def _is_ignorable_word_run(words):
    # A run of words dropped or added between the two sides is ignorable
    # only if every word in it has no alphanumeric content at all — pure
    # formatting glue (rule/border characters, punctuation) with no
    # semantic payload. Two verified, distinct causes have produced such
    # runs so far:
    #   - pandoc's DocBook5 writer drops Markdown horizontal rules
    #     (`---`) entirely; a surviving one in the plain-text writer's
    #     output is a run of dash characters with no internal
    #     whitespace, so it survives word tokenization as dash-only
    #     tokens.
    #   - a Markdown table's plain-text rendering differs completely
    #     depending on path: a column-aligned ASCII grid (dashes) direct
    #     from Markdown, vs. a pipe-delimited rendering (pipes/colons,
    #     from the `:-:` alignment row) after the DocBook round-trip
    #     through informaltable/entry — verified independently on a
    #     real 9-column table that every cell's actual word content is
    #     identical and in the same order on both sides; only the
    #     border/rule characters differ.
    # Deliberately a "no alphanumeric content" predicate rather than an
    # allowlist of the specific characters seen so far (-, |, :): the
    # next structural-rendering divergence pandoc introduces will use
    # different glyphs, and the underlying invariant — content-bearing
    # words never look like this — doesn't change. Tradeoff accepted:
    # an isolated dropped symbol-only token with real meaning (e.g. a
    # stray footnote marker or section symbol) would also be tolerated
    # here: this check's job is catching lost prose, not lost symbols.
    # Any word containing a letter or digit means genuine content
    # changed and must not be swallowed here.
    return all(w and not any(c.isalnum() for c in w) for w in words)


def _word_level_diff(orig_words, roundtrip_words):
    # Shared by content_preservation_diff() and its own test suite, so
    # a change to the ignore rule or the opcode-filtering logic can't
    # silently drift out of sync between production and test.
    matcher = difflib.SequenceMatcher(None, orig_words, roundtrip_words)
    changed = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        removed = orig_words[i1:i2]
        added = roundtrip_words[j1:j2]
        if _is_ignorable_word_run(removed) and _is_ignorable_word_run(added):
            continue
        if removed:
            changed.append("- " + " ".join(removed))
        if added:
            changed.append("+ " + " ".join(added))
    return changed


def content_preservation_diff(md_path, xml_path, title, unwrapped):
    # Normalize the same way pandoc_to_docbook_fragment() does, rather
    # than handing pandoc the raw file path — otherwise this "original"
    # side would still contain the accidental hard-break whitespace
    # _strip_trailing_whitespace() already removed before conversion,
    # comparing against content that was never actually converted.
    original = subprocess.run(
        ["pandoc", "-f", "gfm", "-t", "plain"],
        input=_strip_trailing_whitespace(md_path),
        capture_output=True, text=True, check=True,
    ).stdout

    resolved = subprocess.run(
        ["xmllint", "--xinclude", str(xml_path)],
        capture_output=True, text=True, check=True,
    ).stdout

    roundtrip = subprocess.run(
        ["pandoc", "-f", "docbook", "-t", "plain", "-"],
        input=resolved, capture_output=True, text=True, check=True,
    ).stdout

    if unwrapped:
        # The wrapping <section>'s title was discarded when its
        # children were promoted to the article; pandoc's docbook
        # reader never renders <article><title> as body text, so add
        # the title back for a fair comparison against the original.
        roundtrip = f"{title}\n\n{roundtrip}"

    # Word-level comparison, not line- or paragraph-level: verified on
    # real corpus documents that pandoc's plain-text writer both
    # rewraps long lines at a different column width AND regroups
    # adjacent list items into a different number of blank-line-
    # separated blocks after a DocBook round-trip (list-item nesting
    # context doesn't survive the round-trip) — same words throughout,
    # but neither line boundaries nor paragraph/block boundaries are
    # stable enough to diff on. Word sequences are unaffected by either.
    return _word_level_diff(original.split(), roundtrip.split())


import sys
from dataclasses import dataclass, field


@dataclass
class ConversionResult:
    xml_path: Path
    html_path: Path
    errors: list = field(default_factory=list)
    content_diff: list = field(default_factory=list)


def convert(md_path, out_dir):
    md_path = Path(md_path)
    out_dir = Path(out_dir)
    xml_id = slugify(md_path.stem)
    title = extract_title(md_path)
    meta_name = f"{md_path.stem}.meta.xml"
    xml_path = out_dir / f"{md_path.stem}.xml"
    html_path = out_dir / f"{md_path.stem}.html"

    fragment = pandoc_to_docbook_fragment(md_path)
    try:
        article, unwrapped = wrap_fragment(fragment, xml_id, title, meta_name)
    except ET.ParseError as e:
        # Root cause (petition-corporate-ai-registry-ca-sos.md): a
        # stray, unmatched HTML-like tag in the source (an artifact
        # from whatever generated the document) survives as raw-HTML
        # passthrough in pandoc's DocBook5 output, producing genuinely
        # malformed XML no amount of normalization on our side
        # controls for. Report it the way validate() reports any other
        # malformed input, rather than letting an uncaught exception
        # crash the whole conversion.
        return ConversionResult(
            xml_path=xml_path, html_path=html_path,
            errors=[f"malformed pandoc output, could not parse: {e}"],
        )

    write_metadata(out_dir / meta_name, title)

    tree = ET.ElementTree(article)
    ET.indent(tree, space="  ")
    tree.write(xml_path, encoding="unicode", xml_declaration=True)

    errors = validate(xml_path)

    content_diff = []
    if not errors:
        build_html(xml_path, html_path)
        content_diff = content_preservation_diff(md_path, xml_path, title, unwrapped)

    return ConversionResult(
        xml_path=xml_path, html_path=html_path,
        errors=errors, content_diff=content_diff,
    )


def main():
    if len(sys.argv) != 2:
        print("usage: convert_to_docbook.py <path/to/doc.md>", file=sys.stderr)
        return 2
    md_path = Path(sys.argv[1])
    if not md_path.is_file():
        print(f"error: no such file: {md_path}", file=sys.stderr)
        return 2
    out_dir = md_path.parent
    result = convert(md_path, out_dir)
    if result.errors:
        print(f"VALIDATION FAILED: {md_path}")
        for e in result.errors:
            print(f"  {e}")
        return 1
    if result.content_diff:
        print(f"CONTENT PRESERVATION CHECK FAILED: {md_path}")
        for line in result.content_diff:
            print(f"  {line}")
        return 1
    print(f"OK: {md_path} -> {result.xml_path}, {result.html_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

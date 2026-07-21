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
        lines = f.readlines()
    return "".join(line.rstrip(" \t") + ("\n" if line.endswith("\n") else "") for line in lines)


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


def write_metadata(meta_path, title):
    escaped_title = xml_escape(title)
    content = f"""<?xml version="1.0" encoding="UTF-8"?>
<info xmlns="{DB_NS}" xmlns:dc="http://purl.org/dc/terms/">
  <dc:title>{escaped_title}</dc:title>
  <dc:creator>Ian D.L.N. McLean</dc:creator>
  <dc:publisher>metavacua/legal-theory (GitHub)</dc:publisher>
  <dc:type>Article</dc:type>
  <dc:language>en</dc:language>
  <dc:rights>CC BY-SA 4.0</dc:rights>
  <authorgroup>
    <author>
      <personname>
        <firstname>Ian</firstname>
        <othername role="middle">D.L.N.</othername>
        <surname>McLean</surname>
      </personname>
      <email>metavacua@gmail.com</email>
    </author>
  </authorgroup>
  <legalnotice>
    <para>Copyright &#169; 2026 Ian D.L.N. McLean. Licensed under Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0). This document publishes general legal analysis and does not constitute legal advice.</para>
  </legalnotice>
</info>
"""
    Path(meta_path).write_text(content, encoding="utf-8")


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
    # only if every word in it is a pure-dash token — pandoc's DocBook5
    # writer drops Markdown horizontal rules (`---`) entirely, and its
    # plain-text writer renders a surviving one as a run of dash
    # characters with no internal whitespace, so it survives word
    # tokenization as one or more dash-only tokens. Any real word or
    # punctuation-bearing token in the run means genuine content
    # changed and must not be swallowed here.
    return all(set(w) <= {"-"} for w in words)


def content_preservation_diff(md_path, xml_path, title, unwrapped):
    original = subprocess.run(
        ["pandoc", "-f", "gfm", "-t", "plain", str(md_path)],
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
    orig_words = original.split()
    roundtrip_words = roundtrip.split()

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

    fragment = pandoc_to_docbook_fragment(md_path)
    article, unwrapped = wrap_fragment(fragment, xml_id, title, meta_name)

    write_metadata(out_dir / meta_name, title)

    xml_path = out_dir / f"{md_path.stem}.xml"
    tree = ET.ElementTree(article)
    ET.indent(tree, space="  ")
    tree.write(xml_path, encoding="unicode", xml_declaration=True)

    errors = validate(xml_path)

    html_path = out_dir / f"{md_path.stem}.html"
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

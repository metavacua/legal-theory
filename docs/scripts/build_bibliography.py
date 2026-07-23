"""Generate the consolidated repo-wide bibliography from every corpus
document's "works cited" section plus the flagship paper's
bibliography.bib. See
docs/superpowers/specs/2026-07-23-consolidated-bibliography-design.md."""

import re
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

sys.path.insert(0, str(Path(__file__).resolve().parent))
from convert_to_docbook import (  # noqa: E402
    DB_NS, XI_NS, XLINK_NS, XML_NS, DC_NS,
    REPO_ROOT, element_full_text, validate, build_html,
)


def parse_xincludes(xml_path):
    """Absolute Paths of every file directly xi:include'd by xml_path
    (not recursive)."""
    root = ET.parse(xml_path).getroot()
    hrefs = []
    for el in root.iter(f"{{{XI_NS}}}include"):
        href = el.get("href")
        if href:
            hrefs.append((xml_path.parent / href).resolve())
    return hrefs


def build_backlink_map(root_dir):
    """dict[Path, str]: every shell article (root element <article>) and
    every file it transitively xi:includes, mapped to the shell's
    repo-relative built .html path."""
    root_dir = Path(root_dir)
    shells = []
    for xml_path in sorted(root_dir.rglob("*.xml")):
        try:
            root_tag = ET.parse(xml_path).getroot().tag
        except ET.ParseError:
            continue
        if root_tag == f"{{{DB_NS}}}article":
            shells.append(xml_path)

    backlinks = {}
    for shell in shells:
        rel_html = shell.with_suffix(".html").resolve().relative_to(REPO_ROOT).as_posix()
        shell_resolved = shell.resolve()
        backlinks[shell_resolved] = rel_html
        stack = list(parse_xincludes(shell))
        seen = {shell_resolved}
        while stack:
            frag = stack.pop()
            if frag in seen or not frag.is_file():
                continue
            seen.add(frag)
            backlinks[frag] = rel_html
            stack.extend(parse_xincludes(frag))
    return backlinks


WORKS_CITED_ID = "works-cited"


def _para_title_text(para):
    """Full text of a <para>, excluding a nested <link>'s own inner text
    (which just repeats the URL) but keeping text before/after it."""
    parts = [para.text or ""]
    for child in para:
        if child.tag != f"{{{DB_NS}}}link":
            parts.append(element_full_text(child))
        parts.append(child.tail or "")
    return " ".join(" ".join(parts).split())


def _listitem_text_and_link(li):
    para = li.find(f"{{{DB_NS}}}para")
    if para is None:
        return "", None
    link_el = para.find(f"{{{DB_NS}}}link")
    href = link_el.get(f"{{{XLINK_NS}}}href") if link_el is not None else None
    return _para_title_text(para), href


def extract_works_cited(xml_path):
    """[(text, href), ...] for every works-cited listitem in xml_path."""
    root = ET.parse(xml_path).getroot()
    entries = []
    for section in root.iter(f"{{{DB_NS}}}section"):
        if section.get(f"{{{XML_NS}}}id") != WORKS_CITED_ID:
            continue
        for li in section.iter(f"{{{DB_NS}}}listitem"):
            text, href = _listitem_text_and_link(li)
            if text:
                entries.append((text, href))
    return entries


@dataclass
class RawEntry:
    text: str
    href: str | None
    citing_html: str       # repo-relative .html of the citing shell
    source_file: str       # repo-relative .xml the entry was extracted from (for the Appendix)


def extract_all_raw_entries(corpus_root, exclude_dirs):
    """[RawEntry, ...] for every works-cited listitem across corpus_root,
    skipping any file under a directory named in exclude_dirs."""
    corpus_root = Path(corpus_root)
    backlinks = build_backlink_map(corpus_root)
    entries = []
    for xml_path in sorted(corpus_root.rglob("*.xml")):
        if any(part in exclude_dirs for part in xml_path.relative_to(corpus_root).parts):
            continue
        html = backlinks.get(xml_path.resolve())
        if html is None:
            continue  # not part of any shell's xi:include graph
        source_file = xml_path.resolve().relative_to(REPO_ROOT).as_posix()
        for text, href in extract_works_cited(xml_path):
            entries.append(RawEntry(text=text, href=href, citing_html=html, source_file=source_file))
    return entries


def normalize_url(url):
    """Dedup key for a URL: lowercase scheme/host, strip trailing slash
    from the path. Path case and "www." prefix are preserved as-is since
    they can be semantically significant (case-sensitive paths, or
    www vs. bare host being genuinely different sites)."""
    parts = urlsplit(url.strip())
    scheme = parts.scheme.lower()
    netloc = parts.netloc.lower()
    path = parts.path.rstrip("/")
    return urlunsplit((scheme, netloc, path, parts.query, parts.fragment))


ACCESSED_RE = re.compile(
    r",?\s*(?<![\w-])accessed\s+([A-Za-z]+\s+\d{1,2},\s*\d{4}),?", re.IGNORECASE
)


def extract_access_date(text):
    """The 'Month D, YYYY' access date embedded in an "accessed ..." clause,
    or None if text has no such clause."""
    m = ACCESSED_RE.search(text)
    return m.group(1) if m else None


def strip_access_date(text):
    """text with any "accessed ..." clause removed and surrounding
    punctuation/whitespace trimmed."""
    return " ".join(ACCESSED_RE.sub(" ", text).split())


CODE_ABBREVIATIONS = {
    "corporations code": "Cal. Corp. Code",
    "corp. code": "Cal. Corp. Code",
    "civil code": "Cal. Civ. Code",
    "civ. code": "Cal. Civ. Code",
    "penal code": "Cal. Penal Code",
    "business and professions code": "Cal. Bus. & Prof. Code",
    "revenue and taxation code": "Cal. Rev. & Tax. Code",
    "government code": "Cal. Gov't Code",
    "family code": "Cal. Fam. Code",
    "food and agricultural code": "Cal. Food & Agric. Code",
    "public utilities code": "Cal. Pub. Util. Code",
    "code of civil procedure": "Cal. Civ. Proc. Code",
    "streets and highways code": "Cal. Sts. & High. Code",
    "labor code": "Cal. Lab. Code",
}
_STATUTE_RE = re.compile(
    r"(?P<code>" + "|".join(re.escape(k) for k in CODE_ABBREVIATIONS) + r")\s*§\s*(?P<section>[\d.]+)",
    re.IGNORECASE,
)
_USC_RE = re.compile(r"(?P<title>\d+)\s*U\.S\.C\.\s*§+\s*(?P<section>[\w.-]+(?:,\s*[\w.-]+)*)")
_YEAR_RE = re.compile(r"\((\d{4})\)")


def classify_statute(text):
    """dict(type='statute', abbrev, section, year) if text names a known
    statute (a code in CODE_ABBREVIATIONS or a U.S.C. title) with a
    section symbol, else None. Never guesses at unrecognized
    abbreviations."""
    m = _STATUTE_RE.search(text)
    if m:
        abbrev = CODE_ABBREVIATIONS[m.group("code").lower()]
        section = m.group("section")
    else:
        m = _USC_RE.search(text)
        if not m:
            return None
        abbrev = f"{m.group('title')} U.S.C."
        section = m.group("section")
    year_m = _YEAR_RE.search(text)
    return {"type": "statute", "abbrev": abbrev, "section": section, "year": year_m.group(1) if year_m else None}


def format_statute_bluebook(parsed):
    """Bluebook-style citation string for a classify_statute() result."""
    year = parsed["year"] or "[year unknown]"
    mark = "§§" if "," in parsed["section"] else "§"
    return f"{parsed['abbrev']} {mark} {parsed['section']} ({year})."


CASE_LAW_DOMAINS = {"courtlistener.com", "casetext.com", "casemine.com", "law.justia.com", "scholar.google.com"}
_CASE_RE = re.compile(
    r"(?P<plaintiff>[A-Z][\w.,'&-]*(?:\s+[A-Z][\w.,'&-]*){0,6})\s+v\.\s+"
    r"(?P<defendant>[A-Z][\w.,'&-]*(?:\s+[A-Z][\w.,'&-]*){0,6})"
)
_REPORTER_ABBREVS = ["Cal. 3d", "Cal.3d", "F.2d", "F. 2d", "F.3d", "F. 3d", "U.S.", "P.2d", "P. 2d"]
_REPORTER_RE = re.compile(
    r"\((?P<year>\d{4})\)\s*(?P<volume>\d+)\s+(?P<reporter>"
    + "|".join(re.escape(r) for r in _REPORTER_ABBREVS)
    + r")\.?\s*(?P<page>\d+)"
)


def _looks_like_case_domain(href):
    if not href:
        return False
    host = urlsplit(href).netloc.lower()
    return any(host == d or host.endswith("." + d) for d in CASE_LAW_DOMAINS)


def classify_case(text, href):
    """dict(type='case', name, complete, ...) if text contains a " v. "
    case-name pattern AND that pattern is corroborated by either a full
    reporter citation in the same text or a known case-law-aggregator
    URL, else None. A bare " v. " match with neither signal is NOT
    classified as a case (avoids false positives on essay titles like
    "Privacy v. Transparency in Legal Practice")."""
    m = _CASE_RE.search(text)
    if not m:
        return None
    name = f"{m.group('plaintiff').strip(' ,;')} v. {m.group('defendant').strip(' ,;')}"
    tail = text[m.end():].lstrip(" ,.")
    rep_m = _REPORTER_RE.match(tail)
    if rep_m:
        return {
            "type": "case", "name": name, "complete": True,
            "year": rep_m.group("year"), "volume": rep_m.group("volume"),
            "reporter": rep_m.group("reporter"), "page": rep_m.group("page"),
        }
    if _looks_like_case_domain(href):
        return {"type": "case", "name": name, "complete": False}
    return None


def format_case_bluebook(parsed):
    """Bluebook-style citation string for a classify_case() result. Falls
    back to a "[reporter citation unknown]" marker when the case data is
    only partial (name corroborated by domain but no reporter found)."""
    if parsed["complete"]:
        return f"{parsed['name']}, {parsed['volume']} {parsed['reporter']} {parsed['page']} ({parsed['year']})."
    return f"{parsed['name']}, [reporter citation unknown]."


KNOWN_PUBLISHERS = {
    "justia.com": "Justia", "law.justia.com": "Justia",
    "findlaw.com": "FindLaw", "codes.findlaw.com": "FindLaw",
    "casetext.com": "Casetext", "casemine.com": "CaseMine",
    "courtlistener.com": "CourtListener", "en.wikipedia.org": "Wikipedia",
    "law.cornell.edu": "Cornell Legal Information Institute",
}


def _guess_publisher(href):
    if not href:
        return None
    host = urlsplit(href).netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    return KNOWN_PUBLISHERS.get(host, host)


def format_secondary_chicago(text, href):
    publisher = _guess_publisher(href) or "[author unknown]"
    access_date = extract_access_date(text)
    title = (strip_access_date(text) or "[title unknown]").rstrip(".")
    date_str = f"Accessed {access_date}." if access_date else "[access date unknown]."
    url_str = href if href else "[no url]"
    return f'{publisher}. "{title}." {date_str} {url_str}'


def classify_and_format(raw):
    """(section, display_text) for a RawEntry, where section is one of
    "legal", "secondary", "appendix". Thin dispatcher over the Task 6-8
    classifiers/formatters: statute, then case, then a generic link
    (secondary), else appendix (no link and no recognized pattern)."""
    statute = classify_statute(raw.text)
    if statute:
        return "legal", format_statute_bluebook(statute)

    case = classify_case(raw.text, raw.href)
    if case:
        return "legal", format_case_bluebook(case)

    if raw.href:
        return "secondary", format_secondary_chicago(raw.text, raw.href)

    return "appendix", raw.text


_BIB_ENTRY_START_RE = re.compile(r"@(?P<type>\w+)\{(?P<key>[^,\s]+),")
_BIB_FIELD_NAME_RE = re.compile(r"(?P<name>\w+)\s*=\s*\{")


def _read_balanced(text, start):
    """text[start] must be '{'. Returns (contents without outer braces,
    index just after the matching closing brace), correctly handling
    arbitrarily nested {..} inside."""
    assert text[start] == "{"
    depth = 0
    i = start
    while i < len(text):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[start + 1:i], i + 1
        i += 1
    raise ValueError(f"unbalanced braces in BibTeX starting at index {start}")


def _strip_inner_braces(value):
    return re.sub(r"[{}]", "", value)


def parse_bibtex(path):
    """[{"key": str, "entry_type": str, "fields": dict[str, str]}, ...]
    for every @type{key, ...} entry in a BibTeX file. Field values are
    extracted with a manual balanced-brace scan (not a pure regex) since
    nested braces like {{LARQL} --- {Lazarus Query Language}} defeat a
    naive non-greedy regex, which stops at the first closing brace."""
    text = Path(path).read_text(encoding="utf-8")
    entries = []
    for m in _BIB_ENTRY_START_RE.finditer(text):
        open_brace_idx = text.index("{", m.start())
        _, end_idx = _read_balanced(text, open_brace_idx)
        body = text[m.end():end_idx - 1]

        fields = {}
        for fm in _BIB_FIELD_NAME_RE.finditer(body):
            value_raw, _ = _read_balanced(body, fm.end() - 1)
            value = " ".join(_strip_inner_braces(value_raw).split())
            if value:
                fields[fm.group("name").lower()] = value

        entries.append({
            "key": m.group("key").strip(),
            "entry_type": m.group("type").lower(),
            "fields": fields,
        })
    return entries


LEGAL_BIB_KEYS = frozenset({
    "gema_openai2025", "garcia_characterai2025", "bartz_anthropic2025",
    "kadrey_meta2025", "litchfield1984", "copyright1976fixation",
    "gdpr2016", "ccpa2018", "eu_database_directive1996", "eu_pld2024",
})
SELF_CITATION_HTML = {
    "mclean2025categorical": "docs/court-record/theory/federal-constitutional/extensions/llms-as-categorical-systems.html",
    "mclean2025encoding": "docs/court-record/matters/platform-tos-constitutional-limits/evidence/llm-information-encoding-and-covert-channels.html",
    "mclean2025agpl": "docs/court-record/theory/federal-statutes/extensions/agpl-ai-training-and-code-licensing.html",
}


def _format_bib_legal(entry):
    f = entry["fields"]
    title = f.get("title", "[title unknown]")
    title = title.replace("\\S\\S", "§§").replace("\\S", "§")
    if all(k in f for k in ("volume", "journal", "pages")):
        year = f.get("year", "[year unknown]")
        return f"{title}, {f['volume']} {f['journal']} {f['pages']} ({year})."
    if "section" in f or "§" in title:
        return f"{title} ({f.get('year', '[year unknown]')})."
    return f"{title}, [reporter citation unknown] ({f.get('year', '[year unknown]')})."


def _format_bib_academic(entry):
    f = entry["fields"]
    author = f.get("author") or "[author unknown]"
    year = f.get("year", "[year unknown]")
    title = f.get("title", "[title unknown]")
    venue = f.get("booktitle") or f.get("journal") or f.get("institution") or f.get("howpublished")
    url = f.get("url")
    if entry["key"] in SELF_CITATION_HTML:
        url = SELF_CITATION_HTML[entry["key"]]
    tail = f" {venue}." if venue else ""
    url_str = f" {url}" if url else ""
    return f'{author}. {year}. "{title}."{tail}{url_str}'


def classify_bib_entry(entry):
    """(section, display_text) for a parse_bibtex() entry dict. section
    is "legal" for anything in LEGAL_BIB_KEYS (Bluebook-ish citation,
    falling back to "[reporter citation unknown]" rather than omitting
    or guessing when volume/journal/pages are absent), else "secondary"
    (Chicago-author-date-ish citation, substituting a repo-relative
    built .html for self-citations in SELF_CITATION_HTML)."""
    if entry["key"] in LEGAL_BIB_KEYS:
        return "legal", _format_bib_legal(entry)
    return "secondary", _format_bib_academic(entry)


@dataclass
class BibliographyEntry:
    section: str
    display: str
    citing_htmls: list
    dedup_key: str


def _dedup_key(display_text, href):
    if href:
        return "url:" + normalize_url(href)
    return "text:" + " ".join(display_text.lower().split())


def dedupe(classified):
    """[BibliographyEntry, ...] merging (section, display_text, raw_entry)
    triples that share a dedup key (normalized URL if present, else
    normalized display text), unioning citing_htmls and keeping the
    first-seen display text/section, in file-walk order."""
    by_key = {}
    order = []
    for section, display, raw in classified:
        key = _dedup_key(display, raw.href)
        if key not in by_key:
            by_key[key] = BibliographyEntry(section=section, display=display, citing_htmls=[], dedup_key=key)
            order.append(key)
        entry = by_key[key]
        if raw.citing_html not in entry.citing_htmls:
            entry.citing_htmls.append(raw.citing_html)
    return [by_key[k] for k in order]


def verify_invariants(raw_entries, appendix_entries, legal_entries, secondary_entries, repo_root):
    """[violation message, ...] — empty means all self-check invariants
    hold. "No entry lost" is checked by re-deriving each raw entry's
    expected classification via classify_and_format and confirming it is
    actually present in the output, rather than comparing raw/output
    counts: dedupe() legitimately collapses multiple raw entries from the
    same citing document into one citing_htmls slot, and legal_entries /
    secondary_entries also contain bibliography.bib-derived entries with
    no corresponding raw_entries at all, so a naive count could look
    right while a real entry silently vanished, or look wrong while
    nothing was actually lost."""
    violations = []

    appendix_set = set(appendix_entries)
    output_keys = {e.dedup_key for e in legal_entries + secondary_entries}
    for raw in raw_entries:
        section, display = classify_and_format(raw)
        if section == "appendix":
            if display not in appendix_set:
                violations.append(f"raw entry lost (missing from appendix): {raw.text!r}")
        elif _dedup_key(display, raw.href) not in output_keys:
            violations.append(f"raw entry lost (missing from {section}): {raw.text!r}")

    for e in legal_entries:
        if not any(marker in e.display for marker in ("§", " v. ", "Directive", "Regulation")):
            violations.append(f"legal entry missing § or v. marker: {e.display!r}")

    seen_urls = {}
    for e in legal_entries + secondary_entries:
        for token in re.findall(r"https?://\S+", e.display):
            key = normalize_url(token.rstrip(".\"'"))
            if key in seen_urls and seen_urls[key] != e.display:
                violations.append(f"duplicate normalized URL survived dedup: {key}")
            seen_urls[key] = e.display

    for e in legal_entries + secondary_entries:
        for html in e.citing_htmls:
            if not (Path(repo_root) / html).is_file():
                violations.append(f"dangling backlink, file does not exist: {html}")

    return violations


from xml.sax.saxutils import escape as xml_escape


def relative_html_link(repo_relative_html):
    assert repo_relative_html.startswith("docs/"), repo_relative_html
    return "../" + repo_relative_html[len("docs/"):]


def _entry_listitem_xml(entry):
    links = "; ".join(
        f'<link xlink:href="{xml_escape(relative_html_link(h))}">{xml_escape(h)}</link>'
        for h in sorted(entry.citing_htmls)
    )
    return (
        "    <listitem>\n"
        f"      <para>{xml_escape(entry.display)}</para>\n"
        f"      <para>Cited in: {links}</para>\n"
        "    </listitem>\n"
    )


def _section_xml(title, xml_id, entries):
    items = "".join(_entry_listitem_xml(e) for e in sorted(entries, key=lambda e: e.display.lower()))
    return (
        f'  <section xml:id="{xml_id}">\n'
        f"    <title>{xml_escape(title)}</title>\n"
        '    <orderedlist numeration="arabic" spacing="compact">\n'
        f"{items}"
        "    </orderedlist>\n"
        "  </section>\n"
    )


METHODOLOGY_PARA = (
    "Primary legal sources (cases, statutes, regulations) are cited in Bluebook (21st ed.) "
    "format. All other sources -- academic, technical, and secondary -- are cited in Chicago "
    "Author-Date (17th ed.) format. A field not verifiable from the source corpus is marked "
    "[unknown] rather than inferred. Generated by docs/scripts/build_bibliography.py from "
    "every corpus document's works-cited section plus the flagship paper's bibliography.bib; "
    "see docs/superpowers/specs/2026-07-23-consolidated-bibliography-design.md."
)


def emit_docbook(legal_entries, secondary_entries, appendix_texts):
    appendix_items = "".join(
        f"    <listitem>\n      <para>{xml_escape(t)}</para>\n    </listitem>\n"
        for t in appendix_texts
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<article xmlns="http://docbook.org/ns/docbook" '
        'xmlns:xlink="http://www.w3.org/1999/xlink" '
        'xmlns:xi="http://www.w3.org/2001/XInclude" '
        'version="5.2" xml:id="references" xml:lang="en">\n'
        '  <xi:include href="references.meta.xml"/>\n'
        "  <title>Consolidated References &amp; Bibliography</title>\n"
        '  <section xml:id="methodology">\n'
        "    <title>Scope and Citation Policy</title>\n"
        f"    <para>{xml_escape(METHODOLOGY_PARA)}</para>\n"
        "  </section>\n"
        + _section_xml("Legal Citations", "legal-citations", legal_entries)
        + _section_xml("Academic and Secondary Sources", "academic-secondary-sources", secondary_entries)
        + '  <section xml:id="appendix-needs-review">\n'
        "    <title>Appendix: Entries Needing Manual Review</title>\n"
        '    <orderedlist numeration="arabic" spacing="compact">\n'
        f"{appendix_items}"
        "    </orderedlist>\n"
        "  </section>\n"
        "</article>\n"
    )


def write_meta_xml(path):
    Path(path).write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<info xmlns="http://docbook.org/ns/docbook" xmlns:dc="http://purl.org/dc/terms/" xmlns:xi="http://www.w3.org/2001/XInclude">\n'
        "  <dc:title>Consolidated References &amp; Bibliography</dc:title>\n"
        '  <xi:include href="../common/shared-metadata.xml" />\n'
        "</info>\n",
        encoding="utf-8",
    )


PAPER_ROOT = REPO_ROOT / "docs" / "papers" / "ai_and_ip" / "llm-database-theory"
PAPER_SRC = PAPER_ROOT / "src"
PAPER_FALLBACK_HTML = "docs/papers/ai_and_ip/llm-database-theory/html/01-llm-database-theory.html"
_CITATION_KEY_RE = re.compile(r"<citation>([\w.-]+)</citation>")


def _bib_citation_backlinks():
    """dict[str, str]: bibliography.bib key -> repo-relative .html of the
    paper article (html/01-llm-database-theory.html or
    html/02-legal-corpus-connections.html) whose src/ fragments actually
    contain <citation>KEY</citation>. Reuses build_backlink_map(PAPER_SRC)
    only to determine which shell (by filename stem) each fragment
    belongs to -- the paper's real built HTML lives in a sibling html/
    directory, not alongside src/, so the shell-html path
    build_backlink_map computes is used only for its stem, not taken
    literally."""
    src_backlinks = build_backlink_map(PAPER_SRC)
    key_to_html = {}
    for xml_path in sorted(PAPER_SRC.rglob("*.xml")):
        shell_html_guess = src_backlinks.get(xml_path.resolve())
        if shell_html_guess is None:
            continue
        stem = Path(shell_html_guess).stem
        real_html = f"docs/papers/ai_and_ip/llm-database-theory/html/{stem}.html"
        for key in _CITATION_KEY_RE.findall(xml_path.read_text(encoding="utf-8")):
            key_to_html.setdefault(key, real_html)
    return key_to_html


def main(argv=None):
    out_dir = REPO_ROOT / "docs" / "bibliography"
    out_dir.mkdir(exist_ok=True)

    raw_entries = extract_all_raw_entries(REPO_ROOT / "docs", exclude_dirs={"papers", "scripts", "scratch", "bibliography"})
    bib_entries = parse_bibtex(PAPER_SRC / "bibliography.bib")
    bib_citation_backlinks = _bib_citation_backlinks()

    classified = [(*classify_and_format(r), r) for r in raw_entries]
    appendix_texts = [display for section, display, r in classified if section == "appendix"]

    bib_classified = []
    for entry in bib_entries:
        section, display = classify_bib_entry(entry)
        # Self-citations resolve to the actual corpus document they cite, not
        # the paper itself; everything else resolves to whichever paper
        # article fragment actually uses <citation>KEY</citation>, found via
        # the real <citation> usage sites (see the design spec's survey).
        html = (
            SELF_CITATION_HTML.get(entry["key"])
            or bib_citation_backlinks.get(entry["key"], PAPER_FALLBACK_HTML)
        )
        raw = RawEntry(text=entry["key"], href=entry["fields"].get("url"), citing_html=html, source_file="docs/papers/ai_and_ip/llm-database-theory/src/bibliography.bib")
        bib_classified.append((section, display, raw))

    legal = dedupe([c for c in classified + bib_classified if c[0] == "legal"])
    secondary = dedupe([c for c in classified + bib_classified if c[0] == "secondary"])

    violations = verify_invariants(raw_entries, appendix_texts, legal, secondary, REPO_ROOT)
    if violations:
        print("INVARIANT VIOLATIONS -- refusing to write output:", file=sys.stderr)
        for v in violations:
            print(f"  {v}", file=sys.stderr)
        return 1

    xml_path = out_dir / "references.xml"
    meta_path = out_dir / "references.meta.xml"
    xml_path.write_text(emit_docbook(legal, secondary, appendix_texts), encoding="utf-8")
    write_meta_xml(meta_path)

    errors = validate(xml_path)
    if errors:
        print("VALIDATION FAILED:", file=sys.stderr)
        for e in errors:
            print(f"  {e}", file=sys.stderr)
        return 1
    build_html(xml_path, xml_path.with_suffix(".html"))

    print(f"OK: {len(legal)} legal, {len(secondary)} secondary, {len(appendix_texts)} appendix entries")
    return 0


if __name__ == "__main__":
    sys.exit(main())

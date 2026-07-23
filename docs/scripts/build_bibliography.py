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
    name = f"{m.group('plaintiff').strip()} v. {m.group('defendant').strip()}"
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

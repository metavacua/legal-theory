"""Generate the consolidated repo-wide bibliography from every corpus
document's "works cited" section plus the flagship paper's
bibliography.bib. See
docs/superpowers/specs/2026-07-23-consolidated-bibliography-design.md."""

import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

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

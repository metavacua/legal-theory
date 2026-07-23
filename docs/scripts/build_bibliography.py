"""Generate the consolidated repo-wide bibliography from every corpus
document's "works cited" section plus the flagship paper's
bibliography.bib. See
docs/superpowers/specs/2026-07-23-consolidated-bibliography-design.md."""

import sys
import xml.etree.ElementTree as ET
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

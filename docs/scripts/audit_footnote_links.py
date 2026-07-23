"""Read-only audit of the corpus's orphaned footnote-number markers
against their candidate works-cited entries. Writes a report; never
modifies a corpus document. See
docs/superpowers/specs/2026-07-23-footnote-citation-audit-design.md."""

import re
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_bibliography import (  # noqa: E402
    DB_NS, XI_NS, XLINK_NS, XML_NS,
    REPO_ROOT, parse_xincludes, build_backlink_map, extract_works_cited,
)


def document_content_files(shell_path):
    """shell_path plus every file it transitively xi:includes, in
    document order (the order xi:include elements appear in the
    source, resolved recursively)."""
    shell_path = Path(shell_path)
    ordered = [shell_path]
    for frag in parse_xincludes(shell_path):
        if frag.is_file():
            ordered.extend(document_content_files(frag))
    return ordered


# A glued footnote marker is a "." immediately followed by 1-3 digits and
# then whitespace/end-of-text (e.g. "...Superior Court.4 follows"). The
# same shape is produced by three other things: (1) a decimal section
# title like "2.1 A Section Title", (2) a statute pincite like
# "Family Code § 6751.1", and (3) a Rule/Section/Article sub-numbering
# like "Rule 2.3". Titles are excluded structurally (see
# _element_body_text below). Pincites and rule labels are excluded by a
# single structural rule: in both, the "." sits between two digit runs
# (the section/rule number and its decimal sub-part) -- i.e. the
# character immediately before the "." is itself a digit. A real
# footnote marker's "." always follows a word, punctuation mark, or
# closing tag boundary, never another digit, so this generalizes to any
# statute abbreviation or rule-label wording, not just the ones named in
# CODE_ABBREVIATIONS or the fixed Rule/Section/Article word list. (See
# _is_excluded_context below for why a keyword-based fallback on top of
# this rule was tried and removed.)
_FOOTNOTE_MARKER_RE = re.compile(r"\.(\d{1,3})(?=[\s]|$)")


@dataclass
class Candidate:
    number: int
    context: str        # up to ~80 chars of body text immediately around the marker
    heading_collision: bool = False


def _is_excluded_context(preceding_text):
    """True if the text immediately before a candidate marker signals a
    statute pincite, a decimal Rule/Section/Article label, or any other
    decimal number rather than a real footnote.

    The decisive, general signal is structural: if the character right
    before the marker's "." is itself a digit, the "." is splitting a
    decimal number (e.g. "6751.1", "2.3"), not terminating a sentence a
    footnote is glued to. This alone covers pincites and rule labels
    regardless of the specific code name or label word used, and does
    not depend on the word immediately preceding the marker -- a bare
    keyword lookback (e.g. "Rule"/"Section"/"Article" or a code-name
    abbreviation with no digit between it and the marker) was tried and
    removed: it fired on ordinary prose uses of those words (e.g. "the
    Common Rule.44", a named federal regulation, not a numbering label)
    and silently dropped real footnotes, with no confirmed corpus
    instance it uniquely caught beyond what this digit-adjacency rule
    already handles.
    """
    return bool(preceding_text and preceding_text[-1].isdigit())


def _element_body_text(el):
    """Full text of el, EXCLUDING any nested <title> descendant's text
    -- titles are never footnote candidates, checked structurally."""
    parts = [el.text or ""]
    for child in el:
        if child.tag == f"{{{DB_NS}}}title":
            parts.append(child.tail or "")
            continue
        parts.append(_element_body_text(child))
        parts.append(child.tail or "")
    return "".join(parts)


def find_candidates(xml_path):
    """Every glued footnote-shaped digit run in xml_path's body content
    (never inside <title>), excluding statute pincites and
    Rule/Section/Article labels, in document order."""
    import xml.etree.ElementTree as ET
    root = ET.parse(xml_path).getroot()
    text = _element_body_text(root)
    candidates = []
    for m in _FOOTNOTE_MARKER_RE.finditer(text):
        preceding = text[:m.start()]
        if _is_excluded_context(preceding):
            continue
        number = int(m.group(1))
        start = max(0, m.start() - 60)
        end = min(len(text), m.end() + 20)
        context = " ".join(text[start:end].split())
        candidates.append(Candidate(number=number, context=context))
    return candidates


def locate_works_cited(content_files):
    """The works-cited (text, href) entries, in order, from whichever
    content file in content_files has them -- empty list if none."""
    for f in content_files:
        entries = extract_works_cited(f)
        if entries:
            return entries
    return []


def is_degenerate(entries, max_footnote):
    """True if entries has no real (linked) entries at all, or is
    implausibly short relative to max_footnote -- fewer than half the
    entries needed to cover the highest footnote number referencing it."""
    if max_footnote == 0:
        return False
    linked = [e for e in entries if e[1]]
    if not linked:
        return True
    return len(entries) < max(1, max_footnote // 2)

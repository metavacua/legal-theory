"""Read-only audit of the corpus's orphaned footnote-number markers
against their candidate works-cited entries. Writes a report; never
modifies a corpus document. See
docs/superpowers/specs/2026-07-23-footnote-citation-audit-design.md."""

import argparse
import csv
import html.parser
import re
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_bibliography import (  # noqa: E402,F401
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


class _HeadingTextCollector(html.parser.HTMLParser):
    """Splits an HTML document's text into heading_text (everything
    inside an <h1>-<h6> element) and body_text (everything else),
    for is_inside_heading's second, HTML-side signal.

    Deviation from the Task 4 brief's literal sample code: the brief's
    version has no notion of <script>/<style> content and feeds every
    handle_data() call -- including raw CSS/JS -- into body_text. Every
    built HTML file sampled from the corpus (docs/cross-cutting and
    docs/court-record/matters) embeds an inline <style> block, and that
    CSS routinely contains decimal-looking substrings (e.g.
    "padding: 1.1rem;"). Confirmed on
    docs/cross-cutting/valuing-human-life-economically.html: the CSS
    rule "padding: 1.1rem 1.3rem;" makes "1.1" a false hit in body_text,
    even though "1.1" is also the real heading number for section 1.1
    ("<h3><em>1.1 The Value of a Statistical Life ...</em></h3>") --
    the brief's is_inside_heading(path, "1.1") returns False
    (in_heading=True but in_body=True too, so `in_heading and not
    in_body` fails) on real data, exactly backwards. This is a
    corpus-wide defect, not a one-off: every sampled file has a <style>
    block. Fixed here by tracking a skip_depth for <script>/<style> and
    dropping their handle_data() entirely (added to neither list),
    rather than special-casing CSS unit suffixes or the specific "rem"
    string, since script/script-like content is never real prose in
    this pipeline's inputs.
    """

    _HEADING_TAGS = ("h1", "h2", "h3", "h4", "h5", "h6")
    _SKIP_TAGS = ("script", "style")

    def __init__(self):
        super().__init__()
        self.heading_depth = 0
        self.skip_depth = 0
        self.heading_text = []
        self.body_text = []

    def handle_starttag(self, tag, attrs):
        if tag in self._HEADING_TAGS:
            self.heading_depth += 1
        elif tag in self._SKIP_TAGS:
            self.skip_depth += 1

    def handle_endtag(self, tag):
        if tag in self._HEADING_TAGS:
            self.heading_depth = max(0, self.heading_depth - 1)
        elif tag in self._SKIP_TAGS:
            self.skip_depth = max(0, self.skip_depth - 1)

    def handle_data(self, data):
        if self.skip_depth > 0:
            return
        (self.heading_text if self.heading_depth > 0 else self.body_text).append(data)


def is_inside_heading(html_path, marker_text):
    """True if marker_text appears only inside an <h1>-<h6> element in
    the built HTML at html_path, False if it appears in body text (or
    both, or neither) -- a second, independently-derived signal that a
    candidate is real body content rather than a section-heading number
    the XML-side <title> exclusion should already have caught."""
    parser = _HeadingTextCollector()
    parser.feed(Path(html_path).read_text(encoding="utf-8"))
    in_heading = marker_text in "".join(parser.heading_text)
    in_body = marker_text in "".join(parser.body_text)
    return in_heading and not in_body


def _marker_collides_with_heading(html_path, marker_text):
    """True if marker_text appears anywhere inside an <h1>-<h6> element
    in the built HTML at html_path, regardless of whether it ALSO
    appears in body text.

    Deviation from the Task 5 brief's literal Step 4 sample, which
    reuses is_inside_heading (Task 4) directly as this flag's
    condition. is_inside_heading requires marker_text to appear
    EXCLUSIVELY in a heading ("in_heading and not in_body") -- correct
    for its own purpose (a safety-net check that a "candidate" is
    actually nothing but a heading number that slipped past the
    XML-side <title> exclusion). But every genuine footnote candidate
    reaching this function was found by find_candidates() IN body XML
    content, so its rendered HTML representation will essentially
    always also appear in the HTML body -- meaning is_inside_heading's
    "not in_body" condition can structurally never be satisfied for a
    real candidate that also happens to collide with an unrelated
    heading elsewhere. Confirmed directly:
    is_inside_heading(full_doc_collision/shell.html, ".9") returns
    False even though ".9" plainly appears in the fixture's <h2>,
    because the same real footnote's ".9" also appears in the <p> body
    -- which is exactly the adversarial scenario the brief's own
    full_doc_collision fixture and test_heading_collision_is_flagged_
    not_dropped test are designed to exercise. Reusing is_inside_heading
    literally therefore makes Candidate.heading_collision permanently
    dead code: it could never fire on any real candidate, silently
    defeating the very fix (flag-not-drop) this task exists to
    implement. Fixed by adding this separate, deliberately looser
    "appears anywhere in a heading" signal -- reusing the existing
    _HeadingTextCollector rather than duplicating its HTML-parsing
    logic -- and using it (not is_inside_heading) as the
    heading_collision trigger in audit_document. is_inside_heading
    itself is left untouched; Task 4's own tests still exercise its
    original, stricter semantics unchanged."""
    parser = _HeadingTextCollector()
    parser.feed(Path(html_path).read_text(encoding="utf-8"))
    return marker_text in "".join(parser.heading_text)


@dataclass
class DocumentAudit:
    shell_html: str                 # repo-relative .html of the shell
    candidates: list                # list[Candidate], in document order, across all content files
    works_cited: list               # list[tuple[str, str | None]]
    degenerate: bool


def audit_document(shell_path, backlinks):
    """Walk the whole document rooted at shell_path (Task 1), collect
    candidates from every content file (Task 2), cross-check each
    against the shell's own built HTML and FLAG -- never drop -- any
    candidate whose marker text also appears in a heading there via
    Candidate.heading_collision (see _marker_collides_with_heading for
    why this is not literally is_inside_heading), locate works-cited
    (Task 3), and compute degeneracy (Task 3)."""
    shell_path = Path(shell_path)
    shell_html = backlinks.get(shell_path.resolve())
    html_path = REPO_ROOT / shell_html if shell_html else None

    content_files = document_content_files(shell_path)
    candidates = []
    for f in content_files:
        for c in find_candidates(f):
            marker_text = f".{c.number}"
            if html_path and html_path.is_file() and _marker_collides_with_heading(html_path, marker_text):
                c.heading_collision = True
            candidates.append(c)

    works_cited = locate_works_cited(content_files)
    max_footnote = max((c.number for c in candidates), default=0)
    degenerate = is_degenerate(works_cited, max_footnote)

    return DocumentAudit(
        shell_html=shell_html or "",
        candidates=candidates,
        works_cited=works_cited,
        degenerate=degenerate,
    )


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


_RESTART_DROP_THRESHOLD = 20   # preceding value must exceed the dip by at least this much
_RESTART_LOW_CEILING = 10      # the dip value itself must be at or below this
_RESTART_RUN_LENGTH = 3        # at least this many subsequent values must also stay low


@dataclass
class AuditRow:
    candidate: Candidate
    matched_entry_text: str | None
    matched_entry_url: str | None
    confidence: str          # "High" | "Medium" | "Needs manual triage"
    flags: list[str]         # subset of restart_detected, exceeds_length,
                              # no_link_corroboration, degenerate_bibliography,
                              # possible_heading_collision


def score_document(audit):
    """One AuditRow per audit.candidates entry (Task 5's DocumentAudit),
    per the design doc's §5 tier rules: High requires a linked works-cited
    entry at the matching position AND no restart detected before this
    candidate's position; Needs manual triage covers an out-of-bounds
    footnote number, a flagged-degenerate works-cited list (§7), a
    heading-text collision (Task 5), or -- per §5's own explicit compound
    case -- a linkless entry that ALSO falls after a detected restart
    point; everything else with exactly one weaker signal is Medium.

    Deviation from the brief's literal Step 3 sample code: that sample's
    confidence if/elif only promotes to "Needs manual triage" for
    exceeds_length, degenerate_bibliography, or possible_heading_collision,
    and otherwise falls through to a flat "Medium" whenever EITHER
    restart_detected or no_link_corroboration is set -- never checking
    whether both are set together. But design section 5's own text is
    explicit that this is a fourth, distinct "Needs manual triage"
    trigger: "entry N is itself garbled/linkless AND the footnote is also
    past a restart point (both problems compounding)" -- named as
    compounding precisely because each condition ALONE is only Medium
    (per §5's own Medium definition: "missing exactly one of the two High
    conditions"), and per §6, "Every footnote at or after a detected
    restart point is downgraded AT LEAST ONE confidence tier from what
    its own individual signals would otherwise earn" -- for a candidate
    whose individual signal (no link) already earns Medium, "at least one
    tier down" from Medium is Needs manual triage, not a no-op back to
    Medium. The brief's literal code silently drops this compound trigger
    entirely (confirmed via a new adversarial test,
    test_compounding_no_link_and_restart_forces_needs_manual_triage, that
    fails against the brief's literal sample and passes against the fix
    below). Fixed by adding an explicit
    ("restart_detected" in flags and "no_link_corroboration" in flags)
    clause to the Needs-manual-triage condition; everything else is
    unchanged from the brief's sample.
    """
    numbers = [c.number for c in audit.candidates]
    restart_idx = detect_restart_index(numbers)

    rows = []
    for i, c in enumerate(audit.candidates):
        flags = []
        entry_text = entry_url = None
        idx = c.number - 1
        if 0 <= idx < len(audit.works_cited):
            entry_text, entry_url = audit.works_cited[idx]
        else:
            flags.append("exceeds_length")

        if audit.degenerate:
            flags.append("degenerate_bibliography")
        if restart_idx is not None and i >= restart_idx:
            flags.append("restart_detected")
        if entry_text is not None and not entry_url:
            flags.append("no_link_corroboration")
        if c.heading_collision:
            flags.append("possible_heading_collision")

        if (
            "exceeds_length" in flags
            or "degenerate_bibliography" in flags
            or "possible_heading_collision" in flags
            or ("restart_detected" in flags and "no_link_corroboration" in flags)
        ):
            confidence = "Needs manual triage"
        elif "restart_detected" in flags or "no_link_corroboration" in flags:
            confidence = "Medium"
        else:
            confidence = "High"

        rows.append(AuditRow(
            candidate=c, matched_entry_text=entry_text, matched_entry_url=entry_url,
            confidence=confidence, flags=flags,
        ))
    return rows


def detect_restart_index(numbers):
    """Detect the index in a document-order candidate-number sequence
    where footnote numbering restarts mid-document: a drop from a high
    value to a low one that STAYS low for several subsequent markers,
    as opposed to a single-value dip consistent with ordinary
    out-of-order reuse of a low footnote number. Returns the index of
    the first low value in that sustained drop, or None if no such
    restart is present."""
    for i in range(1, len(numbers)):
        prev, cur = numbers[i - 1], numbers[i]
        if cur > _RESTART_LOW_CEILING or prev - cur < _RESTART_DROP_THRESHOLD:
            continue
        window = numbers[i:i + _RESTART_RUN_LENGTH]
        if len(window) == _RESTART_RUN_LENGTH and all(n <= _RESTART_LOW_CEILING * 2 for n in window):
            return i
    return None


_REPORT_FIELDS = [
    "file", "footnote_number", "body_context_snippet",
    "matched_works_cited_entry", "matched_works_cited_url",
    "confidence_tier", "flags",
]


def write_report(rows_by_shell, out_path):
    """Flatten rows_by_shell (Task 6/7's per-document AuditRow lists,
    keyed by shell .html path) into the design doc's §8 CSV report:
    one row per candidate, columns exactly _REPORT_FIELDS, flags joined
    with ';', sorted by (file, footnote_number) for a deterministic
    diff-friendly output regardless of dict/candidate iteration order.

    Sorting happens on the flat dict BEFORE footnote_number is handed
    to csv.DictWriter, so the sort key is still the int
    r.candidate.number, not its eventual string form in the CSV cell --
    confirmed with an adversarial test (numbers 2 and 10 in the same
    file) that a naive post-stringification sort would get wrong
    ("10" < "2" lexicographically) but this ordering does not.

    csv.DictWriter (the stdlib csv module, default dialect) already
    quotes any field containing a comma, double quote, or newline and
    escapes embedded double quotes, so a body_context_snippet or
    matched_works_cited_entry containing a comma and/or a newline --
    both routine in real corpus prose -- round-trips through
    write+csv.DictReader unmangled with no extra escaping needed here;
    confirmed via
    test_context_snippet_containing_a_comma_and_newline_round_trips_safely.
    """
    flat = []
    for shell_html, rows in rows_by_shell.items():
        for r in rows:
            flat.append({
                "file": shell_html,
                "footnote_number": r.candidate.number,
                "body_context_snippet": r.candidate.context,
                "matched_works_cited_entry": r.matched_entry_text or "",
                "matched_works_cited_url": r.matched_entry_url or "",
                "confidence_tier": r.confidence,
                "flags": ";".join(r.flags),
            })
    flat.sort(key=lambda row: (row["file"], row["footnote_number"]))

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=_REPORT_FIELDS)
        writer.writeheader()
        writer.writerows(flat)


DEFAULT_EXCLUDE_DIRS = {"papers", "scripts", "scratch", "bibliography"}


def main(argv=None):
    """CLI entry point: walk a corpus (default docs/, excluding
    docs/papers, docs/scripts, docs/scratch, docs/bibliography per the
    design doc), run the full Task 1-8 pipeline over every shell
    article found, write the §8 CSV report, and print a one-line
    per-tier summary. Never writes to any corpus document -- read-only
    end to end."""
    import xml.etree.ElementTree as ET

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus-root", default=str(REPO_ROOT / "docs"))
    parser.add_argument("--out", default=str(REPO_ROOT / "docs" / "audits" / "footnote-citation-audit.csv"))
    args = parser.parse_args(argv)

    corpus_root = Path(args.corpus_root)
    backlinks = build_backlink_map(corpus_root)

    shells = []
    for xml_path in sorted(corpus_root.rglob("*.xml")):
        if any(part in DEFAULT_EXCLUDE_DIRS for part in xml_path.relative_to(corpus_root).parts):
            continue
        try:
            root_tag = ET.parse(xml_path).getroot().tag
        except ET.ParseError:
            continue
        if root_tag == f"{{{DB_NS}}}article":
            shells.append(xml_path)

    rows_by_shell = {}
    tier_counts = {"High": 0, "Medium": 0, "Needs manual triage": 0}
    for shell in shells:
        audit = audit_document(shell, backlinks)
        if not audit.candidates:
            continue
        rows = score_document(audit)
        rows_by_shell[audit.shell_html] = rows
        for r in rows:
            tier_counts[r.confidence] += 1

    write_report(rows_by_shell, Path(args.out))
    print(f"OK: {sum(tier_counts.values())} candidates -- High {tier_counts['High']}, "
          f"Medium {tier_counts['Medium']}, Needs manual triage {tier_counts['Needs manual triage']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

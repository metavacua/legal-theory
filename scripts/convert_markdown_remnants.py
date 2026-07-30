"""Corpus-wide detection and conversion of raw, unconverted Markdown
inline-emphasis and pipe-table syntax that survived as literal text
content in DocBook XML -- the original markdown-to-DocBook conversion
for this subset of documents built correct DocBook *structure*
(<para>, <itemizedlist>, even <informaltable> in some cases) but never
ran that structure's own text through a real Markdown *inline*
parser, so "**bold**", "*italic*", and whole raw pipe-delimited
tables survive as literal text instead of <emphasis>/<informaltable>
markup. Confirmed live in the corpus's own checked-in generated HTML,
e.g. docs/court-record/theory/federal-constitutional/existing-doctrine/
first-amendment-landmark-cases-research.html (a literal "**" inside an
<h4>) and docs/court-record/matters/google-platform-misclassification/
evidence/potential-service-contracts-in-google.html (an entire table
rendered as raw pipe-and-asterisk text).

Both conversions delegate the actual Markdown parsing to pandoc (the
same tool convert_to_docbook.py already trusts for the same job)
rather than hand-rolling a Markdown emphasis/table parser: real
CommonMark emphasis resolution is a documented, non-trivial algorithm
(delimiter runs, flanking rules, nesting) that pandoc already
implements correctly -- confirmed against real corpus edge cases a
naive regex gets wrong: a 5-asterisk-run nested bold-inside-italic-
inside-bold case, and an academic citation title containing genuine,
non-emphasis footnote-style asterisks ("Schwartz* & Robert E.
Scott**") that must NOT be touched. See
.superpowers/sdd/2026-07-29-docbook-content-conformance.md for the
full design rationale."""

import argparse
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from convert_to_docbook import DB_NS, XLINK_NS, REPO_ROOT  # noqa: E402
from build_bibliography import _normalize_ws  # noqa: E402

# Both wrapper elements below need not just the default DocBook
# namespace but also xlink: a bare URL in plain prose (routine in
# citation/works-cited text) is autolinked by pandoc's GFM reader into
# a real <link xlink:href="..."> with no xmlns:xlink declaration of
# its own (it relies on an ancestor to provide one, matching how
# convert_to_docbook.py's own wrap_fragment() declares it on ITS
# wrapper root for the same reason) -- confirmed live: omitting this
# crashed the real corpus-wide run with "unbound prefix" on the first
# citation text containing both a stray, non-emphasis '*' and a bare
# URL (docs/bibliography/references.xml), well before
# _convert_run_if_safe's own safety checks ever got a chance to
# correctly decline converting that text for unrelated reasons.
_WRAPPER_XMLNS = f'xmlns="{DB_NS}" xmlns:xlink="{XLINK_NS}"'


def _run_pandoc_docbook5(text):
    """text run through pandoc's GFM reader and DocBook5 writer,
    stripped of pandoc's own line-wrapped pretty-printing (collapsed
    to single spaces -- pure wrapper/formatting artifact, not
    meaningful content -- confirmed live during design: without this,
    a converted run's leading space survives as a genuine, wrong extra
    space glued onto whatever plain text precedes it) and of the
    repeated xmlns declaration pandoc puts on every top-level element.
    Shared by _pandoc_inline_fragment and _pandoc_table_fragment,
    which each do their own wrapping/extraction on top of this common
    "run pandoc, get a clean fragment string back" step."""
    result = subprocess.run(
        ["pandoc", "-f", "gfm", "-t", "docbook5"],
        input=text, capture_output=True, text=True, check=True,
    )
    fragment = result.stdout.replace(f'xmlns="{DB_NS}" ', "")
    return re.sub(r"\s+", " ", fragment).strip()


def _pandoc_inline_fragment(text):
    """Run text (a single, tag-free XML text/tail run -- no XML
    entities to worry about, since ElementTree already decoded them
    into real characters) through pandoc. Returns the parsed <r>
    wrapper element (its .text is the leading plain text, its children
    are the resolved inline elements with their own correct .tail
    chain, with text's own original leading/trailing whitespace
    restored -- see below), or None if pandoc's output isn't the
    single <para>...</para> it always produces for one-line input
    (defensive; not expected on real corpus text)."""
    # This corpus's own XML pretty-printing routinely gives a deeply
    # nested element's .text/.tail substantial leading/trailing
    # whitespace of its own -- e.g. a <entry> nested inside
    # <informaltable>/<tgroup>/<tbody>/<row> commonly looks like
    # "\n              **word**\n            " (confirmed live: this
    # corpus's real <entry> cells are one of the deepest nesting
    # levels it has). CommonMark treats a line indented 4+ spaces as
    # an INDENTED CODE BLOCK, not a paragraph (confirmed directly:
    # feeding pandoc that exact indented text produces
    # <programlisting>, not <para>) -- so passing text to pandoc
    # unstripped silently fails this function's own <para> check for
    # every sufficiently-indented run. Confirmed live: this was the
    # root cause of the first real corpus-wide run converting only 65
    # of 1124 bold spans and 0 of 265 italic spans (italic is
    # exclusively inside <entry>, which is always this deeply
    # indented in practice; see
    # test_deeply_indented_entry_text_still_converts).
    leading_ws = text[: len(text) - len(text.lstrip())]
    trailing_ws = text[len(text.rstrip()):]
    stripped = text.strip()
    if not stripped:
        return None
    fragment = _run_pandoc_docbook5(stripped)
    if not (fragment.startswith("<para") and fragment.endswith("</para>")):
        return None
    # _run_pandoc_docbook5's own .strip() only reaches the boundary of
    # the WHOLE fragment string, which is a no-op here (the string
    # starts with "<para" and ends with "</para>", not whitespace) --
    # it does NOT reach the collapsed single space now sitting just
    # inside those tags (e.g. "<para> This is ... </para>"). Slicing
    # the wrapper off exposes that inner boundary, so it needs its own
    # .strip(): without it, a converted run's leading space survives
    # as a genuine, wrong extra space glued onto whatever plain text
    # precedes it (confirmed live: this exact omission was caught by
    # test_para_containing_bold_converts_to_emphasis_strong during the
    # simplify pass that introduced _run_pandoc_docbook5).
    inner = fragment[fragment.index(">") + 1: -len("</para>")].strip()
    wrapped = f'<r {_WRAPPER_XMLNS}>{inner}</r>'
    new_root = ET.fromstring(wrapped)
    # Restore text's own original boundary whitespace (stripped off
    # above only so pandoc wouldn't misread it) onto whichever end of
    # new_root now represents that same boundary: its own .text for
    # the leading side; the last child's .tail for the trailing side
    # (or .text again if pandoc produced no child elements at all --
    # reachable here since a stray, non-emphasis '*' still parses to a
    # childless <para>, even though _convert_run_if_safe's own rule 2
    # will separately decline to use this result).
    new_root.text = leading_ws + (new_root.text or "")
    children = list(new_root)
    if children:
        children[-1].tail = (children[-1].tail or "") + trailing_ws
    else:
        new_root.text += trailing_ws
    return new_root


def _strip_markdown_noise(s):
    """s with '*' and '\\' characters removed, for the word-preservation
    comparison in _convert_run_if_safe. '*' is the emphasis delimiter
    itself, expected to disappear on conversion. '\\' is CommonMark's
    escape-next-character marker (e.g. "\\_", "\\&", "\\[", "\\]") --
    pandoc always un-escapes these as normal, spec-required rendering,
    which is not a content change worth rejecting (confirmed live on
    real corpus text: "*303 Creative LLC v. Elenis*, 599 U.S. \\_\\_\\_"
    round-trips through pandoc as
    "<emphasis>303 Creative LLC v. Elenis</emphasis>, 599 U.S. ___" --
    genuinely correct, but a raw-character comparison sees "\\_\\_\\_"
    != "___" and would wrongly reject the whole run over an unrelated
    trailing citation placeholder). Stripping backslashes wholesale
    (not just the specific escaped characters seen so far) is safe for
    this corpus: legal prose has no legitimate standalone backslash of
    its own, so any backslash present is a CommonMark escape marker."""
    return s.replace("*", "").replace("\\", "")


def _convert_run_if_safe(text):
    """The parsed <r> replacement for text if converting it is safe,
    else None (including the common case: text has no '*' at all, and
    the case where pandoc found nothing to convert). "Safe" means:
    (1) every word in text survives, unchanged, in the converted plain
    text once markdown-noise characters ('*', '\\' -- see
    _strip_markdown_noise) are stripped from both sides for comparison
    -- catches pandoc reinterpreting something unexpected; (2) the
    result contains at least one real <emphasis> element (nothing to
    do otherwise). Together these two rules are what correctly leave a
    genuine, non-emphasis asterisk pair like the "Schwartz* & Robert
    E. Scott**" citation-footnote-marker text untouched: rule (1)
    trivially holds (pandoc leaves it as literal text too, so both
    sides are identical once noise is stripped from both), but rule
    (2) is what actually excludes it -- its converted form has no
    <emphasis> in it at all."""
    if "*" not in text:
        return None
    new_root = _pandoc_inline_fragment(text)
    if new_root is None:
        return None
    new_plain = "".join(new_root.itertext())
    if _normalize_ws(_strip_markdown_noise(text)) != _normalize_ws(_strip_markdown_noise(new_plain)):
        return None
    if new_root.find(f".//{{{DB_NS}}}emphasis") is None:
        return None
    return new_root


def convert_inline_emphasis(root):
    """Walks every element in root's tree exactly once (a snapshot
    taken before any mutation, so newly-inserted <emphasis> elements
    -- whose own text is already fully resolved, plain content with
    no further '*' to process -- are correctly never revisited) and
    replaces every convertible '**bold**' / '*italic*' / '***both***'
    run in each element's own .text and each of its direct children's
    .tail with real <emphasis>/<emphasis role="strong"> markup,
    leaving everything else (including nested descendant content,
    handled separately when the loop reaches that descendant as its
    own 'el') untouched. Returns the number of runs actually
    converted."""
    converted = 0
    for el in list(root.iter()):
        original_children = list(el)
        new_children = []

        if el.text:
            replacement = _convert_run_if_safe(el.text)
            if replacement is not None:
                converted += 1
                el.text = replacement.text or None
                new_children.extend(list(replacement))

        for child in original_children:
            new_children.append(child)
            if child.tail:
                replacement = _convert_run_if_safe(child.tail)
                if replacement is not None:
                    converted += 1
                    child.tail = replacement.text or None
                    new_children.extend(list(replacement))

        el[:] = new_children
    return converted


_ALIGN_ROW_RE = re.compile(r"^\|?\s*:?-{1,}:?\s*(\|\s*:?-{1,}:?\s*)+\|?$")


def _para_own_text(el):
    return "".join(el.itertext())


def _is_pipe_row(text):
    stripped = text.strip()
    return stripped.startswith("|") and stripped.endswith("|") and stripped.count("|") >= 2


def _is_align_row(text):
    return bool(_ALIGN_ROW_RE.match(_normalize_ws(text)))


def _find_table_runs(parent):
    """[(start, end), ...] half-open index ranges into list(parent) of
    every contiguous run of >= 2 direct <para> children that are all
    pipe rows AND include at least one real alignment row -- the
    signal that distinguishes an actual (if unconverted) Markdown
    table from a paragraph that merely happens to contain a pipe
    character. Confirmed live: a real corpus document
    (docs/court-record/matters/cooperative-investment-law/evidence/
    community-care-cooperatives/04-...xml) has 6 contiguous pipe-
    shaped <para> siblings with NO alignment row anywhere among them
    -- a malformed Markdown table GFM itself would never have
    recognized either, so it is correctly excluded here, not
    converted (see test_pipe_paragraphs_without_an_alignment_row_are_
    not_converted)."""
    children = list(parent)
    runs = []
    i, n = 0, len(children)
    while i < n:
        if children[i].tag == f"{{{DB_NS}}}para" and _is_pipe_row(_para_own_text(children[i])):
            j = i
            while j < n and children[j].tag == f"{{{DB_NS}}}para" and _is_pipe_row(_para_own_text(children[j])):
                j += 1
            run = children[i:j]
            if len(run) >= 2 and any(_is_align_row(_para_own_text(c)) for c in run):
                runs.append((i, j))
            i = j
        else:
            i += 1
    return runs


def _markdown_table_source(row_paragraphs):
    return "\n".join(_normalize_ws(_para_own_text(r)) for r in row_paragraphs)


def _pandoc_table_fragment(markdown_text):
    """The single <informaltable> pandoc's GFM table reader + DocBook5
    writer produces for markdown_text -- raises ValueError if the
    input didn't resolve to exactly one (defensive; convert_raw_tables
    only ever calls this with source _find_table_runs already
    confirmed is a valid table)."""
    fragment = _run_pandoc_docbook5(markdown_text)
    wrapped = f'<r {_WRAPPER_XMLNS}>{fragment}</r>'
    root = ET.fromstring(wrapped)
    tables = [c for c in root if c.tag == f"{{{DB_NS}}}informaltable"]
    if len(tables) != 1:
        raise ValueError(f"expected exactly one informaltable from {markdown_text!r}, got {len(tables)}")
    return tables[0]


def convert_raw_tables(root):
    """Replaces every raw pipe-table <para> run found by
    _find_table_runs anywhere in root's tree with a single real
    <informaltable>, built by handing the reconstructed raw Markdown
    table source to pandoc -- the same engine, and so the same
    <informaltable>/<tgroup>/<colspec align=".."/> shape, this
    corpus's OTHER, already-correctly-converted tables were built
    with (confirmed live against docs/court-record/matters/
    cooperative-investment-law/evidence/community-care-cooperatives-v2/
    06-...xml's existing <informaltable>). A table whose Markdown
    source has an all-blank first row (three of the five real corpus
    cases) is pandoc/GFM's own "headerless table" convention: no
    <thead> is emitted, and the row that LOOKS like column labels
    lands in <tbody> as an ordinary first data row, matching this
    corpus's own existing convention exactly -- this is not a
    structural choice made by this function, it falls out of handing
    pandoc the real reconstructed source unmodified.

    Runs within the same parent are processed back-to-front so
    removing/inserting elements for one run never invalidates a later
    run's still-pending indices. Returns the number of tables
    converted."""
    converted = 0
    for parent in list(root.iter()):
        for start, end in reversed(_find_table_runs(parent)):
            children = list(parent)
            row_paragraphs = children[start:end]
            table = _pandoc_table_fragment(_markdown_table_source(row_paragraphs))
            table.tail = row_paragraphs[-1].tail
            for row in row_paragraphs:
                parent.remove(row)
            parent.insert(start, table)
            converted += 1
    return converted


def convert_file(xml_path):
    """Applies both conversions to xml_path, tables first (see the
    design doc's Design Notes for why this order is load-bearing, not
    arbitrary). Writes xml_path back only if something actually
    changed. Returns (tables_converted, emphasis_runs_converted)."""
    tree = ET.parse(xml_path)
    root = tree.getroot()
    n_tables = convert_raw_tables(root)
    n_emphasis = convert_inline_emphasis(root)
    if n_tables or n_emphasis:
        ET.indent(tree, space="  ")
        tree.write(xml_path, encoding="unicode", xml_declaration=True)
    return n_tables, n_emphasis


_BOLD_COUNT_RE = re.compile(r"\*\*[^*\n]+?\*\*")
_ITALIC_COUNT_RE = re.compile(r"(?<!\*)\*(?!\*)[^*\n]+?(?<!\*)\*(?!\*)")


def count_markdown_remnants(xml_path):
    """dict(bold=N, italic=N, raw_tables=N) -- the exact same "own
    text/tail run" tree walk convert_inline_emphasis/convert_raw_tables
    use, so this count is trustworthy as a before/after measurement of
    the SAME thing the fix itself acts on, not a separately-maintained
    approximation. Bold spans are stripped from each run BEFORE
    searching for italic spans in the remainder, matching how a
    "***triple***" span's outer italic half is only visible once its
    inner bold half is accounted for (confirmed live during design: a
    naive un-stripped scan undercounts italic corpus-wide by exactly
    the 3 real '***word***' triple-star spans in the corpus).

    The bold strip's replacement text MUST be non-empty (here, "X"):
    "***Borello***" contains exactly one _BOLD_COUNT_RE match, using
    the inner two of each three-star run ("**Borello**", positions
    1-11), leaving a lone '*' on each side (positions 0 and 12). A
    NON-empty replacement keeps those two lone stars separated by the
    placeholder, so "*X*" still reads as one valid italic span. An
    EMPTY replacement instead collapses the gap between them into a
    bare "**" -- two adjacent stars, which _ITALIC_COUNT_RE's own
    "(?!\\*)"/"(?<!\\*)" guards correctly refuse to match at all,
    silently undercounting italic by 3 again. (Caught live during
    design: an early draft of this exact function used
    `_BOLD_COUNT_RE.sub("", run)` and reported 262, not the correct
    265, on the real corpus -- do not reintroduce that regression;
    see test_triple_star_span_counts_as_one_bold_and_one_italic.)"""
    try:
        root = ET.parse(xml_path).getroot()
    except ET.ParseError:
        return {"bold": 0, "italic": 0, "raw_tables": 0}
    bold = italic = 0
    for el in root.iter():
        runs = ([el.text] if el.text else []) + [c.tail for c in el if c.tail]
        for run in runs:
            bold += len(_BOLD_COUNT_RE.findall(run))
            italic += len(_ITALIC_COUNT_RE.findall(_BOLD_COUNT_RE.sub("X", run)))
    raw_tables = sum(len(_find_table_runs(parent)) for parent in root.iter())
    return {"bold": bold, "italic": italic, "raw_tables": raw_tables}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus-root", default=str(REPO_ROOT / "docs"))
    parser.add_argument("--check", action="store_true",
                         help="report counts only; do not modify any file")
    args = parser.parse_args(argv)
    corpus_root = Path(args.corpus_root)

    totals = {"bold": 0, "italic": 0, "raw_tables": 0}
    changed_files = []
    for xml_path in sorted(corpus_root.rglob("*.xml")):
        before = count_markdown_remnants(xml_path)
        for k in totals:
            totals[k] += before[k]
        if args.check:
            continue
        n_tables, n_emphasis = convert_file(xml_path)
        if n_tables or n_emphasis:
            changed_files.append(str(xml_path))

    mode = "found" if args.check else "found before fix (now converted)"
    print(f"OK: {mode} -- bold {totals['bold']}, italic {totals['italic']}, "
          f"raw_tables {totals['raw_tables']}, across {len(changed_files)} changed files")
    for f in changed_files:
        print(f"  {f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

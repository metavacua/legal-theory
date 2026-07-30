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
from convert_to_docbook import DB_NS, REPO_ROOT  # noqa: E402
from build_bibliography import _normalize_ws  # noqa: E402


def _pandoc_inline_fragment(text):
    """Run text (a single, tag-free XML text/tail run -- no XML
    entities to worry about, since ElementTree already decoded them
    into real characters) through pandoc's GFM reader and DocBook5
    writer. Returns the parsed <r> wrapper element (its .text is the
    leading plain text, its children are the resolved inline elements
    with their own correct .tail chain), or None if pandoc's output
    isn't the single <para>...</para> it always produces for one-line
    input (defensive; not expected on real corpus text)."""
    result = subprocess.run(
        ["pandoc", "-f", "gfm", "-t", "docbook5"],
        input=text, capture_output=True, text=True, check=True,
    )
    fragment = result.stdout.strip()
    if not (fragment.startswith("<para") and fragment.endswith("</para>")):
        return None
    inner = fragment[fragment.index(">") + 1: -len("</para>")]
    # Collapse pandoc's own line-wrapped pretty-printing to single
    # spaces, then strip the outer boundary: pandoc always wraps
    # output as "<para>\n  CONTENT\n</para>", and that "\n  "/"\n" is
    # pure wrapper artifact, not meaningful leading/trailing content.
    # (Confirmed live during design: without the final .strip(), a
    # converted run's leading space survives as a genuine, wrong extra
    # space glued onto whatever plain text precedes it.)
    inner = re.sub(r"\s+", " ", inner).strip()
    inner = inner.replace(f'xmlns="{DB_NS}" ', "")
    wrapped = f'<r xmlns="{DB_NS}">{inner}</r>'
    return ET.fromstring(wrapped)


def _convert_run_if_safe(text):
    """The parsed <r> replacement for text if converting it is safe,
    else None (including the common case: text has no '*' at all, and
    the case where pandoc found nothing to convert). "Safe" means:
    (1) every word in text survives, unchanged, in the converted plain
    text once '*' characters are stripped from both sides for
    comparison -- catches pandoc reinterpreting something unexpected;
    (2) the result contains at least one real <emphasis> element
    (nothing to do otherwise). Together these two rules are what
    correctly leave a genuine, non-emphasis asterisk pair like the
    "Schwartz* & Robert E. Scott**" citation-footnote-marker text
    untouched: rule (1) trivially holds (pandoc leaves it as literal
    text too, so both sides are identical once '*' is stripped from
    both), but rule (2) is what actually excludes it -- its converted
    form has no <emphasis> in it at all."""
    if "*" not in text:
        return None
    new_root = _pandoc_inline_fragment(text)
    if new_root is None:
        return None
    new_plain = "".join(new_root.itertext())
    if _normalize_ws(text.replace("*", "")) != _normalize_ws(new_plain.replace("*", "")):
        return None
    if not any(True for _ in new_root.iter(f"{{{DB_NS}}}emphasis")):
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
    result = subprocess.run(
        ["pandoc", "-f", "gfm", "-t", "docbook5"],
        input=markdown_text, capture_output=True, text=True, check=True,
    )
    fragment = result.stdout.strip()
    fragment = fragment.replace(f'xmlns="{DB_NS}" ', "")
    fragment = re.sub(r"\s+", " ", fragment).strip()
    wrapped = f'<r xmlns="{DB_NS}">{fragment}</r>'
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

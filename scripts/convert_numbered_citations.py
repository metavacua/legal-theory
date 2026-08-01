"""Converts the Deep-Research-style numbered-citation pattern (see
docs/superpowers/specs/2026-07-26-citation-standardization-design.md
Section 6, Category A only -- documents whose numbered works-cited
list is confirmed intact against their real source) into real DocBook
structure: one entry file per works-cited item, and every glued
"word.N" marker in every fragment of the shell article rewritten to a
real <biblioref linkend="KEY"/> pointing at it -- DocBook 5.2's actual
cross-reference-to-a-bibliography-entry element, not <citation> (which
renders as inert bracketed text under both this project's own
html5.xsl and the unmodified official docbook-xsl-ns stylesheet;
<biblioref> renders as a real resolved hyperlink under the latter,
confirmed by direct testing 2026-07-26).

Reuses audit_footnote_links.py's _is_excluded_context() for exclusion
(statute pincites, alphanumeric regulatory codes) rather than
re-deriving it -- that function was written and adversarially tested
against itertext()-extracted plain text, but confirmed by direct
testing 2026-07-26 to also work correctly applied to the text/tail of
a single element (a shorter span than full itertext(), but the
function only ever looks at the tail end of what it's given, so a
shorter-but-still-correctly-bounded span is equivalent).

convert_markers_in_fragment() is structural (tree-based via
ElementTree), not text-pattern-based: it parses each fragment, walks
every element's own .text and .tail independently, and excludes
<title> descendant text (section headings are never real footnote
candidates), <link> descendant text (works-cited citation URLs/
display text), and works-cited <section> descendant text (its own
listitem prose, scanned because this function runs on every fragment
of a document -- including the one holding the works-cited list --
before remove_works_cited_section deletes it) via real ancestry
checks, not raw-text span heuristics. Originally implemented as a
raw-text regex requiring an immediate preceding "." (the "glued"
shape); replaced with the current tree-walk after Task 1's corpus
survey (.superpowers/sdd/task-1-survey-findings.md) found real
marker instances in four more shapes the raw-text regex could not
structurally express -- see convert_markers_in_fragment's own
docstring for the full list of five shapes it now recognizes.

Known limitation, stated plainly: two markers glued directly together
with NO separator between them (e.g. raw text "...gradients.3258"
meaning two markers, 32 and 58, with no space or punctuation dividing
them) are not split apart -- _DIGIT_RUN_RE's greedy up-to-3-digit
match consumes "325" then "8" as a single 4-digit run, neither of
which is likely a valid key_map ordinal, so the whole run is left
unconverted. Resolving this in general requires trying every way to
partition a digit run into 1-3-digit chunks against key_map, which
introduces real ambiguity (multiple partitions can each coincidentally
match SOME key_map entry) that Task 1's survey did not identify a safe
structural signal for, and no confirmed corpus instance beyond the one
pre-existing pilot-document case (already hand-fixed in commit
8de2d12) motivated solving it here. A real limitation to revisit if
Task 3's corpus-wide run surfaces more instances."""

import re
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parent))
from convert_to_docbook import DB_NS, XML_NS  # noqa: E402
from citation_entry import ENTRIES_DIR, derive_entry_key, write_biblioentry  # noqa: E402
from audit_footnote_links import _is_excluded_context  # noqa: E402

# Any 1-3 digit run is a candidate -- deliberately broader than a
# preceding-"." requirement (see convert_markers_in_fragment's
# docstring for the four structural shapes this now recognizes: glued,
# whole-cell, bare-token, em-dash-bounded bare-token, bracket-glued).
_DIGIT_RUN_RE = re.compile(r"\d{1,3}")

# U+2014 (em dash) vs U+2013 (en dash) -- Task 1's survey confirmed
# both appear glued directly onto a bare digit in real corpus text, but
# only the em-dash case is a real marker boundary (5 confirmed
# instances, all verified against their document's works-cited
# ordinal); the en-dash case is confirmed NOT a marker in every
# instance checked (statute section numbers like "3-303", ordinary
# prose like "age of 18-has the legal right", a USC title citation).
# The two characters must not be conflated.
_EM_DASH = "—"

# Trailing-boundary set for bare-token/bracket-glued shapes. Excludes
# ":" (unlike the brief's draft, which lifted the pilot's own
# `.,;:]"` set verbatim) -- Task 1 found a digit run immediately
# followed by ":" is, in every corpus instance checked, one of two
# confirmed non-marker shapes: an inline "Label N:" section/list header
# (484 instances) or a clock time/ratio/timestamp/docket number (8
# instances). No corpus instance found where a digit immediately
# followed by ":" was a real marker.
_BARE_TOKEN_FOLLOWING = ").,;]"
# Leading-boundary set for bare-token/em-dash-bounded shapes: whitespace
# (checked separately via .isspace()) or an opening bracket/paren --
# i.e. this token starts a parenthetical or is the first thing on a
# line, not glued onto a preceding word.
_BARE_TOKEN_PRECEDING = "(["

# Column-header keywords marking a table column as part of the
# document's citation apparatus, not literal tabular data. Chosen by
# directly reading the real header row of all 9 real corpus documents
# Task 1 found containing whole-cell candidates: 7 of 9 have a citation
# column whose header contains one of these words verbatim ("Source(s)",
# "Relevant Sources", "Relevant Snippets", "Source Study Snippet",
# "Representative Research", "Source Citations"); the remaining 2 (real
# DATA tables -- ages 16/17/18 in "General Age of Consent",
# dependents 0/1 in "Dependents") contain none of them. See
# convert_markers_in_fragment's docstring and this task's report for
# the full investigation and the conservative trade-off this implies
# (a genuine citation column using none of these words, e.g. a header
# that says nothing but "Cite", would be missed and left unconverted --
# preferred over the alternative of converting a real data table's
# literal numbers).
_WHOLE_CELL_HEADER_KEYWORDS = ("source", "citation", "reference", "snippet", "research")

_TITLE_TAG = f"{{{DB_NS}}}title"
_LINK_TAG = f"{{{DB_NS}}}link"
_SECTION_TAG = f"{{{DB_NS}}}section"
_ENTRY_TAG = f"{{{DB_NS}}}entry"
_ROW_TAG = f"{{{DB_NS}}}row"
_TGROUP_TAG = f"{{{DB_NS}}}tgroup"
_THEAD_TAG = f"{{{DB_NS}}}thead"
_TBODY_TAG = f"{{{DB_NS}}}tbody"


def _is_excluded_ancestor(elem):
    """True if elem itself must never contribute a real marker: a
    <title> (section headings are never footnote candidates) or a
    <link> (works-cited citation URLs/display text -- Task 1's largest
    single false-positive category, 5,870 of 14,705 "other"-bucket
    candidates, 39.9%) or a works-cited <section
    xml:id="works-cited"> (its own listitem prose -- accessed dates,
    volume numbers, etc. -- is scanned by this function too, since the
    production driver calls convert_markers_in_fragment on every
    fragment of a document, including the one holding the works-cited
    list, BEFORE remove_works_cited_section deletes it; see
    docs/superpowers/sdd/2026-07-29-category-a-toolchain-verification-
    plan.md's Task 3 loop)."""
    if elem.tag in (_TITLE_TAG, _LINK_TAG):
        return True
    if elem.tag == _SECTION_TAG and elem.get(f"{{{XML_NS}}}id") == "works-cited":
        return True
    return False


def _in_excluded_ancestry(container, parent_map):
    """True if container itself, or any of its ancestors, is excluded
    per _is_excluded_ancestor -- walked via parent_map (computed once,
    before any mutation, since new <biblioref> elements this function
    inserts are never queried for their ancestry)."""
    elem = container
    while elem is not None:
        if _is_excluded_ancestor(elem):
            return True
        elem = parent_map.get(elem)
    return False


def _column_header_text(entry, parent_map):
    """Lowercased, whitespace-normalized text of the column header
    <entry> that entry (a table cell) sits under, or None when this
    can't be determined (entry isn't inside a <row>/<tgroup>, there is
    no header row, or entry's own row IS the header row -- all treated
    as "no corroborating evidence" by the caller, not as an error)."""
    row = parent_map.get(entry)
    if row is None or row.tag != _ROW_TAG:
        return None
    row_container = parent_map.get(row)  # <thead> or <tbody>
    tgroup = parent_map.get(row_container) if row_container is not None else None
    if tgroup is None or tgroup.tag != _TGROUP_TAG:
        return None
    try:
        col_index = list(row).index(entry)
    except ValueError:
        return None
    thead = tgroup.find(_THEAD_TAG)
    if thead is not None:
        header_rows = thead.findall(_ROW_TAG)
    else:
        tbody = tgroup.find(_TBODY_TAG)
        header_rows = tbody.findall(_ROW_TAG)[:1] if tbody is not None else []
    if not header_rows:
        return None
    header_row = header_rows[0]
    if header_row is row:
        return None  # entry IS in the header row itself
    header_entries = list(header_row)
    if col_index >= len(header_entries):
        return None
    return " ".join("".join(header_entries[col_index].itertext()).split()).lower()


def _whole_cell_is_corroborated(elem, parent_map):
    """Task 1's finding: whole-cell (the digit run is the ENTIRE text
    content of its containing element) is NOT a universally safe
    signal on its own -- 2 of 9 real corpus documents with whole-cell
    candidates are ordinary data tables (ages, dependent counts) whose
    values can coincidentally fall inside a valid key_map ordinal
    range. Only table <entry> cells need this extra check: a
    standalone element that isn't a table cell (e.g. a citation number
    isolated as its own <para>, the real shape found in
    patron-artist-collective-work-structure fragment 07) has no known
    false-positive pattern in Task 1's survey, so it is trusted on
    shape + key_map membership alone, same as bare-token.

    For a table cell, this requires the cell's own column header to
    name the citation apparatus (see _WHOLE_CELL_HEADER_KEYWORDS) --
    when the header can't be determined at all, this is conservative
    and returns False (flagged, not auto-converted) rather than
    guessing; a real, defensible signal beats no signal, but "no
    signal found" must not default to "convert"."""
    if elem.tag != _ENTRY_TAG:
        return True
    header = _column_header_text(elem, parent_map)
    if header is None:
        return False
    return any(keyword in header for keyword in _WHOLE_CELL_HEADER_KEYWORDS)


def _listitem_text_and_href(listitem):
    """(display_text, href|None) for a works-cited <listitem> -- the
    link's own text is excluded from display_text (it's normally just
    a repeat of the href), matching build_bibliography.py's existing
    convention for this exact shape."""
    link = listitem.find(f".//{{{DB_NS}}}link")
    href = link.get("{http://www.w3.org/1999/xlink}href") if link is not None else None
    full_text = " ".join(" ".join(listitem.itertext()).split())
    if href and href in full_text:
        full_text = full_text.replace(href, "").strip()
    return full_text, href


def build_entry_key_map(works_cited_fragment_path):
    """dict[int, str]: works-cited ordinal (1-based) -> entry key, and
    writes one entry file per listitem as a side effect via
    write_biblioentry, called unconditionally (not guarded by our own
    entry_path.exists() pre-check) so that write_biblioentry's own
    idempotent-no-op-on-identical-content / raise-on-genuine-mismatch
    logic is always reachable. write_biblioentry no-ops when the file
    already holds identical (key, role, title, href), so calling this
    twice on the SAME fragment is safe to re-run (confirmed live by
    test_is_idempotent_when_called_twice_on_same_fragment) -- but it
    correctly raises ValueError when two DIFFERENT sources collide on
    the same derived key (derive_entry_key() is not injective;
    confirmed live by
    test_two_different_sources_colliding_on_the_same_derived_key_raises,
    which reproduces a real, previously-silent data-loss bug: an
    earlier version of this function pre-checked entry_path.exists()
    and skipped the write_biblioentry call entirely whenever the path
    already existed, regardless of whether the existing content
    actually matched the current listitem -- silently discarding a
    second, genuinely different source and mapping its ordinal to the
    first source's entry instead, with no error anywhere). Only call
    this for a document already confirmed Category A (see
    docs/bibliography/numbered-citation-classification.json, Task 5)
    -- this function does not itself verify the list is complete or
    trustworthy.

    Only the FIRST <section xml:id="works-cited"> found in document
    order is processed (confirmed live by
    test_only_the_first_works_cited_section_is_processed). A single
    fragment should never legitimately contain more than one -- a
    duplicate xml:id is invalid XML and would fail schema validation
    before this function is ever reached -- so this is a defensive
    choice against a malformed/pre-validation input, not a feature."""
    root = ET.parse(works_cited_fragment_path).getroot()
    key_map = {}
    for section in root.iter(f"{{{DB_NS}}}section"):
        if section.get(f"{{{XML_NS}}}id") != "works-cited":
            continue
        for i, listitem in enumerate(section.iter(f"{{{DB_NS}}}listitem"), start=1):
            text, href = _listitem_text_and_href(listitem)
            key = derive_entry_key(text, href)
            entry_path = ENTRIES_DIR / f"{key}.xml"
            write_biblioentry(entry_path, key=key, role="secondary", title=text, href=href)
            key_map[i] = key
        break
    return key_map


def convert_markers_in_fragment(fragment_path, key_map):
    """Rewrites every numbered-citation marker in fragment_path to a
    real <biblioref linkend="KEY"/>, in place, using key_map. Returns
    the number of markers actually converted -- never counts a
    candidate _DIGIT_RUN_RE found but that failed a shape check,
    _is_excluded_context(), the <title>/<link>/works-cited exclusion,
    or key_map membership.

    Structural, not text-pattern-based: parses fragment_path as a tree
    and walks every element's own .text and .tail independently
    (ElementTree never conflates them -- a candidate digit run in one
    is never confused with the other). A candidate converts when its N
    is in key_map, _is_excluded_context() does not flag the text
    immediately preceding it (statute pincites, alphanumeric codes,
    decimals -- checked on the same span the original raw-text
    implementation checked: the text ending right before a marker's
    "." for the glued shape, or right before the digit run itself for
    every other shape), it is not inside a <title>, <link>, or
    works-cited <section> (see _is_excluded_ancestor), and it matches
    one of five structural shapes (Task 1's corpus survey --
    .superpowers/sdd/task-1-survey-findings.md -- is the source of
    truth for all five; the original pilot commit 8de2d12 only needed
    the first three, the other two are lower-frequency real shapes the
    survey found across the other 81 documents):

      - glued: immediately preceded by a single "." with no
        intervening space (e.g. "parameters.1") -- the original,
        already-verified shape, trusted on shape + key_map alone.
      - whole-cell: the digit run is the WHOLE, exact text content of
        its containing element (nothing precedes or follows it there,
        and nothing else in the element's full text either). NOT
        universally safe as pure shape -- when the containing element
        is a table <entry>, this also requires
        _whole_cell_is_corroborated() (the column's header must name
        the citation apparatus; see that function's docstring for the
        real-document investigation behind this, and this task's
        report for the two real DATA tables it exists to reject).
        Elsewhere (e.g. a citation number isolated as its own <para>)
        it converts on shape + key_map alone -- Task 1 found no
        false-positive pattern for that case.
      - bare-token: bounded by whitespace/opening-bracket before and
        whitespace/").,;]" after (note: NOT ":" -- Task 1 found a
        digit immediately followed by ":" is, in every real instance
        checked, a "Label N:" section header or a clock time/ratio/
        docket number, never a marker).
      - em-dash-bounded bare-token: same leading boundary as
        bare-token, but bounded on the trailing side by an em dash
        (U+2014) glued on with no space (e.g. "business 12—making").
        An en dash (U+2013, a different character) is NOT this shape
        and never converts via this path.
      - bracket-glued: immediately preceded by "]" with no space and
        no period anywhere (e.g. "[Arcara]32"), trailing boundary same
        as bare-token.

    key_map is always 1-based, so a literal ".0" marker never converts
    even if key_map somehow contains a 0 key (confirmed live by
    test_marker_number_zero_is_never_converted).

    Every distinct match _DIGIT_RUN_RE finds converts independently --
    the same marker number appearing twice in one fragment converts
    both times, with no shared mutable state that could under-convert
    a repeated number (confirmed live by
    test_same_marker_number_appears_twice_both_convert).

    Uses ET.indent() before writing, matching remove_works_cited_
    section's own convention in this same file."""
    fragment_path = Path(fragment_path)
    tree = ET.parse(fragment_path)
    root = tree.getroot()
    # Computed once, over the pristine (unmutated) tree -- ancestry and
    # whole-cell's own "am I the entire content of my element" check
    # must both see the ORIGINAL structure, not a tree partway through
    # being spliced with new <biblioref> elements.
    parent_map = {child: parent for parent in root.iter() for child in parent}
    elem_full_text = {e: ("".join(e.itertext()).strip() or None) for e in root.iter()}
    converted = 0

    def _classify(preceding, following):
        """(is_glued, is_whole_cell_shape, is_bare_token,
        is_em_dash_bounded, is_bracket_glued) for a single candidate,
        given the text immediately before (preceding) and after
        (following) it within its own text/tail run. is_whole_cell_shape
        is pure shape only -- the corroboration check happens in the
        caller, which also has the containing element available."""
        is_glued = preceding.endswith(".") and not preceding.endswith("..")
        is_whole_cell_shape = not preceding.strip() and not following.strip()
        preceding_ok = (
            not preceding or preceding[-1].isspace() or preceding[-1] in _BARE_TOKEN_PRECEDING
        )
        following_char = following[:1]
        following_ok = (
            not following_char or following_char.isspace() or following_char in _BARE_TOKEN_FOLLOWING
        )
        is_bare_token = preceding_ok and following_ok
        is_em_dash_bounded = preceding_ok and following_char == _EM_DASH
        is_bracket_glued = preceding.endswith("]") and following_ok
        return is_glued, is_whole_cell_shape, is_bare_token, is_em_dash_bounded, is_bracket_glued

    def _convert_run(text, container, is_text_run):
        """[str, (marker_key,), str, (marker_key,), ..., str] -- text
        with every converted candidate's digits replaced by a
        1-tuple marker placeholder, ready for _splice(). A single-item
        return means nothing converted in this run."""
        nonlocal converted
        pieces = []
        pos = 0
        for m in _DIGIT_RUN_RE.finditer(text):
            start, end = m.span()
            preceding = text[:start]
            following = text[end:]
            exclusion_text = preceding[:-1] if preceding.endswith(".") else preceding
            if _is_excluded_context(exclusion_text):
                continue
            n = int(m.group(0))
            if n not in key_map:
                continue
            is_glued, is_whole_cell_shape, is_bare_token, is_em_dash_bounded, is_bracket_glued = (
                _classify(preceding, following)
            )
            is_whole_cell_candidate = (
                is_text_run
                and is_whole_cell_shape
                and elem_full_text.get(container) == m.group(0)
            )
            if is_whole_cell_candidate:
                # Whole-cell is exclusive of the other shapes, not an
                # additional alternative alongside them: empty
                # preceding/following text trivially ALSO satisfies
                # bare-token's boundary conditions (isolated content is
                # "whitespace-bounded" by definition), so without this
                # exclusivity a whole-cell candidate that FAILS
                # corroboration (a real data-table digit, e.g. an
                # age-of-consent "16") would still slip through via the
                # bare-token check below and convert anyway --
                # confirmed live by
                # test_whole_cell_in_a_real_data_table_is_not_converted,
                # which failed against an earlier version of this
                # function that treated the checks as independent
                # alternatives.
                if not _whole_cell_is_corroborated(container, parent_map):
                    continue
            elif not (is_glued or is_bare_token or is_em_dash_bounded or is_bracket_glued):
                continue
            pieces.append(text[pos:start])
            pieces.append((key_map[n],))
            converted += 1
            pos = end
        if not pieces:
            return [text]
        pieces.append(text[pos:])
        return pieces

    def _splice(pieces, owner, is_tail, insertion_parent, insertion_start_index):
        """Rewrites owner.text (is_tail=False) or owner.tail
        (is_tail=True) as plain leftover text, inserting one real
        <biblioref> element into insertion_parent's children (starting
        at insertion_start_index) per marker in pieces. insertion_parent
        is owner itself for a .text run (new bibliorefs become owner's
        new FIRST children, pushing owner's real pre-existing children
        after them) or owner's parent for a .tail run (new bibliorefs
        become owner's new immediately-following siblings)."""
        leading = pieces[0]
        if is_tail:
            owner.tail = leading or None
        else:
            owner.text = leading or None
        idx = insertion_start_index
        i = 1
        while i < len(pieces):
            key = pieces[i][0]
            biblioref = ET.Element(f"{{{DB_NS}}}biblioref", {"linkend": key})
            trailing_text = pieces[i + 1] if i + 1 < len(pieces) else ""
            biblioref.tail = trailing_text or None
            insertion_parent.insert(idx, biblioref)
            idx += 1
            i += 2

    def _process(parent):
        # Snapshot BEFORE any mutation at this level -- new <biblioref>
        # elements get inserted into `parent`'s (and its children's)
        # live children lists as this loop runs, but only ever
        # alongside/after an already-visited original element, never
        # taking an unvisited original element's place in this
        # snapshot.
        for elem in list(parent):
            _process(elem)  # recurse first, using elem's still-untouched children
            if elem.text and not _in_excluded_ancestry(elem, parent_map):
                pieces = _convert_run(elem.text, elem, is_text_run=True)
                if len(pieces) > 1:
                    _splice(pieces, owner=elem, is_tail=False, insertion_parent=elem, insertion_start_index=0)
            if elem.tail and not _in_excluded_ancestry(parent, parent_map):
                pieces = _convert_run(elem.tail, None, is_text_run=False)
                if len(pieces) > 1:
                    insert_at = list(parent).index(elem) + 1
                    _splice(pieces, owner=elem, is_tail=True, insertion_parent=parent, insertion_start_index=insert_at)

    _process(root)
    ET.indent(tree, space="  ")
    tree.write(fragment_path, encoding="unicode", xml_declaration=True)
    return converted


def remove_works_cited_section(fragment_path):
    """Removes the <section xml:id="works-cited"> from fragment_path,
    now that its content lives in standalone entry files. No-op (and
    returns False) if the fragment doesn't have one -- most fragments
    of a multi-fragment document don't; the list typically lives in
    only one."""
    fragment_path = Path(fragment_path)
    tree = ET.parse(fragment_path)
    root = tree.getroot()
    removed = False
    # root.iter() already yields root itself first -- do not also
    # prepend [root], which would list it twice and raise ValueError
    # on the second, redundant removal attempt for any match that is a
    # direct child of root (confirmed live by
    # test_removes_a_direct_child_of_root_without_raising).
    for parent in root.iter():
        for child in list(parent):
            if (child.tag == f"{{{DB_NS}}}section"
                    and child.get(f"{{{XML_NS}}}id") == "works-cited"):
                parent.remove(child)
                removed = True
    if removed:
        ET.indent(tree, space="  ")
        tree.write(fragment_path, encoding="unicode", xml_declaration=True)
    return removed

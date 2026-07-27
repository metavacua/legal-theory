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
testing 2026-07-26 to also work correctly applied to raw (tag-
containing) fragment text, which is what this module operates on (it
needs to preserve surrounding markup for in-place replacement, unlike
audit_footnote_links.py's own read-only reporting use case).

Also excludes markers inside <title> elements (section headings are
never real footnote candidates), matching audit_footnote_links.py's
own _element_body_text() exclusion -- but done here as a raw-text
span check (_title_spans()) rather than a tree-based one, since this
module operates on unparsed raw file text and must preserve markup for
in-place replacement rather than extracting plain text. A task review
found this exclusion missing from an earlier version and reproduced it
live: "<title>New Approach.5</title>" with a matching key_map entry
was corrupted into "<title>New Approach.<biblioref .../></title>";
confirmed fixed by test_marker_inside_title_element_is_not_converted.

Known limitation, stated plainly: a marker glued directly onto inline-
formatted text where the closing tag sits BETWEEN the digit run and
its terminating boundary (not the more common case of a closing tag
sitting between a word and the marker's own "." -- that case converts
correctly; confirmed live by
test_marker_after_inline_closing_tag_converts_correctly in this
module's test suite) is not caught. No such case exists in the single
verified pilot document this phase targets; a real limitation to fix
before any corpus-wide run."""

import re
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parent))
from convert_to_docbook import DB_NS, XML_NS  # noqa: E402
from citation_entry import ENTRIES_DIR, derive_entry_key, write_biblioentry  # noqa: E402
from audit_footnote_links import _is_excluded_context  # noqa: E402

# Broader than measure_citation_conformance.py's _GLUED_MARKER_RE (no
# preceding-letter requirement, matching audit_footnote_links.py's own
# _FOOTNOTE_MARKER_RE), and scoped for raw XML file text: a marker at
# the end of a <para> sits immediately before "</para>" with no
# whitespace, so the lookahead must also accept "<" as a terminator.
# False positives (statute pincites, decimals, regulatory codes) are
# filtered by _is_excluded_context() below, not by this pattern alone.
_RAW_TEXT_MARKER_RE = re.compile(r"\.(\d{1,3})(?=\s|$|<)")

# Raw-text equivalent of audit_footnote_links.py's tree-based
# _element_body_text(), which excludes <title> descendant text
# structurally (section headings are never real footnote candidates).
# This module operates on unparsed raw file text, not a parsed tree, so
# it can't reuse that function directly -- instead it locates the
# character spans of every <title>...</title> element (a fragment can
# have multiple nested sections, each with its own <title>) and skips
# any marker match that falls inside one. non-greedy .*? is correct
# here because <title> elements are never nested inside themselves, so
# stopping at the first </title> always closes the right one; re.DOTALL
# covers the (unusual but possible) case of a title's content spanning
# a newline.
_TITLE_SPAN_RE = re.compile(r"<title\b[^>]*>.*?</title\s*>", re.DOTALL)


def _title_spans(text):
    """List of (start, end) character offsets in text covering every
    <title>...</title> element. Confirmed live by
    test_marker_inside_title_element_is_not_converted (a marker inside
    one of these spans must be skipped) and
    test_marker_outside_title_still_converts_when_fragment_also_has_a_title
    (a marker outside every span, even in a fragment that also contains
    a <title>, must still convert -- this function must not be used to
    exclude more than the actual title spans)."""
    return [m.span() for m in _TITLE_SPAN_RE.finditer(text)]


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
    """Rewrites every glued "word.N" marker in fragment_path to
    "word<biblioref linkend="KEY"/>" using key_map, in place. Returns
    the number of markers actually converted -- not re.sub()'s own
    match count, which would count every candidate the regex found
    regardless of whether it was actually converted. A marker is
    excluded (left untouched, not counted) when either
    _is_excluded_context() flags it (statute pincite, regulatory code,
    decimal number) or its N has no entry in key_map (out of range /
    unrelated digit). key_map is always 1-based, so a literal ".0"
    marker never converts even if key_map somehow contains a 0 key
    (confirmed live by test_marker_number_zero_is_never_converted).

    re.sub() computes all matches against the ORIGINAL text up front
    and invokes the replacement callback once per match, with match
    objects indexed into that original (unmutated) string -- it does
    not re-scan the progressively-edited output. Two occurrences of
    the same marker number therefore both convert independently, with
    no shared mutable state that could under-convert a repeated number
    (confirmed live by
    test_same_marker_number_appears_twice_both_convert)."""
    fragment_path = Path(fragment_path)
    text = fragment_path.read_text(encoding="utf-8")
    converted = 0
    title_spans = _title_spans(text)

    def _replace(match):
        nonlocal converted
        if any(start <= match.start() < end for start, end in title_spans):
            return match.group(0)
        preceding = text[: match.start()]
        if _is_excluded_context(preceding):
            return match.group(0)
        n = int(match.group(1))
        if n not in key_map:
            return match.group(0)
        converted += 1
        prefix = match.group(0)[: -len(match.group(1))]
        return f'{prefix}<biblioref linkend="{key_map[n]}"/>'

    new_text = _RAW_TEXT_MARKER_RE.sub(_replace, text)
    fragment_path.write_text(new_text, encoding="utf-8")
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

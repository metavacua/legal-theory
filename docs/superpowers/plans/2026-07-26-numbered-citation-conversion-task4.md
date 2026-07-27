# Numbered-Citation Conversion (Task 4) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `docs/scripts/convert_numbered_citations.py`, which converts the
Deep-Research-style glued numbered-citation pattern ("word.N") in a Category-A
document into real DocBook structure: one `<biblioentry>` file per works-cited
item, and every glued marker rewritten in place to `<biblioref linkend="KEY"/>`.

**Architecture:** Three small, independently-testable functions operating on
XML fragment files: `build_entry_key_map` (parses a fragment's
`<section xml:id="works-cited">`, writes one entry file per `<listitem>` via
`citation_entry.write_biblioentry`, returns `{ordinal: key}`),
`convert_markers_in_fragment` (regex-scans a fragment's raw text for
`.N` markers, excludes false positives via `audit_footnote_links._is_excluded_context`,
rewrites genuine matches to `<biblioref>` in place), and
`remove_works_cited_section` (strips the now-redundant list from a fragment).
No new marker-detection or exclusion logic is written — exclusion logic is
imported from `audit_footnote_links.py` (already adversarially tested against
statute pincites and alphanumeric regulatory codes) rather than re-derived.

**Tech Stack:** Python 3 stdlib only (`re`, `xml.etree.ElementTree`, `pathlib`),
`unittest`.

## Global Constraints

- Reuse `audit_footnote_links.py`'s `_is_excluded_context()` for exclusion —
  do not re-derive statute-pincite/regulatory-code exclusion logic.
- Emit `<biblioref linkend="KEY"/>`, never `<citation>KEY</citation>` — the
  latter renders as inert bracketed text under both stylesheets in this repo;
  `<biblioref>` is the real DocBook 5.2 cross-reference-to-bibliography element.
- `build_entry_key_map` must be safe to call twice on the same fragment
  (idempotent) — verify this claim live, not just by reading the code.
- `convert_markers_in_fragment` must return the count of markers *actually
  converted*, not the regex's total candidate-match count.
- All new code lives in `docs/scripts/convert_numbered_citations.py` with
  tests in `docs/scripts/tests/test_convert_numbered_citations.py`, matching
  this repo's existing `docs/scripts/*.py` + `docs/scripts/tests/test_*.py`
  layout (confirmed against `citation_entry.py` / `audit_footnote_links.py`
  and their test siblings already in the tree).

---

### Task 1: `build_entry_key_map`

**Files:**
- Create: `docs/scripts/convert_numbered_citations.py`
- Test: `docs/scripts/tests/test_convert_numbered_citations.py`

**Interfaces:**
- Consumes: `citation_entry.ENTRIES_DIR`, `citation_entry.derive_entry_key(text, href=None)`,
  `citation_entry.write_biblioentry(entry_path, key, role, title, href=None)`;
  `convert_to_docbook.DB_NS`, `convert_to_docbook.XML_NS`.
- Produces: `build_entry_key_map(works_cited_fragment_path) -> dict[int, str]`
  (1-based works-cited ordinal -> entry key), used by Task 2's test setup and
  by the pilot task (not part of this plan).

- [ ] **Step 1: Write the failing test**

Create `docs/scripts/tests/test_convert_numbered_citations.py` with just the
`TestBuildEntryKeyMap` class (full file content below is added to
incrementally in later tasks; this step writes only this class plus the
shared imports):

```python
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class TestBuildEntryKeyMap(unittest.TestCase):
    def test_builds_map_and_writes_one_entry_per_listitem(self):
        from convert_numbered_citations import build_entry_key_map
        import citation_entry
        out_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, out_dir)
        original_entries_dir = citation_entry.ENTRIES_DIR
        citation_entry.ENTRIES_DIR = out_dir / "entries"
        self.addCleanup(setattr, citation_entry, "ENTRIES_DIR", original_entries_dir)
        import convert_numbered_citations
        convert_numbered_citations.ENTRIES_DIR = citation_entry.ENTRIES_DIR
        self.addCleanup(setattr, convert_numbered_citations, "ENTRIES_DIR", original_entries_dir)

        fragment = out_dir / "fragment.xml"
        fragment.write_text("""<?xml version="1.0"?>
<section xmlns="http://docbook.org/ns/docbook" xmlns:xlink="http://www.w3.org/1999/xlink" xml:id="conclusion">
  <section xml:id="works-cited">
    <orderedlist numeration="arabic" spacing="compact">
      <listitem><para>First Source, accessed June 9, 2025, <link xlink:href="https://example.com/first">https://example.com/first</link></para></listitem>
      <listitem><para>Second Source, accessed June 9, 2025, <link xlink:href="https://example.com/second">https://example.com/second</link></para></listitem>
    </orderedlist>
  </section>
</section>
""", encoding="utf-8")
        key_map = build_entry_key_map(fragment)
        self.assertEqual(len(key_map), 2)
        self.assertTrue((citation_entry.ENTRIES_DIR / f"{key_map[1]}.xml").exists())
        self.assertTrue((citation_entry.ENTRIES_DIR / f"{key_map[2]}.xml").exists())

    def test_is_idempotent_when_called_twice_on_same_fragment(self):
        """The brief claims build_entry_key_map is safe to re-run because
        write_biblioentry no-ops on identical content. Verify live: same
        fragment, called twice, must produce an identical key_map and must
        not raise (a ValueError would mean derive_entry_key/content drifted
        between calls, which would be a real bug)."""
        from convert_numbered_citations import build_entry_key_map
        import citation_entry
        out_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, out_dir)
        original_entries_dir = citation_entry.ENTRIES_DIR
        citation_entry.ENTRIES_DIR = out_dir / "entries"
        self.addCleanup(setattr, citation_entry, "ENTRIES_DIR", original_entries_dir)
        import convert_numbered_citations
        convert_numbered_citations.ENTRIES_DIR = citation_entry.ENTRIES_DIR
        self.addCleanup(setattr, convert_numbered_citations, "ENTRIES_DIR", original_entries_dir)

        fragment = out_dir / "fragment.xml"
        fragment.write_text("""<?xml version="1.0"?>
<section xmlns="http://docbook.org/ns/docbook" xmlns:xlink="http://www.w3.org/1999/xlink" xml:id="conclusion">
  <section xml:id="works-cited">
    <orderedlist numeration="arabic" spacing="compact">
      <listitem><para>First Source, accessed June 9, 2025, <link xlink:href="https://example.com/first">https://example.com/first</link></para></listitem>
    </orderedlist>
  </section>
</section>
""", encoding="utf-8")
        first = build_entry_key_map(fragment)
        second = build_entry_key_map(fragment)
        self.assertEqual(first, second)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd docs/scripts && python3 -m unittest tests.test_convert_numbered_citations -v`
Expected: `ModuleNotFoundError: No module named 'convert_numbered_citations'`

- [ ] **Step 3: Write the module header and `build_entry_key_map`**

Create `docs/scripts/convert_numbered_citations.py`:

```python
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
audit_footnote_links.py's own read-only reporting use case)."""

import re
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parent))
from convert_to_docbook import DB_NS, XML_NS  # noqa: E402
from citation_entry import ENTRIES_DIR, derive_entry_key, write_biblioentry  # noqa: E402
from audit_footnote_links import _is_excluded_context  # noqa: E402


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
    writes one entry file per listitem as a side effect (skips writing
    if a file for that key already exists, so this is safe to re-run).
    Only call this for a document already confirmed Category A -- this
    function does not itself verify the list is complete or
    trustworthy.

    Only the FIRST <section xml:id="works-cited"> found in document
    order is processed. A single fragment should never legitimately
    contain more than one (xml:id must be unique in a valid document;
    a second one would fail schema validation before this function is
    ever reached), so this is a defensive choice, not a feature."""
    root = ET.parse(works_cited_fragment_path).getroot()
    key_map = {}
    for section in root.iter(f"{{{DB_NS}}}section"):
        if section.get(f"{{{XML_NS}}}id") != "works-cited":
            continue
        for i, listitem in enumerate(section.iter(f"{{{DB_NS}}}listitem"), start=1):
            text, href = _listitem_text_and_href(listitem)
            key = derive_entry_key(text, href)
            entry_path = ENTRIES_DIR / f"{key}.xml"
            if not entry_path.exists():
                write_biblioentry(entry_path, key=key, role="secondary", title=text, href=href)
            key_map[i] = key
        break
    return key_map
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `cd docs/scripts && python3 -m unittest tests.test_convert_numbered_citations -v`
Expected: both `TestBuildEntryKeyMap` tests `PASS`.

- [ ] **Step 5: Commit**

```bash
git add docs/scripts/convert_numbered_citations.py docs/scripts/tests/test_convert_numbered_citations.py
git commit -m "feat: add build_entry_key_map for numbered-citation conversion (Task 4 part 1)"
```

---

### Task 2: `convert_markers_in_fragment`

**Files:**
- Modify: `docs/scripts/convert_numbered_citations.py`
- Modify: `docs/scripts/tests/test_convert_numbered_citations.py`

**Interfaces:**
- Consumes: `audit_footnote_links._is_excluded_context(preceding_text) -> bool`.
- Produces: `convert_markers_in_fragment(fragment_path, key_map) -> int`
  (count of markers actually converted), used by the pilot task.

- [ ] **Step 1: Write the failing tests**

Append to `docs/scripts/tests/test_convert_numbered_citations.py`:

```python
class TestConvertMarkersInFragment(unittest.TestCase):
    def _write(self, content):
        out_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, out_dir)
        path = out_dir / "fragment.xml"
        path.write_text(content, encoding="utf-8")
        return path

    def test_replaces_glued_markers_with_real_biblioref_elements(self):
        from convert_numbered_citations import convert_markers_in_fragment
        path = self._write(
            '<?xml version="1.0"?>\n'
            '<section xmlns="http://docbook.org/ns/docbook" xml:id="intro">\n'
            '  <para>LLMs process trillions of parameters.1 They exhibit long-range dependencies.2</para>\n'
            '</section>\n'
        )
        count = convert_markers_in_fragment(path, {1: "key-one", 2: "key-two"})
        self.assertEqual(count, 2)
        text = path.read_text(encoding="utf-8")
        self.assertIn('parameters.<biblioref linkend="key-one"/>', text)
        self.assertIn('dependencies.<biblioref linkend="key-two"/>', text)
        ET.parse(path)  # still well-formed

    def test_marker_outside_key_map_is_left_untouched(self):
        from convert_numbered_citations import convert_markers_in_fragment
        path = self._write(
            '<?xml version="1.0"?>\n'
            '<section xmlns="http://docbook.org/ns/docbook" xml:id="intro">\n'
            '  <para>An unrelated number.9 appears here.</para>\n'
            '</section>\n'
        )
        count = convert_markers_in_fragment(path, {1: "key-one"})
        self.assertEqual(count, 0)
        self.assertIn("number.9", path.read_text(encoding="utf-8"))

    def test_statute_pincite_is_not_converted_even_if_number_is_in_range(self):
        """Guards the exact false positive this task's first draft let
        through: a statute/rule number that happens to fall within the
        works-cited list's range must still not convert -- reusing
        audit_footnote_links.py's _is_excluded_context() is what
        prevents this, not just the key_map range check."""
        from convert_numbered_citations import convert_markers_in_fragment
        path = self._write(
            '<?xml version="1.0"?>\n'
            '<section xmlns="http://docbook.org/ns/docbook" xml:id="intro">\n'
            '  <para>SMC Corporate Practices NYSE Section 303A.01 requires disclosure.</para>\n'
            '</section>\n'
        )
        count = convert_markers_in_fragment(path, {1: "key-one"})
        self.assertEqual(count, 0)
        self.assertIn("303A.01", path.read_text(encoding="utf-8"))

    def test_same_marker_number_appears_twice_both_convert(self):
        """Bug-hunt case: the same footnote number cited twice in one
        fragment must convert at BOTH occurrences, not just the first
        (a naive implementation using str.replace(count=1) or a stateful
        already-converted guard could under-convert here)."""
        from convert_numbered_citations import convert_markers_in_fragment
        path = self._write(
            '<?xml version="1.0"?>\n'
            '<section xmlns="http://docbook.org/ns/docbook" xml:id="intro">\n'
            '  <para>First mention.3 Second mention of the same source.3</para>\n'
            '</section>\n'
        )
        count = convert_markers_in_fragment(path, {3: "key-three"})
        self.assertEqual(count, 2)
        text = path.read_text(encoding="utf-8")
        self.assertEqual(text.count('<biblioref linkend="key-three"/>'), 2)

    def test_marker_number_zero_is_never_converted(self):
        """key_map is always 1-based (works-cited ordinals start at 1),
        so a literal ".0" marker must never match, regardless of what
        key_map contains."""
        from convert_numbered_citations import convert_markers_in_fragment
        path = self._write(
            '<?xml version="1.0"?>\n'
            '<section xmlns="http://docbook.org/ns/docbook" xml:id="intro">\n'
            '  <para>Odd footnote.0 here.</para>\n'
            '</section>\n'
        )
        count = convert_markers_in_fragment(path, {0: "key-zero", 1: "key-one"})
        self.assertEqual(count, 0)
        self.assertIn("footnote.0", path.read_text(encoding="utf-8"))

    def test_three_digit_marker_number_converts_when_in_key_map(self):
        """Works-cited lists in the corpus run into the 80s; verify a
        3-digit ordinal (100) still matches and converts correctly, and
        does not get truncated to a 2-digit prefix by the regex."""
        from convert_numbered_citations import convert_markers_in_fragment
        path = self._write(
            '<?xml version="1.0"?>\n'
            '<section xmlns="http://docbook.org/ns/docbook" xml:id="intro">\n'
            '  <para>A very long list.100 indeed.</para>\n'
            '</section>\n'
        )
        count = convert_markers_in_fragment(path, {100: "key-hundred"})
        self.assertEqual(count, 1)
        self.assertIn('list.<biblioref linkend="key-hundred"/>', path.read_text(encoding="utf-8"))
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd docs/scripts && python3 -m unittest tests.test_convert_numbered_citations -v`
Expected: `ImportError: cannot import name 'convert_markers_in_fragment'` for the
new `TestConvertMarkersInFragment` tests; Task 1's tests still pass.

- [ ] **Step 3: Implement `convert_markers_in_fragment`**

Append to `docs/scripts/convert_numbered_citations.py` (insert the regex
constant right after the imports, above `_listitem_text_and_href`):

```python
# Broader than measure_citation_conformance.py's _GLUED_MARKER_RE (no
# preceding-letter requirement, matching audit_footnote_links.py's own
# _FOOTNOTE_MARKER_RE), and scoped for raw XML file text: a marker at
# the end of a <para> sits immediately before "</para>" with no
# whitespace, so the lookahead must also accept "<" as a terminator.
# False positives (statute pincites, decimals, regulatory codes) are
# filtered by _is_excluded_context() below, not by this pattern alone.
_RAW_TEXT_MARKER_RE = re.compile(r"\.(\d{1,3})(?=\s|$|<)")


def convert_markers_in_fragment(fragment_path, key_map):
    """Rewrites every glued "word.N" marker in fragment_path to
    "word<biblioref linkend="KEY"/>" using key_map, in place. Returns
    the number of markers actually converted -- not re.sub()'s own
    match count, which would count every candidate the regex found
    regardless of whether it was actually converted. A marker is
    excluded (left untouched, not counted) when either
    _is_excluded_context() flags it (statute pincite, regulatory code,
    decimal number) or its N has no entry in key_map (out of range /
    unrelated digit). key_map is always 1-based; a literal ".0" marker
    therefore never converts even if key_map somehow contains a 0 key.

    re.sub() finds all matches against the ORIGINAL text up front and
    calls the replacement callback once per match with match objects
    indexed into that original string -- it does not re-scan the
    progressively-edited output -- so two occurrences of the same
    marker number both convert independently; there is no shared
    mutable state across calls that could under-convert a repeated
    number."""
    fragment_path = Path(fragment_path)
    text = fragment_path.read_text(encoding="utf-8")
    converted = 0

    def _replace(match):
        nonlocal converted
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
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `cd docs/scripts && python3 -m unittest tests.test_convert_numbered_citations -v`
Expected: all tests so far `PASS` (2 from Task 1 + 6 from Task 2 = 8).

- [ ] **Step 5: Commit**

```bash
git add docs/scripts/convert_numbered_citations.py docs/scripts/tests/test_convert_numbered_citations.py
git commit -m "feat: add convert_markers_in_fragment for numbered-citation conversion (Task 4 part 2)"
```

---

### Task 3: `remove_works_cited_section`

**Files:**
- Modify: `docs/scripts/convert_numbered_citations.py`
- Modify: `docs/scripts/tests/test_convert_numbered_citations.py`

**Interfaces:**
- Consumes: nothing new (stdlib `ElementTree` only).
- Produces: `remove_works_cited_section(fragment_path) -> bool`, used by the
  pilot task.

- [ ] **Step 1: Write the failing tests**

Append to `docs/scripts/tests/test_convert_numbered_citations.py`:

```python
class TestRemoveWorksCitedSection(unittest.TestCase):
    def test_removes_the_section_when_present(self):
        from convert_numbered_citations import remove_works_cited_section
        path = Path(tempfile.mkdtemp()) / "fragment.xml"
        path.write_text(
            '<?xml version="1.0"?>\n'
            '<section xmlns="http://docbook.org/ns/docbook" xml:id="conclusion">\n'
            '  <para>Text.</para>\n'
            '  <section xml:id="works-cited"><orderedlist numeration="arabic"><listitem><para>X</para></listitem></orderedlist></section>\n'
            '</section>\n',
            encoding="utf-8",
        )
        removed = remove_works_cited_section(path)
        self.assertTrue(removed)
        self.assertNotIn("works-cited", path.read_text(encoding="utf-8"))

    def test_no_op_when_absent(self):
        from convert_numbered_citations import remove_works_cited_section
        path = Path(tempfile.mkdtemp()) / "fragment.xml"
        path.write_text(
            '<?xml version="1.0"?>\n'
            '<section xmlns="http://docbook.org/ns/docbook" xml:id="intro">\n'
            '  <para>Text.</para>\n'
            '</section>\n',
            encoding="utf-8",
        )
        removed = remove_works_cited_section(path)
        self.assertFalse(removed)

    def test_removes_a_direct_child_of_root_without_raising(self):
        """Bug-hunt case: root.iter() already yields root itself first.
        If the removal loop also prepended [root] before iterating (a
        plausible naive variant), the same works-cited section -- when
        it is a DIRECT child of root -- would be found twice and the
        second parent.remove(child) call would raise ValueError. This
        fragment's works-cited section is a direct child of the root
        <section>, exercising exactly that path."""
        from convert_numbered_citations import remove_works_cited_section
        path = Path(tempfile.mkdtemp()) / "fragment.xml"
        path.write_text(
            '<?xml version="1.0"?>\n'
            '<section xmlns="http://docbook.org/ns/docbook" xml:id="root">\n'
            '  <section xml:id="works-cited"><orderedlist numeration="arabic"><listitem><para>X</para></listitem></orderedlist></section>\n'
            '</section>\n',
            encoding="utf-8",
        )
        removed = remove_works_cited_section(path)
        self.assertTrue(removed)
        self.assertNotIn("works-cited", path.read_text(encoding="utf-8"))
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd docs/scripts && python3 -m unittest tests.test_convert_numbered_citations -v`
Expected: `ImportError: cannot import name 'remove_works_cited_section'` for the
new tests; Tasks 1-2's tests still pass.

- [ ] **Step 3: Implement `remove_works_cited_section`**

Append to `docs/scripts/convert_numbered_citations.py`:

```python
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
    # direct child of root (confirmed by direct testing 2026-07-26).
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
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `cd docs/scripts && python3 -m unittest tests.test_convert_numbered_citations -v`
Expected: all tests `PASS` (2 + 6 + 3 = 11).

- [ ] **Step 5: Commit**

```bash
git add docs/scripts/convert_numbered_citations.py docs/scripts/tests/test_convert_numbered_citations.py
git commit -m "feat: add remove_works_cited_section, completing numbered-citation conversion (Task 4)"
```

---

### Task 4: Grammar verification and bug hunt

**Files:** none created/modified unless the bug hunt finds a real defect (see
below).

- [ ] **Step 1: Verify `<biblioref>` against the real DocBook 5.2 grammar**

```bash
cat > /tmp/biblioref-test.xml << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<article xmlns="http://docbook.org/ns/docbook" version="5.2" xml:id="t" xml:lang="en">
  <title>T</title>
  <para>See <biblioref linkend="smith2020"/> for details.</para>
</article>
EOF
jing -c .cache/docbook-5.2/docbookxi.rnc /tmp/biblioref-test.xml && echo VALID
```
Expected: `VALID`.

- [ ] **Step 2: Full test suite regression check**

Run: `cd docs/scripts && python3 -m unittest discover tests -v 2>&1 | tail -30`
Expected: no new failures introduced in sibling test modules.

- [ ] **Step 3: Systematic-debugging bug hunt**

Invoke `superpowers:systematic-debugging` (or apply its discipline directly,
since no failing test is yet known) against these specific scenarios beyond
what Tasks 1-3's own tests already cover — each becomes a real test added to
`test_convert_numbered_citations.py` if it reveals or confirms a behavior
worth locking in, and a real fix (not a quick patch) if it reveals a bug:

1. A fragment with a SECOND `<section xml:id="works-cited">` nested inside
   the first one's sibling tree (duplicate `xml:id`, which is invalid XML but
   `ElementTree` does not enforce uniqueness) — confirm `build_entry_key_map`'s
   `break` after the first match means only the first section's listitems are
   ever mapped, and document this as deliberate, not silently wrong.
2. The "known limitation" docstring claim about
   `<emphasis>word</emphasis>.1` not being caught — trace it by hand against
   `_RAW_TEXT_MARKER_RE` and `_is_excluded_context`: the marker's `.1` sits
   immediately after `</emphasis>`, which ends in `>`, not a digit/letter, so
   `_is_excluded_context` does NOT exclude it, and `_RAW_TEXT_MARKER_RE`
   matches `.1` followed by whitespace/`<`/end normally. Confirm empirically
   with a real test whether this converts correctly or not, and correct
   whichever of (a) the code or (b) the module docstring is wrong.
3. Re-confirm `build_entry_key_map` idempotence (Task 1 Step 1's second test)
   under a THIRD call, and under a call where `ENTRIES_DIR` already has a
   *different* file at the derived key path with different content — confirm
   `write_biblioentry` raises `ValueError` as documented rather than silently
   overwriting.

- [ ] **Step 4: Self-review the diff**

```bash
git diff main --stat -- docs/scripts/convert_numbered_citations.py docs/scripts/tests/test_convert_numbered_citations.py
git log --oneline -5
```

- [ ] **Step 5: Write the task report**

Write findings (writing-plans output already saved here; test results; bug-hunt
outcome; concerns) to `.superpowers/sdd/task-4-report.md`.

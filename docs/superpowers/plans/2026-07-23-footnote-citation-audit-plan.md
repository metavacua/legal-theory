{% raw %}
# Footnote-to-Citation Audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `docs/scripts/audit_footnote_links.py`, a read-only report generator that finds
every candidate footnote-marker-to-works-cited-entry mapping across the corpus's 446 files with
orphaned footnote digits, tags each with a confidence tier (High / Medium / Needs manual triage)
and the specific reason for that tier, and writes the result to a report file. **It never modifies
a corpus document.**

**Architecture:** Bottom-up pure functions (document-order fragment resolution → structural
candidate detection → works-cited location → HTML cross-check → restart detection → confidence
scoring → report emission), reusing `docs/scripts/build_bibliography.py`'s `parse_xincludes`,
`build_backlink_map`, `extract_works_cited`, and `CODE_ABBREVIATIONS` rather than reimplementing
them. The corpus-wide run is a deliberately-invoked step (Task 11), gated by code review, a
simplify pass, and a human actually reading a sample of the report before it's considered done —
the report's whole purpose is human triage, so an unreviewed report is a contradiction in terms.

**Tech Stack:** Python 3 stdlib only (`xml.etree.ElementTree`, `re`, `csv`, `pathlib`), matching
`build_bibliography.py`'s existing toolchain — no new dependencies.

**Reference:** Design rationale, the confidence-tier model, and the (already-investigated, not
assumed) positional-correspondence evidence are in
`docs/superpowers/specs/2026-07-23-footnote-citation-audit-design.md`. Consult it for *why*.

## Global Constraints

- **Read-only.** No task in this plan writes to any file under `docs/**` except the report output
  itself (a new file, not an edit to an existing corpus document) and `docs/scripts/*`. If any
  code accidentally opens a corpus `.xml`/`.html` file in write mode, that is a plan violation.
- **Reuse, don't redefine.** Import `parse_xincludes`, `build_backlink_map`, `extract_works_cited`,
  `CODE_ABBREVIATIONS`, `WORKS_CITED_ID`, and the DocBook namespace constants
  (`DB_NS`, `XI_NS`, `XLINK_NS`, `XML_NS`) from `docs/scripts/build_bibliography.py`
  (`sys.path.insert(0, str(Path(__file__).resolve().parent))` then a normal import — matching how
  `build_bibliography.py` itself imports from `convert_to_docbook.py`).
- **Determinism.** Every directory walk uses `sorted()`. Given the same corpus state, two runs
  produce byte-identical report output.
- **Under-classify, don't over-classify.** Where a heuristic's confidence is genuinely ambiguous,
  the correct behavior is "Needs manual triage," not a forced High/Medium tier. A wrongly-High
  entry actively misleads the human reviewer; a wrongly-cautious "needs triage" entry only costs
  them a few extra seconds of reading.
- Every existing test in `docs/scripts/tests/` must still pass after every task.

## Process Discipline

- **TDD, adversarial-first.** Every detection/scoring function's tests include a deliberately
  adversarial fixture *before* the task is considered done — each task below specifies its
  adversarial case explicitly.
- **Verify after every task.** Run `python3 -m unittest discover -s docs/scripts/tests -v` after
  every task, not just the new test.
- **Systematic debugging — on "too right" as well as "too wrong."** If a test fails unexpectedly
  (not the RED step you just wrote), stop and invoke `superpowers:systematic-debugging` before
  writing more code. The same applies to suspiciously clean results: if Task 11's corpus-wide run
  produces zero "Needs manual triage" rows, that is a red flag — the design's own research
  confirmed real restart cases, degenerate bibliographies, and out-of-bounds footnotes exist in
  this corpus today, so their absence from the report means a check is silently not firing.
- **Systematic-debug every bug fix**, not just every bug — if a task's tests fail for an
  unexpected reason and get fixed, run `superpowers:systematic-debugging` on the fix itself
  before moving on, confirming the root cause was actually addressed.
- **Code review** after Task 10 (full pipeline integration-tested), before Task 11 (the real
  corpus-wide run). Dispatch a code-reviewer over the full diff from Tasks 1-10.
- **Simplify** immediately after code review passes, still before Task 11.
- **The human-reads-the-report gate is the actual completion criterion for Task 11**, not "tests
  pass" or "the script exits 0." A human must read a stratified sample of the real report (every
  "Needs manual triage" row, a sample of High and Medium rows) and judge whether the confidence
  tiers are trustworthy before this project is considered done — mirroring how the bibliography
  project's stratified human review caught a critical bug (a silent self-citation collision) that
  no automated invariant did.
- **Ask the user** before Task 11's corpus-wide run (this is the point where the tool actually
  reads all 446 files' worth of real content) and before considering the project complete. Do not
  ask before Tasks 1-10 — those are pure-function code, fully test-covered, touching no corpus
  data beyond read-only fixture-scale tests.

## File Structure

- **Create** `docs/scripts/audit_footnote_links.py` — the generator, built task-by-task below.
- **Create** `docs/scripts/tests/test_audit_footnote_links.py` — one test class per stage.
- **Create** `docs/scripts/tests/fixtures/footnote_audit/` — a small synthetic mini-corpus
  (multi-fragment documents covering the clean case, the restart case, the degenerate-bibliography
  case, and the false-positive-shape case) mirroring
  `docs/scripts/tests/fixtures/bibliography/`'s role for `test_build_bibliography.py`.
- **Create** `docs/audits/footnote-citation-audit.csv` — Task 11's real output (generated, not
  hand-written), one row per candidate across the real corpus.

---

### Task 1: Document-order fragment resolution

**Files:**
- Create: `docs/scripts/audit_footnote_links.py`
- Create: `docs/scripts/tests/fixtures/footnote_audit/doc_order/shell.xml`
- Create: `docs/scripts/tests/fixtures/footnote_audit/doc_order/shell/01-frag-a.xml`
- Create: `docs/scripts/tests/fixtures/footnote_audit/doc_order/shell/02-frag-b.xml`
- Create: `docs/scripts/tests/fixtures/footnote_audit/doc_order/shell/frag-a-nested.xml`
- Test: `docs/scripts/tests/test_audit_footnote_links.py`

**Interfaces:**
- Produces: `document_content_files(shell_path: Path) -> list[Path]` — `shell_path` itself,
  followed by every file it transitively `xi:include`s, in **document order** (the order
  `xi:include` elements appear in the source, resolved recursively), not the arbitrary order
  `build_backlink_map`'s reverse-index dict happens to iterate in.

- [ ] **Step 1: Create the fixture — a shell with two fragments, one of which nests a further include**

`docs/scripts/tests/fixtures/footnote_audit/doc_order/shell.xml`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<article xmlns="http://docbook.org/ns/docbook" xmlns:xi="http://www.w3.org/2001/XInclude" xml:id="shell" xml:lang="en">
  <title>Shell</title>
  <xi:include href="shell/01-frag-a.xml"/>
  <xi:include href="shell/02-frag-b.xml"/>
</article>
```

`docs/scripts/tests/fixtures/footnote_audit/doc_order/shell/01-frag-a.xml`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<section xmlns="http://docbook.org/ns/docbook" xmlns:xi="http://www.w3.org/2001/XInclude" xml:id="frag-a">
  <title>Fragment A</title>
  <para>Body A.</para>
  <xi:include href="frag-a-nested.xml"/>
</section>
```

`docs/scripts/tests/fixtures/footnote_audit/doc_order/shell/frag-a-nested.xml`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<section xmlns="http://docbook.org/ns/docbook" xml:id="frag-a-nested">
  <title>Nested</title>
  <para>Nested body.</para>
</section>
```

`docs/scripts/tests/fixtures/footnote_audit/doc_order/shell/02-frag-b.xml`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<section xmlns="http://docbook.org/ns/docbook" xml:id="frag-b">
  <title>Fragment B</title>
  <para>Body B.</para>
</section>
```

- [ ] **Step 2: Write the failing test**

```python
# docs/scripts/tests/test_audit_footnote_links.py
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "footnote_audit"


class TestDocumentContentFiles(unittest.TestCase):
    def test_resolves_document_order_including_a_nested_include(self):
        from audit_footnote_links import document_content_files
        shell = FIXTURES / "doc_order" / "shell.xml"
        files = document_content_files(shell)
        names = [f.name for f in files]
        self.assertEqual(names, ["shell.xml", "01-frag-a.xml", "frag-a-nested.xml", "02-frag-b.xml"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd docs/scripts/tests && python3 -m unittest test_audit_footnote_links -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'audit_footnote_links'`

- [ ] **Step 4: Write minimal implementation**

```python
# docs/scripts/audit_footnote_links.py
"""Read-only audit of the corpus's orphaned footnote-number markers
against their candidate works-cited entries. Writes a report; never
modifies a corpus document. See
docs/superpowers/specs/2026-07-23-footnote-citation-audit-design.md."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_bibliography import (  # noqa: E402
    DB_NS, XI_NS, XLINK_NS, XML_NS,
    REPO_ROOT, parse_xincludes, build_backlink_map, extract_works_cited,
    CODE_ABBREVIATIONS,
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
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd docs/scripts/tests && python3 -m unittest test_audit_footnote_links -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add docs/scripts/audit_footnote_links.py docs/scripts/tests/test_audit_footnote_links.py docs/scripts/tests/fixtures/footnote_audit/
git commit -m "feat: document-order fragment resolution for footnote audit"
```

---

### Task 2: Structural candidate detection within a single file

**Files:**
- Modify: `docs/scripts/audit_footnote_links.py`
- Create: `docs/scripts/tests/fixtures/footnote_audit/candidates_sample.xml`
- Test: `docs/scripts/tests/test_audit_footnote_links.py`

**Interfaces:**
- Consumes: `CODE_ABBREVIATIONS` (imported).
- Produces:
  ```python
  @dataclass
  class Candidate:
      number: int
      context: str        # up to ~80 chars of body text immediately around the marker
  ```
  `find_candidates(xml_path: Path) -> list[Candidate]` — every glued footnote-shaped digit run
  in `xml_path`'s body content (never inside `<title>`), excluding statute pincites and
  Rule/Section/Article labels, in document order.

- [ ] **Step 1: Create the fixture covering the happy path and all three false-positive shapes**

`docs/scripts/tests/fixtures/footnote_audit/candidates_sample.xml`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<section xmlns="http://docbook.org/ns/docbook" xml:id="candidates-sample">
  <title>2.1 A Section Title That Looks Like a Footnote</title>
  <para>A real citation to <emphasis>Dynamex Operations West, Inc. v. Superior Court</emphasis>.4 follows here.</para>
  <para>A pincite to Family Code § 6751.1 must not be mistaken for a footnote.</para>
  <para>See Rule 2.3 for the procedural requirement, which is not a footnote either.</para>
  <para>A second real footnote appears here.12 and continues.</para>
</section>
```

- [ ] **Step 2: Write the failing tests**

```python
class TestFindCandidates(unittest.TestCase):
    def test_finds_real_footnotes_only_not_title_pincite_or_rule_label(self):
        from audit_footnote_links import find_candidates
        candidates = find_candidates(FIXTURES / "candidates_sample.xml")
        numbers = [c.number for c in candidates]
        self.assertEqual(numbers, [4, 12])

    def test_context_captures_text_around_the_marker(self):
        from audit_footnote_links import find_candidates
        candidates = find_candidates(FIXTURES / "candidates_sample.xml")
        self.assertIn("Dynamex", candidates[0].context)
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `cd docs/scripts/tests && python3 -m unittest test_audit_footnote_links -v`
Expected: FAIL with `ImportError: cannot import name 'find_candidates'`

- [ ] **Step 4: Write minimal implementation**

```python
import re
from dataclasses import dataclass

_FOOTNOTE_MARKER_RE = re.compile(r"\.(\d{1,3})(?=[\s]|$)")
_LABEL_EXCLUSION_RE = re.compile(r"\b(?:Rule|Section|Article)\s*$", re.IGNORECASE)
_CODE_NAME_EXCLUSION_RE = re.compile(
    r"(?:§|" + "|".join(re.escape(k) for k in CODE_ABBREVIATIONS) + r")\s*$",
    re.IGNORECASE,
)


@dataclass
class Candidate:
    number: int
    context: str
    heading_collision: bool = False


def _is_excluded_context(preceding_text):
    """True if the text immediately before a candidate marker signals
    a statute pincite or a Rule/Section/Article label rather than a
    real footnote."""
    tail = preceding_text[-40:]
    return bool(_LABEL_EXCLUSION_RE.search(tail) or _CODE_NAME_EXCLUSION_RE.search(tail))


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
    import xml.etree.ElementTree as ET
    root = ET.parse(xml_path).getroot()
    text = _element_body_text(root)
    candidates = []
    for m in _FOOTNOTE_MARKER_RE.finditer(text):
        preceding = text[:m.start()]
        if _is_excluded_context(preceding):
            continue
        number = int(m.group(1))
        start = max(0, m.start() - 40)
        end = min(len(text), m.end() + 20)
        context = " ".join(text[start:end].split())
        candidates.append(Candidate(number=number, context=context))
    return candidates
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd docs/scripts/tests && python3 -m unittest test_audit_footnote_links -v`
Expected: PASS

- [ ] **Step 6: Run full suite, then commit**

```bash
python3 -m unittest discover -s docs/scripts/tests -v
git add docs/scripts/audit_footnote_links.py docs/scripts/tests/
git commit -m "feat: structural footnote-candidate detection with statute/rule/title exclusions"
```

---

### Task 3: Works-cited entry locator and degenerate-bibliography detection

**Files:**
- Modify: `docs/scripts/audit_footnote_links.py`
- Create: `docs/scripts/tests/fixtures/footnote_audit/works_cited_doc/shell.xml`
- Create: `docs/scripts/tests/fixtures/footnote_audit/works_cited_doc/shell/01-body.xml`
- Create: `docs/scripts/tests/fixtures/footnote_audit/works_cited_doc/shell/02-works-cited.xml`
- Create: `docs/scripts/tests/fixtures/footnote_audit/degenerate_doc/shell.xml`
- Test: `docs/scripts/tests/test_audit_footnote_links.py`

**Interfaces:**
- Consumes: `document_content_files` (Task 1), `extract_works_cited` (imported).
- Produces: `locate_works_cited(content_files: list[Path]) -> list[tuple[str, str | None]]` —
  the works-cited `(text, href)` entries in order from whichever content file has them (empty
  list if none). `is_degenerate(entries: list[tuple[str, str | None]], max_footnote: int) -> bool`
  — True if the list has no real (linked) entries at all, or its length is implausibly short
  relative to the highest footnote number referencing it (fewer than half the entries needed to
  cover `max_footnote`).

- [ ] **Step 1: Create the fixtures**

`docs/scripts/tests/fixtures/footnote_audit/works_cited_doc/shell.xml`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<article xmlns="http://docbook.org/ns/docbook" xmlns:xi="http://www.w3.org/2001/XInclude" xml:id="wc-doc" xml:lang="en">
  <title>WC Doc</title>
  <xi:include href="shell/01-body.xml"/>
  <xi:include href="shell/02-works-cited.xml"/>
</article>
```

`docs/scripts/tests/fixtures/footnote_audit/works_cited_doc/shell/01-body.xml`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<section xmlns="http://docbook.org/ns/docbook" xml:id="body">
  <title>Body</title>
  <para>Some text.1</para>
</section>
```

`docs/scripts/tests/fixtures/footnote_audit/works_cited_doc/shell/02-works-cited.xml`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<section xmlns="http://docbook.org/ns/docbook" xmlns:xlink="http://www.w3.org/1999/xlink" xml:id="works-cited">
  <title>Works cited</title>
  <orderedlist numeration="arabic" spacing="compact">
    <listitem><para>First source <link xlink:href="https://example.com/a">https://example.com/a</link></para></listitem>
  </orderedlist>
</section>
```

`docs/scripts/tests/fixtures/footnote_audit/degenerate_doc/shell.xml` (72-style case: many
footnotes, one fake linkless entry):
```xml
<?xml version="1.0" encoding="UTF-8"?>
<article xmlns="http://docbook.org/ns/docbook" xml:id="degenerate-doc" xml:lang="en">
  <title>Degenerate Doc</title>
  <section xml:id="body">
    <title>Body</title>
    <para>Text.1 more text.1 more.1</para>
  </section>
  <section xml:id="works-cited">
    <title>Works cited</title>
    <orderedlist numeration="arabic" spacing="compact">
      <listitem><para>Bare Title With No Link</para></listitem>
    </orderedlist>
  </section>
</article>
```

- [ ] **Step 2: Write the failing tests**

```python
class TestLocateWorksCited(unittest.TestCase):
    def test_finds_entries_in_whichever_fragment_has_them(self):
        from audit_footnote_links import document_content_files, locate_works_cited
        files = document_content_files(FIXTURES / "works_cited_doc" / "shell.xml")
        entries = locate_works_cited(files)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0][1], "https://example.com/a")

    def test_empty_when_no_works_cited_section_present(self):
        from audit_footnote_links import document_content_files, locate_works_cited
        files = document_content_files(FIXTURES / "doc_order" / "shell.xml")
        self.assertEqual(locate_works_cited(files), [])


class TestIsDegenerate(unittest.TestCase):
    def test_single_linkless_entry_against_many_footnotes_is_degenerate(self):
        from audit_footnote_links import is_degenerate
        entries = [("Bare Title With No Link", None)]
        self.assertTrue(is_degenerate(entries, max_footnote=72))

    def test_well_populated_linked_list_is_not_degenerate(self):
        from audit_footnote_links import is_degenerate
        entries = [(f"Source {i}", f"https://example.com/{i}") for i in range(1, 11)]
        self.assertFalse(is_degenerate(entries, max_footnote=10))
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `cd docs/scripts/tests && python3 -m unittest test_audit_footnote_links -v`
Expected: FAIL with `ImportError`

- [ ] **Step 4: Write minimal implementation**

```python
def locate_works_cited(content_files):
    for f in content_files:
        entries = extract_works_cited(f)
        if entries:
            return entries
    return []


def is_degenerate(entries, max_footnote):
    if max_footnote == 0:
        return False
    linked = [e for e in entries if e[1]]
    if not linked:
        return True
    return len(entries) < max(1, max_footnote // 2)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd docs/scripts/tests && python3 -m unittest test_audit_footnote_links -v`
Expected: PASS

- [ ] **Step 6: Run full suite, then commit**

```bash
python3 -m unittest discover -s docs/scripts/tests -v
git add docs/scripts/audit_footnote_links.py docs/scripts/tests/
git commit -m "feat: works-cited entry locator and degenerate-bibliography detection"
```

---

### Task 4: HTML cross-check

**Files:**
- Modify: `docs/scripts/audit_footnote_links.py`
- Create: `docs/scripts/tests/fixtures/footnote_audit/html_check/doc.html`
- Test: `docs/scripts/tests/test_audit_footnote_links.py`

**Interfaces:**
- Produces: `is_inside_heading(html_path: Path, marker_text: str) -> bool` — True if
  `marker_text` (e.g. `".4"`) appears only inside an `<h1>`-`<h6>` element in the built HTML,
  False if it appears in body text (a `<p>` or similar), used as a second, independently-derived
  signal that a candidate is real body content, not a section-heading number the XML-side
  `<title>` exclusion should already have caught.

- [ ] **Step 1: Create the fixture — one heading-only occurrence, one body occurrence**

`docs/scripts/tests/fixtures/footnote_audit/html_check/doc.html`:
```html
<!DOCTYPE html>
<html><body>
<h2>2.1 A Section Heading</h2>
<p>Real citation text.4 continues here.</p>
</body></html>
```

- [ ] **Step 2: Write the failing tests**

```python
class TestIsInsideHeading(unittest.TestCase):
    def test_body_paragraph_marker_is_not_inside_a_heading(self):
        from audit_footnote_links import is_inside_heading
        self.assertFalse(is_inside_heading(FIXTURES / "html_check" / "doc.html", ".4"))

    def test_heading_number_is_inside_a_heading(self):
        from audit_footnote_links import is_inside_heading
        self.assertTrue(is_inside_heading(FIXTURES / "html_check" / "doc.html", "2.1"))
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `cd docs/scripts/tests && python3 -m unittest test_audit_footnote_links -v`
Expected: FAIL with `ImportError`

- [ ] **Step 4: Write minimal implementation**

```python
import html.parser


class _HeadingTextCollector(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.heading_depth = 0
        self.heading_text = []
        self.body_text = []

    def handle_starttag(self, tag, attrs):
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self.heading_depth += 1

    def handle_endtag(self, tag):
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self.heading_depth = max(0, self.heading_depth - 1)

    def handle_data(self, data):
        (self.heading_text if self.heading_depth > 0 else self.body_text).append(data)


def is_inside_heading(html_path, marker_text):
    parser = _HeadingTextCollector()
    parser.feed(Path(html_path).read_text(encoding="utf-8"))
    in_heading = marker_text in "".join(parser.heading_text)
    in_body = marker_text in "".join(parser.body_text)
    return in_heading and not in_body
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd docs/scripts/tests && python3 -m unittest test_audit_footnote_links -v`
Expected: PASS

- [ ] **Step 6: Run full suite, then commit**

```bash
python3 -m unittest discover -s docs/scripts/tests -v
git add docs/scripts/audit_footnote_links.py docs/scripts/tests/
git commit -m "feat: HTML cross-check as an independent second signal against heading numbers"
```

---

### Task 5: Per-document candidate aggregation

**Files:**
- Modify: `docs/scripts/audit_footnote_links.py`
- Create: `docs/scripts/tests/fixtures/footnote_audit/full_doc/shell.xml`
- Create: `docs/scripts/tests/fixtures/footnote_audit/full_doc/shell.html`
- Create: `docs/scripts/tests/fixtures/footnote_audit/full_doc/shell/01-body.xml`
- Create: `docs/scripts/tests/fixtures/footnote_audit/full_doc/shell/02-works-cited.xml`
- Test: `docs/scripts/tests/test_audit_footnote_links.py`

**Interfaces:**
- Consumes: `document_content_files` (Task 1), `find_candidates` (Task 2), `locate_works_cited`/
  `is_degenerate` (Task 3), `is_inside_heading` (Task 4), `build_backlink_map` (imported).
- Produces:
  ```python
  @dataclass
  class DocumentAudit:
      shell_html: str                 # repo-relative .html of the shell
      candidates: list[Candidate]     # in document order, across all content files
      works_cited: list[tuple[str, str | None]]
      degenerate: bool
  ```
  `audit_document(shell_path: Path, backlinks: dict) -> DocumentAudit` — walks the whole
  document (Task 1), collects candidates from every content file (Task 2), cross-checks each
  against the shell's own built HTML (Task 4) and marks (never drops — see Global Constraints:
  under-classify, don't silently lose data) any candidate the cross-check flags as heading-only
  via `Candidate.heading_collision`, locates works-cited (Task 3), and computes degeneracy.

- [ ] **Step 1: Create the fixture — a realistic small document**

`docs/scripts/tests/fixtures/footnote_audit/full_doc/shell.xml`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<article xmlns="http://docbook.org/ns/docbook" xmlns:xi="http://www.w3.org/2001/XInclude" xml:id="full-doc" xml:lang="en">
  <title>Full Doc</title>
  <xi:include href="shell/01-body.xml"/>
  <xi:include href="shell/02-works-cited.xml"/>
</article>
```

`docs/scripts/tests/fixtures/footnote_audit/full_doc/shell/01-body.xml`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<section xmlns="http://docbook.org/ns/docbook" xml:id="body">
  <title>2.1 A Heading That Looks Like a Footnote</title>
  <para>Real citation text.4 follows.</para>
</section>
```

`docs/scripts/tests/fixtures/footnote_audit/full_doc/shell/02-works-cited.xml`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<section xmlns="http://docbook.org/ns/docbook" xmlns:xlink="http://www.w3.org/1999/xlink" xml:id="works-cited">
  <title>Works cited</title>
  <orderedlist numeration="arabic" spacing="compact">
    <listitem><para>First</para></listitem>
    <listitem><para>Second</para></listitem>
    <listitem><para>Third</para></listitem>
    <listitem><para>Fourth <link xlink:href="https://example.com/four">https://example.com/four</link></para></listitem>
  </orderedlist>
</section>
```

`docs/scripts/tests/fixtures/footnote_audit/full_doc/shell.html` (the built HTML the real
pipeline would have produced — heading rendered as `<h2>`, body as `<p>`, matching what
`html5.xsl` already does):
```html
<!DOCTYPE html>
<html><body>
<h2>2.1 A Heading That Looks Like a Footnote</h2>
<p>Real citation text.4 follows.</p>
</body></html>
```

- [ ] **Step 2: Write the failing tests, including the adversarial "flag not drop" case**

Also add a second fixture pair proving a heading-collision candidate is *retained, flagged* —
not silently dropped (the bug this task must not reintroduce):

`docs/scripts/tests/fixtures/footnote_audit/full_doc_collision/shell.xml`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<article xmlns="http://docbook.org/ns/docbook" xml:id="full-doc-collision" xml:lang="en">
  <title>Full Doc Collision</title>
  <section xml:id="body">
    <title>Body</title>
    <para>Real citation text.9 follows, and elsewhere a table cell reads "Item 9".</para>
  </section>
  <section xml:id="works-cited">
    <title>Works cited</title>
    <orderedlist numeration="arabic" spacing="compact">
      <listitem><para>Filler</para></listitem>
      <listitem><para>Filler</para></listitem>
      <listitem><para>Filler</para></listitem>
      <listitem><para>Filler</para></listitem>
      <listitem><para>Filler</para></listitem>
      <listitem><para>Filler</para></listitem>
      <listitem><para>Filler</para></listitem>
      <listitem><para>Filler</para></listitem>
      <listitem><para>Ninth Source <link xmlns:xlink="http://www.w3.org/1999/xlink" xlink:href="https://example.com/nine">https://example.com/nine</link></para></listitem>
    </orderedlist>
  </section>
</article>
```

`docs/scripts/tests/fixtures/footnote_audit/full_doc_collision/shell.html` (deliberately
contrived: the literal substring ".9" also happens to appear inside an unrelated `<h2>`
elsewhere in the same document, simulating a coincidental cross-check collision):
```html
<!DOCTYPE html>
<html><body>
<h2>Table row count.9 unrelated heading text</h2>
<p>Real citation text.9 follows, and elsewhere a table cell reads "Item 9".</p>
</body></html>
```

```python
class TestAuditDocument(unittest.TestCase):
    def test_audits_a_full_document_end_to_end(self):
        from audit_footnote_links import audit_document, build_backlink_map
        root = FIXTURES / "full_doc"
        shell = root / "shell.xml"
        backlinks = build_backlink_map(root)
        result = audit_document(shell, backlinks)

        self.assertEqual(len(result.candidates), 1)
        self.assertEqual(result.candidates[0].number, 4)
        self.assertEqual(len(result.works_cited), 4)
        self.assertFalse(result.degenerate)
        self.assertTrue(result.shell_html.endswith("full_doc/shell.html"))

    def test_heading_collision_is_flagged_not_dropped(self):
        # Adversarial: the marker text also happens to appear inside an
        # unrelated heading. It must survive into audit.candidates with
        # heading_collision=True -- NOT silently disappear. A dropped
        # candidate is invisible to the human reviewer, which is a worse
        # failure than a flagged one per this plan's own Global Constraints.
        from audit_footnote_links import audit_document, build_backlink_map
        root = FIXTURES / "full_doc_collision"
        shell = root / "shell.xml"
        backlinks = build_backlink_map(root)
        result = audit_document(shell, backlinks)

        self.assertEqual(len(result.candidates), 1)
        self.assertEqual(result.candidates[0].number, 9)
        self.assertTrue(result.candidates[0].heading_collision)
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd docs/scripts/tests && python3 -m unittest test_audit_footnote_links -v`
Expected: FAIL with `ImportError`

- [ ] **Step 4: Write minimal implementation**

```python
from dataclasses import dataclass, field


@dataclass
class DocumentAudit:
    shell_html: str
    candidates: list
    works_cited: list
    degenerate: bool


def audit_document(shell_path, backlinks):
    shell_path = Path(shell_path)
    shell_html = backlinks.get(shell_path.resolve())
    html_path = REPO_ROOT / shell_html if shell_html else None

    content_files = document_content_files(shell_path)
    candidates = []
    for f in content_files:
        for c in find_candidates(f):
            marker_text = f".{c.number}"
            if html_path and html_path.is_file() and is_inside_heading(html_path, marker_text):
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
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd docs/scripts/tests && python3 -m unittest test_audit_footnote_links -v`
Expected: PASS

- [ ] **Step 6: Run full suite, then commit**

```bash
python3 -m unittest discover -s docs/scripts/tests -v
git add docs/scripts/audit_footnote_links.py docs/scripts/tests/
git commit -m "feat: per-document candidate aggregation combining detection, HTML cross-check, and works-cited location"
```

---

### Task 6: Restart detection

**Files:**
- Modify: `docs/scripts/audit_footnote_links.py`
- Test: `docs/scripts/tests/test_audit_footnote_links.py`

**Interfaces:**
- Produces: `detect_restart_index(numbers: list[int]) -> int | None` — the index into `numbers`
  (document-order candidate sequence) where a restart begins (the sequence drops from a high
  value to a low one and stays low for multiple subsequent markers, rather than a single-value
  dip consistent with ordinary reuse), or `None` if no restart is detected.

- [ ] **Step 1: Write the failing tests, including the adversarial "heavy reuse, no restart" case**

```python
class TestDetectRestartIndex(unittest.TestCase):
    def test_no_restart_in_a_monotonic_sequence(self):
        from audit_footnote_links import detect_restart_index
        self.assertIsNone(detect_restart_index([1, 2, 3, 4, 158, 226, 244, 245, 246, 267]))

    def test_detects_a_real_restart_confirmed_shape(self):
        # Matches the confirmed real case: climbs to 267, then drops to
        # low integers and stays low for several subsequent markers.
        from audit_footnote_links import detect_restart_index
        numbers = [158, 226, 244, 245, 246, 267, 2, 2, 1, 3, 3, 3, 3, 3, 4, 4, 7, 3, 2, 3]
        idx = detect_restart_index(numbers)
        self.assertIsNotNone(idx)
        self.assertEqual(idx, 6)  # the first "2" after 267

    def test_heavy_reuse_of_low_numbers_is_not_mistaken_for_a_restart(self):
        # Adversarial: footnote "1" reused 9 times is normal (confirmed
        # real corpus behavior), not a restart -- there is no preceding
        # HIGH value for it to have dropped from.
        from audit_footnote_links import detect_restart_index
        numbers = [1, 1, 1, 7, 1, 1, 18, 18, 18, 18, 18, 18, 25, 30, 1, 1]
        self.assertIsNone(detect_restart_index(numbers))

    def test_single_low_outlier_amid_a_high_run_is_not_a_restart(self):
        # A single dip (ordinary out-of-order reuse) must not trigger --
        # only a drop that STAYS low for multiple subsequent markers does.
        from audit_footnote_links import detect_restart_index
        numbers = [100, 101, 102, 3, 103, 104, 105]
        self.assertIsNone(detect_restart_index(numbers))
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd docs/scripts/tests && python3 -m unittest test_audit_footnote_links -v`
Expected: FAIL with `ImportError`

- [ ] **Step 3: Write minimal implementation**

```python
_RESTART_DROP_THRESHOLD = 20   # preceding value must exceed the dip by at least this much
_RESTART_LOW_CEILING = 10      # the dip value itself must be at or below this
_RESTART_RUN_LENGTH = 3        # at least this many subsequent values must also stay low


def detect_restart_index(numbers):
    for i in range(1, len(numbers)):
        prev, cur = numbers[i - 1], numbers[i]
        if cur > _RESTART_LOW_CEILING or prev - cur < _RESTART_DROP_THRESHOLD:
            continue
        window = numbers[i:i + _RESTART_RUN_LENGTH]
        if len(window) == _RESTART_RUN_LENGTH and all(n <= _RESTART_LOW_CEILING * 2 for n in window):
            return i
    return None
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd docs/scripts/tests && python3 -m unittest test_audit_footnote_links -v`
Expected: PASS

**Note for the implementer:** if any of the 4 tests don't pass with this exact threshold
combination, tune `_RESTART_DROP_THRESHOLD`/`_RESTART_LOW_CEILING`/`_RESTART_RUN_LENGTH` — the
spec explicitly leaves exact thresholds as an implementation decision (design doc §6), the
requirement is that all 4 tests (real restart detected, monotonic sequence clean, heavy
low-number reuse clean, single-outlier dip clean) pass together, not that these exact numbers are
sacred.

- [ ] **Step 5: Run full suite, then commit**

```bash
python3 -m unittest discover -s docs/scripts/tests -v
git add docs/scripts/audit_footnote_links.py docs/scripts/tests/
git commit -m "feat: restart detection for mid-document footnote renumbering"
```

---

### Task 7: Confidence scoring

**Files:**
- Modify: `docs/scripts/audit_footnote_links.py`
- Test: `docs/scripts/tests/test_audit_footnote_links.py`

**Interfaces:**
- Consumes: `DocumentAudit` (Task 5), `detect_restart_index` (Task 6).
- Produces:
  ```python
  @dataclass
  class AuditRow:
      candidate: Candidate
      matched_entry_text: str | None
      matched_entry_url: str | None
      confidence: str          # "High" | "Medium" | "Needs manual triage"
      flags: list[str]         # subset of restart_detected, exceeds_length, no_link_corroboration, degenerate_bibliography, possible_heading_collision
  ```
  `score_document(audit: DocumentAudit) -> list[AuditRow]` — one row per candidate, per the
  design's §5 tier rules.

- [ ] **Step 1: Write the failing tests, one per tier plus the compounding-flags adversarial case**

```python
class TestScoreDocument(unittest.TestCase):
    def _audit(self, candidates, works_cited, degenerate=False):
        from audit_footnote_links import DocumentAudit
        return DocumentAudit(shell_html="docs/x.html", candidates=candidates, works_cited=works_cited, degenerate=degenerate)

    def test_high_confidence_linked_entry_no_restart(self):
        from audit_footnote_links import score_document, Candidate
        audit = self._audit(
            [Candidate(number=1, context="ctx")],
            [("Real Source", "https://example.com/a")],
        )
        rows = score_document(audit)
        self.assertEqual(rows[0].confidence, "High")
        self.assertEqual(rows[0].matched_entry_url, "https://example.com/a")

    def test_medium_confidence_when_entry_has_no_link(self):
        from audit_footnote_links import score_document, Candidate
        audit = self._audit(
            [Candidate(number=1, context="ctx")],
            [("Plausible Title, No Link", None)],
        )
        rows = score_document(audit)
        self.assertEqual(rows[0].confidence, "Medium")
        self.assertIn("no_link_corroboration", rows[0].flags)

    def test_needs_triage_when_footnote_exceeds_works_cited_length(self):
        from audit_footnote_links import score_document, Candidate
        audit = self._audit([Candidate(number=99, context="ctx")], [("Only One", "https://example.com/a")])
        rows = score_document(audit)
        self.assertEqual(rows[0].confidence, "Needs manual triage")
        self.assertIn("exceeds_length", rows[0].flags)

    def test_needs_triage_when_document_is_degenerate_regardless_of_other_signals(self):
        from audit_footnote_links import score_document, Candidate
        audit = self._audit(
            [Candidate(number=1, context="ctx")],
            [("Real Source", "https://example.com/a")],
            degenerate=True,
        )
        rows = score_document(audit)
        self.assertEqual(rows[0].confidence, "Needs manual triage")
        self.assertIn("degenerate_bibliography", rows[0].flags)

    def test_heading_collision_forces_needs_manual_triage(self):
        from audit_footnote_links import score_document, Candidate
        audit = self._audit(
            [Candidate(number=1, context="ctx", heading_collision=True)],
            [("Real Source", "https://example.com/a")],
        )
        rows = score_document(audit)
        self.assertEqual(rows[0].confidence, "Needs manual triage")
        self.assertIn("possible_heading_collision", rows[0].flags)

    def test_restart_downgrades_everything_from_its_index_onward(self):
        from audit_footnote_links import score_document, Candidate
        works_cited = [(f"Source {i}", f"https://example.com/{i}") for i in range(1, 6)]
        candidates = [Candidate(number=n, context="ctx") for n in [1, 2, 3, 100, 1, 1, 1]]
        audit = self._audit(candidates, works_cited)
        rows = score_document(audit)
        # First three (1,2,3) precede any restart signal and should be High;
        # the restart is only detectable once the sequence actually drops
        # back down after climbing -- rows at/after that point are downgraded.
        self.assertEqual(rows[0].confidence, "High")
        restart_flagged = [r for r in rows if "restart_detected" in r.flags]
        self.assertTrue(restart_flagged)
        for r in restart_flagged:
            self.assertNotEqual(r.confidence, "High")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd docs/scripts/tests && python3 -m unittest test_audit_footnote_links -v`
Expected: FAIL with `ImportError`

- [ ] **Step 3: Write minimal implementation**

```python
@dataclass
class AuditRow:
    candidate: object
    matched_entry_text: object
    matched_entry_url: object
    confidence: str
    flags: list


def score_document(audit):
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

        if "exceeds_length" in flags or "degenerate_bibliography" in flags or "possible_heading_collision" in flags:
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd docs/scripts/tests && python3 -m unittest test_audit_footnote_links -v`
Expected: PASS

- [ ] **Step 5: Run full suite, then commit**

```bash
python3 -m unittest discover -s docs/scripts/tests -v
git add docs/scripts/audit_footnote_links.py docs/scripts/tests/
git commit -m "feat: confidence-tier scoring combining link corroboration, restart, bounds, and degeneracy signals"
```

---

### Task 8: Report row construction and CSV emission

**Files:**
- Modify: `docs/scripts/audit_footnote_links.py`
- Test: `docs/scripts/tests/test_audit_footnote_links.py`

**Interfaces:**
- Consumes: `AuditRow` (Task 7).
- Produces: `write_report(rows_by_shell: dict[str, list[AuditRow]], out_path: Path) -> None` —
  writes a CSV with columns `file, footnote_number, body_context_snippet,
  matched_works_cited_entry, matched_works_cited_url, confidence_tier, flags` (design §8),
  `flags` joined with `;`, rows sorted by `(file, footnote_number)` for determinism.

- [ ] **Step 1: Write the failing test**

```python
class TestWriteReport(unittest.TestCase):
    def test_writes_expected_csv_columns_and_deterministic_order(self):
        import csv
        from audit_footnote_links import write_report, AuditRow, Candidate
        rows_by_shell = {
            "docs/b.html": [AuditRow(candidate=Candidate(number=2, context="b ctx"),
                                       matched_entry_text="B", matched_entry_url="https://example.com/b",
                                       confidence="High", flags=[])],
            "docs/a.html": [AuditRow(candidate=Candidate(number=1, context="a ctx"),
                                       matched_entry_text=None, matched_entry_url=None,
                                       confidence="Needs manual triage", flags=["exceeds_length"])],
        }
        out = FIXTURES / "report_out.csv"
        write_report(rows_by_shell, out)
        with open(out, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        self.assertEqual(rows[0]["file"], "docs/a.html")
        self.assertEqual(rows[1]["file"], "docs/b.html")
        self.assertEqual(rows[0]["flags"], "exceeds_length")
        out.unlink()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd docs/scripts/tests && python3 -m unittest test_audit_footnote_links -v`
Expected: FAIL with `ImportError`

- [ ] **Step 3: Write minimal implementation**

```python
import csv

_REPORT_FIELDS = [
    "file", "footnote_number", "body_context_snippet",
    "matched_works_cited_entry", "matched_works_cited_url",
    "confidence_tier", "flags",
]


def write_report(rows_by_shell, out_path):
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd docs/scripts/tests && python3 -m unittest test_audit_footnote_links -v`
Expected: PASS

- [ ] **Step 5: Run full suite, then commit**

```bash
python3 -m unittest discover -s docs/scripts/tests -v
git add docs/scripts/audit_footnote_links.py docs/scripts/tests/
git commit -m "feat: deterministic CSV report emission"
```

---

### Task 9: CLI wiring (`main()`)

**Files:**
- Modify: `docs/scripts/audit_footnote_links.py`
- Test: `docs/scripts/tests/test_audit_footnote_links.py`

**Interfaces:**
- Consumes: everything from Tasks 1-8.
- Produces: `main(argv=None) -> int` — walks `docs/` (excluding `docs/papers`, `docs/scripts`,
  `docs/scratch`, `docs/bibliography`), finds every shell article, runs `audit_document` +
  `score_document` on each, writes `docs/audits/footnote-citation-audit.csv`, prints a one-line
  summary (counts per confidence tier). This task's own test does NOT run against the real
  corpus (that is Task 11) — it runs `main()` against a small fixture corpus and confirms the
  file gets written with the right shape.

- [ ] **Step 1: Create a tiny fixture corpus reusing prior fixtures' shape**

`docs/scripts/tests/fixtures/footnote_audit/mini_corpus/doc.xml`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<article xmlns="http://docbook.org/ns/docbook" xml:id="mini-doc" xml:lang="en">
  <title>Mini Doc</title>
  <section xml:id="body">
    <title>Body</title>
    <para>Citation text.1 here.</para>
  </section>
  <section xml:id="works-cited">
    <title>Works cited</title>
    <orderedlist numeration="arabic" spacing="compact">
      <listitem><para>Source One <link xmlns:xlink="http://www.w3.org/1999/xlink" xlink:href="https://example.com/1">https://example.com/1</link></para></listitem>
    </orderedlist>
  </section>
</article>
```

`docs/scripts/tests/fixtures/footnote_audit/mini_corpus/doc.html`:
```html
<!DOCTYPE html>
<html><body><p>Citation text.1 here.</p></body></html>
```

- [ ] **Step 2: Write the failing test**

```python
class TestMain(unittest.TestCase):
    def test_main_writes_report_against_a_fixture_corpus(self):
        from audit_footnote_links import main
        out_path = FIXTURES / "mini_corpus_report.csv"
        exit_code = main(["--corpus-root", str(FIXTURES / "mini_corpus"), "--out", str(out_path)])
        self.assertEqual(exit_code, 0)
        self.assertTrue(out_path.is_file())
        content = out_path.read_text(encoding="utf-8")
        self.assertIn("mini_corpus/doc.html", content)
        self.assertIn("High", content)
        out_path.unlink()
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd docs/scripts/tests && python3 -m unittest test_audit_footnote_links -v`
Expected: FAIL with `ImportError`

- [ ] **Step 4: Write minimal implementation**

```python
import argparse

DEFAULT_EXCLUDE_DIRS = {"papers", "scripts", "scratch", "bibliography"}


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus-root", default=str(REPO_ROOT / "docs"))
    parser.add_argument("--out", default=str(REPO_ROOT / "docs" / "audits" / "footnote-citation-audit.csv"))
    args = parser.parse_args(argv)

    corpus_root = Path(args.corpus_root)
    backlinks = build_backlink_map(corpus_root)

    import xml.etree.ElementTree as ET
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
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd docs/scripts/tests && python3 -m unittest test_audit_footnote_links -v`
Expected: PASS

- [ ] **Step 6: Run full suite, then commit**

```bash
python3 -m unittest discover -s docs/scripts/tests -v
git add docs/scripts/audit_footnote_links.py docs/scripts/tests/
git commit -m "feat: CLI entry point for the footnote-citation audit"
```

---

### Task 10: End-to-end integration test

**Files:**
- Modify: `docs/scripts/tests/test_audit_footnote_links.py`
- Create: `docs/scripts/tests/fixtures/footnote_audit/integration_corpus/` (a shell exercising a
  clean High-confidence footnote, a Medium (linkless entry), a restart, and a degenerate
  bibliography, in one small synthetic corpus)

**Interfaces:**
- Consumes: the whole pipeline (Tasks 1-9).
- Produces: no new production code — pure verification that the assembled pipeline produces the
  right confidence distribution end to end, the way `build_bibliography.py`'s own Task 15 did.

- [ ] **Step 1: Build the fixture corpus**

`docs/scripts/tests/fixtures/footnote_audit/integration_corpus/doc-a.xml` (clean High case):
```xml
<?xml version="1.0" encoding="UTF-8"?>
<article xmlns="http://docbook.org/ns/docbook" xml:id="doc-a" xml:lang="en">
  <title>Doc A</title>
  <section xml:id="body"><title>Body</title><para>Cited text.1 here.</para></section>
  <section xml:id="works-cited">
    <title>Works cited</title>
    <orderedlist numeration="arabic" spacing="compact">
      <listitem><para>Only Source <link xmlns:xlink="http://www.w3.org/1999/xlink" xlink:href="https://example.com/only">https://example.com/only</link></para></listitem>
    </orderedlist>
  </section>
</article>
```

`docs/scripts/tests/fixtures/footnote_audit/integration_corpus/doc-a.html`:
```html
<!DOCTYPE html><html><body><p>Cited text.1 here.</p></body></html>
```

`docs/scripts/tests/fixtures/footnote_audit/integration_corpus/doc-b.xml` (degenerate case —
many reuses of footnote 1, one fake linkless entry):
```xml
<?xml version="1.0" encoding="UTF-8"?>
<article xmlns="http://docbook.org/ns/docbook" xml:id="doc-b" xml:lang="en">
  <title>Doc B</title>
  <section xml:id="body"><title>Body</title><para>First.1 second.1 third.1</para></section>
  <section xml:id="works-cited">
    <title>Works cited</title>
    <orderedlist numeration="arabic" spacing="compact">
      <listitem><para>Bare Fake Entry</para></listitem>
    </orderedlist>
  </section>
</article>
```

`docs/scripts/tests/fixtures/footnote_audit/integration_corpus/doc-b.html`:
```html
<!DOCTYPE html><html><body><p>First.1 second.1 third.1</p></body></html>
```

- [ ] **Step 2: Write the failing integration test**

```python
class TestEndToEndIntegration(unittest.TestCase):
    def test_full_pipeline_produces_the_expected_confidence_distribution(self):
        from audit_footnote_links import main
        import csv
        out_path = FIXTURES / "integration_report.csv"
        exit_code = main(["--corpus-root", str(FIXTURES / "integration_corpus"), "--out", str(out_path)])
        self.assertEqual(exit_code, 0)

        with open(out_path, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))

        doc_a_rows = [r for r in rows if "doc-a" in r["file"]]
        doc_b_rows = [r for r in rows if "doc-b" in r["file"]]

        self.assertEqual(len(doc_a_rows), 1)
        self.assertEqual(doc_a_rows[0]["confidence_tier"], "High")

        self.assertEqual(len(doc_b_rows), 3)
        for r in doc_b_rows:
            self.assertEqual(r["confidence_tier"], "Needs manual triage")
            self.assertIn("degenerate_bibliography", r["flags"])

        out_path.unlink()
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd docs/scripts/tests && python3 -m unittest test_audit_footnote_links -v`
Expected: FAIL (surfaces whatever integration gap exists — this is expected; Tasks 1-9's unit
tests couldn't see across function boundaries)

- [ ] **Step 4: Fix whatever the failure reveals.** If the failure is anything other than an
  obvious wiring mistake (wrong argument order, wrong field name), this is a Process Discipline
  trigger — invoke `superpowers:systematic-debugging` before changing code, since it means two
  already-tested units disagree about their interface.

- [ ] **Step 5: Run test to verify it passes**

Run: `cd docs/scripts/tests && python3 -m unittest test_audit_footnote_links -v`
Expected: PASS

- [ ] **Step 6: Run the full suite once more, then commit**

```bash
python3 -m unittest discover -s docs/scripts/tests -v
git add docs/scripts/tests/
git commit -m "test: end-to-end integration test for the footnote-citation audit pipeline"
```

---

### Task 11: Corpus-wide run (process-discipline checkpoint, not a code task)

This task has no RED/GREEN steps — Tasks 1-10 already produced tested, working code. This is the
actual completion gate, run in order:

- [ ] **Step 1: Code review.** Dispatch a code-reviewer agent over the complete diff from Tasks
  1-10 (`git diff <task-1-base>...HEAD -- docs/scripts/audit_footnote_links.py
  docs/scripts/tests/`). Fix anything flagged; re-run the full suite after each fix.

- [ ] **Step 2: Simplify.** Run a `/simplify`-style pass over the same diff. Apply what it flags;
  re-run the full suite.

- [ ] **Step 3: Ask the user before running against the real corpus.** This is the point where
  the tool reads all 446 files' worth of real content for the first time — surface that you're
  about to do this and wait for go-ahead, per Process Discipline.

- [ ] **Step 4: Run the generator on the real corpus**

```bash
python3 docs/scripts/audit_footnote_links.py
```

If this exits non-zero or crashes, stop — invoke `superpowers:systematic-debugging`.

- [ ] **Step 5: The "too right" tripwire.** Check the tier counts printed by Step 4. The design's
  own research confirmed real restart cases, a real degenerate bibliography, and real
  out-of-bounds footnotes exist in this corpus today. **If "Needs manual triage" is zero, or the
  report contains no `restart_detected` flags at all, treat this as a red flag** — it means a
  check is silently not firing, not that the corpus turned out cleaner than the research found.
  Invoke `superpowers:systematic-debugging` before proceeding to Step 6.

- [ ] **Step 6: The human-reads-the-report gate (the actual completion criterion).** Read (not
  just count):
  - Every "Needs manual triage" row — confirm each genuinely has a real problem (exceeds length,
    degenerate bibliography, or a restart), not a scoring bug.
  - A sample of ~20 "High" confidence rows spread across different documents — confirm the
    matched works-cited entry text plausibly corresponds to the body context snippet. This is
    exactly the kind of semantic spot-check that caught the self-citation collision in the
    bibliography project; a mechanically "High" score is not proof of correctness.
  - A sample of ~10 "Medium" rows — confirm the missing signal (no link, or past a restart) is
    the actual reason for caution, not a mis-scored High-quality match.
  - Specifically re-verify the two documents named in the design research
    (`the-architecture-of-non-consensual-legality` for the restart case,
    `from-intangible-to-investment-ip-securitization` for the degenerate case) — confirm the
    audit's own output correctly flags both.

- [ ] **Step 7: Commit the report.**

```bash
git add docs/audits/footnote-citation-audit.csv
git commit -m "feat: run the footnote-citation audit against the real corpus"
```

- [ ] **Step 8: Report to the user** what the audit found (tier counts, notable patterns) and
  that any mechanical rewrite based on this report's "High" rows is a **separate, not-yet-designed
  project** (per the design's §9 explicit out-of-scope) — this audit's job ends at producing a
  trustworthy report, not acting on it.

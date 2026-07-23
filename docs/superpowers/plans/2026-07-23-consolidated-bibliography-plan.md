{% raw %}
# Consolidated References & Bibliography Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `docs/scripts/build_bibliography.py`, a repeatable generator that extracts every
corpus "works cited" entry (~5,488 links across ~89 files) and the paper's 28-entry
`bibliography.bib`, deduplicates them, elevates them to Bluebook (legal sources) or Chicago
Author-Date (everything else) citations without ever fabricating a missing field, and emits
`docs/bibliography/references.xml` — a DocBook article following the corpus's existing shell +
`.meta.xml` convention, requiring zero XSL/schema changes.

**Architecture:** A single-purpose script built bottom-up as independently-tested pure functions
(extraction → classification → elevation → dedup → invariant checks → emission), reusing
`convert_to_docbook.py`'s existing namespace constants and `validate()`/`build_html()` helpers
rather than redefining them. The corpus-wide run is a deliberately-invoked maintenance step
(Task 16), not wired into `build-corpus.yml`'s CI auto-commit — heuristic citation classification
needs a human review gate before it lands in a corpus used for real legal controversies.

**Tech Stack:** Python 3 stdlib only (`xml.etree.ElementTree`, `re`, `urllib.parse`,
`dataclasses`, `subprocess`) — no new dependencies. `xmllint`, `jing`, `xsltproc` via the
existing `validate()`/`build_html()` functions.

**Reference:** Full design rationale, the classification decision table, and the no-fabrication
policy are in `docs/superpowers/specs/2026-07-23-consolidated-bibliography-design.md`. This plan
implements that spec; consult it for *why*, not just *what*.

## Global Constraints

- **No fabrication, ever.** Any function that would need a citation field not literally present
  in the source text (an author, a year, a reporter volume/page) emits an explicit
  `[field unknown]` marker string instead of guessing. This is checked by an automated invariant
  in Task 13, not left to review alone.
- **Reuse, don't redefine.** Import `DB_NS`, `XI_NS`, `XLINK_NS`, `XML_NS`, `DC_NS`, `REPO_ROOT`,
  `element_full_text`, `validate`, `build_html` from `docs/scripts/convert_to_docbook.py`
  (`sys.path.insert(0, str(Path(__file__).resolve().parent))` then a normal import, matching
  `atomize_existing_document.py`'s own import pattern at the top of that file).
- **Determinism.** Every directory walk uses `sorted()`. Given the same corpus state, two runs
  of the script must produce byte-identical output.
- **Stdlib only.** No `bibtexparser`, no `lxml`, no third-party regex libraries. The BibTeX
  parser (Task 10) is hand-written against this repo's one `bibliography.bib` file's actual
  shape — it does not need to handle arbitrary BibTeX.
- **Under-classify, don't mis-classify.** Where a heuristic's confidence is genuinely
  ambiguous (see Task 7's case-vs-essay-title problem), the correct behavior is to *not* force
  the entry into Legal Citations — let it fall through to the generic secondary-source bucket or
  the Appendix. A wrong Bluebook-shaped citation is worse than an honestly-generic one.
- Every existing test in `docs/scripts/tests/` must still pass after every task. This script
  imports from, but never modifies, `convert_to_docbook.py`.

## Process Discipline

This governs every task below, not just the risky ones — per explicit instruction this session.

- **TDD, adversarial-first.** Every classification/formatting function's test file includes at
  least one deliberately adversarial fixture *before* the task is considered done — not just the
  happy-path case. Each task below specifies its adversarial case explicitly; do not skip it.
- **Verify after every task.** Run the full suite —
  `python3 -m unittest discover -s docs/scripts/tests -v` — after every task, not just the new
  test. A task's own new test passing doesn't prove it didn't silently break extraction logic an
  earlier task depends on.
- **Systematic debugging — on "too right" as well as "too wrong."** If any test fails that isn't
  the RED step you just wrote, stop and invoke `superpowers:systematic-debugging` before writing
  more code — root-cause it, don't loosen the assertion. The same applies to suspiciously *clean*
  results: if Task 16's corpus-wide run produces an empty or near-empty Appendix, that is a
  red flag, not a success — the survey already found real garbled works-cited entries, so their
  absence from the output means the classifier is silently swallowing them. Treat it exactly
  like a test failure and debug before proceeding.
- **Systematic-debug every bug fix, not just every bug.** If a task's implementation needs a
  fix after its own tests initially fail for an unexpected reason (not the planned RED step),
  run `superpowers:systematic-debugging` on *that fix itself* before moving to the next task —
  confirm the root cause was actually addressed, not just that the specific failing assertion
  now passes. Note the root cause in the commit message.
- **Code review** after Task 15 (full pipeline complete and integration-tested), before Task 16
  (the real corpus-wide run touches no test fixtures — it's the last checkpoint before real
  output). Dispatch a code-reviewer agent or run `/code-review` over the full diff from Tasks
  1-15. Fix anything flagged, re-run the full suite, before proceeding.
- **Simplify** immediately after code review passes, still before Task 16 — a `/simplify`-style
  pass over the same diff. Apply what it flags, re-run the full suite.
- **Verification-before-completion is the actual gate for Task 16**, not "tests pass." Task 16
  is not done until: the automated invariants (Task 13) hold on the real corpus-wide output, the
  Appendix tripwire above has been checked, the stratified sample (Task 16, step 5) has been
  read, and `xmllint`/`jing`/`xsltproc` succeed on the real generated file — in that order.
- **Ask the user** before committing Task 16's generated `docs/bibliography/references.xml` and
  before updating `docs/index.md` — this is the point where heuristic-classified content
  actually lands in the corpus. Do not ask before Tasks 1-15 — those are pure-function code,
  fully test-covered, touching no committed corpus data.

## File Structure

- **Create** `docs/scripts/build_bibliography.py` — the generator, built task-by-task below.
- **Create** `docs/scripts/tests/test_build_bibliography.py` — one test class per pipeline stage.
- **Create** `docs/scripts/tests/fixtures/bibliography/` — a small synthetic mini-corpus (shell
  articles, fragments, works-cited sections, a `bibliography.bib`) used by unit and integration
  tests, mirroring `docs/scripts/tests/fixtures/atomize_pilot/`'s role for
  `test_atomize_existing_document.py`.
- **Create** `docs/bibliography/references.xml`, `docs/bibliography/references.meta.xml`,
  `docs/bibliography/references.html` — Task 16's real output, generated (not hand-written), on
  real corpus data.
- **Modify** `docs/index.md` — Task 16, link to the new bibliography page.

---

### Task 1: Backlink map (xi:include graph resolution)

**Files:**
- Create: `docs/scripts/build_bibliography.py`
- Create: `docs/scripts/tests/fixtures/bibliography/backlink_corpus/shell-a.xml`
- Create: `docs/scripts/tests/fixtures/bibliography/backlink_corpus/shell-a/01-frag.xml`
- Create: `docs/scripts/tests/fixtures/bibliography/backlink_corpus/shell-b.xml`
- Test: `docs/scripts/tests/test_build_bibliography.py`

**Interfaces:**
- Produces: `parse_xincludes(xml_path) -> list[Path]` (absolute paths, direct includes only).
  `build_backlink_map(root_dir: Path) -> dict[Path, str]` — maps every shell article's own
  resolved path, and every file it (transitively) `xi:include`s, to the shell's repo-relative
  built `.html` path (e.g. `"docs/cross-cutting/foo.html"`).

- [ ] **Step 1: Create the fixture mini-corpus**

`docs/scripts/tests/fixtures/bibliography/backlink_corpus/shell-a.xml`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<article xmlns="http://docbook.org/ns/docbook" xmlns:xi="http://www.w3.org/2001/XInclude" xml:id="shell-a" xml:lang="en">
  <title>Shell A</title>
  <xi:include href="shell-a/01-frag.xml"/>
</article>
```

`docs/scripts/tests/fixtures/bibliography/backlink_corpus/shell-a/01-frag.xml`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<section xmlns="http://docbook.org/ns/docbook" xml:id="frag-a">
  <title>Fragment</title>
  <para>Body text.</para>
</section>
```

`docs/scripts/tests/fixtures/bibliography/backlink_corpus/shell-b.xml` (a shell with no
fragments, to prove a shell always maps to itself even with nothing to include):
```xml
<?xml version="1.0" encoding="UTF-8"?>
<article xmlns="http://docbook.org/ns/docbook" xml:id="shell-b" xml:lang="en">
  <title>Shell B</title>
  <para>No fragments here.</para>
</article>
```

- [ ] **Step 2: Write the failing test**

```python
# docs/scripts/tests/test_build_bibliography.py
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "bibliography"


class TestBuildBacklinkMap(unittest.TestCase):
    def test_maps_shell_and_its_fragment_to_shells_html(self):
        from build_bibliography import build_backlink_map
        root = FIXTURES / "backlink_corpus"
        backlinks = build_backlink_map(root)

        shell_a = (root / "shell-a.xml").resolve()
        frag_a = (root / "shell-a" / "01-frag.xml").resolve()
        shell_b = (root / "shell-b.xml").resolve()

        self.assertTrue(backlinks[shell_a].endswith("backlink_corpus/shell-a.html"))
        self.assertEqual(backlinks[frag_a], backlinks[shell_a])
        self.assertTrue(backlinks[shell_b].endswith("backlink_corpus/shell-b.html"))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd docs/scripts/tests && python3 -m unittest test_build_bibliography -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'build_bibliography'`

- [ ] **Step 4: Write minimal implementation**

```python
# docs/scripts/build_bibliography.py
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
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd docs/scripts/tests && python3 -m unittest test_build_bibliography -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add docs/scripts/build_bibliography.py docs/scripts/tests/test_build_bibliography.py docs/scripts/tests/fixtures/bibliography/
git commit -m "feat: add backlink map (xi:include graph resolution) for bibliography generator"
```

---

### Task 2: Works-cited extraction from a single file

**Files:**
- Modify: `docs/scripts/build_bibliography.py`
- Create: `docs/scripts/tests/fixtures/bibliography/works_cited_sample.xml`
- Test: `docs/scripts/tests/test_build_bibliography.py`

**Interfaces:**
- Consumes: nothing new.
- Produces: `extract_works_cited(xml_path: Path) -> list[tuple[str, str | None]]` — `(text,
  href)` per listitem, `href` is `None` when the listitem carries no `<link>`.

- [ ] **Step 1: Create the fixture, copied structure from a real corpus works-cited section**
  (`docs/court-record/matters/platform-tos-constitutional-limits/evidence/directed-ip-creation/06-works-cited.xml`),
  trimmed to 4 representative listitems: one garbled no-link entry, one with a link, and one
  with inline text before *and* after the link (the case `_para_title_text` must handle
  correctly — link text must not leak into the title).

`docs/scripts/tests/fixtures/bibliography/works_cited_sample.xml`:
```xml
<?xml version='1.0' encoding='utf-8'?>
<section xmlns="http://docbook.org/ns/docbook" xmlns:xlink="http://www.w3.org/1999/xlink" xml:id="works-cited">
  <title><emphasis role="strong">Works cited</emphasis></title>
  <orderedlist numeration="arabic" spacing="compact">
    <listitem><para>Systemic_Misclassification</para></listitem>
    <listitem><para>
        California Civil Code § 1550 (2024) - Justia Law, accessed
        September 19, 2025,
        <link xlink:href="https://law.justia.com/codes/california/code-civ/division-3/part-2/title-1/chapter-1/section-1550/">https://law.justia.com/codes/california/code-civ/division-3/part-2/title-1/chapter-1/section-1550/</link>
    </para></listitem>
    <listitem><para>
      Before-text
      <link xlink:href="https://example.com/x">https://example.com/x</link>
      after-text
    </para></listitem>
  </orderedlist>
</section>
```

- [ ] **Step 2: Write the failing test**

```python
class TestExtractWorksCited(unittest.TestCase):
    def test_extracts_text_and_link_skips_garbled_no_link_entry_correctly(self):
        from build_bibliography import extract_works_cited
        entries = extract_works_cited(FIXTURES / "works_cited_sample.xml")
        self.assertEqual(len(entries), 3)
        self.assertEqual(entries[0], ("Systemic_Misclassification", None))
        self.assertIn("California Civil Code § 1550 (2024) - Justia Law", entries[1][0])
        self.assertEqual(
            entries[1][1],
            "https://law.justia.com/codes/california/code-civ/division-3/part-2/title-1/chapter-1/section-1550/",
        )

    def test_link_inner_text_excluded_but_surrounding_text_kept(self):
        from build_bibliography import extract_works_cited
        entries = extract_works_cited(FIXTURES / "works_cited_sample.xml")
        text, href = entries[2]
        self.assertEqual(text, "Before-text after-text")
        self.assertEqual(href, "https://example.com/x")
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd docs/scripts/tests && python3 -m unittest test_build_bibliography -v`
Expected: FAIL with `ImportError: cannot import name 'extract_works_cited'`

- [ ] **Step 4: Write minimal implementation**

```python
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
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd docs/scripts/tests && python3 -m unittest test_build_bibliography -v`
Expected: PASS

- [ ] **Step 6: Run full suite, then commit**

```bash
python3 -m unittest discover -s docs/scripts/tests -v
git add docs/scripts/build_bibliography.py docs/scripts/tests/
git commit -m "feat: extract works-cited listitems (text + link) from a single document"
```

---

### Task 3: Corpus-wide raw extraction

**Files:**
- Modify: `docs/scripts/build_bibliography.py`
- Create: `docs/scripts/tests/fixtures/bibliography/mini_corpus/` (2 shells, one with a fragment
  carrying a works-cited section, one paper-like excluded directory)
- Test: `docs/scripts/tests/test_build_bibliography.py`

**Interfaces:**
- Consumes: `build_backlink_map` (Task 1), `extract_works_cited` (Task 2).
- Produces:
  ```python
  @dataclass
  class RawEntry:
      text: str
      href: str | None
      citing_html: str       # repo-relative .html of the citing shell
      source_file: str       # repo-relative .xml the entry was extracted from (for the Appendix)
  ```
  `extract_all_raw_entries(corpus_root: Path, exclude_dirs: set[str]) -> list[RawEntry]`.

- [ ] **Step 1: Create the fixture corpus**

`docs/scripts/tests/fixtures/bibliography/mini_corpus/doc-one.xml`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<article xmlns="http://docbook.org/ns/docbook" xmlns:xi="http://www.w3.org/2001/XInclude" xml:id="doc-one" xml:lang="en">
  <title>Doc One</title>
  <xi:include href="doc-one/01-works-cited.xml"/>
</article>
```

`docs/scripts/tests/fixtures/bibliography/mini_corpus/doc-one/01-works-cited.xml`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<section xmlns="http://docbook.org/ns/docbook" xmlns:xlink="http://www.w3.org/1999/xlink" xml:id="works-cited">
  <title>Works cited</title>
  <orderedlist numeration="arabic" spacing="compact">
    <listitem><para>Only entry <link xlink:href="https://example.com/a">https://example.com/a</link></para></listitem>
  </orderedlist>
</section>
```

`docs/scripts/tests/fixtures/bibliography/mini_corpus/excluded/doc-excluded.xml` (must NOT be
picked up — proves `exclude_dirs` filtering works):
```xml
<?xml version="1.0" encoding="UTF-8"?>
<article xmlns="http://docbook.org/ns/docbook" xml:id="doc-excluded" xml:lang="en">
  <title>Doc Excluded</title>
  <section xml:id="works-cited">
    <title>Works cited</title>
    <orderedlist numeration="arabic" spacing="compact">
      <listitem><para>Should never appear <link xlink:href="https://example.com/never">https://example.com/never</link></para></listitem>
    </orderedlist>
  </section>
</article>
```

- [ ] **Step 2: Write the failing test**

```python
class TestExtractAllRawEntries(unittest.TestCase):
    def test_extracts_from_fragment_and_skips_excluded_dir(self):
        from build_bibliography import extract_all_raw_entries
        root = FIXTURES / "mini_corpus"
        entries = extract_all_raw_entries(root, exclude_dirs={"excluded"})

        self.assertEqual(len(entries), 1)
        entry = entries[0]
        self.assertEqual(entry.href, "https://example.com/a")
        self.assertTrue(entry.citing_html.endswith("mini_corpus/doc-one.html"))
        self.assertTrue(entry.source_file.endswith("doc-one/01-works-cited.xml"))
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd docs/scripts/tests && python3 -m unittest test_build_bibliography -v`
Expected: FAIL with `ImportError: cannot import name 'extract_all_raw_entries'`

- [ ] **Step 4: Write minimal implementation**

```python
from dataclasses import dataclass


@dataclass
class RawEntry:
    text: str
    href: str | None
    citing_html: str
    source_file: str


def extract_all_raw_entries(corpus_root, exclude_dirs):
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
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd docs/scripts/tests && python3 -m unittest test_build_bibliography -v`
Expected: PASS

- [ ] **Step 6: Run full suite, then commit**

```bash
python3 -m unittest discover -s docs/scripts/tests -v
git add docs/scripts/build_bibliography.py docs/scripts/tests/
git commit -m "feat: corpus-wide raw works-cited entry extraction with backlinks"
```

---

### Task 4: URL normalization (dedup key)

**Files:**
- Modify: `docs/scripts/build_bibliography.py`
- Test: `docs/scripts/tests/test_build_bibliography.py`

**Interfaces:**
- Produces: `normalize_url(url: str) -> str`.

- [ ] **Step 1: Write the failing tests (happy path + adversarial)**

```python
class TestNormalizeUrl(unittest.TestCase):
    def test_strips_trailing_slash(self):
        from build_bibliography import normalize_url
        self.assertEqual(normalize_url("https://onellp.com/"), "https://onellp.com")

    def test_lowercases_scheme_and_host_but_not_path(self):
        from build_bibliography import normalize_url
        self.assertEqual(
            normalize_url("HTTPS://Justia.COM/Codes/CA-Civ-1550"),
            "https://justia.com/Codes/CA-Civ-1550",
        )

    def test_preserves_www_prefix_as_is(self):
        # Adversarial: two DIFFERENT hosts (www vs bare) must NOT collide —
        # normalizing away "www." would incorrectly merge them.
        from build_bibliography import normalize_url
        self.assertNotEqual(
            normalize_url("https://www.jmbm.com/entertainment.html"),
            normalize_url("https://jmbm.com/entertainment.html"),
        )

    def test_trailing_slash_and_case_variant_dedup_to_same_key(self):
        from build_bibliography import normalize_url
        self.assertEqual(
            normalize_url("https://Justia.com/x/"),
            normalize_url("https://justia.com/x"),
        )
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd docs/scripts/tests && python3 -m unittest test_build_bibliography -v`
Expected: FAIL with `ImportError: cannot import name 'normalize_url'`

- [ ] **Step 3: Write minimal implementation**

```python
from urllib.parse import urlsplit, urlunsplit


def normalize_url(url):
    parts = urlsplit(url.strip())
    scheme = parts.scheme.lower()
    netloc = parts.netloc.lower()
    path = parts.path.rstrip("/")
    return urlunsplit((scheme, netloc, path, parts.query, parts.fragment))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd docs/scripts/tests && python3 -m unittest test_build_bibliography -v`
Expected: PASS

- [ ] **Step 5: Run full suite, then commit**

```bash
python3 -m unittest discover -s docs/scripts/tests -v
git add docs/scripts/build_bibliography.py docs/scripts/tests/
git commit -m "feat: URL normalization for bibliography entry deduplication"
```

---

### Task 5: Access-date extraction and stripping

**Files:**
- Modify: `docs/scripts/build_bibliography.py`
- Test: `docs/scripts/tests/test_build_bibliography.py`

**Interfaces:**
- Produces: `extract_access_date(text: str) -> str | None`, `strip_access_date(text: str) -> str`.

- [ ] **Step 1: Write the failing tests**

```python
class TestAccessDate(unittest.TestCase):
    def test_extracts_accessed_date(self):
        from build_bibliography import extract_access_date
        text = "California Civil Code § 1550 (2024) - Justia Law, accessed September 19, 2025,"
        self.assertEqual(extract_access_date(text), "September 19, 2025")

    def test_returns_none_when_absent(self):
        from build_bibliography import extract_access_date
        self.assertIsNone(extract_access_date("No date marker here at all."))

    def test_strip_removes_accessed_clause_and_trims_punctuation(self):
        from build_bibliography import strip_access_date
        text = "Justia Law, accessed September 19, 2025,"
        self.assertEqual(strip_access_date(text), "Justia Law")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd docs/scripts/tests && python3 -m unittest test_build_bibliography -v`
Expected: FAIL with `ImportError`

- [ ] **Step 3: Write minimal implementation**

```python
import re

ACCESSED_RE = re.compile(r",?\s*accessed\s+([A-Za-z]+\s+\d{1,2},\s*\d{4})", re.IGNORECASE)


def extract_access_date(text):
    m = ACCESSED_RE.search(text)
    return m.group(1) if m else None


def strip_access_date(text):
    return ACCESSED_RE.sub("", text).strip(" ,.")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd docs/scripts/tests && python3 -m unittest test_build_bibliography -v`
Expected: PASS

- [ ] **Step 5: Run full suite, then commit**

```bash
python3 -m unittest discover -s docs/scripts/tests -v
git add docs/scripts/build_bibliography.py docs/scripts/tests/
git commit -m "feat: access-date extraction/stripping for secondary-source entries"
```

---

### Task 6: Statute classification + Bluebook formatting

**Files:**
- Modify: `docs/scripts/build_bibliography.py`
- Test: `docs/scripts/tests/test_build_bibliography.py`

**Interfaces:**
- Produces: `classify_statute(text: str) -> dict | None` (keys: `type="statute"`, `abbrev`,
  `section`, `year` [`str | None`]). `format_statute_bluebook(parsed: dict) -> str`.

- [ ] **Step 1: Write the failing tests (happy path + adversarial: nonstandard abbreviation
  falls through to `None` rather than crashing or guessing)**

```python
class TestClassifyStatute(unittest.TestCase):
    def test_classifies_known_code_with_year(self):
        from build_bibliography import classify_statute
        parsed = classify_statute("California Civil Code § 1550 (2024) - Justia Law")
        self.assertEqual(parsed["abbrev"], "Cal. Civ. Code")
        self.assertEqual(parsed["section"], "1550")
        self.assertEqual(parsed["year"], "2024")

    def test_classifies_usc(self):
        from build_bibliography import classify_statute
        parsed = classify_statute("17 U.S.C. § 101")
        self.assertEqual(parsed["abbrev"], "17 U.S.C.")
        self.assertEqual(parsed["section"], "101")
        self.assertIsNone(parsed["year"])

    def test_unrecognized_abbreviation_returns_none_not_a_guess(self):
        # Adversarial: "CORP §" is a real corpus abbreviation form NOT in the
        # lookup table. Must fall through cleanly (None), not crash, not
        # silently guess "Corporations Code".
        from build_bibliography import classify_statute
        self.assertIsNone(classify_statute("Under CORP § 202 the articles..."))

    def test_no_section_symbol_returns_none(self):
        from build_bibliography import classify_statute
        self.assertIsNone(classify_statute("California Civil Code generally"))


class TestFormatStatuteBluebook(unittest.TestCase):
    def test_formats_with_known_year(self):
        from build_bibliography import format_statute_bluebook
        parsed = {"type": "statute", "abbrev": "Cal. Civ. Code", "section": "1550", "year": "2024"}
        self.assertEqual(format_statute_bluebook(parsed), "Cal. Civ. Code § 1550 (2024).")

    def test_formats_with_unknown_year_marker(self):
        from build_bibliography import format_statute_bluebook
        parsed = {"type": "statute", "abbrev": "17 U.S.C.", "section": "101", "year": None}
        self.assertEqual(format_statute_bluebook(parsed), "17 U.S.C. § 101 ([year unknown]).")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd docs/scripts/tests && python3 -m unittest test_build_bibliography -v`
Expected: FAIL with `ImportError`

- [ ] **Step 3: Write minimal implementation**

```python
CODE_ABBREVIATIONS = {
    "corporations code": "Cal. Corp. Code",
    "corp. code": "Cal. Corp. Code",
    "civil code": "Cal. Civ. Code",
    "civ. code": "Cal. Civ. Code",
    "penal code": "Cal. Penal Code",
    "business and professions code": "Cal. Bus. & Prof. Code",
    "revenue and taxation code": "Cal. Rev. & Tax. Code",
    "government code": "Cal. Gov't Code",
    "family code": "Cal. Fam. Code",
    "food and agricultural code": "Cal. Food & Agric. Code",
    "public utilities code": "Cal. Pub. Util. Code",
    "code of civil procedure": "Cal. Civ. Proc. Code",
    "streets and highways code": "Cal. Sts. & High. Code",
    "labor code": "Cal. Lab. Code",
}
_STATUTE_RE = re.compile(
    r"(?P<code>" + "|".join(re.escape(k) for k in CODE_ABBREVIATIONS) + r")\s*§\s*(?P<section>[\d.]+)",
    re.IGNORECASE,
)
_USC_RE = re.compile(r"(?P<title>\d+)\s*U\.S\.C\.\s*§+\s*(?P<section>[\w.-]+)")
_YEAR_RE = re.compile(r"\((\d{4})\)")


def classify_statute(text):
    m = _STATUTE_RE.search(text)
    if m:
        abbrev = CODE_ABBREVIATIONS[m.group("code").lower()]
        section = m.group("section")
    else:
        m = _USC_RE.search(text)
        if not m:
            return None
        abbrev = f"{m.group('title')} U.S.C."
        section = m.group("section")
    year_m = _YEAR_RE.search(text)
    return {"type": "statute", "abbrev": abbrev, "section": section, "year": year_m.group(1) if year_m else None}


def format_statute_bluebook(parsed):
    year = parsed["year"] or "[year unknown]"
    return f"{parsed['abbrev']} § {parsed['section']} ({year})."
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd docs/scripts/tests && python3 -m unittest test_build_bibliography -v`
Expected: PASS

- [ ] **Step 5: Run full suite, then commit**

```bash
python3 -m unittest discover -s docs/scripts/tests -v
git add docs/scripts/build_bibliography.py docs/scripts/tests/
git commit -m "feat: statute classification and Bluebook formatting"
```

---

### Task 7: Case classification (domain-confidence heuristic) + Bluebook formatting

**Files:**
- Modify: `docs/scripts/build_bibliography.py`
- Test: `docs/scripts/tests/test_build_bibliography.py`

**Interfaces:**
- Produces: `classify_case(text: str, href: str | None) -> dict | None` (keys: `type="case"`,
  `name`, `complete: bool`, plus `year`/`volume`/`reporter`/`page` when `complete`).
  `format_case_bluebook(parsed: dict) -> str`.

**This is the highest false-positive-risk classifier in the whole pipeline — an essay title like
"Privacy v. Transparency in Legal Practice" is grammatically indistinguishable from a real case
name by regex alone.** The mitigation: a `" v. "` match is only trusted as a case if it's backed
by *one* of two independent, cheap signals — (a) a full reporter citation appears in the same
text, or (b) the entry's URL is on a known case-law aggregator domain. Absent both, the entry is
**not** classified as a case at all (it falls through to statute/generic classification in Task
9) — this is the "under-classify, don't mis-classify" constraint from Global Constraints in
concrete form.

- [ ] **Step 1: Write the failing tests, including the essay-title adversarial case**

```python
class TestClassifyCase(unittest.TestCase):
    def test_full_reporter_citation_gives_complete_bluebook_data(self):
        from build_bibliography import classify_case
        parsed = classify_case("Marvin v. Marvin (1976) 18 Cal. 3d 660.", href=None)
        self.assertEqual(parsed["name"], "Marvin v. Marvin")
        self.assertTrue(parsed["complete"])
        self.assertEqual(parsed["year"], "1976")
        self.assertEqual(parsed["volume"], "18")
        self.assertEqual(parsed["page"], "660")

    def test_courtlistener_url_without_reporter_gives_partial_case(self):
        from build_bibliography import classify_case
        parsed = classify_case(
            "Dynamex Operations West, Inc. v. Superior Court",
            href="https://www.courtlistener.com/opinion/dynamex/",
        )
        self.assertEqual(parsed["name"], "Dynamex Operations West, Inc. v. Superior Court")
        self.assertFalse(parsed["complete"])

    def test_essay_title_with_v_but_no_reporter_and_no_case_domain_is_not_a_case(self):
        # Adversarial: exactly the false-positive shape the design doc warns
        # about — title-case "X v. Y", no reporter, no case-law-aggregator URL.
        from build_bibliography import classify_case
        parsed = classify_case(
            "Privacy v. Transparency in Legal Practice",
            href="https://somelawfirmblog.example.com/privacy-vs-transparency",
        )
        self.assertIsNone(parsed)

    def test_no_v_pattern_returns_none(self):
        from build_bibliography import classify_case
        self.assertIsNone(classify_case("Restatement (Second) of Contracts § 45", href=None))


class TestFormatCaseBluebook(unittest.TestCase):
    def test_formats_complete_citation(self):
        from build_bibliography import format_case_bluebook
        parsed = {"type": "case", "name": "Marvin v. Marvin", "complete": True,
                  "year": "1976", "volume": "18", "reporter": "Cal. 3d", "page": "660"}
        self.assertEqual(format_case_bluebook(parsed), "Marvin v. Marvin, 18 Cal. 3d 660 (1976).")

    def test_formats_partial_citation_with_flag(self):
        from build_bibliography import format_case_bluebook
        parsed = {"type": "case", "name": "Dynamex Operations West, Inc. v. Superior Court", "complete": False}
        self.assertEqual(
            format_case_bluebook(parsed),
            "Dynamex Operations West, Inc. v. Superior Court, [reporter citation unknown].",
        )
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd docs/scripts/tests && python3 -m unittest test_build_bibliography -v`
Expected: FAIL with `ImportError`

- [ ] **Step 3: Write minimal implementation**

```python
CASE_LAW_DOMAINS = {"courtlistener.com", "casetext.com", "casemine.com", "law.justia.com", "scholar.google.com"}
_CASE_RE = re.compile(
    r"(?P<plaintiff>[A-Z][\w.,'&-]*(?:\s+[A-Z][\w.,'&-]*){0,6})\s+v\.\s+"
    r"(?P<defendant>[A-Z][\w.,'&-]*(?:\s+[A-Z][\w.,'&-]*){0,6})"
)
_REPORTER_ABBREVS = ["Cal. 3d", "Cal.3d", "F.2d", "F. 2d", "F.3d", "F. 3d", "U.S.", "P.2d", "P. 2d"]
_REPORTER_RE = re.compile(
    r"\((?P<year>\d{4})\)\s*(?P<volume>\d+)\s+(?P<reporter>"
    + "|".join(re.escape(r) for r in _REPORTER_ABBREVS)
    + r")\.?\s*(?P<page>\d+)"
)


def _looks_like_case_domain(href):
    if not href:
        return False
    host = urlsplit(href).netloc.lower()
    return any(host == d or host.endswith("." + d) for d in CASE_LAW_DOMAINS)


def classify_case(text, href):
    m = _CASE_RE.search(text)
    if not m:
        return None
    name = f"{m.group('plaintiff').strip()} v. {m.group('defendant').strip()}"
    rep_m = _REPORTER_RE.search(text)
    if rep_m:
        return {
            "type": "case", "name": name, "complete": True,
            "year": rep_m.group("year"), "volume": rep_m.group("volume"),
            "reporter": rep_m.group("reporter"), "page": rep_m.group("page"),
        }
    if _looks_like_case_domain(href):
        return {"type": "case", "name": name, "complete": False}
    return None


def format_case_bluebook(parsed):
    if parsed["complete"]:
        return f"{parsed['name']}, {parsed['volume']} {parsed['reporter']} {parsed['page']} ({parsed['year']})."
    return f"{parsed['name']}, [reporter citation unknown]."
```

Add `from urllib.parse import urlsplit` to the existing `urllib.parse` import line from Task 4
(`from urllib.parse import urlsplit, urlunsplit` — already present, no new import needed).

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd docs/scripts/tests && python3 -m unittest test_build_bibliography -v`
Expected: PASS

- [ ] **Step 5: Run full suite, then commit**

```bash
python3 -m unittest discover -s docs/scripts/tests -v
git add docs/scripts/build_bibliography.py docs/scripts/tests/
git commit -m "feat: case classification with domain-confidence heuristic, Bluebook formatting"
```

---

### Task 8: Generic secondary-source Chicago formatting

**Files:**
- Modify: `docs/scripts/build_bibliography.py`
- Test: `docs/scripts/tests/test_build_bibliography.py`

**Interfaces:**
- Consumes: `extract_access_date`, `strip_access_date` (Task 5).
- Produces: `format_secondary_chicago(text: str, href: str | None) -> str`.

- [ ] **Step 1: Write the failing tests**

```python
class TestFormatSecondaryChicago(unittest.TestCase):
    def test_known_publisher_with_access_date(self):
        from build_bibliography import format_secondary_chicago
        text = "California Civil Code § 1550 (2024) - Justia Law, accessed September 19, 2025,"
        result = format_secondary_chicago(text, "https://law.justia.com/codes/x")
        self.assertIn("Justia", result)
        self.assertIn("Accessed September 19, 2025", result)
        self.assertIn("https://law.justia.com/codes/x", result)

    def test_unknown_publisher_falls_back_to_bare_host_not_unknown_marker(self):
        # Adversarial: a host with no entry in KNOWN_PUBLISHERS still yields a
        # real, visible identifier (the host itself) rather than
        # "[author unknown]" — that marker is reserved for when there is truly
        # no href at all, per the no-fabrication policy's "denote empty, don't
        # omit" rule applied honestly (the host IS visible information).
        from build_bibliography import format_secondary_chicago
        result = format_secondary_chicago("Entertainment", "https://www.jmbm.com/entertainment.html")
        self.assertIn("jmbm.com", result)
        self.assertNotIn("[author unknown]", result)

    def test_no_href_and_no_access_date_marks_both_unknown(self):
        from build_bibliography import format_secondary_chicago
        result = format_secondary_chicago("Some Title With No Link", None)
        self.assertIn("[author unknown]", result)
        self.assertIn("[access date unknown]", result)
        self.assertIn("[no url]", result)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd docs/scripts/tests && python3 -m unittest test_build_bibliography -v`
Expected: FAIL with `ImportError`

- [ ] **Step 3: Write minimal implementation**

```python
KNOWN_PUBLISHERS = {
    "justia.com": "Justia", "law.justia.com": "Justia",
    "findlaw.com": "FindLaw", "codes.findlaw.com": "FindLaw",
    "casetext.com": "Casetext", "casemine.com": "CaseMine",
    "courtlistener.com": "CourtListener", "en.wikipedia.org": "Wikipedia",
    "law.cornell.edu": "Cornell Legal Information Institute",
}


def _guess_publisher(href):
    if not href:
        return None
    host = urlsplit(href).netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    return KNOWN_PUBLISHERS.get(host, host)


def format_secondary_chicago(text, href):
    publisher = _guess_publisher(href) or "[author unknown]"
    access_date = extract_access_date(text)
    title = strip_access_date(text) or "[title unknown]"
    date_str = f"Accessed {access_date}." if access_date else "[access date unknown]."
    url_str = href if href else "[no url]"
    return f'{publisher}. "{title}." {date_str} {url_str}'
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd docs/scripts/tests && python3 -m unittest test_build_bibliography -v`
Expected: PASS

- [ ] **Step 5: Run full suite, then commit**

```bash
python3 -m unittest discover -s docs/scripts/tests -v
git add docs/scripts/build_bibliography.py docs/scripts/tests/
git commit -m "feat: Chicago Author-Date formatting for generic secondary sources"
```

---

### Task 9: Entry classification pipeline (routes each raw entry to a section)

**Files:**
- Modify: `docs/scripts/build_bibliography.py`
- Test: `docs/scripts/tests/test_build_bibliography.py`

**Interfaces:**
- Consumes: `classify_statute`/`format_statute_bluebook` (Task 6), `classify_case`/
  `format_case_bluebook` (Task 7), `format_secondary_chicago` (Task 8).
- Produces: `classify_and_format(raw: RawEntry) -> tuple[str, str]` — `(section, display_text)`
  where `section` is one of `"legal"`, `"secondary"`, `"appendix"`.

- [ ] **Step 1: Write the failing tests, including the "no link + no pattern → appendix, not
  forced into a bucket" adversarial case**

```python
class TestClassifyAndFormat(unittest.TestCase):
    def test_statute_routes_to_legal(self):
        from build_bibliography import classify_and_format, RawEntry
        raw = RawEntry(text="California Civil Code § 1550 (2024)", href="https://justia.com/x",
                        citing_html="docs/x.html", source_file="docs/x.xml")
        section, display = classify_and_format(raw)
        self.assertEqual(section, "legal")
        self.assertEqual(display, "Cal. Civ. Code § 1550 (2024).")

    def test_case_with_reporter_routes_to_legal(self):
        from build_bibliography import classify_and_format, RawEntry
        raw = RawEntry(text="Marvin v. Marvin (1976) 18 Cal. 3d 660.", href=None,
                        citing_html="docs/x.html", source_file="docs/x.xml")
        section, display = classify_and_format(raw)
        self.assertEqual(section, "legal")
        self.assertIn("18 Cal. 3d 660", display)

    def test_generic_link_routes_to_secondary(self):
        from build_bibliography import classify_and_format, RawEntry
        raw = RawEntry(text="Entertainment", href="https://www.jmbm.com/entertainment.html",
                        citing_html="docs/x.html", source_file="docs/x.xml")
        section, display = classify_and_format(raw)
        self.assertEqual(section, "secondary")
        self.assertIn("jmbm.com", display)

    def test_no_link_no_pattern_routes_to_appendix(self):
        from build_bibliography import classify_and_format, RawEntry
        raw = RawEntry(text="Systemic_Misclassification", href=None,
                        citing_html="docs/x.html", source_file="docs/x.xml")
        section, display = classify_and_format(raw)
        self.assertEqual(section, "appendix")
        self.assertEqual(display, "Systemic_Misclassification")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd docs/scripts/tests && python3 -m unittest test_build_bibliography -v`
Expected: FAIL with `ImportError`

- [ ] **Step 3: Write minimal implementation**

```python
def classify_and_format(raw):
    statute = classify_statute(raw.text)
    if statute:
        return "legal", format_statute_bluebook(statute)

    case = classify_case(raw.text, raw.href)
    if case:
        return "legal", format_case_bluebook(case)

    if raw.href:
        return "secondary", format_secondary_chicago(raw.text, raw.href)

    return "appendix", raw.text
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd docs/scripts/tests && python3 -m unittest test_build_bibliography -v`
Expected: PASS

- [ ] **Step 5: Run full suite, then commit**

```bash
python3 -m unittest discover -s docs/scripts/tests -v
git add docs/scripts/build_bibliography.py docs/scripts/tests/
git commit -m "feat: entry classification pipeline routing to legal/secondary/appendix"
```

---

### Task 10: BibTeX parsing

**Files:**
- Modify: `docs/scripts/build_bibliography.py`
- Create: `docs/scripts/tests/fixtures/bibliography/sample.bib`
- Test: `docs/scripts/tests/test_build_bibliography.py`

**Interfaces:**
- Produces: `parse_bibtex(path: Path) -> list[dict]` — one dict per entry:
  `{"key": str, "entry_type": str, "fields": dict[str, str]}`.

- [ ] **Step 1: Create the fixture (2 entries: one with braces-nested-braces in a field value,
  matching the real file's `{{LARQL}}`-style nesting — the adversarial case for a naive
  brace-counting parser)**

`docs/scripts/tests/fixtures/bibliography/sample.bib`:
```bibtex
@misc{hay2024larql,
  author       = {Hay, Chris},
  title        = {{LARQL} --- {Lazarus Query Language}: A Graph Database Interface},
  year         = {2024},
  url          = {https://github.com/chrishayuk/larql}
}

@article{litchfield1984,
  title        = {Litchfield v. {Spielberg}},
  year         = {1984},
  volume       = {736},
  pages        = {1352},
  journal      = {F.2d}
}
```

- [ ] **Step 2: Write the failing tests**

```python
class TestParseBibtex(unittest.TestCase):
    def test_parses_both_entries_with_correct_types_and_keys(self):
        from build_bibliography import parse_bibtex
        entries = parse_bibtex(FIXTURES / "sample.bib")
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0]["key"], "hay2024larql")
        self.assertEqual(entries[0]["entry_type"], "misc")
        self.assertEqual(entries[1]["key"], "litchfield1984")
        self.assertEqual(entries[1]["entry_type"], "article")

    def test_field_with_nested_braces_extracted_without_the_braces(self):
        from build_bibliography import parse_bibtex
        entries = parse_bibtex(FIXTURES / "sample.bib")
        title = entries[0]["fields"]["title"]
        self.assertEqual(title, "LARQL --- Lazarus Query Language: A Graph Database Interface")

    def test_no_author_field_is_simply_absent_not_fabricated(self):
        from build_bibliography import parse_bibtex
        entries = parse_bibtex(FIXTURES / "sample.bib")
        self.assertNotIn("author", entries[1]["fields"])
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `cd docs/scripts/tests && python3 -m unittest test_build_bibliography -v`
Expected: FAIL with `ImportError`

- [ ] **Step 4: Write minimal implementation.** A pure-regex field extractor breaks on this
  file's own real content: `.*?` (non-greedy) stops at the *first* `}` it finds, which
  truncates a nested-brace value like `{{LARQL} --- {Lazarus Query Language}: ...}` at
  `{LARQL` — exactly the case the fixture tests. Python's `re` has no recursive/balanced-group
  support, so field values are extracted by a manual balanced-brace scan instead:

```python
_BIB_ENTRY_START_RE = re.compile(r"@(?P<type>\w+)\{(?P<key>[^,\s]+),")
_BIB_FIELD_NAME_RE = re.compile(r"(?P<name>\w+)\s*=\s*\{")


def _read_balanced(text, start):
    """text[start] must be '{'. Returns (contents without outer braces,
    index just after the matching closing brace), correctly handling
    arbitrarily nested {..} inside."""
    assert text[start] == "{"
    depth = 0
    i = start
    while i < len(text):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[start + 1:i], i + 1
        i += 1
    raise ValueError(f"unbalanced braces in BibTeX starting at index {start}")


def _strip_inner_braces(value):
    return re.sub(r"[{}]", "", value)


def parse_bibtex(path):
    text = Path(path).read_text(encoding="utf-8")
    entries = []
    for m in _BIB_ENTRY_START_RE.finditer(text):
        open_brace_idx = text.index("{", m.start())
        _, end_idx = _read_balanced(text, open_brace_idx)
        body = text[m.end():end_idx - 1]

        fields = {}
        for fm in _BIB_FIELD_NAME_RE.finditer(body):
            value_raw, _ = _read_balanced(body, fm.end() - 1)
            value = " ".join(_strip_inner_braces(value_raw).split())
            if value:
                fields[fm.group("name").lower()] = value

        entries.append({
            "key": m.group("key").strip(),
            "entry_type": m.group("type").lower(),
            "fields": fields,
        })
    return entries
```

**Note on the balanced-scan approach:** this correctly handles arbitrary brace nesting depth
(not just the one-level case in the fixture), so it is robust to any of the real file's 28
entries independent of their specific nesting shape. It still assumes each entry's fields
follow the file's actual `name = {value}` shape throughout — verified for real in Task 15's
integration test against the *actual* `bibliography.bib`, not just the fixture. If Task 15
finds an entry this doesn't parse correctly, that is exactly the kind of "went wrong" signal
Process Discipline requires stopping and systematic-debugging before patching blindly.

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd docs/scripts/tests && python3 -m unittest test_build_bibliography -v`
Expected: PASS

- [ ] **Step 6: Run full suite, then commit**

```bash
python3 -m unittest discover -s docs/scripts/tests -v
git add docs/scripts/build_bibliography.py docs/scripts/tests/
git commit -m "feat: BibTeX parser for bibliography.bib"
```

---

### Task 11: Bib-entry classification and formatting

**Files:**
- Modify: `docs/scripts/build_bibliography.py`
- Test: `docs/scripts/tests/test_build_bibliography.py`

**Interfaces:**
- Consumes: `parse_bibtex` (Task 10).
- Produces: `LEGAL_BIB_KEYS: frozenset[str]`, `SELF_CITATION_KEYS: dict[str, str]` (bib key →
  repo-relative `.md` path substring used to resolve it to a built `.html` page),
  `classify_bib_entry(entry: dict) -> tuple[str, str]` — `(section, display_text)`.

- [ ] **Step 1: Write the failing tests**

```python
class TestClassifyBibEntry(unittest.TestCase):
    def test_case_type_bib_entry_routes_to_legal(self):
        from build_bibliography import classify_bib_entry
        entry = {"key": "litchfield1984", "entry_type": "article",
                  "fields": {"title": "Litchfield v. Spielberg", "year": "1984",
                             "volume": "736", "pages": "1352", "journal": "F.2d"}}
        section, display = classify_bib_entry(entry)
        self.assertEqual(section, "legal")
        self.assertIn("Litchfield v. Spielberg", display)
        self.assertIn("736 F.2d 1352 (1984)", display)

    def test_academic_bib_entry_routes_to_secondary_chicago_style(self):
        from build_bibliography import classify_bib_entry
        entry = {"key": "geva2021ffn", "entry_type": "inproceedings",
                  "fields": {"author": "Geva, Mor and Schuster, Roei and Berant, Jonathan and Levy, Omer",
                             "title": "Transformer Feed-Forward Layers Are Key-Value Memories",
                             "year": "2021", "booktitle": "EMNLP 2021"}}
        section, display = classify_bib_entry(entry)
        self.assertEqual(section, "secondary")
        self.assertIn("Geva, Mor", display)
        self.assertIn("2021", display)
        self.assertIn("Transformer Feed-Forward Layers Are Key-Value Memories", display)

    def test_missing_reporter_on_legal_entry_marked_unknown_not_omitted(self):
        # Adversarial: bartz_anthropic2025-shaped entry has no
        # volume/journal/pages (real bib: ongoing litigation, no reporter
        # cite exists yet) -- must be flagged in the output text, not
        # silently dropped or guessed.
        from build_bibliography import classify_bib_entry
        entry = {"key": "bartz_anthropic2025", "entry_type": "misc",
                  "fields": {"title": "Bartz v. Anthropic", "year": "2025"}}
        section, display = classify_bib_entry(entry)
        self.assertEqual(section, "legal")  # LEGAL_BIB_KEYS override
        self.assertIn("[reporter citation unknown]", display)
        self.assertIn("2025", display)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd docs/scripts/tests && python3 -m unittest test_build_bibliography -v`
Expected: FAIL with `ImportError`

- [ ] **Step 3: Write minimal implementation.** `bartz_anthropic2025`/`kadrey_meta2025`/
  `garcia_characterai2025`/`gema_openai2025` have no `journal`/`volume`/`pages` fields at all
  (survey confirmed: they're `@misc` entries, ongoing/foreign litigation with no US reporter
  cite yet) — these use the same partial-citation `[reporter citation unknown]` shape as Task
  7's case classifier, keeping the two code paths consistent rather than inventing a third
  citation shape.

```python
LEGAL_BIB_KEYS = frozenset({
    "gema_openai2025", "garcia_characterai2025", "bartz_anthropic2025",
    "kadrey_meta2025", "litchfield1984", "copyright1976fixation",
    "gdpr2016", "ccpa2018", "eu_database_directive1996", "eu_pld2024",
})
SELF_CITATION_HTML = {
    "mclean2025categorical": "docs/court-record/theory/federal-constitutional/extensions/llms-as-categorical-systems.html",
    "mclean2025encoding": "docs/court-record/matters/platform-tos-constitutional-limits/evidence/llm-information-encoding-and-covert-channels.html",
    "mclean2025agpl": "docs/court-record/theory/federal-statutes/extensions/agpl-ai-training-and-code-licensing.html",
}


def _format_bib_legal(entry):
    f = entry["fields"]
    title = f.get("title", "[title unknown]")
    if all(k in f for k in ("volume", "journal", "pages")):
        year = f.get("year", "[year unknown]")
        return f"{title}, {f['volume']} {f['journal']} {f['pages']} ({year})."
    if "section" in f or "§" in title:
        return f"{title} ({f.get('year', '[year unknown]')})."
    return f"{title}, [reporter citation unknown] ({f.get('year', '[year unknown]')})."


def _format_bib_academic(entry):
    f = entry["fields"]
    author = f.get("author") or "[author unknown]"
    year = f.get("year", "[year unknown]")
    title = f.get("title", "[title unknown]")
    venue = f.get("booktitle") or f.get("journal") or f.get("institution") or f.get("howpublished")
    url = f.get("url")
    if entry["key"] in SELF_CITATION_HTML:
        url = SELF_CITATION_HTML[entry["key"]]
    tail = f" {venue}." if venue else ""
    url_str = f" {url}" if url else ""
    return f'{author}. {year}. "{title}."{tail}{url_str}'


def classify_bib_entry(entry):
    if entry["key"] in LEGAL_BIB_KEYS:
        return "legal", _format_bib_legal(entry)
    return "secondary", _format_bib_academic(entry)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd docs/scripts/tests && python3 -m unittest test_build_bibliography -v`
Expected: PASS

- [ ] **Step 5: Run full suite, then commit**

```bash
python3 -m unittest discover -s docs/scripts/tests -v
git add docs/scripts/build_bibliography.py docs/scripts/tests/
git commit -m "feat: bibliography.bib entry classification and formatting"
```

---

### Task 12: Deduplication

**Files:**
- Modify: `docs/scripts/build_bibliography.py`
- Test: `docs/scripts/tests/test_build_bibliography.py`

**Interfaces:**
- Consumes: `normalize_url` (Task 4).
- Produces:
  ```python
  @dataclass
  class BibliographyEntry:
      section: str
      display: str
      citing_htmls: list[str]
      dedup_key: str
  ```
  `dedupe(classified: list[tuple[str, str, RawEntry]]) -> list[BibliographyEntry]` — input is
  `(section, display_text, raw_entry)` triples in file-walk order (already deterministic per
  Global Constraints); output merges same-key entries, unioning `citing_htmls`.

- [ ] **Step 1: Write the failing tests**

```python
class TestDedupe(unittest.TestCase):
    def test_merges_entries_with_same_normalized_url_keeping_first_seen_title(self):
        from build_bibliography import dedupe, RawEntry
        raw1 = RawEntry(text="t1", href="https://Justia.com/x/", citing_html="docs/a.html", source_file="docs/a.xml")
        raw2 = RawEntry(text="t2", href="https://justia.com/x", citing_html="docs/b.html", source_file="docs/b.xml")
        classified = [("secondary", "First Title.", raw1), ("secondary", "Second Title.", raw2)]

        result = dedupe(classified)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].display, "First Title.")
        self.assertEqual(sorted(result[0].citing_htmls), ["docs/a.html", "docs/b.html"])

    def test_distinct_urls_stay_separate(self):
        from build_bibliography import dedupe, RawEntry
        raw1 = RawEntry(text="t1", href="https://a.example.com", citing_html="docs/a.html", source_file="docs/a.xml")
        raw2 = RawEntry(text="t2", href="https://b.example.com", citing_html="docs/b.html", source_file="docs/b.xml")
        classified = [("secondary", "A.", raw1), ("secondary", "B.", raw2)]
        self.assertEqual(len(dedupe(classified)), 2)

    def test_urlless_entries_dedup_by_normalized_display_text(self):
        # Adversarial: two bib-entry-derived legal citations with no href at
        # all (e.g. two case entries) must still dedup correctly on their
        # citation string, not silently treated as always-distinct.
        from build_bibliography import dedupe, RawEntry
        raw1 = RawEntry(text="orig1", href=None, citing_html="docs/a.html", source_file="docs/a.xml")
        raw2 = RawEntry(text="orig2", href=None, citing_html="docs/b.html", source_file="docs/b.xml")
        classified = [("legal", "Bartz v. Anthropic, [reporter citation unknown] (2025).", raw1),
                      ("legal", "Bartz v. Anthropic, [reporter citation unknown] (2025).", raw2)]
        result = dedupe(classified)
        self.assertEqual(len(result), 1)
        self.assertEqual(sorted(result[0].citing_htmls), ["docs/a.html", "docs/b.html"])
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd docs/scripts/tests && python3 -m unittest test_build_bibliography -v`
Expected: FAIL with `ImportError`

- [ ] **Step 3: Write minimal implementation**

```python
@dataclass
class BibliographyEntry:
    section: str
    display: str
    citing_htmls: list
    dedup_key: str


def _dedup_key(display_text, href):
    if href:
        return "url:" + normalize_url(href)
    return "text:" + " ".join(display_text.lower().split())


def dedupe(classified):
    by_key = {}
    order = []
    for section, display, raw in classified:
        key = _dedup_key(display, raw.href)
        if key not in by_key:
            by_key[key] = BibliographyEntry(section=section, display=display, citing_htmls=[], dedup_key=key)
            order.append(key)
        entry = by_key[key]
        if raw.citing_html not in entry.citing_htmls:
            entry.citing_htmls.append(raw.citing_html)
    return [by_key[k] for k in order]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd docs/scripts/tests && python3 -m unittest test_build_bibliography -v`
Expected: PASS

- [ ] **Step 5: Run full suite, then commit**

```bash
python3 -m unittest discover -s docs/scripts/tests -v
git add docs/scripts/build_bibliography.py docs/scripts/tests/
git commit -m "feat: deduplicate bibliography entries by URL or citation text"
```

---

### Task 13: Self-check invariants

**Files:**
- Modify: `docs/scripts/build_bibliography.py`
- Test: `docs/scripts/tests/test_build_bibliography.py`

**Interfaces:**
- Consumes: `BibliographyEntry` (Task 12), `RawEntry` (Task 3).
- Produces: `verify_invariants(raw_entries, appendix_entries, legal_entries, secondary_entries,
  repo_root) -> list[str]` — list of violation messages, empty means all invariants hold.

- [ ] **Step 1: Write the failing tests, one per invariant, plus one proving each invariant
  actually catches its violation (not just passes on good input)**

```python
class TestVerifyInvariants(unittest.TestCase):
    def _entry(self, section, display, htmls):
        from build_bibliography import BibliographyEntry
        return BibliographyEntry(section=section, display=display, citing_htmls=htmls,
                                   dedup_key=f"k:{display}")

    def test_no_entry_lost_passes_when_counts_reconcile(self):
        from build_bibliography import verify_invariants, RawEntry
        raw = [RawEntry(text="t", href=None, citing_html="docs/a.html", source_file="docs/a.xml")]
        appendix = ["t"]
        self.assertEqual(verify_invariants(raw, appendix, [], [], REPO_ROOT), [])

    def test_entry_lost_is_flagged(self):
        from build_bibliography import verify_invariants, RawEntry
        raw = [RawEntry(text="t", href=None, citing_html="docs/a.html", source_file="docs/a.xml")]
        violations = verify_invariants(raw, [], [], [], REPO_ROOT)
        self.assertTrue(any("lost" in v for v in violations))

    def test_legal_entry_missing_section_or_v_is_flagged(self):
        from build_bibliography import verify_invariants
        bad = self._entry("legal", "Some Non-Citation Text.", ["docs/a.html"])
        violations = verify_invariants([], [], [bad], [], REPO_ROOT)
        self.assertTrue(any("missing" in v.lower() for v in violations))

    def test_duplicate_normalized_url_across_entries_is_flagged(self):
        from build_bibliography import verify_invariants
        e1 = self._entry("secondary", 'X. "A." Accessed 1. https://justia.com/x', ["docs/a.html"])
        e2 = self._entry("secondary", 'Y. "B." Accessed 1. https://justia.com/x/', ["docs/b.html"])
        violations = verify_invariants([], [], [], [e1, e2], REPO_ROOT)
        self.assertTrue(any("duplicate" in v.lower() for v in violations))

    def test_dangling_backlink_is_flagged(self):
        from build_bibliography import verify_invariants
        bad = self._entry("secondary", 'X. "A." Accessed 1. https://x.com', ["docs/does-not-exist.html"])
        violations = verify_invariants([], [], [], [bad], REPO_ROOT)
        self.assertTrue(any("does-not-exist.html" in v for v in violations))
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd docs/scripts/tests && python3 -m unittest test_build_bibliography -v`
Expected: FAIL with `ImportError`

- [ ] **Step 3: Write minimal implementation.** The "no entry lost" check does **not** compare
  raw-entry counts against output counts — that arithmetic doesn't actually hold even on
  correct output: `dedupe()` collapses two raw entries from the *same* citing document to the
  *same* URL into a single `citing_htmls` slot (by design, Task 12), and `legal`/`secondary`
  here also contain `bibliography.bib`-derived entries with no corresponding `raw_entries` at
  all — so a naive count could "reconcile" while a real works-cited entry silently vanished, or
  look wrong while nothing is actually lost. Instead, **re-derive** each raw entry's expected
  classification and confirm it is actually present in the output — checking the real
  invariant (every raw entry landed *somewhere*) instead of an approximation of it:

```python
def verify_invariants(raw_entries, appendix_entries, legal_entries, secondary_entries, repo_root):
    violations = []

    appendix_set = set(appendix_entries)
    output_keys = {e.dedup_key for e in legal_entries + secondary_entries}
    for raw in raw_entries:
        section, display = classify_and_format(raw)
        if section == "appendix":
            if display not in appendix_set:
                violations.append(f"raw entry lost (missing from appendix): {raw.text!r}")
        elif _dedup_key(display, raw.href) not in output_keys:
            violations.append(f"raw entry lost (missing from {section}): {raw.text!r}")

    for e in legal_entries:
        if "§" not in e.display and " v. " not in e.display:
            violations.append(f"legal entry missing § or v. marker: {e.display!r}")

    seen_urls = {}
    for e in legal_entries + secondary_entries:
        for token in re.findall(r"https?://\S+", e.display):
            key = normalize_url(token.rstrip(".\"'"))
            if key in seen_urls and seen_urls[key] != e.display:
                violations.append(f"duplicate normalized URL survived dedup: {key}")
            seen_urls[key] = e.display

    for e in legal_entries + secondary_entries:
        for html in e.citing_htmls:
            if not (Path(repo_root) / html).is_file():
                violations.append(f"dangling backlink, file does not exist: {html}")

    return violations
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd docs/scripts/tests && python3 -m unittest test_build_bibliography -v`
Expected: PASS

- [ ] **Step 5: Run full suite, then commit**

```bash
python3 -m unittest discover -s docs/scripts/tests -v
git add docs/scripts/build_bibliography.py docs/scripts/tests/
git commit -m "feat: automated self-check invariants for generated bibliography"
```

---

### Task 14: DocBook emission + `.meta.xml` + CLI

**Files:**
- Modify: `docs/scripts/build_bibliography.py`
- Test: `docs/scripts/tests/test_build_bibliography.py`

**Interfaces:**
- Consumes: `BibliographyEntry` (Task 12), `SELF_CITATION_HTML` (Task 11), `build_backlink_map`
  (Task 1), `extract_all_raw_entries` (Task 3), `parse_bibtex`/`classify_bib_entry`
  (Tasks 10-11), `classify_and_format` (Task 9), `dedupe`/`verify_invariants` (Tasks 12-13).
- Produces: `relative_html_link(repo_relative_html: str) -> str`,
  `_bib_citation_backlinks() -> dict[str, str]` (bib key -> the paper article `.html` whose
  fragments actually use `<citation>KEY</citation>`),
  `emit_docbook(legal_entries, secondary_entries, appendix_texts) -> str` (returns the shell
  XML as a string, sorted alphabetically within each section), `write_meta_xml(path: Path)`,
  `main(argv) -> int`.

- [ ] **Step 1: Write the failing tests**

```python
class TestEmitDocbook(unittest.TestCase):
    def test_relative_html_link_from_bibliography_dir(self):
        from build_bibliography import relative_html_link
        self.assertEqual(
            relative_html_link("docs/cross-cutting/foo.html"),
            "../cross-cutting/foo.html",
        )

    def test_emits_sections_with_alphabetized_entries_and_backlinks(self):
        from build_bibliography import emit_docbook, BibliographyEntry
        legal = [BibliographyEntry(section="legal", display="Marvin v. Marvin, 18 Cal. 3d 660 (1976).",
                                     citing_htmls=["docs/a.html"], dedup_key="k1")]
        secondary = [BibliographyEntry(section="secondary", display='Justia. "X." Accessed 1. https://justia.com/x',
                                         citing_htmls=["docs/b.html"], dedup_key="k2")]
        xml_text = emit_docbook(legal, secondary, ["Garbled Entry"])

        self.assertIn('xml:id="legal-citations"', xml_text)
        self.assertIn('xml:id="academic-secondary-sources"', xml_text)
        self.assertIn('xml:id="appendix-needs-review"', xml_text)
        self.assertIn("Marvin v. Marvin", xml_text)
        self.assertIn('xlink:href="../a.html"', xml_text)
        self.assertIn("Garbled Entry", xml_text)

    def test_emitted_xml_is_well_formed(self):
        import xml.etree.ElementTree as ET
        from build_bibliography import emit_docbook, BibliographyEntry
        legal = [BibliographyEntry(section="legal", display="A & B v. C.", citing_htmls=["docs/a.html"], dedup_key="k1")]
        xml_text = emit_docbook(legal, [], [])
        ET.fromstring(xml_text)  # raises ParseError if malformed — must not raise
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd docs/scripts/tests && python3 -m unittest test_build_bibliography -v`
Expected: FAIL with `ImportError`

- [ ] **Step 3: Write minimal implementation**

```python
from xml.sax.saxutils import escape as xml_escape


def relative_html_link(repo_relative_html):
    assert repo_relative_html.startswith("docs/"), repo_relative_html
    return "../" + repo_relative_html[len("docs/"):]


def _entry_listitem_xml(entry):
    links = "; ".join(
        f'<link xlink:href="{xml_escape(relative_html_link(h))}">{xml_escape(h)}</link>'
        for h in sorted(entry.citing_htmls)
    )
    return (
        "    <listitem>\n"
        f"      <para>{xml_escape(entry.display)}</para>\n"
        f"      <para>Cited in: {links}</para>\n"
        "    </listitem>\n"
    )


def _section_xml(title, xml_id, entries):
    items = "".join(_entry_listitem_xml(e) for e in sorted(entries, key=lambda e: e.display.lower()))
    return (
        f'  <section xml:id="{xml_id}">\n'
        f"    <title>{xml_escape(title)}</title>\n"
        '    <orderedlist numeration="arabic" spacing="compact">\n'
        f"{items}"
        "    </orderedlist>\n"
        "  </section>\n"
    )


METHODOLOGY_PARA = (
    "Primary legal sources (cases, statutes, regulations) are cited in Bluebook (21st ed.) "
    "format. All other sources -- academic, technical, and secondary -- are cited in Chicago "
    "Author-Date (17th ed.) format. A field not verifiable from the source corpus is marked "
    "[unknown] rather than inferred. Generated by docs/scripts/build_bibliography.py from "
    "every corpus document's works-cited section plus the flagship paper's bibliography.bib; "
    "see docs/superpowers/specs/2026-07-23-consolidated-bibliography-design.md."
)


def emit_docbook(legal_entries, secondary_entries, appendix_texts):
    appendix_items = "".join(
        f"    <listitem>\n      <para>{xml_escape(t)}</para>\n    </listitem>\n"
        for t in appendix_texts
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<article xmlns="http://docbook.org/ns/docbook" '
        'xmlns:xlink="http://www.w3.org/1999/xlink" '
        'xmlns:xi="http://www.w3.org/2001/XInclude" '
        'xml:id="references" xml:lang="en">\n'
        '  <xi:include href="references.meta.xml"/>\n'
        "  <title>Consolidated References &amp; Bibliography</title>\n"
        '  <section xml:id="methodology">\n'
        "    <title>Scope and Citation Policy</title>\n"
        f"    <para>{xml_escape(METHODOLOGY_PARA)}</para>\n"
        "  </section>\n"
        + _section_xml("Legal Citations", "legal-citations", legal_entries)
        + _section_xml("Academic and Secondary Sources", "academic-secondary-sources", secondary_entries)
        + '  <section xml:id="appendix-needs-review">\n'
        "    <title>Appendix: Entries Needing Manual Review</title>\n"
        '    <orderedlist numeration="arabic" spacing="compact">\n'
        f"{appendix_items}"
        "    </orderedlist>\n"
        "  </section>\n"
        "</article>\n"
    )


def write_meta_xml(path):
    Path(path).write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<info xmlns="http://docbook.org/ns/docbook" xmlns:dc="http://purl.org/dc/terms/" xmlns:xi="http://www.w3.org/2001/XInclude">\n'
        "  <dc:title>Consolidated References &amp; Bibliography</dc:title>\n"
        '  <xi:include href="../common/shared-metadata.xml" />\n'
        "</info>\n",
        encoding="utf-8",
    )


PAPER_SRC = REPO_ROOT / "docs" / "papers" / "ai_and_ip" / "llm-database-theory" / "src"
PAPER_FALLBACK_HTML = "docs/papers/ai_and_ip/llm-database-theory/generated/01-llm-database-theory.html"
_CITATION_KEY_RE = re.compile(r"<citation>([\w.-]+)</citation>")


def _bib_citation_backlinks():
    """dict[str, str]: bibliography.bib key -> repo-relative .html of the
    paper article (01-llm-database-theory.html or
    02-legal-corpus-connections.html) whose fragments actually contain
    <citation>KEY</citation> -- resolved via the same xi:include backlink
    mechanism used for the rest of the corpus (build_backlink_map), so this
    points at the paper's REAL built page, not a guessed default."""
    paper_backlinks = build_backlink_map(PAPER_SRC)
    key_to_html = {}
    for xml_path in sorted(PAPER_SRC.rglob("*.xml")):
        html = paper_backlinks.get(xml_path.resolve())
        if html is None:
            continue
        for key in _CITATION_KEY_RE.findall(xml_path.read_text(encoding="utf-8")):
            key_to_html.setdefault(key, html)
    return key_to_html


def main(argv=None):
    out_dir = REPO_ROOT / "docs" / "bibliography"
    out_dir.mkdir(exist_ok=True)

    raw_entries = extract_all_raw_entries(REPO_ROOT / "docs", exclude_dirs={"papers", "scripts", "scratch", "bibliography"})
    bib_entries = parse_bibtex(PAPER_SRC / "bibliography.bib")
    bib_citation_backlinks = _bib_citation_backlinks()

    classified = [(*classify_and_format(r), r) for r in raw_entries]
    appendix_texts = [display for section, display, r in classified if section == "appendix"]

    bib_classified = []
    for entry in bib_entries:
        section, display = classify_bib_entry(entry)
        # Self-citations resolve to the actual corpus document they cite, not
        # the paper itself; everything else resolves to whichever paper
        # article fragment actually uses <citation>KEY</citation>, found via
        # the real <citation> usage sites (see the design spec's survey).
        html = (
            SELF_CITATION_HTML.get(entry["key"])
            or bib_citation_backlinks.get(entry["key"], PAPER_FALLBACK_HTML)
        )
        raw = RawEntry(text=entry["key"], href=None, citing_html=html, source_file="docs/papers/ai_and_ip/llm-database-theory/src/bibliography.bib")
        bib_classified.append((section, display, raw))

    legal = dedupe([c for c in classified + bib_classified if c[0] == "legal"])
    secondary = dedupe([c for c in classified + bib_classified if c[0] == "secondary"])

    violations = verify_invariants(raw_entries, appendix_texts, legal, secondary, REPO_ROOT)
    if violations:
        print("INVARIANT VIOLATIONS -- refusing to write output:", file=sys.stderr)
        for v in violations:
            print(f"  {v}", file=sys.stderr)
        return 1

    xml_path = out_dir / "references.xml"
    meta_path = out_dir / "references.meta.xml"
    xml_path.write_text(emit_docbook(legal, secondary, appendix_texts), encoding="utf-8")
    write_meta_xml(meta_path)

    errors = validate(xml_path)
    if errors:
        print("VALIDATION FAILED:", file=sys.stderr)
        for e in errors:
            print(f"  {e}", file=sys.stderr)
        return 1
    build_html(xml_path, xml_path.with_suffix(".html"))

    print(f"OK: {len(legal)} legal, {len(secondary)} secondary, {len(appendix_texts)} appendix entries")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd docs/scripts/tests && python3 -m unittest test_build_bibliography -v`
Expected: PASS

- [ ] **Step 5: Run full suite, then commit**

```bash
python3 -m unittest discover -s docs/scripts/tests -v
git add docs/scripts/build_bibliography.py docs/scripts/tests/
git commit -m "feat: DocBook emission, meta.xml, and CLI entry point for bibliography generator"
```

---

### Task 15: End-to-end integration test

**Files:**
- Modify: `docs/scripts/tests/test_build_bibliography.py`
- Create: `docs/scripts/tests/fixtures/bibliography/integration_corpus/` (2-3 shells covering a
  statute works-cited entry, a case works-cited entry via a case-law-domain URL, a generic
  secondary entry, and a garbled no-link entry — the full range Task 9 routes)

**Interfaces:**
- Consumes: the whole pipeline (Tasks 1-14).
- Produces: no new production code — this task is pure verification that the assembled pipeline
  produces valid, buildable DocBook end to end, catching integration bugs no single unit test
  can (e.g. a naming mismatch between what Task 3 produces and what Task 9 consumes).

- [ ] **Step 1: Build the fixture corpus** (one shell with a statute + case + generic + garbled
  works-cited section, one shell with none — proving a document with no works-cited section is
  simply skipped, not an error)

`docs/scripts/tests/fixtures/bibliography/integration_corpus/doc.xml`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<article xmlns="http://docbook.org/ns/docbook" xml:id="doc" xml:lang="en">
  <title>Integration Doc</title>
  <section xml:id="works-cited">
    <title>Works cited</title>
    <orderedlist numeration="arabic" spacing="compact">
      <listitem><para>California Civil Code § 1550 (2024)</para></listitem>
      <listitem><para>Dynamex Operations West, Inc. v. Superior Court, <link xmlns:xlink="http://www.w3.org/1999/xlink" xlink:href="https://www.courtlistener.com/opinion/dynamex/">https://www.courtlistener.com/opinion/dynamex/</link></para></listitem>
      <listitem><para>Entertainment, accessed May 1, 2025, <link xmlns:xlink="http://www.w3.org/1999/xlink" xlink:href="https://www.jmbm.com/entertainment.html">https://www.jmbm.com/entertainment.html</link></para></listitem>
      <listitem><para>Systemic_Misclassification</para></listitem>
    </orderedlist>
  </section>
</article>
```

`docs/scripts/tests/fixtures/bibliography/integration_corpus/doc-no-citations.xml`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<article xmlns="http://docbook.org/ns/docbook" xml:id="doc-no-citations" xml:lang="en">
  <title>No Citations Here</title>
  <para>Nothing to extract.</para>
</article>
```

- [ ] **Step 2: Write the failing integration test**

```python
class TestEndToEndIntegration(unittest.TestCase):
    def test_full_pipeline_produces_valid_docbook_with_all_four_buckets(self):
        from build_bibliography import (
            extract_all_raw_entries, parse_bibtex, classify_and_format, classify_bib_entry,
            dedupe, verify_invariants, emit_docbook, SELF_CITATION_HTML,
        )
        import xml.etree.ElementTree as ET

        root = FIXTURES / "integration_corpus"
        raw_entries = extract_all_raw_entries(root, exclude_dirs=set())
        self.assertEqual(len(raw_entries), 4)

        classified = [(*classify_and_format(r), r) for r in raw_entries]
        appendix_texts = [d for s, d, r in classified if s == "appendix"]
        legal = dedupe([c for c in classified if c[0] == "legal"])
        secondary = dedupe([c for c in classified if c[0] == "secondary"])

        self.assertEqual(len(legal), 2)     # statute + case
        self.assertEqual(len(secondary), 1)  # jmbm.com entry
        self.assertEqual(len(appendix_texts), 1)  # Systemic_Misclassification

        violations = verify_invariants(raw_entries, appendix_texts, legal, secondary, REPO_ROOT)
        self.assertEqual(violations, [])

        xml_text = emit_docbook(legal, secondary, appendix_texts)
        ET.fromstring(xml_text)  # well-formed
        self.assertIn("Cal. Civ. Code § 1550", xml_text)
        self.assertIn("Dynamex Operations West, Inc. v. Superior Court", xml_text)
        self.assertIn("[reporter citation unknown]", xml_text)
        self.assertIn("Systemic_Misclassification", xml_text)

    def test_real_bibliography_bib_parses_and_classifies_without_exceptions(self):
        # Runs Tasks 10-11 against the ACTUAL repo file, not a fixture --
        # the one place a real-file regression (e.g. an unhandled field
        # shape) would be caught before Task 16's full run.
        from build_bibliography import parse_bibtex, classify_bib_entry
        bib_path = REPO_ROOT / "docs" / "papers" / "ai_and_ip" / "llm-database-theory" / "src" / "bibliography.bib"
        entries = parse_bibtex(bib_path)
        self.assertEqual(len(entries), 28)
        for entry in entries:
            section, display = classify_bib_entry(entry)
            self.assertIn(section, ("legal", "secondary"))
            self.assertNotEqual(display.strip(), "")
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd docs/scripts/tests && python3 -m unittest test_build_bibliography -v`
Expected: FAIL (either an assertion mismatch or an exception — this is expected to surface
integration issues Tasks 1-14's isolated unit tests couldn't see)

- [ ] **Step 4: Fix whatever the failure reveals.** Do not guess — if the failure is
  unexpected (not simply "haven't imported the right names yet"), this is a Process Discipline
  trigger: invoke `superpowers:systematic-debugging` before changing code, since an integration
  failure here means two already-tested units disagree about their interface, and root-causing
  which one is wrong matters more than making the assertion pass.

- [ ] **Step 5: Run test to verify it passes**

Run: `cd docs/scripts/tests && python3 -m unittest test_build_bibliography -v`
Expected: PASS

- [ ] **Step 6: Run the full suite one more time, then commit**

```bash
python3 -m unittest discover -s docs/scripts/tests -v
git add docs/scripts/tests/
git commit -m "test: end-to-end integration test for the bibliography generation pipeline"
```

---

### Task 16: Corpus-wide run (process-discipline checkpoint, not a code task)

This task has no RED/GREEN steps of its own — Tasks 1-15 already produced tested, working code.
This task is the actual completion gate from Process Discipline, run in order:

- [ ] **Step 1: Code review.** Dispatch a code-reviewer agent (or run `/code-review`) over the
  complete diff from Tasks 1-15 (`git diff main...HEAD -- docs/scripts/build_bibliography.py
  docs/scripts/tests/`). Fix anything flagged. Re-run
  `python3 -m unittest discover -s docs/scripts/tests -v` after each fix.

- [ ] **Step 2: Simplify.** Run a `/simplify`-style pass over the same diff. Apply what it
  flags. Re-run the full test suite.

- [ ] **Step 3: Run the generator on the real corpus.**

```bash
python3 docs/scripts/build_bibliography.py
```

If this exits non-zero (invariant violations or validation failure), **stop** — invoke
`superpowers:systematic-debugging`. Do not loosen an invariant to make it pass; the invariants
encode real correctness properties from the design's no-fabrication and no-lost-entry
guarantees.

- [ ] **Step 4: The "too right" tripwire.** Check the Appendix section of the generated
  `docs/bibliography/references.xml`. The survey (design doc §1) found real garbled works-cited
  entries (e.g. `"Systemic_Misclassification"`, truncated mid-sentence fragments) in the corpus
  today. **If the Appendix is empty or has fewer than a handful of entries, treat this as a red
  flag, not a clean result** — it means the classifier is silently absorbing garbled entries
  into a citation-shaped bucket rather than correctly failing to classify them. Invoke
  `superpowers:systematic-debugging` on the classification pipeline before proceeding to Step 5.

- [ ] **Step 5: Stratified human-reviewable sample.** From the real output, read (not just
  count) a sample weighted toward the weakest-heuristic buckets: all partial case citations
  (`[reporter citation unknown]`), 20 random Legal Citations entries, 20 random Academic &
  Secondary entries, and every Appendix entry. Confirm none of the sampled Legal Citations
  entries are false-positive "case"-shaped non-case text (the Task 7 risk) and none of the
  sampled statute entries used a wrong code abbreviation. Separately — `verify_invariants`
  (Task 13) only reconciles `raw_entries` (works-cited), not `bibliography.bib` entries, against
  the output; with only 28 of those, check exhaustively rather than sampling: confirm all 28
  keys from `docs/papers/ai_and_ip/llm-database-theory/src/bibliography.bib` appear somewhere
  in `references.xml` (`grep -c` each key's rendered title text, or diff against the 28-entry
  list from Task 15's `test_real_bibliography_bib_parses_and_classifies_without_exceptions`).

- [ ] **Step 6: Validate the build directly** (this duplicates what `main()` already does
  internally, run once more standalone as the final confirmation before committing generated
  output):

```bash
xmllint --noout --xinclude docs/bibliography/references.xml
jing -c docs/schema/docbook-corpus.rnc docs/bibliography/references.xml
xsltproc --xinclude docs/xsl/html5.xsl docs/bibliography/references.xml > /tmp/references-check.html
diff /tmp/references-check.html docs/bibliography/references.html
```

Expected: all four commands succeed with no output/no diff.

- [ ] **Step 7: Ask the user** (per Process Discipline) before committing — surface the entry
  counts from Step 3's `OK: N legal, N secondary, N appendix` output and a link to read the
  generated `docs/bibliography/references.html` locally, and wait for explicit go-ahead before
  the next step.

- [ ] **Step 8: Link it from `docs/index.md`** — add a `## Bibliography` entry pointing to
  `bibliography/references.html`, following the file's existing flat-bullet-list-with-annotation
  convention (see the design doc §4 precedent discussion).

- [ ] **Step 9: Commit the generated output and index update**

```bash
git add docs/bibliography/ docs/index.md
git commit -m "feat: generate consolidated references & bibliography for the full corpus"
```
{% endraw %}

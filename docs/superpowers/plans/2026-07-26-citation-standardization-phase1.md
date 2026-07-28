# Citation & Bibliography Standardization Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and verify, end-to-end on one real document, the standardized citation
architecture from `docs/superpowers/specs/2026-07-26-citation-standardization-design.md`: real
DocBook `<biblioentry>` entry files reused via XInclude, an `eyecite`-driven typing/validation
layer, real rendering, and a numbered-citation-marker converter -- proving the whole pipeline on
`llms-as-categorical-systems` (already fully verified against its real Google Drive original)
before any corpus-wide bulk conversion is attempted.

**Architecture:** One standalone `<biblioentry>` file per real-world citable source
(`docs/bibliography/entries/<key>.xml`), reused via `<xi:include>` into both per-document and
repo-wide bibliographies. `eyecite` (installed via a dedicated venv, not apt-packaged) types and
validates citation text. A new converter rewrites the Deep-Research-style glued-marker pattern
(`"word.N"`) into real `<biblioref>` elements pointing at real entries, for documents confirmed to
have their full numbered reference list intact (Category A -- see the design's Section 1). Marker
detection and works-cited location reuse `docs/scripts/audit_footnote_links.py`'s existing,
already-adversarially-tested logic (`_is_excluded_context`, `locate_works_cited`) rather than
duplicating it -- discovered 2026-07-26, after this plan's first draft had already built parallel,
less rigorous detection logic; corrected before any task was executed. Rendering verification uses
the real, apt-installable official DocBook XSL stylesheets (`docbook-xsl-ns`) directly, confirmed by
direct testing to render `<bibliography>`/`<biblioentry>` correctly out of the box with zero custom
XSLT. `docs/xsl/html5.xsl` is a non-standard, hand-rolled renderer and is not exempt from this
project's standardization mandate; it is not modified in this plan purely for sequencing reasons
(this plan proves the citation architecture on one document first), and its full replacement by
`docbook-xsl-ns` is real, scoped work, tracked as Phase 2 of this project.

**Tech Stack:** Python 3 stdlib `xml.etree.ElementTree` (matching every existing script's
convention -- the corpus has not yet migrated to `lxml` corpus-wide), `eyecite` (Free Law Project,
via venv), `jing`/`xmllint` (existing), the official `docbook-xsl-ns` package (apt), XSLT 1.0.

## Global Constraints

- Every new/changed element combination in this plan was verified directly against the real,
  fetched DocBook 5.2 RELAX NG grammar (`jing -c .cache/docbook-5.2/docbookxi.rnc`) before being
  written into a task -- not assumed from the older, now-corrected ontology plan's own example
  code (which assumed `<link>` was valid directly inside `<biblioentry>`; it is not -- confirmed
  by direct testing 2026-07-26. `<biblioid class="uri">` is used instead, matching this corpus's
  own already-established `derive_identifier()`/`<biblioid class="uri">` convention).
- `<biblioentry>` is not a valid standalone document root (confirmed by direct `jing` testing,
  same class of finding as `docs/common/authorgroup.xml` in Phase 1) -- entry files are validated
  nested inside a realistic `<article><para>...</para><bibliography>...</bibliography></article>`
  wrapper, not asserted valid on their own.
- `eyecite` has no apt package (unlike `lxml`, which Phase 1 installed via `apt`). It is installed
  into a dedicated venv at `.venv-eyecite/` (repo root, gitignored). Any script that imports
  `eyecite` must be run via `.venv-eyecite/bin/python3`, not the bare system `python3` every other
  script in this repo uses -- this is a genuine, new operational convention this plan introduces,
  not an oversight.
- **Do not duplicate `audit_footnote_links.py`.** That script already solves glued-footnote-marker
  detection, works-cited location, and false-positive exclusion (statute pincites, alphanumeric
  regulatory codes) more rigorously than anything written fresh for this plan -- confirmed 2026-07-
  26 via direct testing that its `_is_excluded_context()` correctly excludes both false positives
  (`303A.01`, `9a.44`) `measure_citation_conformance.py`'s own simpler pattern lets through. Its
  pre-generated report, `docs/audits/footnote-citation-audit.csv` (7,667 rows), already flags
  `prompts-as-expression` `degenerate_bibliography` -- the same Category B finding this project's
  brainstorming re-derived by hand via live Drive comparison. Reuse its detection/location
  functions and its existing report; do not re-derive them.
- `docbook-xsl-ns` (apt-packaged) is used directly for this plan's rendering verification.
  `docs/xsl/html5.xsl` is non-standard and is not modified in this plan for sequencing reasons only
  (this plan proves the citation architecture first) -- not because its current behavior is being
  preserved. Its full replacement by `docbook-xsl-ns` is tracked as Phase 2 of this project.
- No task in this plan performs a corpus-wide bulk conversion. The only real content conversion in
  this plan is the single, fully-verified pilot document (`llms-as-categorical-systems`). Bulk
  execution across the remaining 87 flat-entry documents and the remaining numbered-citation
  documents is explicit follow-on scope for a future plan, per the design's own Section 7.
- `measure_citation_conformance.py` (already built, TDD, committed) is re-run after every
  content-changing step in this plan as the acceptance check -- not a new tool, the one already
  established as this project's RED/GREEN harness.

---

## File Structure

- Create `docs/scripts/citation_entry.py` -- standalone `<biblioentry>` file creation/parsing.
- Create `docs/scripts/tests/test_citation_entry.py`.
- Create `.venv-eyecite/` (gitignored) -- the eyecite venv.
- Create `docs/scripts/eyecite_classify.py` -- thin wrapper classifying citation text via eyecite.
- Create `docs/scripts/tests/test_eyecite_classify.py`.
- Install `docbook-xsl-ns` (apt) -- the official DocBook XSL stylesheets, used directly for this
  plan's rendering verification. `docs/xsl/html5.xsl` (non-standard, slated for full replacement by
  `docbook-xsl-ns` in Phase 2) is not modified in this plan -- sequencing only.
- Create `docs/scripts/convert_numbered_citations.py` -- the Category-A marker-to-citation
  converter, built on `audit_footnote_links.py`'s existing detection/exclusion logic, not a
  parallel reimplementation.
- Create `docs/scripts/tests/test_convert_numbered_citations.py`.
- Create `docs/bibliography/numbered-citation-classification.json` -- the Category A/B manifest,
  derived primarily from the existing `docs/audits/footnote-citation-audit.csv`, not re-researched
  from scratch for every document.
- Modify `docs/court-record/theory/federal-constitutional/extensions/llms-as-categorical-systems/
  01-*.xml` through `08-*.xml`, and the shell `llms-as-categorical-systems.xml` -- the pilot
  conversion.
- Create `docs/bibliography/entries/*.xml` -- 82 new entry files, one per the pilot document's
  works-cited list.

---

### Task 1: Standalone citation entry files

**Files:**
- Create: `docs/scripts/citation_entry.py`
- Test: `docs/scripts/tests/test_citation_entry.py`

**Interfaces:**
- Consumes: `DB_NS`, `XML_NS`, `REPO_ROOT`, `slugify()` (all existing, `convert_to_docbook.py`),
  `fetch_docbook_schema()` (existing).
- Produces: `derive_entry_key(text, href=None) -> str`, `write_biblioentry(entry_path, key, role,
  title, href=None) -> None`, `parse_biblioentry(entry_path) -> dict`, `ENTRIES_DIR` (Path
  constant) -- all consumed by Task 4 and the pilot task.

- [ ] **Step 1: Write the failing tests**

Create `docs/scripts/tests/test_citation_entry.py`:
```python
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class TestDeriveEntryKey(unittest.TestCase):
    def test_derives_key_from_url_host_and_tail(self):
        from citation_entry import derive_entry_key
        key = derive_entry_key("some display text", href="https://en.wikipedia.org/wiki/DisCoCat")
        self.assertEqual(key, "en-discocat")

    def test_falls_back_to_slugified_text_without_href(self):
        from citation_entry import derive_entry_key
        key = derive_entry_key("A Real Paper Title")
        self.assertEqual(key, "a-real-paper-title")

    def test_key_length_is_capped(self):
        from citation_entry import derive_entry_key
        key = derive_entry_key("A " * 100)
        self.assertLessEqual(len(key), 80)


class TestWriteAndParseBiblioentry(unittest.TestCase):
    def test_round_trips_key_role_title_href(self):
        from citation_entry import write_biblioentry, parse_biblioentry
        out_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, out_dir)
        entry_path = out_dir / "smith2020.xml"
        write_biblioentry(entry_path, key="smith2020", role="secondary",
                           title="Some Real Paper", href="https://example.com/a")
        parsed = parse_biblioentry(entry_path)
        self.assertEqual(parsed["key"], "smith2020")
        self.assertEqual(parsed["role"], "secondary")
        self.assertEqual(parsed["title"], "Some Real Paper")
        self.assertEqual(parsed["href"], "https://example.com/a")

    def test_href_is_optional(self):
        from citation_entry import write_biblioentry, parse_biblioentry
        out_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, out_dir)
        entry_path = out_dir / "noref.xml"
        write_biblioentry(entry_path, key="noref", role="needs-research", title="Unresolved Citation")
        parsed = parse_biblioentry(entry_path)
        self.assertIsNone(parsed["href"])

    def test_written_entry_validates_against_real_docbook_5_2_when_wrapped(self):
        """<biblioentry> is not a valid standalone root (same class of
        finding as docs/common/authorgroup.xml in Phase 1) -- validated
        nested in a realistic article, matching how it will actually be
        consumed via xi:include."""
        from citation_entry import write_biblioentry
        from convert_to_docbook import fetch_docbook_schema
        out_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, out_dir)
        entry_path = out_dir / "smith2020.xml"
        write_biblioentry(entry_path, key="smith2020", role="secondary",
                           title="Some Real Paper", href="https://example.com/a")
        wrapper_path = out_dir / "wrapper.xml"
        wrapper_path.write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<article xmlns="http://docbook.org/ns/docbook" '
            'xmlns:xi="http://www.w3.org/2001/XInclude" version="5.2" xml:id="t" xml:lang="en">\n'
            '  <title>T</title>\n'
            '  <para>Body content.</para>\n'
            '  <bibliography>\n'
            f'    <xi:include href="{entry_path.name}"/>\n'
            '  </bibliography>\n'
            '</article>\n',
            encoding="utf-8",
        )
        schema = fetch_docbook_schema()
        result = subprocess.run(["jing", "-c", str(schema), str(wrapper_path)],
                                 capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_double_quote_in_href_does_not_break_xml(self):
        """Guards the exact escaping bug this project's own global
        constraints already flagged once (the superseded ontology
        plan's note on avoiding _entry_listitem_xml's pattern)."""
        from citation_entry import write_biblioentry
        out_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, out_dir)
        entry_path = out_dir / "tricky.xml"
        write_biblioentry(entry_path, key="tricky", role="secondary",
                           title='A Title With "Quotes" & Ampersands',
                           href='https://example.com/a?q="x"&y=1')
        ET.parse(entry_path)  # must not raise
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python3 -m unittest docs.scripts.tests.test_citation_entry -v`
Expected: `ModuleNotFoundError: No module named 'citation_entry'`

- [ ] **Step 3: Implement `citation_entry.py`**

Create `docs/scripts/citation_entry.py`:
```python
"""Creates and parses standalone DocBook <biblioentry> citation entry
files (docs/bibliography/entries/<key>.xml), one file per real-world
citable source, reused via XInclude into both per-document and
repo-wide bibliographies (see
docs/superpowers/specs/2026-07-26-citation-standardization-design.md
Section 3). A bare fragment, no <info> wrapper -- entries are not
top-level articles, matching docs/common/authorgroup.xml's own
convention. Not a valid standalone document root (confirmed by direct
jing testing) -- always consumed via xi:include into a real
<bibliography> context."""

import re
import sys
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape, quoteattr
from xml.etree import ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parent))
from convert_to_docbook import DB_NS, REPO_ROOT, XML_NS, slugify  # noqa: E402

ENTRIES_DIR = REPO_ROOT / "docs" / "bibliography" / "entries"

XLINK_HREF = f"{{{'http://www.w3.org/1999/xlink'}}}href"


def derive_entry_key(text, href=None):
    """Stable, deterministic identifier for a citation entry. Prefers
    the URL's host + final path segment (stable across re-runs, unlike
    a key derived from display text, which changes if the text is
    ever re-formatted); falls back to a slug of the display text when
    there is no href."""
    if href:
        match = re.match(r"https?://([^/]+)/?(.*)", href)
        if match:
            host = match.group(1).replace("www.", "").split(".")[0]
            tail = match.group(2).rstrip("/").split("/")[-1] or host
            return slugify(f"{host}-{tail}")[:80]
    return slugify(text)[:80]


def write_biblioentry(entry_path, key, role, title, href=None):
    """Writes a standalone <biblioentry xml:id="key" role="role">
    file. `href` (optional) becomes a <biblioid class="uri"> child --
    not <link>, which db.bibliographic.elements does not include
    (confirmed 2026-07-26 by direct jing testing)."""
    entry_path = Path(entry_path)
    entry_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f"<biblioentry xmlns={quoteattr(DB_NS)} "
        f"xml:id={quoteattr(key)} role={quoteattr(role)}>",
        f"  <title>{xml_escape(title)}</title>",
    ]
    if href:
        lines.append(f'  <biblioid class="uri">{xml_escape(href)}</biblioid>')
    lines.append("</biblioentry>")
    lines.append("")
    entry_path.write_text("\n".join(lines), encoding="utf-8")


def parse_biblioentry(entry_path):
    """dict of {key, role, title, href} for an existing entry file."""
    root = ET.parse(entry_path).getroot()
    biblioid = root.find(f"{{{DB_NS}}}biblioid[@class='uri']")
    return {
        "key": root.get(f"{{{XML_NS}}}id"),
        "role": root.get("role"),
        "title": (root.find(f"{{{DB_NS}}}title").text or "").strip(),
        "href": (biblioid.text or "").strip() if biblioid is not None else None,
    }
```

Note: `xmlns=quoteattr(DB_NS)` is used (not an f-string interpolating `DB_NS` directly into an
unescaped attribute) even though `DB_NS` is a fixed, safe, internal constant -- consistent,
defensive attribute construction throughout, not "safe because I know the value," matching the
exact anti-pattern this project's own global constraints flagged once already.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python3 -m unittest docs.scripts.tests.test_citation_entry -v`
Expected: all 6 `PASS`, including the real-schema validation test.

- [ ] **Step 5: Commit**

```bash
git add docs/scripts/citation_entry.py docs/scripts/tests/test_citation_entry.py
git commit -m "feat: add standalone <biblioentry> citation entry file creation/parsing, verified against the real DocBook 5.2 grammar"
```

---

### Task 2: `eyecite` venv setup and classification wrapper

**Files:**
- Create: `.venv-eyecite/` (gitignored, not committed)
- Modify: `.gitignore`
- Create: `docs/scripts/eyecite_classify.py`
- Test: `docs/scripts/tests/test_eyecite_classify.py`

**Interfaces:**
- Produces: `classify_citation_text(text) -> dict` with keys `role` (`"case"`, `"statute"`,
  `None`), `resolved` (bool), `parsed` (the matched citation string, or `None`) -- consumed by
  Task 4 and the pilot task.

- [ ] **Step 1: Create the venv and install eyecite**

```bash
python3 -m venv .venv-eyecite
.venv-eyecite/bin/pip install --quiet eyecite
.venv-eyecite/bin/python3 -c "import eyecite; print('OK')"
```
Expected: prints `OK`. (Debian's PEP 668 "externally managed environment" blocks a bare
system-wide `pip install`; a venv is the correct install path here, unlike `lxml`, which Phase 1
installed via `apt` because an apt package exists for it -- none exists for `eyecite`.)

- [ ] **Step 2: Gitignore the venv**

Add to `.gitignore`:
```
.venv-eyecite/
```

- [ ] **Step 3: Write the failing tests**

Create `docs/scripts/tests/test_eyecite_classify.py`:
```python
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class TestClassifyCitationText(unittest.TestCase):
    def test_full_case_citation_resolves_as_case(self):
        from eyecite_classify import classify_citation_text
        result = classify_citation_text(
            "This references Alice Corp. v. CLS Bank Int'l, 573 U.S. 208 (2014) directly."
        )
        self.assertEqual(result["role"], "case")
        self.assertTrue(result["resolved"])
        self.assertIn("573 U.S. 208", result["parsed"])

    def test_webpage_title_without_a_real_citation_does_not_resolve(self):
        """The corpus's actual works-cited text -- confirmed 2026-07-26
        that eyecite correctly finds nothing here, because there is
        nothing there to find (no reporter citation, just a webpage
        title mentioning a case name)."""
        from eyecite_classify import classify_citation_text
        result = classify_citation_text(
            "Alice v. CLS Bank: United States Supreme Court Establishes "
            "General Patentability Test, accessed September 2, 2025,"
        )
        self.assertFalse(result["resolved"])
        self.assertIsNone(result["role"])

    def test_statute_symbol_alone_is_unresolved_not_a_confident_statute(self):
        """A bare "§" glued into aggregator-title noise is flagged
        UnknownCitation by eyecite, not a confidently-typed statute --
        confirmed 2026-07-26 by direct testing. Must not be reported
        as role="statute" on that weak a signal."""
        from eyecite_classify import classify_citation_text
        result = classify_citation_text(
            "California Code, Corporations Code - CORP § 12200 - Codes - FindLaw"
        )
        self.assertFalse(result["resolved"])
```

- [ ] **Step 4: Run the tests to verify they fail**

Run: `.venv-eyecite/bin/python3 -m unittest docs.scripts.tests.test_eyecite_classify -v`
Expected: `ModuleNotFoundError: No module named 'eyecite_classify'`

- [ ] **Step 5: Implement `eyecite_classify.py`**

Create `docs/scripts/eyecite_classify.py`:
```python
"""Thin wrapper around eyecite (Free Law Project) for classifying
citation text -- see
docs/superpowers/specs/2026-07-26-citation-standardization-design.md
Section 5 for eyecite's three confirmed roles in this project
(validator, extraction aid, explicit-flagging mechanism). Must be run
via .venv-eyecite/bin/python3, not the bare system python3 every other
script in this repo uses -- eyecite has no apt package, unlike lxml."""

from eyecite import get_citations
from eyecite.models import FullCaseCitation, FullLawCitation


def classify_citation_text(text):
    """dict with keys role ("case"/"statute"/None), resolved (bool),
    parsed (the matched citation string or None). Only a FullCaseCitation
    or FullLawCitation counts as resolved -- eyecite's own UnknownCitation
    (a citation-shaped fragment it can't confidently type, e.g. a bare
    section symbol in webpage-title noise) is deliberately treated as
    unresolved, not a weak positive."""
    citations = get_citations(text)
    for citation in citations:
        if isinstance(citation, FullCaseCitation):
            return {"role": "case", "resolved": True, "parsed": citation.corrected_citation()}
        if isinstance(citation, FullLawCitation):
            return {"role": "statute", "resolved": True, "parsed": citation.corrected_citation()}
    return {"role": None, "resolved": False, "parsed": None}
```

- [ ] **Step 6: Run the tests to verify they pass**

Run: `.venv-eyecite/bin/python3 -m unittest docs.scripts.tests.test_eyecite_classify -v`
Expected: all 3 `PASS`.

- [ ] **Step 7: Commit**

```bash
git add .gitignore docs/scripts/eyecite_classify.py docs/scripts/tests/test_eyecite_classify.py
git commit -m "feat: add eyecite-based citation classification wrapper (venv-installed, no apt package exists for it)"
```

---

### Task 3: Verify real bibliography/cross-reference rendering via the official DocBook XSL stylesheets

This task verifies that the official, apt-installable `docbook-xsl-ns` package already renders
`<bibliography>`/`<biblioentry>` correctly out of the box, with zero custom XSLT -- writing a
second, hand-rolled implementation of the same rendering (which an earlier draft of this task did,
directly in `docs/xsl/html5.xsl`) is exactly the pattern this whole project exists to eliminate, and
`html5.xsl` itself is non-standard, not something to extend further. Separately, this task also
confirmed `<citation>KEY</citation>` -- what Task 4 was going to convert markers into -- is the
wrong element regardless of which stylesheet renders it: DocBook 5.2 has a purpose-built element for
exactly this, `<biblioref linkend="KEY"/>` ("A cross-reference to a bibliographic entry"), confirmed
by direct testing to render as a real, resolved hyperlink via the unmodified official stylesheet.
This task is pure verification -- no file is modified; replacing `html5.xsl` itself is Phase 2
scope (see Task 6, Step 9).

**Files:** none modified.

**Interfaces:**
- Consumes: the entry-file shape from Task 1.
- Produces: confirmation that `docbook-xsl-ns` (installed this task) correctly renders this
  project's real DocBook structure -- consumed by the pilot task's verification, which renders via
  `docbook-xsl-ns` directly, not `html5.xsl`.

- [ ] **Step 1: Install the official DocBook XSL stylesheets**

```bash
sudo apt-get install -y docbook-xsl-ns
find /usr/share/xml/docbook/stylesheet/docbook-xsl-ns/html -name "docbook.xsl"
```
Expected: prints `/usr/share/xml/docbook/stylesheet/docbook-xsl-ns/html/docbook.xsl`.

- [ ] **Step 2: Verify bibliography/biblioentry rendering against a real, minimal example**

```bash
mkdir -p /tmp/html5-bib-test
cat > /tmp/html5-bib-test/entry.xml << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<biblioentry xmlns="http://docbook.org/ns/docbook" xml:id="smith2020" role="secondary">
  <title>Some Real Paper</title>
  <biblioid class="uri">https://example.com/a</biblioid>
</biblioentry>
EOF
cat > /tmp/html5-bib-test/doc.xml << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<article xmlns="http://docbook.org/ns/docbook" xmlns:xi="http://www.w3.org/2001/XInclude" version="5.2" xml:id="t" xml:lang="en">
  <info><title>T</title></info>
  <para>See <biblioref linkend="smith2020"/> for details.</para>
  <bibliography>
    <xi:include href="entry.xml"/>
  </bibliography>
</article>
EOF
jing -c .cache/docbook-5.2/docbookxi.rnc /tmp/html5-bib-test/doc.xml && echo VALID
xsltproc --xinclude /usr/share/xml/docbook/stylesheet/docbook-xsl-ns/html/docbook.xsl /tmp/html5-bib-test/doc.xml | grep -o '<a href="#smith2020"[^<]*<[^<]*<[^<]*'
```
Expected: `VALID`, then output containing `<a href="#smith2020" class="biblioref" title="[smith2020]">smith2020</a>` -- a real, resolved hyperlink from the citation site directly to the bibliography entry, rendered by the unmodified official stylesheet.

- [ ] **Step 3: `html5.xsl`'s full replacement is Phase 2 scope, not skipped or deferred indefinitely**

`docs/xsl/html5.xsl` is confirmed non-standard: it duplicates rendering that `docbook-xsl-ns`
already does correctly, and lacks support for the new `<bibliography>`/`<biblioref>` structure this
plan introduces. Retiring it entirely and rendering the corpus via `docbook-xsl-ns` directly is the
correct end state -- this plan does not do that retirement itself (it is scoped to proving the
citation architecture on one document), but the retirement is real, identified follow-on work
(Phase 2), not an open question about whether it should happen.

No commit for this task -- nothing was modified, only installed and verified.

---

### Task 4: Convert the Deep-Research numbered-citation pattern (Category A)

**Design correction (2026-07-26), stated plainly:** this task's first draft defined its own
marker-detection regex and its own works-cited extraction, duplicating
`docs/scripts/audit_footnote_links.py` -- an existing, already-adversarially-tested tool for
exactly this problem (statute-pincite/regulatory-code exclusion, restart detection, confidence
scoring), discovered only after that first draft was written. Confirmed by direct testing: its
`_is_excluded_context()` correctly excludes the two false positives
(`303A.01`, `9a.44`) this plan's original, cruder pattern let through, and it works correctly even
applied to raw (tag-containing) fragment text, which it was not originally written for. This task
now reuses that logic instead of re-deriving it. It also now emits `<biblioref linkend="KEY"/>`
instead of `<citation>KEY</citation>` -- DocBook 5.2's actual purpose-built cross-reference element
("A cross-reference to a bibliographic entry"), confirmed by direct testing to render as a real,
resolved hyperlink via the unmodified official `docbook-xsl-ns` stylesheet (Task 3), where
`<citation>` renders as inert bracketed text under both the official stylesheet and this project's
own `html5.xsl`.

**Files:**
- Create: `docs/scripts/convert_numbered_citations.py`
- Test: `docs/scripts/tests/test_convert_numbered_citations.py`

**Interfaces:**
- Consumes: `ENTRIES_DIR`, `derive_entry_key()`, `write_biblioentry()` (Task 1);
  `_is_excluded_context()` (existing, `audit_footnote_links.py`) -- reused, not reimplemented.
- Produces: `build_entry_key_map(works_cited_fragment_path) -> dict[int, str]`,
  `convert_markers_in_fragment(fragment_path, key_map) -> int`,
  `remove_works_cited_section(fragment_path) -> bool` -- all consumed by the pilot task.

- [ ] **Step 1: Write the failing tests**

Create `docs/scripts/tests/test_convert_numbered_citations.py`:
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
        through, confirmed 2026-07-26: a statute/rule number that
        happens to fall within the works-cited list's range must still
        not convert -- reusing audit_footnote_links.py's
        _is_excluded_context() is what prevents this, not just the
        key_map range check."""
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


class TestRemoveWorksCitedSection(unittest.TestCase):
    def test_removes_the_section_when_present(self):
        from convert_numbered_citations import remove_works_cited_section
        out_dir = Path(tempfile.mkdtemp())
        Path(out_dir).mkdir(exist_ok=True)
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
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python3 -m unittest docs.scripts.tests.test_convert_numbered_citations -v`
Expected: `ModuleNotFoundError: No module named 'convert_numbered_citations'`

- [ ] **Step 3: Implement `convert_numbered_citations.py`**

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
audit_footnote_links.py's own read-only reporting use case).

Known limitation, stated plainly: a marker glued directly onto inline-
formatted text (e.g. "<emphasis>word</emphasis>.1") is not caught,
because the closing tag sits between the letter and the period in the
raw text. Acceptable for this phase's single verified pilot document
(no such case exists in it); a real limitation to fix before any
corpus-wide run."""

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
    Only call this for a document already confirmed Category A (see
    docs/bibliography/numbered-citation-classification.json, Task 5) --
    this function does not itself verify the list is complete or
    trustworthy."""
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
    unrelated digit)."""
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

Run: `python3 -m unittest docs.scripts.tests.test_convert_numbered_citations -v`
Expected: all 6 `PASS`.

- [ ] **Step 5: Verify `<biblioref>` against the real DocBook 5.2 grammar**

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

- [ ] **Step 6: Commit**

```bash
git add docs/scripts/convert_numbered_citations.py docs/scripts/tests/test_convert_numbered_citations.py
git commit -m "feat: convert the Deep-Research numbered-citation pattern (Category A) into real biblioentry/biblioref structure, reusing audit_footnote_links.py's exclusion logic"
```

---

### Task 5: Classify numbered-citation documents (Category A vs. B) from the existing audit report

**Design correction (2026-07-26), stated plainly:** this task's first draft planned to classify
all ~96 documents via live Google Drive comparison, one at a time, from scratch. Discovered before
execution: `docs/audits/footnote-citation-audit.csv` (7,667 rows) already exists, already computed
by `audit_footnote_links.py`, and already carries a per-marker confidence tier and a
`degenerate_bibliography` flag that strongly correlates with Category B. Confirmed by direct
testing: aggregating this existing report by file (majority-`degenerate_bibliography` -> B,
majority-`High`-confidence -> A) correctly classifies both documents already confirmed by hand
during this project's brainstorming (`llms-as-categorical-systems` -> A, `prompts-as-expression`
-> B), and reduces live Drive verification from ~96 documents to the small minority the aggregate
signal alone doesn't resolve (confirmed 12 of 95, not 96 -- the count differs slightly from
`measure_numbered_citation_pattern()`'s own candidate count, itself worth a one-line note in the
manifest, not silently reconciled).

**Files:**
- Create: `docs/scripts/classify_numbered_citations.py`
- Test: `docs/scripts/tests/test_classify_numbered_citations.py`
- Create: `docs/bibliography/numbered-citation-classification.json`

**Interfaces:**
- Consumes: `docs/audits/footnote-citation-audit.csv` (existing, `audit_footnote_links.py`'s own
  report).
- Produces: `classify_from_audit_csv(csv_path) -> dict[str, dict]` (per-file category:
  `"A"`/`"B"`/`"ambiguous"`, plus the row counts behind the call) -- consumed by the manifest-
  writing step and any future corpus-wide conversion plan.

- [ ] **Step 1: Write the failing tests**

Create `docs/scripts/tests/test_classify_numbered_citations.py`:
```python
import csv
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class TestClassifyFromAuditCsv(unittest.TestCase):
    def _write_csv(self, rows):
        out_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, out_dir)
        path = out_dir / "audit.csv"
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "file", "footnote_number", "body_context_snippet",
                "matched_works_cited_entry", "matched_works_cited_url",
                "confidence_tier", "flags",
            ])
            writer.writeheader()
            for row in rows:
                writer.writerow(row)
        return path

    def _row(self, file, confidence, flags=""):
        return {
            "file": file, "footnote_number": "1", "body_context_snippet": "x",
            "matched_works_cited_entry": "", "matched_works_cited_url": "",
            "confidence_tier": confidence, "flags": flags,
        }

    def test_majority_high_confidence_classifies_a(self):
        from classify_numbered_citations import classify_from_audit_csv
        csv_path = self._write_csv([
            self._row("doc1.html", "High"),
            self._row("doc1.html", "High"),
            self._row("doc1.html", "Medium"),
        ])
        result = classify_from_audit_csv(csv_path)
        self.assertEqual(result["doc1.html"]["category"], "A")

    def test_majority_degenerate_bibliography_classifies_b(self):
        from classify_numbered_citations import classify_from_audit_csv
        csv_path = self._write_csv([
            self._row("doc2.html", "Needs manual triage", "degenerate_bibliography"),
            self._row("doc2.html", "Needs manual triage", "degenerate_bibliography"),
            self._row("doc2.html", "High"),
        ])
        result = classify_from_audit_csv(csv_path)
        self.assertEqual(result["doc2.html"]["category"], "B")

    def test_mixed_signal_is_ambiguous(self):
        from classify_numbered_citations import classify_from_audit_csv
        csv_path = self._write_csv([
            self._row("doc3.html", "High"),
            self._row("doc3.html", "Needs manual triage", "degenerate_bibliography"),
        ])
        result = classify_from_audit_csv(csv_path)
        self.assertEqual(result["doc3.html"]["category"], "ambiguous")

    def test_real_audit_report_classifies_both_known_ground_truth_documents_correctly(self):
        """Anchors this classifier against the two documents this
        project's brainstorming already confirmed by hand via direct
        Google Drive comparison, 2026-07-26."""
        from classify_numbered_citations import classify_from_audit_csv, REPO_ROOT
        result = classify_from_audit_csv(REPO_ROOT / "docs" / "audits" / "footnote-citation-audit.csv")
        categorical = next(k for k in result if "categorical-systems" in k)
        prompts = next(k for k in result if "prompts-as-expression" in k)
        self.assertEqual(result[categorical]["category"], "A")
        self.assertEqual(result[prompts]["category"], "B")
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python3 -m unittest docs.scripts.tests.test_classify_numbered_citations -v`
Expected: `ModuleNotFoundError: No module named 'classify_numbered_citations'`

- [ ] **Step 3: Implement `classify_numbered_citations.py`**

Create `docs/scripts/classify_numbered_citations.py`:
```python
"""Classifies documents matching the Deep-Research numbered-citation
pattern into Category A (works-cited list intact, safe for
convert_numbered_citations.py) or Category B (needs-research),
primarily from docs/audits/footnote-citation-audit.csv --
audit_footnote_links.py's own, already-computed report (7,667 rows) --
rather than re-researching every document from scratch via live Google
Drive comparison. Confirmed 2026-07-26: this correctly reproduces both
ground-truth classifications this project's brainstorming already
established by hand (llms-as-categorical-systems -> A,
prompts-as-expression -> B), and reduces live Drive verification to the
small minority of documents where the aggregate signal alone is mixed
("ambiguous"), not all ~96 candidates."""

import csv
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from convert_to_docbook import REPO_ROOT  # noqa: E402

_MAJORITY_THRESHOLD = 0.5


def classify_from_audit_csv(csv_path):
    """dict[str, dict]: audit CSV file path -> {category, total_rows,
    high_count, degenerate_count}. category is "A" when more than half
    the file's rows are High confidence, "B" when more than half are
    flagged degenerate_bibliography, "ambiguous" otherwise -- neither
    signal reaches a majority, so this needs a live Drive check."""
    by_file = defaultdict(list)
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            by_file[row["file"]].append(row)

    results = {}
    for file, rows in by_file.items():
        total = len(rows)
        high = sum(1 for r in rows if r["confidence_tier"] == "High")
        degenerate = sum(1 for r in rows if "degenerate_bibliography" in r["flags"])
        if degenerate / total > _MAJORITY_THRESHOLD:
            category = "B"
        elif high / total > _MAJORITY_THRESHOLD:
            category = "A"
        else:
            category = "ambiguous"
        results[file] = {
            "category": category, "total_rows": total,
            "high_count": high, "degenerate_count": degenerate,
        }
    return results


def main(argv=None):
    results = classify_from_audit_csv(REPO_ROOT / "docs" / "audits" / "footnote-citation-audit.csv")
    counts = defaultdict(int)
    for r in results.values():
        counts[r["category"]] += 1
    print(f"Classified {len(results)} documents from the existing audit report:")
    print(f"  Category A (mechanically convertible): {counts['A']}")
    print(f"  Category B (needs-research): {counts['B']}")
    print(f"  Ambiguous (needs live Drive verification): {counts['ambiguous']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python3 -m unittest docs.scripts.tests.test_classify_numbered_citations -v`
Expected: all 4 `PASS`, including the real ground-truth anchor test.

- [ ] **Step 5: Run against the real corpus and inspect the ambiguous set**

```bash
python3 docs/scripts/classify_numbered_citations.py
```
Expected output shape (exact numbers confirmed 2026-07-26; re-verify against the corpus state at
execution time, since it may have changed):
```
Classified 95 documents from the existing audit report:
  Category A (mechanically convertible): 71
  Category B (needs-research): 12
  Ambiguous (needs live Drive verification): 12
```

- [ ] **Step 6: Write the manifest, live-verifying only the ambiguous set via Google Drive**

```bash
python3 -c "
import sys, json
sys.path.insert(0, 'docs/scripts')
from classify_numbered_citations import classify_from_audit_csv, REPO_ROOT
results = classify_from_audit_csv(REPO_ROOT / 'docs' / 'audits' / 'footnote-citation-audit.csv')
ambiguous = {k: v for k, v in results.items() if v['category'] == 'ambiguous'}
print(json.dumps(list(ambiguous.keys()), indent=2))
"
```
For each file printed: extract its `<title>` (`grep "<title>" <corresponding .meta.xml>`), search
Google Drive (`fullText contains '<distinctive phrase>'`), read the matched file, and determine
whether its reference list is genuinely present (reclassify "A") or absent (reclassify "B") --
same methodology already used and verified twice during this project's brainstorming. Write
`docs/bibliography/numbered-citation-classification.json` with every file from
`classify_from_audit_csv`'s full result, `ambiguous` entries overwritten with their live-verified
`"A"`/`"B"` outcome and a `verified: "2026-07-26"` field; non-ambiguous entries keep their
CSV-derived category with no `verified` field (they were not individually Drive-checked).

- [ ] **Step 7: Verify internal consistency**

```bash
python3 -c "
import json
data = json.load(open('docs/bibliography/numbered-citation-classification.json'))
assert all(v['category'] in ('A', 'B') for v in data.values()), 'no ambiguous entries should remain'
print(f'{len(data)} documents classified, 0 ambiguous')
"
```
Expected: `0 ambiguous` -- every document has a final A/B determination.

- [ ] **Step 8: Commit**

```bash
git add docs/scripts/classify_numbered_citations.py docs/scripts/tests/test_classify_numbered_citations.py \
        docs/bibliography/numbered-citation-classification.json
git commit -m "feat: classify numbered-citation documents into Category A/B primarily from the existing footnote-citation-audit.csv report, live-Drive-verifying only the ambiguous minority"
```

---

### Task 6: Pilot conversion -- `llms-as-categorical-systems`, end to end

**Files:**
- Modify: `docs/court-record/theory/federal-constitutional/extensions/llms-as-categorical-systems/
  01-*.xml` through `08-*.xml` (all 8 fragments)
- Create: `docs/bibliography/entries/*.xml` (82 new entry files)

**Interfaces:**
- Consumes: `build_entry_key_map()`, `convert_markers_in_fragment()`,
  `remove_works_cited_section()` (Task 4); `docbook-xsl-ns` (Task 3) for content-preservation
  verification -- not `html5.xsl`, which does not yet support `db:bibliography`/`db:biblioref`
  (Task 3's own deferred follow-on) and would show degraded, unstyled, unlinked rendering
  regardless of whether the new XML structure itself is correct; `measure_citation_conformance.py`
  (existing) as the acceptance check.

- [ ] **Step 1: Confirm the pilot document is classified Category A**

```bash
python3 -c "
import json
data = json.load(open('docs/bibliography/numbered-citation-classification.json'))
key = 'docs/court-record/theory/federal-constitutional/extensions/llms-as-categorical-systems.xml'
assert data[key]['category'] == 'A'
print('confirmed Category A')
"
```

- [ ] **Step 2: Snapshot the pre-conversion rendered text (content-preservation baseline)**

Rendered via the official `docbook-xsl-ns` stylesheet (Task 3), not `docs/xsl/html5.xsl` -- this
check needs to verify the new XML *structure* preserves content, independent of whether this
project's own not-yet-updated stylesheet happens to render every element it now contains:
```bash
xsltproc --xinclude /usr/share/xml/docbook/stylesheet/docbook-xsl-ns/html/docbook.xsl docs/court-record/theory/federal-constitutional/extensions/llms-as-categorical-systems.xml | python3 -c "
import sys, re
html = sys.stdin.read()
text = re.sub(r'<[^>]+>', ' ', html)
text = ' '.join(text.split())
open('/tmp/pilot-before.txt', 'w').write(text)
print(len(text), 'chars')
"
```

- [ ] **Step 3: Build the entry-key map and write entry files**

```bash
python3 -c "
import sys
sys.path.insert(0, 'docs/scripts')
from convert_numbered_citations import build_entry_key_map
key_map = build_entry_key_map('docs/court-record/theory/federal-constitutional/extensions/llms-as-categorical-systems/08-viii-conclusion-synthesizing-llms-and-category-theory-for-deeper-understanding.xml')
print(f'{len(key_map)} entries written')
assert len(key_map) == 82
"
```
Expected: prints `82 entries written`.

- [ ] **Step 4: Convert markers in every fragment**

```bash
python3 -c "
import sys, json
sys.path.insert(0, 'docs/scripts')
from convert_numbered_citations import build_entry_key_map, convert_markers_in_fragment
from pathlib import Path

frag_dir = Path('docs/court-record/theory/federal-constitutional/extensions/llms-as-categorical-systems')
key_map = build_entry_key_map(frag_dir / '08-viii-conclusion-synthesizing-llms-and-category-theory-for-deeper-understanding.xml')

total = 0
for fragment in sorted(frag_dir.glob('*.xml')):
    count = convert_markers_in_fragment(fragment, key_map)
    print(fragment.name, count)
    total += count
print('total converted:', total)
"
```
Expected: a non-zero count for at least the `01-` (introduction) and `08-` (conclusion) fragments,
matching the two glued markers already confirmed present in them
(`parameters.1`/`dependencies...2`-style markers).

- [ ] **Step 5: Remove the works-cited section and add a real `<bibliography>` to the shell**

```bash
python3 -c "
import sys
sys.path.insert(0, 'docs/scripts')
from convert_numbered_citations import remove_works_cited_section
removed = remove_works_cited_section('docs/court-record/theory/federal-constitutional/extensions/llms-as-categorical-systems/08-viii-conclusion-synthesizing-llms-and-category-theory-for-deeper-understanding.xml')
assert removed
"
```

Add a `<bibliography>` to the shell article
(`docs/court-record/theory/federal-constitutional/extensions/llms-as-categorical-systems.xml`),
XIncluding every entry file the key map produced. Generate the XInclude list:
```bash
python3 -c "
import sys
sys.path.insert(0, 'docs/scripts')
from convert_numbered_citations import build_entry_key_map
key_map = build_entry_key_map('docs/court-record/theory/federal-constitutional/extensions/llms-as-categorical-systems/08-viii-conclusion-synthesizing-llms-and-category-theory-for-deeper-understanding.xml')
for key in sorted(set(key_map.values())):
    print(f'  <xi:include href=\"bibliography/entries/{key}.xml\"/>')
" > /tmp/pilot-bibliography-includes.txt
```
Then manually insert a `<bibliography>` element containing those includes as the last child of
the shell article's `<article>` element (before the closing `</article>` tag), with a relative
path of `../../../../bibliography/entries/<key>.xml` from the shell's own directory (repo-root-
relative math: `docs/court-record/theory/federal-constitutional/extensions/` is 4 levels under
`docs/`, matching the same depth-based relative-path convention `write_metadata()` already uses).

- [ ] **Step 6: Verify against the real DocBook 5.2 grammar**

```bash
schema=$(python3 -c 'from docs.scripts.convert_to_docbook import fetch_docbook_schema; print(fetch_docbook_schema())')
jing -c "$schema" docs/court-record/theory/federal-constitutional/extensions/llms-as-categorical-systems.xml
echo "exit: $?"
```
Expected: exit 0.

- [ ] **Step 7: Verify via `measure_citation_conformance.py` -- the RED/GREEN check**

```bash
python3 -c "
import sys
sys.path.insert(0, 'docs/scripts')
from measure_citation_conformance import measure_citation_conformance, measure_numbered_citation_pattern
path = 'docs/court-record/theory/federal-constitutional/extensions/llms-as-categorical-systems.xml'
conformance = measure_citation_conformance(path)
numbered = measure_numbered_citation_pattern(path)
print(conformance)
print(numbered)
assert conformance['standard_entries'] == 82
assert conformance['nonstandard_entries'] == 0
assert numbered['works_cited_count'] == 0
"
```
Expected: `standard_entries == 82`, `nonstandard_entries == 0`, `works_cited_count == 0` -- this
single document goes from the corpus's largest single contributor to the non-standard baseline (82
entries) to fully standard, verified by the same tool that measured the original baseline.

- [ ] **Step 8: Verify no content was lost -- rebuild and diff against the pre-conversion snapshot**

Rendered via `docbook-xsl-ns`, matching Step 2's baseline (same reasoning: this checks the XML
structure, not `html5.xsl`'s current feature set):
```bash
xsltproc --xinclude /usr/share/xml/docbook/stylesheet/docbook-xsl-ns/html/docbook.xsl docs/court-record/theory/federal-constitutional/extensions/llms-as-categorical-systems.xml | python3 -c "
import sys, re
html = sys.stdin.read()
text = re.sub(r'<[^>]+>', ' ', html)
text = ' '.join(text.split())
before = open('/tmp/pilot-before.txt').read()
before_words = set(before.split())
after_words = set(text.split())
# Body prose should be near-identical; only the numeric footnote
# markers (now real biblioref links) and the works-cited section's own
# text (now replaced by the generated bibliography's own rendering)
# are expected to change shape, not disappear as concepts.
print('before:', len(before), 'chars, after:', len(text), 'chars')
print('words only in before:', len(before_words - after_words))
print('words only in after:', len(after_words - before_words))
"
```
Expected: total character count is comparable (not a drastic drop indicating lost content); review
the word-diff output directly for anything that looks like lost, not just reformatted, content.

- [ ] **Step 9: This pilot does not rebuild the corpus's committed HTML -- `html5.xsl` itself needs
  to be retired, not patched to cope with this one document**

`docs/xsl/html5.xsl` cannot render `db:bibliography`/`db:biblioref` at all. Rebuilding this
document's tracked `.html` through it would produce degraded, unstyled, unlinked output -- correct
XML, broken HTML. That is not a reason to accept `html5.xsl` as permanent: it is confirmation that
`html5.xsl` needs to be replaced by `docbook-xsl-ns` corpus-wide (Phase 2), not patched document-by-
document to render the new structure. This pilot leaves the tracked `.html` stale in this one narrow
respect (works-cited section and inline markers) only because rebuilding the whole corpus's HTML
output is out of this plan's scope, not because the old renderer is being kept. Confirm the `.html`
is untouched by this task specifically:
```bash
git status --short docs/court-record/theory/federal-constitutional/extensions/llms-as-categorical-systems.html
```
Expected: no output (the `.html` file is unmodified).

- [ ] **Step 10: Run the full test suite**

```bash
python3 -m unittest discover -s docs/scripts/tests -p "test_*.py"
```
Expected: all pass (this pilot conversion must not regress anything else in the corpus).

- [ ] **Step 11: Commit**

```bash
git add docs/court-record/theory/federal-constitutional/extensions/llms-as-categorical-systems.xml \
        docs/court-record/theory/federal-constitutional/extensions/llms-as-categorical-systems/ \
        docs/court-record/theory/federal-constitutional/extensions/llms-as-categorical-systems.html \
        docs/bibliography/entries/
git commit -m "feat: pilot-convert llms-as-categorical-systems to real DocBook bibliography structure (82 entries, Category A, verified against real DocBook 5.2 grammar and its Google Drive original)"
```

---

### Task 7: Full-corpus baseline re-measurement and Phase 2 scoping

**Files:**
- None modified -- this task produces a report, not code changes.

**Interfaces:**
- Consumes: `measure_citation_conformance.py`, `corpus_wide_report()`,
  `corpus_wide_numbered_citation_report()` (all existing).

- [ ] **Step 1: Re-run the full corpus-wide measurement**

```bash
python3 docs/scripts/measure_citation_conformance.py
```
Expected output shape (exact numbers will differ from the original 2026-07-26 baseline by exactly
the pilot document's contribution):
```
Non-standard (works-cited) entries: <baseline - 0, the pilot had no flat works-cited entries> across <88 or 87> documents
Standard (biblioentry/bibliomixed) entries: 82
Citation markers: <resolved count including the pilot's markers> resolved, <unresolved count> unresolved
Deep-Research-style numbered citation pattern: <95> documents, <6109 minus the pilot's marker count> plausible markers, 88 implausible/unrelated
```
The document count here (originally 96, now one fewer) comes from `measure_citation_conformance
.py`'s own `corpus_wide_numbered_citation_report()`. It is not required to match
`classify_numbered_citations.py`'s 95-document count from the audit CSV (Task 5) -- those are two
independently-built measurement tools over overlapping but not identical criteria; a 1-document
difference between them is expected and was already noted, not silently reconciled, when Task 5
was designed.

- [ ] **Step 2: Record the confirmed A/B split size for Phase 2 scoping**

```bash
python3 -c "
import json
data = json.load(open('docs/bibliography/numbered-citation-classification.json'))
a_count = sum(1 for v in data.values() if v['category'] == 'A')
b_count = sum(1 for v in data.values() if v['category'] == 'B')
print(f'Category A (mechanically convertible): {a_count} documents, 1 already converted this phase')
print(f'Category B (needs-research): {b_count} documents')
"
```

- [ ] **Step 3: Update the SDD progress ledger**

```bash
cat >> .superpowers/sdd/progress.md << 'EOF'

## Citation Standardization Phase 1 Complete

Built and verified end-to-end: standalone biblioentry architecture (Task 1),
eyecite venv + classification wrapper (Task 2), confirmed the official
docbook-xsl-ns stylesheets render db:bibliography/biblioentry/biblioref
correctly with zero custom XSLT (Task 3 -- html5.xsl is non-standard and
not modified in this plan for sequencing reasons only; its full retirement
and replacement by docbook-xsl-ns is Phase 2 scope), the Category-A numbered-citation converter
built on audit_footnote_links.py's existing detection/exclusion logic rather
than duplicating it (Task 4), the full numbered-citation-document
classification manifest derived primarily from the existing
footnote-citation-audit.csv report (Task 5), and one fully-converted,
fully-verified pilot document (Task 6, llms-as-categorical-systems: 82
entries, 0 remaining non-standard content, verified against the real
DocBook 5.2 grammar, re-measured via measure_citation_conformance.py,
content-preservation diffed against the pre-conversion rendering via
docbook-xsl-ns).

Ready for a Phase 2 plan: bulk-convert the remaining confirmed Category A
documents via the same Task 4 tooling; the flat works-cited entries (5,482,
88 documents) via eyecite-gated automated conversion per the design's
Section 6; Category B documents get needs-research entries only, never
fabricated content.
EOF
git add .superpowers/sdd/progress.md
git commit -m "docs: log Citation Standardization Phase 1 completion in the SDD progress ledger"
```

---

## Self-Review

**Spec coverage:** Design Section 3 (entry architecture) → Task 1. Section 4 (`@role` typing) →
Task 1 + Task 2 (eyecite drives the role, though full corpus-wide auto-typing of flat entries via
eyecite's extraction-aid role is Phase 2 scope, not this plan -- the pilot document's entries all
use `role="secondary"` since none of its 82 sources are legal citations). Section 5 (eyecite's
three roles) → Task 2 builds the validator; extraction-aid and full needs-research flagging at
corpus scale are exercised in Phase 2, not this narrower pilot. Section 6 (migration strategy) →
Task 6 is exactly the "automated, gated by verification" path for one Category A document; Section
7's explicit out-of-scope items (graph export, researching needs-research entries, session
recovery) are correctly not attempted anywhere in this plan.

**2026-07-26 mid-writing revision, noted here for the record:** Tasks 3-5 were substantially
revised after a fresh review of the hand-rolled-vs-industry-standard landscape surfaced three
findings before any task was executed: `audit_footnote_links.py` already solves marker
detection/exclusion more rigorously than this plan's first draft (Task 4 rewritten to reuse it,
not duplicate it); its own pre-generated report already gives most of the Category A/B signal
(Task 5 rewritten to derive from it, not re-research all ~96 documents by hand); and the official
`docbook-xsl-ns` stylesheets already render this project's new structure correctly, including a
better element choice (`<biblioref>`, not `<citation>`) discovered in the course of verifying that.
Task 3 was rewritten from an `html5.xsl` modification to pure verification -- confirming
`docbook-xsl-ns` renders correctly, not exempting `html5.xsl` from eventual replacement, which
remains real Phase 2 scope. All code in the current task text was independently re-verified live
after each change, not left as originally drafted.

**Placeholder scan:** No TBD/TODO; every step has complete, concrete code or an exact command.

**Type consistency:** `write_biblioentry(entry_path, key, role, title, href=None)` (Task 1) is
called identically in Task 4's `build_entry_key_map()`. `ENTRIES_DIR`, `derive_entry_key()` (Task
1) are imported and used identically in Task 4. `_is_excluded_context()` (existing,
`audit_footnote_links.py`) is imported, not redefined, in Task 4; Task 4 emits `<biblioref
linkend="KEY"/>` consistently across its implementation, tests, and the pilot task's own
verification steps -- no lingering `<citation>` references outside historical design-correction
prose describing what the first draft did. `classify_from_audit_csv()` (Task 5) is consumed with
the same signature in Task 6's Step 1 and Task 7's Step 2.
`measure_citation_conformance()`/`measure_numbered_citation_pattern()` (existing) are called with
the same signatures throughout Task 6/7.

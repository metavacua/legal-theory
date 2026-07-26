# DocBook-Native Corpus Standardization — Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make every document in the `docs/` legal-theory corpus (118+ documents + the 2-article `llm-database-theory` paper) genuinely valid against the real, unmodified OASIS DocBook 5.2 RELAX NG grammar — replacing the custom, paper-scoped `docs/schema/docbook-corpus.rnc` and the `dc:*`-in-`<info>`-with-sibling-title shape with native DocBook elements.

**Architecture:** Three verified, corpus-wide structural defects get fixed: `<title>` moves inside `<info>` (DocBook requires this); `docs/common/shared-metadata.xml`'s `<shared>` wrapper (not a valid DocBook element) is replaced by two small files (`authorgroup.xml`, `legalnotice.xml`) whose roots are themselves real DocBook elements, included via plain XInclude; and `dc:*` metadata fields are replaced by their native DocBook equivalents wherever one exists (only `dc:type="Text"` has no native equivalent and remains). The real DocBook 5.2 RNG is fetched from OASIS at build/validate time and becomes the sole structural validator; a Python tree-walk (not RELAX NG or Schematron — both confirmed to have real gaps in this pipeline's toolchain) enforces this project's own field-completeness policy on top.

**Tech Stack:** RELAX NG (the real OASIS DocBook 5.2 grammar, `jing`), XSLT 1.0 (`docs/xsl/html5.xsl`), Python 3 stdlib (`xml.etree.ElementTree`, `unittest`, `subprocess`, `urllib.request` or `curl` via `subprocess`), `xmllint`, `git`. No new dependencies — this plan predates the `lxml` migration (a separate, unaffected task in the corresponding ontology-layer follow-on plan).

## Global Constraints

- Every native-element replacement in this plan was individually verified against the real, OASIS-fetched DocBook 5.2 RNG (`https://docs.oasis-open.org/docbook/docbook/v5.2/os/rng/docbookxi.rnc`) before being written here — not the Debian `docbook5-xml` 5.0 package, which is close but not version-identical. Re-verify with the same fetched file if anything here seems not to validate; do not fall back to assuming the 5.0 package is equivalent.
- `jing`'s XInclude resolution on this host is unconditional (its wrapper hard-codes Xerces's `XIncludeParserConfiguration`) — `jing -c <schema> <file>` validates the fully-resolved document, not the literal unresolved markup. Do not add any XPointer-scheme `xi:include` (`xpointer="..."`) anywhere — confirmed unsupported by this `jing`/Xerces combination (`SchemeUnsupported` fatal error). Only plain, whole-root XInclude is used anywhere in this plan.
- `derive_date`, `derive_identifier`, `derive_subject` (all in `docs/scripts/convert_to_docbook.py`, already implemented and tested) are reused **unchanged** — only the XML element each value gets written into changes, not the derivation logic.
- `write_metadata(meta_path, title, subject=None)`'s signature does not change in this plan — only its internal output shape changes. Every existing call site (`convert_to_docbook.py`, `atomize_existing_document.py`, `build_bibliography.py`) keeps working without modification to the call itself.
- `REPO_ROOT` (`docs/scripts/convert_to_docbook.py`) remains the one source of truth for repo-root-relative path math.
- This plan does **not** add the `xlink:href` SKOS-concept attribute to `<subjectterm>` — that's ontology-layer enrichment (a follow-on plan, once this corpus is structurally valid). This plan's `<subjectterm>` carries text only (from the already-existing `derive_subject()`), leaving the attribute for later, additive work.
- This plan does not attempt every possible DocBook 5.2 conformance nuance — only the three defects verified corpus-wide (title placement, the `<shared>` wrapper, `dc:*` vs. native fields) plus whatever the real schema additionally flags once those are fixed (surfaced and fixed during Task 8's full-corpus verification, not assumed away in advance).
- New Python code follows existing `docs/scripts/` conventions: `unittest.TestCase`, docstrings explaining the non-obvious *why*, no hand-rolled XML string-building for attribute content that could contain untrusted characters.

---

## File Structure

- Create `docs/common/authorgroup.xml` — root `<authorgroup>`, real DocBook element, replaces the author portion of `shared-metadata.xml`.
- Create `docs/common/legalnotice.xml` — root `<legalnotice>`, real DocBook element (with an embedded SPDX `<link>`), replaces the rights/license portion of `shared-metadata.xml`.
- Delete `docs/common/shared-metadata.xml` — its root `<shared>` element is not valid DocBook (verified).
- Modify `docs/scripts/convert_to_docbook.py` — add `fetch_docbook_schema()`; rewrite `write_metadata()`; rewrite `wrap_fragment()` to stop emitting a sibling `<title>`; rewrite `validate()` to use the fetched real schema; add `validate_dcterms_completeness()`.
- Modify `docs/scripts/atomize_existing_document.py` — its title round-trip logic reads the now-native `<title>` instead of `dc:title`.
- Modify `docs/xsl/html5.xsl` — read native elements (`db:title`, `db:pubdate`, `db:biblioid`, `db:legalnotice`, `db:subjectset//db:subjectterm`, `@xml:lang`) instead of `dc:*` for the HTML `<title>`, `DC.*` meta tags, and the h1/byline header.
- Create `docs/scripts/migrate_to_native_metadata.py` — one-shot corpus-wide migration: regenerates every `.meta.xml` through the fixed `write_metadata()` and strips the now-redundant sibling `<title>` from every content `.xml` file.
- Modify `docs/schema/docbook-corpus.rnc` → **deleted**.
- Modify `.github/workflows/build-corpus.yml`, `.github/workflows/build-papers.yml`, `docs/papers/ai_and_ip/llm-database-theory/Makefile` — fetch the real DocBook 5.2 RNG and validate against it instead of the deleted custom schema.
- Modify `docs/scripts/tests/test_convert_to_docbook.py` — new/updated test coverage for every change above.
- Modify `docs/papers/ai_and_ip/llm-database-theory/src/01-llm-database-theory.meta.xml`, `02-legal-corpus-connections.meta.xml` — same native-shape migration as the rest of the corpus (the paper predates and is included in this fix).

---

### Task 1: Real-schema fetch helper, and native shared-boilerplate files

**Files:**
- Modify: `docs/scripts/convert_to_docbook.py` (add `fetch_docbook_schema()`)
- Create: `docs/common/authorgroup.xml`
- Create: `docs/common/legalnotice.xml`
- Delete: `docs/common/shared-metadata.xml`
- Modify: `.gitignore` (ignore the schema download cache)
- Test: `docs/scripts/tests/test_convert_to_docbook.py`

**Interfaces:**
- Produces: `fetch_docbook_schema() -> Path` — downloads-and-caches the real DocBook 5.2 RNG on first call, returns the cached path on every call. Consumed by Task 7's rewritten `validate()` and by CI/Makefile (Task 8, via a matching `curl` step to the same cache path).

- [ ] **Step 1: Write the failing test**

Add to `docs/scripts/tests/test_convert_to_docbook.py`:
```python
class TestFetchDocbookSchema(unittest.TestCase):
    def test_fetches_and_caches_the_real_schema(self):
        from convert_to_docbook import fetch_docbook_schema, REPO_ROOT
        cache_path = REPO_ROOT / ".cache" / "docbook-5.2" / "docbookxi.rnc"
        if cache_path.exists():
            cache_path.unlink()
        path = fetch_docbook_schema()
        self.assertEqual(path, cache_path)
        self.assertTrue(path.exists())
        content = path.read_text(encoding="utf-8")
        self.assertIn("docbook.org/ns/docbook", content)

    def test_second_call_reuses_cache_without_refetching(self):
        from convert_to_docbook import fetch_docbook_schema
        path = fetch_docbook_schema()
        mtime_before = path.stat().st_mtime
        path2 = fetch_docbook_schema()
        self.assertEqual(path, path2)
        self.assertEqual(path.stat().st_mtime, mtime_before)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python3 -m unittest docs.scripts.tests.test_convert_to_docbook.TestFetchDocbookSchema -v`
Expected: `ImportError: cannot import name 'fetch_docbook_schema'`.

- [ ] **Step 3: Implement `fetch_docbook_schema()`**

Add to `docs/scripts/convert_to_docbook.py`, near `REPO_ROOT`:
```python
DOCBOOK_RNC_URL = "https://docs.oasis-open.org/docbook/docbook/v5.2/os/rng/docbookxi.rnc"
DOCBOOK_SCHEMA_CACHE = REPO_ROOT / ".cache" / "docbook-5.2" / "docbookxi.rnc"


def fetch_docbook_schema():
    """Path to the real, official DocBook 5.2 XInclude-aware RELAX NG
    compact schema, fetched from OASIS on first use and cached locally
    (not vendored into the repo -- kept out of git, matching how this
    pipeline already installs jing/xmllint/xsltproc via apt at build
    time rather than committing them). Subsequent calls reuse the
    cached file without a network round-trip."""
    if not DOCBOOK_SCHEMA_CACHE.exists():
        DOCBOOK_SCHEMA_CACHE.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ["curl", "-fsSL", "-o", str(DOCBOOK_SCHEMA_CACHE), DOCBOOK_RNC_URL],
            check=True,
        )
    return DOCBOOK_SCHEMA_CACHE
```

Add to `.gitignore`:
```
.cache/
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python3 -m unittest docs.scripts.tests.test_convert_to_docbook.TestFetchDocbookSchema -v`
Expected: `PASS` (requires network access to `docs.oasis-open.org`; if unavailable in this environment, the test will report a `curl` failure — install/verify network access before proceeding, since every later task in this plan depends on this schema being fetchable).

- [ ] **Step 5: Create `docs/common/authorgroup.xml`**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<authorgroup xmlns="http://docbook.org/ns/docbook">
  <author>
    <personname>
      <firstname>Ian</firstname>
      <othername role="middle">D.L.N.</othername>
      <surname>McLean</surname>
    </personname>
    <email>metavacua@gmail.com</email>
    <uri>https://github.com/metavacua</uri>
  </author>
</authorgroup>
```

- [ ] **Step 6: Create `docs/common/legalnotice.xml`**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<legalnotice xmlns="http://docbook.org/ns/docbook" xmlns:xlink="http://www.w3.org/1999/xlink">
  <para>Copyright &#169; 2026 Ian D.L.N. McLean. Licensed under <link xlink:href="https://spdx.org/licenses/CC-BY-SA-4.0">Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)</link>. This document publishes general legal analysis and does not constitute legal advice.</para>
</legalnotice>
```

- [ ] **Step 7: Delete the invalid shared wrapper and verify the two replacements individually**

```bash
git rm docs/common/shared-metadata.xml
python3 -c "from docs.scripts.convert_to_docbook import fetch_docbook_schema; print(fetch_docbook_schema())"
jing -c "$(python3 -c 'from docs.scripts.convert_to_docbook import fetch_docbook_schema; print(fetch_docbook_schema())')" docs/common/authorgroup.xml
jing -c "$(python3 -c 'from docs.scripts.convert_to_docbook import fetch_docbook_schema; print(fetch_docbook_schema())')" docs/common/legalnotice.xml
```
Expected: both `jing` calls succeed silently (exit 0) — each file is independently valid DocBook, verified directly against the real schema, not assumed.

- [ ] **Step 8: Commit**

```bash
git add docs/scripts/convert_to_docbook.py docs/scripts/tests/test_convert_to_docbook.py \
        docs/common/authorgroup.xml docs/common/legalnotice.xml .gitignore
git commit -m "feat: fetch the real DocBook 5.2 RNG from OASIS, replace the invalid shared-metadata.xml wrapper with real DocBook authorgroup.xml/legalnotice.xml"
```

---

### Task 2: Rewrite `write_metadata()` to the native-first shape

**Files:**
- Modify: `docs/scripts/convert_to_docbook.py`
- Test: `docs/scripts/tests/test_convert_to_docbook.py`

**Interfaces:**
- Consumes: `fetch_docbook_schema()` (Task 1), `derive_date`/`derive_identifier`/`derive_subject` (existing, unchanged), `docs/common/authorgroup.xml`/`legalnotice.xml` (Task 1).
- Produces: `write_metadata(meta_path, title, subject=None)` — same signature, new output shape. Every existing call site keeps working unmodified.

- [ ] **Step 1: Write the failing test**

Add to `docs/scripts/tests/test_convert_to_docbook.py`:
```python
class TestWriteMetadataNativeShape(unittest.TestCase):
    def test_emits_native_title_inside_info(self):
        from convert_to_docbook import write_metadata, REPO_ROOT, DB_NS
        out_dir = Path(tempfile.mkdtemp(dir=REPO_ROOT / "docs" / "wip"))
        self.addCleanup(shutil.rmtree, out_dir)
        meta_path = out_dir / "sample.meta.xml"
        write_metadata(meta_path, "Sample Title")

        root = ET.parse(meta_path).getroot()
        self.assertEqual(root.tag, f"{{{DB_NS}}}info")
        title_el = root.find(f"{{{DB_NS}}}title")
        self.assertIsNotNone(title_el)
        self.assertEqual(title_el.text, "Sample Title")

    def test_emits_native_pubdate_biblioid_subjectset(self):
        from convert_to_docbook import write_metadata, REPO_ROOT, DB_NS
        out_dir = Path(tempfile.mkdtemp(dir=REPO_ROOT / "docs" / "wip"))
        self.addCleanup(shutil.rmtree, out_dir)
        meta_path = out_dir / "sample.meta.xml"
        write_metadata(meta_path, "Sample Title", subject="work in progress")

        root = ET.parse(meta_path).getroot()
        self.assertRegex(root.find(f"{{{DB_NS}}}pubdate").text, r"^\d{4}-\d{2}-\d{2}$")
        biblioid = root.find(f"{{{DB_NS}}}biblioid")
        self.assertEqual(biblioid.get("class"), "uri")
        self.assertTrue(biblioid.text.startswith("https://github.com/metavacua/legal-theory/blob/main/"))
        subjectterm = root.find(f"{{{DB_NS}}}subjectset/{{{DB_NS}}}subject/{{{DB_NS}}}subjectterm")
        self.assertEqual(subjectterm.text, "work in progress")

    def test_dc_type_is_the_only_remaining_dcterms_element(self):
        from convert_to_docbook import write_metadata, REPO_ROOT, DB_NS, DC_NS
        out_dir = Path(tempfile.mkdtemp(dir=REPO_ROOT / "docs" / "wip"))
        self.addCleanup(shutil.rmtree, out_dir)
        meta_path = out_dir / "sample.meta.xml"
        write_metadata(meta_path, "Sample Title")

        root = ET.parse(meta_path).getroot()
        dc_elements = [el for el in root.iter() if el.tag.startswith(f"{{{DC_NS}}}")]
        self.assertEqual(len(dc_elements), 1)
        self.assertEqual(dc_elements[0].tag, f"{{{DC_NS}}}type")
        self.assertEqual(dc_elements[0].text, "Text")

    def test_includes_authorgroup_and_legalnotice(self):
        from convert_to_docbook import write_metadata, REPO_ROOT, XI_NS
        out_dir = Path(tempfile.mkdtemp(dir=REPO_ROOT / "docs" / "wip"))
        self.addCleanup(shutil.rmtree, out_dir)
        meta_path = out_dir / "sample.meta.xml"
        write_metadata(meta_path, "Sample Title")

        root = ET.parse(meta_path).getroot()
        includes = root.findall(f"{{{XI_NS}}}include")
        hrefs = {el.get("href") for el in includes}
        self.assertEqual(len(includes), 2)
        self.assertTrue(any(h.endswith("common/authorgroup.xml") for h in hrefs))
        self.assertTrue(any(h.endswith("common/legalnotice.xml") for h in hrefs))

    def test_full_resolved_document_validates_against_real_docbook_5_2(self):
        from convert_to_docbook import write_metadata, fetch_docbook_schema, REPO_ROOT
        out_dir = Path(tempfile.mkdtemp(dir=REPO_ROOT / "docs" / "wip"))
        self.addCleanup(shutil.rmtree, out_dir)
        meta_path = out_dir / "sample.meta.xml"
        write_metadata(meta_path, "Sample Title", subject="work in progress")
        article_path = out_dir / "sample.xml"
        article_path.write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<article xmlns="http://docbook.org/ns/docbook" '
            'xmlns:xi="http://www.w3.org/2001/XInclude" version="5.2" xml:id="s" xml:lang="en">\n'
            '  <xi:include href="sample.meta.xml"/>\n'
            '  <para>Body content.</para>\n'
            '</article>\n',
            encoding="utf-8",
        )
        schema = fetch_docbook_schema()
        result = subprocess.run(
            ["jing", "-c", str(schema), str(article_path)],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python3 -m unittest docs.scripts.tests.test_convert_to_docbook.TestWriteMetadataNativeShape -v`
Expected: failures — the current implementation still emits `<info>` with `dc:title`/`dc:date`/`dc:identifier`/`dc:subject` and one `xi:include` to the now-deleted `shared-metadata.xml`.

- [ ] **Step 3: Rewrite `write_metadata()`**

Replace the current implementation in `docs/scripts/convert_to_docbook.py`:
```python
def write_metadata(meta_path, title, subject=None):
    meta_path = Path(meta_path)
    docs_dir = (REPO_ROOT / "docs").resolve()
    meta_dir = meta_path.resolve().parent
    depth = len(meta_dir.relative_to(docs_dir).parts)
    prefix = "../" * depth + "common/"
    escaped_title = xml_escape(title)
    resolved_subject = subject if subject is not None else derive_subject(meta_path)
    date = derive_date(meta_path)
    identifier = derive_identifier(meta_path)
    content = f"""<?xml version="1.0" encoding="UTF-8"?>
<info xmlns="{DB_NS}" xmlns:dc="http://purl.org/dc/terms/" xmlns:xi="{XI_NS}">
  <title>{escaped_title}</title>
  <pubdate>{date}</pubdate>
  <biblioid class="uri">{xml_escape(identifier)}</biblioid>
  <subjectset><subject><subjectterm>{xml_escape(resolved_subject)}</subjectterm></subject></subjectset>
  <dc:type>Text</dc:type>
  <xi:include href="{prefix}authorgroup.xml" />
  <xi:include href="{prefix}legalnotice.xml" />
</info>
"""
    meta_path.write_text(content, encoding="utf-8")
```
Note: `dc:type` is the one deliberate, retained DCTERMS extension element (per Global Constraints — no native DocBook equivalent for the DCMI Type Vocabulary). Everything else in this function's output is now a native DocBook element.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python3 -m unittest docs.scripts.tests.test_convert_to_docbook.TestWriteMetadataNativeShape -v`
Expected: all 5 `PASS`, including the full real-schema validation test — this is the single most important test in this plan; if it fails, do not proceed to later tasks until it's fixed.

- [ ] **Step 5: Commit**

```bash
git add docs/scripts/convert_to_docbook.py docs/scripts/tests/test_convert_to_docbook.py
git commit -m "feat: rewrite write_metadata() to emit native DocBook elements (title/pubdate/biblioid/subjectset) instead of dc:* extensions, verified against the real DocBook 5.2 schema"
```

---

### Task 3: Stop emitting the invalid sibling `<title>`, fix downstream title readers

**Files:**
- Modify: `docs/scripts/convert_to_docbook.py` (`wrap_fragment()`)
- Modify: `docs/scripts/atomize_existing_document.py`
- Test: `docs/scripts/tests/test_convert_to_docbook.py`, `docs/scripts/tests/test_atomize_existing_document.py`

**Interfaces:**
- Consumes: nothing new.
- Produces: `wrap_fragment()` keeps its exact existing signature and return type (`(article_element, unwrapped_bool)`) — only the article's child shape changes (no more sibling `<title>`).

Verified directly (this session): the real corpus's actual article shell is `<article><xi:include href="X.meta.xml"/><title>PageTitle</title>...</article>` — the sibling `<title>` is a **direct child of `<article>`**, confirmed rejected by the real DocBook 5.2 grammar (`element "title" not allowed here`). `docs/xsl/html5.xsl` already has `<xsl:template match="db:article/db:title | db:article/db:subtitle"/>` (an empty, suppressing template) and renders the visible page heading from `db:info`'s own template instead — so removing the sibling `<title>` does not remove any currently-rendered content; it removes dead, schema-invalid markup that was never actually used for rendering.

- [ ] **Step 1: Write the failing test**

Add to `docs/scripts/tests/test_convert_to_docbook.py`:
```python
class TestWrapFragmentNoSiblingTitle(unittest.TestCase):
    def test_article_has_no_direct_title_child(self):
        from convert_to_docbook import pandoc_to_docbook_fragment, wrap_fragment, DB_NS
        fragment = pandoc_to_docbook_fragment(self.fixtures / "flat.md")
        article, _ = wrap_fragment(fragment, "flat", "A Flat Document", "flat.meta.xml")
        direct_titles = [c for c in article if c.tag == f"{{{DB_NS}}}title"]
        self.assertEqual(direct_titles, [])

    def test_article_still_has_xi_include_and_body_content(self):
        from convert_to_docbook import pandoc_to_docbook_fragment, wrap_fragment, DB_NS, XI_NS
        fragment = pandoc_to_docbook_fragment(self.fixtures / "flat.md")
        article, _ = wrap_fragment(fragment, "flat", "A Flat Document", "flat.meta.xml")
        includes = [c for c in article if c.tag == f"{{{XI_NS}}}include"]
        self.assertEqual(len(includes), 1)
        self.assertEqual(includes[0].get("href"), "flat.meta.xml")
        self.assertTrue(any(c.tag == f"{{{DB_NS}}}para" for c in article))
```
(This test class lives in the same file as the existing `TestPandocAndWrapping` tests and reuses that class's `self.fixtures` setup — add it as a sibling `unittest.TestCase`, matching the existing pattern in the file for accessing `self.fixtures`.)

- [ ] **Step 2: Run the test to verify it fails**

Run: `python3 -m unittest docs.scripts.tests.test_convert_to_docbook.TestWrapFragmentNoSiblingTitle -v`
Expected: `test_article_has_no_direct_title_child` fails — `direct_titles` currently has one element.

- [ ] **Step 3: Remove the sibling `<title>` from `wrap_fragment()`**

In `docs/scripts/convert_to_docbook.py`, remove these two lines from `wrap_fragment()`:
```python
    title_el = ET.SubElement(article, f"{{{DB_NS}}}title")
    title_el.text = title
```
`wrap_fragment()`'s `title` parameter is still used elsewhere in the function (for the section-unwrapping duplicate-title check a few lines below — leave that logic as-is, it still needs `title` for comparison purposes even though no `<title>` element gets written into the tree anymore).

- [ ] **Step 4: Run the test to verify it passes**

Run: `python3 -m unittest docs.scripts.tests.test_convert_to_docbook.TestWrapFragmentNoSiblingTitle -v`
Expected: `PASS`. Also run the full existing `TestPandocAndWrapping`/`TestSplitIntoFragments` classes to confirm no regressions: `python3 -m unittest docs.scripts.tests.test_convert_to_docbook.TestPandocAndWrapping docs.scripts.tests.test_convert_to_docbook.TestSplitIntoFragments -v`.

- [ ] **Step 5: Fix `atomize_existing_document.py`'s title round-trip**

Read `docs/scripts/atomize_existing_document.py` around its title-extraction logic (currently `meta_root.find(f"{{{DC_NS}}}title")`, reading the old `dc:title`). Change:
```python
        title_el = meta_root.find(f"{{{DC_NS}}}title")
```
to:
```python
        title_el = meta_root.find(f"{{{DB_NS}}}title")
```
(`DB_NS` is already imported into this file from `convert_to_docbook` — confirm the existing import line includes it; if not, add it to the existing `from convert_to_docbook import (...)` statement.)

- [ ] **Step 6: Run `atomize_existing_document.py`'s existing test suite**

Run: `python3 -m unittest docs.scripts.tests.test_atomize_existing_document -v`
Expected: all pre-existing tests still pass (this file's own tests construct their own fixture `.meta.xml` content — if any fixture still uses `dc:title`, update it to native `<title>` to match; check the fixture files under `docs/scripts/tests/` this test module reads from).

- [ ] **Step 7: Commit**

```bash
git add docs/scripts/convert_to_docbook.py docs/scripts/atomize_existing_document.py \
        docs/scripts/tests/test_convert_to_docbook.py docs/scripts/tests/test_atomize_existing_document.py
git commit -m "fix: stop emitting the DocBook-invalid sibling <title>; read the now-native title in atomize_existing_document.py"
```

---

### Task 4: Update `html5.xsl` to read native elements

**Files:**
- Modify: `docs/xsl/html5.xsl`

**Interfaces:**
- Consumes: the native shape from Task 2 (`db:title`, `db:pubdate`, `db:biblioid`, `db:legalnotice`, `db:subjectset//db:subjectterm`, `db:authorgroup`) and the article's existing `@xml:lang` attribute.

Verified directly (this session): an XPath selector for a native DocBook element **must** use the `db:` prefix inside this stylesheet (`db:title`, not unprefixed `title` — unprefixed names in XPath resolve to "no namespace," confirmed empty when tested against real content, while `db:title` correctly resolves).

- [ ] **Step 1: Update the HTML `<title>` and `DC.*` meta tags**

In `docs/xsl/html5.xsl`, change:
```xml
        <title><xsl:value-of select="db:info/dc:title"/></title>

        <!-- Dublin Core meta tags -->
        <meta name="DC.title"       content="{db:info/dc:title}"/>
        <meta name="DC.creator"     content="{db:info//dc:creator}"/>
        <meta name="DC.subject"     content="{db:info/dc:subject}"/>
        <meta name="DC.description" content="{db:info/dc:description}"/>
        <meta name="DC.date"        content="{db:info/dc:date}"/>
        <meta name="DC.type"        content="{db:info//dc:type}"/>
        <meta name="DC.language"    content="{db:info//dc:language}"/>
        <meta name="DC.rights"      content="{db:info//dc:rights}"/>
```
to:
```xml
        <title><xsl:value-of select="db:info/db:title"/></title>

        <!-- Dublin Core meta tags (HTML meta-tag names are the DCMI-standard
             DC.* convention; sourced from native DocBook elements now that
             dc:* extension elements only remain where DocBook has no native
             equivalent -- see docs/superpowers/specs/2026-07-25-docbook-native-corpus-standardization-design.md) -->
        <meta name="DC.title"       content="{db:info/db:title}"/>
        <meta name="DC.creator"     content="{concat(db:info//db:authorgroup/db:author/db:personname/db:firstname, ' ', db:info//db:authorgroup/db:author/db:personname/db:surname)}"/>
        <meta name="DC.subject"     content="{db:info//db:subjectterm}"/>
        <meta name="DC.date"        content="{db:info/db:pubdate}"/>
        <meta name="DC.type"        content="{db:info/dc:type}"/>
        <meta name="DC.language"    content="{/db:article/@xml:lang}"/>
        <meta name="DC.rights"      content="{db:info//db:legalnotice}"/>
```
`DC.description` is dropped: no corpus document has ever populated a description via `write_metadata()` (only the hand-authored paper metadata once did, informally, and that field isn't part of the native mapping this plan establishes) — leaving a permanently-empty meta tag in place would be dead output, not a real regression. `DC.language` now reads the article's own `@xml:lang` attribute (already present on every article, e.g. `xml:lang="en"`) instead of a `dc:language` element, since DocBook's native attribute is the correct place for this, not a DCTERMS extension element.

- [ ] **Step 2: Update the `db:info` header template (h1/byline)**

In `docs/xsl/html5.xsl`, change:
```xml
  <xsl:template match="db:info">
    <header class="doc-header">
      <h1><xsl:value-of select="dc:title"/></h1>
      <p class="byline">
        By <xsl:value-of select=".//db:authorgroup/db:author/db:personname/db:firstname"/>
        <xsl:text> </xsl:text>
        <xsl:value-of select=".//db:authorgroup/db:author/db:personname/db:othername"/>
        <xsl:text> </xsl:text>
        <xsl:value-of select=".//db:authorgroup/db:author/db:personname/db:surname"/>
        <xsl:text> — </xsl:text>
        <xsl:value-of select="dc:date"/>
      </p>
      <xsl:apply-templates select="db:abstract"/>
    </header>
  </xsl:template>
```
to:
```xml
  <xsl:template match="db:info">
    <header class="doc-header">
      <h1><xsl:value-of select="db:title"/></h1>
      <p class="byline">
        By <xsl:value-of select=".//db:authorgroup/db:author/db:personname/db:firstname"/>
        <xsl:text> </xsl:text>
        <xsl:value-of select=".//db:authorgroup/db:author/db:personname/db:othername"/>
        <xsl:text> </xsl:text>
        <xsl:value-of select=".//db:authorgroup/db:author/db:personname/db:surname"/>
        <xsl:text> — </xsl:text>
        <xsl:value-of select="db:pubdate"/>
      </p>
      <xsl:apply-templates select="db:abstract"/>
    </header>
  </xsl:template>
```
(Only `dc:title`→`db:title` and `dc:date`→`db:pubdate` change; the authorgroup selectors were already correctly reading the native `db:authorgroup` structure and are untouched.)

- [ ] **Step 3: Suppress the now-nonexistent-but-still-safe-to-keep sibling-title template**

`<xsl:template match="db:article/db:title | db:article/db:subtitle"/>` (the empty, suppressing template) can stay as-is — after Task 3, no document has a `db:article/db:title` any more, so this template simply never matches. Leaving it costs nothing and protects against any future regression that reintroduces a sibling title. No change needed here.

- [ ] **Step 4: Rebuild a real document and verify manually**

```bash
python3 - <<'EOF'
import sys
sys.path.insert(0, "docs/scripts")
from convert_to_docbook import write_metadata, REPO_ROOT
write_metadata(REPO_ROOT / "docs" / "wip" / "_xsl_smoke_test.meta.xml", "XSLT Smoke Test", subject="work in progress")
EOF
cat > docs/wip/_xsl_smoke_test.xml <<'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<article xmlns="http://docbook.org/ns/docbook" xmlns:xi="http://www.w3.org/2001/XInclude" version="5.2" xml:id="smoke" xml:lang="en">
  <xi:include href="_xsl_smoke_test.meta.xml"/>
  <para>Body content.</para>
</article>
EOF
xsltproc --xinclude docs/xsl/html5.xsl docs/wip/_xsl_smoke_test.xml > /tmp/_xsl_smoke_test.html
grep -o '<title>[^<]*</title>' /tmp/_xsl_smoke_test.html
grep -o '<h1>[^<]*</h1>' /tmp/_xsl_smoke_test.html
grep 'DC\.' /tmp/_xsl_smoke_test.html
rm docs/wip/_xsl_smoke_test.xml docs/wip/_xsl_smoke_test.meta.xml /tmp/_xsl_smoke_test.html
```
Expected: `<title>XSLT Smoke Test</title>`, `<h1>XSLT Smoke Test</h1>`, and populated `DC.title`/`DC.creator`/`DC.subject`/`DC.date`/`DC.type`/`DC.language`/`DC.rights` meta tags with real values (not empty strings).

- [ ] **Step 5: Commit**

```bash
git add docs/xsl/html5.xsl
git commit -m "fix(xsl): read native title/pubdate/biblioid/legalnotice/subjectterm/xml:lang instead of dc:* extension elements"
```

---

### Task 5: Corpus-wide migration

**Files:**
- Create: `docs/scripts/migrate_to_native_metadata.py`
- Test: run against the real corpus (this task's own verification, not a unit-test fixture)

**Interfaces:**
- Consumes: `write_metadata()` (Task 2), `element_full_text()`, `DB_NS`, `DC_NS`, `REPO_ROOT` (all existing/updated).

- [ ] **Step 1: Write the migration script**

```python
"""One-shot corpus-wide migration to the native-DocBook metadata shape
(see docs/superpowers/specs/2026-07-25-docbook-native-corpus-standardization-design.md
and docs/superpowers/plans/2026-07-25-docbook-native-corpus-standardization-phase1.md).
For every corpus .meta.xml: regenerate it through the now-native
write_metadata(), reading the existing title from wherever it currently
lives (native <title> if already migrated, else the old dc:title -- so
this script is safe to re-run). For every corpus content .xml: remove
the now-invalid sibling <title> element, since the title now lives
inside <info> (pulled in via the meta.xml's own xi:include)."""

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from convert_to_docbook import REPO_ROOT, DB_NS, DC_NS, element_full_text, write_metadata  # noqa: E402

EXCLUDE_TOP_LEVEL = {"scripts"}


def find_corpus_meta_files():
    docs_dir = REPO_ROOT / "docs"
    for meta_path in sorted(docs_dir.rglob("*.meta.xml")):
        rel_parts = meta_path.resolve().relative_to(docs_dir).parts
        if rel_parts[0] in EXCLUDE_TOP_LEVEL:
            continue
        yield meta_path


def existing_title(meta_path):
    root = ET.parse(meta_path).getroot()
    native = root.find(f"{{{DB_NS}}}title")
    if native is not None:
        return element_full_text(native)
    old = root.find(f"{{{DC_NS}}}title")
    return element_full_text(old)


def strip_sibling_title(content_path):
    """Remove a direct <title> child of <article> in content_path, if
    present -- idempotent, so a document already migrated is untouched."""
    tree = ET.parse(content_path)
    root = tree.getroot()
    if root.tag != f"{{{DB_NS}}}article":
        return False
    sibling_titles = [c for c in root if c.tag == f"{{{DB_NS}}}title"]
    if not sibling_titles:
        return False
    for el in sibling_titles:
        root.remove(el)
    ET.indent(tree, space="  ")
    tree.write(content_path, encoding="unicode", xml_declaration=True)
    return True


def content_path_for_meta(meta_path):
    name = meta_path.name
    if name.endswith(".meta.xml"):
        return meta_path.parent / (name[: -len(".meta.xml")] + ".xml")
    return meta_path


def main(argv=None):
    meta_count = 0
    stripped_count = 0
    for meta_path in find_corpus_meta_files():
        title = existing_title(meta_path)
        write_metadata(meta_path, title)
        meta_count += 1

        content_path = content_path_for_meta(meta_path)
        if content_path.exists() and strip_sibling_title(content_path):
            stripped_count += 1

    print(f"OK: regenerated {meta_count} .meta.xml files, stripped sibling <title> from {stripped_count} content files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Run it against the real corpus**

```bash
python3 docs/scripts/migrate_to_native_metadata.py
```
Expected: `OK: regenerated <N> .meta.xml files, stripped sibling <title> from <M> content files` — `<N>` should match the corpus's total `.meta.xml` count (run `find docs -name '*.meta.xml' -not -path 'docs/scripts/*' | wc -l` to compare); `<M>` should be close to `<N>` (every document previously had the invalid sibling title).

Note this migration deliberately covers `docs/papers/**` too (unlike the earlier metadata-completeness plan's backfill, which excluded it) — the paper's two articles have exactly the same title-placement defect and need the same fix. Confirm this by checking that `docs/papers/ai_and_ip/llm-database-theory/src/01-llm-database-theory.meta.xml` and `02-legal-corpus-connections.meta.xml` were among the regenerated files (`git status --short` after running should show them modified).

- [ ] **Step 3: Spot-check and rebuild HTML**

```bash
cat docs/wip/jpa-and-city-cooperatives.meta.xml
xmllint --xinclude --noout docs/wip/jpa-and-city-cooperatives.xml
head -5 docs/wip/jpa-and-city-cooperatives.xml
```
Expected: the meta file now has native `<title>`/`<pubdate>`/`<biblioid>`/`<subjectset>` + `dc:type` + two `xi:include`s; the content file's well-formedness check passes; the content file's first lines no longer show a sibling `<title>`.

```bash
while IFS= read -r xml; do
  xsltproc --xinclude docs/xsl/html5.xsl "$xml" > "${xml%.xml}.html"
done < <(find docs -name '*.xml' -not -path '*/scratch/*' -not -path 'docs/papers/*' -not -path 'docs/scripts/*' | sort)
cd docs/papers/ai_and_ip/llm-database-theory && make html && cd -
git status --short docs | wc -l
```

- [ ] **Step 4: Commit**

```bash
git add docs/scripts/migrate_to_native_metadata.py
git add docs/cross-cutting docs/wip docs/court-record docs/proposals docs/bibliography docs/papers
git commit -m "feat: migrate the entire corpus (including the paper) to native DocBook metadata, removing the invalid sibling <title>"
```

---

### Task 6: Retire the custom schema; wire in the real DocBook 5.2 RNG

**Files:**
- Modify: `docs/scripts/convert_to_docbook.py` (`validate()`)
- Delete: `docs/schema/docbook-corpus.rnc`
- Modify: `.github/workflows/build-corpus.yml`, `.github/workflows/build-papers.yml`
- Modify: `docs/papers/ai_and_ip/llm-database-theory/Makefile`
- Test: `docs/scripts/tests/test_convert_to_docbook.py`

**Interfaces:**
- Consumes: `fetch_docbook_schema()` (Task 1).
- Produces: `validate(xml_path)` keeps its existing signature and return type (`list[str]` of errors) — only its internal schema source changes.

- [ ] **Step 1: Confirm the custom schema is no longer referenced anywhere else**

```bash
grep -rn "docbook-corpus.rnc" docs/ .github/ --include="*.py" --include="*.yml" --include="*.mk" 2>/dev/null
grep -rn "docbook-corpus.rnc" docs/papers/ai_and_ip/llm-database-theory/Makefile
```
Note every hit — each one gets updated in this task.

- [ ] **Step 2: Rewrite `validate()`**

In `docs/scripts/convert_to_docbook.py`, remove the now-unused `SCHEMA_PATH` constant and change:
```python
def validate(xml_path):
    errors = []
    wf = subprocess.run(
        ["xmllint", "--noout", "--xinclude", str(xml_path)],
        capture_output=True, text=True,
    )
    if wf.returncode != 0:
        errors.append(wf.stderr.strip())
        return errors  # schema validation is meaningless on malformed XML

    rng = subprocess.run(
        ["jing", "-c", str(SCHEMA_PATH), str(xml_path)],
        capture_output=True, text=True,
    )
    if rng.returncode != 0:
        errors.append(rng.stdout.strip() or rng.stderr.strip())
    return errors
```
to:
```python
def validate(xml_path):
    errors = []
    wf = subprocess.run(
        ["xmllint", "--noout", "--xinclude", str(xml_path)],
        capture_output=True, text=True,
    )
    if wf.returncode != 0:
        errors.append(wf.stderr.strip())
        return errors  # schema validation is meaningless on malformed XML

    rng = subprocess.run(
        ["jing", "-c", str(fetch_docbook_schema()), str(xml_path)],
        capture_output=True, text=True,
    )
    if rng.returncode != 0:
        errors.append(rng.stdout.strip() or rng.stderr.strip())
    return errors
```

- [ ] **Step 3: Run the existing `validate()` tests**

Run: `python3 -m unittest docs.scripts.tests.test_convert_to_docbook.TestValidateAndBuild -v`
Expected: `test_validate_accepts_well_formed_document` and the schema-related tests may need their fixtures updated if they assert against the OLD custom-schema error shape (e.g. `test_validate_rejects_well_formed_but_schema_invalid_document` — check what invalid-schema fixture it uses; it must still be something the REAL DocBook grammar also rejects, e.g. an unknown element name, not something that was only invalid under the old custom whitelist). Update any fixture that specifically relied on the old schema's narrower rules.

- [ ] **Step 4: Delete the custom schema**

```bash
git rm docs/schema/docbook-corpus.rnc
```

- [ ] **Step 5: Update the paper's Makefile**

Replace the `validate` target's RELAX NG section:
```makefile
	@echo "==> Custom RELAX NG validation"
	@which jing >/dev/null 2>&1 && \
	  for f in $(ARTICLES); do \
	    jing -c ../../../schema/docbook-corpus.rnc "$$f" && echo "    OK: $$f" || true; \
	  done || echo "    (jing not installed; skipping RELAX NG step)"
```
with:
```makefile
	@echo "==> Real DocBook 5.2 RELAX NG validation"
	@mkdir -p ../../../../.cache/docbook-5.2
	@test -f ../../../../.cache/docbook-5.2/docbookxi.rnc || \
	  curl -fsSL -o ../../../../.cache/docbook-5.2/docbookxi.rnc \
	    https://docs.oasis-open.org/docbook/docbook/v5.2/os/rng/docbookxi.rnc
	@which jing >/dev/null 2>&1 && \
	  for f in $(ARTICLES); do \
	    jing -c ../../../../.cache/docbook-5.2/docbookxi.rnc "$$f" && echo "    OK: $$f" || true; \
	  done || echo "    (jing not installed; skipping RELAX NG step)"
```
(Path depth: `docs/papers/ai_and_ip/llm-database-theory/` is 3 levels under `docs/`, so `../../../../` from there reaches the repo root, matching `REPO_ROOT / ".cache" / "docbook-5.2" / "docbookxi.rnc"` from Task 1 — the same cache file, whether populated by the Python helper or this `curl` step, whichever runs first.)

Also remove the now-stale `Metadata (info-element) validation` block if a prior session added one referencing `docbook-corpus.rnc` (check the Makefile's `validate` target for any such block and remove it — the real DocBook grammar now covers everything the old custom schema's `info-element` pattern was checking, structurally; project-specific policy is Task 7's job).

- [ ] **Step 6: Update `build-corpus.yml`**

Verified against the actual current file (the earlier metadata-completeness plan's Task 4, which would have added a `shared-metadata.xml`/`.meta.xml`-specific loop here, was never dispatched — this file is still at its original shape). Replace:
```yaml
      - name: Validate and rebuild corpus HTML
        run: |
          set -euo pipefail
          while IFS= read -r xml; do
            root_element="$(xmllint --xpath 'name(/*)' "$xml" 2>/dev/null || true)"
            if [ "$root_element" != "article" ]; then
              continue
            fi
            echo "== $xml =="
            xmllint --noout --xinclude "$xml"
            jing -c docs/schema/docbook-corpus.rnc "$xml"
            xsltproc --xinclude docs/xsl/html5.xsl "$xml" > "${xml%.xml}.html"
          done < <(find docs -name '*.xml' -not -path '*/scratch/*' -not -path 'docs/papers/*' -not -path 'docs/scripts/*' | sort)
```
to:
```yaml
      - name: Validate and rebuild corpus HTML
        run: |
          set -euo pipefail
          mkdir -p .cache/docbook-5.2
          test -f .cache/docbook-5.2/docbookxi.rnc || \
            curl -fsSL -o .cache/docbook-5.2/docbookxi.rnc \
              https://docs.oasis-open.org/docbook/docbook/v5.2/os/rng/docbookxi.rnc
          while IFS= read -r xml; do
            root_element="$(xmllint --xpath 'name(/*)' "$xml" 2>/dev/null || true)"
            if [ "$root_element" != "article" ]; then
              continue
            fi
            echo "== $xml =="
            xmllint --noout --xinclude "$xml"
            jing -c .cache/docbook-5.2/docbookxi.rnc "$xml"
            xsltproc --xinclude docs/xsl/html5.xsl "$xml" > "${xml%.xml}.html"
          done < <(find docs -name '*.xml' -not -path '*/scratch/*' -not -path 'docs/papers/*' -not -path 'docs/scripts/*' | sort)
```

- [ ] **Step 7: Update `build-papers.yml`**

Verified against the actual current file: it installs only `libxml2-utils xsltproc` (no `jing`) and runs only `make html` — there is no `Validate` step at all (the earlier metadata-completeness plan's Task 4, which would have added one, was never dispatched). Change:
```yaml
      - name: Install DocBook toolchain
        run: sudo apt-get update && sudo apt-get install -y libxml2-utils xsltproc

      - name: Build HTML
        working-directory: docs/papers/ai_and_ip/llm-database-theory
        run: make html
```
to:
```yaml
      - name: Install DocBook toolchain
        run: sudo apt-get update && sudo apt-get install -y libxml2-utils xsltproc jing

      - name: Validate
        working-directory: docs/papers/ai_and_ip/llm-database-theory
        run: make validate

      - name: Build HTML
        working-directory: docs/papers/ai_and_ip/llm-database-theory
        run: make html
```
(`make validate`'s real-schema fetch is handled by the Makefile itself, per Step 5 above — no separate `curl` step needed in this workflow.)

- [ ] **Step 8: Verify end to end**

```bash
cd docs/papers/ai_and_ip/llm-database-theory && make validate && cd -
find docs -name '*.xml' -not -path '*/scratch/*' -not -path 'docs/papers/*' -not -path 'docs/scripts/*' | while read -r xml; do
  root_element="$(xmllint --xpath 'name(/*)' "$xml" 2>/dev/null || true)"
  [ "$root_element" = "article" ] || continue
  jing -c .cache/docbook-5.2/docbookxi.rnc "$xml" || echo "FAILED: $xml"
done
```
Expected: `make validate` reports `OK:` for both paper articles under the real-schema check; the corpus-wide loop produces zero `FAILED:` lines. If any document fails, read the `jing` error, fix the specific document or a remaining gap in Task 2/5's migration, and re-run — do not proceed to Task 7 with known-failing documents.

- [ ] **Step 9: Commit**

```bash
git add docs/scripts/convert_to_docbook.py docs/scripts/tests/test_convert_to_docbook.py \
        .github/workflows/build-corpus.yml .github/workflows/build-papers.yml \
        docs/papers/ai_and_ip/llm-database-theory/Makefile
git rm docs/schema/docbook-corpus.rnc
git add docs/wip docs/cross-cutting docs/court-record docs/proposals docs/bibliography docs/papers/ai_and_ip/llm-database-theory/generated docs/papers/ai_and_ip/llm-database-theory/html
git commit -m "feat: retire the custom docbook-corpus.rnc entirely; validate every document against the real, fetched OASIS DocBook 5.2 grammar"
```

---

### Task 7: Project-specific policy validation (Python, not RNG/Schematron)

**Files:**
- Modify: `docs/scripts/convert_to_docbook.py` (add `validate_dcterms_completeness()`, wire into `validate()`)
- Test: `docs/scripts/tests/test_convert_to_docbook.py`

**Interfaces:**
- Produces: `validate_dcterms_completeness(xml_path) -> list[str]`, wired into `validate()`'s existing `errors` list (additive).

The real DocBook grammar correctly has no opinion about *this project's* policy (every document must have a title, a publication date, an identifier, and a fixed `dc:type`) — DocBook makes all of these optional. This check enforces the project's own requirement, in Python (matching the already-established pattern for exactly this class of constraint elsewhere in this corpus's tooling), not RELAX NG or Schematron.

- [ ] **Step 1: Write the failing tests**

Add to `docs/scripts/tests/test_convert_to_docbook.py`:
```python
class TestValidateDctermsCompleteness(unittest.TestCase):
    def _write(self, tmp, info_children):
        path = Path(tmp) / "sample.xml"
        path.write_text(
            '<?xml version="1.0"?>\n'
            '<article xmlns="http://docbook.org/ns/docbook" xmlns:dc="http://purl.org/dc/terms/" version="5.2" xml:id="s" xml:lang="en">\n'
            f'  <info>{info_children}</info>\n'
            '  <para>Body.</para>\n'
            '</article>\n',
            encoding="utf-8",
        )
        return path

    def test_complete_document_has_no_violations(self):
        from convert_to_docbook import validate_dcterms_completeness
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write(
                tmp,
                '<title>T</title><pubdate>2026-01-01</pubdate>'
                '<biblioid class="uri">https://example.com/x</biblioid><dc:type>Text</dc:type>',
            )
            self.assertEqual(validate_dcterms_completeness(path), [])

    def test_missing_title_is_flagged(self):
        from convert_to_docbook import validate_dcterms_completeness
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write(
                tmp,
                '<pubdate>2026-01-01</pubdate><biblioid class="uri">https://example.com/x</biblioid><dc:type>Text</dc:type>',
            )
            violations = validate_dcterms_completeness(path)
            self.assertEqual(len(violations), 1)
            self.assertIn("missing title", violations[0])

    def test_missing_pubdate_is_flagged(self):
        from convert_to_docbook import validate_dcterms_completeness
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write(
                tmp,
                '<title>T</title><biblioid class="uri">https://example.com/x</biblioid><dc:type>Text</dc:type>',
            )
            violations = validate_dcterms_completeness(path)
            self.assertEqual(len(violations), 1)
            self.assertIn("missing pubdate", violations[0])

    def test_missing_biblioid_is_flagged(self):
        from convert_to_docbook import validate_dcterms_completeness
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write(tmp, '<title>T</title><pubdate>2026-01-01</pubdate><dc:type>Text</dc:type>')
            violations = validate_dcterms_completeness(path)
            self.assertEqual(len(violations), 1)
            self.assertIn("missing biblioid", violations[0])

    def test_wrong_dc_type_value_is_flagged(self):
        from convert_to_docbook import validate_dcterms_completeness
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write(
                tmp,
                '<title>T</title><pubdate>2026-01-01</pubdate>'
                '<biblioid class="uri">https://example.com/x</biblioid><dc:type>ScholarlyArticle</dc:type>',
            )
            violations = validate_dcterms_completeness(path)
            self.assertEqual(len(violations), 1)
            self.assertIn("dc:type", violations[0])

    def test_real_corpus_document_has_no_violations(self):
        from convert_to_docbook import validate_dcterms_completeness, REPO_ROOT
        path = REPO_ROOT / "docs" / "wip" / "jpa-and-city-cooperatives.xml"
        self.assertEqual(validate_dcterms_completeness(path), [])
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python3 -m unittest docs.scripts.tests.test_convert_to_docbook.TestValidateDctermsCompleteness -v`
Expected: `ImportError: cannot import name 'validate_dcterms_completeness'`.

- [ ] **Step 3: Implement `validate_dcterms_completeness()` and wire it into `validate()`**

Add to `docs/scripts/convert_to_docbook.py`:
```python
def validate_dcterms_completeness(xml_path):
    """[violation message, ...] for a document (after XInclude resolution)
    missing any of this project's own required <info> fields: <title>,
    <pubdate>, <biblioid>, or a dc:type not equal to "Text". DocBook's
    own grammar correctly has no opinion about any of this -- these are
    this project's policy, not DocBook's, so they're enforced here in
    Python rather than forced into RELAX NG or Schematron (both
    confirmed, elsewhere in this project's tooling, to have real gaps
    in this environment's jing/xmllint combination)."""
    resolved = subprocess.run(
        ["xmllint", "--xinclude", str(xml_path)], capture_output=True, text=True, check=True,
    ).stdout
    root = ET.fromstring(resolved)
    info = root.find(f"{{{DB_NS}}}info")
    violations = []
    if info is None:
        return [f"{xml_path}: missing info"]
    if info.find(f"{{{DB_NS}}}title") is None:
        violations.append(f"{xml_path}: missing title")
    if info.find(f"{{{DB_NS}}}pubdate") is None:
        violations.append(f"{xml_path}: missing pubdate")
    if info.find(f"{{{DB_NS}}}biblioid") is None:
        violations.append(f"{xml_path}: missing biblioid")
    dc_type = info.find(f"{{{DC_NS}}}type")
    if dc_type is None or dc_type.text != "Text":
        violations.append(f"{xml_path}: dc:type must be exactly \"Text\", found {dc_type.text if dc_type is not None else None!r}")
    return violations
```

In `validate()`, add the new check after the RNG check:
```python
def validate(xml_path):
    errors = []
    wf = subprocess.run(
        ["xmllint", "--noout", "--xinclude", str(xml_path)],
        capture_output=True, text=True,
    )
    if wf.returncode != 0:
        errors.append(wf.stderr.strip())
        return errors  # schema validation is meaningless on malformed XML

    rng = subprocess.run(
        ["jing", "-c", str(fetch_docbook_schema()), str(xml_path)],
        capture_output=True, text=True,
    )
    if rng.returncode != 0:
        errors.append(rng.stdout.strip() or rng.stderr.strip())

    errors.extend(validate_dcterms_completeness(xml_path))
    return errors
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python3 -m unittest docs.scripts.tests.test_convert_to_docbook.TestValidateDctermsCompleteness -v`
Expected: all 6 `PASS`, including `test_real_corpus_document_has_no_violations` — confirms Task 5's migration already produced a conformant real document, not just the synthetic fixtures.

- [ ] **Step 5: Add a CLI wrapper for the shell-based CI loop**

Create `docs/scripts/check_dcterms_completeness.py`:
```python
"""CLI check for this project's DCTERMS-completeness policy (see
docs/superpowers/plans/2026-07-25-docbook-native-corpus-standardization-phase1.md,
Task 7) -- wired into the shell-based build-corpus.yml loop alongside
the real DocBook 5.2 jing check, so this project-specific policy is
enforced for every document, not only ones a Python caller happens to
invoke validate() on."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from convert_to_docbook import validate_dcterms_completeness  # noqa: E402


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    violations = []
    for path in argv:
        violations.extend(validate_dcterms_completeness(path))
    for v in violations:
        print(v, file=sys.stderr)
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
```

In `.github/workflows/build-corpus.yml`'s per-article loop, add, right after the `jing -c .cache/docbook-5.2/docbookxi.rnc "$xml"` line:
```yaml
            python3 docs/scripts/check_dcterms_completeness.py "$xml"
```

- [ ] **Step 6: Verify end to end against the whole corpus**

```bash
find docs -name '*.xml' -not -path '*/scratch/*' -not -path 'docs/papers/*' -not -path 'docs/scripts/*' | while read -r xml; do
  root_element="$(xmllint --xpath 'name(/*)' "$xml" 2>/dev/null || true)"
  [ "$root_element" = "article" ] || continue
  python3 docs/scripts/check_dcterms_completeness.py "$xml" || echo "FAILED: $xml"
done
cd docs/papers/ai_and_ip/llm-database-theory
python3 ../../../scripts/check_dcterms_completeness.py src/01-llm-database-theory.xml src/02-legal-corpus-connections.xml
cd -
```
Expected: zero `FAILED:` lines; the paper check exits 0 with no output.

- [ ] **Step 7: Commit**

```bash
git add docs/scripts/convert_to_docbook.py docs/scripts/check_dcterms_completeness.py \
        docs/scripts/tests/test_convert_to_docbook.py .github/workflows/build-corpus.yml
git commit -m "feat: enforce this project's DCTERMS-completeness policy in Python, corpus-wide, alongside the real DocBook 5.2 schema check"
```

---

### Task 8: Full-corpus verification and final commit

**Files:** none (verification only)

- [ ] **Step 1: Run the complete existing test suite**

```bash
python3 -m unittest discover -s docs/scripts/tests -v 2>&1 | tail -60
```
Expected: 100% pass (the 4 pre-existing, unrelated `test_atomize_existing_document.py` failures noted during the earlier metadata-completeness plan's Task 2 review should be independently re-checked here — confirm via `git stash` against this branch's pre-Phase-1 state whether they're still present and still unrelated, or whether this plan's changes happen to have fixed them incidentally).

- [ ] **Step 2: Full corpus + paper real-schema and policy sweep**

```bash
fail=0
find docs -name '*.xml' -not -path '*/scratch/*' -not -path 'docs/papers/*' -not -path 'docs/scripts/*' | while read -r xml; do
  root_element="$(xmllint --xpath 'name(/*)' "$xml" 2>/dev/null || true)"
  [ "$root_element" = "article" ] || continue
  jing -c .cache/docbook-5.2/docbookxi.rnc "$xml" > /tmp/jingerr 2>&1 || { echo "SCHEMA FAILED: $xml"; cat /tmp/jingerr; fail=1; }
  python3 docs/scripts/check_dcterms_completeness.py "$xml" || { echo "POLICY FAILED: $xml"; fail=1; }
done
cd docs/papers/ai_and_ip/llm-database-theory && make validate && cd -
echo "sweep complete"
```
Expected: zero `SCHEMA FAILED:`/`POLICY FAILED:` lines across the entire corpus; `make validate` succeeds for the paper.

- [ ] **Step 3: Confirm no orphaned references to the retired custom schema remain**

```bash
grep -rn "docbook-corpus.rnc\|shared-metadata.xml" docs/ .github/ 2>/dev/null
```
Expected: no output (both are fully retired).

- [ ] **Step 4: Final status check and commit any remaining drift**

```bash
git status --short
```
If anything is unstaged (e.g., regenerated HTML from Step 2's `make validate` run), review it, then:
```bash
git add -A
git commit -m "chore: Phase 1 verification sweep — full corpus + paper pass the real DocBook 5.2 grammar and this project's DCTERMS-completeness policy"
```
(Only run this commit if `git status --short` actually shows changes; skip if the tree is already clean.)

---

## Self-Review Notes

- **Spec coverage:** Every Phase 1 component from `docs/superpowers/specs/2026-07-25-docbook-native-corpus-standardization-design.md` has a task: schema fetch (Task 1), native shared boilerplate (Task 1), native `write_metadata()` (Task 2), sibling-title removal (Task 3), XSLT updates (Task 4), corpus-wide migration (Task 5), real-schema CI wiring (Task 6), Python policy check (Task 7), full verification (Task 8). The design doc's explicit deferral (SKOS `xlink:href` on `<subjectterm>`) is called out in Global Constraints as deliberately out of scope here, for the Phase 2 follow-on plan.
- **Placeholder scan:** no `TBD`/`[fill in]` markers; every code block is complete; every XML fixture is full, real content.
- **Type/signature consistency:** `write_metadata(meta_path, title, subject=None)` — signature unchanged from before this plan (Task 2 only changes its body); `validate(xml_path) -> list[str]` — signature unchanged, additive internals across Tasks 6 and 7; `wrap_fragment(fragment, xml_id, title, metadata_href) -> (Element, bool)` — signature unchanged, Task 3 only removes two lines from its body; `fetch_docbook_schema() -> Path` (Task 1) is a new function, consumed consistently by `validate()` (Task 6) and the CLI test in Task 2's Step 1; `validate_dcterms_completeness(xml_path) -> list[str]` (Task 7) matches the established `[violation, ...]` return convention used elsewhere in this codebase (e.g. the corresponding pattern in the earlier metadata-completeness plan's Task 10).

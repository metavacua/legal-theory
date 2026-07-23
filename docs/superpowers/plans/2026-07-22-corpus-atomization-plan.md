# Corpus Atomization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Decompose the corpus's monolithic DocBook documents (117 corpus documents + the
flagship paper's 2 articles) into a thin shell `.xml` per document plus one fragment file per
top-level section, and deduplicate the currently-100%-duplicated per-document metadata
boilerplate into one shared file — both via XInclude, requiring no changes to the existing
`xmllint --xinclude` / `jing` / `xsltproc --xinclude` build commands.

**Architecture:** `convert_to_docbook.py` gains a `split_into_fragments()` function used both
by fresh Markdown conversions and by a new one-off migration script
(`atomize_existing_document.py`) that mechanically migrates the 117+2 already-converted
documents in place. `write_metadata()` is rewritten to emit a minimal per-document `.meta.xml`
that XIncludes a new `docs/common/shared-metadata.xml`. Two XSLT stylesheets
(`html5.xsl`, `latex.xsl`) get a small, backward-compatible XPath relaxation to tolerate the
resulting extra wrapper element. `build-corpus.yml` is updated to discriminate CI build targets
by root element instead of file path, since fragment files are no longer excludable by path
pattern alone.

**Tech Stack:** Python 3 (stdlib `xml.etree.ElementTree`, `subprocess`), `pandoc`, `xmllint`,
`jing`, `xsltproc` — same toolchain already in use, no new dependencies.

## Global Constraints

- Only **one level** of section splitting — nested subsections stay embedded in their parent
  fragment. Never recursively re-split.
- No fragment catalog, index, or "what includes this file" tooling.
- No changes to `docs/index.md` — shell files keep their existing filenames and locations.
- No changes to the paper's `Makefile` — `wildcard src/0*.xml` already only matches files
  directly in `src/`, unaffected by fragments living in a subdirectory.
- The paper's `00-metadata.xml` shares only the fields that are simple, unqualified leaf values
  with no paper-specific variation: `dc:publisher`, `dc:language`, `dc:rights`. Its `dc:creator`
  (credits AI research assistance), full `authorgroup` (includes a `<uri>` the shared block
  doesn't have), `legalnotice`, `dc:title`, `dc:date`, `dc:subject`, `dc:description`,
  `abstract`, and the Schema.org JSON-LD block all stay local, unchanged. (This is a resolved
  simplification of spec Section 6's slightly ambiguous wording — attempting to share only
  *part* of `authorgroup` while keeping `<uri>` local would require element-level splicing the
  whole-element XInclude mechanism this design relies on doesn't support cleanly. If this
  reads differently than intended, flag it — it's a small, reversible scope note, not a
  structural decision.)
- `REPO_ROOT`, `SCHEMA_PATH`, `HTML5_XSL_PATH` are already defined in `convert_to_docbook.py`
  (module-level, near the bottom of the file) — reuse them, don't redefine.
- Every existing test in `docs/scripts/tests/test_convert_to_docbook.py` must still pass after
  every task. If one breaks unexpectedly, that's the systematic-debugging trigger below, not
  something to patch by loosening the assertion.

## Process Discipline

This governs every task below, not just the risky ones.

- **Verify.** Each task's own RED→GREEN cycle is not sufficient on its own. After Tasks 1, 3
  (both XSLT fixes), 6 (splitter complete), 8 (refactor), and 9 (migration script), run the
  **full** test suite: `python3 -m unittest discover -s docs/scripts/tests -v`. A task's own new
  tests passing doesn't guarantee it didn't silently break something else in the file.
- **Systematic debugging.** If any test fails that is *not* the RED step you just wrote — an
  existing test breaks, or a verification step fails against real corpus data during Task 11 or
  14 — stop. Invoke `superpowers:systematic-debugging` before touching code again. Root-cause
  it; don't patch the symptom (don't loosen an assertion, don't wrap a failure in a broad
  `try/except` to make it "pass"). If you're not converging on a root cause within a few minutes,
  revert to the last good commit rather than debugging against a moving target.
- **Code review.** After Task 9, before Task 11 — dispatch a code-reviewer agent (or run
  `/code-review`) over the full diff from Tasks 1-9. This is the last point where the new code
  is complete but hasn't touched real corpus data yet, the cheapest place to catch a design flaw.
  Fix anything it flags, re-run the full test suite, before proceeding to Task 11.
- **Simplify.** Immediately after code review passes, still before Task 11 — run a
  `/simplify`-style pass (parallel review agents: reuse, simplification, efficiency, altitude)
  over the same diff, the same way the original conversion tool was simplified in commit
  `4f6a9f7`. Apply what it flags, re-run the full test suite.
- **Ask the user.** (1) After Task 11's 3-document pilot (2 corpus docs + the paper), before
  Task 14's full batch — the natural "small scale proved out, ready to touch the other 114
  documents" checkpoint, matching the matter-by-matter confirmation pattern already used for
  this corpus's original Markdown migration. (2) If systematic debugging on a migration failure
  doesn't converge on a clear root cause — stop and surface the specific document and error
  rather than skipping it silently or forcing an unexplained fix. (3) Do **not** ask before Tasks
  1-10 — those are reversible, test-covered, and touch no committed corpus data yet.

## File Structure

- **Create** `docs/common/shared-metadata.xml` — the deduplicated corpus-wide metadata fragment.
- **Modify** `docs/scripts/convert_to_docbook.py` — `write_metadata()` rewritten;
  `split_into_fragments()` added; `render_docbook_plain()` extracted;
  `content_preservation_diff()` updated to use it; `convert()` wired to call the splitter.
- **Modify** `docs/scripts/tests/test_convert_to_docbook.py` — updated/new tests; `tearDown` in
  `TestConvertEndToEnd` fixed to handle the fragment subdirectories `convert()` now creates.
- **Create** `docs/scripts/tests/fixtures/nested_sections.md` — new fixture for the
  one-level-only splitting test.
- **Create** `docs/scripts/atomize_existing_document.py` — the one-off migration script, plus
  its own test file `docs/scripts/tests/test_atomize_existing_document.py`.
- **Modify** `docs/xsl/html5.xsl`, `docs/xsl/latex.xsl` — descendant-axis XPath relaxation.
- **Modify** `.github/workflows/build-corpus.yml` — root-element-based file discrimination.
- **Modify** `docs/papers/ai_and_ip/llm-database-theory/src/00-metadata.xml` — pulls the 3
  shared fields.
- **Modify** (data, not code) the 117 corpus documents + 2 paper articles — migrated in Task 14.

---

### Task 1: Shared metadata file + `write_metadata()` rewrite

**Files:**
- Create: `docs/common/shared-metadata.xml`
- Modify: `docs/scripts/convert_to_docbook.py:117-142` (`write_metadata`)
- Test: `docs/scripts/tests/test_convert_to_docbook.py` (`TestWriteMetadata` class, imports)

**Interfaces:**
- Produces: `write_metadata(meta_path, title)` — same signature as before, now writes the
  minimal `<dc:title>` + shared `xi:include` form. `docs/common/shared-metadata.xml` — new
  corpus-wide file, root element `<shared xmlns="http://docbook.org/ns/docbook" ...>`.

- [ ] **Step 1: Create the shared metadata file**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<shared xmlns="http://docbook.org/ns/docbook" xmlns:dc="http://purl.org/dc/terms/">
  <dc:creator>Ian D.L.N. McLean</dc:creator>
  <dc:publisher>metavacua/legal-theory (GitHub)</dc:publisher>
  <dc:type>Article</dc:type>
  <dc:language>en</dc:language>
  <dc:rights>CC BY-SA 4.0</dc:rights>
  <authorgroup>
    <author>
      <personname>
        <firstname>Ian</firstname>
        <othername role="middle">D.L.N.</othername>
        <surname>McLean</surname>
      </personname>
      <email>metavacua@gmail.com</email>
    </author>
  </authorgroup>
  <legalnotice>
    <para>Copyright &#169; 2026 Ian D.L.N. McLean. Licensed under Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0). This document publishes general legal analysis and does not constitute legal advice.</para>
  </legalnotice>
</shared>
```

Save to `docs/common/shared-metadata.xml`. Verify it's well-formed:

Run: `xmllint --noout docs/common/shared-metadata.xml`
Expected: no output, exit code 0.

- [ ] **Step 2: Write the failing test**

Add `import subprocess` to the top of `docs/scripts/tests/test_convert_to_docbook.py` (it isn't
imported there yet). Replace the existing
`test_write_metadata_produces_well_formed_xincludable_info` in `TestWriteMetadata`:

```python
    def test_write_metadata_produces_well_formed_xincludable_info(self):
        from convert_to_docbook import write_metadata
        fixtures = Path(__file__).resolve().parent / "fixtures"
        meta_path = fixtures / "tmp.meta.xml"
        write_metadata(meta_path, "A Flat Document")
        tree = ET.parse(meta_path)
        root = tree.getroot()
        self.assertEqual(root.tag, f"{DB_NS}info")
        dc_ns = "{http://purl.org/dc/terms/}"
        title_el = root.find(f"{dc_ns}title")
        self.assertEqual(title_el.text, "A Flat Document")

        xi_ns = "{http://www.w3.org/2001/XInclude}"
        includes = root.findall(f"{xi_ns}include")
        self.assertEqual(len(includes), 1)

        resolved = subprocess.run(
            ["xmllint", "--xinclude", str(meta_path)],
            capture_output=True, text=True, check=True,
        ).stdout
        resolved_root = ET.fromstring(resolved)
        rights_el = resolved_root.find(f".//{dc_ns}rights")
        self.assertIsNotNone(rights_el)
        self.assertEqual(rights_el.text, "CC BY-SA 4.0")
        publisher_el = resolved_root.find(f".//{dc_ns}publisher")
        self.assertEqual(publisher_el.text, "metavacua/legal-theory (GitHub)")

        meta_path.unlink()
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd docs/scripts/tests && python3 -m unittest test_convert_to_docbook.TestWriteMetadata.test_write_metadata_produces_well_formed_xincludable_info -v`
Expected: FAIL — `AssertionError: 1 != 0` (no `xi:include` in the old monolithic output) or
similar, since the current `write_metadata()` still writes the full inline boilerplate with no
`xi:include` at all.

- [ ] **Step 4: Implement the new `write_metadata()`**

Replace `docs/scripts/convert_to_docbook.py:117-142`:

```python
def write_metadata(meta_path, title):
    meta_path = Path(meta_path)
    docs_dir = (REPO_ROOT / "docs").resolve()
    meta_dir = meta_path.resolve().parent
    depth = len(meta_dir.relative_to(docs_dir).parts)
    shared_href = "../" * depth + "common/shared-metadata.xml"
    escaped_title = xml_escape(title)
    content = f"""<?xml version="1.0" encoding="UTF-8"?>
<info xmlns="{DB_NS}" xmlns:dc="http://purl.org/dc/terms/" xmlns:xi="{XI_NS}">
  <dc:title>{escaped_title}</dc:title>
  <xi:include href="{shared_href}" />
</info>
"""
    meta_path.write_text(content, encoding="utf-8")
```

`REPO_ROOT` is defined later in the module (near line 145) — this works because Python resolves
module-level names at call time, not at function-definition time, and by the time
`write_metadata()` is ever *called* the whole module has finished executing top to bottom.

- [ ] **Step 5: Run test to verify it passes**

Run: `cd docs/scripts/tests && python3 -m unittest test_convert_to_docbook.TestWriteMetadata -v`
Expected: all `TestWriteMetadata` tests PASS, including the unchanged
`test_write_metadata_escapes_special_characters_in_title`.

- [ ] **Step 6: Run the full test suite**

Run: `python3 -m unittest discover -s docs/scripts/tests -v`
Expected: some pre-existing tests that assert on `write_metadata()`'s old shape may now fail —
check `TestValidateAndBuild` and `TestContentPreservationDiff`, which both call
`write_metadata()` via their `_convert_fixture` helpers. Those helpers only check the produced
`.xml` (not `.meta.xml`) for validity, so they should be unaffected, but confirm rather than
assume. If anything unrelated to this task's change fails, invoke systematic-debugging per the
Process Discipline section before proceeding.

- [ ] **Step 7: Commit**

```bash
git add docs/common/shared-metadata.xml docs/scripts/convert_to_docbook.py docs/scripts/tests/test_convert_to_docbook.py
git commit -m "feat: dedupe per-document metadata into shared docs/common/shared-metadata.xml"
```

---

### Task 2: `html5.xsl` descendant-axis fix

**Files:**
- Modify: `docs/xsl/html5.xsl` (4 `<head>` meta-tag attribute value templates + 2 body
  `xsl:value-of` selects — 6 spots total, all direct-child lookups into `db:info`)

**Interfaces:**
- Consumes: `docs/common/shared-metadata.xml` from Task 1 (for the manual verification fixture).
- Produces: no interface change — same template match patterns, relaxed XPath only.

**Important — this is 6 fixes, not 2.** Investigating during plan-writing surfaced a second,
easy-to-miss instance of the same problem: `html5.xsl`'s `<head>` block has 4 more direct-child
lookups into `db:info` (`DC.creator`, `DC.type`, `DC.language`, `DC.rights` meta tags) that use
the exact same broken pattern as the body's authorgroup/legalnotice lookups — since for corpus
documents (not just the paper), `dc:creator`/`dc:type`/`dc:language`/`dc:rights` *all* move into
the shared file per Task 1, all 4 of these meta tags would silently render `content=""` for
every migrated document if left unfixed. Confirmed empirically before writing this task: built
a throwaway fixture with the real `docs/common/shared-metadata.xml` shape and ran it through the
*unfixed* stylesheet — `DC.creator`, `DC.type`, `DC.language`, `DC.rights` all rendered empty;
`DC.subject`/`DC.description`/`DC.date` stayed empty too, but that's pre-existing and correct
(corpus documents never populated those fields to begin with, wrapped metadata or not).

- [ ] **Step 1: Build a throwaway fixture exercising the wrapped shape**

```bash
mkdir -p /tmp/xsl-fix-test
cat > /tmp/xsl-fix-test/test.meta.xml <<'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<info xmlns="http://docbook.org/ns/docbook" xmlns:dc="http://purl.org/dc/terms/" xmlns:xi="http://www.w3.org/2001/XInclude">
  <dc:title>XSL Fix Test</dc:title>
  <xi:include href="/home/metavacua/legal-theory/docs/common/shared-metadata.xml"/>
</info>
EOF
cat > /tmp/xsl-fix-test/test.xml <<'EOF'
<?xml version='1.0' encoding='utf-8'?>
<article xmlns="http://docbook.org/ns/docbook" xmlns:xi="http://www.w3.org/2001/XInclude" version="5.2" xml:id="test" xml:lang="en">
  <xi:include href="test.meta.xml" />
  <title>XSL Fix Test</title>
  <para>Body content.</para>
</article>
EOF
```

Also add the real shared-metadata file content so the fixture's `xi:include` actually resolves
(not just falls back on a missing-file error):

```bash
cp /home/metavacua/legal-theory/docs/common/shared-metadata.xml /tmp/xsl-fix-test/shared-metadata.xml
sed -i 's#href="[^"]*shared-metadata.xml"#href="/tmp/xsl-fix-test/shared-metadata.xml"#' /tmp/xsl-fix-test/test.meta.xml
```

- [ ] **Step 2: Confirm the bug (RED)**

```bash
xsltproc --xinclude /home/metavacua/legal-theory/docs/xsl/html5.xsl /tmp/xsl-fix-test/test.xml | grep -i "DC\.\|byline\|footer"
```
Expected: `<meta name="DC.creator" content="">`, `<meta name="DC.type" content="">`,
`<meta name="DC.language" content="">`, `<meta name="DC.rights" content="">` (all 4 empty), plus
`<p class="byline">\n        By    — </p>` (empty author name) and `<footer><p></p></footer>`
(empty legal notice) — all 6 fail to resolve because they're nested one level deeper inside the
`<shared>` wrapper than their current direct-child XPath expects.

- [ ] **Step 3: Apply the fix — 6 spots total**

In `docs/xsl/html5.xsl`'s `<head>` block, change these 4 attribute value templates:

```xml
        <meta name="DC.creator"     content="{db:info/dc:creator}"/>
        ...
        <meta name="DC.type"        content="{db:info/dc:type}"/>
        <meta name="DC.language"    content="{db:info/dc:language}"/>
        <meta name="DC.rights"      content="{db:info/dc:rights}"/>
```
to:
```xml
        <meta name="DC.creator"     content="{db:info//dc:creator}"/>
        ...
        <meta name="DC.type"        content="{db:info//dc:type}"/>
        <meta name="DC.language"    content="{db:info//dc:language}"/>
        <meta name="DC.rights"      content="{db:info//dc:rights}"/>
```

Leave `DC.title`, `DC.subject`, `DC.description`, `DC.date` untouched — `title` always stays a
direct child of `info` (never shared), and `subject`/`description`/`date` are never populated
for corpus documents in either the old or new metadata shape, so there's nothing to fix there.

Then, in the `db:info` template, change:

```xml
            <xsl:value-of select="db:info/db:legalnotice/db:para"/>
```
to:
```xml
            <xsl:value-of select="db:info//db:legalnotice/db:para"/>
```

and change all three of:
```xml
        By <xsl:value-of select="db:authorgroup/db:author/db:personname/db:firstname"/>
        <xsl:text> </xsl:text>
        <xsl:value-of select="db:authorgroup/db:author/db:personname/db:othername"/>
        <xsl:text> </xsl:text>
        <xsl:value-of select="db:authorgroup/db:author/db:personname/db:surname"/>
```
to:
```xml
        By <xsl:value-of select=".//db:authorgroup/db:author/db:personname/db:firstname"/>
        <xsl:text> </xsl:text>
        <xsl:value-of select=".//db:authorgroup/db:author/db:personname/db:othername"/>
        <xsl:text> </xsl:text>
        <xsl:value-of select=".//db:authorgroup/db:author/db:personname/db:surname"/>
```

(These 3 lines are inside the `db:info` template, so `.` is already the `db:info` context node —
`.//db:authorgroup` finds it regardless of nesting depth. The `<head>` block's 4 fixes are in the
root `/db:article` template, so they use `db:info//dc:X` — full path from the article root —
rather than `.//`.)

- [ ] **Step 4: Confirm the fix (GREEN) on the wrapped fixture**

```bash
xsltproc --xinclude docs/xsl/html5.xsl /tmp/xsl-fix-test/test.xml | grep -i "DC\.\|byline\|footer"
```
Expected: `DC.creator` → `Ian D.L.N. McLean`, `DC.type` → `Article`, `DC.language` → `en`,
`DC.rights` → `CC BY-SA 4.0`, `<p class="byline">\n        By Ian D.L.N. McLean — </p>`, and
`<footer><p>Copyright © 2026 Ian D.L.N. McLean...</p></footer>`.

- [ ] **Step 5: Confirm backward compatibility against real, unmigrated corpus documents**

The fix must not change any of the 117 documents' output before Task 14 migrates them (they
still use the old, un-wrapped metadata shape).

```bash
for f in docs/cross-cutting/patron-as-client.xml docs/court-record/matters/google-platform-misclassification/findings.xml; do
  xsltproc --xinclude docs/xsl/html5.xsl "$f" > /tmp/rebuilt-$(basename "$f" .xml).html
  diff /tmp/rebuilt-$(basename "$f" .xml).html "${f%.xml}.html" && echo "IDENTICAL: $f"
done
```

Expected: `IDENTICAL:` printed for both, empty diffs — proves `.//` and `//` are strict
supersets of the direct-child lookups they replace, so nothing changes for documents that
haven't been migrated yet.

- [ ] **Step 6: Clean up and commit**

```bash
rm -rf /tmp/xsl-fix-test /tmp/rebuilt-*.html
git add docs/xsl/html5.xsl
git commit -m "fix(xsl): resolve authorgroup/legalnotice through the shared-metadata wrapper"
```

---

### Task 3: `latex.xsl` descendant-axis fix

**Files:**
- Modify: `docs/xsl/latex.xsl:56,58,60`

**Interfaces:**
- Same as Task 2, mirrored for the paper's LaTeX build path.

- [ ] **Step 1: Confirm the bug (RED)**

```bash
xsltproc --xinclude docs/xsl/latex.xsl /tmp/xsl-fix-test/test.xml 2>&1 | grep -i "author\|mclean" || echo "NO AUTHOR FOUND (bug confirmed)"
```

(Recreate `/tmp/xsl-fix-test/` from Task 2 Step 1 if it was already cleaned up.)
Expected: `NO AUTHOR FOUND (bug confirmed)`.

- [ ] **Step 2: Apply the fix**

In `docs/xsl/latex.xsl`, change lines 56, 58, 60 from:
```xml
    <xsl:value-of select="db:info/db:authorgroup/db:author/db:personname/db:firstname"/>
    ...
    <xsl:value-of select="db:info/db:authorgroup/db:author/db:personname/db:othername"/>
    ...
    <xsl:value-of select="db:info/db:authorgroup/db:author/db:personname/db:surname"/>
```
to:
```xml
    <xsl:value-of select="db:info//db:authorgroup/db:author/db:personname/db:firstname"/>
    ...
    <xsl:value-of select="db:info//db:authorgroup/db:author/db:personname/db:othername"/>
    ...
    <xsl:value-of select="db:info//db:authorgroup/db:author/db:personname/db:surname"/>
```

`latex.xsl` has no `legalnotice` lookup at all (its `db:info` template, line 88, is empty —
`<xsl:template match="db:info"/>` — so legal notice text never appears in the LaTeX build
regardless; nothing to fix there). Leave `db:info/dc:date` and `db:info/db:abstract` (lines 63,
71, 74) unchanged — `abstract` is never wrapped (it stays local to each document's own metadata,
never shared), so its direct-child lookup remains correct.

- [ ] **Step 3: Confirm the fix (GREEN)**

```bash
xsltproc --xinclude docs/xsl/latex.xsl /tmp/xsl-fix-test/test.xml 2>&1 | grep -i "mclean"
```
Expected: a line containing "Ian" and "McLean" (the author byline now resolves).

- [ ] **Step 4: Confirm backward compatibility on the paper's real, unmigrated articles**

```bash
for f in docs/papers/ai_and_ip/llm-database-theory/src/01-llm-database-theory.xml docs/papers/ai_and_ip/llm-database-theory/src/02-legal-corpus-connections.xml; do
  xsltproc --xinclude docs/xsl/latex.xsl "$f" > /tmp/rebuilt-$(basename "$f" .xml).tex
  diff /tmp/rebuilt-$(basename "$f" .xml).tex "docs/papers/ai_and_ip/llm-database-theory/generated/$(basename "$f" .xml).tex" && echo "IDENTICAL: $f"
done
```
Expected: `IDENTICAL:` for both.

- [ ] **Step 5: Clean up and commit**

```bash
rm -rf /tmp/xsl-fix-test /tmp/rebuilt-*.tex
git add docs/xsl/latex.xsl
git commit -m "fix(xsl): resolve authorgroup through the shared-metadata wrapper in the LaTeX build"
```

---

### Task 4: `split_into_fragments()` — multi-section case

**Files:**
- Modify: `docs/scripts/convert_to_docbook.py` (new function, placed after `sanitize_xml_ids`)
- Test: `docs/scripts/tests/test_convert_to_docbook.py` (new `TestSplitIntoFragments` class)

**Interfaces:**
- Consumes: `slugify()` (existing), `DB_NS`/`XI_NS` module constants (existing).
- Produces: `split_into_fragments(article, out_dir, stem) -> bool` — mutates `article` in place
  (replacing each direct-child `db:section` with an `xi:include`), writes fragment files to
  `<out_dir>/<stem>/NN-<slug>.xml`. Returns `True` if it split anything, `False` if `article` had
  no direct-child sections (left untouched). Later tasks (7, 9) call this exact signature.

- [ ] **Step 1: Write the failing test**

```python
import tempfile

class TestSplitIntoFragments(unittest.TestCase):
    def setUp(self):
        self.fixtures = Path(__file__).resolve().parent / "fixtures"

    def test_multi_section_splits_each_top_level_section(self):
        from convert_to_docbook import (
            pandoc_to_docbook_fragment, wrap_fragment, split_into_fragments,
        )
        fragment = pandoc_to_docbook_fragment(self.fixtures / "multi_section.md")
        article, _ = wrap_fragment(fragment, "multi", "Multi Section", "multi.meta.xml")

        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            result = split_into_fragments(article, out_dir, "multi")
            self.assertTrue(result)

            frag_dir = out_dir / "multi"
            self.assertTrue((frag_dir / "01-first-topic.xml").exists())
            self.assertTrue((frag_dir / "02-second-topic.xml").exists())

            frag1 = ET.parse(frag_dir / "01-first-topic.xml").getroot()
            self.assertEqual(frag1.tag, f"{DB_NS}section")
            self.assertEqual(frag1.get("{http://www.w3.org/XML/1998/namespace}id"), "first-topic")

            xi_ns = "{http://www.w3.org/2001/XInclude}"
            includes = [c for c in article if c.tag == f"{xi_ns}include"]
            # 3 total: wrap_fragment() already added a metadata xi:include
            # (href="multi.meta.xml") as the article's first child, before
            # split_into_fragments() ever runs. split_into_fragments() must
            # NOT touch that include — it only replaces db:section children.
            # So the 2 new fragment includes land alongside it, not instead
            # of it.
            self.assertEqual(len(includes), 3)
            self.assertEqual(includes[0].get("href"), "multi.meta.xml")
            self.assertEqual(includes[1].get("href"), "multi/01-first-topic.xml")
            self.assertEqual(includes[2].get("href"), "multi/02-second-topic.xml")

            sections_left = [c for c in article if c.tag == f"{DB_NS}section"]
            self.assertEqual(sections_left, [])

    def test_split_shell_resolves_to_original_content(self):
        # The shell + fragments, resolved via xmllint --xinclude, must
        # reproduce the exact original tree.
        from convert_to_docbook import (
            pandoc_to_docbook_fragment, wrap_fragment, write_metadata,
            split_into_fragments,
        )
        fragment = pandoc_to_docbook_fragment(self.fixtures / "multi_section.md")
        article, _ = wrap_fragment(fragment, "multi", "Multi Section", "multi.meta.xml")

        # A subdirectory of the fixtures tree (itself under docs/), not a
        # system temp dir — write_metadata() computes the shared-metadata
        # href relative to docs/ (Task 1), so out_dir must stay under docs/
        # for that calculation to resolve correctly. Do NOT change
        # write_metadata() to accommodate an out-of-docs path here — that
        # function's contract belongs to Task 1, already reviewed.
        out_dir = Path(tempfile.mkdtemp(dir=self.fixtures))
        self.addCleanup(shutil.rmtree, out_dir)

        split_into_fragments(article, out_dir, "multi")
        write_metadata(out_dir / "multi.meta.xml", "Multi Section")
        xml_path = out_dir / "multi.xml"
        tree = ET.ElementTree(article)
        ET.indent(tree, space="  ")
        tree.write(xml_path, encoding="unicode", xml_declaration=True)

        resolved = subprocess.run(
            ["xmllint", "--xinclude", str(xml_path)],
            capture_output=True, text=True, check=True,
        ).stdout
        self.assertIn("First Topic", resolved)
        self.assertIn("Content for the first topic.", resolved)
        self.assertIn("Second Topic", resolved)
        self.assertIn("Content for the second topic.", resolved)
```

(This test file needs `import shutil` added at the top alongside the existing `import tempfile`.)

- [ ] **Step 2: Run test to verify it fails**

Run: `cd docs/scripts/tests && python3 -m unittest test_convert_to_docbook.TestSplitIntoFragments -v`
Expected: FAIL — `ImportError: cannot import name 'split_into_fragments'`.

- [ ] **Step 3: Implement `split_into_fragments()`**

Add to `docs/scripts/convert_to_docbook.py`, immediately after `sanitize_xml_ids()`:

```python
def split_into_fragments(article, out_dir, stem):
    sections = [c for c in article if c.tag == f"{{{DB_NS}}}section"]
    if not sections:
        return False

    out_dir = Path(out_dir)
    frag_dir = out_dir / stem
    frag_dir.mkdir(parents=True, exist_ok=True)

    used_slugs = {}
    for i, section in enumerate(sections, start=1):
        title_el = section.find(f"{{{DB_NS}}}title")
        section_title = title_el.text if title_el is not None else ""
        base_slug = slugify(section_title)
        count = used_slugs.get(base_slug, 0)
        slug = base_slug if count == 0 else f"{base_slug}-{count}"
        used_slugs[base_slug] = count + 1

        frag_name = f"{i:02d}-{slug}.xml"
        frag_path = frag_dir / frag_name

        frag_tree = ET.ElementTree(section)
        ET.indent(frag_tree, space="  ")
        frag_tree.write(frag_path, encoding="unicode", xml_declaration=True)

        idx = list(article).index(section)
        xi_include = ET.Element(f"{{{XI_NS}}}include")
        xi_include.set("href", f"{stem}/{frag_name}")
        article.remove(section)
        article.insert(idx, xi_include)

    return True
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd docs/scripts/tests && python3 -m unittest test_convert_to_docbook.TestSplitIntoFragments -v`
Expected: both tests PASS.

- [ ] **Step 5: Commit**

```bash
git add docs/scripts/convert_to_docbook.py docs/scripts/tests/test_convert_to_docbook.py
git commit -m "feat: add split_into_fragments() for multi-section documents"
```

---

### Task 5: `split_into_fragments()` — flat/no-sections passthrough

**Files:**
- Test: `docs/scripts/tests/test_convert_to_docbook.py` (`TestSplitIntoFragments`)

**Interfaces:**
- Consumes: `split_into_fragments()` from Task 4 — no implementation change expected, this task
  proves the existing `if not sections: return False` guard is correct.

- [ ] **Step 1: Write the test**

```python
    def test_flat_document_is_not_split(self):
        from convert_to_docbook import (
            pandoc_to_docbook_fragment, wrap_fragment, split_into_fragments,
        )
        fragment = pandoc_to_docbook_fragment(self.fixtures / "flat.md")
        article, _ = wrap_fragment(fragment, "flat", "A Flat Document", "flat.meta.xml")
        children_before = list(article)

        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            result = split_into_fragments(article, out_dir, "flat")
            self.assertFalse(result)
            self.assertFalse((out_dir / "flat").exists())
            self.assertEqual(list(article), children_before)
```

- [ ] **Step 2: Run test to verify it passes immediately**

Run: `cd docs/scripts/tests && python3 -m unittest test_convert_to_docbook.TestSplitIntoFragments.test_flat_document_is_not_split -v`
Expected: PASS — this is a regression test for behavior Task 4's implementation already
provides (the `if not sections` guard). It's still written and run explicitly so a future change
to the guard can't silently break the flat-document case without a visible test failure.

- [ ] **Step 3: Commit**

```bash
git add docs/scripts/tests/test_convert_to_docbook.py
git commit -m "test: cover flat/no-sections passthrough for split_into_fragments()"
```

---

### Task 6: `split_into_fragments()` — nested-section case (one-level-only rule)

**Files:**
- Create: `docs/scripts/tests/fixtures/nested_sections.md`
- Test: `docs/scripts/tests/test_convert_to_docbook.py` (`TestSplitIntoFragments`)

**Interfaces:**
- Consumes: `split_into_fragments()` from Task 4.

- [ ] **Step 1: Create the fixture**

```markdown
## Top Section

Intro paragraph for the top section.

### Nested Subsection

Content inside the nested subsection.

## Second Top Section

Content for the second top-level section.
```

Save to `docs/scripts/tests/fixtures/nested_sections.md`.

- [ ] **Step 2: Write the failing test**

```python
    def test_nested_section_stays_inline_one_level_only(self):
        from convert_to_docbook import (
            pandoc_to_docbook_fragment, wrap_fragment, split_into_fragments,
        )
        fragment = pandoc_to_docbook_fragment(self.fixtures / "nested_sections.md")
        article, unwrapped = wrap_fragment(
            fragment, "nested", "Nested Test", "nested.meta.xml"
        )
        self.assertFalse(unwrapped)

        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            split_into_fragments(article, out_dir, "nested")

            frag_dir = out_dir / "nested"
            self.assertTrue((frag_dir / "01-top-section.xml").exists())
            self.assertTrue((frag_dir / "02-second-top-section.xml").exists())
            # Only 2 fragments — the nested subsection did NOT get its own file.
            self.assertEqual(len(list(frag_dir.iterdir())), 2)

            frag1_text = (frag_dir / "01-top-section.xml").read_text(encoding="utf-8")
            self.assertIn("Nested Subsection", frag1_text)
            self.assertIn("Content inside the nested subsection.", frag1_text)

            frag1_root = ET.parse(frag_dir / "01-top-section.xml").getroot()
            nested = frag1_root.findall(f"{DB_NS}section")
            self.assertEqual(len(nested), 1)
            self.assertEqual(
                nested[0].get("{http://www.w3.org/XML/1998/namespace}id"),
                "nested-subsection",
            )
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd docs/scripts/tests && python3 -m unittest test_convert_to_docbook.TestSplitIntoFragments.test_nested_section_stays_inline_one_level_only -v`
Expected: FAIL — `FileNotFoundError` (fixture doesn't exist yet if Step 1 wasn't done first) or,
once the fixture exists, the test should actually already pass against the Task 4
implementation, since `split_into_fragments()` only ever iterates `[c for c in article if
c.tag == ...]` — a single-level, non-recursive list comprehension over `article`'s direct
children. This test's job is proving that behavior explicitly, not discovering new
implementation work.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd docs/scripts/tests && python3 -m unittest test_convert_to_docbook.TestSplitIntoFragments -v`
Expected: all `TestSplitIntoFragments` tests PASS (no implementation change needed — see Step
3's note).

- [ ] **Step 5: Run the full test suite**

Run: `python3 -m unittest discover -s docs/scripts/tests -v`
Expected: all PASS.

- [ ] **Step 6: Commit**

```bash
git add docs/scripts/tests/fixtures/nested_sections.md docs/scripts/tests/test_convert_to_docbook.py
git commit -m "test: prove split_into_fragments() splits one level only, not recursively"
```

---

### Task 7: Wire `split_into_fragments()` into `convert()`

**Files:**
- Modify: `docs/scripts/convert_to_docbook.py:281-323` (`convert`)
- Modify: `docs/scripts/tests/test_convert_to_docbook.py` (`TestConvertEndToEnd.tearDown`, new test)

**Interfaces:**
- Consumes: `split_into_fragments()` from Task 4.
- Produces: `convert()` now also creates a `<stem>/` fragments subdirectory in `out_dir` for any
  document with top-level sections. `ConversionResult` is unchanged.

- [ ] **Step 1: Fix `tearDown` for the new subdirectory (prerequisite, not yet exercised)**

The existing `TestConvertEndToEnd.tearDown` only handles files directly in `out_dir`:

```python
    def tearDown(self):
        for f in self.out_dir.iterdir():
            f.unlink()
        self.out_dir.rmdir()
```

Once `convert()` creates a fragments subdirectory, `f.unlink()` raises `IsADirectoryError`.
Replace with:

```python
    def tearDown(self):
        import shutil
        for f in self.out_dir.iterdir():
            if f.is_dir():
                shutil.rmtree(f)
            else:
                f.unlink()
        self.out_dir.rmdir()
```

- [ ] **Step 2: Write the failing test**

```python
    def test_convert_multi_section_document_creates_fragments(self):
        from convert_to_docbook import convert
        result = convert(self.fixtures / "multi_section.md", self.out_dir)
        self.assertEqual(result.errors, [])
        self.assertEqual(result.content_diff, [])
        frag_dir = self.out_dir / "multi_section"
        self.assertTrue(frag_dir.is_dir())
        self.assertTrue((frag_dir / "01-first-topic.xml").exists())
        self.assertTrue((frag_dir / "02-second-topic.xml").exists())
        # The shell itself no longer inlines section content directly.
        shell_text = result.xml_path.read_text(encoding="utf-8")
        self.assertNotIn("Content for the first topic.", shell_text)
        self.assertIn("xi:include", shell_text)
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd docs/scripts/tests && python3 -m unittest test_convert_to_docbook.TestConvertEndToEnd.test_convert_multi_section_document_creates_fragments -v`
Expected: FAIL — no fragments directory exists yet, since `convert()` doesn't call
`split_into_fragments()`.

- [ ] **Step 4: Wire the call into `convert()`**

In `docs/scripts/convert_to_docbook.py`, in the `convert()` function, add the call right after
`write_metadata()` and before serializing `article` to `xml_path`:

```python
    write_metadata(out_dir / meta_name, title)
    split_into_fragments(article, out_dir, md_path.stem)

    tree = ET.ElementTree(article)
```

(This replaces the existing `write_metadata(...)` line followed directly by `tree = ...` — just
insert the one new line between them.)

- [ ] **Step 5: Run test to verify it passes**

Run: `cd docs/scripts/tests && python3 -m unittest test_convert_to_docbook.TestConvertEndToEnd -v`
Expected: all `TestConvertEndToEnd` tests PASS, including the pre-existing
`test_convert_flat_document_end_to_end` (unaffected — `flat.md` has no top-level sections) and
`test_convert_multi_section_document_end_to_end` (still passes — it didn't assert on internal
structure, only `errors == []` and `content_diff == []`).

- [ ] **Step 6: Run the full test suite**

Run: `python3 -m unittest discover -s docs/scripts/tests -v`
Expected: all PASS.

- [ ] **Step 7: Commit**

```bash
git add docs/scripts/convert_to_docbook.py docs/scripts/tests/test_convert_to_docbook.py
git commit -m "feat: wire split_into_fragments() into convert() for fresh conversions"
```

---

### Task 8: Extract `render_docbook_plain()`, refactor `content_preservation_diff()`

**Files:**
- Modify: `docs/scripts/convert_to_docbook.py:229-266` (`content_preservation_diff`)
- Test: `docs/scripts/tests/test_convert_to_docbook.py`

**Interfaces:**
- Produces: `render_docbook_plain(xml_path) -> str` — resolves XIncludes via `xmllint
  --xinclude`, then converts to plain text via `pandoc -f docbook -t plain`. Used by
  `content_preservation_diff()` (this task) and `atomize_existing_document.py` (Task 9).

Note: this task is a pure refactor, not new capability — `content_preservation_diff()` already
resolves XIncludes correctly today (it already runs `xmllint --xinclude` before handing content
to pandoc); this task only extracts that existing logic into a named, reusable function so the
migration script in Task 9 doesn't duplicate it.

- [ ] **Step 1: Write the failing test**

```python
class TestRenderDocbookPlain(unittest.TestCase):
    def setUp(self):
        self.fixtures = Path(__file__).resolve().parent / "fixtures"

    def _convert_fixture(self, name, xml_id, title):
        from convert_to_docbook import (
            pandoc_to_docbook_fragment, wrap_fragment, write_metadata,
        )
        fragment = pandoc_to_docbook_fragment(self.fixtures / name)
        article, _ = wrap_fragment(fragment, xml_id, title, f"{xml_id}.meta.xml")
        xml_path = self.fixtures / f"{xml_id}.xml"
        meta_path = self.fixtures / f"{xml_id}.meta.xml"
        write_metadata(meta_path, title)
        tree = ET.ElementTree(article)
        ET.indent(tree, space="  ")
        tree.write(xml_path, encoding="unicode", xml_declaration=True)
        self.addCleanup(xml_path.unlink)
        self.addCleanup(meta_path.unlink)
        return xml_path

    def test_renders_resolved_content_as_plain_text(self):
        from convert_to_docbook import render_docbook_plain
        xml_path = self._convert_fixture("flat.md", "flat", "A Flat Document")
        text = render_docbook_plain(xml_path)
        self.assertIn("This document has one heading", text)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd docs/scripts/tests && python3 -m unittest test_convert_to_docbook.TestRenderDocbookPlain -v`
Expected: FAIL — `ImportError: cannot import name 'render_docbook_plain'`.

- [ ] **Step 3: Extract the function and refactor the caller**

In `docs/scripts/convert_to_docbook.py`, replace the body of `content_preservation_diff()`
(lines 229-266) with:

```python
def render_docbook_plain(xml_path):
    resolved = subprocess.run(
        ["xmllint", "--xinclude", str(xml_path)],
        capture_output=True, text=True, check=True,
    ).stdout
    return subprocess.run(
        ["pandoc", "-f", "docbook", "-t", "plain", "-"],
        input=resolved, capture_output=True, text=True, check=True,
    ).stdout


def content_preservation_diff(md_path, xml_path, title, unwrapped):
    # Normalize the same way pandoc_to_docbook_fragment() does, rather
    # than handing pandoc the raw file path — otherwise this "original"
    # side would still contain the accidental hard-break whitespace
    # _strip_trailing_whitespace() already removed before conversion,
    # comparing against content that was never actually converted.
    original = subprocess.run(
        ["pandoc", "-f", "gfm", "-t", "plain"],
        input=_strip_trailing_whitespace(md_path),
        capture_output=True, text=True, check=True,
    ).stdout

    roundtrip = render_docbook_plain(xml_path)

    if unwrapped:
        # The wrapping <section>'s title was discarded when its
        # children were promoted to the article; pandoc's docbook
        # reader never renders <article><title> as body text, so add
        # the title back for a fair comparison against the original.
        roundtrip = f"{title}\n\n{roundtrip}"

    # Word-level comparison, not line- or paragraph-level: verified on
    # real corpus documents that pandoc's plain-text writer both
    # rewraps long lines at a different column width AND regroups
    # adjacent list items into a different number of blank-line-
    # separated blocks after a DocBook round-trip (list-item nesting
    # context doesn't survive the round-trip) — same words throughout,
    # but neither line boundaries nor paragraph/block boundaries are
    # stable enough to diff on. Word sequences are unaffected by either.
    return _word_level_diff(original.split(), roundtrip.split())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd docs/scripts/tests && python3 -m unittest test_convert_to_docbook.TestRenderDocbookPlain -v`
Expected: PASS.

- [ ] **Step 5: Run the full test suite**

Run: `python3 -m unittest discover -s docs/scripts/tests -v`
Expected: all PASS, including every existing `TestContentPreservationDiff` test — this was a
pure extraction with no behavior change.

- [ ] **Step 6: Commit**

```bash
git add docs/scripts/convert_to_docbook.py docs/scripts/tests/test_convert_to_docbook.py
git commit -m "refactor: extract render_docbook_plain() shared by diff check and migration script"
```

---

### Task 9: Migration script `atomize_existing_document.py`

**Files:**
- Create: `docs/scripts/atomize_existing_document.py`
- Create: `docs/scripts/tests/test_atomize_existing_document.py`

**Interfaces:**
- Consumes: `split_into_fragments()`, `write_metadata()`, `validate()`, `build_html()`,
  `render_docbook_plain()`, `_word_level_diff()` (all from `convert_to_docbook.py`).
- Produces: `atomize_existing_document(xml_path, meta_path) -> (diff, errors)` — `errors` is a
  non-empty list if the migrated shell fails schema validation (file is rolled back to its
  original content, fragments cleaned up). `diff` is non-empty word-level diff lines if the
  resolved content changed unexpectedly (also rolled back). On success, both are empty lists and
  the files on disk are the new shell + fragments + minimal meta.xml, with HTML already rebuilt.

- [ ] **Step 1: Copy a real, small corpus document as the test fixture**

```bash
mkdir -p docs/scripts/tests/fixtures/atomize_pilot
cp docs/cross-cutting/patron-as-client.xml docs/scripts/tests/fixtures/atomize_pilot/
cp docs/cross-cutting/patron-as-client.meta.xml docs/scripts/tests/fixtures/atomize_pilot/
```

This is a real 6-top-level-section document (verified: `patron-as-client`, 6 direct-child
`db:section` elements, no nesting) — representative real-shape input, not synthetic.

- [ ] **Step 2: Write the failing test**

```python
import shutil
import subprocess
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

DB_NS = "{http://docbook.org/ns/docbook}"


class TestAtomizeExistingDocument(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = Path(__file__).resolve().parent / "fixtures" / "atomize_tmp"
        self.tmp_dir.mkdir(exist_ok=True)
        pilot = Path(__file__).resolve().parent / "fixtures" / "atomize_pilot"
        self.xml_path = self.tmp_dir / "patron-as-client.xml"
        self.meta_path = self.tmp_dir / "patron-as-client.meta.xml"
        shutil.copy(pilot / "patron-as-client.xml", self.xml_path)
        shutil.copy(pilot / "patron-as-client.meta.xml", self.meta_path)

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_migrates_real_document_cleanly(self):
        from atomize_existing_document import atomize_existing_document
        diff, errors = atomize_existing_document(self.xml_path, self.meta_path)
        self.assertEqual(errors, [])
        self.assertEqual(diff, [])

        frag_dir = self.tmp_dir / "patron-as-client"
        self.assertTrue(frag_dir.is_dir())
        self.assertEqual(len(list(frag_dir.iterdir())), 6)

        shell_text = self.xml_path.read_text(encoding="utf-8")
        self.assertIn("xi:include", shell_text)
        self.assertNotIn("Introduction: The Blurring Line", shell_text)

        meta_text = self.meta_path.read_text(encoding="utf-8")
        self.assertIn("common/shared-metadata.xml", meta_text)
        self.assertIn(
            "The Patron as Client: Analyzing Crowdfunded Commissions Under California Labor Law",
            meta_text,
        )

    def test_rolls_back_on_validation_failure(self):
        # Simulate a corrupt shell by making the schema fail: strip the
        # xml:id off a section, which docbook-corpus.rnc's finding-section
        # pattern doesn't apply here, so instead corrupt well-formedness
        # directly to force validate() to fail deterministically.
        original_text = self.xml_path.read_text(encoding="utf-8")
        original_meta_text = self.meta_path.read_text(encoding="utf-8")

        from atomize_existing_document import atomize_existing_document
        import atomize_existing_document as mod

        # Monkeypatch validate() to always report an error, to test the
        # rollback path deterministically without depending on a specific
        # corruption technique.
        original_validate = mod.validate
        mod.validate = lambda xml_path: ["forced failure for rollback test"]
        try:
            diff, errors = atomize_existing_document(self.xml_path, self.meta_path)
        finally:
            mod.validate = original_validate

        self.assertEqual(errors, ["forced failure for rollback test"])
        self.assertEqual(self.xml_path.read_text(encoding="utf-8"), original_text)
        self.assertEqual(self.meta_path.read_text(encoding="utf-8"), original_meta_text)
        self.assertFalse((self.tmp_dir / "patron-as-client").exists())


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd docs/scripts/tests && python3 -m unittest test_atomize_existing_document -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'atomize_existing_document'`.

- [ ] **Step 4: Implement the migration script**

Create `docs/scripts/atomize_existing_document.py`:

```python
"""One-off migration: convert an already-converted monolithic DocBook
document to the shell + per-top-level-section-fragment shape in place.

Unlike convert_to_docbook.py's convert(), this operates on an existing
.xml/.meta.xml pair with no Markdown source required — most already-
migrated corpus documents have had their source .md deleted, so the
title must come from the existing .meta.xml, not from a heading.
"""

import shutil
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from convert_to_docbook import (
    build_html,
    render_docbook_plain,
    split_into_fragments,
    validate,
    write_metadata,
    _word_level_diff,
)

DC_NS = "{http://purl.org/dc/terms/}"


def _cleanup_fragments(xml_path):
    frag_dir = xml_path.parent / xml_path.stem
    if frag_dir.is_dir():
        for f in frag_dir.iterdir():
            f.unlink()
        frag_dir.rmdir()


def atomize_existing_document(xml_path, meta_path):
    xml_path = Path(xml_path)
    meta_path = Path(meta_path)

    original_xml_text = xml_path.read_text(encoding="utf-8")
    original_meta_text = meta_path.read_text(encoding="utf-8")
    before_plain = render_docbook_plain(xml_path)

    meta_root = ET.parse(meta_path).getroot()
    title = meta_root.find(f"{DC_NS}title").text

    tree = ET.parse(xml_path)
    article = tree.getroot()
    split_into_fragments(article, xml_path.parent, xml_path.stem)

    new_tree = ET.ElementTree(article)
    ET.indent(new_tree, space="  ")
    new_tree.write(xml_path, encoding="unicode", xml_declaration=True)
    write_metadata(meta_path, title)

    errors = validate(xml_path)
    if errors:
        xml_path.write_text(original_xml_text, encoding="utf-8")
        meta_path.write_text(original_meta_text, encoding="utf-8")
        _cleanup_fragments(xml_path)
        return [], errors

    after_plain = render_docbook_plain(xml_path)
    diff = _word_level_diff(before_plain.split(), after_plain.split())
    if diff:
        xml_path.write_text(original_xml_text, encoding="utf-8")
        meta_path.write_text(original_meta_text, encoding="utf-8")
        _cleanup_fragments(xml_path)
        return diff, []

    html_path = xml_path.with_suffix(".html")
    build_html(xml_path, html_path)
    return [], []


def main():
    if len(sys.argv) != 3:
        print("usage: atomize_existing_document.py <path/to/doc.xml> <path/to/doc.meta.xml>",
              file=sys.stderr)
        return 2
    xml_path = Path(sys.argv[1])
    meta_path = Path(sys.argv[2])
    if not xml_path.is_file() or not meta_path.is_file():
        print(f"error: missing input file(s): {xml_path}, {meta_path}", file=sys.stderr)
        return 2
    diff, errors = atomize_existing_document(xml_path, meta_path)
    if errors:
        print(f"VALIDATION FAILED, rolled back: {xml_path}")
        for e in errors:
            print(f"  {e}")
        return 1
    if diff:
        print(f"CONTENT CHANGED, rolled back: {xml_path}")
        for line in diff:
            print(f"  {line}")
        return 1
    print(f"OK: {xml_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd docs/scripts/tests && python3 -m unittest test_atomize_existing_document -v`
Expected: both tests PASS.

- [ ] **Step 6: Clean up the pilot copy fixture directory tracking**

```bash
git add docs/scripts/tests/fixtures/atomize_pilot
```

(This directory holds a static copy of real content used only as immutable test input — the
test itself works in a separate `atomize_tmp` scratch directory that's cleaned up in
`tearDown`, so `atomize_pilot` is safe to commit permanently as a fixture.)

- [ ] **Step 7: Run the full test suite**

Run: `python3 -m unittest discover -s docs/scripts/tests -v`
Expected: all PASS.

- [ ] **Step 8: Commit**

```bash
git add docs/scripts/atomize_existing_document.py docs/scripts/tests/test_atomize_existing_document.py docs/scripts/tests/fixtures/atomize_pilot
git commit -m "feat: add atomize_existing_document.py migration script with rollback on failure"
```

---

**◆ Process Discipline checkpoint — do not skip.** Before Task 10: run the full test suite one
more time from a clean state (`python3 -m unittest discover -s docs/scripts/tests -v`) and
confirm `git status --short` shows only the files this plan's tasks so far are expected to have
touched. Then: **code review** (dispatch a code-reviewer agent over the diff since this plan
started), fix anything it flags, **simplify pass** (parallel review agents: reuse,
simplification, efficiency, altitude — matching commit `4f6a9f7`'s pattern), fix anything it
flags, re-run the full test suite again. Only proceed to Task 10 once both passes are clean.

---

### Task 10: Code review + simplify pass (process step, not a code task)

**Files:** none directly — this operates on the cumulative diff from Tasks 1-9.

- [ ] **Step 1: Code review**

Dispatch a code-reviewer agent (or run `/code-review`) scoped to the diff introduced by Tasks
1-9. Report findings.

- [ ] **Step 2: Fix findings, re-verify**

Apply any real findings. Run: `python3 -m unittest discover -s docs/scripts/tests -v` — must be
all-PASS before continuing.

- [ ] **Step 3: Simplify pass**

Dispatch 4 parallel review agents (reuse, simplification, efficiency, altitude — the same
`/simplify` pattern used in commit `4f6a9f7`) over the same diff.

- [ ] **Step 4: Fix findings, re-verify**

Apply any real findings (skip anything that would make the new code inconsistent with
established file conventions, same judgment call documented for the original tool's simplify
pass). Run the full test suite again.

- [ ] **Step 5: Commit if anything changed**

```bash
git add -A
git commit -m "refactor: apply code review + simplify findings from Tasks 1-9"
```

(Skip this commit if nothing changed.)

---

### Task 11: Pilot migration — 2 corpus documents + the paper, then ask the user

**Files:** (data, not code)
- Modify: `docs/cross-cutting/patron-as-client.xml`, `.meta.xml`, `.html` (small pilot)
- Modify: `docs/court-record/theory/.../the-architecture-of-non-consensual-legality.xml`,
  `.meta.xml`, `.html` (largest document, most sections — locate the exact path first)
- Modify: `docs/papers/ai_and_ip/llm-database-theory/src/01-llm-database-theory.xml` and its
  `generated/`+`html/` outputs (the paper's own build path, distinct from `atomize_existing_document.py`'s
  HTML rebuild — see Step 4)

**Interfaces:**
- Consumes: `atomize_existing_document.py` (Task 9).

- [ ] **Step 1: Locate the largest document's exact path**

```bash
find docs/court-record -name "the-architecture-of-non-consensual-legality.xml"
```

- [ ] **Step 2: Run the migration script on the 2 corpus pilots**

```bash
python3 docs/scripts/atomize_existing_document.py \
  docs/cross-cutting/patron-as-client.xml \
  docs/cross-cutting/patron-as-client.meta.xml

python3 docs/scripts/atomize_existing_document.py \
  <path-found-in-step-1>.xml \
  <path-found-in-step-1>.meta.xml
```

Expected: both print `OK: <path>`. If either prints `VALIDATION FAILED` or `CONTENT CHANGED`,
this is the systematic-debugging trigger from Process Discipline — stop, investigate root
cause, do not force through.

- [ ] **Step 3: Independently re-verify both (don't just trust the script's own report)**

```bash
for f in docs/cross-cutting/patron-as-client.xml <path-from-step-1>; do
  echo "== $f =="
  xmllint --noout --xinclude "$f" && echo "well-formed OK"
  jing -c docs/schema/docbook-corpus.rnc "$f" && echo "schema OK"
done
```

Expected: `well-formed OK` and `schema OK` for both.

- [ ] **Step 4: Handle the paper's article separately (no .meta.xml pair to pass)**

The paper's articles use the shared `00-metadata.xml` directly (not a per-article `.meta.xml`),
so `atomize_existing_document.py`'s metadata-rewrite step doesn't apply here — only the
section-splitting matters for the paper. Write a small one-off Python snippet (not a permanent
script — this is a single manual operation, not one this plan repeats):

```bash
python3 -c "
import sys
sys.path.insert(0, 'docs/scripts')
import xml.etree.ElementTree as ET
from convert_to_docbook import split_into_fragments, render_docbook_plain, validate, build_html, _word_level_diff
from pathlib import Path

xml_path = Path('docs/papers/ai_and_ip/llm-database-theory/src/01-llm-database-theory.xml')
before = render_docbook_plain(xml_path)
tree = ET.parse(xml_path)
article = tree.getroot()
split_into_fragments(article, xml_path.parent, xml_path.stem)
new_tree = ET.ElementTree(article)
ET.indent(new_tree, space='  ')
new_tree.write(xml_path, encoding='unicode', xml_declaration=True)
errors = validate(xml_path)
print('errors:', errors)
if not errors:
    after = render_docbook_plain(xml_path)
    diff = _word_level_diff(before.split(), after.split())
    print('diff:', diff)
"
```

Expected: `errors: []` and `diff: []`. If not, this is the systematic-debugging trigger — stop.

- [ ] **Step 5: Rebuild the paper's HTML and LaTeX outputs through the Makefile**

```bash
cd docs/papers/ai_and_ip/llm-database-theory
make html latex
diff generated/01-llm-database-theory.html html/01-llm-database-theory.html || echo "HTML changed — expected, contains new nav wrapper from fragments; inspect manually"
cp generated/*.html html/
cd /home/metavacua/legal-theory
```

- [ ] **Step 6: Run the full test suite one more time**

Run: `python3 -m unittest discover -s docs/scripts/tests -v`
Expected: all PASS.

- [ ] **Step 7: Ask the user before proceeding to the full batch**

Per Process Discipline: this is the checkpoint. Summarize what was migrated (2 corpus documents
+ 1 paper article), what was verified (schema, well-formedness, content-preservation diff empty,
rebuilt HTML/LaTeX), and ask whether to proceed to Task 14's full batch of the remaining 114
corpus documents + the paper's second article. Do not proceed without an explicit answer.

- [ ] **Step 8: Commit the pilot** (only after the user confirms proceeding)

```bash
git add docs/cross-cutting/patron-as-client.xml docs/cross-cutting/patron-as-client.meta.xml \
        docs/cross-cutting/patron-as-client.html docs/cross-cutting/patron-as-client/ \
        <largest-document-paths> \
        docs/papers/ai_and_ip/llm-database-theory/src/01-llm-database-theory.xml \
        docs/papers/ai_and_ip/llm-database-theory/src/01-llm-database-theory/ \
        docs/papers/ai_and_ip/llm-database-theory/generated/ \
        docs/papers/ai_and_ip/llm-database-theory/html/
git commit -m "migrate: atomize pilot (2 corpus documents + 1 paper article) to shell+fragments"
```

---

### Task 12: Update the paper's `00-metadata.xml`

**Files:**
- Modify: `docs/papers/ai_and_ip/llm-database-theory/src/00-metadata.xml`

**Interfaces:**
- Consumes: `docs/common/shared-metadata.xml` (Task 1), the `.//` XPath fixes (Tasks 2-3).

- [ ] **Step 1: Edit the file**

`docs/papers/ai_and_ip/llm-database-theory/src/00-metadata.xml` currently has `dc:publisher`,
`dc:language`, and `dc:rights` inline, byte-identical to the shared file's values (verified in
spec Section 6). Remove exactly those 3 lines and add one `xi:include` in their place — nothing
else in the file changes. `dc:creator`, `authorgroup` (with its extra `<uri>` the shared block
doesn't have), and `legalnotice` all stay exactly as they are; this task doesn't touch them, so
no duplicate/conflicting values are introduced.

Change:

```xml
  <dc:publisher>metavacua/legal-theory (GitHub)</dc:publisher>
  <dc:date>2026-07-01</dc:date>
  <dc:type>ScholarlyArticle</dc:type>
  <dc:language>en</dc:language>
  <dc:rights>CC BY-SA 4.0</dc:rights>
```

to:

```xml
  <dc:date>2026-07-01</dc:date>
  <dc:type>ScholarlyArticle</dc:type>
  <xi:include xmlns:xi="http://www.w3.org/2001/XInclude" href="../../../../common/shared-metadata.xml"/>
```

(No `xpointer` attribute — per Task 1's finding, `jing` doesn't support the `xpointer()` scheme,
so this uses the same plain whole-file include already proven in Tasks 1-3. It pulls in the
entire shared block, wrapped in `<shared>` — including `dc:creator`, `authorgroup`, and
`legalnotice` a second time, alongside the paper's own. This is fine: `db:info { any }` in the
schema permits it, and every XSLT lookup that matters (`.//db:authorgroup/...`,
`db:info//db:legalnotice/db:para`, `db:info//dc:creator`) is a *first-match* `xsl:value-of`, and
the paper's own `dc:creator`/`authorgroup`/`legalnotice` are declared earlier in the file — in
document order — than the `xi:include`, so they're the ones actually selected. Verify this in
Step 3.)

- [ ] **Step 2: Verify resolution**

```bash
xmllint --xinclude docs/papers/ai_and_ip/llm-database-theory/src/00-metadata.xml | grep -E "dc:publisher|dc:language|dc:rights"
```

Expected: 3 lines showing `metavacua/legal-theory (GitHub)`, `en`, `CC BY-SA 4.0` (now sourced
from the shared file, not inline).

- [ ] **Step 3: Rebuild the paper and verify no visible regression**

```bash
cd docs/papers/ai_and_ip/llm-database-theory
make html latex
grep -A1 "byline" generated/01-llm-database-theory.html
cd /home/metavacua/legal-theory
```

Expected: the byline still shows "Ian D.L.N. McLean" (the paper's own `authorgroup`, unaffected
by this metadata change — Task 11 already migrated this article's sections; this task is purely
about metadata dedup, layered on top).

- [ ] **Step 4: Commit**

```bash
git add docs/papers/ai_and_ip/llm-database-theory/src/00-metadata.xml docs/papers/ai_and_ip/llm-database-theory/generated/ docs/papers/ai_and_ip/llm-database-theory/html/
git commit -m "refactor: paper's 00-metadata.xml shares publisher/language/rights from shared-metadata.xml"
```

---

### Task 13: `build-corpus.yml` — discriminate by root element

**Files:**
- Modify: `.github/workflows/build-corpus.yml`

**Interfaces:** none — CI configuration only.

- [ ] **Step 1: Replace the file-discovery step**

Current step (`Validate and rebuild corpus HTML`):

```yaml
      - name: Validate and rebuild corpus HTML
        run: |
          set -euo pipefail
          while IFS= read -r xml; do
            echo "== $xml =="
            xmllint --noout --xinclude "$xml"
            jing -c docs/schema/docbook-corpus.rnc "$xml"
            xsltproc --xinclude docs/xsl/html5.xsl "$xml" > "${xml%.xml}.html"
          done < <(find docs -name '*.xml' -not -name '*.meta.xml' -not -path 'docs/papers/*' -not -path '*/scratch/*' | sort)
```

Replace with:

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
          done < <(find docs -name '*.xml' -not -path '*/scratch/*' | sort)
```

This drops the `-not -name '*.meta.xml'` and `-not -path 'docs/papers/*'` exclusions (no longer
needed — the root-element check already skips `.meta.xml` files, `shared-metadata.xml`, and
every section-fragment file, none of which have an `article` root; it correctly still picks up
the paper's 2 real articles now that they're in scope).

- [ ] **Step 2: Verify locally before pushing**

```bash
while IFS= read -r xml; do
  root_element="$(xmllint --xpath 'name(/*)' "$xml" 2>/dev/null || true)"
  [ "$root_element" = "article" ] && echo "$xml"
done < <(find docs -name '*.xml' -not -path '*/scratch/*' | sort) | wc -l
```

Expected: a count matching the number of real top-level documents (117 corpus + 2 paper
articles = 119, once Task 14 completes; fewer than that right after this task, since only the
Task 11 pilot has been migrated so far — the count should still equal the total number of
`<article>`-rooted files regardless of migration state, since unmigrated documents are still
`<article>`-rooted monoliths too).

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/build-corpus.yml
git commit -m "ci: discriminate build-corpus.yml targets by root element, not file path"
```

- [ ] **Step 4: Push and watch the workflow run for real**

```bash
git push origin claude/llm-database-theory-codification
```

Then use `gh run list --branch claude/llm-database-theory-codification --limit 3` and `gh run
watch <id> --exit-status` to confirm it succeeds on real CI infrastructure, per the pattern
already established this session for `build-corpus.yml`'s original rollout.

---

### Task 14: Batch migration — remaining 114 corpus documents + the paper's 2nd article

**Files:** (data, not code) — all remaining unmigrated `.xml`/`.meta.xml`/`.html` files and their
new `<stem>/` fragment directories.

**Interfaces:**
- Consumes: `atomize_existing_document.py` (Task 9), confirmed working via the Task 11 pilot and
  approved by the user.

- [ ] **Step 1: Enumerate every remaining corpus document (excluding already-migrated pilots)**

```bash
find docs -name "*.xml" -not -name "*.meta.xml" -not -path "*/papers/*" -not -path "*/scratch/*" \
  | grep -v "docs/cross-cutting/patron-as-client.xml" \
  | grep -v "the-architecture-of-non-consensual-legality.xml" \
  | sort > /tmp/remaining-corpus-docs.txt
wc -l /tmp/remaining-corpus-docs.txt
```

Expected: 115 (117 total minus the 2 pilot corpus documents already migrated in Task 11).

- [ ] **Step 2: Run the migration script over every remaining document, tracking failures**

```bash
> /tmp/atomize-failures.txt
while IFS= read -r xml; do
  meta="${xml%.xml}.meta.xml"
  echo "== $xml =="
  python3 docs/scripts/atomize_existing_document.py "$xml" "$meta" || echo "$xml" >> /tmp/atomize-failures.txt
done < /tmp/remaining-corpus-docs.txt
echo "--- failures ---"
cat /tmp/atomize-failures.txt
wc -l /tmp/atomize-failures.txt
```

Expected: `/tmp/atomize-failures.txt` is empty (0 lines) — every document is a deterministic,
already-valid DocBook file with no per-document judgment calls needed, per spec Section 8. If
**any** document fails, this is the systematic-debugging trigger from Process Discipline: stop,
investigate that specific document's failure (it was rolled back automatically, so the corpus
is not in a broken state), root-cause it, and do not proceed to Step 3 until every failure is
either fixed and re-run, or explicitly surfaced to the user per the "ask" clause.

- [ ] **Step 3: Migrate the paper's second article**

Repeat Task 11 Step 4's one-off snippet, substituting
`docs/papers/ai_and_ip/llm-database-theory/src/02-legal-corpus-connections.xml`.

- [ ] **Step 4: Rebuild the paper's HTML/LaTeX outputs**

```bash
cd docs/papers/ai_and_ip/llm-database-theory
make html latex
cp generated/*.html html/
cd /home/metavacua/legal-theory
```

- [ ] **Step 5: Run the full test suite**

Run: `python3 -m unittest discover -s docs/scripts/tests -v`
Expected: all PASS.

- [ ] **Step 6: Run the full corpus link/anchor sweep**

Reuse the same sweep script pattern already used after every matter conversion earlier this
session (reimplements GitHub's heading-slug algorithm, checks every link in `docs/index.md` and
every internal cross-reference resolves and every anchor exists). Confirm 0 broken files, 0
broken anchors.

- [ ] **Step 7: Independently spot-check schema validation on a sample**

```bash
for f in $(shuf -n 10 /tmp/remaining-corpus-docs.txt); do
  jing -c docs/schema/docbook-corpus.rnc "$f" && echo "OK: $f"
done
```

Expected: `OK:` for all 10 sampled files.

- [ ] **Step 8: Stage and commit**

```bash
git add docs/
git status --short | grep '^ D' # confirm nothing was deleted that shouldn't have been
git commit -m "$(cat <<'EOF'
migrate: atomize remaining 115 corpus documents + paper's 2nd article

Completes the corpus atomization: every corpus document and the
flagship paper's 2 articles are now a thin shell + per-top-level-
section fragment files, verified via schema validation, well-
formedness, and word-level content-preservation diff against each
document's pre-migration resolved content (all empty diffs, all
rolled back automatically on any failure — none occurred).
EOF
)"
```

- [ ] **Step 9: Push and watch CI + verify live**

```bash
git push origin claude/llm-database-theory-codification
```

Watch `Validate & Build DocBook Corpus`, `Build DocBook papers`, and `Deploy Pages` via `gh run
list` / `gh run watch <id> --exit-status`. Then `curl` a handful of live pages (at minimum the 2
pilot documents from Task 11 and 2-3 newly-migrated ones) to confirm 200 responses and correct
`<title>` tags, matching the verification pattern used after every prior deploy this session.

---

### Task 15: Update the design spec's living log

**Files:**
- Modify: `docs/superpowers/specs/2026-07-22-corpus-atomization-design.md`

- [ ] **Step 1: Append a completion log entry**

Following the same pattern as `2026-07-21-docbook-corpus-migration-design.md`'s living log
(e.g. commit `0fa02a7`'s Phase 2 completion note), append a section to the end of
`2026-07-22-corpus-atomization-design.md` recording: the pilot (2 corpus docs + paper article
1), the batch (115 corpus docs + paper article 2), any deviations from the original spec found
during implementation (e.g., the Task 12 clarification on which paper metadata fields are
actually shared), and the final commit hashes.

- [ ] **Step 2: Commit**

```bash
git add docs/superpowers/specs/2026-07-22-corpus-atomization-design.md
git commit -m "docs: log corpus atomization completion in the design spec"
git push origin claude/llm-database-theory-codification
```

# DocBook Conversion Tool Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `docs/scripts/convert_to_docbook.py`, a tool that converts one Markdown document into validated, XSLT-buildable DocBook 5.2 XML — the reusable engine the corpus-wide migration (design spec's Section 3 "operational rollout") will invoke once per document, later, as separate work. This plan does not convert any of the 123 corpus documents; it builds and tests the tool in isolation using small synthetic fixtures.

**Architecture:** `pandoc -t docbook5` does the Markdown→XML structural conversion; a Python post-processing layer wraps pandoc's output (which is a bare `<section>` fragment, sometimes several sibling fragments with no shared root) into a proper `<article>`, injects a per-document metadata `XInclude`, sanitizes invalid `xml:id`s, validates against the shared RELAX NG schema, builds HTML5 via the shared XSLT, and checks content preservation by round-tripping both the original Markdown and the built XML through `pandoc -t plain` and diffing.

**Tech Stack:** Python 3 stdlib only (`xml.etree.ElementTree`, `difflib`, `subprocess`, `unittest`) + `pandoc` (new dependency, confirmed available via `apt-get install pandoc`) + the existing `xmllint`/`xsltproc`/`jing` toolchain.

## Global Constraints

- No new Python package dependencies — stdlib only. `pandoc` is the one new external tool; document it in prerequisites everywhere `xsltproc`/`libxml2-utils` are already documented.
- Every function gets a test before (or as) it's implemented, per `superpowers:test-driven-development`. Run with `python3 -m unittest discover -s docs/scripts/tests -v`.
- Test fixtures are small and synthetic (a handful of lines each) — never the real 123-document corpus. Fast, focused, independent of corpus content that may change.
- This plan converts zero real corpus documents. Its deliverable is the tool plus a passing test suite. Corpus conversion is separate, future, operational work per the design spec.
- License footer requirement from the reorganization plan (`docs/superpowers/plans/2026-07-20-repo-accessibility-reorganization.md`) carries forward via `write_metadata()`'s fixed CC BY-SA 4.0 / Ian D.L.N. McLean fields — Task 5 below.

---

## Task 1: Promote shared schema/xsl and repoint the paper's build

**Files:**
- Create: `docs/schema/docbook-corpus.rnc` (moved from `docs/papers/ai_and_ip/llm-database-theory/schema/custom.rnc`)
- Create: `docs/xsl/html5.xsl`, `docs/xsl/latex.xsl` (moved from `docs/papers/ai_and_ip/llm-database-theory/xsl/`)
- Modify: `docs/papers/ai_and_ip/llm-database-theory/Makefile`
- Delete: `docs/papers/ai_and_ip/llm-database-theory/schema/`, `docs/papers/ai_and_ip/llm-database-theory/xsl/` (now empty)

**Interfaces:**
- Produces: `docs/schema/docbook-corpus.rnc`, `docs/xsl/html5.xsl`, `docs/xsl/latex.xsl` — the shared validation/build targets every later task's tests reference by this exact path.

- [ ] **Step 1: Move the three shared files**

```bash
cd /home/metavacua/legal-theory
mkdir -p docs/schema docs/xsl
git mv docs/papers/ai_and_ip/llm-database-theory/schema/custom.rnc docs/schema/docbook-corpus.rnc
git mv docs/papers/ai_and_ip/llm-database-theory/xsl/html5.xsl docs/xsl/html5.xsl
git mv docs/papers/ai_and_ip/llm-database-theory/xsl/latex.xsl docs/xsl/latex.xsl
rmdir docs/papers/ai_and_ip/llm-database-theory/schema docs/papers/ai_and_ip/llm-database-theory/xsl
```

- [ ] **Step 2: Repoint the paper's Makefile**

In `docs/papers/ai_and_ip/llm-database-theory/Makefile`, every reference to `xsl/html5.xsl`, `xsl/latex.xsl`, and `schema/custom.rnc` becomes `../../../xsl/html5.xsl`, `../../../xsl/latex.xsl`, `../../../schema/docbook-corpus.rnc` (three directories up from `docs/papers/ai_and_ip/llm-database-theory/` to `docs/`). Read the current file first to get exact line content — do not guess at surrounding context:

```bash
grep -n 'xsl/\|schema/' docs/papers/ai_and_ip/llm-database-theory/Makefile
```

Then apply the same substitution to each matched line: `xsl/html5.xsl` → `../../../xsl/html5.xsl`, `xsl/latex.xsl` → `../../../xsl/latex.xsl`, `schema/custom.rnc` → `../../../schema/docbook-corpus.rnc`.

- [ ] **Step 3: Verify the paper still builds clean (regression check)**

```bash
cd docs/papers/ai_and_ip/llm-database-theory
rm -rf generated
make all
echo "exit: $?"
```
Expected: `exit: 0`, and `make validate`'s RNG step prints `OK: src/01-llm-database-theory.xml` and `OK: src/02-legal-corpus-connections.xml` (no errors). Clean up: `rm -rf generated`.

- [ ] **Step 4: Update `.github/workflows/build-papers.yml`'s reference to the schema/xsl paths**

The workflow doesn't reference `xsl/`/`schema/` paths directly (it just runs `make html` inside the paper's directory), so no change needed there — confirm by reading the current file:

```bash
grep -n 'xsl\|schema' .github/workflows/build-papers.yml
```
Expected: no matches. If there are matches, update them to the new `docs/xsl/`/`docs/schema/` paths.

- [ ] **Step 5: Commit**

```bash
git add docs/schema docs/xsl docs/papers/ai_and_ip/llm-database-theory/Makefile
git commit -m "refactor: promote schema/xsl to shared docs/ locations for corpus-wide reuse"
```

---

## Task 2: Scaffold the tool package and its test runner

**Files:**
- Create: `docs/scripts/convert_to_docbook.py`
- Create: `docs/scripts/tests/__init__.py`
- Create: `docs/scripts/tests/test_convert_to_docbook.py`
- Create: `docs/scripts/tests/fixtures/` (directory, populated in later tasks)

**Interfaces:**
- Produces: the module path `convert_to_docbook` every later task's tests import from, and the `python3 -m unittest discover -s docs/scripts/tests -v` test-runner convention every later task uses.

- [ ] **Step 1: Write the failing test**

Create `docs/scripts/tests/test_convert_to_docbook.py`:

```python
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class TestScaffold(unittest.TestCase):
    def test_module_importable(self):
        import convert_to_docbook  # noqa: F401


if __name__ == "__main__":
    unittest.main()
```

Create empty `docs/scripts/tests/__init__.py` (zero bytes).

- [ ] **Step 2: Run to verify it fails**

```bash
python3 -m unittest discover -s docs/scripts/tests -v
```
Expected: `ModuleNotFoundError: No module named 'convert_to_docbook'`.

- [ ] **Step 3: Create the module**

Create `docs/scripts/convert_to_docbook.py`:

```python
"""Convert a Markdown document to validated, XSLT-buildable DocBook 5.2 XML."""
```

- [ ] **Step 4: Run test to verify it passes**

```bash
python3 -m unittest discover -s docs/scripts/tests -v
```
Expected: `test_module_importable ... ok`.

- [ ] **Step 5: Commit**

```bash
mkdir -p docs/scripts/tests/fixtures
git add docs/scripts/convert_to_docbook.py docs/scripts/tests/
git commit -m "feat(convert-to-docbook): scaffold module and test runner"
```

---

## Task 3: `slugify()` and `extract_title()`

**Files:**
- Modify: `docs/scripts/convert_to_docbook.py`
- Modify: `docs/scripts/tests/test_convert_to_docbook.py`
- Create: `docs/scripts/tests/fixtures/flat.md`
- Create: `docs/scripts/tests/fixtures/numbered_headings.md`

**Interfaces:**
- Produces: `slugify(text: str) -> str`, `extract_title(md_path: Path) -> str` — used by Task 4's `convert()` orchestration to compute the article's `xml:id` and `<title>`.

- [ ] **Step 1: Create the fixtures**

Create `docs/scripts/tests/fixtures/flat.md`:

```markdown
# A Flat Document

This document has one heading and no sub-sections. It exists to test
the case where pandoc's output, once unwrapped, leaves bare paragraph
content directly under the article.

- First item
- Second item
```

Create `docs/scripts/tests/fixtures/numbered_headings.md`:

```markdown
# Numbered Sections

## 1. First Section

Pandoc auto-generates this section's xml:id from its heading text,
which starts with a digit — not a valid XML NCName unless sanitized.

## 2. Second Section

Same issue, second instance.
```

- [ ] **Step 2: Write the failing test**

Add to `docs/scripts/tests/test_convert_to_docbook.py`:

```python
class TestSlugifyAndTitle(unittest.TestCase):
    def test_slugify_basic(self):
        from convert_to_docbook import slugify
        self.assertEqual(slugify("A Flat Document"), "a-flat-document")

    def test_slugify_leading_digit_gets_prefixed(self):
        from convert_to_docbook import slugify
        self.assertEqual(slugify("1. First Section"), "s-1-first-section")

    def test_slugify_empty_string(self):
        from convert_to_docbook import slugify
        self.assertEqual(slugify(""), "s")

    def test_extract_title_reads_first_heading(self):
        from convert_to_docbook import extract_title
        fixtures = Path(__file__).resolve().parent / "fixtures"
        self.assertEqual(extract_title(fixtures / "flat.md"), "A Flat Document")

    def test_extract_title_falls_back_to_filename(self):
        from convert_to_docbook import extract_title
        fixtures = Path(__file__).resolve().parent / "fixtures"
        no_heading = fixtures / "no_heading.md"
        no_heading.write_text("Just a paragraph, no heading.\n", encoding="utf-8")
        self.assertEqual(extract_title(no_heading), "No Heading")
        no_heading.unlink()
```

- [ ] **Step 3: Run to verify it fails**

```bash
python3 -m unittest discover -s docs/scripts/tests -v
```
Expected: `ImportError: cannot import name 'slugify'` (and similarly for `extract_title`).

- [ ] **Step 4: Implement**

Add to `docs/scripts/convert_to_docbook.py`:

```python
import re
from pathlib import Path


def slugify(text):
    text = text.strip().lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"\s+", "-", text)
    if not text:
        return "s"
    if re.match(r"^[0-9]", text):
        text = f"s-{text}"
    return text


def extract_title(md_path):
    with open(md_path, encoding="utf-8") as f:
        for line in f:
            m = re.match(r"^#{1,6}\s+(.*)", line)
            if m:
                return re.sub(r"[*_]", "", m.group(1)).strip()
    return Path(md_path).stem.replace("-", " ").replace("_", " ").title()
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
python3 -m unittest discover -s docs/scripts/tests -v
```
Expected: all tests pass, including `test_module_importable` from Task 2.

- [ ] **Step 6: Commit**

```bash
git add docs/scripts/convert_to_docbook.py docs/scripts/tests/
git commit -m "feat(convert-to-docbook): add slugify() and extract_title()"
```

---

## Task 4: Pandoc invocation, article wrapping, and xml:id sanitization

**Files:**
- Modify: `docs/scripts/convert_to_docbook.py`
- Modify: `docs/scripts/tests/test_convert_to_docbook.py`
- Create: `docs/scripts/tests/fixtures/multi_section.md`
- Create: `docs/scripts/tests/fixtures/with_link.md`

**Interfaces:**
- Consumes: `pandoc` (external tool, must be on `PATH`).
- Produces: `pandoc_to_docbook_fragment(md_path: Path) -> str`, `wrap_fragment(fragment: str, xml_id: str, title: str, metadata_href: str) -> tuple[xml.etree.ElementTree.Element, bool]` (the `bool` is `unwrapped` — `True` when the single-top-section case fired, needed by Task 7's content-preservation check), `sanitize_xml_ids(article: Element) -> None` (mutates in place).

- [ ] **Step 1: Create the fixtures**

Create `docs/scripts/tests/fixtures/multi_section.md` — three sibling top-level headings at the same level, the shape pandoc does *not* wrap in a shared root:

```markdown
### First Topic

Content for the first topic.

### Second Topic

Content for the second topic.
```

Create `docs/scripts/tests/fixtures/with_link.md`:

```markdown
# A Document With a Link

See [the source](https://example.com/source) for details.
```

- [ ] **Step 2: Write the failing tests**

Add to `docs/scripts/tests/test_convert_to_docbook.py`:

```python
DB_NS = "{http://docbook.org/ns/docbook}"
XLINK_NS = "{http://www.w3.org/1999/xlink}"
XML_NS = "{http://www.w3.org/XML/1998/namespace}"


class TestPandocAndWrapping(unittest.TestCase):
    def setUp(self):
        self.fixtures = Path(__file__).resolve().parent / "fixtures"

    def test_pandoc_produces_docbook_fragment(self):
        from convert_to_docbook import pandoc_to_docbook_fragment
        fragment = pandoc_to_docbook_fragment(self.fixtures / "flat.md")
        self.assertIn("<section", fragment)
        self.assertIn("A Flat Document", fragment)

    def test_wrap_single_section_unwraps_and_reports_true(self):
        from convert_to_docbook import pandoc_to_docbook_fragment, wrap_fragment
        fragment = pandoc_to_docbook_fragment(self.fixtures / "flat.md")
        article, unwrapped = wrap_fragment(fragment, "flat", "A Flat Document", "flat.meta.xml")
        self.assertTrue(unwrapped)
        self.assertEqual(article.tag, f"{DB_NS}article")
        # The wrapping <section>'s own title must not survive as a
        # duplicate — only the article's <title> carries it.
        child_tags = [c.tag for c in article]
        self.assertEqual(child_tags.count(f"{DB_NS}section"), 0)
        self.assertIn(f"{DB_NS}para", child_tags)

    def test_wrap_multi_section_keeps_all_and_reports_false(self):
        from convert_to_docbook import pandoc_to_docbook_fragment, wrap_fragment
        fragment = pandoc_to_docbook_fragment(self.fixtures / "multi_section.md")
        article, unwrapped = wrap_fragment(fragment, "multi", "Multi Section", "multi.meta.xml")
        self.assertFalse(unwrapped)
        child_sections = [c for c in article if c.tag == f"{DB_NS}section"]
        self.assertEqual(len(child_sections), 2)

    def test_wrap_includes_xi_include_with_metadata_href(self):
        from convert_to_docbook import pandoc_to_docbook_fragment, wrap_fragment
        fragment = pandoc_to_docbook_fragment(self.fixtures / "flat.md")
        article, _ = wrap_fragment(fragment, "flat", "A Flat Document", "flat.meta.xml")
        xi_ns = "{http://www.w3.org/2001/XInclude}"
        includes = [c for c in article if c.tag == f"{xi_ns}include"]
        self.assertEqual(len(includes), 1)
        self.assertEqual(includes[0].get("href"), "flat.meta.xml")

    def test_wrap_preserves_xlink_href(self):
        from convert_to_docbook import pandoc_to_docbook_fragment, wrap_fragment
        fragment = pandoc_to_docbook_fragment(self.fixtures / "with_link.md")
        article, _ = wrap_fragment(fragment, "with-link", "A Document With a Link", "x.meta.xml")
        links = article.findall(f".//{DB_NS}link")
        self.assertEqual(len(links), 1)
        self.assertEqual(links[0].get(f"{XLINK_NS}href"), "https://example.com/source")

    def test_sanitize_xml_ids_prefixes_digit_leading_ids(self):
        from convert_to_docbook import (
            pandoc_to_docbook_fragment, wrap_fragment, sanitize_xml_ids,
        )
        fragment = pandoc_to_docbook_fragment(self.fixtures / "numbered_headings.md")
        article, _ = wrap_fragment(fragment, "numbered", "Numbered Sections", "n.meta.xml")
        sanitize_xml_ids(article)
        ids = [el.get(f"{XML_NS}id") for el in article.iter() if el.get(f"{XML_NS}id")]
        self.assertTrue(ids, "expected at least one xml:id in the converted tree")
        for id_value in ids:
            self.assertRegex(id_value, r"^[A-Za-z_]")
```

- [ ] **Step 3: Run to verify failure**

```bash
python3 -m unittest discover -s docs/scripts/tests -v
```
Expected: `ImportError: cannot import name 'pandoc_to_docbook_fragment'`.

- [ ] **Step 4: Implement**

Add to `docs/scripts/convert_to_docbook.py`:

```python
import subprocess
import xml.etree.ElementTree as ET

DB_NS = "http://docbook.org/ns/docbook"
XI_NS = "http://www.w3.org/2001/XInclude"
XLINK_NS = "http://www.w3.org/1999/xlink"
XML_NS = "http://www.w3.org/XML/1998/namespace"
ET.register_namespace("", DB_NS)
ET.register_namespace("xi", XI_NS)
ET.register_namespace("xlink", XLINK_NS)


def pandoc_to_docbook_fragment(md_path):
    result = subprocess.run(
        ["pandoc", "-f", "gfm", "-t", "docbook5", str(md_path)],
        capture_output=True, text=True, check=True,
    )
    return result.stdout


def wrap_fragment(fragment, xml_id, title, metadata_href):
    # Pandoc emits one or more top-level <section> elements with no
    # shared root, each carrying its own repeated xmlns declarations.
    # Strip the repeats and wrap everything in one parseable <root>.
    stripped = fragment.replace(f'xmlns="{DB_NS}" ', "").replace(
        f'xmlns:xlink="{XLINK_NS}" ', ""
    )
    wrapped = f'<root xmlns="{DB_NS}" xmlns:xlink="{XLINK_NS}">{stripped}</root>'
    root = ET.fromstring(wrapped)
    children = list(root)

    article = ET.Element(f"{{{DB_NS}}}article")
    article.set("version", "5.2")
    article.set(f"{{{XML_NS}}}id", xml_id)
    article.set(f"{{{XML_NS}}}lang", "en")

    xi_include = ET.SubElement(article, f"{{{XI_NS}}}include")
    xi_include.set("href", metadata_href)

    title_el = ET.SubElement(article, f"{{{DB_NS}}}title")
    title_el.text = title

    # A single top-level <section> whose own <title> just duplicates
    # the article title we already set: unwrap it so its children
    # become the article's direct children, matching the flatter
    # structure the hand-authored paper already uses. Multiple
    # top-level siblings have no single title to unwrap from, so they
    # stay as direct article children as-is.
    unwrapped = len(children) == 1 and children[0].tag == f"{{{DB_NS}}}section"
    if unwrapped:
        for child in list(children[0]):
            if child.tag != f"{{{DB_NS}}}title":
                article.append(child)
    else:
        for child in children:
            article.append(child)

    sanitize_xml_ids(article)
    return article, unwrapped


def sanitize_xml_ids(article):
    xml_id_attr = f"{{{XML_NS}}}id"
    for el in article.iter():
        value = el.get(xml_id_attr)
        if value and re.match(r"^[0-9]", value):
            el.set(xml_id_attr, f"s-{value}")
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
python3 -m unittest discover -s docs/scripts/tests -v
```
Expected: all tests pass.

- [ ] **Step 6: Commit**

```bash
git add docs/scripts/convert_to_docbook.py docs/scripts/tests/
git commit -m "feat(convert-to-docbook): pandoc invocation, article wrapping, xml:id sanitization"
```

---

## Task 5: Metadata fragment generation

**Files:**
- Modify: `docs/scripts/convert_to_docbook.py`
- Modify: `docs/scripts/tests/test_convert_to_docbook.py`

**Interfaces:**
- Produces: `write_metadata(meta_path: Path, title: str) -> None`.

- [ ] **Step 1: Write the failing test**

Add to `docs/scripts/tests/test_convert_to_docbook.py`:

```python
class TestWriteMetadata(unittest.TestCase):
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
        rights_el = root.find(f"{dc_ns}rights")
        self.assertEqual(rights_el.text, "CC BY-SA 4.0")
        meta_path.unlink()
```

Add `import xml.etree.ElementTree as ET` to the test file's top-level imports if not already present (it is, from Task 4 — reuse it).

- [ ] **Step 2: Run to verify it fails**

```bash
python3 -m unittest discover -s docs/scripts/tests -v
```
Expected: `ImportError: cannot import name 'write_metadata'`.

- [ ] **Step 3: Implement**

Add to `docs/scripts/convert_to_docbook.py`:

```python
def write_metadata(meta_path, title):
    content = f"""<?xml version="1.0" encoding="UTF-8"?>
<info xmlns="{DB_NS}" xmlns:dc="http://purl.org/dc/terms/">
  <dc:title>{title}</dc:title>
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
</info>
"""
    Path(meta_path).write_text(content, encoding="utf-8")
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python3 -m unittest discover -s docs/scripts/tests -v
```
Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add docs/scripts/convert_to_docbook.py docs/scripts/tests/
git commit -m "feat(convert-to-docbook): add write_metadata()"
```

---

## Task 6: Validate and build (xmllint/jing/xsltproc wrappers)

**Files:**
- Modify: `docs/scripts/convert_to_docbook.py`
- Modify: `docs/scripts/tests/test_convert_to_docbook.py`

**Interfaces:**
- Consumes: `docs/schema/docbook-corpus.rnc`, `docs/xsl/html5.xsl` (Task 1's shared paths — hardcoded relative to repo root, resolved via a `REPO_ROOT` constant computed from `__file__`).
- Produces: `validate(xml_path: Path) -> list[str]` (empty list = valid; otherwise the list of error messages), `build_html(xml_path: Path, out_path: Path) -> None`.

- [ ] **Step 1: Write the failing tests**

Add to `docs/scripts/tests/test_convert_to_docbook.py`:

```python
class TestValidateAndBuild(unittest.TestCase):
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

    def test_validate_accepts_well_formed_document(self):
        from convert_to_docbook import validate
        xml_path = self._convert_fixture("flat.md", "flat", "A Flat Document")
        self.assertEqual(validate(xml_path), [])

    def test_validate_rejects_malformed_document(self):
        from convert_to_docbook import validate
        bad_path = self.fixtures / "bad.xml"
        bad_path.write_text("<article><unclosed></article>", encoding="utf-8")
        self.addCleanup(bad_path.unlink)
        errors = validate(bad_path)
        self.assertTrue(errors)

    def test_build_html_produces_output_with_title(self):
        from convert_to_docbook import build_html
        xml_path = self._convert_fixture("flat.md", "flat", "A Flat Document")
        html_path = self.fixtures / "flat.html"
        build_html(xml_path, html_path)
        self.addCleanup(html_path.unlink)
        content = html_path.read_text(encoding="utf-8")
        self.assertIn("A Flat Document", content)
```

- [ ] **Step 2: Run to verify failure**

```bash
python3 -m unittest discover -s docs/scripts/tests -v
```
Expected: `ImportError: cannot import name 'validate'`.

- [ ] **Step 3: Implement**

Add to `docs/scripts/convert_to_docbook.py`:

```python
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCHEMA_PATH = REPO_ROOT / "docs" / "schema" / "docbook-corpus.rnc"
HTML5_XSL_PATH = REPO_ROOT / "docs" / "xsl" / "html5.xsl"


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


def build_html(xml_path, out_path):
    result = subprocess.run(
        ["xsltproc", "--xinclude", str(HTML5_XSL_PATH), str(xml_path)],
        capture_output=True, text=True, check=True,
    )
    Path(out_path).write_text(result.stdout, encoding="utf-8")
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python3 -m unittest discover -s docs/scripts/tests -v
```
Expected: all tests pass. (Requires Task 1 to already be done — `docs/schema/docbook-corpus.rnc` and `docs/xsl/html5.xsl` must exist at those paths.)

- [ ] **Step 5: Commit**

```bash
git add docs/scripts/convert_to_docbook.py docs/scripts/tests/
git commit -m "feat(convert-to-docbook): add validate() and build_html()"
```

---

## Task 7: Content-preservation diff check

**Files:**
- Modify: `docs/scripts/convert_to_docbook.py`
- Modify: `docs/scripts/tests/test_convert_to_docbook.py`
- Create: `docs/scripts/tests/fixtures/with_hr.md`

**Interfaces:**
- Consumes: `unwrapped: bool` from Task 4's `wrap_fragment()`.
- Produces: `content_preservation_diff(md_path: Path, xml_path: Path, title: str, unwrapped: bool) -> list[str]` (empty list = clean; otherwise the flagged diff lines).

- [ ] **Step 1: Create the fixture**

Create `docs/scripts/tests/fixtures/with_hr.md` — exercises the one *known, accepted* difference class (pandoc's DocBook5 writer drops `---` horizontal rules entirely; this is a real, verified, cosmetic-only loss, not a bug to fix):

```markdown
# A Document With Dividers

First section content.

---

Second section content, after a horizontal rule.
```

- [ ] **Step 2: Write the failing tests**

Add to `docs/scripts/tests/test_convert_to_docbook.py`:

```python
class TestContentPreservationDiff(unittest.TestCase):
    def setUp(self):
        self.fixtures = Path(__file__).resolve().parent / "fixtures"

    def _convert_fixture(self, name, xml_id, title):
        from convert_to_docbook import (
            pandoc_to_docbook_fragment, wrap_fragment, write_metadata,
        )
        fragment = pandoc_to_docbook_fragment(self.fixtures / name)
        article, unwrapped = wrap_fragment(fragment, xml_id, title, f"{xml_id}.meta.xml")
        xml_path = self.fixtures / f"{xml_id}.xml"
        meta_path = self.fixtures / f"{xml_id}.meta.xml"
        write_metadata(meta_path, title)
        tree = ET.ElementTree(article)
        ET.indent(tree, space="  ")
        tree.write(xml_path, encoding="unicode", xml_declaration=True)
        self.addCleanup(xml_path.unlink)
        self.addCleanup(meta_path.unlink)
        return xml_path, unwrapped

    def test_clean_conversion_flags_nothing(self):
        from convert_to_docbook import content_preservation_diff
        xml_path, unwrapped = self._convert_fixture("flat.md", "flat", "A Flat Document")
        diff = content_preservation_diff(
            self.fixtures / "flat.md", xml_path, "A Flat Document", unwrapped
        )
        self.assertEqual(diff, [])

    def test_multi_section_conversion_flags_nothing(self):
        # No title-compensation needed here (unwrapped=False) — the first
        # section's own heading already carries the text verbatim.
        from convert_to_docbook import content_preservation_diff
        xml_path, unwrapped = self._convert_fixture(
            "multi_section.md", "multi", "Multi Section"
        )
        diff = content_preservation_diff(
            self.fixtures / "multi_section.md", xml_path, "Multi Section", unwrapped
        )
        self.assertEqual(diff, [])

    def test_dropped_horizontal_rule_is_a_known_accepted_difference(self):
        from convert_to_docbook import content_preservation_diff
        xml_path, unwrapped = self._convert_fixture(
            "with_hr.md", "with-hr", "A Document With Dividers"
        )
        diff = content_preservation_diff(
            self.fixtures / "with_hr.md", xml_path, "A Document With Dividers", unwrapped
        )
        self.assertEqual(diff, [])

    def test_genuinely_dropped_paragraph_is_flagged(self):
        from convert_to_docbook import content_preservation_diff
        xml_path, unwrapped = self._convert_fixture("flat.md", "flat", "A Flat Document")
        # Simulate real content loss: overwrite the built XML's body text.
        text = xml_path.read_text(encoding="utf-8")
        text = text.replace("This document has one heading", "Something else entirely")
        xml_path.write_text(text, encoding="utf-8")
        diff = content_preservation_diff(
            self.fixtures / "flat.md", xml_path, "A Flat Document", unwrapped
        )
        self.assertTrue(diff, "expected genuine content loss to be flagged")
```

- [ ] **Step 3: Run to verify failure**

```bash
python3 -m unittest discover -s docs/scripts/tests -v
```
Expected: `ImportError: cannot import name 'content_preservation_diff'`.

- [ ] **Step 4: Implement**

Add to `docs/scripts/convert_to_docbook.py`:

```python
import difflib


def _is_ignorable_diff_line(line):
    # unified_diff change lines start with '-' or '+'; a line that is,
    # once that marker is stripped, empty or pure dashes is pandoc's
    # DocBook5 writer dropping a Markdown horizontal rule (`---`) — a
    # verified, cosmetic-only, accepted difference. Anything else
    # (an actual sentence or word) is genuine content loss and must
    # not be swallowed here.
    body = line[1:].strip()
    return body == "" or set(body) <= {"-"}


def content_preservation_diff(md_path, xml_path, title, unwrapped):
    original = subprocess.run(
        ["pandoc", "-f", "gfm", "-t", "plain", str(md_path)],
        capture_output=True, text=True, check=True,
    ).stdout

    resolved = subprocess.run(
        ["xmllint", "--xinclude", str(xml_path)],
        capture_output=True, text=True, check=True,
    ).stdout

    roundtrip = subprocess.run(
        ["pandoc", "-f", "docbook", "-t", "plain", "-"],
        input=resolved, capture_output=True, text=True, check=True,
    ).stdout

    if unwrapped:
        # The wrapping <section>'s title was discarded when its
        # children were promoted to the article; pandoc's docbook
        # reader never renders <article><title> as body text, so add
        # the title back for a fair comparison against the original.
        roundtrip = f"{title}\n\n{roundtrip}"

    diff = list(difflib.unified_diff(
        original.splitlines(), roundtrip.splitlines(), lineterm=""
    ))
    changed = [
        line for line in diff
        if (line.startswith("-") or line.startswith("+"))
        and not line.startswith(("--- ", "+++ "))
        and not _is_ignorable_diff_line(line)
    ]
    return changed
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
python3 -m unittest discover -s docs/scripts/tests -v
```
Expected: all tests pass, including the genuine-content-loss test correctly flagging a non-empty diff.

- [ ] **Step 6: Commit**

```bash
git add docs/scripts/convert_to_docbook.py docs/scripts/tests/
git commit -m "feat(convert-to-docbook): add content_preservation_diff() safety check"
```

---

## Task 8: CLI orchestration and end-to-end test

**Files:**
- Modify: `docs/scripts/convert_to_docbook.py`
- Modify: `docs/scripts/tests/test_convert_to_docbook.py`
- Modify: `docs/papers/ai_and_ip/llm-database-theory/README.md` (add `pandoc` to Prerequisites, matching the existing `libxml2-utils`/`xsltproc` entries)

**Interfaces:**
- Consumes: every function from Tasks 3–7.
- Produces: `convert(md_path: Path, out_dir: Path) -> ConversionResult` (a small dataclass: `xml_path`, `html_path`, `errors: list[str]`, `content_diff: list[str]`) and a `python3 docs/scripts/convert_to_docbook.py <path/to/doc.md>` CLI entrypoint that prints a pass/fail summary and exits non-zero if `errors` or `content_diff` is non-empty. This is the exact tool the future corpus-wide rollout (design spec, Section 3) will invoke once per document — this task does not perform that rollout.

- [ ] **Step 1: Write the failing end-to-end test**

Add to `docs/scripts/tests/test_convert_to_docbook.py`:

```python
class TestConvertEndToEnd(unittest.TestCase):
    def setUp(self):
        self.fixtures = Path(__file__).resolve().parent / "fixtures"
        self.out_dir = self.fixtures / "out"
        self.out_dir.mkdir(exist_ok=True)

    def tearDown(self):
        for f in self.out_dir.iterdir():
            f.unlink()
        self.out_dir.rmdir()

    def test_convert_flat_document_end_to_end(self):
        from convert_to_docbook import convert
        result = convert(self.fixtures / "flat.md", self.out_dir)
        self.assertEqual(result.errors, [])
        self.assertEqual(result.content_diff, [])
        self.assertTrue(result.xml_path.exists())
        self.assertTrue(result.html_path.exists())
        self.assertIn("A Flat Document", result.html_path.read_text(encoding="utf-8"))

    def test_convert_multi_section_document_end_to_end(self):
        from convert_to_docbook import convert
        result = convert(self.fixtures / "multi_section.md", self.out_dir)
        self.assertEqual(result.errors, [])
        self.assertEqual(result.content_diff, [])

    def test_convert_numbered_headings_document_end_to_end(self):
        # Regression coverage for Task 4's xml:id sanitization, exercised
        # through the full pipeline including RNG validation.
        from convert_to_docbook import convert
        result = convert(self.fixtures / "numbered_headings.md", self.out_dir)
        self.assertEqual(result.errors, [])
```

- [ ] **Step 2: Run to verify failure**

```bash
python3 -m unittest discover -s docs/scripts/tests -v
```
Expected: `ImportError: cannot import name 'convert'`.

- [ ] **Step 3: Implement**

Add to `docs/scripts/convert_to_docbook.py`:

```python
import sys
from dataclasses import dataclass, field


@dataclass
class ConversionResult:
    xml_path: Path
    html_path: Path
    errors: list = field(default_factory=list)
    content_diff: list = field(default_factory=list)


def convert(md_path, out_dir):
    md_path = Path(md_path)
    out_dir = Path(out_dir)
    xml_id = slugify(md_path.stem)
    title = extract_title(md_path)
    meta_name = f"{md_path.stem}.meta.xml"

    fragment = pandoc_to_docbook_fragment(md_path)
    article, unwrapped = wrap_fragment(fragment, xml_id, title, meta_name)

    write_metadata(out_dir / meta_name, title)

    xml_path = out_dir / f"{md_path.stem}.xml"
    tree = ET.ElementTree(article)
    ET.indent(tree, space="  ")
    tree.write(xml_path, encoding="unicode", xml_declaration=True)

    errors = validate(xml_path)

    html_path = out_dir / f"{md_path.stem}.html"
    content_diff = []
    if not errors:
        build_html(xml_path, html_path)
        content_diff = content_preservation_diff(md_path, xml_path, title, unwrapped)

    return ConversionResult(
        xml_path=xml_path, html_path=html_path,
        errors=errors, content_diff=content_diff,
    )


def main():
    if len(sys.argv) != 2:
        print("usage: convert_to_docbook.py <path/to/doc.md>", file=sys.stderr)
        return 2
    md_path = Path(sys.argv[1])
    out_dir = md_path.parent
    result = convert(md_path, out_dir)
    if result.errors:
        print(f"VALIDATION FAILED: {md_path}")
        for e in result.errors:
            print(f"  {e}")
        return 1
    if result.content_diff:
        print(f"CONTENT PRESERVATION CHECK FAILED: {md_path}")
        for line in result.content_diff:
            print(f"  {line}")
        return 1
    print(f"OK: {md_path} -> {result.xml_path}, {result.html_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python3 -m unittest discover -s docs/scripts/tests -v
```
Expected: all tests across all 8 tasks pass — run the full suite, not just Task 8's new tests, as a final regression check.

- [ ] **Step 5: Try the CLI manually against a real corpus document (read-only — does not modify the corpus)**

```bash
mkdir -p /tmp/convert-smoke-test
python3 docs/scripts/convert_to_docbook.py docs/wip/jpa-and-city-cooperatives.md
```

Wait — this writes output next to the source file inside `docs/wip/`, which would leave untracked files in the working tree. Run it against a copy instead:

```bash
mkdir -p /tmp/convert-smoke-test
cp docs/wip/jpa-and-city-cooperatives.md /tmp/convert-smoke-test/
python3 docs/scripts/convert_to_docbook.py /tmp/convert-smoke-test/jpa-and-city-cooperatives.md
```
Expected: `OK: /tmp/convert-smoke-test/jpa-and-city-cooperatives.md -> ...xml, ...html`, exit code 0. Inspect `/tmp/convert-smoke-test/jpa-and-city-cooperatives.html` in a browser or `cat` it to confirm it looks right. Clean up: `rm -rf /tmp/convert-smoke-test`.

- [ ] **Step 6: Add `pandoc` to the paper's documented prerequisites**

In `docs/papers/ai_and_ip/llm-database-theory/README.md`, find the `### Prerequisites` code block (currently lists `libxml2-utils libxslt1-dev` for Debian/Ubuntu and `libxml2 libxslt` for macOS) and add `pandoc` to both the apt and brew install lines, plus a one-line note that it's required by `docs/scripts/convert_to_docbook.py`, not by the paper's own build.

- [ ] **Step 7: Commit**

```bash
git add docs/scripts/convert_to_docbook.py docs/scripts/tests/ docs/papers/ai_and_ip/llm-database-theory/README.md
git commit -m "feat(convert-to-docbook): CLI entrypoint, end-to-end test, document pandoc prerequisite"
```

---

## Self-Review

- **Spec coverage:** Design spec Section 1 (shared schema/xsl) → Task 1. Section 2's six-step recipe → Steps 1–5 covered by Tasks 3–7 (pandoc conversion, wrapping, metadata, validate, build, diff-check); Step 6 (git rm/commit the corpus document, rewrite inbound links) is explicitly the future operational rollout, not this plan, per the spec's own Section 3 and this plan's Global Constraints. Section 4 (testing/CI/safety net) → the TDD structure of every task IS the "tool testing" requirement; CI generalization and the corpus-wide rollout are future work once this tool exists and is reviewed.
- **No placeholders:** every step has complete, verified code — all of it was prototyped and actually run against real corpus documents (`docs/wip/jpa-and-city-cooperatives.md`, `docs/cross-cutting/tax-and-regulatory-thresholds-explained.md`, `docs/court-record/matters/google-platform-misclassification/{evidence/google-user-contracts.md,findings.md}`) before being written into this plan, including three real bugs this process found and fixed directly in the shared schema (Task 1's starting point): `db:para` not permitted directly under `db:article`, and the `mixed{any}` interleave-ambiguity error — see commit `3ee01a5`.
- **Type consistency:** `wrap_fragment()`'s `(Element, bool)` return in Task 4 matches its four call sites in Tasks 6–8 exactly (`article, unwrapped = wrap_fragment(...)` / `article, _ = wrap_fragment(...)` where `unwrapped` isn't needed). `content_preservation_diff()`'s four-argument signature (Task 7) matches Task 8's call inside `convert()`. `ConversionResult`'s four fields match every test's assertions against `result.errors`/`result.content_diff`/`result.xml_path`/`result.html_path`.
- **Not touched:** no file under `docs/court-record/**` is created, moved, or deleted anywhere in this plan — Task 8 Step 5's manual smoke test explicitly copies a document to `/tmp` first rather than running the tool against the corpus in place.

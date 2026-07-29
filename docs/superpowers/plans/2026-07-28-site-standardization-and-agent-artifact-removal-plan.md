# Site Standardization & Agent-Artifact Removal Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `docs/index.xml` a real, generated, first-class DocBook document; convert the 7
genuinely-authored README files to DocBook; drop Jekyll for a static-HTML Pages deployment;
relocate `docs/scripts/` out of the Pages source root; and remove this session's own planning-
document archive (`docs/superpowers/`) plus two other unjustified artifacts from the tracked
working tree.

**Architecture:** A new `scripts/generate_index.py` walks the corpus's real DocBook state (same
`_shell_articles()` selection logic `measure_citation_conformance.py` already uses) and emits
`docs/index.xml` + `docs/sitemap.xml`, built through the existing `build_html()` pipeline --
eliminating hand-maintenance drift structurally. `docs/scripts/` moves to `scripts/` (repo root)
first, since the generator lives there. Once nothing under `docs/` is Markdown,
`.github/workflows/deploy-pages.yml` switches from Jekyll to a direct static-HTML artifact upload.
`docs/superpowers/` (including this plan and its design doc) is removed from the tracked tree as
the final step, once everything else has landed and been verified -- git history is the durable
record; nothing is lost.

**Tech Stack:** Python 3 stdlib (`xml.etree.ElementTree`, `subprocess`, `pathlib` -- matching every
existing script's convention), `xmllint`/`jing`/`xsltproc` (existing), GitHub Actions
(`actions/upload-pages-artifact@v3`, replacing `actions/jekyll-build-pages@v1`).

## Global Constraints

- `docs/index.xml` gets the same `<info>` DCTERMS metadata block every other document gets via
  `write_metadata()`, and passes through the same `validate()` (real DocBook 5.2 grammar +
  DCTERMS-completeness policy) and `build_html()` pipeline as every other document -- no special
  casing, per explicit direction that the index is a scholarship document like any other, not a
  lesser navigational artifact.
- The generator (`scripts/generate_index.py`) does not fabricate descriptive prose for any
  document or category. It emits titles (read from each document's own `<info><title>`) and
  structural grouping only. Per-matter/per-category framing text is real authored content and is
  not synthesized.
- No task in this plan pushes to `origin` or deploys to GitHub Pages. Every task's verification is
  local (build, validate, diff, test). Deployment remains a separate, explicit step outside this
  plan, matching the existing convention for this branch.
- `docs/superpowers/` -- including this plan file and its design doc -- is removed from the tracked
  working tree only as this plan's final task, after every other task has landed and passed review.
  Earlier tasks' subagents still read their briefs from this plan file; it must exist until then.
- Root-level `README.md` and `LICENSE` (outside `docs/`, outside the Pages build) are not touched
  by this plan.

---

## File Structure

- Move `docs/scripts/` (22 `.py` files + `tests/`) to `scripts/` (repo root).
- Modify: `docs/scripts/build_bibliography.py` (now `scripts/build_bibliography.py`) -- one
  docstring path reference. `docs/scripts/audit_footnote_links.py` (now
  `scripts/audit_footnote_links.py`) -- one docstring reference, drop `docs/scripts` from its
  excluded-subdirectory list.
- Modify: `.github/workflows/build-corpus.yml` -- two `docs/scripts/...` references repointed;
  `docs/_config.yml`'s single `exclude:` entry logic no longer needed once Jekyll is dropped
  (Task 5).
- Delete: `.markdownlint-cli2.jsonc` (`docs/papers/ai_and_ip/llm-database-theory/scratch/` is
  kept -- see Task 2).
- Create: `scripts/generate_index.py`.
- Create: `docs/index.xml`, `docs/index.meta.xml`, `docs/sitemap.xml` (generated, then committed --
  matching every other built artifact's convention in this repo).
- Delete: `docs/index.md`, and 8 pure-listing `README.md` stub files (see Task 3).
- Create: 7 `README.xml` + `README.meta.xml` pairs (replacing the 7 authored `README.md` files),
  built to `README.html`.
- Modify: `.github/workflows/deploy-pages.yml` (drop Jekyll build step). Delete: `docs/_config.yml`.
- Delete: `docs/superpowers/` (20 pre-existing files + this plan + its design doc, as the final
  task).

---

### Task 1: Relocate `docs/scripts/` to `scripts/`

**Files:**
- Move: `docs/scripts/` → `scripts/` (directory move, all contents)
- Modify: `scripts/build_bibliography.py` (one docstring line)
- Modify: `scripts/audit_footnote_links.py` (one docstring line)
- Modify: `.github/workflows/build-corpus.yml` (two path references)

**Interfaces:**
- Consumes: nothing new -- every script's own `sys.path.insert(0, str(Path(__file__).resolve().parent))`
  convention is self-relative and unaffected by the move (confirmed by direct grep before this
  plan was written: every script uses this exact pattern, none hardcode `"docs/scripts"` as an
  import path).
- Produces: `scripts/` as the new home for every build/validation/test tool in this repo --
  consumed by Task 3's `generate_index.py` (created directly in the new location) and Task 4's
  README conversions (which reuse `build_html()` from its new path).

- [ ] **Step 1: Move the directory**

```bash
git mv docs/scripts scripts
```

- [ ] **Step 2: Fix the two hardcoded path references**

In `scripts/build_bibliography.py`, find the line (search for `docs/scripts/build_bibliography.py`):

```python
    "[unknown] rather than inferred. Generated by docs/scripts/build_bibliography.py from "
```

Change to:

```python
    "[unknown] rather than inferred. Generated by scripts/build_bibliography.py from "
```

In `scripts/audit_footnote_links.py`, find the line (search for `docs/papers, docs/scripts,`):

```python
    docs/papers, docs/scripts, docs/scratch, docs/bibliography per the
```

Change to (dropping `docs/scripts`, since it no longer exists under `docs/` to exclude):

```python
    docs/papers, docs/scratch, docs/bibliography per the
```

- [ ] **Step 3: Update `build-corpus.yml`'s two references**

In `.github/workflows/build-corpus.yml`, change:

```yaml
            python3 docs/scripts/check_dcterms_completeness.py "$xml"
```

to:

```yaml
            python3 scripts/check_dcterms_completeness.py "$xml"
```

and change the `find` line's exclusion filter from:

```yaml
          done < <(find docs -name '*.xml' -not -path '*/scratch/*' -not -path 'docs/scripts/*' | sort)
```

to (the exclusion is no longer needed -- `scripts/` isn't under `docs/` anymore, so `find docs`
never sees it):

```yaml
          done < <(find docs -name '*.xml' -not -path '*/scratch/*' | sort)
```

- [ ] **Step 4: Run the full test suite from the new location**

```bash
cd scripts && python3 -m unittest discover -s tests -p "test_*.py" 2>&1 | tail -10
```

Expected: `Ran 247 tests ... OK (skipped=8)` -- identical to the pre-move baseline. This confirms
the move broke no imports.

- [ ] **Step 5: Confirm no remaining references to the old path**

```bash
cd /home/metavacua/legal-theory/.worktrees/claude/llm-database-theory-codification-sdd-1785019559
git grep -n "docs/scripts" -- '*.py' '*.yml'
```

Expected: no output (the only two remaining `docs/scripts` mentions were fixed in Step 2; nothing
else in `.py`/`.yml` files references the old path). `docs/index.md` and the various `README.md`
files still mention `docs/scripts` in prose -- that's expected and handled by Tasks 3-4, not this
task.

- [ ] **Step 6: Commit**

```bash
git add -A scripts docs .github/workflows/build-corpus.yml
git commit -m "refactor: relocate docs/scripts/ to scripts/ -- it is tooling, not corpus content, and docs/ is the literal GitHub Pages source root"
```

---

### Task 2: Remove the dead lint config (`docs/papers/.../scratch/` kept -- see below)

**Corrected during execution, replacing the original task text outright rather than annotating
beside it:** this task originally also planned to delete
`docs/papers/ai_and_ip/llm-database-theory/scratch/{formulas,notes}.md`. Step 3 below's own
verification check (run for real during execution) found the opposite of what this plan assumed:
the paper's own `README.md` actively references both files -- its "Source Files" table lists them
alongside real build inputs, and its "Open Questions" section directs readers to
`scratch/notes.md` directly. That is real, load-bearing documentation, not unintegrated content.
**`scratch/` is kept, not removed.** This task now only removes the lint config; Task 4's
README-to-DocBook conversion is where `scratch/`'s ultimate disposition (kept as-is, folded into
the converted README, or promoted into the paper's citable body) gets decided, with that document
actually in hand.

**Files:**
- Delete: `.markdownlint-cli2.jsonc`

**Interfaces:** None -- this task has no consumers and consumes nothing from other tasks.

- [ ] **Step 1: Confirm `.markdownlint-cli2.jsonc` is genuinely unreferenced (re-verify, don't
  trust the design doc's claim blindly)**

```bash
grep -rl "markdownlint" .github/ scripts/*.py 2>/dev/null
```

Expected: no output. If this prints anything, STOP -- do not delete the file, report back with
what references it.

- [ ] **Step 2: Delete it**

```bash
git rm .markdownlint-cli2.jsonc
```

- [ ] **Step 3: Run the full test suite to confirm nothing depended on the removed file**

```bash
cd scripts && python3 -m unittest discover -s tests -p "test_*.py" 2>&1 | tail -5
```

Expected: `Ran 247 tests ... OK (skipped=8)`, unchanged.

- [ ] **Step 4: Commit**

```bash
git add -A .markdownlint-cli2.jsonc
git commit -m "chore: remove unreferenced markdownlint config (scratch/ retained -- confirmed actively referenced by the paper's own README, reversing this plan's original assumption)"
```

---

### Task 3: Build `generate_index.py`; generate `docs/index.xml` + `docs/sitemap.xml`; retire the 8 pure-listing README stubs

**Files:**
- Create: `scripts/generate_index.py`
- Create: `scripts/tests/test_generate_index.py`
- Create (generated): `docs/index.xml`, `docs/index.meta.xml`, `docs/index.html`,
  `docs/sitemap.xml`
- Delete: `docs/index.md`
- Delete: `docs/cross-cutting/README.md`, `docs/wip/README.md`, `docs/papers/README.md`,
  `docs/papers/ai_and_ip/README.md`, `docs/court-record/README.md`,
  `docs/court-record/theory/README.md`, `docs/court-record/matters/README.md`,
  `docs/proposals/README.md`

**Interfaces:**
- Consumes: `write_metadata(meta_path, title, subject=None)`, `build_html(xml_path, out_path)`,
  `validate(xml_path)` (all existing, `scripts/convert_to_docbook.py`, Task 1's new location).
- Produces: `generate_index()` (walks the corpus, returns the list of `(relative_path, title,
  category)` tuples used to build both `index.xml` and `sitemap.xml` -- no other task consumes
  this directly, but Task 4's README conversions may link to `docs/index.html#<anchor>` using the
  same category-anchor naming this task establishes).

This was prototyped and verified against the real corpus before being written into this plan: the
walk-and-title-extraction logic below returns exactly 120 shell articles, correctly grouped, with
real titles read from each document's own `<info><title>` (confirmed live, not assumed).

- [ ] **Step 1: Write `scripts/generate_index.py`**

```python
"""Generates docs/index.xml (the corpus's own DocBook table of contents,
per explicit direction: a scholarship document itself, not a lesser
navigational artifact) and docs/sitemap.xml, by walking the corpus's real
built state -- titles read from each document's own <info><title>, never
duplicated or hand-maintained. Regenerate whenever the corpus changes:
    python3 scripts/generate_index.py
"""
import subprocess
import sys
from pathlib import Path
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape as xml_escape

sys.path.insert(0, str(Path(__file__).resolve().parent))
from convert_to_docbook import (  # noqa: E402
    REPO_ROOT, DB_NS, write_metadata, build_html, validate,
)

DOCS_DIR = REPO_ROOT / "docs"
SITE_URL = "https://metavacua.github.io/legal-theory"

CATEGORY_ORDER = [
    ("court-record/matters", "Matters"),
    ("court-record/theory", "Theory"),
    ("cross-cutting", "Cross-Cutting"),
    ("proposals", "Proposals"),
    ("wip", "Works in Progress"),
    ("papers", "Papers"),
    ("bibliography", "Bibliography"),
]


def _shell_articles(docs_dir):
    for xml_path in sorted(Path(docs_dir).rglob("*.xml")):
        s = str(xml_path)
        if "/scratch/" in s or "/bibliography/entries/" in s or "/scripts/" in s:
            continue
        if xml_path.name.endswith(".meta.xml") or xml_path.name == "index.xml":
            continue
        root_tag = subprocess.run(
            ["xmllint", "--xpath", "name(/*)", str(xml_path)],
            capture_output=True, text=True,
        ).stdout.strip()
        if root_tag == "article":
            yield xml_path


def _title_for(xml_path):
    resolved = subprocess.run(
        ["xmllint", "--xinclude", str(xml_path)],
        capture_output=True, text=True, check=True,
    ).stdout
    root = ET.fromstring(resolved)
    info = root.find(f"{{{DB_NS}}}info")
    title_el = info.find(f"{{{DB_NS}}}title") if info is not None else None
    return title_el.text if title_el is not None and title_el.text else xml_path.stem


def _category_for(rel_path):
    rel_str = str(rel_path)
    for prefix, label in CATEGORY_ORDER:
        if rel_str.startswith(prefix + "/") or rel_str == prefix:
            return label
    return "Other"


def collect_documents():
    """[(relative_html_path, title, category), ...] sorted by category
    order then title -- the single source of truth both index.xml and
    sitemap.xml are built from."""
    docs = []
    for xml_path in _shell_articles(DOCS_DIR):
        rel = xml_path.relative_to(DOCS_DIR)
        title = _title_for(xml_path)
        category = _category_for(rel)
        html_rel = rel.with_suffix(".html")
        docs.append((html_rel, title, category))
    order_index = {label: i for i, (_, label) in enumerate(CATEGORY_ORDER)}
    docs.sort(key=lambda d: (order_index.get(d[2], len(CATEGORY_ORDER)), d[1]))
    return docs


def _anchor(label):
    return label.lower().replace(" ", "-")


def build_index_xml(docs, xml_path):
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<article xmlns="http://docbook.org/ns/docbook" '
        'xmlns:xi="http://www.w3.org/2001/XInclude" version="5.2" '
        'xml:id="index" xml:lang="en">',
        '  <xi:include href="index.meta.xml" />',
        '  <para>Generated index of every document in this corpus. '
        'Regenerated by <code>scripts/generate_index.py</code> -- do not hand-edit.</para>',
    ]
    by_category = {}
    for html_rel, title, category in docs:
        by_category.setdefault(category, []).append((html_rel, title))
    for _, label in CATEGORY_ORDER:
        entries = by_category.get(label)
        if not entries:
            continue
        lines.append(f'  <section xml:id="{_anchor(label)}">')
        lines.append(f'    <title>{xml_escape(label)}</title>')
        lines.append('    <itemizedlist>')
        for html_rel, title in entries:
            lines.append(
                f'      <listitem><para>'
                f'<link xlink:href="{xml_escape(str(html_rel))}" '
                f'xmlns:xlink="http://www.w3.org/1999/xlink">'
                f'{xml_escape(title)}</link></para></listitem>'
            )
        lines.append('    </itemizedlist>')
        lines.append('  </section>')
    lines.append('</article>')
    xml_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_sitemap(docs, sitemap_path):
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    lines.append(f"  <url><loc>{SITE_URL}/index.html</loc></url>")
    for html_rel, _, _ in docs:
        lines.append(f"  <url><loc>{SITE_URL}/{html_rel}</loc></url>")
    lines.append('</urlset>')
    sitemap_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    docs = collect_documents()
    meta_path = DOCS_DIR / "index.meta.xml"
    write_metadata(meta_path, "legal-theory — Index", subject="index")
    xml_path = DOCS_DIR / "index.xml"
    build_index_xml(docs, xml_path)
    errors = validate(xml_path)
    if errors:
        print(f"VALIDATION FAILED:\n" + "\n".join(errors), file=sys.stderr)
        return 1
    build_html(xml_path, DOCS_DIR / "index.html")
    build_sitemap(docs, DOCS_DIR / "sitemap.xml")
    print(f"Generated docs/index.xml + docs/index.html + docs/sitemap.xml "
          f"({len(docs)} documents indexed).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Write `scripts/tests/test_generate_index.py`**

```python
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class TestCollectDocuments(unittest.TestCase):
    def test_finds_the_real_corpus_documents(self):
        from generate_index import collect_documents
        docs = collect_documents()
        # 120 confirmed by direct count against the real corpus before
        # this plan was written; re-verify here so a future corpus
        # change that silently breaks the walk is caught, not silently
        # accepted.
        self.assertEqual(len(docs), 120)

    def test_every_document_has_a_real_title_not_a_filename_fallback(self):
        from generate_index import collect_documents
        docs = collect_documents()
        # A title equal to its own filename stem is the fallback path
        # (info/title missing or empty) -- every real corpus document
        # has a real <info><title>, so zero fallbacks is the expected,
        # verified state, not an assumption.
        stem_matches = [
            (html_rel, title) for html_rel, title, _ in docs
            if title == html_rel.stem
        ]
        self.assertEqual(stem_matches, [])

    def test_categorizes_into_the_expected_seven_buckets(self):
        from generate_index import collect_documents, CATEGORY_ORDER
        docs = collect_documents()
        categories_found = {category for _, _, category in docs}
        expected_labels = {label for _, label in CATEGORY_ORDER}
        self.assertTrue(categories_found.issubset(expected_labels))
        self.assertNotIn("Other", categories_found)


class TestBuildIndexXml(unittest.TestCase):
    def test_generated_xml_is_well_formed_and_has_one_section_per_category(self):
        import tempfile
        from generate_index import build_index_xml
        docs = [
            (Path("cross-cutting/a.html"), "Doc A", "Cross-Cutting"),
            (Path("cross-cutting/b.html"), "Doc B", "Cross-Cutting"),
            (Path("wip/c.html"), "Doc C", "Works in Progress"),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            xml_path = Path(tmp) / "index.xml"
            build_index_xml(docs, xml_path)
            content = xml_path.read_text(encoding="utf-8")
            self.assertIn('xml:id="cross-cutting"', content)
            self.assertIn('xml:id="works-in-progress"', content)
            self.assertEqual(content.count("<itemizedlist>"), 2)
            self.assertEqual(content.count("<listitem>"), 3)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run the new tests to verify they pass against the real corpus**

```bash
cd scripts && python3 -m unittest tests.test_generate_index -v
```

Expected: `Ran 4 tests ... OK`. If `test_finds_the_real_corpus_documents` or
`test_every_document_has_a_real_title_not_a_filename_fallback` fails, the corpus has changed since
this plan was written -- investigate the actual count/titles before assuming the test is wrong.

- [ ] **Step 4: Run the generator for real**

```bash
cd /home/metavacua/legal-theory/.worktrees/claude/llm-database-theory-codification-sdd-1785019559
python3 scripts/generate_index.py
```

Expected: `Generated docs/index.xml + docs/index.html + docs/sitemap.xml (120 documents indexed).`

- [ ] **Step 5: Verify the generated index against the real DocBook 5.2 grammar (already done
  inside `main()`, confirm independently too)**

```bash
schema=$(python3 -c 'import sys; sys.path.insert(0,"scripts"); from convert_to_docbook import fetch_docbook_schema; print(fetch_docbook_schema())')
jing -c "$schema" docs/index.xml
echo "exit: $?"
```

Expected: `exit: 0`.

- [ ] **Step 6: Spot-check the generated HTML renders correctly**

```bash
grep -c "class=\"itemizedlist\"" docs/index.html
grep -o "cross-cutting/patron-as-client.html" docs/index.html
```

Expected: a nonzero itemizedlist count (one per category with documents), and the second command
finds the real link to a known document, confirming the generated links resolve correctly.

- [ ] **Step 7: Delete `docs/index.md` and the 8 pure-listing README stubs**

```bash
git rm docs/index.md docs/cross-cutting/README.md docs/wip/README.md docs/papers/README.md \
       docs/papers/ai_and_ip/README.md docs/court-record/README.md \
       docs/court-record/theory/README.md docs/court-record/matters/README.md \
       docs/proposals/README.md
```

- [ ] **Step 8: Run the full test suite**

```bash
cd scripts && python3 -m unittest discover -s tests -p "test_*.py" 2>&1 | tail -5
```

Expected: `Ran 251 tests ... OK (skipped=8)` (247 + 4 new).

- [ ] **Step 9: Commit**

```bash
cd /home/metavacua/legal-theory/.worktrees/claude/llm-database-theory-codification-sdd-1785019559
git add -A scripts docs
git commit -m "feat: generate docs/index.xml + sitemap.xml from real corpus state; retire 8 redundant README listing-stubs"
```

---

### Task 4: Convert the 7 genuinely-authored README files to DocBook

**`scratch/` disposition (decided here, not in Task 2):** the paper's `README.md` currently
references `scratch/formulas.md` and `scratch/notes.md` in its "Source Files" table and its "Open
Questions" section (which points readers to `scratch/notes.md` for the full list, giving only a
truncated summary inline). When converting this file, decide explicitly whether to keep those
references as-is, fold the referenced content directly into the converted README, or promote it
into the paper's own citable body -- and reflect that decision in the converted `README.xml`. Do
not silently drop the references without one of these three resolutions.

**Files:**
- Create + Delete (replace): `docs/audits/README.md` → `docs/audits/README.xml` +
  `README.meta.xml`
- Create + Delete (replace, ×5): each matter's `docs/court-record/matters/<matter>/README.md` →
  `README.xml` + `README.meta.xml`
- Create + Delete (replace): `docs/papers/ai_and_ip/llm-database-theory/README.md` → `README.xml`
  + `README.meta.xml`

**Interfaces:**
- Consumes: `write_metadata()`, `build_html()`, `validate()` (existing). Links to
  `docs/index.html#<anchor>` use the exact anchor naming Task 3 established
  (`_anchor(label)` = lowercased, spaces→hyphens: `#matters`, `#theory`, `#cross-cutting`,
  `#proposals`, `#works-in-progress`, `#papers`, `#bibliography`).

- [ ] **Step 1: For each of the 7 files, snapshot the pre-conversion rendered text**

Same content-preservation technique already proven in the citation-standardization pilot and the
`html5.xsl` retirement. Example for one file (repeat for all 7):

```bash
mkdir -p /tmp/readme-conversion-sample
# Snapshot the raw markdown text itself as the "before" reference -- there
# is no built HTML for these .md files today (they were Jekyll-rendered,
# not built by this project's own pipeline), so the source text itself is
# the correctness baseline, not a rendered comparison.
cp docs/audits/README.md /tmp/readme-conversion-sample/audits-README-before.md
cp docs/court-record/matters/cooperative-investment-law/README.md /tmp/readme-conversion-sample/cooperative-investment-law-README-before.md
cp docs/court-record/matters/copyright-ip-authorship/README.md /tmp/readme-conversion-sample/copyright-ip-authorship-README-before.md
cp docs/court-record/matters/google-platform-misclassification/README.md /tmp/readme-conversion-sample/google-platform-misclassification-README-before.md
cp docs/court-record/matters/platform-tos-constitutional-limits/README.md /tmp/readme-conversion-sample/platform-tos-constitutional-limits-README-before.md
cp docs/court-record/matters/sex-work-consent-bodily-autonomy/README.md /tmp/readme-conversion-sample/sex-work-consent-bodily-autonomy-README-before.md
cp docs/papers/ai_and_ip/llm-database-theory/README.md /tmp/readme-conversion-sample/paper-README-before.md
```

- [ ] **Step 2: Convert each file's content to DocBook, preserving every section, heading, and
  cross-reference**

For each file: write `README.xml` using the same section/para/itemizedlist/link vocabulary already
established throughout this corpus (see `docs/court-record/matters/cooperative-investment-law/README.md`'s
current structure for the shape: `## Jurisdiction and Venue`, `## Parties`, `## Statement of
Facts`, `## Causes of Action`, `## Prayer for Relief` -- each becomes a `<section><title>`). Every
relative link to another file (`findings.html`, `evidence/`, other matters' theory documents)
is preserved with the same relative path, converted to `<link xlink:href="...">`. Every link that
previously pointed at `../../../index.md#<anchor>` is repointed to
`../../../index.html#<anchor>` (Task 3's real, working anchors). Write the matching `README.meta.xml`
via `write_metadata(meta_path, title)` for each (do not hand-write metadata -- reuse the existing
function so every document's `<info>` block is produced identically, matching every other document
in the corpus).

This step has no single canonical code block -- it is 7 independent content-preserving format
conversions, each requiring the implementer to read the source file in full and represent every
section faithfully. There is no shortcut around reading each file; do not skip any section.

- [ ] **Step 3: Validate each converted file against the real DocBook 5.2 grammar**

```bash
schema=$(python3 -c 'import sys; sys.path.insert(0,"scripts"); from convert_to_docbook import fetch_docbook_schema; print(fetch_docbook_schema())')
for f in docs/audits/README.xml \
         docs/court-record/matters/cooperative-investment-law/README.xml \
         docs/court-record/matters/copyright-ip-authorship/README.xml \
         docs/court-record/matters/google-platform-misclassification/README.xml \
         docs/court-record/matters/platform-tos-constitutional-limits/README.xml \
         docs/court-record/matters/sex-work-consent-bodily-autonomy/README.xml \
         docs/papers/ai_and_ip/llm-database-theory/README.xml \
         ; do
  echo "=== $f ==="
  jing -c "$schema" "$f"
  echo "exit: $?"
done
```

Expected: `exit: 0` for all 7.

- [ ] **Step 4: Build each to HTML and manually diff against the pre-conversion snapshot**

```bash
python3 -c "
import sys
sys.path.insert(0, 'scripts')
from convert_to_docbook import build_html
pairs = [
    ('docs/audits/README.xml', 'docs/audits/README.html'),
    ('docs/court-record/matters/cooperative-investment-law/README.xml', 'docs/court-record/matters/cooperative-investment-law/README.html'),
    ('docs/court-record/matters/copyright-ip-authorship/README.xml', 'docs/court-record/matters/copyright-ip-authorship/README.html'),
    ('docs/court-record/matters/google-platform-misclassification/README.xml', 'docs/court-record/matters/google-platform-misclassification/README.html'),
    ('docs/court-record/matters/platform-tos-constitutional-limits/README.xml', 'docs/court-record/matters/platform-tos-constitutional-limits/README.html'),
    ('docs/court-record/matters/sex-work-consent-bodily-autonomy/README.xml', 'docs/court-record/matters/sex-work-consent-bodily-autonomy/README.html'),
    ('docs/papers/ai_and_ip/llm-database-theory/README.xml', 'docs/papers/ai_and_ip/llm-database-theory/README.html'),
]
for xml_path, html_path in pairs:
    build_html(xml_path, html_path)
    print(f'built {html_path}')
"
```

Then, for each pair, read both the `/tmp/readme-conversion-sample/*-before.md` snapshot and the
newly built `.html` side by side and confirm every heading and every substantive sentence from the
original survives in the converted version. This is manual review, not an automated diff -- the
format change (Markdown headings to DocBook sections) means a naive text-diff produces mostly
noise. Report explicitly, per file, that this review was done and what (if anything) changed in
wording versus structure only.

- [ ] **Step 5: Delete the 7 original `.md` files**

```bash
git rm docs/audits/README.md \
       docs/court-record/matters/cooperative-investment-law/README.md \
       docs/court-record/matters/copyright-ip-authorship/README.md \
       docs/court-record/matters/google-platform-misclassification/README.md \
       docs/court-record/matters/platform-tos-constitutional-limits/README.md \
       docs/court-record/matters/sex-work-consent-bodily-autonomy/README.md \
       docs/papers/ai_and_ip/llm-database-theory/README.md
```

- [ ] **Step 6: Regenerate `docs/index.xml` (its links to these READMEs need to point at the new
  `.html` files, which they already do automatically -- `generate_index.py` reads real corpus
  state, so simply re-running it picks up the change; but the 7 README files themselves are not
  indexed by `generate_index.py`, since it only walks `_shell_articles()` root-`article` documents
  -- confirm this explicitly rather than assuming)**

```bash
python3 scripts/generate_index.py
git diff --stat docs/index.xml docs/index.html docs/sitemap.xml
```

Expected: little or no diff (the READMEs were never part of `collect_documents()`'s output in the
first place, since they're not top-level shell articles under the categories it walks -- confirm
this is genuinely unchanged, not silently broken).

- [ ] **Step 7: Run the full test suite**

```bash
cd scripts && python3 -m unittest discover -s tests -p "test_*.py" 2>&1 | tail -5
```

Expected: `Ran 251 tests ... OK (skipped=8)`, unchanged from Task 3.

- [ ] **Step 8: Commit**

```bash
cd /home/metavacua/legal-theory/.worktrees/claude/llm-database-theory-codification-sdd-1785019559
git add -A docs
git commit -m "feat: convert the 7 genuinely-authored README.md files to DocBook 5.2, matching every other corpus document"
```

---

### Task 5: Drop Jekyll; deploy `docs/` as static HTML

**Files:**
- Modify: `.github/workflows/deploy-pages.yml`
- Delete: `docs/_config.yml`

**Interfaces:** None -- this task only touches deployment configuration, consumed by nothing else
in this repo.

- [ ] **Step 1: Confirm the precondition -- zero Markdown files remain under `docs/`, outside two
  known, deliberate exceptions**

**Corrected during execution, replacing the original check outright:** the original form of this
check (`find docs -iname "*.md" -not -path "*/scratch/*"`) found 27 files and correctly blocked --
but 22 of those are `docs/superpowers/*.md`, which are *known* to still exist at this point in the
plan: Task 6 (the final task) removes them, and it must run last so its own brief can still be
extracted from this plan file while every earlier task runs. That is not a gap, it is this plan's
own documented ordering constraint (see the Global Constraints section). The real gap the original
check also caught was genuine: 5 orphaned pre-DocBook-conversion `.md` originals in `docs/proposals/`
(each with a real, current `.xml`/`.html` counterpart already in place, confirmed unreferenced from
anywhere live) that no earlier task in this plan ever addressed. The corrected check excludes the
known, deliberate `docs/superpowers/` case and separately handles the real gap:

```bash
find docs -iname "*.md" -not -path "*/scratch/*" -not -path "*/superpowers/*"
```

Expected: exactly 5 files, all under `docs/proposals/` (orphaned pre-conversion originals with real
`.xml`/`.html` counterparts already built). If this finds anything else, STOP and investigate
before proceeding -- only these 5, specifically, are a known, already-diagnosed gap.

- [ ] **Step 1b: Verify each of the 5 files has a real, current `.xml`+`.html` counterpart and is
  unreferenced from anywhere live, then remove them**

```bash
for f in \
  docs/proposals/legislative/california/state-legislature/blueprint-for-innovation-ip-in-cooperative-securities \
  docs/proposals/legislative/california/state-legislature/hybrid-cooperative-ipo-framework \
  docs/proposals/legislative/california/state-legislature/legalizing-sexual-service-contracts \
  docs/proposals/legislative/california/state-legislature/regulating-sexual-services-states-role \
  docs/proposals/executive/agencies/california/secretary-of-state/improving-ai-accountability-petition-arguments \
  ; do
  echo "=== $f ==="
  ls "${f}.xml" "${f}.html"
done
grep -rln "blueprint-for-innovation-ip-in-cooperative-securities\.md\|hybrid-cooperative-ipo-framework\.md\|legalizing-sexual-service-contracts\.md\|regulating-sexual-services-states-role\.md\|improving-ai-accountability-petition-arguments\.md" docs/ --include="*.xml" --include="*.html" 2>/dev/null
```

Expected: all 5 `.xml`+`.html` pairs exist, and the `grep` finds no live references to any `.md`
filename. If either check fails for any file, STOP -- do not delete that file.

```bash
git rm docs/proposals/legislative/california/state-legislature/blueprint-for-innovation-ip-in-cooperative-securities.md \
       docs/proposals/legislative/california/state-legislature/hybrid-cooperative-ipo-framework.md \
       docs/proposals/legislative/california/state-legislature/legalizing-sexual-service-contracts.md \
       docs/proposals/legislative/california/state-legislature/regulating-sexual-services-states-role.md \
       docs/proposals/executive/agencies/california/secretary-of-state/improving-ai-accountability-petition-arguments.md
```

- [ ] **Step 1c: Re-run the corrected precondition check**

```bash
find docs -iname "*.md" -not -path "*/scratch/*" -not -path "*/superpowers/*"
```

Expected: no output.

- [ ] **Step 1d: Commit the proposals cleanup separately from the Jekyll changes below**

```bash
cd scripts && python3 -m unittest discover -s tests -p "test_*.py" 2>&1 | tail -5
cd ..
git commit -m "chore: remove 5 orphaned pre-DocBook-conversion .md originals from docs/proposals/ (real .xml/.html counterparts already exist, confirmed unreferenced)"
```

Expected: `Ran 252 tests ... OK (skipped=8)`, unchanged (these were dead files, nothing depended on
them).

- [ ] **Step 2: Update `deploy-pages.yml`**

Change the `build` job from:

```yaml
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Build with Jekyll
        uses: actions/jekyll-build-pages@v1
        with:
          source: docs
          destination: _site

      - uses: actions/upload-pages-artifact@v3
        with:
          path: _site
```

to:

```yaml
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/upload-pages-artifact@v3
        with:
          path: docs
```

- [ ] **Step 3: Delete `docs/_config.yml`**

```bash
git rm docs/_config.yml
```

- [ ] **Step 4: Validate the workflow YAML is syntactically well-formed**

```bash
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/deploy-pages.yml'))" && echo "valid YAML"
```

Expected: `valid YAML`. (This does not verify the workflow *runs* correctly -- that requires an
actual push, explicitly out of scope for this plan per the Global Constraints. It verifies the
file is at least syntactically correct before it's committed.)

- [ ] **Step 5: Confirm nothing else references `docs/_config.yml` or Jekyll**

```bash
grep -rln "_config.yml\|jekyll\|Jekyll" .github/workflows/ docs/*.xml docs/*.html 2>/dev/null
```

Expected: no output.

- [ ] **Step 6: Commit**

```bash
git add -A .github/workflows/deploy-pages.yml docs/_config.yml
git commit -m "feat: deploy docs/ as static HTML, dropping Jekyll entirely (nothing under docs/ is Markdown anymore)"
```

---

### Task 6: Remove `docs/superpowers/` from the tracked working tree (final task)

**Files:**
- Delete: all 20 pre-existing files under `docs/superpowers/plans/` and `docs/superpowers/specs/`,
  plus this plan (`2026-07-28-site-standardization-and-agent-artifact-removal-plan.md`) and its
  design doc (`2026-07-28-site-standardization-and-agent-artifact-removal-design.md`) -- 22 files
  total.

**Interfaces:** None. This is the final task; nothing depends on it.

- [ ] **Step 1: Confirm every other task in this plan is complete and committed**

```bash
git log --oneline | head -10
cd scripts && python3 -m unittest discover -s tests -p "test_*.py" 2>&1 | tail -5
```

Expected: the 5 preceding tasks' commits are visible in the log, and the full suite passes
(`Ran 251 tests ... OK (skipped=8)`). Do not proceed if either check fails.

- [ ] **Step 2: Remove the entire directory**

```bash
cd /home/metavacua/legal-theory/.worktrees/claude/llm-database-theory-codification-sdd-1785019559
git rm -r docs/superpowers/
```

- [ ] **Step 3: Confirm nothing under `docs/` still references a `docs/superpowers/` path**

```bash
grep -rln "superpowers/" docs/*.xml docs/*.html docs/*/*.xml docs/*/*.html 2>/dev/null
```

Expected: no output (the reorganization-plan self-links were part of the now-deleted `docs/index.md`;
`docs/index.xml`, generated in Task 3, never referenced `docs/superpowers/` in the first place,
since the generator only walks real corpus documents).

- [ ] **Step 4: Run the full test suite one final time**

```bash
cd scripts && python3 -m unittest discover -s tests -p "test_*.py" 2>&1 | tail -5
```

Expected: `Ran 251 tests ... OK (skipped=8)` -- confirms removing the planning-document archive
broke nothing (it shouldn't have; nothing in `scripts/` reads from `docs/superpowers/`).

- [ ] **Step 5: Commit**

```bash
git add -A docs/superpowers
git commit -m "chore: remove docs/superpowers/ from the tracked working tree -- git history is the durable provenance record, a parallel hand-curated archive only duplicates it (imperfectly, as this session's own two correction passes already demonstrated)"
```

---

## Self-Review

**Spec coverage:** Design §2.1 (generated `docs/index.xml`) → Task 3. §2.2 (README split: 8
retired, 7 converted) → Tasks 3 and 4. §2.3 (drop Jekyll, sitemap) → Tasks 3 (sitemap generation
folded into the same generator) and 5 (Jekyll removal). §2.4 (relocate `docs/scripts/`) → Task 1.
§2.5 (remove `docs/superpowers/`, including this plan/design as its own final step) → Task 6.
§2.6 (`scratch/` disposition -- corrected during execution to "kept," see Task 2) → Tasks 2/4. §2.7 (dead lint config) → Task 2. §4's
explicit out-of-scope items (root README.md/LICENSE, draft-consolidation clusters, the mojibake
bug, eyecite wiring, citation Phase 2) are correctly not touched by any task.

**Placeholder scan:** No TBD/TODO. Task 4's README conversions are the one place this plan
explicitly documents that it cannot pre-write the exact converted content (7 independent
prose-preserving format conversions) -- this is stated directly as a real constraint on what a
plan can specify in advance, not a placeholder; the verification steps (grammar validation,
content-preservation review) are concrete and complete.

**Type consistency:** `collect_documents()` (Task 3) returns `[(Path, str, str), ...]` --
consumed identically by `build_index_xml()` and `build_sitemap()` in the same file, and by
`test_generate_index.py`'s tests using the same tuple shape. `_anchor(label)` (Task 3) is the same
function Task 4's README conversions reference by name for their own link-repointing (its output
shape -- lowercase, hyphenated -- is documented in Task 4's Interfaces block so a fresh
implementer doesn't need to re-derive it). `write_metadata()`, `build_html()`, `validate()`
(existing, `scripts/convert_to_docbook.py`) are called with their existing, unchanged signatures
throughout Tasks 3-4 -- confirmed by reading the actual current function definitions before this
plan was written, not assumed from memory.

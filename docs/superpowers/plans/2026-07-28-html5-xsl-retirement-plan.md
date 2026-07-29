# Retire html5.xsl Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Delete `docs/xsl/html5.xsl` and render every corpus document (120 real DocBook articles,
confirmed by direct count) via the stock `xhtml5/docbook.xsl` stylesheet from the apt-packaged
`docbook-xsl-ns`, with no project-owned XSLT and no customization layer.

**Architecture:** `docs/scripts/convert_to_docbook.py`'s `build_html()` is the single function every
HTML-producing code path in this repo calls (`atomize_existing_document.py`,
`build_bibliography.py`, the test suite, and `.github/workflows/build-corpus.yml`'s own inline
`xsltproc` call, which mirrors it). Repointing its one stylesheet-path constant, then rebuilding and
committing all 120 documents' `.html` through it, is sufficient to retire `html5.xsl` corpus-wide.

**Tech Stack:** Python 3 stdlib `xml.etree.ElementTree` (existing convention), `xsltproc`
(existing), the official `docbook-xsl-ns` apt package (`xhtml5/docbook.xsl` variant), `unittest`.

## Global Constraints

- `docs/xsl/html5.xsl` is deleted entirely by this plan -- not modified, not kept as a dormant
  customization layer. No project-owned XSLT file exists after this plan lands.
- No theming, finding-badges, DC meta tags, JSON-LD, or site-nav bar is reimplemented as a
  replacement. The stock `docbook-xsl-ns` output is the accepted end state (per
  `docs/superpowers/specs/2026-07-28-html5-xsl-retirement-design.md` §3).
- `xhtml5/docbook.xsl` is used, not the sibling `html/docbook.xsl` variant -- confirmed by direct
  testing that `html/docbook.xsl` hardcodes `ISO-8859-1` output encoding (a literal `<xsl:output>`
  declaration, not a parameter), which mis-encodes this corpus's real UTF-8 non-ASCII content;
  `xhtml5/docbook.xsl` hardcodes `UTF-8` instead and needs no override.
- All 120 documents are rebuilt in one pass (not staged/piloted) -- this is a verified stock
  stylesheet, not new custom code needing incremental de-risking (explicit 2026-07-27 direction).
- The paper (`docs/papers/ai_and_ip/llm-database-theory`) already renders through this same unified
  `build_html()`/CI pipeline (confirmed via its own Makefile comment) -- no special-casing needed.
  Its separate `latex.xsl`/PDF build path is untouched by this plan.
- `jing` schema validation is unaffected by this plan -- it operates on the XML/schema layer, never
  invokes `html5.xsl` or its replacement, and needs no change.

---

## File Structure

- Modify `docs/scripts/convert_to_docbook.py:266` -- `HTML5_XSL_PATH` repointed to the system
  `docbook-xsl-ns` stylesheet path.
- Modify `docs/scripts/tests/test_convert_to_docbook.py` -- add one new test proving the new
  stylesheet renders `<bibliography>`/`<biblioref>` (which `html5.xsl` never could).
- Delete `docs/xsl/html5.xsl`.
- Modify `.github/workflows/build-corpus.yml` -- add `docbook-xsl-ns` to the apt-get install line;
  repoint its own inline `xsltproc` invocation.
- Modify (rebuild, not hand-edit) 120 corpus `.html` files -- every document `build_html()` applies
  to, per the same `find`-based selection `build-corpus.yml` already uses.

---

### Task 1: Repoint `build_html()` to `docbook-xsl-ns`, delete `html5.xsl`, update CI

**Files:**
- Modify: `docs/scripts/convert_to_docbook.py:266` (`HTML5_XSL_PATH`)
- Modify: `docs/scripts/tests/test_convert_to_docbook.py` (new test in `TestValidateAndBuild`,
  after `test_build_html_produces_output_with_title` at line 406)
- Delete: `docs/xsl/html5.xsl`
- Modify: `.github/workflows/build-corpus.yml:29` (apt-get install line),
  `.github/workflows/build-corpus.yml:47` (xsltproc invocation)

**Interfaces:**
- Consumes: `build_html(xml_path, out_path)` (existing, `docs/scripts/convert_to_docbook.py:338`) --
  signature and callers (`atomize_existing_document.py:152`, `build_bibliography.py:692`,
  `convert_to_docbook.py:490`) are unchanged by this task; only the module-level constant it reads
  changes.
- Produces: `HTML5_XSL_PATH` now points at
  `/usr/share/xml/docbook/stylesheet/docbook-xsl-ns/xhtml5/docbook.xsl` -- consumed by Task 2's
  corpus-wide rebuild, which calls `build_html()` unmodified.

- [ ] **Step 1: Write a failing test proving the current stylesheet cannot render bibliography structure**

Add to `docs/scripts/tests/test_convert_to_docbook.py`, in `TestValidateAndBuild`, directly after
`test_build_html_produces_output_with_title` (after line 406):

```python
    def test_build_html_renders_bibliography_as_a_real_hyperlink(self):
        # html5.xsl has no template for <bibliography>/<biblioentry>/<biblioref>
        # at all (confirmed by direct grep of the file) -- this proves the
        # switch to docbook-xsl-ns's xhtml5 stylesheet actually happened, not
        # just that HTML5_XSL_PATH points somewhere that still runs.
        from convert_to_docbook import build_html
        xml_path = self.fixtures / "biblio-check.xml"
        xml_path.write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<article xmlns="http://docbook.org/ns/docbook" version="5.2" '
            'xml:id="biblio-check" xml:lang="en">\n'
            '  <info><title>Biblio Check</title></info>\n'
            '  <para>See <biblioref linkend="smith2020"/> for details.</para>\n'
            '  <bibliography>\n'
            '    <biblioentry xml:id="smith2020" role="secondary">\n'
            '      <title>Some Real Paper</title>\n'
            '      <biblioid class="uri">https://example.com/a</biblioid>\n'
            '    </biblioentry>\n'
            '  </bibliography>\n'
            '</article>\n',
            encoding="utf-8",
        )
        self.addCleanup(xml_path.unlink)
        html_path = self.fixtures / "biblio-check.html"
        build_html(xml_path, html_path)
        self.addCleanup(html_path.unlink)
        content = html_path.read_text(encoding="utf-8")
        # A real, resolved hyperlink from the citation site to the entry --
        # html5.xsl's default-template fallback would emit the raw text with
        # no <a href> and no "biblioentry" class at all.
        self.assertIn('href="#smith2020"', content)
        self.assertIn('class="biblioentry"', content)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd docs/scripts && python3 -m unittest tests.test_convert_to_docbook.TestValidateAndBuild.test_build_html_renders_bibliography_as_a_real_hyperlink -v`

Expected: FAIL -- `content` contains neither `href="#smith2020"` nor `class="biblioentry"` (`html5.xsl`
has no template for these elements; XSLT's built-in default template falls through to raw text with
no href or class).

- [ ] **Step 3: Repoint `HTML5_XSL_PATH` to the real stylesheet**

In `docs/scripts/convert_to_docbook.py`, change line 266 from:

```python
HTML5_XSL_PATH = REPO_ROOT / "docs" / "xsl" / "html5.xsl"
```

to:

```python
HTML5_XSL_PATH = Path("/usr/share/xml/docbook/stylesheet/docbook-xsl-ns/xhtml5/docbook.xsl")
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `cd docs/scripts && python3 -m unittest tests.test_convert_to_docbook.TestValidateAndBuild.test_build_html_renders_bibliography_as_a_real_hyperlink -v`

Expected: PASS.

- [ ] **Step 5: Run the full test suite to confirm nothing else broke**

Run: `cd docs/scripts && python3 -m unittest discover -s tests -p "test_*.py"`

Expected: all tests pass (8 skipped, eyecite, as always under bare `python3`). In particular,
`test_build_html_produces_output_with_title` (line 399, unmodified) must still pass -- the new
stylesheet still renders the document's `<title>` text into the output, just via different markup.

- [ ] **Step 6: Delete `docs/xsl/html5.xsl`**

```bash
git rm docs/xsl/html5.xsl
```

- [ ] **Step 7: Run the full test suite again, confirming the deletion broke nothing**

Run: `cd docs/scripts && python3 -m unittest discover -s tests -p "test_*.py"`

Expected: identical results to Step 5 -- nothing in the test suite references the deleted file path
directly (only `HTML5_XSL_PATH`, already repointed in Step 3).

- [ ] **Step 8: Update the CI workflow to install `docbook-xsl-ns` and use the new path**

In `.github/workflows/build-corpus.yml`, change line 29 from:

```yaml
        run: sudo apt-get update && sudo apt-get install -y libxml2-utils xsltproc jing
```

to:

```yaml
        run: sudo apt-get update && sudo apt-get install -y libxml2-utils xsltproc jing docbook-xsl-ns
```

Change line 47 from:

```yaml
            xsltproc --xinclude docs/xsl/html5.xsl "$xml" > "${xml%.xml}.html"
```

to:

```yaml
            xsltproc --xinclude /usr/share/xml/docbook/stylesheet/docbook-xsl-ns/xhtml5/docbook.xsl "$xml" > "${xml%.xml}.html"
```

- [ ] **Step 9: Commit**

```bash
git add docs/scripts/convert_to_docbook.py docs/scripts/tests/test_convert_to_docbook.py \
        .github/workflows/build-corpus.yml
git commit -m "feat: retire html5.xsl, render the corpus via docbook-xsl-ns's xhtml5 stylesheet directly"
```

---

### Task 2: Corpus-wide HTML rebuild and verification

**Files:**
- Modify (rebuild): every `.html` file corresponding to a real DocBook article under `docs/`
  (excluding `docs/scripts/**` and any `**/scratch/**` path), matching the exact selection
  `.github/workflows/build-corpus.yml`'s own `find` command already uses.

**Interfaces:**
- Consumes: `build_html(xml_path, out_path)` (Task 1, now pointed at the real stylesheet),
  `measure_citation_conformance.py`'s `_shell_articles()`/`corpus_wide_report()`/
  `measure_citation_conformance()` (existing, used here only for verification, not selection).

- [ ] **Step 1: Snapshot a content-preservation sample before rebuilding**

Reuses the same before/after rendered-text-diff technique already proven in the citation-
standardization pilot (Task 6 of that plan). Sample 4 documents spanning different structural
shapes -- a short cross-cutting document, the citation pilot's own document (real bibliography
structure), a `docs/wip/` draft, and a proposals document. The "before" snapshot is simply the
currently-committed `.html` on disk, read directly -- no need to re-render it, since it already
reflects the pre-rebuild state this step is meant to snapshot:

```bash
mkdir -p /tmp/html5-retirement-sample
for doc in \
  docs/cross-cutting/patron-as-client.xml \
  docs/court-record/theory/federal-constitutional/extensions/llms-as-categorical-systems.xml \
  docs/wip/systemic-misclassification-draft.xml \
  docs/proposals/legislative/california/state-legislature/hybrid-cooperative-ipo-framework.xml \
  ; do
  name=$(basename "$doc" .xml)
  python3 -c "
import re
html = open('${doc%.xml}.html', encoding='utf-8').read()
text = re.sub(r'<[^>]+>', ' ', html)
text = ' '.join(text.split())
open('/tmp/html5-retirement-sample/${name}-before.txt', 'w').write(text)
print('${name}:', len(text), 'chars')
"
done
```

Expected: four lines printed, one per document, each with a nonzero char count.

- [ ] **Step 2: Rebuild all 120 corpus documents' HTML**

```bash
python3 -c "
import subprocess
import sys
from pathlib import Path
sys.path.insert(0, 'docs/scripts')
from convert_to_docbook import build_html

paths = []
for xml_path in sorted(Path('docs').rglob('*.xml')):
    s = str(xml_path)
    if '/scratch/' in s or s.startswith('docs/scripts/'):
        continue
    root = subprocess.run(
        ['xmllint', '--xpath', 'name(/*)', str(xml_path)],
        capture_output=True, text=True,
    ).stdout.strip()
    if root != 'article':
        continue
    paths.append(xml_path)

print(f'{len(paths)} shell articles found')
built, failed = 0, []
for xml_path in paths:
    html_path = xml_path.with_suffix('.html')
    try:
        build_html(xml_path, html_path)
        built += 1
    except subprocess.CalledProcessError as e:
        failed.append((str(xml_path), e.stderr))

print(f'built: {built}, failed: {len(failed)}')
for f, err in failed:
    print(f'FAILED: {f}')
    print(err)
"
```

Expected: `120 shell articles found`, `built: 120, failed: 0`. If any document fails, stop and
diagnose that document specifically (via `superpowers:systematic-debugging` if the cause isn't
immediately obvious) before proceeding -- do not skip failures.

- [ ] **Step 3: Diff the sampled documents' rendered text against the pre-rebuild snapshot**

```bash
for doc in \
  docs/cross-cutting/patron-as-client.xml \
  docs/court-record/theory/federal-constitutional/extensions/llms-as-categorical-systems.xml \
  docs/wip/systemic-misclassification-draft.xml \
  docs/proposals/legislative/california/state-legislature/hybrid-cooperative-ipo-framework.xml \
  ; do
  name=$(basename "$doc" .xml)
  python3 -c "
import re
before = open('/tmp/html5-retirement-sample/${name}-before.txt', encoding='utf-8').read()
after_html = open('${doc%.xml}.html', encoding='utf-8').read()
after = re.sub(r'<[^>]+>', ' ', after_html)
after = ' '.join(after.split())
before_words = set(before.split())
after_words = set(after.split())
print('${name}: before', len(before), 'chars, after', len(after), 'chars')
print('  words only in before:', len(before_words - after_words))
print('  words only in after:', len(after_words - before_words))
"
done
```

Expected: character counts are comparable (not a drastic drop). Review the word-diff output
directly for each document -- some difference is expected (the old finding-badges/DC-meta/nav text
disappears, the new stylesheet's own boilerplate appears), but no body prose should be missing.
This is manual review, not an automated pass/fail assertion, matching the same judgment call the
citation pilot's own content-preservation step already used.

- [ ] **Step 4: Re-run the full test suite**

Run: `cd docs/scripts && python3 -m unittest discover -s tests -p "test_*.py"`

Expected: all tests pass (8 skipped). This corpus-wide rebuild must not regress anything the test
suite already covers.

- [ ] **Step 5: Re-run the corpus-wide citation conformance measurement as a sanity check**

```bash
python3 docs/scripts/measure_citation_conformance.py
```

Expected: identical numbers to the pre-rebuild baseline (`5400/87 nonstandard, 79 standard, 78
resolved/22 unresolved, 95 numbered docs/6039 plausible`) -- this tool measures the XML layer, which
this plan does not touch, so its output must be unchanged. A difference here means something
touched the XML unexpectedly and needs investigation before proceeding.

- [ ] **Step 6: Confirm `jing` validation is unaffected, spot-check one document**

```bash
schema=$(python3 -c 'import sys; sys.path.insert(0,"docs/scripts"); from convert_to_docbook import fetch_docbook_schema; print(fetch_docbook_schema())')
jing -c "$schema" docs/court-record/theory/federal-constitutional/extensions/llms-as-categorical-systems.xml
echo "exit: $?"
```

Expected: `exit: 0` -- confirms this plan's changes to the HTML rendering layer had no effect on
XML schema validity, as the design predicted.

- [ ] **Step 7: Commit the corpus-wide rebuild**

```bash
git add -A docs
git status --short | grep -v '^ M.*\.html$' | grep -v '^$'
```

Expected: the second command prints nothing -- confirms every staged change is a modified `.html`
file (no unexpected `.xml`/`.py`/other file caught up in the `git add -A docs`). If anything else
appears, investigate before committing.

```bash
git commit -m "chore: rebuild all 120 corpus documents' HTML via docbook-xsl-ns (retires html5.xsl output)"
```

---

## Self-Review

**Spec coverage:** Design §2 (architecture: repoint `build_html()`, delete `html5.xsl`, update CI)
→ Task 1. Design §2 (rebuild + commit all 120 documents in one pass) → Task 2. Design §3 (nothing
reimplemented/preserved) → no task adds any customization layer; Task 1's Global Constraints state
this explicitly. Design §4 (verification: schema unaffected, test suite updated, content-
preservation check, citation-conformance re-run) → Task 2 Steps 3-6 cover all four directly. Design
§5 out-of-scope items (mojibake bug, paper's LaTeX path, future customization layer, citation Phase
2) → none of them are touched by any task here.

**Placeholder scan:** No TBD/TODO; every step has complete, concrete code or an exact command.

**Type consistency:** `build_html(xml_path, out_path)`'s signature is unchanged throughout --
Task 1 only changes the module-level `HTML5_XSL_PATH` constant it reads internally, confirmed by
re-reading `docs/scripts/convert_to_docbook.py:338-343` directly (the function body performs no
other stylesheet-path lookup). Task 2 calls `build_html()` with the same two-positional-argument
shape used everywhere else in the codebase (`atomize_existing_document.py:152`,
`build_bibliography.py:692`). No new function or class is introduced by this plan -- it is a path
change, a deletion, a CI update, and a mechanical corpus-wide rebuild, not new library code.

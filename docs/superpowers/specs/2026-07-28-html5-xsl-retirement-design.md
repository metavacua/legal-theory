# Retire `html5.xsl`: Render the Corpus via `docbook-xsl-ns` Directly

## 1. Motivation

`docs/xsl/html5.xsl` is a hand-rolled, project-owned XSLT stylesheet that transforms every DocBook
5.2 document in this corpus (119 real documents under `court-record`/`cross-cutting`/`proposals`/
`wip`, plus the `llm-database-theory` paper) into the `.html` files committed to the repo and served
by GitHub Pages. It is non-standard: no other tool understands it, its behavior is defined entirely
by its own 319 lines, and it duplicates work the real, industry-standard DocBook XSL stylesheets
(`docbook-xsl-ns`, apt-packaged) already do correctly.

This was previously misjudged as an acceptable, permanent split: the citation-standardization
project (2026-07-26) verified `docbook-xsl-ns` renders this corpus's new `<bibliography>`/
`<biblioentry>`/`<biblioref>` structure correctly, then left `html5.xsl` — which cannot render that
structure at all — in place, reasoning that avoiding a second hand-rolled implementation of the same
feature was itself the standardization-respecting choice. That reasoning inverted an explicit
directive: "standardization takes precedence" means non-standard tooling gets replaced, not
protected from having to change. That misjudgment is corrected (2026-07-28) in the citation plan and
ledger directly; this design is the actual follow-through.

Confirmed directly (2026-07-27/28), not assumed:
- `docbook-xsl-ns`'s `xhtml5/docbook.xsl` variant renders `<bibliography>`/`<biblioentry>` correctly
  out of the box, and outputs native UTF-8 (`<xsl:output method="xml" encoding="UTF-8" />` — a
  hardcoded declaration, not a parameter to override). The corpus contains real non-ASCII characters
  (confirmed during the citation pilot), so this matters: the sibling `html/docbook.xsl` variant
  hardcodes `ISO-8859-1` instead and would mis-encode them.
- `docs/scripts/convert_to_docbook.py`'s `build_html(xml_path, out_path)` is the single, real
  function every HTML-producing code path in this repo uses (`atomize_existing_document.py`,
  `build_bibliography.py`, the test suite) — not duplicated logic. `.github/workflows/build-
  corpus.yml`'s CI step calls the same underlying `xsltproc --xinclude <stylesheet> <xml>` shape
  directly in its own shell loop.
- The paper (`docs/papers/ai_and_ip/llm-database-theory`) already renders its HTML through this same
  unified pipeline (confirmed via its own Makefile comment: "Validation and HTML5 generation are NOT
  paper-specific... single uniform pipeline in .github/workflows/build-corpus.yml"). Its separate
  `latex.xsl`/`Makefile` path (LaTeX/PDF generation) is untouched by this design — genuinely
  independent output, not HTML.

## 2. Architecture

Every document in the corpus renders via the stock `xhtml5/docbook.xsl` stylesheet, from the
`docbook-xsl-ns` apt package, invoked directly with no customization layer and no project-owned
XSLT file of any kind. `docs/xsl/html5.xsl` is deleted.

Concretely:
- `docs/scripts/convert_to_docbook.py`: `HTML5_XSL_PATH` changes from
  `REPO_ROOT / "docs" / "xsl" / "html5.xsl"` to the system path
  `/usr/share/xml/docbook/stylesheet/docbook-xsl-ns/xhtml5/docbook.xsl`. `build_html()`'s own logic
  (`subprocess.run(["xsltproc", "--xinclude", str(HTML5_XSL_PATH), str(xml_path)], ...)`) is
  otherwise unchanged — same invocation shape, different stylesheet path.
- `.github/workflows/build-corpus.yml`: add `docbook-xsl-ns` to the existing
  `apt-get install -y libxml2-utils xsltproc jing` line; its own inline `xsltproc --xinclude
  docs/xsl/html5.xsl` invocation gets the same new system path.
- `docs/xsl/html5.xsl` is deleted from the repo (git history preserves it; nothing references it
  once the above two changes land).
- All 119 corpus documents' `.html` (+ the paper's, per-fragment) are rebuilt and committed in one
  pass via the updated pipeline — a single mechanical corpus-wide rebuild, not staged, since this is
  a verified stock stylesheet, not new custom code needing incremental de-risking.

## 3. What does not survive, and why that's correct

`html5.xsl` rendered several things the stock stylesheet does not:

- Dublin Core `<meta name="DC.*">` tags in `<head>`.
- Schema.org JSON-LD injection (from a `<bibliomisc role="schema-org-jsonld">` element).
- The finding-badge color-coding system (`section[data-condition="confirmed"|...]` borders/badges)
  — a domain-specific convention for this legal-theory corpus, not a DocBook concept.
- Custom typography/theming (fonts, colors, layout width).
- The `nav.site-nav` bar linking back to the corpus index.

None of this is standard DocBook output, and none of it is preserved or reimplemented as a
customization layer in this design. Per explicit direction (2026-07-27): "if we really need to
recover or save any of the non-standard custom stuff then we can sequester it into a file" is a
conditional for a future, separately-scoped, explicitly-decided addition — not a default this design
carries forward. The stock stylesheet's own generic output (a plain, readable, valid XHTML5 page
per document) is the accepted result.

`docs/index.md` (the Jekyll-based corpus index page) does not reference any `html5.xsl`-specific
class or markup — confirmed by direct search — so it is unaffected by this change.

## 4. Verification

- **Schema layer unaffected.** This design changes only the XML→HTML rendering step; `jing`
  validation against the real, fetched DocBook 5.2 grammar does not go through `html5.xsl` at all
  and needs no change.
- **Full test suite.** Several existing tests assert specific `html5.xsl`-shaped output (finding-
  badge markup, DC meta tags, nav bar) — e.g. in `test_convert_to_docbook.py`,
  `test_atomize_existing_document.py`. These must be updated to assert against the new stock output
  shape, not merely have their now-failing assertions deleted; each updated test still needs to
  verify something real about the new output (e.g., that `<biblioentry>` renders, that body prose
  survives), not become a no-op.
- **Content-preservation check.** Reusing the same technique already proven in the citation-
  standardization pilot (Task 6): render a sample of documents before/after, strip tags, diff the
  remaining text, and manually review any words present on only one side for genuine loss vs.
  expected reformatting (footnote markers, headings, removed nav/badge text).
- **Corpus-wide `measure_citation_conformance.py` re-run** as an additional sanity check that
  citation resolution (`<biblioref>`/`<citation>` counts) is unaffected by the rendering-pipeline
  change — it measures the XML, not the HTML, so this is confirmation, not a new dependency.

## 5. Explicit scope

**In scope:**
- Deleting `docs/xsl/html5.xsl` and repointing `build_html()`/CI to `docbook-xsl-ns`'s
  `xhtml5/docbook.xsl`.
- Rebuilding and committing all 119 corpus documents' `.html` (+ the paper's) via the new pipeline.
- Updating every existing test whose assertions depend on `html5.xsl`'s specific output shape.

**Explicitly out of scope, not precluded:**
- Any future customization layer restoring theming/finding-badges/DC-meta/JSON-LD as an explicit,
  separately-scoped addition on top of `docbook-xsl-ns` (per "sequester it into a file, if we really
  need it" — a conditional future decision, not part of this design).
- The pre-existing mojibake bug in one bibliography entry's title (`ð¤` instead of the intended 🤗
  emoji) — a source-data encoding defect from an earlier, unrelated conversion step, unaffected by
  which stylesheet renders it.
- The paper's LaTeX/PDF build path (`latex.xsl`) — genuinely separate output, not HTML, not touched.
- Any change to the citation-standardization Phase 2 work (bulk conversion of the remaining Category
  A/flat-entry documents) — this design is a prerequisite for that work rendering correctly on the
  live site, not a replacement for it.

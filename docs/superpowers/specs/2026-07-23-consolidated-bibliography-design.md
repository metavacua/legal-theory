# Consolidated References & Bibliography: Design (superseded)

**Fully superseded 2026-07-26 by
`docs/superpowers/specs/2026-07-26-citation-standardization-design.md`.**

This design proposed generating one separate, consolidated `docs/bibliography/references.xml`
document by extracting and re-classifying the corpus's informal
`<section xml:id="works-cited"><orderedlist><listitem>` citation convention — reusing that same
non-standard convention for the generated output's own body too ("the exact markup pattern every
existing works-cited section already uses... zero XSL or schema changes needed"). That approach
builds standardization tooling *around* a non-standard convention instead of converting it, and is
not the current design.

The current design converts every citation to a real, `xml:id`-tagged DocBook
`<biblioentry>`/`<bibliomixed>` at its own source document (not a separately-generated,
separately-scanned side document), reused via `<xi:include>` for both per-document and repo-wide
bibliographies. See the 2026-07-26 design doc for the actual architecture, and
`docs/superpowers/plans/2026-07-26-citation-standardization-phase1.md` for its implementation plan.

**What still exists from this superseded design:** `docs/scripts/build_bibliography.py` and
`docs/scripts/measure_citation_conformance.py`'s `extract_all_raw_entries()`/
`corpus_wide_report()` (which reuses `build_bibliography.py`'s extraction) are real, currently-used
code built under this design. They are not yet retired; retiring them once every citation is
converted to a real `<biblioentry>` at the source is Phase 2 scope for the citation-standardization
project, tracked in `.superpowers/sdd/progress.md`.

# Consolidated References & Bibliography Implementation Plan (superseded)

**Fully superseded 2026-07-26.** This plan (already executed; it produced the current
`docs/scripts/build_bibliography.py`) built an extraction/classification/emission pipeline around
the corpus's informal `works-cited`/`<listitem>` convention as a permanent, repeatedly-rescanned
input, and reused that same non-standard shape for its own generated output. That approach is not
the current design — see `docs/superpowers/specs/2026-07-23-consolidated-bibliography-design.md`
(also superseded, pointing to the current design) and
`docs/superpowers/specs/2026-07-26-citation-standardization-design.md` (current).

The corrected direction converts every one of the corpus's ~5,482 works-cited entries to a real,
`xml:id`-tagged DocBook `<biblioentry>` at its own source document, retiring the informal
convention entirely rather than building tooling that adapts to it. `build_bibliography.py` itself
is still real, current code (read it directly for its actual behavior, not this plan, which may
have drifted from the final implementation); retiring it once every citation is converted at the
source is Phase 2 scope for the citation-standardization project.

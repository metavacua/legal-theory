# DocBook-Native Corpus Standardization — Design

## Status

Supersedes the `<info>`-metadata design in `docs/superpowers/plans/2026-07-25-external-metadata-ontology-standardization.md` Tasks 1–4 (already partially implemented and committed on this branch — see "Relationship to Already-Committed Work" below). The ontology-layer design in that plan's Tasks 5–11 is retained, adapted to read from native DocBook elements instead of `dc:*` extension elements where a native equivalent now exists.

## Problem

The corpus (119+ documents, `docs/`) declares `version="5.2"` on every `<article>`, but has never been validated against the actual DocBook 5.2 grammar. `docs/schema/docbook-corpus.rnc`, the only schema ever run against it, was introduced narrowly on 2026-07-01 for one paper's `finding-section`/`condition` constraint, then repurposed corpus-wide on 2026-07-20 as a pure filesystem move — not a deliberate corpus-wide design (confirmed via `git log`, see Evidence below). Its own header has claimed since day one that "full grammar validation" happens separately via `xmllint --relaxng`; that step has never actually run.

This session (an in-progress subagent-driven-development pass building the DCTERMS-metadata plan referenced above) surfaced, and verified directly against the real OASIS DocBook 5.2 schema, three independent, corpus-wide structural defects:

1. **`<title>` is placed as a sibling of `<info>`, not inside it.** DocBook 5.2 requires `<title>` as a required child of `<info>`. Every one of the 118+ corpus documents (produced by `docs/scripts/convert_to_docbook.py` / `atomize_existing_document.py`, predating this plan) uses the sibling shape. Verified: a minimal document reproducing this exact shape fails (`element "info" incomplete; missing required element "title"` + `element "title" not allowed here`); moving `<title>` inside `<info>` and nothing else, it passes.
2. **`docs/common/shared-metadata.xml`'s `<shared>` wrapper element is not valid DocBook.** `<info>`'s content model is a flat, repeatable choice of specific named elements (`author`, `authorgroup`, `publisher`, `legalnotice`, `pubdate`, `biblioid`, `subjectset`, ... "or an element from another namespace") — it has no wrapper concept. Verified directly: `jing` against the real schema rejects `<shared>` at every occurrence with `element "shared" not allowed anywhere`.
3. **`dc:*` (DCTERMS) elements do not satisfy DocBook's own structural requirements**, even though they are tolerated as foreign-namespace extension content. Verified: a document using only `dc:title`/`dc:date` inside `<info>` still fails with `missing required element "title"` — DocBook wants its own native `<title>`, and does not treat `dc:title` as satisfying that requirement.

Full corpus sweep against the official DocBook 5.2 RNG (fetched from OASIS, not the close-but-non-identical `docbook5-xml` 5.0 Debian package — both were checked and agree on every finding used here): **0 of 118 corpus articles pass**, but the failures trace almost entirely to defect #1 and #2, which are structural and shared by every document — not 118 independent bugs.

## Evidence

All claims below were independently verified by direct command execution during this session, not assumed from documentation:

- `git log --diff-filter=A -- '*custom.rnc'` → `8495556` ("add RELAX NG compact schema and DocBook build Makefile"), commit message: *"Constrains finding-section attributes... Defers full grammar validation to DocBook 5.2 RNG via xmllint"* — paper-scoped from inception, and its own stated companion step was never built.
- `git show 1774860 --stat` → `docs/papers/.../schema/custom.rnc → docs/schema/docbook-corpus.rnc`, 0 content changes — a rename, not a redesign, on 2026-07-20.
- `git log -1 --format=%B 9962df4` → `build-corpus.yml` created same day, repurposing the paper's schema corpus-wide "to catch schema regressions."
- `jing`'s installed wrapper (`/usr/bin/jing`) hard-codes `-Dorg.apache.xerces.xni.parser.XMLParserConfiguration=org.apache.xerces.parsers.XIncludeParserConfiguration` — `jing` on this system resolves XInclude unconditionally, confirmed by both reading the wrapper script and a minimal schema probe (`xpointer-test/` fixtures used throughout this session).
- `jing`'s Xerces-based XInclude processor does **not** support the `xpointer()` scheme at all: `SchemeUnsupported: The XPointer scheme 'xpointer' is not supported` — confirmed directly, ruling out an XPointer-based fix for the `<shared>` wrapper.
- `xmllint --schematron` on this system's libxml2 (2.9.14) fails on even a minimal, valid Schematron file with an internal error — confirmed directly (see the referenced plan's Plan Notes), ruling out Schematron for project-specific policy constraints.
- Official DocBook 5.2 RNG: `https://docs.oasis-open.org/docbook/docbook/v5.2/os/rng/docbookxi.rnc` (fetched and used directly; matches the corpus's declared `version="5.2"` exactly, unlike the Debian `docbook5-xml` package which only ships 5.0). All findings re-verified against this exact file, not just the 5.0 package, before being written into this design.
- Native-element replacements for every `dc:*` field used in the superseded plan were verified individually against the real 5.2 schema: `<title>`, `<author>`/`<authorgroup>`, `<publisher><publishername>`, `<legalnotice>` with an embedded `<link xlink:href="...">`, `<pubdate>`, `<biblioid class="uri">`, `<subjectset><subject><subjectterm xlink:href="...">` — each individually confirmed passing (`jing` exit 0).

## Goals

- Every corpus document validates against the real, unmodified OASIS DocBook 5.2 RELAX NG schema.
- Metadata uses native DocBook elements wherever DocBook has one; DCTERMS (`dc:*`) is used only where no native equivalent exists.
- External-ontology references (SKOS concepts, SPDX license, CiTO citation types) attach to real, existing, walkable elements via `xlink:href`/`xlink:arcrole` — never to a disconnected side file or opaque JSON-LD blob (this principle, established earlier in the superseded plan for Tasks 7–9, is retained and now also applied to `<legalnotice>`/`<subjectset>`).
- Shared boilerplate (author identity, legal notice) is included via plain, standard XInclude only — no XPointer schemes (confirmed unsupported by this pipeline's validator).
- Project-specific policy (which fields must be present) is enforced in Python, not RELAX NG or Schematron — matching the already-proven pattern from the superseded plan's Task 10, and avoiding two independently-confirmed Xerces/libxml2 gaps.

## Non-Goals

- Migrating to Akoma Ntoso/LegalDocML or any non-DocBook base format — out of scope, unchanged from the superseded plan's own Global Constraints.
- Full ORCID adoption — unchanged, still deferred (needs the author's real iD).
- Fixing every possible DocBook 5.2 conformance nuance beyond `<info>`/title placement/shared-metadata (e.g., deep content-model correctness inside `<section>` bodies) — Phase 1 targets what the real schema actually flags across the corpus today; anything the real schema doesn't flag is out of scope here.

## Architecture — Two Phases

**Phase 1 (this design's primary scope): make the corpus genuinely valid DocBook 5.2.** Blocking — nothing in Phase 2 should be built on a structurally-invalid foundation.

**Phase 2 (adapts the superseded plan's Tasks 5–11): the external-ontology layer**, built on top of Phase 1's now-valid native elements — Schema.org JSON-LD, SKOS-linked `<subjectset>`, PROV-O `<othercredit>`, CiTO `xlink:arcrole` on bibliography links, CSL-JSON export. These tasks' *ontology choices* were already independently corrected earlier in this session (native-element attachment, not side files) and do not need to change again — only their *source elements* change, from `dc:*` to the native equivalents below.

## Phase 1 Design

### 1. Metadata field mapping (native-first)

| Concept | Old (superseded) | New (native) | DCTERMS still needed? |
|---|---|---|---|
| Title | `dc:title` | `<title>` (inside `<info>`, required) | No |
| Creator | `dc:creator` | `<author>` or `<authorgroup>` | No |
| Publisher | `dc:publisher` | `<publisher><publishername>` | No |
| Rights (prose) | `dc:rights` | `<legalnotice><para>...</para></legalnotice>` | No |
| License (machine-resolvable) | `dc:license` | Same `<legalnotice>`, an embedded `<link xlink:href="https://spdx.org/licenses/CC-BY-SA-4.0">` inside the prose | No — unified into one element instead of two parallel ones |
| Date | `dc:date` | `<pubdate>` | No |
| Identifier | `dc:identifier` | `<biblioid class="uri">` | No |
| Subject (SKOS concept) | `dc:subject` + `xlink:href` | `<subjectset><subject><subjectterm xlink:href="...skos-concept-uri">...</subjectterm></subject></subjectset>` | No |
| Type (DCMI Type Vocabulary) | `dc:type` | *(no native equivalent)* | **Yes — the one remaining genuine extension, unchanged: `dc:type` fixed to `"Text"`** |

Every row except the last was verified individually against the real DocBook 5.2 RNG (`jing` exit 0) during this session's brainstorming.

### 2. Shared boilerplate — real DocBook elements, plain XInclude

Replace `docs/common/shared-metadata.xml` (root `<shared>`, invalid) with:
- `docs/common/authorgroup.xml` — root `<authorgroup>` (real DocBook element), containing the existing author `<personname>`/`<email>`/`<uri>` content unchanged.
- `docs/common/legalnotice.xml` — root `<legalnotice>` (real DocBook element), containing the copyright/license prose with the embedded SPDX `<link>`.

Each document's `<info>` gets two `xi:include`s (one per file) instead of one combined include. No `xpointer` attribute anywhere (confirmed unsupported by `jing`). The scalar fields that used to live in the combined `shared-metadata.xml` (`dc:creator`, `dc:publisher`, `dc:type`, `dc:language`, `dc:rights`, `dc:license`) are now either native elements written directly by the generator from one canonical source in the generator code (`<publisher>`, `dc:type`) or absorbed into `<legalnotice>`/`<authorgroup>` (rights+license, creator) — no runtime-shared scalar fields remain, so no wrapper is needed for them.

### 3. Generator changes

`docs/scripts/convert_to_docbook.py` and `docs/scripts/atomize_existing_document.py`'s metadata-writing logic (`write_metadata()` and equivalents) change to emit the native shape above instead of the `dc:*`-in-`<info>`-with-sibling-title shape. `derive_date`/`derive_identifier`/`derive_subject`/`derive_subject_concept_id` (already-verified logic from the superseded plan's Tasks 2/9) are retained as-is — only the *element* they populate changes (`<pubdate>` instead of `dc:date`, etc.), not the *derivation* logic.

### 4. Structural validation

Replace `docs/schema/docbook-corpus.rnc` entirely with the official DocBook 5.2 RNG, fetched at build/CI time from `https://docs.oasis-open.org/docbook/docbook/v5.2/os/rng/docbookxi.rnc` (decision: fetch, not vendor — matches this pipeline's existing pattern of installing tools via network access at build time, e.g. `apt-get`, rather than committing binaries/large generated artifacts). `jing -c <fetched-schema> <file>` becomes the sole structural validator, in both `.github/workflows/build-corpus.yml`/`build-papers.yml` and the paper's `Makefile`.

### 5. Project-specific policy validation

A Python module (new or extending `docs/scripts/convert_to_docbook.py`'s existing `validate()`/`validate_finding_sections()` pattern) walks the resolved document tree and asserts this project's own completeness policy — e.g., every document has `<title>`, `<pubdate>`, `<biblioid>`, `dc:type`. This is deliberately **not** attempted via RELAX NG or Schematron: this session confirmed two independent, real limitations in this pipeline's validator (`jing`/Xerces has no Schematron support and no XPointer support), so project-specific assertions follow the already-proven Python pattern rather than risking a third RNG/Schematron surprise.

### 6. Build/transform updates

`docs/xsl/html5.xsl` (and `latex.xsl` where relevant) read the native elements instead of `dc:*`: `db:title` for the HTML `<title>`, `db:pubdate` for `DC.date`, `db:biblioid[@class='uri']` for `DC.identifier`, `db:legalnotice//db:link/@xlink:href` for the license URI in generated Schema.org JSON-LD, `db:subjectset//db:subjectterm` (text and `@xlink:href`) for `DC.subject`/the Schema.org `about`/`DefinedTerm` block.

### 7. Migration mechanics

1. Fix the generator (native shape).
2. Regenerate every corpus document's `.meta.xml`/metadata block through the fixed generator (same backfill-script pattern as the superseded plan's Task 2).
3. Replace `shared-metadata.xml` with `authorgroup.xml`/`legalnotice.xml`; repoint every document's `xi:include`s.
4. Wire in the fetched DocBook 5.2 RNG in CI/Makefile; retire `docs/schema/docbook-corpus.rnc`.
5. Verify: 118/118 (+ the 2 paper articles) pass the real schema.
6. Add the Python policy check, wired into the same validation pipeline.

## Phase 2 (adapted, not redesigned)

The superseded plan's Tasks 5–11 already independently arrived at "attach ontology references to real elements, not side files" for Schema.org (Task 5), SPAR/CiTO (Task 7), PROV-O (Task 8), and SKOS (Task 9) — that principle is retained unchanged. What changes is only the *source* each reads from:
- Schema.org JSON-LD generation reads `db:title`/`db:pubdate`/`db:biblioid`/`db:legalnotice`/`db:subjectset` instead of `dc:title`/`dc:date`/`dc:identifier`/`dc:rights`/`dc:subject`.
- SKOS concept references move from `dc:subject/@xlink:href` to `db:subjectset//db:subjectterm/@xlink:href` — same SKOS scheme (`docs/common/subject-scheme.jsonld`), same concept-id derivation, different attachment point.
- PROV-O's native `<othercredit xlink:arcrole="...">` (already redesigned mid-plan to be native, not a JSON-LD blob) needs no further change — `<othercredit>` was already verified as a real DocBook element choice within `<info>`.
- SPAR/CiTO's `<bibliography>`/`<biblioentry>`/`xlink:arcrole` design (already redesigned mid-plan) needs re-verification against the real 5.2 schema specifically (flagged in the superseded plan as "plausible but not yet verified the way everything else was" — still true; verify before relying on it in Phase 2 planning).
- CSL-JSON export (Task 6) is unaffected — it's derived from citation classification logic, not from `<info>` shape at all.
- Finding-section policy enforcement (Task 10) is unaffected — already Python-based, already independent of the `<info>`/DCTERMS question.
- The `lxml` AST-unification work (Tasks 7/11) is unaffected in its own right, though its `corpus_ast.new_article_root()` helper's `<info>` construction responsibilities shift to match the native shape above.

## Relationship to Already-Committed Work

On this branch, a subagent-driven-development pass had already implemented and reviewer-approved the superseded plan's Task 1 (`937d5d9`), Task 2 (`c1117d2`), and Task 3 (`35f78e9` + fix `8712fa6`) before this brainstorming session began. Those commits build the `dc:*`-in-`<info>`-with-sibling-title shape this design retires. This design does not attempt to describe how those commits get superseded (revert vs. new commits on top) — that is an implementation-planning decision for whatever plan executes this design, made with full knowledge that working, tested, reviewed code exists and needs to be replaced, not silently overwritten.

## Testing Strategy

- Every native-element mapping in the table above is already individually verified against the real DocBook 5.2 schema (this session, `jing` exit 0 for each). An implementation plan should reproduce these as fixture-based unit tests (matching the existing `docs/scripts/tests/` `unittest.TestCase` convention) before relying on them at corpus scale.
- Full-corpus regression test: after the generator fix and regeneration, every one of the 118+ documents plus the 2 paper articles must pass `jing -c <fetched-docbook-5.2-rng> <file>` — a corpus-wide sweep, not a sample.
- The Python policy-check module follows Task 10's existing test pattern: fixture-based positive/negative cases (a conformant document, a document missing a required field), run via `unittest`.

## Open Questions for the Implementation Plan

- Exact mechanics for superseding the already-committed Task 1–3 work (see above).
- Whether the SPAR/CiTO bibliography design needs adjustment once verified against the real 5.2 schema (not yet done).
- Whether `docs/xsl/latex.xsl` needs the same native-element updates as `html5.xsl` (not audited in this design; the superseded plan's Task 5 only mentioned `html5.xsl` explicitly).

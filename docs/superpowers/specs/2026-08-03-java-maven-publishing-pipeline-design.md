# Design: Legal-Theory Corpus Publishing Pipeline (Java/Maven · DocBook 5.2 · XHTML5)

**Date:** 2026-08-03
**Branch:** `claude/java-maven-publishing-pipeline`, created from `main`. Shares no history with the abandoned pipeline branches (`claude/llm-database-theory-codification`, its `sdd-…` descendant, `claude/xsltng-saxon-migration`) or the two earlier spec attempts.
**Prior art:** the postmortem (`docs/postmortems/2026-08-02-docbook-pipeline-lessons-learned.md`, on its own branch) fixes the hard constraints; design decisions with documented rationale from the abandoned branches are reused as *decisions* (never as ported code).

## Purpose

This pipeline and its CI are a **search-and-sort instrument**. Their job is to systematically and comprehensively surface every place the standards' requirements and the corpus documents (or the pipeline itself) disagree — classified, machine-readable, and published — so that document defects and pipeline defects can be triaged and fixed. Source documents unavoidably need fixing; the pipeline's primary deliverable is the map of exactly what and where.

**Trajectory (recorded so no future session mistakes the means for the end):** the Markdown corpus is legacy input, not the permanent source of truth. The intended end state is its retirement — documents reconstructed correctly from the start (correct formatting, schema, ontologies, structure), salvaging content from the originals (whose true origin is Google Docs in Drive; verified: the Drive originals carry no more usable typed structure than the committed MD). This pipeline is transitional infrastructure: faithful conversion + exhaustive audit, with the census as the salvage survey. Publication of conforming documents is the incentive gradient; nothing here invests in making legacy conversion "nicer."

## Normative standards and hard requirements

**Standards selection principle:** every accepted representation must be parseable by a grammar in a decidable class, and every normative reference must be pinned and versioned. W3C and ISO standards are preferred; the WHATWG HTML Living Standard is **not a valid authority** for this project (its tag-soup serialization is not context-free; its "parser" is an error-recovery state machine, not a grammar). Output is therefore **XHTML5 — the XML serialization** — never tag-soup HTML5.

| Concern | Normative reference | Enforced by |
|---|---|---|
| XML well-formedness | W3C XML 1.0 | native JDK parser (context-free, fail-fast, XXE-hardened) |
| DocBook vocabulary | OASIS DocBook 5.2 (`docbookxi.rnc`, checksum-pinned fetch) | jing (RELAX NG, ISO 19757-2) |
| XHTML5 vocabulary | HTML Review Draft 2020-01, endorsed W3C Recommendation 2021-01-28 (frozen snapshot; W3C HTML 5.2 was formally *retired* 2021-01-28 and is not citable) | jing + pinned validator.nu RELAX NG schema set (see Dependencies) |
| Project policy (metadata, title presence) | ISO Schematron (19757-3); non-empty title cites W3C ACT rule 2779a5 | SchXslt2 → XSLT 3.0 → Saxon |
| Transformation | W3C XSLT 3.0 | Saxon-HE — the **only** XSLT engine, everywhere; the JDK's built-in Xalan (XSLT 1.0 only, verified) is never used for transforms |
| Markdown parsing | CommonMark spec (version pinned at implementation) | commonmark-java |

Further hard requirements:
- The repository **is** the Maven project: one `pom.xml` at root, single module, `docs/` is build input, `target/` is build output.
- **No generated artifact is ever committed.** Pages deploys straight from the build. (Reverses the abandoned branches' committed-HTML + CI-auto-commit design and structurally eliminates its drift-management machinery.)
- **Generated-value discipline: absence → gate; ambiguity → mark; fabrication → never.** No heuristic interpretation of content anywhere.
- No version pinned in this spec is final; every one is re-verified live immediately before being written into `pom.xml`/workflow YAML.

## Architecture

Three transformation pipelines share two endpoints (Markdown source, XHTML5 output), cross-checked by a content-preservation comparison:

```
                 commonmark-java        authored XSLT (Saxon)      xslTNG (Saxon)
 Markdown ──► XHTML5 fragment ──► DocBook 5.2 ──► XHTML5 (XML serialization)
    │           [P1 front]           [P1 back]         [P2 — publishes]
    │               │
    │               └────────────── P3 (direct XHTML5; test scaffolding, never published)
    │                                       │
    └────────── content-preservation oracle ┴── P3 vs P1∘P2 (triangle)
```

Components (each single-purpose, independently testable):
1. `md-to-xhtml` — commonmark-java wrapper emitting strict XHTML5 fragments (`escapeHtml(true)`; default self-closing voids — verified well-formed XML for this corpus: zero named/numeric entities, all-Unicode typography, ampersands escaped by the renderer).
2. `manifest-generator` — the **one impurity quarantine**: a single JGit pass emitting `repo-metadata.xml` (path → earliest-commit author date, biblioid). Hard-fails on shallow clone (`getShallowCommits()` non-empty — a shallow RevWalk otherwise *silently* mis-dates everything to the graft point) and on untracked files. Semantics pinned: earliest commit touching the *current path*, no rename-following (the only JGit-documented-reliable option; also consistent with biblioid) — document identity is **path identity**; a move resets both fields, stated, not hidden.
3. `xhtml-to-docbook` — the authored Saxon XSLT 3.0 stylesheet: a total function over commonmark's finite element vocabulary (one fixed rule per element; heading nesting via `xsl:for-each-group`; heading-level skips close the gap; `hr`/`br` dropped; GFM tables → DocBook HTML-table model). Reads `repo-metadata.xml` via `document()` — the transform is a pure function of (input, manifest).
4. `docbook-render` — xslTNG on Saxon. XML-syntax XHTML5 is xslTNG's verified default (`method="xhtml" html-version="5"`, self-closed voids); resources/css+js staged with output.
5. `validators` — jing (both grammars), SchXslt2/Saxon (policy + the schema set's own `assertions.sch` if SchXslt2-compatible, verified at plan time), vnu (sequenced secondary).
6. `audit-census` — the checks×documents matrix, `census.xml`, and the health page (rendered via Saxon/XSLT; index/sitemap likewise XSLT-first — custom Java only if demonstrated insufficient).

Java application code is confined to the two leaf utilities (1) and (2).

## Per-document stage sequence

```
1. commonmark → XHTML fragment; native JDK XML parse      [gate: well-formedness]
2. authored XSLT (Saxon) → DocBook 5.2
3. jing vs pinned OASIS DocBook 5.2 grammar               [gate: input grammar]
4. Schematron (SchXslt2/Saxon): metadata vs manifest      [gate: policy]
5. xslTNG (Saxon) → XHTML5 (XML serialization)
6. native JDK XML parse of output                          [gate: well-formedness]
7. jing vs pinned XHTML5 RELAX NG schema set              [gate: output grammar — PRIMARY]
8. vnu (XML mode, --xml) — runs ONLY if 6 and 7 pass      [gate: sequenced final check —
                                                            a vnu failure blocks publication and is
                                                            cataloged WITH vnu's message text, forcing
                                                            the why/how to be read; anything it catches
                                                            here passed the primaries, i.e. unknown-issue
                                                            signal by construction]
9. census row assembled (all gate results + audit checks)
```

**Partition:** the build is green when the *pipeline* is proven (fixtures pass all gates, census generated, no pipeline errors). Documents passing all gates are published; failing documents are excluded from the published site and loudly cataloged on the published health page. **Expected initial state: 0/123 documents publishable** (title absence is universal — see Metadata); the initial deployment is the health page itself, reporting the full salvage survey. The published set grows only as source correction/reconstruction produces conforming documents. Honest-empty over fabricated-full.

## Metadata generation

Native DocBook fields only, where a mechanical derivation from *recorded fact* exists. The retired-for-cause rule from the abandoned branches is reused: never duplicate a native DocBook field with a `dc:*` twin (`<title>`→HTML title and `<pubdate>`→`dc.created`/`dc.modified` crosswalks are built into xslTNG, verified in its `head.xsl`; `<biblioid class="uri">` is the native identifier, `"uri"` a literal member of `db.biblio.class.enumeration`).

| Field | Source | Notes |
|---|---|---|
| `pubdate` | manifest: earliest-commit author date | requires full history: CI must set `fetch-depth: 0` (checkout@v6 default is 1, verified); generator hard-fails on shallow/untracked |
| `biblioid class="uri"` | `${CANONICAL_BASE}/blob/main/<repo-relative-path>` | one named constant (repo URL + branch); canonical identity deliberately pins `main` even on feature-branch builds |
| `dc:type` | literal `Text` (DCMI Type Vocabulary) | the sole `dc:*` exception — no native DocBook equivalent exists; admissible in `<info>` per the real grammar (`db.info.extension = db._any`, verified) |
| **title** | **NOT GENERATED.** | see below |

**Title: refusal, formally grounded.** A heading is not a title; deriving a title from any non-title syntax element is undecidable in general (proven for this corpus by a counterexample pair: two h3-first documents with identical structural signatures where the first heading is the title in one and a body heading in the other). Markdown has no title syntax; the Google Docs origin *had* a Title style that the authoring process never used — title absence is a **defect of the source documents**, universal (123/123). The pipeline emits DocBook's grammar-minimum `<title/>` (empty — grammar-valid, verified empirically) and the **non-empty-title policy Schematron rule (citing W3C ACT 2779a5) fails every legacy document at the policy/output gates, loudly.** No heading-derivation, no filename-derivation, no doctoring scripts. Resolution is authoring real titles during source correction/reconstruction — the machine proposes nothing. (Verified: the pinned XHTML5 RELAX NG grammar does *not* constrain title emptiness — `title.inner = (text)` — vnu's equivalent check is Java outside the grammar; hence the project Schematron rule is the enforcement point.)

## Audit framework and census

An *audit check* is a named, versioned, purely structural predicate/extractor over one representation layer, producing per-document findings `(check-id, document, value, provenance)`. The **census** is the corpus-wide matrix (documents × checks): one `census.xml` per build, rendered into the published **health page**.

Tiers — every check declares exactly one; a check may only tighten tier (survey → mark → gate) by explicit spec change:

| Tier | Meaning | Members |
|---|---|---|
| Gate | fails the document (or build, for pipeline-level checks) | well-formedness ×2, both grammars, policy Schematron, vnu (sequenced last), shallow-repo, untracked-file |
| Mark | value emitted with machine-readable provenance | `pubdate` (`generated-from-git-first-commit`), `biblioid` (`generated-from-path`) |
| Survey | census row only | title class, bibliography region, heading structure, works-cited link stats, encoding hygiene |

Initial check set (every row seeded from a verified finding, none invented):
1. **Title class** (survey): Title-element present / H1-first / H2-first / H3-first / headingless — classes only, mechanically decidable; **no severity ranking** (a judgment, not a decidable property). Known: 0 / 98 / 3 / 21 / 1.
2. **Bibliography region** (survey): section titled `Works cited` (exact whole-title match, case-insensitive, against a small configurable label set — `contains()` proven false-positive-prone on this corpus) + entry count. Known: 88/123 present.
3. **Date provenance** (mark+survey): all 123 first-commit dates cluster at the July 2026 import — the *repo import date*, not authorship (Drive original verified created 2025-09-03) — the mark makes this machine-visible; Drive metadata is the future curation source.
4. **Works-cited link statistics** (survey): items with/without a link node (e.g. 7-of-66 garbage entries linkless in the stress document). Survey-only; no construction decision consumes it.
5. **Heading structure** (survey): first-heading level, level-skips, headingless.
6. **Encoding hygiene** (survey; vnu and well-formedness remain the gates): the C1-mojibake class known from corpus history.

## Bibliographic handling (RED now, GREEN later)

The corpus contains **pseudo-bibliographies**: sections labeled `Works cited` whose list items are markup-delineated pseudo-bibliographic entries — none proper DocBook bibliographic elements. Verified at the true origin (Drive): titles were never hyperlinked; the only typed distinction is link-presence; the garbage entries (leaked prompt/file-title fragments) are unlinked *in the origin*.

- **This increment (RED):** container-level discernment only (census check 2). The works-cited region converts as ordinary `section → orderedlist → listitem`. **Zero `biblioentry`/`bibliomixed`/any bibliographic element is constructed from prose, under any method** — no entry inspection, no string decomposition (Operation B, permanently forbidden), no wholesale wrapping. Construction machinery is real and general, not stubbed: it fires only on already-typed bibliographic structure, which this corpus has none of (verified: zero embedded bibliographic markup corpus-wide).
- **Next increment (GREEN):** promotion of discerned regions into proper `<bibliography>` — pinned by a `@Disabled("GREEN target: bibliography promotion — next increment")` JUnit test containing the real promoted-shape assertion, visible as skipped in every test report; paired with an active test asserting the census currently discerns the 88 pseudo-bibliographies. No test asserts "always zero" (that invariant would invite a stub and forbid GREEN).

## Triangle validation

Content-preservation oracle, precisely defined (never structural identity — P3's flat serialization and P2's xslTNG-rich output are deliberately different): extract (a) ordered normalized text-node sequence, (b) link-target set, from each artifact and from the source; compare P3 vs P1∘P2. Since both share the commonmark front end, divergence localizes to the DocBook round-trip (authored XSLT or xslTNG) — the actual risk surface. Report-tier: a comparison step feeding the census, not a per-document publication gate.

## Dependencies (all live-verified this session; re-verify at implementation)

| Dependency | Pin | Notes |
|---|---|---|
| JDK | 25 (LTS) | pre-installed on `ubuntu-latest` (25.0.3); 26 = informational leg only |
| Maven | 3.9.x (3.9.16) | pre-installed on runner; Maven 4 still RC |
| Saxon-HE | 12.10 | 13.0 = informational leg only |
| `org.docbook:docbook-xslTNG` | 2.8.3 (Maven Central) | project moved to Codeberg; GitHub stale at 2.7.1; XML-XHTML5 output is default |
| `org.commonmark:commonmark` | resolve live — agents returned conflicting 0.24.0/0.29.0 | `escapeHtml(true)`; XML-clean voids verified in source |
| `org.relaxng:jing` | 20241231 | + `com.thaiopensource:jing:20091111` as required-agreement matrix leg |
| validator.nu RELAX NG schema set | git tag `26.7.31` or SHA, vendored/sparse-checkout; MIT | **wiring caveat:** modules declare the whattf datatype library — jing needs its implementation on the classpath (plan-time verification; fallback: pin schemas and datatype artifact to matching vintage, or the MIT `unsoup/validator` repackaging) |
| `name.dmaus.schxslt:schxslt2` | 1.11.2 | XSLT 3.0-native Schematron; also candidate runner for the schema set's own `assertions.sch` (compatibility verified at plan time) |
| `nu.validator:validator` (vnu) | plan-time decision: Maven `20.7.2` (frozen, 2020) vs dated-tag jar | sequenced final gate (runs only after primaries pass); XML mode via `--xml` (verified); failures cataloged with message text |
| `org.eclipse.jgit` | 7.7.1.202607240634-r | shallow detection via `getShallowCommits()` (≥6.3); earliest-commit via RevWalk+`ANY_DIFF`+`REVERSE` (documented pattern) |
| `org.codehaus.mojo:xml-maven-plugin` | 1.2.1 (2026-01) | Saxon as TrAX factory for build-bound transforms |
| pandoc | apt-pinned, CI informational leg **only** | not in the product pipeline; not on runner by default (verified: deliberately dropped from ubuntu-24.04 image) |

## CI and deployment

Single net-new workflow (`main` has no `.github/workflows/`): `actions/checkout@v6` (**`fetch-depth: 0` — required**, default is 1), `actions/setup-java@v5` (Temurin), `permissions: contents: read` on validation, `concurrency` by workflow+ref with cancel-in-progress; deploy via `actions/upload-pages-artifact@v4` + `actions/deploy-pages@v4`.

Three matrix tiers:
- **Required-agreement (blocking):** jing `20091111` vs `org.relaxng:jing:20241231` — RELAX NG is unchanged since ~2008; disagreement is a defect signal.
- **Informational (non-blocking):** JDK 26; Saxon 13.0 (gated on xslTNG's documented support to avoid a permanently-red lamp).
- **Informational cross-check (non-blocking):** pandoc `-t docbook5` on the same sources, RELAX-NG-validated, content-preservation-compared against P1's DocBook — an independent (non-commonmark) parse catching front-end blind spots the triangle structurally cannot.

**Acceptance criterion:** a PR must show a green GitHub-hosted CI run of the real matrix **and** a real Pages deployment, visually checkable — initially the health page reporting the full survey (expected 0/123 publishable). Local `mvn verify` alone does not satisfy this spec.

## Testing

- **Generator contract tests:** manifest (shallow → hard-fail naming `fetch-depth: 0`; untracked → hard-fail; biblioid = path function; date = fixture-repo truth); title-refusal (the counterexample pair as permanent fixtures — identical handling, no detection; any future "title detection" fails this test).
- **Stage-isolation fixtures:** one per gate, each failing at its stage only — RELAX NG violation → 3; hand-authored DocBook with biblioid/path mismatch → 4 (proves the forward gate is real for future authored documents, where it has non-zero discriminating power — over generated docs it is a regression check, stated as such); C1-mojibake → 8 only (C1 controls are legal XML 1.0 characters — they pass well-formedness and both grammars; this fixture is the concrete proof of why vnu's sequenced gate exists: a known defect class only it catches); clean minimal doc → passes everything including policy (it gets a real authored title, proving the full-pass path exists).
- **Census tests:** with/without `Works cited` fixtures; title-class column per fixture class; corpus numbers (88/123; 0/98/3/21/1) as tracked descriptive baselines, never hardcoded invariants.
- **Triangle test:** ≥1 real corpus document, both paths, content-preservation asserted.
- **RED marker:** the `@Disabled` GREEN-shape test (above).
- First full-corpus run is expected to fail documents genuinely (title policy universally; possibly more at vnu) — that is the instrument working; the criterion is honest cataloging, not a weakened gate.

## File structure

```
pom.xml                                          (root; single module; groupId io.github.metavacua)
docs/                                            (input corpus — unchanged)
src/main/java/io/github/metavacua/.../           (two leaf utilities only)
src/main/resources/xslt/xhtml-to-docbook.xsl     (authored stylesheet)
src/main/resources/xslt/health-page.xsl,…        (census/site rendering)
src/main/resources/schematron/policy.sch         (metadata + non-empty-title rules)
src/main/resources/schema/xhtml5/…               (vendored pinned validator.nu RNC set + LICENSE)
src/test/java/… , src/test/resources/fixtures/…
.github/workflows/build-and-deploy.yml
target/                                          (manifest, DocBook, XHTML5, census.xml, site — never committed)
```

## Explicitly out of scope
- Bibliography promotion (the GREEN increment), and any entry-level citation parsing/semantics (raw-reference-string extraction remains forbidden as a problem statement).
- Corpus reconstruction itself (title authoring, date curation from Drive, content salvage) — this spec builds the instrument that maps it.
- Document atomization (XInclude shell/fragment); MD frontmatter or any new MD authoring conventions (corpus is slated for retirement, not investment).
- Severity ranking of defect classes (not mechanically decidable; not needed for the census to be useful).

## Decision log (alternatives struck, with cause)
- pandoc as the product converter — struck for the all-JVM composition (zero runner installs, one engine); retained solely as an informational CI cross-check.
- Hand-written JVM Markdown→DocBook renderer; heuristic bibliographic classifiers (scored signals, exact-delimiter grammars); GROBID/reference-string parsing; `bibliomixed`/`bibliomisc` wholesale wrapping — each struck as fabrication or wrong-problem.
- Title generation (first-heading and filename variants) — struck: heading ≠ title; undecidable; absence is a source defect to surface, not patch.
- WHATWG living standard / vnu as *primary* output authority — struck for pinned W3C REC + pinned RELAX NG via jing; vnu repositioned as the sequenced *final* gate (runs only after the primaries pass, so every vnu failure is incremental unknown-issue signal, cataloged with its message text).
- `dcterms:*` twin fields — struck (retired-for-cause upstream; native DocBook fields with verified crosswalks instead).
- Baseline/grandfather exemption list — withdrawn as vacuous under in-pipeline generation.
- Committed generated artifacts + CI auto-commit — struck; `target/`-only.

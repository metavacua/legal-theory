# DocBook Corpus Migration Design

**Status:** Approved by user 2026-07-21. Next step: `superpowers:writing-plans` for the conversion tool (Phase 1 of Execution Strategy, below).

## Context

This repository's flagship scholarly paper (`docs/papers/ai_and_ip/llm-database-theory/`) is authored as DocBook 5.2 XML, transformed to HTML5/LaTeX via XSLT 1.0 (`xsltproc`), validated against a custom RELAX NG compact schema (`custom.rnc`). Everything else in `docs/` — 123 documents across 5 matters' evidence corpora, jurisdictional theory, cross-cutting analysis, proposals, and works-in-progress — is plain Markdown, rendered by GitHub Pages' built-in Jekyll build.

Direction confirmed by the user (2026-07-21, during the deployment work that preceded this design): extend DocBook 5.2 XML + XSLT-built HTML5 to the `docs/` corpus generally, using the same `xsltproc` toolchain already proven on the paper — not introducing a heavier Node/Ruby build.

This design covers the full migration — both the 5 `findings.md` stub files and the 70-document evidence corpus (plus theory/cross-cutting/proposals/wip) — as one architecture, per explicit user direction not to split it into a findings.md-only session with the evidence corpus deferred to a separate design.

## Goals

- Every document currently in Markdown under `docs/` becomes DocBook 5.2 XML, rendered to HTML5 via the existing XSLT pipeline, with the Markdown retired (`git rm`) once a document is converted — DocBook becomes canonical for that document, matching how the paper already works.
- `docs/court-record/matters/*/findings.md`, once populated with real FOF/COL content (separate, future content-authoring work — this design only covers the format/tooling), use `custom.rnc`'s existing `finding-section` element (`role="finding"`, `condition`). No other document type uses `finding-section`.
- No cross-link, anchor, or deployed-site regression versus the current all-Markdown state (this session already built and verified the link/anchor-checking scripts this migration reuses).
- Nothing is bulk-converted or bulk-deleted; every document's migration is its own reviewable, revertable commit.

## Non-Goals

- Writing the actual FOF/COL content for `findings.md` (currently `[STUB — to be completed...]`). Out of scope — a separate, future content-authoring effort.
- Tagging evidence documents with `finding-section` semantics. They convert to plain DocBook structure (sections/paragraphs/lists/tables mirroring their existing Markdown headings) — confirmed with the user that `finding-section` is `findings.md`-only, since the evidence corpus has no existing "Finding of Fact N" convention to derive it from.
- Converting `docs/papers/**` — already DocBook; unaffected except for repointing to the shared schema/xsl location (Section 1).
- A JavaScript/Node-based site generator, or replacing Jekyll — Jekyll keeps serving whatever Markdown hasn't been converted yet, indefinitely, alongside XSLT-built HTML5 for whatever has.

## Section 1 — Schema & Tooling Architecture

Promote the paper's schema and transforms out of its single-paper directory to shared, repo-root locations under `docs/`:

- `docs/papers/ai_and_ip/llm-database-theory/schema/custom.rnc` → `docs/schema/docbook-corpus.rnc`
- `docs/papers/ai_and_ip/llm-database-theory/xsl/html5.xsl` → `docs/xsl/html5.xsl`
- `docs/papers/ai_and_ip/llm-database-theory/xsl/latex.xsl` → `docs/xsl/latex.xsl`

Every converted document — evidence, theory, cross-cutting, wip, proposals, findings — references these same three shared files. The paper's own `Makefile` repoints to the new shared paths (one-line change per reference); nothing about the paper's own build behavior changes.

`docs/schema/docbook-corpus.rnc` gains a second top-level pattern, `plain-document`, for ordinary `db:article`/`db:section` content with no `finding-section` requirement — the existing `finding-section` pattern (`xml:id` required, `role="finding"`, `condition` ∈ `confirmed | confirmed-with-caveats | split`) stays exactly as-is and remains exclusive to `findings.md` documents. The schema's `start` pattern is extended so a document's root can satisfy either pattern; which one applies is determined by whether the document contains any `role="finding"` sections, not by file location — this keeps the schema honest (a `findings.md` accidentally missing finding-section markup fails validation loudly, rather than silently passing as "plain").

## Section 2 — Per-Document Conversion Recipe

For each document `foo.md`:

1. **Structural conversion:** `pandoc -f gfm -t docbook5 foo.md -o foo.xml.raw` — maps Markdown structure (headings→sections, paragraphs, lists, emphasis, links, tables) into DocBook XML automatically. Preserves all existing prose verbatim; does not rewrite content.
2. **Shell + metadata:** a post-processing step wraps pandoc's raw output in a proper DocBook 5.2 `<article>` root (`xmlns`, `xmlns:xi`, `xmlns:xlink`, `version="5.2"`, `xml:id` derived from the filename, `xml:lang="en"`), fixes known pandoc DocBook5-output quirks (section nesting depth, `<link>`→`xlink:href` attribute form), and XIncludes a small per-document metadata fragment (Dublin Core title/author/date, Schema.org type, CC BY-SA 4.0 license, Ian D.L.N. McLean as author) — same shape as the paper's `00-metadata.xml`, populated from the `.md`'s first heading and repo-wide constants.
3. **Validate:** `xmllint --noout --xinclude foo.xml` (well-formedness + XInclude resolution) and `jing -c docs/schema/docbook-corpus.rnc foo.xml` (schema conformance — `plain-document` pattern for everything except `findings.md`).
4. **Build:** `xsltproc docs/xsl/html5.xsl foo.xml > foo.html`.
5. **Content-preservation check:** strip markup from both `foo.md` (source) and `foo.html` (output) to plain text and diff. Any paragraph pandoc dropped, garbled, or duplicated is flagged for human review — the tool does not proceed past this step automatically if anything is flagged (see Section 4, Safety Net).
6. **Commit:** on a clean pass, `git rm foo.md`; `git add foo.xml foo.html`; rewrite every inbound cross-link across the corpus pointing at `foo.md` to `foo.html` (extends this session's full-corpus link-checker script into a rewriter); commit as a single, self-contained, revertable change.

## Section 3 — Execution Strategy

`superpowers:writing-plans` requires every task's steps fully spelled out — no "repeat Task N" shortcuts. 123 near-identical hand-written conversion tasks would be impractical to author and a poor fit for the format. Instead:

**The implementation plan (next step, via `writing-plans`) covers building `docs/scripts/convert-to-docbook.sh`** — a tool implementing recipe Steps 1–6 above — as ordinary TDD software work: a test fixture (small sample `.md` exercising headings/lists/links/emphasis), a failing test asserting well-formed + schema-valid + zero-flagged-diff output, then the implementation. This is a normal, boundedly-scoped engineering task with a clear test cycle.

**Converting the corpus is a separate, operational rollout** using that tool once it exists — one invocation per document, each its own reviewable commit — tracked via a progress checklist (not 123 pre-written plan tasks). This rollout is future work, sequenced after the tool is built and reviewed.

**Proposed rollout order** (for when that future work happens):
1. `findings.md` × 5 — smallest, validates `finding-section` end-to-end through the whole pipeline first.
2. Evidence documents, matter-by-matter, smallest matter first: `google-platform-misclassification` (6) → `platform-tos-constitutional-limits` (12) → `copyright-ip-authorship` (13) → `cooperative-investment-law` (19) → `sex-work-consent-bodily-autonomy` (20, includes the corpus's largest document at 18.4k words) — shakes out tool edge cases cheaply before the hardest documents.
3. Theory (22 documents across the branches from Task 1/2's audit) → cross-cutting (8) → wip (8) → proposals (6) — smaller sets, tool well-proven by this point.

**Rollout progress (2026-07-21):** Phase 1 (`findings.md` × 5) complete — all five converted
via `docs/scripts/convert_to_docbook.py`, each independently re-validated against
`docs/schema/docbook-corpus.rnc` post-commit, full-corpus link/anchor sweep clean (176 links,
0 broken), deployed and verified live (200s at
`https://metavacua.github.io/legal-theory/court-record/matters/<matter>/findings.html`).
Content is unchanged from the original `[STUB]` placeholders — this phase converted format
only, per the Non-Goals section above. Commits: `e17293b`, `8bb8f4f`, `f94809c`, `b4133de`,
`89887ea`. Phase 2 (70-document evidence corpus, matter-by-matter) started
2026-07-21: `google-platform-misclassification` (6 evidence documents, smallest matter)
complete — matter now fully converted (findings.md + all evidence). Found and fixed a real
`content_preservation_diff()` bug in the process (commit `3369c2a`): line- and then
block-level diffing both proved unstable across the DocBook round-trip for real prose
(long lines re-wrap at a different column width; adjacent list items regroup into a
different number of blocks) — fixed by comparing at the word level instead
(`difflib.SequenceMatcher` over whitespace-split tokens), immune to both. Also patched 3
of the 6 documents' titles (`google-user-contracts-implicit-employment-obligations.md`,
`google-user-contracts.md`, `google-user-misclassification.md`) to the human-curated
titles from the earlier accessibility-reorg audit, since `extract_title()`'s mechanical
first-heading extraction picked up an internal sub-section heading for each — same known
issue flagged for ~10 files total across the corpus in that audit. All 6 verified: jing
schema-valid, xsltproc build clean, word-level content-preservation diff empty, live on
the deployed site. 4 matters remain in Phase 2 (64 evidence documents).

**Full corpus-wide classification (2026-07-21):** before continuing to the next matter,
ran a dry-run `convert()` across all 106 remaining content documents (not just
`evidence/`) and cross-referenced against `markdownlint` to systematically classify every
markup-quality pattern that has affected or could affect the conversion pipeline — see
**[docs/superpowers/specs/2026-07-21-source-markdown-quality-taxonomy.md](2026-07-21-source-markdown-quality-taxonomy.md)**
for the full writeup (5 classes: A hard-breaks and B table-rendering, both fixed at the
tool level; C malformed-emphasis-adjacency, deliberately left as manual-per-document
review; D poor title extraction, handled manually per the reorg audit; E stray HTML tags,
fixed at the tool level in commit `f67bac7` after crashing on
`petition-corporate-ai-registry-ca-sos.md`). 97/106 documents scanned clean. A repo-scoped
`.markdownlint-cli2.jsonc` now exists (7 rules that correlate with real conversion
problems; every other default rule disabled as pure noise for this corpus's authoring
style) — **linting via that config is a mandatory step** before investigating any new
class this taxonomy doesn't already cover.

**Phase 2 complete (2026-07-21).** Remaining 4 matters converted in sequence, each following
the same process: mandatory scoped lint → dry-run `convert()` → per-file schema/build
verification → known-class cross-check against the taxonomy doc → `docs/index.md` link
rewrite (including draft-lineage cross-reference annotations, never touching links to
not-yet-converted documents) → full corpus link/anchor sweep → commit → push → live
verification.

- `platform-tos-constitutional-limits` (12 docs, commit `612bb4b`) — 1 genuine Class D title
  patch (`vrp-legal-vulnerability.md`), 2 MD041 false positives correctly ruled out.
- `copyright-ip-authorship` (13 docs, commit `409b939`) — 1 genuine Class D title patch
  (`strategic-compliant-ip.md`), 3 MD041 false positives; 1 already-known Class C file
  (`ai-corporate-personhood-and-legal-rights.md`) re-verified against the taxonomy's
  recorded pattern before proceeding.
- `cooperative-investment-law` (19 docs, commit `f53b7b3`) — largest matter; 1 genuine Class D
  patch (`from-intangible-to-investment-ip-securitization.md`), 3 MD041 false positives (the
  "Unified Framework" draft-lineage trio all extract identically and correctly); 1 known
  Class C file re-verified; all evidentiary revision files (community-care-cooperatives
  v1/v2, the three "Unified Framework" revisions, from-clay-tablets-to-blockchains
  draft/final, the-membership-security/securitizing-cooperative-membership-voting-rights)
  converted independently with no consolidation, per the still-deferred Task 6 constraint.
- `sex-work-consent-bodily-autonomy` (20 docs, commit `153ec7c`) — final matter; zero MD041
  hits, zero Class D issues; 2 known Class C files re-verified; the corpus's largest document
  (`the-architecture-of-non-consensual-legality.md`, 18.4k words) converted clean; correctly
  left the-nexus-of-consent-and-consideration.md's cross-reference to the still-unconverted
  theory document `california-sex-contracts-and-consent.md` pointing at its `.md` path.

**Result: all 70 evidence documents + 5 `findings.md` across all 5 matters are now DocBook
5.2, validated, built, and live.** Only Phase 3 (theory 22, cross-cutting 8, wip 8,
proposals 6 — 44 documents) remains of the original corpus-migration scope.

## Section 4 — Testing, CI, and Safety Net

- **Tool testing (TDD):** `docs/scripts/convert-to-docbook.sh` ships with a test fixture and a test asserting well-formed + schema-valid + zero-flagged-diff output, written before the implementation, per `superpowers:test-driven-development`.
- **CI generalization:** `.github/workflows/build-papers.yml` currently hardcodes one paper's `Makefile`. Generalizes to a corpus-wide job: `find docs -name '*.xml' -not -name '00-metadata.xml' -not -path '*/scratch/*'`, `xsltproc docs/xsl/html5.xsl` per file, commit outputs — same pattern already proven this session, applied to however much of the corpus has been converted so far. Triggers on push touching `docs/**/*.xml`.
- **Safety net:** the tool refuses to `git rm` a `.md` if its content-preservation diff (Section 2, Step 5) flags anything — surfaces for human review instead of silently proceeding. Every conversion is one commit, so `git revert <sha>` undoes exactly one document if a bad conversion slips through later. Nothing is ever bulk-deleted or bulk-converted.
- **Metadata consistency:** every converted document's XIncluded metadata fragment carries the same Dublin Core / CC BY-SA 4.0 / Ian D.L.N. McLean fields the paper's `00-metadata.xml` already uses, so the corpus's existing licensing footer requirement (this session's own plan, Global Constraints) is satisfied per-document automatically rather than needing separate re-assertion.

## Open Items for the Implementation Plan

These are decisions for `writing-plans` to make concrete, not open architecturally:

- Exact pandoc invocation flags and post-processing script language (likely Python, given the repo has no other scripting language dependency yet and stdlib `xml.etree`/`lxml` suffice for the shell-wrapping and metadata-injection steps).
- Exact diff algorithm and threshold for the content-preservation check (Section 2, Step 5) — e.g. whether whitespace-only differences are ignored, how tables/footnotes are normalized before comparison.
- Whether the corpus-wide CI job (Section 4) replaces `build-papers.yml` outright or the paper keeps a dedicated workflow alongside a new corpus-wide one.

**Plan/spec divergence, noted at final branch review:** Section 1 above described the schema gaining a second, separately-named top-level pattern, `plain-document`, alongside `finding-section`. What shipped instead — already true at this branch's base commit, before any of this branch's own work — is a single relaxed `start` pattern that permits either shape without a separately-named pattern of its own. `start`'s `block-content*` already accepts ordinary article content, and `finding-section` remains its own distinct, stricter pattern used only where `role="finding"` applies. This branch's Fix 1 extended `block-content` (and therefore `start`) to also cover `informaltable` and `programlisting`, pandoc's actual GFM table/code output. This is a reasonable simplification, not a gap: it achieves the same permit-either-shape goal as the originally envisioned `plain-document` pattern without the extra indirection of naming and threading through a second top-level pattern, and it was confirmed intentional during the final branch review rather than left silently unresolved.

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

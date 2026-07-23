# Repository Accessibility & Visibility Reorganization Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the 124 substantial documents in this repository actually discoverable — both in the GitHub-rendered/deployed web view and in the top-level README — by replacing the current directory-only index (which links to dead/empty directories) with a real, file-level, titled index, and by standing up an actual deployed web page.

**Architecture:** No deployed web page currently exists (`repos/metavacua/legal-theory/pages` returns 404, no `.github/workflows`, no `_config.yml`). The plan (a) rewrites `README.md` and `docs/index.md` as content-first navigation with real titles and one-line descriptions, (b) adds minimal GitHub Pages scaffolding (`docs/_config.yml`, a supported theme, `jekyll-relative-links` — bundled by default in the `github-pages` gem — so existing relative `.md` links resolve to `.html` automatically), (c) leaves the repo-settings flip (Settings → Pages → source) and any merge-to-main as an explicit human-confirmed step, and (d) records — without acting on — a set of near-duplicate/draft document clusters for a future consolidation pass.

**Tech Stack:** Plain Markdown, GitHub Pages (Jekyll, `jekyll-relative-links`, a GitHub-supported theme — no Gemfile/local Ruby build required), existing DocBook 5.2 + XSLT 1.0 + `make` pipeline under `papers/ai_and_ip/llm-database-theory/`.

## Global Constraints

- Do not move, rename, or delete any file under `docs/court-record/**` (evidentiary record) without explicit user confirmation — these are court-record artifacts, not ordinary docs.
- Every link added to `README.md` or `docs/index.md` MUST resolve to a real file or a real non-empty directory. No links to empty directories.
- Theme choice for `docs/_config.yml` MUST be one of GitHub Pages' supported themes (https://pages.github.com/themes/) so no custom Ruby build step is required.
- Do not flip the GitHub Pages repository setting or merge to `main` without explicit user confirmation (visible, hard-to-reverse, affects a shared/public system).
- License footer (CC BY-SA 4.0, © Ian D.L.N. McLean) must be preserved verbatim in both README.md and docs/index.md.

---

## Current-state findings (from repository audit, 2026-07-20)

- **124 markdown/XML documents**: 70 evidence docs across 5 matters, 22 theory docs, 8 cross-cutting, 8 wip, 6 proposals, 1 scholarly DocBook paper (2 XML articles).
- **`docs/index.md` links mostly to empty directories.** Of the taxonomy's ~30 theory/proposal leaf directories, only 9 contain files. `california-constitutional/*` (all 4 subcategories), `municipal/*` (both), and most of `proposals/executive/*` and `proposals/legislative/*` are entirely empty — a reader following the index hits a bare GitHub directory listing roughly 70% of the time.
- **No deployed web page exists.** `GET /repos/metavacua/legal-theory/pages` → 404. No `.github/workflows/*`, no `_config.yml`.
- **The flagship scholarly paper (`papers/ai_and_ip/llm-database-theory/`) is invisible from both README.md and docs/index.md.** It has its own polished README, a DocBook 5.2 build (`make html`, `make pdf`), 6 findings of fact, 6 conclusions of law — and zero inbound links from the repository's two navigation entry points.
- **Draft/revision clusters** (files differ but share a title or clear lineage — flagged for a future consolidation pass, not touched by this plan):
  - `cooperative-investment-law/evidence/`: `cooperative-security.md`, `us-ca-coop-securities.md`, `us-ca-coop-securities-v6.md` (same title, 3 revisions); `the-membership-security.md` / `securitizing-cooperative-membership-voting-rights.md` (same title); `from-clay-tablets-to-blockchains-draft.md` / `-final.md`.
  - `sex-work-consent-bodily-autonomy/evidence/`: `the-architecture-of-non-consensual-legality.md` (18.4k words, largest doc in repo) / `legal-actions-without-consent-draft.md` (same title, earlier draft); `the-sovereign-self-bodily-autonomy-kink-sex-work.md` / `kink-sex-work-body-autonomy-research.md` (same title).
  - Cross-location: `sex-work-consent-bodily-autonomy/evidence/the-nexus-of-consent-and-consideration.md` and `theory/california-statutes/existing-law/california-sex-contracts-and-consent.md` share an identical title but differ in length (289 vs 475 lines) — worth a content diff to determine if one supersedes the other.
  - `docs/wip/systemic-misclassification-draft.md` already correctly named as the draft of `google-platform-misclassification/evidence/systemic-misclassification-final.md`.

---

## Task 1: Rewrite `docs/index.md` as a real file-level index

**Files:**
- Modify: `docs/index.md`

**Interfaces:**
- Produces: the canonical navigation page every matter/theory/cross-cutting/proposal/paper link routes through. Task 2 (README) links here for the full listing.

- [x] **Step 1: Extract accurate titles for all 124 documents**

Ran, for every `.md` under `docs/` and `papers/` (excluding `scratch/`):
```bash
find docs papers -name "*.md" -not -path "*/scratch/*" | sort | while read f; do
  grep -m1 -E '^#+ ' "$f" | sed -E 's/^#+\s*//; s/\*\*//g'
done
```
Result saved for reference at `/tmp/.../scratchpad/titles.tsv` (not committed — regenerate if needed).

- [x] **Step 2: Identify and hand-correct titles that are section headers, not document titles**

Files where the first `#`-heading is a sub-section rather than the true title (fixed by using a humanized filename instead):
`google-user-contracts-implicit-employment-obligations.md`, `google-user-contracts.md`, `google-user-misclassification.md`, `vrp-legal-vulnerability.md`, `from-intangible-to-investment-ip-securitization.md`, `strategic-compliant-ip.md`, `knowledge-graph-ca-service-contracts.md`, `ip-contract-knowledge-graph.md`, `patronage-sourced-income.md`, `petition-corporate-ai-registry-ca-sos.md` (also a placeholder template — flag as `[template]`).

- [x] **Step 3: Write the new `docs/index.md`**

Structure (top to bottom): intro + doc-count summary → "Start Here" (flagship paper + matters + theory anchors) → Matters (5, each with description/findings-link/evidence list) → Theory (only the 9 non-empty leaf directories, each listing real files; empty branches collapsed into one "not yet populated" note, no dead links) → Cross-Cutting (8) → Proposals (only the 2 non-empty leaf directories) → Works in Progress (8, explicitly marked draft) → Papers (the DocBook paper, with build instructions link) → duplicate/draft-lineage callout (links to this plan's findings section, doesn't touch the files) → license footer.

Every entry is `[Title](relative/path/to/file.md)` — never a bare directory link — so `jekyll-relative-links` (Task 3) can resolve every link once Pages is live, and GitHub's own markdown renderer resolves them today.

- [x] **Step 4: Verify no dead links**

```bash
grep -oE '\]\([a-zA-Z0-9/_.-]+\.md\)' docs/index.md | sed -E 's/^\]\(//; s/\)$//' | while read p; do
  [ -f "docs/$p" ] || [ -f "$p" ] || echo "DEAD: $p"
done
```
Expected: no output (all links resolve). Run relative to repo root; index links are relative to `docs/`.

- [x] **Step 5: Commit**

```bash
git add docs/index.md
git commit -m "docs: rewrite index as file-level navigation, drop dead directory links"
```

---

## Task 2: Rewrite `README.md` to surface the flagship paper and give real signposting

**Files:**
- Modify: `README.md`

**Interfaces:**
- Consumes: `docs/index.md` (Task 1) as the "full listing" link target.
- Produces: the first thing a visitor (or GitHub search result click-through) sees.

- [x] **Step 1: Add a "Start Here" section above the existing prose** linking to (a) the flagship paper `papers/ai_and_ip/llm-database-theory/README.md`, (b) `docs/index.md` for the full listing, (c) the five matters directly by name.
- [x] **Step 2: Add a one-line document-count summary** ("124 documents: 70 evidentiary research files across 5 active matters, 22 jurisdictional theory files, 8 cross-cutting analyses, 6 legislative/executive proposals, 1 formal scholarly paper.")
- [x] **Step 3: Preserve the existing standing/scope/license paragraphs verbatim** — only add navigation, don't remove the legal-standing context.
- [x] **Step 4: Verify links resolve**

```bash
grep -oE '\]\([a-zA-Z0-9/_.-]+\)' README.md | sed -E 's/^\]\(//; s/\)$//' | while read p; do
  [ -e "$p" ] || echo "DEAD: $p"
done
```
Expected: no output.

- [x] **Step 5: Commit**

```bash
git add README.md
git commit -m "docs: surface flagship paper and add real navigation to README"
```

---

## Task 3: Add minimal GitHub Pages scaffolding (file-only, does not deploy anything)

**Files:**
- Create: `docs/_config.yml`

**Interfaces:**
- Consumes: nothing.
- Produces: the config GitHub Pages will use *if and when* Settings → Pages → Source is pointed at `docs/` on a branch (Task 5, human-confirmed).

- [x] **Step 1: Create `docs/_config.yml`**

```yaml
theme: jekyll-theme-cayman
title: "legal-theory"
description: "Findings of fact and legal theory — labor, cooperative investment, and expression law in California and federal jurisdiction."
plugins:
  - jekyll-relative-links
relative_links:
  enabled: true
  collections: false
markdown: kramdown
```

`jekyll-relative-links` is bundled in the `github-pages` gem GitHub Pages runs by default, so no `Gemfile` is needed — this rewrites the `.md` links already written in Tasks 1–2 to `.html` at build time.

- [x] **Step 2: Validate YAML**

```bash
python3 -c "import yaml; yaml.safe_load(open('docs/_config.yml'))" && echo OK
```
Expected: `OK`. Ran — got `OK`.

- [ ] **Step 3: Commit**

```bash
git add docs/_config.yml
git commit -m "chore: add GitHub Pages Jekyll config (cayman theme, relative-links)"
```

---

## Task 4: Wire the DocBook paper's HTML build into the deployed site

**Files:**
- Create: `.github/workflows/build-papers.yml`
- Modify: `papers/ai_and_ip/llm-database-theory/Makefile` (add an `install-dir` target if the existing `make html` doesn't already support an output-directory override — check first, don't duplicate logic)

**Interfaces:**
- Consumes: the existing `make html` target (already produces `generated/01-llm-database-theory.html`, `generated/02-legal-corpus-connections.html`).
- Produces: `docs/papers/ai_and_ip/llm-database-theory/*.html`, committed by CI so GitHub Pages serves it as static HTML alongside the Jekyll-rendered markdown.

- [x] **Step 1: Read the existing Makefile to confirm the `html` target and output path**

```bash
grep -A3 '^html:' papers/ai_and_ip/llm-database-theory/Makefile
```
Confirmed: `html: $(HTML_OUTS)` with pattern rule `generated/%.html: src/%.xml xsl/html5.xsl` running `xsltproc --xinclude xsl/html5.xsl $< > $@`. Output lands in `generated/*.html` as assumed.

- [x] **Step 2: Write `.github/workflows/build-papers.yml`**

```yaml
name: Build DocBook papers
on:
  push:
    branches: [main]
    paths:
      - 'papers/**'
permissions:
  contents: write
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install DocBook toolchain
        run: sudo apt-get update && sudo apt-get install -y libxml2-utils xsltproc
      - name: Build HTML
        working-directory: papers/ai_and_ip/llm-database-theory
        run: make html
      - name: Copy into docs/ for Pages
        run: |
          mkdir -p docs/papers/ai_and_ip/llm-database-theory
          cp papers/ai_and_ip/llm-database-theory/generated/*.html docs/papers/ai_and_ip/llm-database-theory/
      - name: Commit generated HTML
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add docs/papers/
          git diff --cached --quiet || git commit -m "chore: rebuild papers HTML [skip ci]"
          git push
```

- [x] **Step 3: Add links from `docs/index.md`'s Papers section to the built HTML** — done
  once the workflow was actually exercised (see "Post-deploy bug found and fixed" section:
  the build was broken twice over; fixed both bugs, then ran it for real, including in CI, and
  it committed `docs/papers/ai_and_ip/llm-database-theory/html/*.html`, which `docs/index.md`
  now links to directly).

- [x] **Step 4: Verify the workflow YAML parses**

```bash
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/build-papers.yml'))" && echo OK
```
Ran — got `OK`.

- [ ] **Step 5: Commit**

```bash
git add .github/workflows/build-papers.yml
git commit -m "ci: build DocBook paper to HTML and publish under docs/ for Pages"
```

---

## Task 5: Enable GitHub Pages — DONE, previewing from this branch (2026-07-21)

Executed with explicit user confirmation via AskUserQuestion (user wanted to preview from the
feature branch before merging to `main` — deliberately did not merge).

- [x] Confirmed Pages was already enabled repo-side (`build_type: "workflow"` — the newer
  Actions-based model, not classic branch-source) but nothing had ever deployed: `html_url`
  set, live URL 404, zero workflow runs.
- [x] Added `.github/workflows/deploy-pages.yml` (`actions/jekyll-build-pages` →
  `upload-pages-artifact` → `deploy-pages`), triggered on push to
  `claude/llm-database-theory-codification` + `workflow_dispatch`. Honors `docs/_config.yml`
  (cayman theme, `jekyll-relative-links`).
- [x] First deploy attempt was rejected: the `github-pages` environment's deployment-branch
  policy only allowed `main`. Confirmed with user, then added this branch to the policy via
  `gh api -X POST .../environments/github-pages/deployment-branch-policies -f name=claude/llm-database-theory-codification`
  (additive — `main` stays allowed too).
- [x] Re-ran the workflow — build + deploy both succeeded.
- [x] Verified live: `https://metavacua.github.io/legal-theory/` returns 200, title renders,
  nested pages (e.g. `court-record/matters/cooperative-investment-law/`) return 200, and
  `jekyll-relative-links` correctly rewrites `.md` links to `.html` in the served HTML.

**Remaining for a future session, on request:** merge to `main` (the workflow trigger would
need broadening to include `main`, and the `deploy-pages.yml` branch trigger updated —
`main` is already in the environment's branch policy so no further policy change is needed);
add the live URL to `README.md`'s "Start Here" section once the canonical (main-branch) URL
is the one being pointed to.

---

## Task 6: Draft/revision consolidation pass (future — not executed by this plan)

**This task is deliberately deferred** — it touches court-record evidentiary files, which the Global Constraints above forbid moving without explicit confirmation.

- [ ] For each cluster in "Current-state findings" above, `diff` the files, determine which is canonical, and either (a) get user sign-off to move superseded drafts to an `archive/` subfolder with a pointer left behind, or (b) confirm both are intentionally distinct evidence (e.g., successive drafts submitted at different times) and leave as-is with an explicit note in the matter's `README.md`.
- [ ] Specifically resolve whether `sex-work-consent-bodily-autonomy/evidence/the-nexus-of-consent-and-consideration.md` and `theory/california-statutes/existing-law/california-sex-contracts-and-consent.md` (same title, different lengths) are duplicate submissions or genuinely distinct documents.

---

## Task 7: DocBook/XSLT migration for the docs/ corpus (future — needs its own brainstorming pass)

**Deliberately not started.** Direction confirmed 2026-07-21: extend the repository toward
DocBook 5.2 XML + XSLT-built HTML5 for the `docs/` corpus generally, not just
`papers/ai_and_ip/llm-database-theory/`. `xsltproc` (already the toolchain for that paper) is
confirmed as the right tool — no new dependency, no Node/Ruby build.

**Why this is a separate effort, not a Task 1–6 add-on:** 123 documents, most several thousand
words, currently in free-form Markdown with inconsistent heading structure (see Task 1 Step 2's
list of files where the first heading is a stray sub-section, not a title). Converting all of
them is a multi-week effort with real design decisions (schema shape, per-matter vs. per-corpus
schema, how `evidence/` vs. `findings.md` differ structurally) that should go through
`superpowers:brainstorming` before any conversion work starts, not be decided inside this
loop's stop-hook cycle.

**A concrete, promising starting point for that future brainstorming session:**
`papers/ai_and_ip/llm-database-theory/schema/custom.rnc`'s `finding-section` element
(`role="finding"`, `condition` ∈ `confirmed | confirmed-with-caveats | split`, required
`xml:id`) already models exactly the Findings-of-Fact/Conclusions-of-Law structure every
matter's `findings.md` uses informally today (see e.g.
`docs/court-record/matters/cooperative-investment-law/findings.md`). Converting `findings.md`
files first — 5 short, structurally-uniform documents — would be a much smaller first slice
than the 70-document `evidence/` corpus, and would validate the schema generalizes before
committing to converting evidence documents too.

**Suggested shape for that future plan** (not committed to — for the brainstorming session to
evaluate): promote `schema/custom.rnc` and `xsl/{html5,latex}.xsl` out of the single-paper
directory to a repo-root `schema/` and `xsl/`, so both `papers/` and `docs/` can reference the
same transforms; keep Markdown as the source format for documents not yet converted (the
Jekyll deploy in Tasks 3–5 keeps serving those) so the corpus is never in a broken intermediate
state — HTML5 output from converted DocBook sources and Jekyll-rendered HTML from
not-yet-converted Markdown sources can co-exist under the same deployed site indefinitely.

## Post-deploy bug found and fixed (2026-07-21)

QA sweep of the live site (not just spot-checks) caught a real defect: `papers/` sat at the
repo root, outside the Jekyll Pages source root (`docs/`), so the flagship paper — the very
first "Start Here" link in both README.md and docs/index.md — 404'd live, despite rendering
fine when browsing GitHub directly (GitHub's own renderer isn't scoped to the Pages source
root; Jekyll's build is). Fixed by `git mv papers docs/papers` and updating every internal
reference (README.md, docs/index.md, docs/papers/README.md, docs/papers/ai_and_ip/README.md,
the paper's own BibTeX citation URL, build-papers.yml's trigger path and generated-HTML target).
Re-deployed and verified: `/papers/ai_and_ip/llm-database-theory/` now returns 200.

Followed up with a full sweep — extracted all 124 `docs/index.md` document links
programmatically and curl'd every one against the live site (README.md links resolve to the
directory's index via the bundled `jekyll-readme-index` plugin, not `README.html` — accounted
for in the check). All 124 return 200.

**Second post-deploy check: `build-papers.yml` had never actually been run, only YAML-linted.**
Testing it required broadening its push trigger to this branch (workflow_dispatch doesn't work
for workflows that only exist on a non-default branch — confirmed via a 404 from the Actions
API). Running `make all` locally surfaced two real, pre-existing bugs in the paper's own build
(neither introduced by this reorganization): `xsl/html5.xsl`'s `db:link[@xlink:href]` template
never declared the `xlink` prefix (only article 2 uses `xlink:href`, so article 1 masked it);
`schema/custom.rnc`'s top-level `db:section` pattern declared explicit attributes that
collided with its own `any` wildcard (RELAX NG "duplicate attribute"), and the Makefile's
`validate` target ran that schema against `00-metadata.xml`, an XInclude fragment with no
`<db:article>` root the schema could ever match. Fixed all three; `make all` and CI both run
clean now, and the CI-committed HTML is linked from `docs/index.md`'s Papers section.

## Full-corpus link/anchor sweep (2026-07-21) — clean, no changes needed

Prior checks only covered links *from* README.md/docs/index.md *to* documents. Never checked
whether the 123 documents link to each other with broken paths, or whether fragment anchors
(`#section-name`) actually match a real heading rather than just an existing file. Ran both
checks programmatically across all of `docs/**/*.md` (180 internal links; GitHub-slug
algorithm reimplemented, including the `-1`/`-2` suffixing GitHub applies to duplicate
headings): 0 broken file targets (one false positive — the plan's own prose describing the
link-format convention, not a real link) and 0 mismatched anchors. No fixes needed.

## Iteration log

- **Iter 1:** Tasks 1–3 (index rewrite, README rewrite, Pages config scaffold). Commits `608bfdd`.
- **Iter 2:** Task 4 (CI workflow to build the DocBook paper, inert until Task 5). Commit `b52c606`.
- **Iter 3:** Found and fixed a gap Task 1 didn't cover — GitHub's native file-tree browsing
  (as opposed to following `docs/index.md`) dead-ended at bare directories. Added landing
  READMEs to `docs/court-record/`, `docs/court-record/theory/`, `docs/proposals/`; wired real
  links into the 5 matter READMEs' `findings.md`/`evidence/` references. Commit `1c12243`.
- **Iter 4:** Swept the rest of the tree for the same gap — added landing READMEs to
  `docs/cross-cutting/`, `docs/wip/`, `docs/court-record/matters/`, `papers/`,
  `papers/ai_and_ip/` (commit `e7a59ba`). Also set GitHub repo topics
  (`legal-theory`, `legal-research`, `california-law`, `constitutional-law`, `labor-law`,
  `copyright-law`, `docbook`, `pro-se`, `public-record`, `ai-and-law`) via
  `gh api -X PUT repos/metavacua/legal-theory/topics` — reversible metadata, done without
  further confirmation since it doesn't touch content or flip Pages. Every directory reachable
  from README.md or docs/index.md now has a landing page; Tasks 1–4 are complete. Only Task 5
  (Pages + merge, needs a branch/settings decision) and Task 6 (evidence dedup, needs a
  content decision) remain, both explicitly gated on user confirmation.

## Self-review

- **Spec coverage:** "accessibility and visibility... in the deployed web page index" → Tasks 1, 3, 4, 5. "...and in the github readme" → Task 2. Both explicitly requested surfaces are covered.
- **No placeholders:** all steps have literal file content, exact commands, and expected output.
- **Not touched:** court-record evidence files are neither moved nor renamed anywhere in Tasks 1–5 (Task 6 explicitly defers this behind a confirmation gate, per Global Constraints).

## Continuation log — everything since Iter 4 (this section keeps the plan current; the work below went far beyond this document's original 6 tasks)

This plan's Tasks 1–4 shipped the navigation/index/README rewrite and landing-page sweep. Task 5
(Pages + merge) and Task 6 (evidence dedup) were left gated on user confirmation. What actually
happened after that confirmation, in order, spans several dedicated specs/plans of its own — this
section is the index of record, not a duplicate of their detail:

- **Pages deployed** (Task 5 confirmed): GitHub Pages enabled via Actions (`actions/jekyll-build-pages`
  + `actions/deploy-pages`), deploying from this feature branch (`claude/llm-database-theory-codification`)
  per explicit user preference, without merging to `main` first. Live at
  `https://metavacua.github.io/legal-theory/`.
- **Full DocBook 5.2 corpus migration** — every Markdown document in the corpus (70 evidence + 5
  `findings.md` + 20 theory + 8 cross-cutting + 8 wip + 6 proposals = 117 documents) converted to
  validated, schema-checked DocBook 5.2 XML and built to HTML5, matter-by-matter with user
  confirmation at each boundary. Full detail, including the markup-quality taxonomy the tool
  encountered (5 defect classes) and the conversion tool's own TDD history:
  [2026-07-21-docbook-corpus-migration-design.md](../specs/2026-07-21-docbook-corpus-migration-design.md),
  [2026-07-21-source-markdown-quality-taxonomy.md](../specs/2026-07-21-source-markdown-quality-taxonomy.md).
- **README.md and docs/index.md brought current** after that migration — accurate document counts,
  a prominent link to the live site (the index had drifted to describe the live site as still
  "pending" after it was actually live), every link updated from `.md` to its built `.html`.
- **Site-wide UX/accessibility fixes** applied directly to the DocBook→HTML5 XSLT
  (`docs/xsl/html5.xsl`): every built page gained a small "← Index" navigation link back to the
  site root (previously a dead end reachable only via the browser back button), and finding-status
  sections (confirmed/confirmed-with-caveats/split) gained a text badge alongside their existing
  color-coding (previously color was the *only* signal, which fails for colorblind readers and
  is invisible to screen readers).
- **GitHub repo metadata**: `topics` were already set (see Iter 4 above); the repo's homepage/
  "Website" field (shown at the top of every GitHub repo page, separate from `topics`) was empty
  and is now set to the live Pages URL.
- **CI generalized**: `.github/workflows/build-corpus.yml` added to validate (`xmllint`/`jing`)
  and rebuild (`xsltproc`) the whole corpus on every relevant push, rather than the pre-existing
  `build-papers.yml` only ever covering the flagship paper.
- **Corpus atomization**: every one of the 117 corpus documents plus the flagship paper's 2
  articles was decomposed from one monolithic XML file into a thin "shell" file plus one fragment
  file per top-level section (via XInclude) — the largest document had been ~18.4k words in a
  single file, unwieldy for both human and LLM-agent editing. Metadata boilerplate, previously
  duplicated byte-for-byte across all 117 `.meta.xml` files, was deduplicated into one shared
  file. Executed as its own 15-task subagent-driven-development plan with a fresh implementer +
  independent reviewer per task; caught and fixed 3 real defects along the way (a critical bug
  where the splitter silently dropped a document's metadata reference, a title-extraction bug
  found and fixed twice via systematic debugging, and a CI regression the final whole-branch
  review caught before it ever reached production). Full detail:
  [2026-07-22-corpus-atomization-design.md](../specs/2026-07-22-corpus-atomization-design.md),
  [2026-07-22-corpus-atomization-plan.md](2026-07-22-corpus-atomization-plan.md) (the plan's own
  completion log has the exact commit-by-commit account).
- **Search-engine discoverability**: no `sitemap.xml` existed for the deployed site — search
  engines had no structured way to discover the corpus's 117+ document pages beyond following
  in-site links. Added `jekyll-sitemap` (GitHub Pages' supported plugin) to `docs/_config.yml`;
  also excluded two internal session/provenance notes files
  (`papers/ai_and_ip/llm-database-theory/scratch/*.md`) that were being built and served publicly
  despite never being referenced from the curated index — they no longer appear in the sitemap
  or resolve to a public page.
- **Task 6 (evidence draft-lineage consolidation) remains explicitly deferred** — the draft/
  revision clusters catalogued in the "Current-state findings" section above were never touched;
  every draft and its corresponding final/revision were converted to DocBook independently, with
  no consolidation, per this plan's original Global Constraints. This is the one item from the
  original 6-task scope that is still genuinely open, should a future session want to pick it up.

**Current state, in one sentence:** the two originally-requested surfaces (deployed web page
index, GitHub README) are live, accurate, fully linked, navigable, accessible, and
search-engine-discoverable, and the underlying corpus is now structured for efficient ongoing
maintenance — the reorganization this plan set out to do is complete except for the deliberately
deferred draft-consolidation pass.

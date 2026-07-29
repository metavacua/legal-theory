# Site Standardization & Agent-Artifact Removal: Design

## 1. Motivation

Retiring `html5.xsl` (previous design/plan, complete) fixed how documents render but surfaced a
deeper split: `docs/index.md` and 15 `README.md` files under `docs/` are still Markdown, rendered
by Jekyll with the `jekyll-theme-cayman` theme -- an entirely separate pipeline from the 120
DocBook documents it links to, producing a jarring, inconsistent site. Investigating that split
surfaced four more, confirmed by direct testing, not assumed:

- **`docs/index.md` is hand-maintained and has already drifted from reality.** Its Bibliography
  section describes `docs/scripts/build_bibliography.py`'s output as current, working methodology,
  and links to design/plan documents for it -- but both linked documents are now short
  "fully superseded" stubs (this session's own earlier correction pass), and
  `bibliography/references.html` itself still uses the informal `works-cited`/`listitem`
  convention the citation-standardization project exists to replace. The index presents superseded
  architecture as current truth, purely because nothing keeps it in sync with the corpus's actual
  state.
- **`docs/index.md`'s own stated linking policy contradicts itself** ("every link... points to a
  document's built HTML page, not a bare directory or a `.md` source file") while 7 of its own
  links are literal `.md` files, and 5 more label targets `.md` when no `.md` source has existed
  for any corpus document since the DocBook migration completed.
- **`docs/_config.yml`'s Jekyll `exclude:` list has exactly one entry.** Nothing excludes
  `docs/scripts/` (this project's own Python tooling) or `docs/superpowers/` (this session's own
  planning documents) from the Jekyll build. Both are confirmed live on the deployed site today
  (`.../scripts/convert_to_docbook.py` and `.../superpowers/plans/....html` both return HTTP 200)
  -- a legal-research site is currently also serving an AI coding agent's Python source and its
  own internal planning narrative as part of the same public corpus.
- **`docs/proposals/legislative/california/state-legislature/` (and one `docs/proposals/executive/...`
  path) still carries 5 orphaned pre-DocBook-conversion `.md` originals** alongside their already-
  converted `.xml`/`.html`. Confirmed harmless today (the DocBook `.html` wins any path collision,
  verified live), but real, unlinked debris.

Separately, a recursive audit of the repository for coding-agent-specific artifacts (this
session, on request) found: `docs/superpowers/` (20 tracked planning documents) has no
justification to remain in the tracked working tree once the work it describes is complete -- git
history is the durable, complete, non-decaying record of that provenance; a parallel hand-curated
archive only duplicates it, imperfectly, as already demonstrated twice by real drift in this
session. `.markdownlint-cli2.jsonc` is confirmed dead (referenced by no script, no CI step).
`docs/papers/ai_and_ip/llm-database-theory/scratch/{formulas,notes}.md` is real, substantive,
deliberately-committed content (research provenance, math reference tables), actively referenced
by the paper's own `README.md` (its "Source Files" table, and its "Open Questions" section pointing
readers to `scratch/notes.md` directly) -- kept, not removed; see §2.6.

**Framing correction, mid-design (explicit user direction):** `docs/index.html` is not
"navigation" in a lesser, non-scholarly sense -- it is a legal-theory and scholarship document
itself, the same way a table of contents or structural outline is part of a treatise, properly
constructed as the top-level document that makes the corpus accessible and is, in a real sense,
constructed *from* it. It gets the same `<info>`/DCTERMS metadata and passes through the same
validation pipeline as every other document in this corpus -- not a special case.

## 2. Architecture

### 2.1 `docs/index.xml` -- generated, first-class DocBook document

A new script, `scripts/generate_index.py` (see §2.4 for why `scripts/`, not `docs/scripts/`),
walks the corpus the same way `measure_citation_conformance.py`'s `_shell_articles()` already
does (root-tag `article`, excluding test fixtures and non-corpus paths), reads each document's
`<info><title>` (already real, DCTERMS-complete DocBook metadata -- no separate title source
needed), and groups by directory structure (matters, theory jurisdictional level, cross-cutting,
proposals, wip, the paper) to emit a real DocBook 5.2 `<article>`: `<section>`s per category,
`<itemizedlist>` of `<link xlink:href="...">` entries per document, matching the corpus's own
established citation/cross-reference conventions (`<biblioref>` where an entry is itself a
citable bibliography entry, e.g. the Bibliography section linking to `bibliography/references.xml`).
`docs/index.xml` gets the same `<info>` block (title, pubdate, biblioid, dc:type) every other
document gets via `write_metadata()`, and passes through the same `validate()` (real DocBook 5.2
grammar + this project's DCTERMS-completeness policy) and `build_html()` pipeline -- no special
casing. It is regenerated (not hand-edited) whenever the corpus changes; this eliminates the
Bibliography-section drift and the self-contradicting-policy findings structurally, not by
one-time correction.

The generator explicitly does **not** attempt automatic classification of a document's legal
subject matter or write descriptive prose (e.g. "CA Labor Code ABC test; NLRA...") -- that framing
text is genuine authored content, not derivable from a document's own metadata, and stays hand-
authored where it already exists meaningfully (see §2.2).

### 2.2 The 15 `README.md` files -- split by whether they're generatable

Direct inspection of all 15 (word counts + content read in full) splits them into two real
categories:

- **Pure-listing stubs (8 files, 7-15 lines each: `cross-cutting/README.md`,
  `wip/README.md`, `papers/README.md`, `papers/ai_and_ip/README.md`, `court-record/README.md`,
  `court-record/theory/README.md`, `court-record/matters/README.md`, `proposals/README.md`).**
  Every one of these is either a bare pointer to `docs/index.md`'s own anchors, or a directory
  listing already fully reconstructable from the corpus structure `generate_index.py` already
  walks. These are retired, not converted -- `docs/index.xml`'s own per-category sections (§2.1)
  already are this content, and maintaining a second, separate copy of the same list is the exact
  redundancy this whole design corrects. Any inbound link to one of these (from `docs/index.md`
  itself, or the matter READMEs' cross-references) is repointed to the corresponding
  `docs/index.html#anchor`.
- **Genuinely authored content (7 files: the 5 matter `README.md`s, `docs/audits/README.md`,
  `docs/papers/ai_and_ip/llm-database-theory/README.md`).** These contain real, non-derivable
  prose -- e.g. a matter's complaint-structure framing ("Jurisdiction and Venue," "Parties,"
  "Causes of Action"), the paper's own extended abstract, the audit methodology writeup. These are
  hand-converted to DocBook 5.2 `<article>`s (one conversion pass per file, preserving every
  section and cross-reference, verified via the same content-preservation diff technique already
  proven in the citation pilot and the `html5.xsl` retirement), built through the identical
  `build_html()` pipeline as everything else.

### 2.3 Drop Jekyll; deploy `docs/` as static HTML

Once nothing under `docs/` is Markdown that needs processing, Jekyll has no remaining job.
`.github/workflows/deploy-pages.yml`'s build step changes from `actions/jekyll-build-pages@v1`
to `actions/upload-pages-artifact@v3` pointed directly at `docs/` -- a standard, documented
GitHub Pages deployment mode requiring no `.nojekyll` workaround (`actions/upload-pages-artifact`
bypasses Jekyll processing entirely; it is not the classic branch-based Pages source, which is
the only mode where `.nojekyll` matters). `docs/_config.yml` (Jekyll config: theme,
`jekyll-relative-links`, `jekyll-sitemap`, the one-entry `exclude:` list) is deleted -- nothing
reads it once Jekyll isn't invoked.

`jekyll-sitemap`'s automatic `sitemap.xml` is replaced with a small addition to
`generate_index.py` (or a sibling `generate_sitemap.py`, decided at plan-writing time by which is
the cleaner single-responsibility split): walk every built `.html` file the same way
`_shell_articles()`/the corpus-wide rebuild already do, emit a standard `sitemap.xml` at
`docs/sitemap.xml`. This is not dropped as an unaddressed gap -- it is regenerated by the same
kind of real, standard tooling as everything else in this design, not preserved as a Jekyll
dependency.

### 2.4 Relocate `docs/scripts/` to `scripts/` (repo root)

`docs/` is not "a docs folder" in the generic sense -- it is the literal GitHub Pages source root
(`deploy-pages.yml`'s `source: docs`, confirmed). Anything placed under it for organizational
convenience gets unintentionally published, as already demonstrated. `docs/scripts/` (22 `.py`
files, their tests, and their fixtures) is real, justified, actively-used tooling -- not cruft --
but has no reason to live inside the Pages source root. It moves to `scripts/` at the repo root,
sibling to `docs/`.

Confirmed via direct scan before this design was written: every script's own internal imports use
`sys.path.insert(0, str(Path(__file__).resolve().parent))` (self-relative; unaffected by the
move). Only two hardcoded `"docs/scripts"` string references exist in script source, both inside
docstrings/prose (`build_bibliography.py`'s generated-by attribution string,
`audit_footnote_links.py`'s docstring listing excluded corpus subdirectories) -- both updated to
`scripts/build_bibliography.py` and dropped from the excluded-subdirectory list respectively (it
is no longer under `docs/` at all, so it needs no exclusion). One CI file,
`.github/workflows/build-corpus.yml`, references the path twice (the `python3 docs/scripts/...`
invocation and the `find`'s `-not -path 'docs/scripts/*'` filter) -- both updated to the new path.

### 2.5 Remove `docs/superpowers/` from the tracked working tree

Per explicit direction: git history is the durable, complete provenance record; a parallel
hand-curated archive of planning documents duplicates it imperfectly (this session's own
`html5.xsl`-framing correction and the bibliography-design supersession are concrete evidence of
that drift, not a hypothetical). All 20 tracked files under `docs/superpowers/` are removed
(`git rm`) -- recoverable in full via `git log`/`git show` for anyone who needs them, but no
longer part of the working tree, the Pages build, or `docs/index.xml`'s generated listing (the
generator in §2.1 only walks real corpus documents; it was never going to reference these anyway
once they're gone). This also resolves, structurally, the self-referential "see the reorganization
plan for how this index is maintained" links `docs/index.md` currently carries -- there is no
reorganization plan left to point to, and the generated index doesn't need one; how it's
maintained is "run the generator," documented in the generator's own docstring, not a separate
narrative file.

Plans/specs authored during future work on this repo follow the same lifecycle: written and used
while the work they describe is active, removed from the tracked tree once that work lands. This
is a working convention for future sessions, not a mechanical step this plan executes once --
concretely, that means this design document itself, and the implementation plan that executes it,
are removed from the tracked tree as this same plan's own final step, once the rest of it has
landed and been verified. Writing them was legitimate (the work they describe needed a design and
a plan); keeping them after execution would repeat the exact pattern §2.5 corrects.

### 2.6 `docs/papers/.../scratch/{formulas,notes}.md`

The paper's own `README.md` actively references both files -- its "Source Files" table lists them
alongside real build inputs, and its "Open Questions" section directs readers to
`scratch/notes.md` for the full list, giving only a truncated summary inline. This is real,
currently load-bearing documentation the paper's own README depends on, not unintegrated or
uncited content. **Disposition: kept, not removed.** Task 4's README-to-DocBook conversion decides,
with that context in hand, whether to keep referencing `scratch/` as-is, fold its content directly
into the converted README, or promote it into the paper's own citable body.

### 2.7 `.markdownlint-cli2.jsonc`

Confirmed dead (no CI step, no script, nothing references it). Removed.

## 3. Verification

- Every new/converted document (`docs/index.xml`, 7 converted READMEs) validates against the real,
  fetched DocBook 5.2 grammar (`jing`) and this project's DCTERMS-completeness policy
  (`check_dcterms_completeness.py`) -- the same gate every existing document already passes,
  applied uniformly, no exceptions.
- Content-preservation diff (the same before/after rendered-text-diff technique proven in the
  citation pilot and the `html5.xsl` retirement) for each of the 7 hand-converted READMEs, to
  confirm no authored prose is lost in the Markdown-to-DocBook conversion.
- Full test suite re-run after the `scripts/` relocation (path changes are exactly the kind of
  thing a full suite run catches if anything was missed).
- Live-site checks, matching the pattern already used for the `html5.xsl` retirement: confirm
  `docs/scripts/**` and `docs/superpowers/**` paths 404 on the deployed site (currently 200);
  confirm zero Cayman-theme markers (`cayman`, `jekyll-theme`) anywhere in deployed output; confirm
  `sitemap.xml` is present and lists real corpus URLs; confirm `docs/index.html` itself validates
  and renders with the same bare `docbook-xsl-ns` styling as every other page (no theme mismatch).
- `measure_citation_conformance.py` re-run as a sanity check that the citation/bibliography layer
  is untouched by this restructuring (it measures the XML layer; this design changes rendering,
  navigation, and repo layout, not citation content).

## 4. Explicit scope

**In scope:** `docs/index.xml` generation (§2.1), the 7 README conversions + 8 README retirements
(§2.2), dropping Jekyll for static-HTML Pages deployment + sitemap generation (§2.3), relocating
`docs/scripts/` to `scripts/` (§2.4), removing `docs/superpowers/` from the tracked tree (§2.5),
`scratch/` disposition (§2.6, kept), removing the dead lint config (§2.7).

**Explicitly out of scope, not precluded:**
- Root-level `README.md` and `LICENSE` (repo root, outside `docs/`, outside the Pages build
  entirely -- serves GitHub's native repo-browsing experience specifically, a genuinely different
  audience/pipeline than the deployed site, untouched by this design).
- The draft/revision document clusters flagged in the original 2026-07-20 reorganization plan
  (e.g. `cooperative-security.md`/`us-ca-coop-securities.md`/`us-ca-coop-securities-v6.md`) --
  pre-existing, explicitly deferred content-curation work, unrelated to markup standardization.
- The pre-existing mojibake bug in one bibliography entry's title (`ð¤` instead of the intended
  emoji) and the eyecite-wiring gap flagged in the citation-standardization final review -- both
  already tracked separately, unrelated to this design.
- Citation-standardization Phase 2 (bulk conversion of the remaining Category A/flat-entry
  documents) -- unrelated, separately scoped.

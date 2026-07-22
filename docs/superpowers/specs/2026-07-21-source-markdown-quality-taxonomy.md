# Source Markdown Quality Taxonomy

**Status:** Living reference document for the DocBook corpus migration
(`docs/superpowers/specs/2026-07-21-docbook-corpus-migration-design.md`).
Every markup-quality class that has affected `docs/scripts/convert_to_docbook.py`
must be recorded here — symptom, root cause, corpus prevalence, lint
correlation, and current handling status — before the Phase 2/3 rollout
continues into a new matter. Update this document, not just the code, whenever
a new class is found.

**Linting is mandatory.** `npx markdownlint-cli2 <path>` (repo-scoped config
at `.markdownlint-cli2.jsonc`) must be run over a document — or, for a
corpus-wide sweep, the glob patterns in this doc's "How to reproduce this
scan" section — as part of investigating any new conversion problem, before
writing an ad-hoc detection script. The scoped config exists precisely so
this is fast and low-noise; reach for it first.

## How this taxonomy was built

1. A full-corpus dry run of `convert()` (docs/scripts/convert_to_docbook.py)
   across all 106 non-README content documents under `docs/court-record/`,
   `docs/cross-cutting/`, `docs/wip/`, `docs/proposals/` — not just the
   `evidence/` documents already converted — writing output to a scratch
   directory, never touching the real corpus files.
2. `npx --yes markdownlint-cli2` run twice: once with markdownlint's full
   default ruleset (to see the complete signal, however noisy), once with
   this repo's scoped `.markdownlint-cli2.jsonc` (the rules that actually
   correlate with a `convert()` problem).
3. Every document `convert()` flagged (non-empty `errors` or `content_diff`,
   or an uncaught exception) was traced to a root cause by hand — reading the
   actual generated XML, not just the diff output — the same standard applied
   to the two bugs found earlier in this session (the `<literallayout>`
   rendering defect and the table-border false positive).
4. Cross-referenced each root cause against the two lint runs to determine
   whether a lint rule would have predicted it, partially predicted it, or
   missed it entirely — recorded honestly per class, including where lint
   turned out not to help.

## Corpus-wide scan results (2026-07-21)

- **106 content documents** scanned (`evidence/`, `theory/`, `cross-cutting/`,
  `wip/`, `proposals/` — excludes the 6 already-converted `google-platform-
  misclassification` evidence documents and the 5 already-converted
  `findings.md` files, and excludes `README.md` landing pages, which are new
  files this session authored and aren't legacy source-quality candidates).
- **97/106 clean** (no `errors`, empty `content_diff`).
- **9/106 flagged**, covering 3 of the 5 classes below (Classes A and B are
  already fixed at the tool level and produce zero flags now).

## The classes

### Class A — Accidental Markdown hard line breaks

**Symptom:** Before the fix, pandoc emitted `<literallayout>` (preformatted,
non-reflowable) instead of `<para>` for the containing block — and
`html5.xsl` had no template for it, so it rendered as bare, unstyled text
with no paragraph wrapping in the built HTML. This was live and broken on 3
already-deployed pages before being caught.

**Root cause:** CommonMark treats a line ending in 2+ trailing spaces,
immediately followed by another non-blank line, as an intentional hard line
break. In this corpus these are copy-paste artifacts (from word processors,
chat/AI tool output, or similar), not deliberate formatting — legal analysis
prose has no typographic reason to force a mid-sentence line break.

**Lint correlation — imprecise in both directions:**
- markdownlint's **default** `MD009` config (`br_spaces: 2`) treats
  exactly-2-trailing-space lines as intentional hard breaks per the
  CommonMark spec and does *not* flag them — only 17 hits across 9 files
  (lines with 1, 3+, or otherwise-anomalous trailing whitespace).
- `MD009` with `br_spaces: 0` (flag *any* trailing whitespace) over-counts:
  4699 hits across 93 files — because it also flags harmless lone `"  "`
  blank-content spacer lines (another copy-paste artifact, common in this
  corpus) that never trigger CommonMark's hard-break parsing since they have
  no preceding text content in the same paragraph flow.
- **Neither markdownlint config alone gives the precise count.** The
  distinguishing script (below) checks specifically for real text content
  ending in 2+ trailing spaces, immediately followed by another non-blank
  line — the exact condition that produces a hard break.

**Prevalence:** 223 genuine mid-paragraph hard-break lines across 35 of 132
corpus `.md` files (precise scan, run once against the pre-fix corpus).

**Status: FIXED at the tool level** (commit `ec9853f`).
`_strip_trailing_whitespace()` in `convert_to_docbook.py` normalizes the
source before pandoc ever sees it, removing the trigger at its source.
`html5.xsl` also gained a `db:literallayout` template (merged with the
existing `db:screen` template, commit `4f6a9f7`) as defense-in-depth, in case
a document ever has a genuinely-intentional preformatted block.

**Example:** `california-worker-misclassification-risk-analysis.md` (10
occurrences before the fix, 0 after; re-converted in commit `6fea314`).

**Reproduce the precise count:**
```python
# A genuine CommonMark hard break: real text content, 2+ trailing spaces,
# immediately followed (no blank line) by another non-blank line.
import re, glob
files = glob.glob("docs/court-record/**/*.md", recursive=True) + \
        glob.glob("docs/cross-cutting/*.md") + \
        glob.glob("docs/wip/**/*.md", recursive=True) + \
        glob.glob("docs/proposals/**/*.md", recursive=True)
for fn in files:
    lines = open(fn, encoding="utf-8", errors="replace").readlines()
    for i in range(len(lines) - 1):
        line, nxt = lines[i].rstrip("\n"), lines[i + 1]
        stripped = line.rstrip(" ")
        if len(line) - len(stripped) >= 2 and stripped.strip() and nxt.strip():
            print(f"{fn}:{i+1}")
```

---

### Class B — Table plain-text rendering divergence

**Symptom:** `content_preservation_diff()`'s word-level check flags dozens of
border-character-only tokens (dashes on one side, pipes/colons on the other)
even though every cell's actual word content is identical and in the same
order on both sides.

**Root cause:** pandoc's plain-text writer renders the *same* GFM table two
different ways depending on which path produced the input: a column-aligned
ASCII grid (dashes) when converting directly from Markdown, vs. a
pipe-delimited rendering (pipes, colons — echoing the `:-:` alignment row)
when converting from the DocBook round-trip through `informaltable`/`entry`.
Verified independently on a real 9-column table before generalizing the fix:
zero real-word differences once border-only tokens are filtered out.

**Lint correlation — a false lead.** `MD060` (table-column-style) flags
*cosmetic* pipe-spacing inconsistency in source table syntax (1528 hits
across 75 files — the single largest scoped-lint category) but does **not**
predict which tables will trigger this specific diff-check false positive;
a table can be `MD060`-clean and still hit this, or `MD060`-flagged and never
hit it. Kept in the scoped config as a "worth a glance" signal, not a
predictor.

**Prevalence:** any document with a sufficiently large/complex table; the
originally-found case was a 9-column, ~15-row table.

**Status: FIXED at the tool level** (commit `ca812dd`, generalized in
`4f6a9f7`). `_is_ignorable_word_run()` tolerates any word-diff run with no
alphanumeric content — subsumes both this class and Class A's horizontal-rule
tolerance under one principled predicate, rather than an enumerated
character allowlist.

**Example:** `california-worker-misclassification-risk-analysis.md`.

---

### Class C — Malformed/tight nested emphasis and punctuation adjacency

**Symptom:** `content_preservation_diff()` flags single-space
insertions/removals at boundaries where the source has **no space** between
a word and adjacent `**bold**`/`*italic*` markup, or between markup and
punctuation/a bare URL — e.g. `Post-**Alice` / `Post-** Alice`, `FEC**:` /
`FEC **:`, `Goodridgehttps://...` / `Goodridge https://...`.

**Root cause:** ambiguous/malformed source markup — typically excessive
consecutive asterisks (`*****`, an unclear nesting of bold+italic with no
space) or a bare URL directly abutting a closing emphasis marker with no
space. Pandoc's plain-text writer's inline-span-boundary spacing convention
doesn't behave identically across the two comparison paths for this specific
kind of ambiguous input. Manually verified on every flagged instance so far:
**zero real content loss** — only a single space's presence/absence at a
formatting-boundary edge, confirmed by diffing the full word sequence with
the boundary-adjacent tokens excluded.

**Lint correlation — no reliable predictor found.** `MD037`/`MD038`/`MD039`
(spaces *inside* emphasis markers) target a different problem and had zero
hits in this corpus. `MD034` (bare URLs, 46 hits across 36 files) catches
the *"Goodridge"*-style sub-case (a bare URL with no wrapping `<>` or link
syntax) but not the excessive-asterisk sub-case. No single rule, or
combination checked so far, reliably predicts this class before running the
actual conversion.

**Prevalence:** 6 files found in the corpus-wide scan, 2–108 flagged
instances each:
- `contractual-architectures-for-ip-and-cooperatives.md` — 4
- `ai-corporate-personhood-and-legal-rights.md` — 6
- `state-supreme-court-case-study-report.md` — 2
- `the-laudable-contract-licit-sexual-service-agreements.md` — 6
- `california-contract-law-analysis.md` — 2
- `california-law-employment-retroactivity.md` — 2
- `first-amendment-landmark-cases-research.md` — **108** (a ~100-case-citation
  compendium; the malformed-emphasis pattern repeats once per citation —
  same root cause as the others, just at much higher frequency due to the
  document's structure, not a new class)
- `the-playable-social-contract.md` — 8

**Status: NOT auto-tolerated at the tool level — deliberately.** Every
instance found so far genuinely preserves content once manually verified;
but this class, unlike A and B, has no principled, narrow predicate that
distinguishes it from a genuine "a word got dropped right next to
punctuation" bug. Auto-tolerating single-word-boundary spacing diffs broadly
would blunt the safety net's ability to catch that real failure mode.
**Handling: per-document manual review** at conversion time — exactly what
the safety net is designed to produce (`content_preservation_diff`'s
non-empty return, read and judged by a human before the document is
committed) — not a tool-level fix. Revisit this decision if a 4th, 5th
affected file surfaces a pattern precise enough to safely automate.

---

### Class D — Poor/mechanical title extraction

**Symptom:** `extract_title()`'s article `<title>` doesn't reflect the
document's actual subject — it mechanically reads the first `#`-prefixed
heading verbatim, which for some documents is an internal sub-section
("Scenario 1: ...", "I. The Threshold Issue...") rather than a true
document-level title.

**Root cause:** some documents open with a body paragraph before their first
real heading, use a deep heading level (H3/H4) as their effective title, or
rely on a `**Bold Text**` pseudo-heading (no `#` at all) that
`extract_title()`/`wrap_fragment()` never recognize as a heading or section
boundary.

**Lint correlation — two rules together predict this well.** `MD041`
(first-line-heading — file doesn't start with a top-level heading; 21 files)
and `MD001` (heading-increment — heading levels skip; 34 files) both
correlate strongly with this class. `MD036` (emphasis-as-heading — bold text
used where a real heading belongs; 19 files) flags the pseudo-heading
variant specifically.

**Prevalence:** ~10 files identified during the earlier accessibility-reorg
audit (`docs/superpowers/plans/2026-07-20-repo-accessibility-reorganization.md`,
Task 1 Step 2). 3 already handled during this rollout:
`google-user-contracts-implicit-employment-obligations.md`,
`google-user-contracts.md`, `google-user-misclassification.md`. `MD041`'s
21-file list is the best available superset to check against as remaining
matters convert — not identical to the original 10 (some `MD041` hits are
files with a real title just formatted unusually, not a wrong title), but a
strong starting point.

**Status: HANDLED MANUALLY per-document.** Not automatable without either
LLM-assisted title inference or hand curation — "what is the true title" is
a judgment call the mechanical first-heading heuristic structurally cannot
make. Pattern already established: patch the article `<title>` and the
`.meta.xml`'s `dc:title` post-conversion to the human-curated title (matching
`docs/index.md`'s existing link text where one was already curated during
the reorg audit), rebuild HTML, re-validate.

**Example:** `google-user-contracts.md` (fixed in commit `192ff30`).

---

### Class E — Stray/malformed raw HTML-like tags in source

**Symptom:** `wrap_fragment()` crashed with an uncaught
`xml.etree.ElementTree.ParseError` (before this session's fix) — not a
flagged-for-review diff, a hard crash of the whole `convert()` call.

**Root cause:** a literal, unmatched HTML-like tag embedded in the source
Markdown (found: a lone `</content>` with no opening tag — almost certainly
a leftover artifact from whatever generation process produced the document,
e.g. an AI-assistant response that wrapped its output in `<content>...
</content>` and had the wrapper only partially stripped before being
committed). Pandoc's GFM reader passes unrecognized raw HTML through
verbatim into its DocBook5 output (the `raw_html` extension is on by
default), producing genuinely malformed XML no source-side whitespace
normalization can prevent.

**Lint correlation — no signal at all.** `MD033` (no-inline-html) is the
theoretically relevant rule, but it is **not enabled by default** in
markdownlint-cli2's stock ruleset, and — checked directly — does not fire on
this exact document even when explicitly scanned for it (an unmatched
closing tag with no corresponding open tag doesn't register the same way
`MD033`'s balanced-tag detection works). Not included in this repo's scoped
config: enabling it would also flag any legitimate inline HTML elsewhere in
the corpus with no way to distinguish "artifact" from "intentional," and it
still wouldn't have caught the one real instance found.

**Prevalence:** 1 confirmed instance in the 106-document scan
(`petition-corporate-ai-registry-ca-sos.md`) — the only crash found; likely
rare, but the corpus-wide dry run had never been run in full before this
investigation, so treat "1 known instance" as a floor, not a ceiling, for
documents not yet scanned (theory/cross-cutting/wip/proposals were included
in this scan; anything added to the corpus later should be re-scanned).

**Status: FIXED at the tool level** (commit `f67bac7`) — `convert()` now
catches `ET.ParseError` around `wrap_fragment()` and reports it through the
same `errors` list every other failure mode uses, instead of crashing
uncaught. **The affected source document itself is still unconverted** —
`petition-corporate-ai-registry-ca-sos.md` needs its stray `</content>` tag
manually stripped before it can convert successfully. It's also already
flagged in `docs/index.md` as `[template]` (placeholder fields not filled
in) — a Phase 3 (proposals-track) document, not blocking the current Phase 2
evidence-corpus rollout.

---

## Rules checked and found irrelevant to conversion correctness

Recorded so a future investigation doesn't re-walk this ground: `MD013`
(line-length, 13152 hits) — this corpus's prose is deliberately unwrapped,
reflowed by the renderer; `MD012` (multiple-blanks, 8795 hits) — collapses to
an ordinary paragraph break, harmless; `MD007` (ul-indent, 2498 hits) — no
observed correlation with a `content_diff`/`errors` flag; `MD030`
(list-marker-space, 1382 hits) — same; `MD047` (single-trailing-newline, 58
hits) — pandoc is insensitive to this; `MD032` (blanks-around-lists, 1 hit)
— negligible. None of these are in the scoped `.markdownlint-cli2.jsonc`.

## Repo-scoped lint config

`.markdownlint-cli2.jsonc` (repo root) enables only `MD009`, `MD041`,
`MD001`, `MD036`, `MD060`, `MD034`, `MD024` — the rules with a documented
correlation above — and disables every other default rule. Run before
investigating a new conversion problem:

```bash
npx --yes markdownlint-cli2 "docs/court-record/matters/**/*.md" \
  "docs/court-record/theory/**/*.md" "docs/cross-cutting/*.md" \
  "docs/wip/**/*.md" "docs/proposals/**/*.md"
```

## How to reproduce the full classification scan

```python
import sys, glob
sys.path.insert(0, "docs/scripts")
from convert_to_docbook import convert
from pathlib import Path

files = sorted(
    f for f in glob.glob("docs/court-record/matters/**/*.md", recursive=True)
    + glob.glob("docs/court-record/theory/**/*.md", recursive=True)
    + glob.glob("docs/cross-cutting/*.md")
    + glob.glob("docs/wip/**/*.md", recursive=True)
    + glob.glob("docs/proposals/**/*.md", recursive=True)
    if not f.endswith("README.md")
)
for f in files:
    try:
        r = convert(Path(f), Path("/tmp/scratch-scan"))  # never the real corpus dir
        if r.errors or r.content_diff:
            print(f, "errors=", len(r.errors), "content_diff=", len(r.content_diff))
    except Exception as e:
        print(f, "CRASH:", e)
```

Always write dry-run output to a scratch directory, never into the real
corpus tree, until a document is actually being converted for real (per the
per-document commit process already established in Phase 1/2).

# Footnote-to-Citation Audit: Design

## 1. Motivation

The consolidated bibliography (`docs/bibliography/references.xml`, shipped this session) solved
one half of the corpus's citation problem: it gives every source a single, deduplicated,
Bluebook/Chicago-formatted entry. The other half — named as sequenced follow-on work in that
project's own design doc (`docs/superpowers/specs/2026-07-23-consolidated-bibliography-design.md`
§8.1) — remains open: **446 files contain orphaned numeric footnote markers glued directly onto
body text** (`</emphasis>.4`, `word.12`) with no structural link to anything. These are vestiges
of the original Markdown→pandoc→DocBook conversion, where they were real footnote references
(`[^4]`) that the conversion flattened into plain digits, dropping the structural connection.

The working hypothesis — footnote *N* corresponds positionally to the *N*th entry in that
document's `works-cited` `<orderedlist>` — was investigated before any design work started
(not assumed). The investigation covered 8 documents spanning all 5 corpus areas and the
corpus-wide statistics across all 88 works-cited directories containing footnote markers. Full
method and evidence are in the research transcript this design draws from; the summary:

- **Positional correspondence is real and precise when it holds** — the majority of spot-checked
  mappings matched exact-title-to-exact-sentence, including cases with heavy footnote-number
  reuse (the same number cited 6-9 times across a document, every instance topically correct).
- **It is not safe to build blind, corpus-wide automation on it**, for three independently
  confirmed reasons:
  1. **Detection is ambiguous by construction.** The glued-digit shape is also produced by
     decimal section/subsection titles (`2.1 Deconstructing Wrongful Death Damages`),
     statute/regulation pincites (`Family Code § 6751.1`, `NAC 441A.805`), and in-body rule
     labels (`Rule 1.1`, `Rule 2.3`). None of these are footnotes; all match the same regex shape.
  2. **Mid-document renumbering restarts happen.** At least one confirmed case
     (`the-architecture-of-non-consensual-legality`) maps almost perfectly for 90% of its
     footnotes, then silently drops from a high number (267) to low integers (1-4) mid-fragment
     — evidence of content pasted in from a separately-numbered source without renumbering. A
     tool that assumes one number-space per document will corrupt exactly the block after an
     undetected restart.
  3. **Degenerate works-cited lists exist.** At least one document has 72 real footnote-1 uses
     against a works-cited list with exactly one entry, and that entry is not a real citation —
     just the bare title of a sibling document with no link. The hypothesis isn't applicable
     there regardless of numbering behavior.

This design's job is to make the ambiguity **visible and triaged**, not to resolve it blindly.

## 2. Scope: audit first, no rewrites

This project produces a **read-only audit report** — a structured list of every candidate
footnote-to-citation mapping across the corpus, each with a confidence tier and the specific
reason for that tier. **It modifies zero corpus documents.** A human reads the report and decides,
document by document, which mappings are safe for a future automated rewrite pass (a *separate*,
not-yet-designed project), which need manual correction first, and which should be left alone.
This mirrors the bibliography project's own most important lesson: the stratified human-review
gate caught a critical bug (a silent self-citation collision) that no automated invariant did —
for a rewrite that touches the body text of up to 446 real corpus documents, an unreviewed
mechanical pass is not an acceptable risk profile for a repository whose stated purpose is real
legal controversies.

## 3. Candidate detection: structural, not purely regex

A digit run is only a **footnote candidate** if it survives all of the following, applied to the
parsed DocBook XML (not the raw text):

1. **Never inside `<title>`.** Section/subsection titles use the same `N.M Heading` decimal shape
   as a footnote; DocBook already distinguishes a title from body prose structurally, so this
   exclusion is a parse-tree check, not a regex guess.
2. **Not immediately preceded (within a short token window) by `§`.** Excludes statute/regulation
   pincites (`§ 6751.1`) — the same character sequence used for statute detection in
   `build_bibliography.py`'s `_STATUTE_RE`.
3. **Not immediately preceded by a known California code name.** Reuses
   `build_bibliography.py`'s existing `CODE_ABBREVIATIONS` table (already validated against this
   corpus) rather than a second, independently-maintained list — catches pincites like
   `NAC 441A.805` structured as `<code-like-token> <digits>.<digits>`.
4. **Not immediately preceded by "Rule", "Section", or "Article" (case-insensitive).** Excludes
   in-body rule/section labels (`Rule 1.1`, `Rule 2.3`) found in the research sample.

What survives all four checks becomes a **candidate**.

## 4. Independent cross-check: the built HTML

Every candidate is additionally checked against the document's already-built `.html` output
(the same file `build-corpus.yml` already produces and commits for every shell article): does
the digit render as inline text inside a paragraph, or inside an `<h1>`–`<h6>` heading element?
This is a second, independently-derived signal — DocBook `<title>` maps to a heading tag via
`html5.xsl`, so in the ordinary case this simply re-confirms step 3.1's XML-structural check. It
is included anyway as defense-in-depth: the whole premise of this audit is that trusting one
signal path silently produces wrong answers (exactly what happened with the pure-regex approach
before it was investigated), and a second, differently-derived check on the same underlying
document is cheap to compute and catches any gap the XML-side parse alone might miss (e.g. a
title rendered through an unexpected XSLT template path).

## 5. Matching and confidence tiers

For each surviving candidate footnote *N* in a document, match it against the *N*th entry of that
document's `works-cited` `<orderedlist>` (resolved across the document's full `xi:include` graph,
reusing `build_bibliography.py`'s `build_backlink_map`/fragment-resolution machinery rather than
re-deriving it) and assign one of three tiers:

- **High** — entry *N* exists, has a real `<link xlink:href>` (not linkless/garbled), and no
  restart has been detected in this document *before* this footnote's position.
- **Medium** — entry *N* exists but is missing exactly one of the two High conditions (e.g. a
  real, linked entry, but positioned after a detected restart point; or a plausible entry with
  no link, positioned before any restart).
- **Needs manual triage** — footnote number exceeds the works-cited list's length, OR entry *N*
  is itself garbled/linkless AND the footnote is also past a restart point (both problems
  compounding), OR the document's works-cited list is flagged degenerate (§6).

The `<link>`-presence check is a corroboration signal in the same spirit as
`build_bibliography.py`'s case-classification domain-confidence heuristic: a positional match
alone is not proof, but a positional match *plus* independent evidence the target is a real,
resolvable source raises confidence the way a case-law-domain URL raised confidence for an
uncorroborated case-name match there.

## 6. Restart detection

Within a document's full footnote-number sequence (concatenated across its fragments in body
order), a **restart** is flagged when the sequence drops from a high value to a low one and then
continues at low values for multiple subsequent markers, rather than a single low-value outlier
consistent with ordinary footnote reuse (the exact drop-size and run-length thresholds are an
implementation-plan decision, tuned against the confirmed real restart case and validated against
false-positive risk on documents with heavy low-number reuse and no restart, not locked here).
Every footnote at or after a detected
restart point is downgraded at least one confidence tier from what its own individual signals
would otherwise earn, since a restart means the document's assumed single number-space is wrong
for that whole block. Restart detection runs **per fragment file**, not just per document, since
the confirmed restart case occurred within a single fragment, not at a fragment boundary.

## 7. Degenerate-bibliography triage

A document's works-cited list is flagged **degenerate** when it has real footnote markers but
the list itself is unusably short relative to the highest footnote number, or every entry in it
is linkless/garbled. Every footnote candidate in a degenerate document is routed straight to
"needs manual triage" regardless of its own individual signals — matching indices in vs indices
that don't map to real data isn't a confidence question, the underlying data doesn't exist.

## 8. Output format

A generated report — not a rewrite — one row per candidate footnote occurrence:

```
file, footnote_number, body_context_snippet, matched_works_cited_entry_text,
matched_works_cited_entry_url (or "none"), confidence_tier, flags
```

`flags` is a list drawn from: `restart_detected`, `exceeds_length`, `no_link_corroboration`,
`degenerate_bibliography`. Format choice (CSV vs. a generated DocBook/Markdown document, matching
the corpus's own conventions) and exact file location are implementation-plan decisions, not
locked here — this design fixes the *content and confidence model* of the audit, not its
serialization.

## 9. Explicitly out of scope for this project

- **Any file rewrite.** No `<footnote>`/`xref` markup is written by this project. That is
  necessarily a separate, later design — informed by reading this audit's output — with its own
  per-document review gate, matching how seriously the bibliography project treated touching
  real corpus data.
- **Fixing degenerate works-cited lists at the source.** Already named as separate follow-on work
  in the bibliography design (§8.3); this audit only *identifies* them.
- **Normalizing the statute-citation-abbreviation diversity** that step 3.3's exclusion list
  incidentally touches. Already named as separate follow-on work (bibliography design §8.4).

## 10. Reuse

This project reuses, rather than reimplements, `docs/scripts/build_bibliography.py`'s
`build_backlink_map`/`parse_xincludes` (xi:include graph resolution for locating a fragment's
works-cited section and owning shell), `CODE_ABBREVIATIONS` (statute-name exclusion list), and
the general pattern of `extract_works_cited`'s DocBook parsing. The new script imports these the
same way `build_bibliography.py` itself imports from `convert_to_docbook.py` — established,
working convention, not a new pattern.

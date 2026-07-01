# Session Notes — LLM Database Theory Paper

## Provenance

- Primary source: User-authored HTML position paper ("Language models are databases — a position paper
  on LLMs and intellectual property", July 2026).
- Research assistant: Claude Sonnet 4.6 (Anthropic), 2026-07-01.
- Deep-research workflow run: `wf_3d8e52ec-fd6` (launched 2026-07-01; status at time of
  DocBook encoding: still running, ~16 of 33+ agents complete). Full synthesis will be
  available when the workflow completes; this paper is written from sources confirmed prior
  to workflow completion.

## Citation Gaps

- **Cooper et al. 2025** (arXiv:2505.12546): Confirmed to exist; cite verifiable.
- **Follow-on 2026** (arXiv:2601.02671): Listed in HTML position paper; not independently
  verified at time of encoding. Treat as cited-by-source pending workflow confirmation.
- **Admissions compilation** (arXiv:2603.20957): Listed in HTML position paper; not
  independently verified at time of encoding.
- **LARQL INSERT INTO EDGES demo**: From YouTube presentation and LARQL repo README.
  The specific "Feature F8821@L26" numbering in the paper is illustrative of the mechanism;
  actual feature IDs will vary by model and session.
- **Gemma 3 4B performance claim** ("marginally faster than dense matmul"): From LARQL repo
  documentation and presentations; should be confirmed against LARQL CHANGELOG or benchmark
  data in the repo when citing in litigation contexts.

## Open Questions for Follow-Up

1. **Source attribution precision**: LARQL currently returns entity–relation–target triples
   at the semantic level (e.g. France → capital → Paris). It does not yet identify *which
   training document* is the source of a specific edge. This gap matters for litigation:
   a plaintiff must show that *their* work is the source of a specific set of entries.
   Follow-up research needed on whether mechanistic interpretability tools (e.g. gradient
   attribution, activation patching) can bridge this gap.

2. **Polysemy and the hallucination analysis**: The polysemantic-noise-as-product-defect
   argument (§9 of the primary article) needs quantification. What fraction of hallucinations
   are attributable to polysemantic feature collisions vs. missing training coverage vs.
   attention-head interference? Papers to consult: Elhage et al. (Toy Models of
   Superposition, Anthropic 2022); Geva et al. (Transformer Feed-Forward Layers Are
   Key-Value Memories, EMNLP 2021).

3. **EU Database Directive sui generis right**: The primary article cites Directive 96/9/EC.
   The specific case law on whether AI model weights qualify as a "database" under the
   Directive has not yet been tested in EU courts. Watch for ECJ referrals from national
   courts hearing AI training data cases.

4. **GDPR Right to Erasure operationalisation**: The INSERT INTO EDGES argument for erasure
   feasibility is theoretically grounded but not yet demonstrated for personal data
   specifically. A named individual in training data (e.g. a person mentioned in a news
   article) would need to have their edges located in the vindex and surgically removed.
   Feasibility study needed: can LARQL-class tools identify and delete edges corresponding
   to a specific named person without corrupting the surrounding graph structure?

5. **First Amendment speech-vs-retrieval split**: The §2 of the legal-corpus-connections
   article notes that characterising AI output as database retrieval (vs. speech) has First
   Amendment implications. This is contested. Need to consult *Reno v. ACLU* (1997),
   *Packingham v. North Carolina* (2017), and the emerging case law on AI content moderation.

## Architecture of the HTML Position Paper (for traceability)

The HTML paper served as the primary drafting source. Its structure maps to the DocBook
article sections as follows:

| HTML section | DocBook §01 section |
|---|---|
| Hero / console demo | §2 (LARQL Demonstration) |
| "The position" | §1 (The Position) |
| "LARQL returns the entries" | §2 + §3.1–3.2 |
| "Format is not a defence" | §5 (Format Is Not a Defence) |
| "The proof is in the output" | §4 (The Basis Limitation) |
| "What the model is, legally" | §6 (Legal Classification) |
| "Distribution and operation are database acts" | §7 (Distribution as Database Acts) |
| Sources section | bibliography.bib |

## Deep-Research Workflow: Search Angles Dispatched

Workflow `wf_3d8e52ec-fd6` was dispatched with the following five search angles:
1. Chris Hay LARQL GitHub repos and YouTube presentations
2. Technical papers on transformer/FFN = graph database isomorphism
3. Legal scholarship on mechanistic interpretability and IP/copyright
4. EU/US database directive case law applicability to AI
5. Court decisions and regulatory filings touching LLMs-as-databases theory

When the workflow completes, its verified findings should be used to:
- Confirm or correct the citation to arXiv:2603.20957 (admissions compilation)
- Confirm or correct the citation to arXiv:2601.02671 (follow-on extraction)
- Add any legal scholarship or case law that the workflow surfaces
- Update the bibliography.bib with any new sources

## Relationship to the larql-theory-wt Worktree

The `/home/metavacua/larql-theory-wt` directory (visible in the filesystem) likely contains
LARQL-adjacent theory work. Its contents should be reviewed to avoid duplication and to
incorporate any findings that predate this paper.

# Session Notes — LLM Database Theory Paper

## Provenance

- Primary source: User-authored HTML position paper ("Language models are databases — a position paper
  on LLMs and intellectual property", July 2026).
- Research assistant: Claude Sonnet 4.6 (Anthropic), 2026-07-01.
- Deep-research workflow: `wf_3d8e52ec-fd6` / task `wnb6yvfql` — completed 2026-07-01.
  106 agents, 2,065,445 tokens, 780 tool uses. 25 claims verified; 3 confirmed; 22 refuted.

### Deep-Research Verified Findings

**CONFIRMED (3-0):**
- Geva et al. 2021 (arXiv:2012.14913): FFN layers ARE key-value memories (peer-reviewed, EMNLP 2021)
- Geva et al. 2022 (arXiv:2203.14680): W_K rows = keys; W_V columns = values; output = weighted sum (EMNLP 2022)

**CONFIRMED (2-1, EU jurisdictions):**
- Munich Regional Court I, GEMA v. OpenAI, 42 O 14139/24, 11 Nov 2025: memorisation in weights = unlawful reproduction under UrhG §16
- EP Study 2025 (Nicola Lucchi, PE 774.095): distributing weights with memorised content = prima facie infringement

**REFUTED (1-2):** LARQL vindex/graph-database claim — couldn't be independently verified from GitHub/YouTube alone (not peer-reviewed); the search agents found the repo and documentation but the 3-vote adversarial panel couldn't confirm the specific operational claim from external evidence. NOTE: this reflects the verifiers' inability to run the code, not a finding that the code doesn't work. Direct inspection of the repo source code is required to confirm.

**REFUTED (0-3):** LARQL INSERT INTO EDGES — same caveat as above.

**REFUTED (0-3):** All GDPR Art. 17 direct-application claims; EU Database Directive sui generis for model weights; linear-combination-as-copy; obfuscation irrelevance.

### Additional Sources Surfaced (not previously in bibliography)

- Garcia v. Character Technologies (M.D. Fla., May 2025): strict product liability for AI survives MTD → added as garcia_characterai2025
- EU Product Liability Directive 2024/2853: AI providers = manufacturers → added as eu_pld2024
- arXiv:2503.01630 (LLMs as personal data sources) — cited in legal scholarship; GDPR claims refuted
- UK High Court, Getty Images v. Stability AI, 4 Nov 2025: weights = "purely product of patterns and features, not copies" (UK law only; post-Brexit; contradicts Munich ruling in EU)
- Kluwer Copyright Blog: "Are AI models' weights protected databases?" (blog, not verified)
- arXiv:2507.11128v1: LLM personal data store framing (not yet adversarially confirmed)

## Citation Gaps

- **Cooper et al. 2025** (arXiv:2505.12546): Confirmed to exist; cite verifiable.
- **Follow-on 2026** (arXiv:2601.02671): Listed in HTML position paper; NOT independently
  confirmed by deep-research workflow. Retain in bibliography but mark as unconfirmed.
- **Admissions compilation** (arXiv:2603.20957): Listed in HTML position paper; NOT independently
  confirmed by deep-research workflow. Retain in bibliography but mark as unconfirmed.
- **LARQL INSERT INTO EDGES demo**: From YouTube presentation and LARQL repo README.
  The specific "Feature F8821@L26" numbering in the paper is illustrative of the mechanism;
  actual feature IDs will vary by model and session. LARQL's operational claims scored 1-2
  (vindex) and 0-3 (INSERT INTO EDGES) in adversarial verification — not because the code
  doesn't work, but because the verifiers couldn't run it. Direct `larql-probe`-style
  inspection is needed (see memory: larql-probe-tool).
- **Gemma 3 4B performance claim** ("marginally faster than dense matmul"): From LARQL repo
  documentation and presentations; should be confirmed against LARQL CHANGELOG or benchmark
  data in the repo when citing in litigation contexts.
- **UK counterargument**: Getty Images v. Stability AI (UK High Court, 4 Nov 2025) holds
  weights are "purely product of patterns and features, not copies" — directly contradicts
  Munich ruling. Must be addressed when arguing in common-law jurisdictions. Not fatal
  in EU proceedings; may be persuasive in US courts depending on circuit.

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

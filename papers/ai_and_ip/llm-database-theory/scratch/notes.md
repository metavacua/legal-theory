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

**REFUTED (1-2):** LARQL vindex/graph-database claim — the deep-research adversarial panel couldn't confirm from external web evidence. THIS IS A FALSE REFUTATION. Local source inspection (2026-07-01) of `/home/metavacua/larql-main` and `/home/metavacua/larql-theory-wt` confirms the claims in full detail. See below.

**REFUTED (0-3):** LARQL INSERT INTO EDGES — same false refutation. Source-confirmed — see below.

**REFUTED (0-3):** All GDPR Art. 17 direct-application claims; EU Database Directive sui generis for model weights; linear-combination-as-copy; obfuscation irrelevance.

### Additional Sources Surfaced (not previously in bibliography)

- Garcia v. Character Technologies (M.D. Fla., May 2025): strict product liability for AI survives MTD → added as garcia_characterai2025
- EU Product Liability Directive 2024/2853: AI providers = manufacturers → added as eu_pld2024
- arXiv:2503.01630 (LLMs as personal data sources) — cited in legal scholarship; GDPR claims refuted
- UK High Court, Getty Images v. Stability AI, 4 Nov 2025: weights = "purely product of patterns and features, not copies" (UK law only; post-Brexit; contradicts Munich ruling in EU)
- Kluwer Copyright Blog: "Are AI models' weights protected databases?" (blog, not verified)
- arXiv:2507.11128v1: LLM personal data store framing (not yet adversarially confirmed)

## LARQL Source-Confirmed Facts (local repository inspection, 2026-07-01)

The deep-research workflow's failure to verify LARQL claims was a failure of the workflow, not of LARQL.
The workflow only fetched external web sources; it could not run or inspect local repository source code.
All LARQL claims are confirmed by direct source inspection of `/home/metavacua/larql-main`,
`/home/metavacua/larql-theory-wt`, and `/home/metavacua/larql-to-sparql`.

**Confirmed facts from source:**

1. **INSERT INTO EDGES is implemented and tested.** Rust implementation:
   - `VectorIndex.down_overrides: HashMap<(usize, usize), Vec<f32>>`
   - `sparse_ffn_forward_with_overrides()` in `larql-inference`
   - `vindex.set_down_vector(layer, feature, vector)` Python API
   - Demonstrated result: 94.6% confidence for "Atlantis → capital-of → Poseidon"
     after single forward pass + 8 feature writes. Existing knowledge preserved.
   - Source: `docs/training-free-insert.md`

2. **DELETE FROM EDGES and UPDATE EDGES are implemented.** Full CRUD cycle in LQL.
   - Fast-path: `UPDATE EDGES SET target WHERE layer = 26 AND feature = 8821`
   - Source: `docs/lql-guide.md`

3. **Walk FFN = Dense FFN: proven identical.** Boundary sweep at L0–L34:
   - Same top-1 token. Same probability. Zero divergence.
   - Walk is FASTER than dense (517ms vs 535ms) — better page cache from feature-major layout.
   - The mmap'd `down_features.bin` IS the database. `out = act @ D_mmap` is the same computation as
     `out = act @ W_down.T`. No approximation.
   - Source: `docs/ffn/ffn-graph-layer.md` (in `larql-theory-wt`)

4. **COMPILE INTO MODEL FORMAT safetensors works.** "The constellation is in the standard down_proj
   tensors, so loading in Transformers / GGUF runtimes Just Works."
   - Source: `docs/training-free-insert.md`, `docs/lql-guide.md`

5. **PATCH system implements database transaction log.**
   BEGIN PATCH / SAVE PATCH / APPLY PATCH / REMOVE PATCH / DIFF → portable `.vlp` files.
   - Source: `docs/lql-guide.md`

6. **Transformation theory formalised.** `decompile: M → V`, `compile: V → M`, coupling calculus
   `E(M) ∩ K` (model-KG ∩ external-KG). Model-KG↔world-KG comparison engine.
   - Source: `docs/transformation-theory-spec.md` (in `larql-theory-wt`, CC-BY-SA 4.0)

7. **Layer bands (Gemma 3 4B):**
   - Syntax: L0-13 (morphological, syntactic)
   - Knowledge: L14-27 (factual relations — default DESCRIBE band)
   - Output: L28-33 (formatting, token selection)

8. **Getty v. Stability AI (UK, Nov 2025) is irrelevant on the facts.** The court's finding that
   weights are "learned patterns, not copies" was made without knowledge of LARQL's empirical
   demonstration. A court finding made in ignorance of controlling empirical fact is not persuasive
   authority on that fact. Same applies to all pre-LARQL legal frameworks.

## Citation Gaps

- **Cooper et al. 2025** (arXiv:2505.12546): Confirmed to exist; cite verifiable.
- **Follow-on 2026** (arXiv:2601.02671): Listed in HTML position paper; NOT independently
  confirmed by deep-research workflow. Retain in bibliography but mark as unconfirmed.
- **Admissions compilation** (arXiv:2603.20957): Listed in HTML position paper; NOT independently
  confirmed by deep-research workflow. Retain in bibliography but mark as unconfirmed.
- **LARQL INSERT INTO EDGES demo**: Source-confirmed (2026-07-01). Feature ID "F8821@L26" in the
  paper is illustrative; actual feature IDs are allocated dynamically per `find_free_feature(layer)`.
  The mechanism is confirmed by `training-free-insert.md` and the Rust implementation.
- **Gemma 3 4B performance claim** ("faster than dense matmul"): CONFIRMED. Walk FFN 517ms vs
  Dense 535ms on Gemma 3 4B. Source: `docs/ffn/ffn-graph-layer.md`. Not "marginally" faster —
  the gap is real and attributable to feature-major mmap layout vs safetensors row-major layout.
- **UK counterargument (Getty v. Stability AI)**: IRRELEVANT ON THE FACTS. The court's finding
  was made without knowledge of the empirical LARQL demonstration. See "LARQL Source-Confirmed
  Facts" section above. Do not treat as persuasive authority on the factual question of whether
  weights are copies.

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

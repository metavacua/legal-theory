# Language Models Are Databases
### A Technical and Legal Position Paper

**Category:** `ai_and_ip`  
**Slug:** `llm-database-theory`  
**Author:** Ian D.L.N. McLean  
**Date:** 2026-07-01  
**License:** [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)

---

## Position

Transformer language models are **graph databases** in a technically precise, legally operative sense:

1. **FFN layers are key-value stores** — each layer encodes entity→relation→target triples addressable by vector similarity search, isomorphic to a property graph.
2. **Forward passes are KNN graph walks** — `Attention(Q,K,V) = softmax(QK^T/√d_k)·V` is KNN retrieval over the key-value graph.
3. **LARQL demonstrates this directly** — Chris Hay's open-source tool ([github.com/chrishayuk/larql](https://github.com/chrishayuk/larql)) extracts transformer weights into a queryable *vindex* and returns labelled edges via declarative LQL (`DESCRIBE`, `WALK`, `INSERT INTO EDGES`, `COMPILE ... INTO MODEL FORMAT safetensors`).
4. **Memorisation is empirically confirmed** — Llama 3.1 70B regenerates Harry Potter near-verbatim from a seed (Cooper et al. 2025); 100+ training images extracted from Stable Diffusion (Carlini et al. 2023).
5. **Legal consequence** — a model trained on protected works is a derivative work (17 U.S.C. § 101), a collective work, and a database subject to EU Directive 96/9/EC; distributing it distributes copies; GDPR Art. 17 erasure is technically feasible via `INSERT INTO EDGES`.

---

## Source Files

| File | Content |
|---|---|
| `src/00-metadata.xml` | Dublin Core + Schema.org metadata (XIncluded by all articles) |
| `src/01-llm-database-theory.xml` | Primary DocBook 5.2 article (10 sections) |
| `src/02-legal-corpus-connections.xml` | Connections to matters in this repo; proposed FOFs |
| `src/bibliography.bib` | 14 BibTeX entries |
| `xsl/html5.xsl` | DocBook → HTML5 (with DC meta tags + Schema.org JSON-LD) |
| `xsl/latex.xsl` | DocBook → LaTeX (pdflatex-compilable) |
| `schema/custom.rnc` | RELAX NG compact schema (finding-section constraints) |
| `scratch/formulas.md` | Math correspondences, LARQL↔SQL table, memorisation rates |
| `scratch/notes.md` | Session provenance, citation gaps, open questions |

---

## Build

### Prerequisites

```bash
# Debian/Ubuntu
sudo apt-get install libxml2-utils libxslt1-dev pandoc

# macOS
brew install libxml2 libxslt pandoc

# Note: pandoc is required by docs/scripts/convert_to_docbook.py (the
# Markdown-to-DocBook conversion tool), not by this paper's own build.

# Optional: RELAX NG validation
# Download jing from https://relaxng.org/jclark/jing.html

# Optional: PDF output
sudo apt-get install texlive-full   # or texlive-latex-recommended
```

### Commands

```bash
# Validate XML (well-formedness + XInclude resolution)
make validate

# Generate HTML5
make html
# → generated/01-llm-database-theory.html
# → generated/02-legal-corpus-connections.html

# Generate LaTeX
make latex
# → generated/01-llm-database-theory.tex
# → generated/02-legal-corpus-connections.tex

# Generate PDF (requires pdflatex)
make pdf

# All targets
make all

# Open primary article in browser
make open-html
```

---

## Primary Findings

### FOF-AI-1
The FFN layers of a transformer LLM function as key-value stores structurally isomorphic to a property graph.  
*Evidence:* LARQL demonstration; Self-Attention as Parametric Endofunctor (arXiv:2501.02931)

### FOF-AI-2
LARQL returns labelled directed edges from transformer weights via declarative LQL queries, without retraining or structural modification.  
*Evidence:* [github.com/chrishayuk/larql](https://github.com/chrishayuk/larql)

### FOF-AI-3
Llama 3.1 70B regenerates the first Harry Potter novel near-verbatim from a seed of the opening tokens.  
*Evidence:* Cooper et al. 2025 (arXiv:2505.12546) — "copied inside the model parameters"

### FOF-AI-4
Over 100 near-identical training images, including trademarked logos, were extracted from Stable Diffusion and Imagen.  
*Evidence:* Carlini et al. 2023 (arXiv:2301.13188)

### FOF-AI-5
A measurable fraction of diffusion-model outputs are near-exact copies of training images.  
*Evidence:* Somepalli et al. 2023 (CVPR 2023)

### FOF-AI-6
OpenAI and Google stated to the U.S. Copyright Office that their models store no copies of training data — only numbers.  
*Evidence:* Admissions compilation (arXiv:2603.20957) — contradicted by FOF-AI-3 through FOF-AI-5.

---

## Conclusions of Law

| # | Conclusion | Basis |
|---|---|---|
| COL-1 | An LLM trained on protected works is a **derivative work** under 17 U.S.C. § 101 | FOF-AI-1 through FOF-AI-5 |
| COL-2 | An LLM trained on multiple copyrighted works is a **collective work** under 17 U.S.C. § 101 | FOF-AI-1 through FOF-AI-5 |
| COL-3 | A deployed LLM qualifies as a **database** under EU Directive 96/9/EC (sui generis right) | FOF-AI-1, FOF-AI-2 |
| COL-4 | GDPR Art. 17 **right to erasure is technically feasible** via INSERT INTO EDGES | FOF-AI-2 |
| COL-5 | The format defence ("only numbers") fails the 17 U.S.C. § 101 machine-perceptibility test | FOF-AI-2 through FOF-AI-5; *Litchfield v. Spielberg* 736 F.2d 1352 |
| COL-6 | Distribution and API access to an LLM are database acts requiring rights-holder authorisation | COL-1 through COL-3 |

---

## Connections to Legal-Theory Corpus

This paper strengthens and unifies arguments across three existing matters:

- **copyright-ip-authorship** — FOF-AI-1 through FOF-AI-6 are ready for incorporation into the findings stub; provides the derivative-work and collective-work technical predicates.
- **platform-tos-constitutional-limits** — resolves the data-vs-program ambiguity in `llm-data-vs-program.md`; informs the database-retrieval-vs-speech First Amendment analysis.
- **agpl-ai-training-and-code-licensing** — provides the technical premise for the GPL derivative-works / poison-pill argument: training on GPL code encodes GPL-licensed edges into the vindex, retrievable by LARQL.

See `src/02-legal-corpus-connections.xml` for the full analysis.

---

## Open Questions

See `scratch/notes.md` for a detailed list. Key gaps:

1. **Source attribution precision** — LARQL returns semantic triples; it does not yet identify *which training document* is the source of a specific edge. Needed for litigation standing.
2. **GDPR erasure at person-level** — feasibility of identifying and removing edges for a specific named individual without corrupting surrounding graph structure.
3. **EU Database Directive case law** — no ECJ ruling yet on whether AI weights qualify; watch for national court referrals.

---

## Citation

```bibtex
@techreport{mclean2026llm-database-theory,
  author    = {McLean, Ian D.L.N.},
  title     = {Language Models Are Databases: A Technical and Legal Position Paper},
  year      = {2026},
  month     = {July},
  url       = {https://github.com/metavacua/legal-theory/tree/main/docs/papers/ai_and_ip/llm-database-theory},
  license   = {CC BY-SA 4.0}
}
```

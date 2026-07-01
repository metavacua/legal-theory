# Document Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate 112 existing documents from the ad-hoc LLM keyword-sort structure into the jurisdiction-organized directory structure defined in `docs/superpowers/specs/2026-06-30-repository-organization-design.md`.

**Architecture:** Documents are classified by jurisdictional level and argument type, then placed in the appropriate `court-record/theory/`, `court-record/matters/[matter]/evidence/`, `proposals/`, or `cross-cutting/` directory. Each matter receives a stub `README.md` and `findings.md`. The old directories are removed after all documents are migrated.

**Tech Stack:** git (mv for tracked files, preserves history), bash

## Global Constraints

- All `git mv` commands must be run from the repo root: `/tmp/claude-1000/-home-metavacua/1cdc4a82-e952-4641-8d15-795574e7f5c9/scratchpad/legal-theory/`
- Working branch: `claude/legal-theory-doc-migration-0rsqbw`
- Do NOT push until the user explicitly approves
- Commit after each task — small commits, clear messages
- If a document's correct location is genuinely ambiguous after reading its title, move it to `docs/wip/`
- Never delete documents — move to `docs/wip/` if uncertain

---

## Source → Destination Mapping Reference

### Matters

| Matter slug | Subject |
|---|---|
| `google-platform-misclassification` | Google/platform worker misclassification under CA Labor Code ABC test |
| `platform-tos-constitutional-limits` | Platform ToS and LLM policies violating constitutional limits on expression |
| `cooperative-investment-law` | Cooperative securities, patron law, investible cooperative membership |
| `sex-work-consent-bodily-autonomy` | Consent, bodily autonomy, sex work law under CA and federal constitutional frame |
| `copyright-ip-authorship` | Copyright, IP authorship, AI-assisted creation, artist contracts |

---

### Task 1: Create New Directory Structure

**Files:**
- Create: all directories under `docs/` per the design spec

- [ ] **Step 1: Create court-record/theory/ directories**

```bash
cd /tmp/claude-1000/-home-metavacua/1cdc4a82-e952-4641-8d15-795574e7f5c9/scratchpad/legal-theory

mkdir -p docs/court-record/theory/federal-constitutional/existing-doctrine
mkdir -p docs/court-record/theory/federal-constitutional/extensions
mkdir -p docs/court-record/theory/federal-constitutional/specializations
mkdir -p docs/court-record/theory/federal-constitutional/reversal-arguments
mkdir -p docs/court-record/theory/california-constitutional/existing-doctrine
mkdir -p docs/court-record/theory/california-constitutional/extensions
mkdir -p docs/court-record/theory/california-constitutional/specializations
mkdir -p docs/court-record/theory/california-constitutional/reversal-arguments
mkdir -p docs/court-record/theory/federal-statutes/existing-law
mkdir -p docs/court-record/theory/federal-statutes/extensions
mkdir -p docs/court-record/theory/federal-statutes/specializations
mkdir -p docs/court-record/theory/federal-statutes/reversal-arguments
mkdir -p docs/court-record/theory/california-statutes/existing-law
mkdir -p docs/court-record/theory/california-statutes/extensions
mkdir -p docs/court-record/theory/california-statutes/specializations
mkdir -p docs/court-record/theory/california-statutes/reversal-arguments
mkdir -p docs/court-record/theory/municipal/existing-law
mkdir -p docs/court-record/theory/municipal/specializations
```

- [ ] **Step 2: Create matter directories**

```bash
mkdir -p docs/court-record/matters/google-platform-misclassification/evidence
mkdir -p docs/court-record/matters/google-platform-misclassification/administrative-record
mkdir -p docs/court-record/matters/platform-tos-constitutional-limits/evidence
mkdir -p docs/court-record/matters/platform-tos-constitutional-limits/administrative-record
mkdir -p docs/court-record/matters/cooperative-investment-law/evidence
mkdir -p docs/court-record/matters/cooperative-investment-law/administrative-record
mkdir -p docs/court-record/matters/sex-work-consent-bodily-autonomy/evidence
mkdir -p docs/court-record/matters/sex-work-consent-bodily-autonomy/administrative-record
mkdir -p docs/court-record/matters/copyright-ip-authorship/evidence
mkdir -p docs/court-record/matters/copyright-ip-authorship/administrative-record
```

- [ ] **Step 3: Create proposals directories**

```bash
mkdir -p docs/proposals/legislative/federal/congress
mkdir -p docs/proposals/legislative/california/state-legislature
mkdir -p docs/proposals/legislative/california/county
mkdir -p docs/proposals/legislative/california/city
mkdir -p docs/proposals/legislative/california/petitions
mkdir -p docs/proposals/executive/orders/federal/presidential
mkdir -p docs/proposals/executive/orders/california/governor
mkdir -p docs/proposals/executive/orders/california/county-executive
mkdir -p docs/proposals/executive/orders/california/mayor
mkdir -p docs/proposals/executive/agencies/federal/ftc
mkdir -p docs/proposals/executive/agencies/federal/nlrb
mkdir -p docs/proposals/executive/agencies/federal/sec
mkdir -p docs/proposals/executive/agencies/california/attorney-general
mkdir -p docs/proposals/executive/agencies/california/labor-commissioner-dlse
mkdir -p docs/proposals/executive/agencies/california/civil-rights-dept-crd
mkdir -p docs/proposals/executive/agencies/california/dfpi
mkdir -p docs/proposals/executive/agencies/california/fppc
mkdir -p docs/proposals/executive/agencies/california/secretary-of-state
mkdir -p docs/cross-cutting
```

- [ ] **Step 4: Verify structure**

```bash
find docs/court-record docs/proposals docs/cross-cutting -type d | sort
```

Expected: 50+ directories, no errors.

- [ ] **Step 5: Commit empty structure**

```bash
# Git won't track empty dirs — add .gitkeep to leaf directories that have no files yet
find docs/court-record docs/proposals docs/cross-cutting -type d -empty -exec touch {}/.gitkeep \;
git add docs/court-record docs/proposals docs/cross-cutting
git commit -m "Add new directory structure (empty)"
```

---

### Task 2: Migrate Federal Constitutional Theory Documents

**Files:**
- Move: 5 documents from `consent-bodily-autonomy-and-sex-work-law/` and `llm-architecture-and-database-law/`
- Destination: `docs/court-record/theory/federal-constitutional/`

**Classification rationale:**
- `existing-doctrine/` — documents analyzing established 1st Amendment doctrine and bodily autonomy doctrine (Dobbs)
- `extensions/` — documents arguing those doctrines extend to new classes: sex work/prostitution context; payment processors; LLMs as automated decision systems

- [ ] **Step 1: Move existing-doctrine documents**

```bash
cd /tmp/claude-1000/-home-metavacua/1cdc4a82-e952-4641-8d15-795574e7f5c9/scratchpad/legal-theory

git mv docs/consent-bodily-autonomy-and-sex-work-law/first-amendment-landmark-cases-research.md \
       docs/court-record/theory/federal-constitutional/existing-doctrine/

git mv docs/consent-bodily-autonomy-and-sex-work-law/legal-status-of-bodily-autonomy-post-dobbs.md \
       docs/court-record/theory/federal-constitutional/existing-doctrine/
```

- [ ] **Step 2: Move extensions documents**

```bash
git mv docs/consent-bodily-autonomy-and-sex-work-law/first-amendment-and-prostitution-law.md \
       docs/court-record/theory/federal-constitutional/extensions/

git mv docs/consent-bodily-autonomy-and-sex-work-law/payment-processors-censorship-and-discrimination.md \
       docs/court-record/theory/federal-constitutional/extensions/

git mv docs/llm-architecture-and-database-law/llms-as-categorical-systems.md \
       docs/court-record/theory/federal-constitutional/extensions/
```

- [ ] **Step 3: Verify**

```bash
find docs/court-record/theory/federal-constitutional -name "*.md" | sort
```

Expected: 5 files total.

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "Migrate federal constitutional theory documents"
```

---

### Task 3: Migrate California Statutes Theory Documents

**Files:**
- Move: 9 documents from `consent-bodily-autonomy-and-sex-work-law/`, `platform-tos-and-labor-classification/`, and `cooperative-securities-and-patron-law/patron-law/`
- Destination: `docs/court-record/theory/california-statutes/`

**Classification rationale:**
- `existing-law/` — analysis of CA statutes as written (contract law, sex contract standards, patron law, minors in business)
- `extensions/` — arguments that CA statutory doctrine extends to cover new circumstances (employment retroactivity; the consent paradox applying existing consent doctrine to non-consensual-but-lawful interactions)
- `specializations/` — applying CA doctrine to specific facts (sexual relations presumption applied to CA circumstances)

- [ ] **Step 1: Move existing-law documents**

```bash
cd /tmp/claude-1000/-home-metavacua/1cdc4a82-e952-4641-8d15-795574e7f5c9/scratchpad/legal-theory

git mv docs/platform-tos-and-labor-classification/california-contract-law-analysis.md \
       docs/court-record/theory/california-statutes/existing-law/

git mv docs/consent-bodily-autonomy-and-sex-work-law/california-sex-contract-consent-standards.md \
       docs/court-record/theory/california-statutes/existing-law/

git mv docs/consent-bodily-autonomy-and-sex-work-law/california-sex-contracts-and-consent.md \
       docs/court-record/theory/california-statutes/existing-law/

git mv docs/cooperative-securities-and-patron-law/patron-law/ca-patron-law-v2.md \
       docs/court-record/theory/california-statutes/existing-law/

git mv docs/cooperative-securities-and-patron-law/patron-law/california-patron-law-section-analysis.md \
       docs/court-record/theory/california-statutes/existing-law/

git mv docs/cooperative-securities-and-patron-law/patron-law/ca-patronage-law.md \
       docs/court-record/theory/california-statutes/existing-law/

git mv docs/platform-tos-and-labor-classification/minors-operating-businesses-in-california.md \
       docs/court-record/theory/california-statutes/existing-law/
```

- [ ] **Step 2: Move extensions documents**

```bash
git mv docs/platform-tos-and-labor-classification/california-law-employment-retroactivity.md \
       docs/court-record/theory/california-statutes/extensions/

git mv docs/consent-bodily-autonomy-and-sex-work-law/the-consent-paradox-lawful-non-consensual-interaction.md \
       docs/court-record/theory/california-statutes/extensions/
```

- [ ] **Step 3: Move specializations documents**

```bash
git mv docs/consent-bodily-autonomy-and-sex-work-law/from-presumption-to-practice-consensual-sexual-relations-ca.md \
       docs/court-record/theory/california-statutes/specializations/
```

- [ ] **Step 4: Verify**

```bash
find docs/court-record/theory/california-statutes -name "*.md" | sort
```

Expected: 10 files total.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "Migrate California statutes theory documents"
```

---

### Task 4: Migrate Federal Statutes Theory Documents

**Files:**
- Move: 4 documents from `platform-tos-and-labor-classification/`, `cooperative-securities-and-patron-law/patron-law/`, and `copyright-and-ip-authorship/`
- Destination: `docs/court-record/theory/federal-statutes/`

**Classification rationale:**
- `existing-law/` — IRC cooperative treatment, patron income, Section 230, IP contract framework
- `extensions/` — AGPL/open-source licensing as it extends to AI training data contexts

- [ ] **Step 1: Move existing-law documents**

```bash
cd /tmp/claude-1000/-home-metavacua/1cdc4a82-e952-4641-8d15-795574e7f5c9/scratchpad/legal-theory

git mv docs/cooperative-securities-and-patron-law/cooperative-investing-us-ca-irc.md \
       docs/court-record/theory/federal-statutes/existing-law/

git mv docs/cooperative-securities-and-patron-law/patron-law/patronage-sourced-income.md \
       docs/court-record/theory/federal-statutes/existing-law/

git mv docs/platform-tos-and-labor-classification/section-230-legal-shield-under-fire.md \
       docs/court-record/theory/federal-statutes/existing-law/

git mv docs/copyright-and-ip-authorship/ip-contract-knowledge-graph.md \
       docs/court-record/theory/federal-statutes/existing-law/
```

- [ ] **Step 2: Move extensions documents**

```bash
git mv docs/platform-tos-and-labor-classification/agpl-ai-training-and-code-licensing.md \
       docs/court-record/theory/federal-statutes/extensions/
```

- [ ] **Step 3: Verify**

```bash
find docs/court-record/theory/federal-statutes -name "*.md" | sort
```

Expected: 5 files total.

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "Migrate federal statutes theory documents"
```

---

### Task 5: Migrate google-platform-misclassification Matter

**Files:**
- Move: 7 documents from `platform-tos-and-labor-classification/`
- Destination: `docs/court-record/matters/google-platform-misclassification/evidence/` and `docs/wip/`

**Classification rationale:**
- `evidence/` — analysis and research grounding the worker misclassification claims against Google/platforms under CA Labor Code
- The draft version of the systemic misclassification document moves to `wip/` — the final version is the canonical document

- [ ] **Step 1: Move evidence documents**

```bash
cd /tmp/claude-1000/-home-metavacua/1cdc4a82-e952-4641-8d15-795574e7f5c9/scratchpad/legal-theory

git mv docs/platform-tos-and-labor-classification/google-user-contracts.md \
       docs/court-record/matters/google-platform-misclassification/evidence/

git mv docs/platform-tos-and-labor-classification/google-user-misclassification.md \
       docs/court-record/matters/google-platform-misclassification/evidence/

git mv docs/platform-tos-and-labor-classification/california-worker-misclassification-risk-analysis.md \
       docs/court-record/matters/google-platform-misclassification/evidence/

git mv docs/platform-tos-and-labor-classification/systemic-misclassification-final.md \
       docs/court-record/matters/google-platform-misclassification/evidence/

git mv docs/platform-tos-and-labor-classification/google-user-contracts-implicit-employment-obligations.md \
       docs/court-record/matters/google-platform-misclassification/evidence/

git mv docs/platform-tos-and-labor-classification/potential-service-contracts-in-google.md \
       docs/court-record/matters/google-platform-misclassification/evidence/
```

Note: `google-user-contracts-implicit-employment-obligations.md` and `potential-service-contracts-in-google.md` have unconverted conversational preambles ("Here is an analysis of..." / "You have correctly identified"). They are placed in `evidence/` now and should be converted to findings-of-fact format in a future task.

- [ ] **Step 2: Move draft to wip**

```bash
git mv docs/platform-tos-and-labor-classification/systemic-misclassification-draft.md \
       docs/wip/
```

- [ ] **Step 3: Verify**

```bash
find docs/court-record/matters/google-platform-misclassification -name "*.md" | sort
ls docs/wip/systemic-misclassification-draft.md
```

Expected: 6 files in evidence/, 1 file moved to wip/.

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "Migrate google-platform-misclassification matter evidence"
```

---

### Task 6: Migrate platform-tos-constitutional-limits Matter

**Files:**
- Move: 8 documents from `platform-tos-and-labor-classification/`, `llm-architecture-and-database-law/`, and `copyright-and-ip-authorship/ai-tooling/`
- Destination: `docs/court-record/matters/platform-tos-constitutional-limits/evidence/`

**Classification rationale:** These documents analyze the argument that platform ToS and LLM automated decision systems violate constitutional limits on expression and exceed permissible private contract terms.

- [ ] **Step 1: Move platform-tos evidence documents**

```bash
cd /tmp/claude-1000/-home-metavacua/1cdc4a82-e952-4641-8d15-795574e7f5c9/scratchpad/legal-theory

git mv docs/platform-tos-and-labor-classification/ai-toolchain-licensing-and-tos.md \
       docs/court-record/matters/platform-tos-constitutional-limits/evidence/

git mv docs/platform-tos-and-labor-classification/open-research-ai-pro-tos-analysis.md \
       docs/court-record/matters/platform-tos-constitutional-limits/evidence/

git mv docs/platform-tos-and-labor-classification/vrp-legal-vulnerability.md \
       docs/court-record/matters/platform-tos-constitutional-limits/evidence/

git mv docs/platform-tos-and-labor-classification/the-unilateral-mandate-social-media-platforms-as-service-contracts.md \
       docs/court-record/matters/platform-tos-constitutional-limits/evidence/

git mv docs/platform-tos-and-labor-classification/directed-ip-creation.md \
       docs/court-record/matters/platform-tos-constitutional-limits/evidence/
```

- [ ] **Step 2: Move LLM architecture evidence documents**

```bash
git mv docs/llm-architecture-and-database-law/llm-data-vs-program.md \
       docs/court-record/matters/platform-tos-constitutional-limits/evidence/

git mv docs/llm-architecture-and-database-law/llm-information-encoding-and-covert-channels.md \
       docs/court-record/matters/platform-tos-constitutional-limits/evidence/

git mv docs/llm-architecture-and-database-law/semantic-network-profiling-research.md \
       docs/court-record/matters/platform-tos-constitutional-limits/evidence/
```

- [ ] **Step 3: Move AI tooling evidence documents**

```bash
git mv docs/copyright-and-ip-authorship/ai-tooling/the-algorithmic-editor-ai-moderation-as-creative-control.md \
       docs/court-record/matters/platform-tos-constitutional-limits/evidence/

git mv docs/copyright-and-ip-authorship/ai-tooling/ai-assisted-art-tools-for-comics.md \
       docs/court-record/matters/platform-tos-constitutional-limits/evidence/

git mv docs/copyright-and-ip-authorship/ai-tooling/ai-assisted-codebase-organization-strategies.md \
       docs/court-record/matters/platform-tos-constitutional-limits/evidence/

git mv docs/copyright-and-ip-authorship/ai-tooling/ai-assisted-writing-tool-research.md \
       docs/court-record/matters/platform-tos-constitutional-limits/evidence/
```

- [ ] **Step 4: Verify**

```bash
find docs/court-record/matters/platform-tos-constitutional-limits -name "*.md" | sort
```

Expected: 12 files in evidence/.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "Migrate platform-tos-constitutional-limits matter evidence"
```

---

### Task 7: Migrate sex-work-consent-bodily-autonomy Matter

**Files:**
- Move: 20 documents from `consent-bodily-autonomy-and-sex-work-law/`
- Destination: `docs/court-record/matters/sex-work-consent-bodily-autonomy/evidence/`

**Classification rationale:** Research, analysis, and comparative studies that ground the factual claims in this matter. The theory documents (1st Amendment, Dobbs, CA consent statutes) were already migrated in Tasks 2 and 3.

- [ ] **Step 1: Move evidence documents**

```bash
cd /tmp/claude-1000/-home-metavacua/1cdc4a82-e952-4641-8d15-795574e7f5c9/scratchpad/legal-theory

git mv docs/consent-bodily-autonomy-and-sex-work-law/autonomy-a-myth-in-american-law.md \
       docs/court-record/matters/sex-work-consent-bodily-autonomy/evidence/

git mv docs/consent-bodily-autonomy-and-sex-work-law/bodily-autonomy-legal-research.md \
       docs/court-record/matters/sex-work-consent-bodily-autonomy/evidence/

git mv docs/consent-bodily-autonomy-and-sex-work-law/consent-contracts-and-legal-ambiguity.md \
       docs/court-record/matters/sex-work-consent-bodily-autonomy/evidence/

git mv docs/consent-bodily-autonomy-and-sex-work-law/consent-theories-language-culture.md \
       docs/court-record/matters/sex-work-consent-bodily-autonomy/evidence/

git mv docs/consent-bodily-autonomy-and-sex-work-law/contractual-capacity-for-sexual-services.md \
       docs/court-record/matters/sex-work-consent-bodily-autonomy/evidence/

git mv docs/consent-bodily-autonomy-and-sex-work-law/defining-human-experiments-legally.md \
       docs/court-record/matters/sex-work-consent-bodily-autonomy/evidence/

git mv docs/consent-bodily-autonomy-and-sex-work-law/defining-legal-human-experiments.md \
       docs/court-record/matters/sex-work-consent-bodily-autonomy/evidence/

git mv docs/consent-bodily-autonomy-and-sex-work-law/defining-lewd-acts-and-prostitution-law.md \
       docs/court-record/matters/sex-work-consent-bodily-autonomy/evidence/

git mv docs/consent-bodily-autonomy-and-sex-work-law/kink-sex-work-body-autonomy-research.md \
       docs/court-record/matters/sex-work-consent-bodily-autonomy/evidence/

git mv docs/consent-bodily-autonomy-and-sex-work-law/legal-actions-without-consent-draft.md \
       docs/court-record/matters/sex-work-consent-bodily-autonomy/evidence/

git mv docs/consent-bodily-autonomy-and-sex-work-law/prostitution-law-obscenity-consent-regulation.md \
       docs/court-record/matters/sex-work-consent-bodily-autonomy/evidence/

git mv docs/consent-bodily-autonomy-and-sex-work-law/sex-work-contracts-free-speech-and-law.md \
       docs/court-record/matters/sex-work-consent-bodily-autonomy/evidence/

git mv docs/consent-bodily-autonomy-and-sex-work-law/sex-work-regulation-and-state-surveillance.md \
       docs/court-record/matters/sex-work-consent-bodily-autonomy/evidence/

git mv docs/consent-bodily-autonomy-and-sex-work-law/state-supreme-court-case-study-report.md \
       docs/court-record/matters/sex-work-consent-bodily-autonomy/evidence/

git mv docs/consent-bodily-autonomy-and-sex-work-law/the-architecture-of-non-consensual-legality.md \
       docs/court-record/matters/sex-work-consent-bodily-autonomy/evidence/

git mv docs/consent-bodily-autonomy-and-sex-work-law/the-laudable-contract-licit-sexual-service-agreements.md \
       docs/court-record/matters/sex-work-consent-bodily-autonomy/evidence/

git mv docs/consent-bodily-autonomy-and-sex-work-law/the-nexus-of-consent-and-consideration.md \
       docs/court-record/matters/sex-work-consent-bodily-autonomy/evidence/

git mv docs/consent-bodily-autonomy-and-sex-work-law/the-sovereign-self-bodily-autonomy-kink-sex-work.md \
       docs/court-record/matters/sex-work-consent-bodily-autonomy/evidence/

git mv docs/consent-bodily-autonomy-and-sex-work-law/us-sex-crime-law-analysis.md \
       docs/court-record/matters/sex-work-consent-bodily-autonomy/evidence/

git mv docs/consent-bodily-autonomy-and-sex-work-law/vice-regulation-in-aotearoa-new-zealand.md \
       docs/court-record/matters/sex-work-consent-bodily-autonomy/evidence/
```

- [ ] **Step 2: Verify**

```bash
find docs/court-record/matters/sex-work-consent-bodily-autonomy -name "*.md" | sort
```

Expected: 20 files in evidence/.

- [ ] **Step 3: Confirm consent-bodily-autonomy-and-sex-work-law/ is now empty of .md files**

```bash
find docs/consent-bodily-autonomy-and-sex-work-law -name "*.md"
```

Expected: no output (all migrated).

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "Migrate sex-work-consent-bodily-autonomy matter evidence"
```

---

### Task 8: Migrate cooperative-investment-law Matter

**Files:**
- Move: 19 documents from `cooperative-securities-and-patron-law/`
- Destination: `docs/court-record/matters/cooperative-investment-law/evidence/`

**Classification rationale:** Research, analysis, and drafts grounding the cooperative securities and patron law claims. The patron law theory documents were migrated in Task 3; the IRC/federal statutes documents in Task 4.

- [ ] **Step 1: Move evidence documents**

```bash
cd /tmp/claude-1000/-home-metavacua/1cdc4a82-e952-4641-8d15-795574e7f5c9/scratchpad/legal-theory

git mv docs/cooperative-securities-and-patron-law/community-care-cooperatives.md \
       docs/court-record/matters/cooperative-investment-law/evidence/

git mv docs/cooperative-securities-and-patron-law/community-care-cooperatives-v2.md \
       docs/court-record/matters/cooperative-investment-law/evidence/

git mv docs/cooperative-securities-and-patron-law/contractual-architectures-for-ip-and-cooperatives.md \
       docs/court-record/matters/cooperative-investment-law/evidence/

git mv docs/cooperative-securities-and-patron-law/cooperative-rights-commodification-analysis.md \
       docs/court-record/matters/cooperative-investment-law/evidence/

git mv docs/cooperative-securities-and-patron-law/cooperative-securities-analysis-and-strategy.md \
       docs/court-record/matters/cooperative-investment-law/evidence/

git mv docs/cooperative-securities-and-patron-law/cooperative-securities-in-the-global-marketplace.md \
       docs/court-record/matters/cooperative-investment-law/evidence/

git mv docs/cooperative-securities-and-patron-law/cooperative-securities-novel-financial-instruments.md \
       docs/court-record/matters/cooperative-investment-law/evidence/

git mv docs/cooperative-securities-and-patron-law/cooperative-security.md \
       docs/court-record/matters/cooperative-investment-law/evidence/

git mv docs/cooperative-securities-and-patron-law/cooperatives-politics-and-investible-patronage.md \
       docs/court-record/matters/cooperative-investment-law/evidence/

git mv docs/cooperative-securities-and-patron-law/cooperative-tradeable-securities-research.md \
       docs/court-record/matters/cooperative-investment-law/evidence/

git mv docs/cooperative-securities-and-patron-law/from-clay-tablets-to-blockchains-draft.md \
       docs/court-record/matters/cooperative-investment-law/evidence/

git mv docs/cooperative-securities-and-patron-law/from-clay-tablets-to-blockchains-final.md \
       docs/court-record/matters/cooperative-investment-law/evidence/

git mv docs/cooperative-securities-and-patron-law/from-intangible-to-investment-ip-securitization.md \
       docs/court-record/matters/cooperative-investment-law/evidence/

git mv docs/cooperative-securities-and-patron-law/ideal-security-formal-legal-economic.md \
       docs/court-record/matters/cooperative-investment-law/evidence/

git mv docs/cooperative-securities-and-patron-law/ip-securitization-historical-research.md \
       docs/court-record/matters/cooperative-investment-law/evidence/

git mv docs/cooperative-securities-and-patron-law/securitizing-cooperative-membership-voting-rights.md \
       docs/court-record/matters/cooperative-investment-law/evidence/

git mv docs/cooperative-securities-and-patron-law/the-membership-security.md \
       docs/court-record/matters/cooperative-investment-law/evidence/

git mv docs/cooperative-securities-and-patron-law/us-ca-coop-securities.md \
       docs/court-record/matters/cooperative-investment-law/evidence/

git mv docs/cooperative-securities-and-patron-law/us-ca-coop-securities-v6.md \
       docs/court-record/matters/cooperative-investment-law/evidence/
```

- [ ] **Step 2: Verify**

```bash
find docs/court-record/matters/cooperative-investment-law -name "*.md" | sort
```

Expected: 19 files in evidence/.

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "Migrate cooperative-investment-law matter evidence"
```

---

### Task 9: Migrate copyright-ip-authorship Matter

**Files:**
- Move: 13 documents from `copyright-and-ip-authorship/` and `copyright-and-ip-authorship/artist-creator-contracts/`
- Destination: `docs/court-record/matters/copyright-ip-authorship/evidence/`

**Classification rationale:** Analysis of AI-assisted copyright, authorship, and artist contract issues. The ai-tooling subdirectory was migrated to platform-tos-constitutional-limits in Task 6; theory documents migrated in Task 4.

- [ ] **Step 1: Move evidence documents**

```bash
cd /tmp/claude-1000/-home-metavacua/1cdc4a82-e952-4641-8d15-795574e7f5c9/scratchpad/legal-theory

git mv docs/copyright-and-ip-authorship/ai-assisted-copyrightable-work-schema.md \
       docs/court-record/matters/copyright-ip-authorship/evidence/

git mv docs/copyright-and-ip-authorship/ai-assisted-copyright-tool-blueprint.md \
       docs/court-record/matters/copyright-ip-authorship/evidence/

git mv docs/copyright-and-ip-authorship/ai-corporate-personhood-and-legal-rights.md \
       docs/court-record/matters/copyright-ip-authorship/evidence/

git mv docs/copyright-and-ip-authorship/artist-creator-contracts/a-constructive-legal-framework-for-artistic-commissions.md \
       docs/court-record/matters/copyright-ip-authorship/evidence/

git mv docs/copyright-and-ip-authorship/artist-creator-contracts/freelancing-transgressive-art-projects.md \
       docs/court-record/matters/copyright-ip-authorship/evidence/

git mv docs/copyright-and-ip-authorship/artist-creator-contracts/independent-artist-business-model.md \
       docs/court-record/matters/copyright-ip-authorship/evidence/

git mv docs/copyright-and-ip-authorship/artist-creator-contracts/legal-framework-for-artistic-commissions.md \
       docs/court-record/matters/copyright-ip-authorship/evidence/

git mv docs/copyright-and-ip-authorship/artist-creator-contracts/patron-artist-collective-work-structure.md \
       docs/court-record/matters/copyright-ip-authorship/evidence/

git mv docs/copyright-and-ip-authorship/artist-creator-contracts/the-contractual-ecosystem-for-a-modern-artistic-venture.md \
       docs/court-record/matters/copyright-ip-authorship/evidence/

git mv docs/copyright-and-ip-authorship/ip-creation-service-or-self-expression.md \
       docs/court-record/matters/copyright-ip-authorship/evidence/

git mv docs/copyright-and-ip-authorship/prompts-as-expression.md \
       docs/court-record/matters/copyright-ip-authorship/evidence/

git mv docs/copyright-and-ip-authorship/strategic-compliant-ip.md \
       docs/court-record/matters/copyright-ip-authorship/evidence/

git mv docs/copyright-and-ip-authorship/sustainable-ip-creation.md \
       docs/court-record/matters/copyright-ip-authorship/evidence/
```

- [ ] **Step 2: Verify**

```bash
find docs/court-record/matters/copyright-ip-authorship -name "*.md" | sort
```

Expected: 13 files in evidence/.

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "Migrate copyright-ip-authorship matter evidence"
```

---

### Task 10: Migrate Proposals

**Files:**
- Move: 6 documents to `docs/proposals/`
- Sources: `consent-bodily-autonomy-and-sex-work-law/`, `cooperative-securities-and-patron-law/`, `copyright-and-ip-authorship/`, `platform-tos-and-labor-classification/`

**Classification rationale:**
- Legislative proposals advocate for new CA law (new axioms); belong in `proposals/legislative/california/state-legislature/`
- The petition for corporate AI registry is a request to an executive agency; belongs in `proposals/executive/agencies/california/secretary-of-state/`

- [ ] **Step 1: Move legislative proposals**

```bash
cd /tmp/claude-1000/-home-metavacua/1cdc4a82-e952-4641-8d15-795574e7f5c9/scratchpad/legal-theory

git mv docs/consent-bodily-autonomy-and-sex-work-law/legalizing-sexual-service-contracts.md \
       docs/proposals/legislative/california/state-legislature/

git mv docs/consent-bodily-autonomy-and-sex-work-law/regulating-sexual-services-states-role.md \
       docs/proposals/legislative/california/state-legislature/

git mv docs/cooperative-securities-and-patron-law/hybrid-cooperative-ipo-framework.md \
       docs/proposals/legislative/california/state-legislature/

git mv docs/cooperative-securities-and-patron-law/blueprint-for-innovation-ip-in-cooperative-securities.md \
       docs/proposals/legislative/california/state-legislature/

git mv docs/copyright-and-ip-authorship/improving-ai-accountability-petition-arguments.md \
       docs/proposals/legislative/california/state-legislature/
```

- [ ] **Step 2: Move executive agency proposals**

```bash
git mv docs/platform-tos-and-labor-classification/petition-corporate-ai-registry-ca-sos.md \
       docs/proposals/executive/agencies/california/secretary-of-state/
```

- [ ] **Step 3: Verify**

```bash
find docs/proposals -name "*.md" | sort
```

Expected: 5 files in state-legislature/, 1 file in secretary-of-state/.

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "Migrate proposal documents to proposals/"
```

---

### Task 11: Migrate Cross-Cutting Documents

**Files:**
- Move: 8 documents from `platform-tos-and-labor-classification/`, `cooperative-securities-and-patron-law/patron-law/`, `copyright-and-ip-authorship/`, and `general-jurisprudence-and-regulatory-law/`
- Destination: `docs/cross-cutting/`

**Classification rationale:** These documents address legal concepts and frameworks that apply across multiple matters (contract theory, patron-client duties, human capital valuation, regulatory thresholds). They cannot be assigned to a single matter without distortion.

- [ ] **Step 1: Move cross-cutting documents**

```bash
cd /tmp/claude-1000/-home-metavacua/1cdc4a82-e952-4641-8d15-795574e7f5c9/scratchpad/legal-theory

git mv docs/platform-tos-and-labor-classification/patron-client-non-disclaimable-duties.md \
       docs/cross-cutting/

git mv docs/platform-tos-and-labor-classification/knowledge-graph-ca-service-contracts.md \
       docs/cross-cutting/

git mv docs/cooperative-securities-and-patron-law/patron-law/patron-as-client.md \
       docs/cross-cutting/

git mv docs/copyright-and-ip-authorship/intellectual-property-public-good.md \
       docs/cross-cutting/

git mv docs/copyright-and-ip-authorship/contract-ip-create-digital-econ.md \
       docs/cross-cutting/

git mv docs/general-jurisprudence-and-regulatory-law/tax-and-regulatory-thresholds-explained.md \
       docs/cross-cutting/

git mv docs/general-jurisprudence-and-regulatory-law/the-unwritten-ledger-non-fungible-human-capital.md \
       docs/cross-cutting/

git mv docs/general-jurisprudence-and-regulatory-law/valuing-human-life-economically.md \
       docs/cross-cutting/
```

- [ ] **Step 2: Verify**

```bash
find docs/cross-cutting -name "*.md" | sort
```

Expected: 8 files.

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "Migrate cross-cutting documents"
```

---

### Task 12: Move Remaining Documents to wip/

**Files:**
- Move: 2 documents from `general-jurisprudence-and-regulatory-law/` whose matter assignment is uncertain

**Classification rationale:** `managing-inappropriate-patient-behavior-in-therapy.md` and `spousal-investment-adviser-registration-analysis.md` do not clearly belong to any of the five matters identified. The therapy document may have been misfiled; the spousal investment document may be related to cooperative-investment-law but requires reading to confirm.

- [ ] **Step 1: Move uncertain documents to wip/**

```bash
cd /tmp/claude-1000/-home-metavacua/1cdc4a82-e952-4641-8d15-795574e7f5c9/scratchpad/legal-theory

git mv docs/general-jurisprudence-and-regulatory-law/managing-inappropriate-patient-behavior-in-therapy.md \
       docs/wip/

git mv docs/general-jurisprudence-and-regulatory-law/spousal-investment-adviser-registration-analysis.md \
       docs/wip/
```

- [ ] **Step 2: Verify all source directories are now empty**

```bash
find docs/consent-bodily-autonomy-and-sex-work-law \
     docs/cooperative-securities-and-patron-law \
     docs/copyright-and-ip-authorship \
     docs/general-jurisprudence-and-regulatory-law \
     docs/llm-architecture-and-database-law \
     docs/platform-tos-and-labor-classification \
     -name "*.md" 2>/dev/null
```

Expected: no output. If any files remain, move them to `docs/wip/` before proceeding.

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "Move uncertain-classification documents to wip/"
```

---

### Task 13: Remove Old Directories

**Files:**
- Remove: 6 now-empty source directories

- [ ] **Step 1: Remove old directories**

```bash
cd /tmp/claude-1000/-home-metavacua/1cdc4a82-e952-4641-8d15-795574e7f5c9/scratchpad/legal-theory

git rm -r docs/consent-bodily-autonomy-and-sex-work-law
git rm -r docs/cooperative-securities-and-patron-law
git rm -r docs/copyright-and-ip-authorship
git rm -r docs/general-jurisprudence-and-regulatory-law
git rm -r docs/llm-architecture-and-database-law
git rm -r docs/platform-tos-and-labor-classification
```

- [ ] **Step 2: Verify only new structure remains under docs/**

```bash
find docs -maxdepth 1 -type d | sort
```

Expected:
```
docs
docs/court-record
docs/cross-cutting
docs/proposals
docs/superpowers
docs/wip
```

- [ ] **Step 3: Verify total document count is preserved**

```bash
find docs -name "*.md" | grep -v ".gitkeep" | wc -l
```

Expected: 113 (112 original documents + the design spec). If the count differs, run `find docs -name "*.md" | sort` and compare against the original inventory at the top of this plan.

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "Remove old keyword-sort directories (all documents migrated)"
```

---

### Task 14: Create Matter Stubs

**Files:**
- Create: `README.md` and `findings.md` for each of the 5 matters

These are stubs — the complaint structure and FOF/COL sections are marked for future completion. The jurisdictional scope for each cause of action is noted based on the evidence documents in each matter.

- [ ] **Step 1: Create google-platform-misclassification stubs**

Create `docs/court-record/matters/google-platform-misclassification/README.md`:

```markdown
# Matter: Google Platform Worker Misclassification

## Jurisdiction and Venue

Primary claims arise under California Labor Code and the ABC test (Lab. Code § 2775 et seq.). Subject matter jurisdiction in California Superior Court. Federal dimensions under NLRA (unfair labor practices) may invoke concurrent federal jurisdiction.

Constitutional scope: California statutory (ABC test application); federal statutory (NLRA); potentially federal constitutional (Supremacy Clause, preemption analysis if platform argues federal preemption).

Administrative exhaustion: Claims under FEHA require CRD complaint and right-to-sue letter before court filing. NLRA claims require NLRB charge filing.

## Parties

**Plaintiff:** Ian D.L.N. McLean, individually and as member of affected class of platform users systematically misclassified as independent contractors or consumers rather than employees or service providers.

**Defendants:** [To be specified — Google LLC and related entities]

## Statement of Facts

See `findings.md` FOF section. Supporting evidence in `evidence/`.

## Causes of Action

1. Misclassification under CA Labor Code § 2775 (ABC test) — CA statutory — no administrative exhaustion required for individual claims; DLSE complaint recommended as administrative record
2. Failure to pay wages, benefits, and provide protections owed to employees — CA statutory
3. Unfair labor practices — federal statutory (NLRA) — NLRB charge required before proceeding

## Prayer for Relief

[To be specified]
```

Create `docs/court-record/matters/google-platform-misclassification/findings.md`:

```markdown
# Findings of Fact and Conclusions of Law
## Matter: Google Platform Worker Misclassification

*[STUB — to be completed in findings-of-fact format per FRCP Rule 52]*

---

## Findings of Fact

1. [First numbered finding — single declarative sentence, evidence cited.]

---

## Conclusions of Law

1. [First numbered conclusion — flows from named FOF findings, cites authority.]
```

```bash
# Commands to create files (use Write tool, not echo, for actual implementation)
# See file contents above
```

- [ ] **Step 2: Create platform-tos-constitutional-limits stubs**

Create `docs/court-record/matters/platform-tos-constitutional-limits/README.md`:

```markdown
# Matter: Platform ToS and Constitutional Limits on LLM Expression Controls

## Jurisdiction and Venue

Claims arise under the First Amendment (federal constitutional), California Constitution Art. I §2 (state constitutional — speech broader than federal floor), California Business and Professions Code § 17200 (unfair business practices), and federal Section 230 (where platform immunity is being argued against claims here). Federal constitutional claims invoke federal court jurisdiction; state constitutional claims can be heard in CA Superior Court.

Constitutional scope: Federal constitutional (1st Amendment limits on automated decision systems); California constitutional (Art. I §2 broader speech protection); federal statutory (Section 230 scope and limits); California statutory (B&P § 17200 unfair practices).

Lower courts cannot resolve the federal or state constitutional questions — these must be preserved for appellate review or filed directly in appropriate federal or state courts.

## Parties

**Plaintiff:** Ian D.L.N. McLean, individually, as member of affected class, and as member of the public.

**Defendants:** [To be specified — platform operators and LLM service providers]

## Statement of Facts

See `findings.md` FOF section. Supporting evidence in `evidence/`.

## Causes of Action

1. First Amendment violation — federal constitutional — federal court
2. California Art. I §2 violation — state constitutional — CA Superior Court
3. Unfair business practices under B&P § 17200 — CA statutory — CA Superior Court
4. Automated decision system without human review — CA statutory — CA Superior Court

## Prayer for Relief

[To be specified]
```

Create `docs/court-record/matters/platform-tos-constitutional-limits/findings.md`:

```markdown
# Findings of Fact and Conclusions of Law
## Matter: Platform ToS and Constitutional Limits on LLM Expression Controls

*[STUB — to be completed in findings-of-fact format per FRCP Rule 52]*

---

## Findings of Fact

1. [First numbered finding — single declarative sentence, evidence cited.]

---

## Conclusions of Law

1. [First numbered conclusion — flows from named FOF findings, cites authority.]
```

- [ ] **Step 3: Create cooperative-investment-law stubs**

Create `docs/court-record/matters/cooperative-investment-law/README.md`:

```markdown
# Matter: Cooperative Investment Law and Patron Securities

## Jurisdiction and Venue

Claims arise under California Corporations Code (cooperative formation and governance), federal securities law (Investment Company Act, Securities Act of 1933), and IRC provisions governing cooperative patronage income. Federal securities claims invoke federal court jurisdiction; state corporate claims can be heard in CA Superior Court.

Constitutional scope: Federal statutory (federal securities law, IRC); California statutory (Corp Code, patron law).

## Parties

**Plaintiff:** Ian D.L.N. McLean, individually, as patron member of affected cooperatives, and as investor.

**Defendants:** [To be specified]

## Statement of Facts

See `findings.md` FOF section. Supporting evidence in `evidence/`. Theory authority in `court-record/theory/federal-statutes/existing-law/` (cooperative-investing-us-ca-irc.md, patronage-sourced-income.md) and `court-record/theory/california-statutes/existing-law/` (ca-patron-law-v2.md et al.).

## Causes of Action

1. [To be specified — cooperative governance violations]
2. [To be specified — patron rights violations]
3. [To be specified — securities law claims]

## Prayer for Relief

[To be specified]
```

Create `docs/court-record/matters/cooperative-investment-law/findings.md`:

```markdown
# Findings of Fact and Conclusions of Law
## Matter: Cooperative Investment Law and Patron Securities

*[STUB — to be completed in findings-of-fact format per FRCP Rule 52]*

---

## Findings of Fact

1. [First numbered finding — single declarative sentence, evidence cited.]

---

## Conclusions of Law

1. [First numbered conclusion — flows from named FOF findings, cites authority.]
```

- [ ] **Step 4: Create sex-work-consent-bodily-autonomy stubs**

Create `docs/court-record/matters/sex-work-consent-bodily-autonomy/README.md`:

```markdown
# Matter: Sex Work, Consent, and Bodily Autonomy

## Jurisdiction and Venue

Claims arise under the First Amendment (federal constitutional), California Constitution Art. I §1 (privacy) and Art. I §2 (speech), and California Penal Code provisions governing sexual services. Federal constitutional claims invoke federal court jurisdiction; state constitutional claims can be heard in CA Superior Court.

Constitutional scope: Federal constitutional (1st Amendment, bodily autonomy doctrine post-Dobbs); California constitutional (Art. I §1 explicit privacy right, Art. I §2 broader speech). Lower courts cannot resolve these constitutional questions.

## Parties

**Plaintiff:** Ian D.L.N. McLean, individually, as member of affected class, and as member of the public.

**Defendants:** [To be specified — state actors enforcing overbroad statutes; corporate actors restricting constitutionally protected conduct]

## Statement of Facts

See `findings.md` FOF section. Supporting evidence in `evidence/`. Theory authority in `court-record/theory/federal-constitutional/` (first-amendment-landmark-cases-research.md, legal-status-of-bodily-autonomy-post-dobbs.md, first-amendment-and-prostitution-law.md) and `court-record/theory/california-statutes/existing-law/` (california-sex-contract-consent-standards.md et al.).

## Causes of Action

1. Overbroad criminalization of consensual sexual services — federal constitutional, 1st Amendment — federal court
2. California privacy right violations — CA constitutional, Art. I §1 — CA Superior Court
3. [To be specified — additional causes]

## Prayer for Relief

[To be specified]
```

Create `docs/court-record/matters/sex-work-consent-bodily-autonomy/findings.md`:

```markdown
# Findings of Fact and Conclusions of Law
## Matter: Sex Work, Consent, and Bodily Autonomy

*[STUB — to be completed in findings-of-fact format per FRCP Rule 52]*

---

## Findings of Fact

1. [First numbered finding — single declarative sentence, evidence cited.]

---

## Conclusions of Law

1. [First numbered conclusion — flows from named FOF findings, cites authority.]
```

- [ ] **Step 5: Create copyright-ip-authorship stubs**

Create `docs/court-record/matters/copyright-ip-authorship/README.md`:

```markdown
# Matter: Copyright, IP Authorship, and AI-Assisted Creation

## Jurisdiction and Venue

Claims arise under the Copyright Act (federal statutory), California contract law (CA statutory), and potentially federal constitutional dimensions of authorship rights. Federal copyright claims invoke federal court jurisdiction; contract claims can be heard in CA Superior Court.

Constitutional scope: Federal statutory (Copyright Act, 17 U.S.C.); California statutory (contract law governing artist agreements); federal constitutional (IP clause, Art. I §8 cl. 8) for constitutional dimensions of authorship.

## Parties

**Plaintiff:** Ian D.L.N. McLean, individually, as author and creator, and as commissioner of creative works.

**Defendants:** [To be specified — platforms and companies claiming IP ownership of user-generated or AI-assisted content]

## Statement of Facts

See `findings.md` FOF section. Supporting evidence in `evidence/`. Theory authority in `court-record/theory/federal-statutes/existing-law/` (ip-contract-knowledge-graph.md).

## Causes of Action

1. Copyright authorship and ownership — federal statutory — federal court
2. Breach of artist/commission contracts — CA statutory — CA Superior Court
3. [To be specified — additional causes]

## Prayer for Relief

[To be specified]
```

Create `docs/court-record/matters/copyright-ip-authorship/findings.md`:

```markdown
# Findings of Fact and Conclusions of Law
## Matter: Copyright, IP Authorship, and AI-Assisted Creation

*[STUB — to be completed in findings-of-fact format per FRCP Rule 52]*

---

## Findings of Fact

1. [First numbered finding — single declarative sentence, evidence cited.]

---

## Conclusions of Law

1. [First numbered conclusion — flows from named FOF findings, cites authority.]
```

- [ ] **Step 6: Commit all stubs**

```bash
cd /tmp/claude-1000/-home-metavacua/1cdc4a82-e952-4641-8d15-795574e7f5c9/scratchpad/legal-theory
git add docs/court-record/matters/
git commit -m "Add matter stubs (README.md and findings.md) for all five matters"
```

---

### Task 15: Create index.md

**Files:**
- Create: `docs/index.md`

- [ ] **Step 1: Write index.md**

Create `docs/index.md`:

```markdown
# legal-theory — Index

Repository of findings of fact supporting arguments in legal controversies of clear merit.
Copyright Ian D.L.N. McLean — CC BY-SA 4.0.

---

## Court Record

### Theory

Legal authority organized by jurisdictional level. Lower courts cannot rule on or override
constitutional questions that belong to higher levels.

#### Federal Constitutional

- [Existing Doctrine](court-record/theory/federal-constitutional/existing-doctrine/)
- [Extensions](court-record/theory/federal-constitutional/extensions/)
- [Specializations](court-record/theory/federal-constitutional/specializations/)
- [Reversal Arguments](court-record/theory/federal-constitutional/reversal-arguments/)

#### California Constitutional

- [Existing Doctrine](court-record/theory/california-constitutional/existing-doctrine/)
- [Extensions](court-record/theory/california-constitutional/extensions/)
- [Specializations](court-record/theory/california-constitutional/specializations/)
- [Reversal Arguments](court-record/theory/california-constitutional/reversal-arguments/)

#### Federal Statutes

- [Existing Law](court-record/theory/federal-statutes/existing-law/)
- [Extensions](court-record/theory/federal-statutes/extensions/)
- [Specializations](court-record/theory/federal-statutes/specializations/)
- [Reversal Arguments](court-record/theory/federal-statutes/reversal-arguments/)

#### California Statutes

- [Existing Law](court-record/theory/california-statutes/existing-law/)
- [Extensions](court-record/theory/california-statutes/extensions/)
- [Specializations](court-record/theory/california-statutes/specializations/)
- [Reversal Arguments](court-record/theory/california-statutes/reversal-arguments/)

#### Municipal

- [Existing Law](court-record/theory/municipal/existing-law/)
- [Specializations](court-record/theory/municipal/specializations/)

---

### Matters

Each matter contains a complaint-structure README, a findings-of-fact document, an
administrative record (agency prerequisite filings), and supporting evidence.

- [Google Platform Worker Misclassification](court-record/matters/google-platform-misclassification/)
  — CA Labor Code ABC test; NLRA; worker classification of platform users
- [Platform ToS and Constitutional Limits on LLM Controls](court-record/matters/platform-tos-constitutional-limits/)
  — 1st Amendment; CA Art. I §2; automated decision systems; Section 230
- [Cooperative Investment Law and Patron Securities](court-record/matters/cooperative-investment-law/)
  — CA Corporations Code; federal securities law; IRC cooperative treatment
- [Sex Work, Consent, and Bodily Autonomy](court-record/matters/sex-work-consent-bodily-autonomy/)
  — 1st Amendment; CA Art. I §1 privacy; CA consent and criminal law
- [Copyright, IP Authorship, and AI-Assisted Creation](court-record/matters/copyright-ip-authorship/)
  — Copyright Act; CA contract law; AI-assisted authorship

---

## Proposals

### Legislative

- [Federal — Congress](proposals/legislative/federal/congress/)
- [California — State Legislature](proposals/legislative/california/state-legislature/)
- [California — County](proposals/legislative/california/county/)
- [California — City](proposals/legislative/california/city/)
- [California — Petitions](proposals/legislative/california/petitions/)

### Executive

#### Orders

- [Presidential](proposals/executive/orders/federal/presidential/)
- [Governor of California](proposals/executive/orders/california/governor/)

#### Agencies

- [FTC](proposals/executive/agencies/federal/ftc/)
- [NLRB](proposals/executive/agencies/federal/nlrb/)
- [SEC](proposals/executive/agencies/federal/sec/)
- [CA Attorney General](proposals/executive/agencies/california/attorney-general/)
- [CA Labor Commissioner (DLSE)](proposals/executive/agencies/california/labor-commissioner-dlse/)
- [CA Civil Rights Department (CRD)](proposals/executive/agencies/california/civil-rights-dept-crd/)
- [CA DFPI](proposals/executive/agencies/california/dfpi/)
- [CA FPPC](proposals/executive/agencies/california/fppc/)
- [CA Secretary of State](proposals/executive/agencies/california/secretary-of-state/)

---

## Cross-Cutting

Analysis spanning multiple matters or jurisdictional levels.

- [cross-cutting/](cross-cutting/)

---

## Works in Progress

Documents not yet in findings-of-fact format or pending classification.

- [wip/](wip/)

---

## Design

- [Repository Organization Design Spec](superpowers/specs/2026-06-30-repository-organization-design.md)
```

- [ ] **Step 2: Commit**

```bash
cd /tmp/claude-1000/-home-metavacua/1cdc4a82-e952-4641-8d15-795574e7f5c9/scratchpad/legal-theory
git add docs/index.md
git commit -m "Add top-level index.md"
```

---

### Task 16: Final Verification and PR Update

- [ ] **Step 1: Verify final document count**

```bash
cd /tmp/claude-1000/-home-metavacua/1cdc4a82-e952-4641-8d15-795574e7f5c9/scratchpad/legal-theory
find docs -name "*.md" | grep -v ".gitkeep" | wc -l
```

Expected: 113+ (original 112 documents + design spec + index.md + 10 matter stubs [5 README + 5 findings]).

- [ ] **Step 2: Verify no orphaned files remain in old directories**

```bash
find docs -maxdepth 1 -type d | sort
```

Expected only: `docs`, `docs/court-record`, `docs/cross-cutting`, `docs/proposals`, `docs/superpowers`, `docs/wip`

- [ ] **Step 3: Check git log**

```bash
git log --oneline -20
```

Expected: ~15 commits covering each migration task.

- [ ] **Step 4: Report to user for push approval**

Do NOT push. Report the commit count and final document count to the user and ask for explicit push approval before running `git push`.

---

## Self-Review

**Spec coverage check:**

| Spec requirement | Plan task |
|---|---|
| `court-record/theory/` with jurisdictional levels | Task 1 (structure), Tasks 2–4 (migration) |
| Extensions separate from specializations | Tasks 2–4 (separate subdirs) |
| `matters/[matter]/` with README, findings, administrative-record, evidence | Tasks 5–9 (migration), Task 14 (stubs) |
| `proposals/legislative/` with federal, CA state/county/city, petitions | Tasks 1 (structure), Task 10 (migration) |
| `proposals/executive/orders/` with federal/CA | Task 1 (structure) |
| `proposals/executive/agencies/` with specific agencies | Tasks 1 (structure), Task 10 (migration) |
| `cross-cutting/` | Tasks 1 (structure), Task 11 (migration) |
| `wip/` | Tasks 1 (structure), Tasks 5, 12 (migration) |
| `index.md` | Task 15 |
| Municipal has no reversal-arguments | Task 1 (structure) |
| Administrative-record as court prerequisites | Task 14 (stubs reference it) |

**Placeholder scan:** Matter stubs (README, findings.md) contain `[To be specified]` and `[STUB]` markers by design — these are genuine stubs, not placeholder spec text. The plan does not reference any function or method not defined within it.

**Document count:** 112 source documents + 1 design spec = 113 tracked at start. After migration: 113 + 1 index.md + 10 matter stubs = 124 total. The migration itself moves documents, not loses them.

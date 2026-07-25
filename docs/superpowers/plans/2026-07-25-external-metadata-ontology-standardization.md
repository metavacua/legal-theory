# External Metadata & Ontology Standardization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Standardize document metadata across the `docs/` legal-theory corpus (119 documents + the 2-article `llm-database-theory` paper) on real, external, actively-maintained schemas and ontologies — DCTERMS, DCMI Type Vocabulary, Schema.org, SPDX, CSL-JSON, SPAR (FaBiO/CiTO), and PROV-O — replacing ad hoc prose and hand-authored duplicate metadata with mechanically generated, uniform, schema-enforced fields.

**Architecture:** The corpus already uses the right namespace for Dublin Core (`http://purl.org/dc/terms/`, i.e. DCTERMS, not the older simple-DC namespace) via `docs/common/shared-metadata.xml`, xi:included into every document's `.meta.xml`. This plan (1) completes the DCTERMS field set corpus-wide and fixes a live metadata-duplication bug in the paper, (2) tightens `docs/schema/docbook-corpus.rnc` to actually enforce what it currently lets through via an `any` wildcard, (3) closes a CI gap where the paper is never schema-validated, (4) generates Schema.org JSON-LD mechanically from DCTERMS fields instead of hand-duplicating it, and (5) adds three genuinely new external-standard outputs (SPDX license IDs, CSL-JSON bibliography export, SPAR citation-typing graph, PROV-O provenance) that the corpus doesn't have today.

**Tech Stack:** RELAX NG Compact (schema), XSLT 1.0 (`docs/xsl/html5.xsl`), Python 3 (`unittest`, `json`, `subprocess`, and `lxml.etree` — adopted in Tasks 7/11, installed via `apt`, replacing stdlib `xml.etree.ElementTree` as the one shared AST library across `docs/scripts/*.py`), `jing`, `xmllint`, `git` (for `dcterms:date` derivation).

## Global Constraints

- All namespace URIs MUST be the real, published URIs for the standard in question — never invented prefixes standing in for something else. DCTERMS = `http://purl.org/dc/terms/`; DCMI Type Vocabulary = `http://purl.org/dc/dcmitype/`; Schema.org = `https://schema.org/`; CiTO = `http://purl.org/spar/cito/`; FaBiO = `http://purl.org/spar/fabio/`; PROV-O = `http://www.w3.org/ns/prov#`; SPDX license list = `https://spdx.org/licenses/`.
- `dc:type` (DCTERMS) is fixed to the DCMI Type Vocabulary term `"Text"` everywhere. Schema.org's own `@type` (`ScholarlyArticle`, `CreativeWork`, ...) is a separate vocabulary and lives only in the JSON-LD block — the two type systems must never both try to occupy the same `dc:type` element (that collision is the root cause of Task 1's bug).
- Every task that adds or backfills metadata must keep `make validate` (paper) and the corpus validation loop in `.github/workflows/build-corpus.yml` passing — no task may leave the schema stricter than the actual corpus content until a prior task has already brought every document's content up to the new bar.
- New Python code follows the existing `docs/scripts/` conventions exactly: `unittest.TestCase` (not bare `pytest` functions — see `docs/scripts/tests/test_build_bibliography.py`), functions documented with a docstring explaining the non-obvious *why*, no hand-rolled XML string-building for anything touching untrusted/variable attribute content (reuse `xml.sax.saxutils.escape` only for element text, never for attribute values without the caller guaranteeing no `"` — see existing `_entry_listitem_xml` for the pattern to avoid).
- `REPO_ROOT` (`docs/scripts/convert_to_docbook.py:192`) is the one source of truth for repo-root-relative path math; every new helper reuses it rather than recomputing `Path(__file__).resolve().parent...`.
- ORCID identifiers and Akoma Ntoso/LegalDocML adoption are explicitly **out of scope** for this plan: ORCID needs the author's actual iD (not fabricated here — see plan notes below); Akoma Ntoso would mean abandoning DocBook 5.2 as the corpus base, which is a much larger migration than metadata standardization and is not justified at this corpus's current scale.
- No RNC pattern may be added that is unreachable from `start` (a non-productive grammar rule) — the corpus's schema already had exactly this defect (`finding-section`, fixed in Task 10) and it must not be reintroduced. Every new pattern must be exercised by an actual, wired-in validation command, not merely defined.
- Non-standard, isolated, or document-scoped schema/vocabulary exceptions are not an acceptable resting state: a construct that only one document (or one subtree) uses must be either (a) genuinely standardized — reachable and enforced for any document, corpus-wide, through the one shared validation pipeline — or (b) removed. It must never survive by being carved into a separate, paper-local schema file that only that subtree's build invokes.
- This repo has no dependency-management file today (no `requirements.txt`/`pyproject.toml`) and every script was stdlib-only Python before this plan. That is not a reason to avoid a genuinely better tool: `lxml` is installed via `apt` (`python3-lxml` — the same install mechanism already used for `jing`/`xmllint`/`xsltproc`, not `pip`) and adopted as the corpus's one shared AST library across every `docs/scripts/*.py` file (Tasks 7 and 11) — verified working (native `XInclude` resolution, correct attribute escaping, `nsmap`-based namespace construction) before being written into any task. Absence of a tool is a reason to install it, not a reason to route around it with a weaker substitute.

---

## Plan Notes (read before starting)

**Verified, not assumed, before writing this plan:**
- `docs/common/shared-metadata.xml` and `docs/papers/ai_and_ip/llm-database-theory/src/00-metadata.xml` already bind the `dc:` prefix to `http://purl.org/dc/terms/` (DCTERMS), **not** the older simple-DC namespace — so "adopt DCTERMS" below means *complete* the field set and enforce it, not swap namespaces.
- `xmllint --xinclude --noout` was run against `00-metadata.xml` to resolve its `xi:include` for real. The resolved tree has **two** `dc:type` elements ("ScholarlyArticle" as a direct child of `db:info`, "Article" nested one level deeper inside the included `<shared>` wrapper), **two** `dc:creator` elements, **two** `authorgroup` elements, and **two** `legalnotice` elements. Because both `01-llm-database-theory.xml` and `02-legal-corpus-connections.xml` `xi:include` this same `00-metadata.xml`, and `docs/xsl/html5.xsl` reads `db:info/dc:title` (not the native `db:title`) for the HTML `<title>` tag, the **built HTML for the second article literally has the first article's title** — confirmed by grep on the actual committed `docs/papers/ai_and_ip/llm-database-theory/html/02-legal-corpus-connections.html`, whose `<title>` reads "Language Models Are Databases: A Technical and Legal Position Paper on LLMs and Intellectual Property" instead of "Legal Corpus Connections". This is a real, live, user-visible bug, not a hypothetical one.
- `jing -c docs/schema/docbook-corpus.rnc "$xml"` is invoked in both the Makefile and `build-corpus.yml` **without** `--xinclude` — jing validates the raw, unresolved document (the literal `<xi:include>` element, not what it resolves to). Any RNC tightening in this plan is written against that unresolved shape; a pattern that only works after XInclude resolution would never actually run in this pipeline.
- `.github/workflows/build-papers.yml`'s "Install DocBook toolchain" step installs `libxml2-utils` and `xsltproc` but **not** `jing`, and its only build step is `make html` — `make validate` (which the paper's own Makefile defines and which does run `jing` when installed) is never invoked. The flagship paper of this PR has zero automated schema validation today.
- `docs/xsl/html5.xsl` renders the Schema.org JSON-LD by `xsl:value-of`-copying the hand-authored `<bibliomisc role="schema-org-jsonld">` CDATA blob verbatim (line 44-46) — it does not generate it from the DCTERMS fields, so the JSON-LD's `datePublished`/`keywords`/`author`/`license` are a second, hand-maintained copy of data that already exists as `dc:date`/`dc:subject`/`dc:creator`/`dc:rights`.
- CSL-JSON (the Citation Style Language's JSON schema, used by Zotero, Pandoc, and every `citeproc` implementation) defines `legal_case` and `legislation` as first-class item types — confirmed against the schema at `github.com/citation-style-language/schema`. This is a genuine fit for this corpus's existing statute/case classification, not a forced one.
- SPAR's FaBiO (`http://purl.org/spar/fabio`) and CiTO (`http://purl.org/spar/cito`) ontologies are real, actively maintained (Shotton & Peroni), with CiTO defining exactly the citation-relationship predicates (`citesAsAuthority`, `citesAsSourceDocument`, ...) this corpus's citation-audit work already computes informally.
- PROV-O (`http://www.w3.org/ns/prov#`) is the W3C provenance ontology; `prov:SoftwareAgent` is its standard class for a non-human contributor, which is exactly what "Research assistance by Claude Sonnet 4.6 (Anthropic)" is trying to express in prose today.
- A native DocBook `<orcid>` element could **not** be confirmed to exist in DocBook 5.1/5.2 after checking the OASIS spec and the Definitive Guide — rather than fabricate an element, ORCID support is left out of this plan's tasks entirely (see Global Constraints). If the author later supplies a real ORCID iD, it slots into the existing, already-valid `<uri>` child of `<author>` (the same element `00-metadata.xml` already uses for the GitHub profile link) — no schema change needed.
- `grep -rl 'role="finding"' docs --include="*.xml"` (outside `papers/`) returns nothing, confirmed against the real corpus. `docs/court-record/matters/*/findings.xml` (the corpus's actual Findings-of-Fact/Conclusions-of-Law documents) use plain, unmarked `<section>`s with no equivalent status convention. So two unreconciled ways to express "a finding" coexist, and the schema file that's supposed to govern this corpus-wide actually only serves one of them.
- Direct inspection of `docs/schema/docbook-corpus.rnc`'s `start` production shows `finding-section` is **never referenced** by `start` or by anything `start` reaches (`block-content`'s own `element db:section { any }` alternative is the only section rule actually reachable) — `finding-section` is dead, non-productive grammar. Confirmed by construction, not just inspection: a `<section role="finding" condition="not-a-real-value">` with no `xml:id` was run through `jing -c docs/schema/docbook-corpus.rnc` and validated successfully (should have failed) because the unconstrained `block-content` alternative matches it regardless.
- Tried and rejected: wiring `finding-section` into `start`/`block-content` as an explicit additional choice alternative does not fix this — RELAX NG's choice (`|`) tries every alternative and succeeds if any one matches; the always-permissive `element db:section { any }` alternative for the same element name will always succeed even when the stricter `finding-section` alternative correctly fails, so the constraint is still silently bypassed. This is a structural limitation of RELAX NG choice against a permissive fallback for the same element name, not a mistake in how the rule was written.
- Tried and rejected: RELAX NG's own standard companion for exactly this class of attribute-value-conditioned constraint is Schematron (ISO/IEC 19757-3), and `xmllint` reports `Schematron` in its compiled feature list. But directly tested against this environment's libxml2 (2.9.14): even a minimal, valid Schematron file (a single `<rule context="section">` with one `<assert>`) fails with `validation generated an internal error` under `xmllint --schematron`, reproducibly, across several variations (with/without namespace prefixes, with/without `xml:id` in the test). Confirmed non-functional here by direct testing, not assumed to work from documentation. Task 10 uses a plain Python tree-walk instead — verified working end to end against both the real paper content (0 violations) and a deliberately broken fixture (both expected violations correctly raised).
- `lxml` was not pre-installed (`ModuleNotFoundError` via `pip`, which itself wasn't on `PATH`) and no `requirements.txt`/`pyproject.toml` exists in the repo — but `apt-cache policy python3-lxml` showed it as a real, installable candidate package, and `sudo apt-get install -y python3-lxml` installed it cleanly in one step, verified directly. Every claim used to justify it was tested against this repo's real content before being written into a task: native `lxml.etree` `XInclude` resolution correctly resolved the paper's actual nested fragment structure where stdlib `xml.etree.ElementInclude` raised `FileNotFoundError`; `etree.register_namespace("", DB_NS)` (the pattern `convert_to_docbook.py` relies on throughout) raises `ValueError` under `lxml` and needs `nsmap={None: DB_NS, ...}` at element-creation time instead — verified working, including that a detached sub-element appended later inherits the root's namespace context without redeclaring it; `lxml.etree.indent()` exists with the same signature as stdlib's; `lxml` raises `XMLSyntaxError` where stdlib raises `ParseError`. Given all of that worked, Tasks 7 and 11 adopt `lxml` as the one shared AST library across every script, installed via `apt` alongside the C-library tools (`jing`/`xmllint`/`xsltproc`) this pipeline already depends on.
- Schema.org's `DefinedTerm`/`DefinedTermSet`/`inDefinedTermSet` are real, established vocabulary (confirmed against schema.org's own type pages) — `DefinedTermSet` is a subtype of `CreativeWork`, and `about` is the standard way a `CreativeWork` references a `DefinedTerm`. This is the bridge Task 9 uses to surface the SKOS concept scheme from each document's generated JSON-LD.

---

## File Structure

- Modify `docs/papers/ai_and_ip/llm-database-theory/src/00-metadata.xml` → **deleted**; its per-article content splits into two new files.
- Create `docs/papers/ai_and_ip/llm-database-theory/src/01-llm-database-theory.meta.xml` — article 1's own DCTERMS fields + Schema.org JSON-LD.
- Create `docs/papers/ai_and_ip/llm-database-theory/src/02-legal-corpus-connections.meta.xml` — article 2's own DCTERMS fields + Schema.org JSON-LD.
- Modify `docs/papers/ai_and_ip/llm-database-theory/src/01-llm-database-theory.xml`, `02-legal-corpus-connections.xml` — repoint their `xi:include` at the new per-article meta files.
- Modify `docs/papers/ai_and_ip/llm-database-theory/Makefile` — generalize the `ARTICLES` filter from a hardcoded filename to a `%.meta.xml` pattern (Task 1); add a metadata `jing` loop (Task 4); add the finding-section check (Task 10); pass `bibliography-href` to the HTML build rule (Task 7).
- Modify `docs/common/shared-metadata.xml` — fix `dc:type` to the DCMI Type Vocabulary term `Text`, add the author's GitHub `<uri>`, add `dc:license` (SPDX identifier).
- Modify `docs/scripts/convert_to_docbook.py` — `write_metadata()` gains automatic `dc:date`/`dc:identifier`/`dc:subject` population (Task 2); `SUBJECT_CONCEPTS`/`derive_subject_concept_id()`/`concept_uri()` and an `xlink:href` on the `dc:subject` it emits (Task 9); `validate_finding_sections()` wired into `validate()` (Task 10); migrated onto `lxml` (Task 11).
- Create `docs/scripts/backfill_dcterms_metadata.py` — one-shot script that regenerates every existing corpus `.meta.xml` through the enhanced `write_metadata()` (Task 2).
- Modify `docs/schema/docbook-corpus.rnc` — declare the `xsd` datatype library and `dc` namespace; require the DCTERMS core fields on every article's `db:info`; add a `start` alternative validating `docs/common/shared-metadata.xml` itself (Task 3); allow `xlink:href` on `dc:subject` (Task 9); remove the dead `finding-condition`/`finding-section` patterns and rewrite the header (Task 10); allow `db:bibliography` in `block-content` (Task 7).
- Modify `.github/workflows/build-corpus.yml` — validate `docs/common/shared-metadata.xml` and every `.meta.xml` directly (Task 4); run the finding-section check per article (Task 10); install `python3-lxml` (Task 7).
- Modify `.github/workflows/build-papers.yml` — install `jing`, run `make validate` before `make html` (Task 4); install `python3-lxml` (Task 7).
- Modify `docs/xsl/html5.xsl` — generate the Schema.org JSON-LD `<script>` block from DCTERMS fields instead of copying a hand-authored blob (Task 5); emit a `about`/`DefinedTerm` block when `dc:subject/@xlink:href` is present (Task 9); render `db:bibliography`/`db:biblioentry` and resolve `db:citation` to a real hyperlink via the `bibliography-href` param (Task 7).
- Modify `docs/scripts/build_bibliography.py` — add `emit_csl_json()` (Task 6); rewrite `emit_docbook`/emission functions onto native DocBook bibliography vocabulary + CiTO `xlink:arcrole`, add `bib_key` to `BibliographyEntry`, and install/use `lxml` (Task 7); finish unifying the whole file onto `lxml` (Task 11).
- Create `docs/common/subject-scheme.jsonld` — the SKOS ConceptScheme for `dc:subject` (Task 9).
- Create `docs/scripts/generate_subject_scheme.py` — regenerates `subject-scheme.jsonld` from the taxonomy table in `convert_to_docbook.py` (Task 9).
- Create `docs/scripts/check_finding_sections.py` — CLI wrapper around `validate_finding_sections()` for the shell-based Makefile/CI validation loops (Task 10).
- Create `docs/scripts/corpus_ast.py` — the shared `lxml`-based parse/serialize/root-construction helpers used by `build_bibliography.py` (Task 7) and `convert_to_docbook.py` (Task 11).
- Modify `docs/papers/ai_and_ip/llm-database-theory/src/01-llm-database-theory.meta.xml`, `02-legal-corpus-connections.meta.xml` (again) — add a native `<othercredit xlink:arcrole="...prov#SoftwareAgent">` for AI-assisted research, replacing a JSON-LD `bibliomisc` blob (Task 8); add `xlink:href` to `dc:subject` (Task 9).
- Modify `docs/scripts/atomize_existing_document.py`, `docs/scripts/audit_footnote_links.py` — migrated onto `lxml` (Task 11).
- Modify `docs/scripts/tests/test_convert_to_docbook.py`, `docs/scripts/tests/test_build_bibliography.py` — new test classes for each of the above.

---

### Task 1: Fix the paper's metadata-duplication bug and give each article its own DCTERMS identity

**Files:**
- Delete: `docs/papers/ai_and_ip/llm-database-theory/src/00-metadata.xml`
- Create: `docs/papers/ai_and_ip/llm-database-theory/src/01-llm-database-theory.meta.xml`
- Create: `docs/papers/ai_and_ip/llm-database-theory/src/02-legal-corpus-connections.meta.xml`
- Modify: `docs/papers/ai_and_ip/llm-database-theory/src/01-llm-database-theory.xml:3`
- Modify: `docs/papers/ai_and_ip/llm-database-theory/src/02-legal-corpus-connections.xml:3`
- Modify: `docs/common/shared-metadata.xml`
- Modify: `docs/papers/ai_and_ip/llm-database-theory/Makefile`

**Interfaces:**
- Produces: the `dc:identifier` URI convention `https://github.com/metavacua/legal-theory/blob/main/<repo-relative-path>`, reused by Task 2's `derive_identifier()`.
- Produces: `docs/common/shared-metadata.xml`'s `dc:type` = `Text` (DCMI Type Vocabulary), which Task 3's schema will require verbatim.

- [ ] **Step 1: Confirm the live bug before touching anything**

Run:
```bash
xmllint --xinclude docs/papers/ai_and_ip/llm-database-theory/src/00-metadata.xml 2>/dev/null | grep -c "<dc:type>"
grep -o "<title>.*</title>" docs/papers/ai_and_ip/llm-database-theory/html/02-legal-corpus-connections.html
```
Expected: the first command prints `2` (two `dc:type` elements survive XInclude resolution); the second prints the wrong title, `<title>Language Models Are Databases: A Technical and Legal Position Paper on LLMs and Intellectual Property</title>`, for what should be the "Legal Corpus Connections" page.

- [ ] **Step 2: Fix `docs/common/shared-metadata.xml`**

Replace its full contents with:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<shared xmlns="http://docbook.org/ns/docbook" xmlns:dc="http://purl.org/dc/terms/">
  <dc:creator>Ian D.L.N. McLean</dc:creator>
  <dc:publisher>metavacua/legal-theory (GitHub)</dc:publisher>
  <dc:type>Text</dc:type>
  <dc:language>en</dc:language>
  <dc:rights>CC BY-SA 4.0</dc:rights>
  <dc:license>https://spdx.org/licenses/CC-BY-SA-4.0</dc:license>
  <authorgroup>
    <author>
      <personname>
        <firstname>Ian</firstname>
        <othername role="middle">D.L.N.</othername>
        <surname>McLean</surname>
      </personname>
      <email>metavacua@gmail.com</email>
      <uri>https://github.com/metavacua</uri>
    </author>
  </authorgroup>
  <legalnotice>
    <para>Copyright &#169; 2026 Ian D.L.N. McLean. Licensed under Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0). This document publishes general legal analysis and does not constitute legal advice.</para>
  </legalnotice>
</shared>
```
This changes `dc:type` from the non-standard value `Article` to the correct DCMI Type Vocabulary term `Text` (a scholarly article, a findings memo, and a proposal are all textual resources — the *kind* of article belongs in Schema.org's `@type`, not here), adds the author's GitHub `<uri>` (previously only present in the paper's now-to-be-deleted local `authorgroup`) so every document in the corpus carries it, and adds `dc:license` as a distinct DCTERMS term from `dc:rights` — `dc:rights` stays a human-readable string, `dc:license` is the machine-resolvable SPDX identifier URI for the same license.

- [ ] **Step 3: Create `01-llm-database-theory.meta.xml`**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<info xmlns="http://docbook.org/ns/docbook"
      xmlns:dc="http://purl.org/dc/terms/"
      xmlns:xi="http://www.w3.org/2001/XInclude">

  <dc:title>Language Models Are Databases: A Technical and Legal Position Paper on LLMs and Intellectual Property</dc:title>
  <dc:subject>large language models; graph databases; intellectual property; copyright; LARQL; mechanistic interpretability; derivative works; collective works; database law; GDPR; transformer architecture; knowledge graphs</dc:subject>
  <dc:description>A transformer's weights constitute a queryable graph database of the works it was built from. Chris Hay's LARQL (Lazarus Query Language) supplies the query interface that reads those entries back—entities, relations, directed edges—and writes them into ordinary model files unchanged. Arithmetic storage is still storage; the machine-perceptibility test for fixation predates modern AI and fits without strain. A model that regenerates Harry Potter near-verbatim or renders Superman on demand contains those works, and the settled law of copies, compilations, and distribution is the law that governs it. This paper establishes the technical isomorphism, assembles the empirical memorisation record, and draws the legal conclusions that follow directly from both.</dc:description>
  <dc:date>2026-07-01</dc:date>
  <dc:identifier>https://github.com/metavacua/legal-theory/blob/main/docs/papers/ai_and_ip/llm-database-theory/src/01-llm-database-theory.xml</dc:identifier>
  <xi:include href="../../../../common/shared-metadata.xml"/>

  <bibliomisc role="schema-org-jsonld"><![CDATA[
{
  "@context": "https://schema.org",
  "@type": "ScholarlyArticle",
  "name": "Language Models Are Databases",
  "headline": "Language Models Are Databases: A Technical and Legal Position Paper on LLMs and Intellectual Property",
  "datePublished": "2026-07-01",
  "inLanguage": "en",
  "author": {
    "@type": "Person",
    "name": "Ian D.L.N. McLean",
    "email": "metavacua@gmail.com"
  },
  "publisher": {
    "@type": "Organization",
    "name": "metavacua/legal-theory",
    "url": "https://github.com/metavacua/legal-theory"
  },
  "keywords": ["large language models","graph databases","intellectual property","copyright","LARQL","derivative works","database law","GDPR"],
  "license": "https://creativecommons.org/licenses/by-sa/4.0/",
  "isPartOf": {
    "@type": "Collection",
    "name": "legal-theory: AI and Intellectual Property"
  }
}
  ]]></bibliomisc>

  <abstract>
    <para>A trained language model is a database of the works it was built from. Chris Hay's LARQL (Lazarus Query Language) is an open-source Rust tool that extracts a transformer's weights into a <emphasis>vindex</emphasis>—a vector index—and exposes a query language, LQL, that returns labelled directed edges directly out of the weight tensors. The model's feed-forward network (FFN) layers map isomorphically to knowledge-graph nodes and edges; a forward pass is computationally equivalent to a k-nearest-neighbour graph walk. LARQL further demonstrates that individual edges can be inserted, retrieved, and compiled back into standard model formats without retraining. The storage is arithmetic, but arithmetic storage is still storage: the machine-perceptibility test for copyright fixation covers any form in which a work can be reproduced with the aid of a machine. Peer-reviewed extraction studies confirm that frontier LLMs deterministically regenerate copyrighted books (Cooper et al. 2025) and near-identical training images (Carlini et al. 2023) from their weights. The conclusion that follows is not novel: a model trained on protected works is a derivative work and a collective work; distributing it distributes copies; operating it reproduces them. No new statute is required. Database law and the law of copies, both old and well-settled, reach this case directly.</para>
  </abstract>

</info>
```
Note: `xmlns:dc` is declared once on `<info>`, matching the existing corpus convention exactly (verified against `docs/wip/jpa-and-city-cooperatives.meta.xml`, whose real, committed source declares `dc` and `xi` once on `<info>` and nowhere else) — not redeclared per element.

- [ ] **Step 4: Create `02-legal-corpus-connections.meta.xml`**

Content faithful to the article's own subtitle and actual content (per the PR description: it maps the database theory to copyright-ip-authorship, platform-ToS constitutional limits, and AGPL derivative-works):
```xml
<?xml version="1.0" encoding="UTF-8"?>
<info xmlns="http://docbook.org/ns/docbook"
      xmlns:dc="http://purl.org/dc/terms/"
      xmlns:xi="http://www.w3.org/2001/XInclude">

  <dc:title>Legal Corpus Connections: How the LLM-Database Theory Connects to Existing Matters in This Repository</dc:title>
  <dc:subject>copyright-ip-authorship; platform-ToS constitutional limits; AGPL derivative works; database-retrieval-vs-speech; GPL poison pill; findings of fact; conclusions of law</dc:subject>
  <dc:description>Maps the LLM-database theory established in the companion article onto three existing matters in this repository: copyright-ip-authorship (six findings of fact and two conclusions of law ready for stub completion), platform-ToS constitutional limits (the database-retrieval-vs-speech distinction), and AGPL derivative-works (the technical premise underlying the GPL "poison pill" argument as applied to model weights).</dc:description>
  <dc:date>2026-07-01</dc:date>
  <dc:identifier>https://github.com/metavacua/legal-theory/blob/main/docs/papers/ai_and_ip/llm-database-theory/src/02-legal-corpus-connections.xml</dc:identifier>
  <xi:include href="../../../../common/shared-metadata.xml"/>

  <bibliomisc role="schema-org-jsonld"><![CDATA[
{
  "@context": "https://schema.org",
  "@type": "ScholarlyArticle",
  "name": "Legal Corpus Connections",
  "headline": "Legal Corpus Connections: How the LLM-Database Theory Connects to Existing Matters in This Repository",
  "datePublished": "2026-07-01",
  "inLanguage": "en",
  "author": {
    "@type": "Person",
    "name": "Ian D.L.N. McLean",
    "email": "metavacua@gmail.com"
  },
  "publisher": {
    "@type": "Organization",
    "name": "metavacua/legal-theory",
    "url": "https://github.com/metavacua/legal-theory"
  },
  "keywords": ["copyright-ip-authorship","platform-ToS","constitutional limits","AGPL","derivative works","database law"],
  "license": "https://creativecommons.org/licenses/by-sa/4.0/",
  "isPartOf": {
    "@type": "Collection",
    "name": "legal-theory: AI and Intellectual Property"
  }
}
  ]]></bibliomisc>

</info>
```

- [ ] **Step 5: Repoint the two articles and delete the old shared file**

In `docs/papers/ai_and_ip/llm-database-theory/src/01-llm-database-theory.xml:3`, change:
```xml
  <xi:include href="00-metadata.xml" />
```
to:
```xml
  <xi:include href="01-llm-database-theory.meta.xml" />
```

In `docs/papers/ai_and_ip/llm-database-theory/src/02-legal-corpus-connections.xml:3`, change:
```xml
  <xi:include href="00-metadata.xml" />
```
to:
```xml
  <xi:include href="02-legal-corpus-connections.meta.xml" />
```

Then:
```bash
rm docs/papers/ai_and_ip/llm-database-theory/src/00-metadata.xml
```

- [ ] **Step 6: Fix the Makefile's now-stale filter**

In `docs/papers/ai_and_ip/llm-database-theory/Makefile`, change:
```makefile
# 00-metadata.xml is an XInclude fragment (<db:info>, XIncluded into each
# article's <db:info> slot) — it has no <db:article> root, so it isn't a
# standalone document custom.rnc's `start` pattern can validate.
ARTICLES  := $(filter-out src/00-metadata.xml,$(SRCS))
```
to:
```makefile
# *.meta.xml files are XInclude fragments (<db:info>, XIncluded into each
# article's <db:info> slot) — they have no <db:article> root, so they
# aren't standalone documents docbook-corpus.rnc's `start` pattern can
# validate against the article shape.
ARTICLES  := $(filter-out %.meta.xml,$(SRCS))
```
This also generalizes correctly for the two new `*.meta.xml` files, which `$(wildcard src/0*.xml)` picks up the same way `00-metadata.xml` was.

- [ ] **Step 7: Verify the fix**

```bash
xmllint --xinclude --noout docs/papers/ai_and_ip/llm-database-theory/src/01-llm-database-theory.xml
xmllint --xinclude --noout docs/papers/ai_and_ip/llm-database-theory/src/02-legal-corpus-connections.xml
xmllint --xinclude docs/papers/ai_and_ip/llm-database-theory/src/02-legal-corpus-connections.xml 2>/dev/null | grep -c "<dc:type>"
xmllint --xinclude docs/papers/ai_and_ip/llm-database-theory/src/02-legal-corpus-connections.xml 2>/dev/null | grep "<dc:title>"
cd docs/papers/ai_and_ip/llm-database-theory && make validate && make html
grep -o "<title>.*</title>" generated/02-legal-corpus-connections.html
cd -
```
Expected: both `xmllint --xinclude --noout` calls succeed silently; the `dc:type` count is `1`; `dc:title` reads "Legal Corpus Connections: How the LLM-Database Theory Connects to Existing Matters in This Repository"; `make validate`/`make html` succeed; the final `grep` shows the correct title, not article 1's.

- [ ] **Step 8: Commit**

```bash
git add docs/papers/ai_and_ip/llm-database-theory/src/01-llm-database-theory.meta.xml \
        docs/papers/ai_and_ip/llm-database-theory/src/02-legal-corpus-connections.meta.xml \
        docs/papers/ai_and_ip/llm-database-theory/src/01-llm-database-theory.xml \
        docs/papers/ai_and_ip/llm-database-theory/src/02-legal-corpus-connections.xml \
        docs/papers/ai_and_ip/llm-database-theory/Makefile \
        docs/common/shared-metadata.xml
git rm docs/papers/ai_and_ip/llm-database-theory/src/00-metadata.xml
git commit -m "fix: give each paper article its own DCTERMS metadata, fixing the shared-00-metadata.xml bug that leaked article 1's title into article 2's built HTML"
```

---

### Task 2: Make `write_metadata()` DCTERMS-complete and backfill the existing corpus

**Files:**
- Modify: `docs/scripts/convert_to_docbook.py:176-189` (`write_metadata`), add `derive_date`, `derive_identifier`, `derive_subject`
- Create: `docs/scripts/backfill_dcterms_metadata.py`
- Test: `docs/scripts/tests/test_convert_to_docbook.py`

**Interfaces:**
- Consumes: `REPO_ROOT`, `DB_NS`, `XI_NS`, `DC_NS`, `element_full_text()` (all already defined in `convert_to_docbook.py`).
- Produces: `write_metadata(meta_path, title, subject=None)` — same signature plus one new optional keyword, so all 8 existing call sites (`convert_to_docbook.py:359`, `atomize_existing_document.py:82`, `build_bibliography.py:615`, and 5 test call sites) keep working unchanged. `derive_subject(meta_path) -> str`, `derive_date(meta_path) -> str` (`YYYY-MM-DD`), `derive_identifier(meta_path) -> str` (GitHub blob URL) — used directly by Task 3's schema-conformance expectations.

- [ ] **Step 1: Write the failing tests**

Add to `docs/scripts/tests/test_convert_to_docbook.py` (find the existing `write_metadata` import pattern used by other tests in this file and match it):

```python
class TestWriteMetadataDcterms(unittest.TestCase):
    def test_derive_subject_from_matter_path(self):
        from convert_to_docbook import derive_subject, REPO_ROOT
        path = REPO_ROOT / "docs" / "court-record" / "matters" / "cooperative-investment-law" / "findings.meta.xml"
        self.assertEqual(derive_subject(path), "legal matter: cooperative investment law")

    def test_derive_subject_from_theory_path(self):
        from convert_to_docbook import derive_subject, REPO_ROOT
        path = (REPO_ROOT / "docs" / "court-record" / "theory" / "federal-constitutional"
                / "extensions" / "example.meta.xml")
        self.assertEqual(derive_subject(path), "legal theory: federal constitutional -- extensions")

    def test_derive_subject_from_cross_cutting_path(self):
        from convert_to_docbook import derive_subject, REPO_ROOT
        path = REPO_ROOT / "docs" / "cross-cutting" / "patron-as-client.meta.xml"
        self.assertEqual(derive_subject(path), "cross-cutting analysis")

    def test_derive_identifier_is_a_github_blob_url(self):
        from convert_to_docbook import derive_identifier, REPO_ROOT
        path = REPO_ROOT / "docs" / "wip" / "jpa-and-city-cooperatives.meta.xml"
        self.assertEqual(
            derive_identifier(path),
            "https://github.com/metavacua/legal-theory/blob/main/docs/wip/jpa-and-city-cooperatives.xml",
        )

    def test_write_metadata_adds_dcterms_fields(self):
        from convert_to_docbook import write_metadata, REPO_ROOT, DC_NS
        out_dir = Path(tempfile.mkdtemp(dir=REPO_ROOT / "docs" / "wip"))
        self.addCleanup(shutil.rmtree, out_dir)
        meta_path = out_dir / "sample.meta.xml"
        write_metadata(meta_path, "Sample Title")

        root = ET.parse(meta_path).getroot()
        self.assertEqual(root.find(f"{{{DC_NS}}}title").text, "Sample Title")
        self.assertEqual(root.find(f"{{{DC_NS}}}subject").text, "work in progress")
        self.assertRegex(root.find(f"{{{DC_NS}}}date").text, r"^\d{4}-\d{2}-\d{2}$")
        self.assertTrue(
            root.find(f"{{{DC_NS}}}identifier").text.startswith(
                "https://github.com/metavacua/legal-theory/blob/main/"
            )
        )

    def test_write_metadata_accepts_explicit_subject_override(self):
        from convert_to_docbook import write_metadata, REPO_ROOT, DC_NS
        out_dir = Path(tempfile.mkdtemp(dir=REPO_ROOT / "docs" / "wip"))
        self.addCleanup(shutil.rmtree, out_dir)
        meta_path = out_dir / "sample.meta.xml"
        write_metadata(meta_path, "Sample Title", subject="a custom subject")

        root = ET.parse(meta_path).getroot()
        self.assertEqual(root.find(f"{{{DC_NS}}}subject").text, "a custom subject")
```
(This file already imports `unittest`, `Path`, `ET`, `tempfile`, `shutil` at the top — reuse those, don't re-import.)

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python3 -m unittest docs.scripts.tests.test_convert_to_docbook -v 2>&1 | grep -A2 Dcterms`
Expected: `AttributeError` / `ImportError` — `derive_subject`, `derive_identifier` don't exist yet, and `write_metadata` doesn't emit `dc:subject`/`dc:date`/`dc:identifier`.

- [ ] **Step 3: Implement the three helpers and update `write_metadata()`**

In `docs/scripts/convert_to_docbook.py`, add near the top-level imports:
```python
from datetime import date as _date
```

Add after `element_full_text()` (before `slugify()`, so both are available to what follows):
```python
GITHUB_REPO_URL = "https://github.com/metavacua/legal-theory"


def _content_path_for_meta(meta_path):
    """The sibling content .xml a .meta.xml file describes -- strips the
    ".meta" segment from the stem (patron-as-client.meta.xml ->
    patron-as-client.xml), falling back to meta_path itself for a file
    that doesn't follow that convention (e.g. a bare .xml passed in
    directly by a caller)."""
    meta_path = Path(meta_path)
    name = meta_path.name
    if name.endswith(".meta.xml"):
        return meta_path.parent / (name[: -len(".meta.xml")] + ".xml")
    return meta_path


def derive_date(meta_path):
    """dcterms:date value (YYYY-MM-DD): the author date of the most
    recent commit touching this document's content file, via git --
    the actual date the document's substance last changed, not today's
    date. Falls back to today (UTC) only when git has no history for the
    path yet (a brand-new, not-yet-committed file)."""
    content_path = _content_path_for_meta(meta_path)
    result = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "log", "-1", "--format=%aI", "--", str(content_path)],
        capture_output=True, text=True,
    )
    iso = result.stdout.strip()
    return iso[:10] if iso else _date.today().isoformat()


def derive_identifier(meta_path):
    """dcterms:identifier value: a GitHub blob permalink (on main) to the
    document's content file -- the same repo docs/common/shared-metadata.xml
    already names in dc:publisher, so this is a real, resolvable external
    URI rather than a locally-invented URN."""
    content_path = _content_path_for_meta(meta_path)
    rel = content_path.resolve().relative_to(REPO_ROOT).as_posix()
    return f"{GITHUB_REPO_URL}/blob/main/{rel}"


def derive_subject(meta_path):
    """dcterms:subject value: a coarse phrase derived from the document's
    corpus location, not a manual per-document topic reclassification.
    Documents under court-record/matters/<matter> or
    court-record/theory/<branch>/<posture> get a subject built from those
    path segments; everything else maps by top-level docs/ subdirectory."""
    def humanize(segment):
        return segment.replace("-", " ")

    rel_parts = Path(meta_path).resolve().relative_to(REPO_ROOT / "docs").parts
    if rel_parts[:2] == ("court-record", "matters"):
        return f"legal matter: {humanize(rel_parts[2])}"
    if rel_parts[:2] == ("court-record", "theory"):
        return f"legal theory: {humanize(rel_parts[2])} -- {humanize(rel_parts[3])}"
    if rel_parts[0] == "proposals":
        return f"{humanize(rel_parts[1])} proposal"
    if rel_parts[0] == "cross-cutting":
        return "cross-cutting analysis"
    if rel_parts[0] == "wip":
        return "work in progress"
    if rel_parts[0] == "bibliography":
        return "bibliography"
    return humanize(rel_parts[0])
```

Replace `write_metadata()` (lines 176-189) with:
```python
def write_metadata(meta_path, title, subject=None):
    meta_path = Path(meta_path)
    docs_dir = (REPO_ROOT / "docs").resolve()
    meta_dir = meta_path.resolve().parent
    depth = len(meta_dir.relative_to(docs_dir).parts)
    shared_href = "../" * depth + "common/shared-metadata.xml"
    escaped_title = xml_escape(title)
    resolved_subject = subject if subject is not None else derive_subject(meta_path)
    date = derive_date(meta_path)
    identifier = derive_identifier(meta_path)
    content = f"""<?xml version="1.0" encoding="UTF-8"?>
<info xmlns="{DB_NS}" xmlns:dc="http://purl.org/dc/terms/" xmlns:xi="{XI_NS}">
  <dc:title>{escaped_title}</dc:title>
  <dc:date>{date}</dc:date>
  <dc:identifier>{xml_escape(identifier)}</dc:identifier>
  <dc:subject>{xml_escape(resolved_subject)}</dc:subject>
  <xi:include href="{shared_href}" />
</info>
"""
    meta_path.write_text(content, encoding="utf-8")
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python3 -m unittest docs.scripts.tests.test_convert_to_docbook -v 2>&1 | tail -30`
Expected: all `TestWriteMetadataDcterms` tests `PASS`, and every pre-existing test in the file still passes (they only assert on `dc:title`/structure, not the absence of the three new fields).

- [ ] **Step 5: Write the backfill script**

Create `docs/scripts/backfill_dcterms_metadata.py`:
```python
"""One-shot regeneration of every existing corpus .meta.xml through the
DCTERMS-complete write_metadata() (see
docs/superpowers/plans/2026-07-25-external-metadata-ontology-standardization.md,
Task 2). Every corpus .meta.xml is, today, nothing but the write_metadata()
boilerplate (a single dc:title plus one xi:include) -- so regenerating them
in place from their own existing title is lossless, not a guess."""

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from convert_to_docbook import REPO_ROOT, DC_NS, element_full_text, write_metadata  # noqa: E402

EXCLUDE_TOP_LEVEL = {"papers", "scripts"}


def find_corpus_meta_files():
    docs_dir = REPO_ROOT / "docs"
    for meta_path in sorted(docs_dir.rglob("*.meta.xml")):
        rel_parts = meta_path.resolve().relative_to(docs_dir).parts
        if rel_parts[0] in EXCLUDE_TOP_LEVEL:
            continue
        yield meta_path


def backfill(meta_path):
    root = ET.parse(meta_path).getroot()
    title_el = root.find(f"{{{DC_NS}}}title")
    title = element_full_text(title_el)
    write_metadata(meta_path, title)


def main(argv=None):
    count = 0
    for meta_path in find_corpus_meta_files():
        backfill(meta_path)
        count += 1
    print(f"OK: regenerated {count} .meta.xml files with dc:date/dc:identifier/dc:subject")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 6: Run it against the real corpus and spot-check**

```bash
python3 docs/scripts/backfill_dcterms_metadata.py
git diff --stat docs/cross-cutting docs/wip docs/court-record docs/proposals docs/bibliography | tail -5
cat docs/cross-cutting/patron-as-client.meta.xml
xmllint --xinclude --noout docs/cross-cutting/patron-as-client.xml
```
Expected: prints `OK: regenerated 118 .meta.xml files ...`; the sample file now has `dc:subject`/`dc:date`/`dc:identifier` alongside the original `dc:title`; `xmllint --xinclude --noout` still succeeds (no schema tightened yet, so nothing can fail here).

- [ ] **Step 7: Rebuild corpus HTML so committed HTML doesn't silently drift from the now-changed XML**

```bash
while IFS= read -r xml; do
  xsltproc --xinclude docs/xsl/html5.xsl "$xml" > "${xml%.xml}.html"
done < <(find docs -name '*.xml' -not -path '*/scratch/*' -not -path 'docs/papers/*' -not -path 'docs/scripts/*' | sort)
git status --short docs | head -20
```

- [ ] **Step 8: Commit**

```bash
git add docs/scripts/convert_to_docbook.py docs/scripts/backfill_dcterms_metadata.py \
        docs/scripts/tests/test_convert_to_docbook.py
git add docs/cross-cutting docs/wip docs/court-record docs/proposals docs/bibliography
git commit -m "feat: make write_metadata() DCTERMS-complete (dc:date/identifier/subject) and backfill the existing corpus"
```

---

### Task 3: Tighten `docs/schema/docbook-corpus.rnc` to actually require DCTERMS completeness

**Files:**
- Modify: `docs/schema/docbook-corpus.rnc`
- Test: run `jing` directly against the whole corpus (no new Python test — this schema has no existing pytest coverage; validating with the actual tool it's written for is the correct test here, matching how the rest of this schema is already verified)

**Interfaces:**
- Consumes: every corpus document now satisfying `dc:title`/`dc:date`/`dc:identifier`/`dc:subject` directly on `db:info`, and `docs/common/shared-metadata.xml` satisfying `dc:creator`/`dc:publisher`/`dc:type`/`dc:language`/`dc:rights`/`dc:license`/`authorgroup`/`legalnotice` on its own `db:shared` root (both true as of Task 1+2).
- Produces: `start = article-pattern | shared-metadata-file`, so `jing -c docs/schema/docbook-corpus.rnc <any corpus article>` and `jing -c docs/schema/docbook-corpus.rnc docs/common/shared-metadata.xml` both work — the second is new, wired into CI by Task 4.

- [ ] **Step 1: Confirm this would currently fail (proving the tightening has teeth)**

This step has no separate "write a failing test" — the failing case is real corpus data before this task, so:
```bash
git stash
# (hypothetically) run jing against a document missing dc:date -- skip if Task 2 already ran;
# instead confirm the *current* schema's info pattern really is unconstrained:
grep -n "element db:info" docs/schema/docbook-corpus.rnc
git stash pop
```
Expected: `element db:info { any }` — confirms today's schema imposes no metadata requirement at all, which is exactly what this task fixes.

- [ ] **Step 2: Edit the schema**

Replace the top of `docs/schema/docbook-corpus.rnc`:
```
namespace db     = "http://docbook.org/ns/docbook"
namespace xi     = "http://www.w3.org/2001/XInclude"
namespace xlink  = "http://www.w3.org/1999/xlink"
namespace local  = ""
```
with:
```
datatypes xsd = "http://www.w3.org/2001/XMLSchema-datatypes"

namespace db     = "http://docbook.org/ns/docbook"
namespace dc     = "http://purl.org/dc/terms/"
namespace xi     = "http://www.w3.org/2001/XInclude"
namespace xlink  = "http://www.w3.org/1999/xlink"
namespace local  = ""
```

Add, right after the `finding-section` definition and before `start`:
```
# Required DCTERMS (http://purl.org/dc/terms/) fields on a document's
# <info> root. This validates a *.meta.xml file directly (its own root
# element is <info>) -- not <info> nested inside <db:article>, because in
# every real article that slot holds a literal, unresolved
# <xi:include href="....meta.xml"/> when jing runs (jing is invoked
# WITHOUT --xinclude throughout this pipeline), never a literal <info>.
# So info-element is a top-level `start` alternative alongside
# article-pattern, exercised by running jing directly against each
# *.meta.xml file (Task 4 wires this into CI/Makefile) -- not by
# validating articles. dc:creator/publisher/type/language/rights/
# license/authorgroup/legalnotice live inside the file *.meta.xml itself
# xi:includes and are validated separately, against shared-metadata-file
# below, not here.
info-element =
  element db:info {
    element dc:title      { text } &
    element dc:date       { xsd:date } &
    element dc:identifier { xsd:anyURI } &
    element dc:subject    { text } &
    element xi:include    { attribute href { xsd:anyURI } } &
    (element dc:description { text })? &
    (element db:bibliomisc { any })* &
    (element db:abstract { any })?
  }

# docs/common/shared-metadata.xml's own root shape -- validated directly
# (jing -c docbook-corpus.rnc docs/common/shared-metadata.xml), not as
# part of any article. dc:type is fixed to the DCMI Type Vocabulary
# (http://purl.org/dc/dcmitype/) term "Text": the Schema.org @type
# distinguishing a scholarly article from a findings memo belongs in the
# JSON-LD block, not here.
shared-metadata-file =
  element db:shared {
    element dc:creator   { text } &
    element dc:publisher { text } &
    element dc:type      { "Text" } &
    element dc:language  { xsd:language } &
    element dc:rights    { text } &
    element dc:license   { xsd:anyURI } &
    element db:authorgroup { any } &
    element db:legalnotice { any }
  }
```

Replace the `start` production's `element db:info { any }` alternative and its opening `start =` line. `info-element` is **not** one of the choices inside `db:article`'s content — every real article's info slot holds a literal `<xi:include>` there when jing validates it (unresolved), never a literal `<info>` — so `info-element` becomes its own top-level `start` alternative, validated by pointing jing directly at a `*.meta.xml` file instead:
```
start =
  element db:article {
    attribute version   { "5.2" },
    attribute xml:id    { xsd:NCName }?,
    attribute xml:lang  { xsd:language }?,
    ( element xi:include { attribute href { xsd:anyURI } }
    | element db:title  { text }
    | element db:subtitle { text }
    | block-content
    )*
  }
  | info-element
  | shared-metadata-file
```

- [ ] **Step 3: Validate the whole corpus — both the articles (unchanged shape) and, for the first time, the `.meta.xml` files themselves**

```bash
find docs -name '*.xml' -not -path '*/scratch/*' -not -path 'docs/papers/*' -not -path 'docs/scripts/*' | while read -r xml; do
  root_element="$(xmllint --xpath 'name(/*)' "$xml" 2>/dev/null || true)"
  [ "$root_element" = "article" ] || continue
  jing -c docs/schema/docbook-corpus.rnc "$xml" || echo "FAILED: $xml"
done
find docs -name '*.meta.xml' -not -path 'docs/papers/*' -not -path 'docs/scripts/*' | while read -r meta; do
  jing -c docs/schema/docbook-corpus.rnc "$meta" || echo "FAILED: $meta"
done
jing -c docs/schema/docbook-corpus.rnc docs/common/shared-metadata.xml
```
Expected: no `FAILED:` lines in either loop (the `.meta.xml` loop is the one that actually exercises `info-element`'s new DCTERMS requirement — Task 2's backfill is what makes it pass); `jing` on `shared-metadata.xml` prints nothing (success).

- [ ] **Step 4: Commit**

```bash
git add docs/schema/docbook-corpus.rnc
git commit -m "feat(schema): require DCTERMS core fields on every article's info, and validate shared-metadata.xml's own shape"
```

---

### Task 4: Close the CI validation gap for the flagship paper and for `shared-metadata.xml`

**Files:**
- Modify: `.github/workflows/build-papers.yml`
- Modify: `.github/workflows/build-corpus.yml`
- Modify: `docs/papers/ai_and_ip/llm-database-theory/Makefile`

**Interfaces:**
- Consumes: `make validate` (already defined in the paper's Makefile, runs `jing` when installed), `docs/schema/docbook-corpus.rnc`'s new `info-element` and `shared-metadata-file` `start` alternatives (Task 3).

- [ ] **Step 1: Confirm the current gaps**

```bash
grep -A2 "Install DocBook toolchain" .github/workflows/build-papers.yml
grep "make " .github/workflows/build-papers.yml
grep -A3 "Custom RELAX NG validation" docs/papers/ai_and_ip/llm-database-theory/Makefile
```
Expected: the install step lists `libxml2-utils xsltproc` (no `jing`), the only `make` invocation is `make html` (confirms `make validate` never runs in CI); the Makefile's RNC loop runs `for f in $(ARTICLES)`, which — per Task 1's fix — is `$(filter-out %.meta.xml,$(SRCS))`, so it never runs `jing` against the `*.meta.xml` files at all. `info-element` (Task 3) is validated by pointing `jing` directly at a `.meta.xml` file — this loop is the only place that ever happens for the paper, and today it's excluded on purpose (originally to skip a fragment with no `db:article` root, which is still correct — that fragment needs `jing` run against it, just not through the `db:article`-shaped `ARTICLES` loop).

- [ ] **Step 2: Add a `*.meta.xml` validation loop to the paper's Makefile**

In `docs/papers/ai_and_ip/llm-database-theory/Makefile`, change:
```makefile
	@echo "==> Custom RELAX NG validation"
	@which jing >/dev/null 2>&1 && \
	  for f in $(ARTICLES); do \
	    jing -c ../../../schema/docbook-corpus.rnc "$$f" && echo "    OK: $$f" || true; \
	  done || echo "    (jing not installed; skipping RELAX NG step)"
```
to:
```makefile
	@echo "==> Custom RELAX NG validation"
	@which jing >/dev/null 2>&1 && \
	  for f in $(ARTICLES); do \
	    jing -c ../../../schema/docbook-corpus.rnc "$$f" && echo "    OK: $$f" || true; \
	  done || echo "    (jing not installed; skipping RELAX NG step)"
	@echo "==> Metadata (info-element) validation"
	@which jing >/dev/null 2>&1 && \
	  for f in $(filter %.meta.xml,$(SRCS)); do \
	    jing -c ../../../schema/docbook-corpus.rnc "$$f" && echo "    OK: $$f" || true; \
	  done || echo "    (jing not installed; skipping metadata validation)"
```

- [ ] **Step 3: Edit `build-papers.yml`**

Change:
```yaml
      - name: Install DocBook toolchain
        run: sudo apt-get update && sudo apt-get install -y libxml2-utils xsltproc

      - name: Build HTML
        working-directory: docs/papers/ai_and_ip/llm-database-theory
        run: make html
```
to:
```yaml
      - name: Install DocBook toolchain
        run: sudo apt-get update && sudo apt-get install -y libxml2-utils xsltproc jing

      - name: Validate
        working-directory: docs/papers/ai_and_ip/llm-database-theory
        run: make validate

      - name: Build HTML
        working-directory: docs/papers/ai_and_ip/llm-database-theory
        run: make html
```

- [ ] **Step 4: Add the `shared-metadata.xml` and corpus-wide `.meta.xml` checks to `build-corpus.yml`**

In `.github/workflows/build-corpus.yml`, change:
```yaml
      - name: Validate and rebuild corpus HTML
        run: |
          set -euo pipefail
          while IFS= read -r xml; do
            root_element="$(xmllint --xpath 'name(/*)' "$xml" 2>/dev/null || true)"
            if [ "$root_element" != "article" ]; then
              continue
            fi
            echo "== $xml =="
            xmllint --noout --xinclude "$xml"
            jing -c docs/schema/docbook-corpus.rnc "$xml"
            xsltproc --xinclude docs/xsl/html5.xsl "$xml" > "${xml%.xml}.html"
          done < <(find docs -name '*.xml' -not -path '*/scratch/*' -not -path 'docs/papers/*' -not -path 'docs/scripts/*' | sort)
```
to:
```yaml
      - name: Validate and rebuild corpus HTML
        run: |
          set -euo pipefail
          jing -c docs/schema/docbook-corpus.rnc docs/common/shared-metadata.xml
          while IFS= read -r meta; do
            echo "== $meta =="
            jing -c docs/schema/docbook-corpus.rnc "$meta"
          done < <(find docs -name '*.meta.xml' -not -path 'docs/papers/*' -not -path 'docs/scripts/*' | sort)
          while IFS= read -r xml; do
            root_element="$(xmllint --xpath 'name(/*)' "$xml" 2>/dev/null || true)"
            if [ "$root_element" != "article" ]; then
              continue
            fi
            echo "== $xml =="
            xmllint --noout --xinclude "$xml"
            jing -c docs/schema/docbook-corpus.rnc "$xml"
            xsltproc --xinclude docs/xsl/html5.xsl "$xml" > "${xml%.xml}.html"
          done < <(find docs -name '*.xml' -not -path '*/scratch/*' -not -path 'docs/papers/*' -not -path 'docs/scripts/*' | sort)
```
The new `.meta.xml` loop is what actually exercises `info-element`'s DCTERMS requirement corpus-wide — the pre-existing article loop still only ever sees a literal `<xi:include>` in the info slot, same as before.

- [ ] **Step 5: Verify locally (the closest available approximation to running the workflow)**

```bash
which jing xsltproc xmllint
cd docs/papers/ai_and_ip/llm-database-theory && make validate && cd -
jing -c docs/schema/docbook-corpus.rnc docs/common/shared-metadata.xml
find docs -name '*.meta.xml' -not -path 'docs/papers/*' -not -path 'docs/scripts/*' | while read -r meta; do
  jing -c docs/schema/docbook-corpus.rnc "$meta" || echo "FAILED: $meta"
done
```
Expected: all three tools present; `make validate` now prints an `OK:` line for both `01-llm-database-theory.meta.xml` and `02-legal-corpus-connections.meta.xml` under its new "Metadata (info-element) validation" section; the `shared-metadata.xml` check and the corpus `.meta.xml` loop both succeed with no `FAILED:` lines.

- [ ] **Step 6: Commit**

```bash
git add .github/workflows/build-papers.yml .github/workflows/build-corpus.yml \
        docs/papers/ai_and_ip/llm-database-theory/Makefile
git commit -m "ci: actually validate the flagship paper (jing was never installed), and validate .meta.xml files and shared-metadata.xml directly (info-element was previously unreachable)"
```

---

### Task 5: Generate Schema.org JSON-LD from DCTERMS fields instead of hand-duplicating it

**Files:**
- Modify: `docs/xsl/html5.xsl`
- Modify: `docs/papers/ai_and_ip/llm-database-theory/src/01-llm-database-theory.meta.xml` (remove the hand-authored `bibliomisc` JSON-LD)
- Modify: `docs/papers/ai_and_ip/llm-database-theory/src/02-legal-corpus-connections.meta.xml` (same)

**Interfaces:**
- Consumes: `db:info/dc:title`, `dc:subject`, `dc:description`, `dc:date`, `db:info//dc:creator`, `db:info//dc:rights`, `db:info//dc:license` (all present after Tasks 1-2).
- Produces: a `<script type="application/ld+json">` block generated per page, identical in content to what the hand-authored blob produced for the two paper pages today, but now also rendered for every other corpus document (which previously had none at all).

- [ ] **Step 1: Confirm today's pass-through behavior**

```bash
sed -n '40,50p' docs/xsl/html5.xsl
```
Expected: `xsl:value-of select="db:info/db:bibliomisc[@role='schema-org-jsonld']"` — a verbatim copy, not a generation.

- [ ] **Step 2: Replace the JSON-LD block in `html5.xsl`**

Find:
```xml
        <!-- Schema.org JSON-LD (extracted from bibliomisc element) -->
        <xsl:if test="db:info/db:bibliomisc[@role='schema-org-jsonld']">
          <script type="application/ld+json">
            <xsl:value-of select="db:info/db:bibliomisc[@role='schema-org-jsonld']"/>
          </script>
        </xsl:if>
```
Replace with:
```xml
        <!-- Schema.org JSON-LD, generated from this document's own DCTERMS
             fields -- @type defaults to CreativeWork for ordinary corpus
             documents, ScholarlyArticle for the papers/ subtree (the only
             place today with abstract/bibliomisc-worthy scholarly content). -->
        <script type="application/ld+json">
          <xsl:text>{&#10;</xsl:text>
          <xsl:text>  "@context": "https://schema.org",&#10;</xsl:text>
          <xsl:text>  "@type": "</xsl:text>
          <xsl:choose>
            <xsl:when test="contains(db:info/dc:identifier, '/papers/')">ScholarlyArticle</xsl:when>
            <xsl:otherwise>CreativeWork</xsl:otherwise>
          </xsl:choose>
          <xsl:text>",&#10;</xsl:text>
          <xsl:text>  "name": "</xsl:text><xsl:value-of select="db:info/dc:title"/><xsl:text>",&#10;</xsl:text>
          <xsl:if test="db:info/dc:date">
            <xsl:text>  "datePublished": "</xsl:text><xsl:value-of select="db:info/dc:date"/><xsl:text>",&#10;</xsl:text>
          </xsl:if>
          <xsl:text>  "inLanguage": "</xsl:text><xsl:value-of select="db:info//dc:language"/><xsl:text>",&#10;</xsl:text>
          <xsl:text>  "author": {"@type": "Person", "name": "</xsl:text><xsl:value-of select="db:info//dc:creator"/><xsl:text>"},&#10;</xsl:text>
          <xsl:text>  "publisher": {"@type": "Organization", "name": "</xsl:text><xsl:value-of select="db:info//dc:publisher"/><xsl:text>"},&#10;</xsl:text>
          <xsl:if test="db:info/dc:subject">
            <xsl:text>  "keywords": "</xsl:text><xsl:value-of select="db:info/dc:subject"/><xsl:text>",&#10;</xsl:text>
          </xsl:if>
          <xsl:if test="db:info//dc:license">
            <xsl:text>  "license": "</xsl:text><xsl:value-of select="db:info//dc:license"/><xsl:text>",&#10;</xsl:text>
          </xsl:if>
          <xsl:text>  "identifier": "</xsl:text><xsl:value-of select="db:info/dc:identifier"/><xsl:text>"&#10;</xsl:text>
          <xsl:text>}</xsl:text>
        </script>
```
`dc:identifier` (Task 2) already contains `/papers/` only for the two paper articles, so it doubles as the `@type` discriminator without a new field.

- [ ] **Step 3: Remove the now-redundant hand-authored `bibliomisc` from both paper meta files**

In `docs/papers/ai_and_ip/llm-database-theory/src/01-llm-database-theory.meta.xml` and `.../02-legal-corpus-connections.meta.xml`, delete the entire `<bibliomisc role="schema-org-jsonld">...</bibliomisc>` block from each (the XSLT now generates the equivalent content).

- [ ] **Step 4: Rebuild and diff-check**

```bash
cd docs/papers/ai_and_ip/llm-database-theory && make html && cd -
grep -A15 'application/ld+json' docs/papers/ai_and_ip/llm-database-theory/generated/01-llm-database-theory.html
while IFS= read -r xml; do
  xsltproc --xinclude docs/xsl/html5.xsl "$xml" > "${xml%.xml}.html"
done < <(find docs -name '*.xml' -not -path '*/scratch/*' -not -path 'docs/papers/*' -not -path 'docs/scripts/*' | sort)
grep -l 'application/ld+json' docs/wip/*.html | head -3
```
Expected: the paper's generated JSON-LD still has the core fields (name, author, publisher, keywords); previously-JSON-LD-less corpus pages (e.g. `docs/wip/*.html`) now have a generated block too.

- [ ] **Step 5: Commit**

```bash
git add docs/xsl/html5.xsl \
        docs/papers/ai_and_ip/llm-database-theory/src/01-llm-database-theory.meta.xml \
        docs/papers/ai_and_ip/llm-database-theory/src/02-legal-corpus-connections.meta.xml
git add docs/wip docs/cross-cutting docs/court-record docs/proposals docs/bibliography docs/papers/ai_and_ip/llm-database-theory/html
git commit -m "feat(xsl): generate Schema.org JSON-LD from DCTERMS fields corpus-wide instead of one hand-authored blob per paper article"
```

---

### Task 6: CSL-JSON bibliography export

**Files:**
- Modify: `docs/scripts/build_bibliography.py`
- Test: `docs/scripts/tests/test_build_bibliography.py`

**Interfaces:**
- Consumes: `RawEntry`, `classify_statute()`, `classify_case()`, `strip_access_date()`, `parse_bibtex()`, `LEGAL_BIB_KEYS`, `SELF_CITATION_HTML` (all existing).
- Produces: `csl_item(raw, index) -> dict | None`, `csl_item_for_bib(entry) -> dict | None`, `emit_csl_json(raw_entries, bib_entries) -> list[dict]`, wired into `main()` to write `docs/bibliography/references.csl.json`.

- [ ] **Step 1: Write the failing tests**

Add to `docs/scripts/tests/test_build_bibliography.py`:
```python
class TestCslItem(unittest.TestCase):
    def test_statute_entry_maps_to_legislation_type(self):
        from build_bibliography import csl_item, RawEntry
        raw = RawEntry(text="Cal. Civ. Code § 1550 (2024)", href="https://example.com/x",
                        citing_html="docs/x.html", source_file="docs/x.xml")
        item = csl_item(raw, 0)
        self.assertEqual(item["type"], "legislation")
        self.assertEqual(item["issued"], {"date-parts": [[2024]]})
        self.assertEqual(item["URL"], "https://example.com/x")

    def test_complete_case_entry_maps_to_legal_case_type(self):
        from build_bibliography import csl_item, RawEntry
        raw = RawEntry(text="Smith v. Jones (2020) 45 Cal. 3d 100", href=None,
                        citing_html="docs/x.html", source_file="docs/x.xml")
        item = csl_item(raw, 0)
        self.assertEqual(item["type"], "legal_case")
        self.assertEqual(item["container-title"], "Cal. 3d")
        self.assertEqual(item["volume"], "45")
        self.assertEqual(item["page"], "100")
        self.assertEqual(item["issued"], {"date-parts": [[2020]]})

    def test_bare_link_maps_to_webpage_type(self):
        from build_bibliography import csl_item, RawEntry
        raw = RawEntry(text="Some Article Title", href="https://example.com/a",
                        citing_html="docs/x.html", source_file="docs/x.xml")
        item = csl_item(raw, 0)
        self.assertEqual(item["type"], "webpage")
        self.assertEqual(item["URL"], "https://example.com/a")

    def test_unclassified_entry_with_no_link_is_omitted(self):
        from build_bibliography import csl_item, RawEntry
        raw = RawEntry(text="Some Unresolvable Note", href=None,
                        citing_html="docs/x.html", source_file="docs/x.xml")
        self.assertIsNone(csl_item(raw, 0))


class TestCslItemForBib(unittest.TestCase):
    def test_academic_entry_with_journal_maps_to_article_journal(self):
        from build_bibliography import csl_item_for_bib
        entry = {"key": "cooper2025", "entry_type": "article",
                 "fields": {"title": "Extraction Study", "journal": "arXiv",
                            "year": "2025", "author": "Cooper et al."}}
        item = csl_item_for_bib(entry)
        self.assertEqual(item["type"], "article-journal")
        self.assertEqual(item["container-title"], "arXiv")
        self.assertEqual(item["issued"], {"date-parts": [[2025]]})

    def test_legal_bib_entry_without_section_is_omitted(self):
        from build_bibliography import csl_item_for_bib, LEGAL_BIB_KEYS
        key = next(iter(LEGAL_BIB_KEYS))
        entry = {"key": key, "entry_type": "misc", "fields": {"title": "No section here"}}
        self.assertIsNone(csl_item_for_bib(entry))


class TestEmitCslJson(unittest.TestCase):
    def test_combines_raw_and_bib_entries_skipping_unclassified(self):
        from build_bibliography import emit_csl_json, RawEntry
        raw_entries = [
            RawEntry(text="Cal. Civ. Code § 1550 (2024)", href="https://example.com/x",
                      citing_html="docs/x.html", source_file="docs/x.xml"),
            RawEntry(text="Unresolvable", href=None, citing_html="docs/x.html", source_file="docs/x.xml"),
        ]
        bib_entries = [{"key": "cooper2025", "entry_type": "article",
                        "fields": {"title": "Extraction Study", "journal": "arXiv", "year": "2025"}}]
        items = emit_csl_json(raw_entries, bib_entries)
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]["type"], "legislation")
        self.assertEqual(items[1]["id"], "cooper2025")
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python3 -m unittest docs.scripts.tests.test_build_bibliography -v 2>&1 | grep -E "Csl|ImportError"`
Expected: `ImportError: cannot import name 'csl_item'` (and similarly for the other two new names).

- [ ] **Step 3: Implement**

Add to `docs/scripts/build_bibliography.py`, after `format_secondary_chicago()` (so it sits with the other classify/format functions) and before `classify_and_format()`:
```python
def csl_item(raw, index):
    """CSL-JSON item (Citation Style Language, see
    github.com/citation-style-language/schema) for a RawEntry, or None if
    it matches neither a recognized statute/case pattern nor has a link --
    CSL has no "unknown" type, and assigning one would misrepresent a
    source this pipeline genuinely can't classify."""
    statute = classify_statute(raw.text)
    if statute:
        item = {"id": f"statute-{index}", "type": "legislation",
                "title": strip_access_date(raw.text) or raw.text}
        if statute["year"]:
            item["issued"] = {"date-parts": [[int(statute["year"])]]}
        if raw.href:
            item["URL"] = raw.href
        return item

    case = classify_case(raw.text, raw.href)
    if case:
        item = {"id": f"case-{index}", "type": "legal_case", "title": case["name"]}
        if case["complete"]:
            item["issued"] = {"date-parts": [[int(case["year"])]]}
            item["container-title"] = case["reporter"]
            item["volume"] = case["volume"]
            item["page"] = case["page"]
        if raw.href:
            item["URL"] = raw.href
        return item

    if raw.href:
        return {"id": f"web-{index}", "type": "webpage",
                "title": strip_access_date(raw.text) or raw.text, "URL": raw.href}
    return None


def csl_item_for_bib(entry):
    """CSL-JSON item for a parse_bibtex() entry, or None when a "legal"
    bib entry (in LEGAL_BIB_KEYS) has no section/§ marker to justify the
    "legislation" type -- bibliography.bib doesn't carve legal entries
    into the same structured statute/case sub-fields raw corpus text
    does, so this is a narrower, more conservative check than
    classify_statute()."""
    f = entry["fields"]
    if entry["key"] in LEGAL_BIB_KEYS:
        if "section" not in f and "§" not in f.get("title", ""):
            return None
        item_type = "legislation"
    else:
        item_type = "article-journal" if (f.get("journal") or f.get("booktitle")) else "report"

    item = {"id": entry["key"], "type": item_type, "title": f.get("title", "")}
    year = f.get("year", "")
    if year.isdigit():
        item["issued"] = {"date-parts": [[int(year)]]}
    if f.get("author"):
        item["author"] = [{"literal": f["author"]}]
    if f.get("journal"):
        item["container-title"] = f["journal"]
    if f.get("volume"):
        item["volume"] = f["volume"]
    if f.get("pages"):
        item["page"] = f["pages"]
    url = SELF_CITATION_HTML.get(entry["key"]) or f.get("url")
    if url:
        item["URL"] = url
    if f.get("eprint"):
        item["number"] = f["eprint"]
    return item


def emit_csl_json(raw_entries, bib_entries):
    """The full CSL-JSON array for the corpus: one item per raw
    works-cited entry that csl_item() can classify, plus one item per
    bibliography.bib entry csl_item_for_bib() can classify, in that
    order. Unclassified entries are omitted, not guessed."""
    items = [item for item in (csl_item(r, i) for i, r in enumerate(raw_entries)) if item]
    items += [item for item in (csl_item_for_bib(e) for e in bib_entries) if item]
    return items
```

Add `import json` near the top of the file (with the other stdlib imports).

In `main()`, after the existing `build_html(xml_path, xml_path.with_suffix(".html"))` call and before the final `print(...)`, add:
```python
    csl_items = emit_csl_json(raw_entries, bib_entries)
    csl_path = out_dir / "references.csl.json"
    csl_path.write_text(json.dumps(csl_items, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python3 -m unittest docs.scripts.tests.test_build_bibliography -v 2>&1 | tail -20`
Expected: all new test classes `PASS`, all pre-existing tests still `PASS`.

- [ ] **Step 5: Regenerate the real bibliography and inspect the new file**

```bash
python3 docs/scripts/build_bibliography.py
python3 -c "import json; d = json.load(open('docs/bibliography/references.csl.json')); print(len(d), d[0])"
```
Expected: `OK: ...` from the script; the CSL-JSON file parses and its first item is well-formed.

- [ ] **Step 6: Commit**

```bash
git add docs/scripts/build_bibliography.py docs/scripts/tests/test_build_bibliography.py
git add docs/bibliography/references.csl.json
git commit -m "feat: emit a CSL-JSON bibliography export alongside the existing Bluebook/Chicago DocBook output"
```

---

### Task 7: Native DocBook bibliography vocabulary with CiTO citation-typing, on a single shared AST (lxml)

**Design correction, stated plainly:** the original design for this task generated a separate `citations.jsonld` file — a second, disconnected representation of a fact the bibliography's own elements already state. That fails the actual goal: the ontology-tagged document should *be* the semantically complete AST, not have semantics trapped in a side file only one script reads (unlike CSL-JSON in Task 6 or Schema.org in Task 5, nothing external consumes that file shape, so there was no interoperability justification for it either). This task instead (a) rewrites the consolidated bibliography using DocBook's own native `<bibliography>`/`<biblioentry>`/`<bibliomixed>` elements instead of generic `<section>`/`<orderedlist>`/`<listitem>`, and (b) puts the CiTO citation-type directly on each entry's own `<link>` via the standard XLink `xlink:arcrole` attribute (verified real: XLink's `arcrole` is specifically the attribute for characterizing the *meaning of a traversal*, and CiTO defines `citesAsAuthority`/`isCitedAsAuthorityBy` as a real, documented inverse pair) — walkable via plain XPath, not hidden in JSON. It also migrates the file's XML construction from hand-rolled f-strings to `lxml.etree` (fixing the real double-quote escaping bug from the original review) and installs `lxml` as a real, declared dependency via `apt` — the same install mechanism already used for `jing`/`xmllint`/`xsltproc` — rather than avoiding it.

**Files:**
- Modify: `.github/workflows/build-corpus.yml`, `.github/workflows/build-papers.yml` (add `python3-lxml` to the existing `apt-get install` line)
- Modify: `docs/schema/docbook-corpus.rnc` (`block-content` gains `element db:bibliography { any }` — confirmed missing today: `<bibliography>` is rejected by the current schema entirely)
- Create: `docs/scripts/corpus_ast.py`
- Modify: `docs/scripts/build_bibliography.py`
- Modify: `docs/xsl/html5.xsl` (render `db:bibliography`/`db:biblioentry`/`db:bibliomixed`, which currently have no template and would otherwise fall through to DocBook's bare-text default; add a real `db:citation` → biblioentry hyperlink)
- Modify: `docs/papers/ai_and_ip/llm-database-theory/Makefile` (pass the bibliography's relative HTML path to the XSLT)
- Test: `docs/scripts/tests/test_build_bibliography.py`, `docs/scripts/tests/test_convert_to_docbook.py`

**Interfaces:**
- Consumes: `BibliographyEntry` (`.display`, `.citing_htmls`, `.dedup_key`, and a new `.bib_key`), `relative_html_link()` (existing).
- Produces: `corpus_ast.parse_resolved`/`new_article_root`/`serialize` (consumed here and available to Task 11); `emit_docbook_tree(...) -> lxml.etree._Element`; `emit_docbook(...)` keeps its existing signature/return type (an XML string), so `main()`'s call site is unchanged.

Verified, not deferred: `grep -rl "<citation>" docs --include="*.xml"` shows `<citation>KEY</citation>` is used **only** in the paper's own 11 fragment files, and every key used matches a real `bibliography.bib` entry — a small, fixed-shape problem, not an open-ended one. This task makes that citation mechanism actually work as a real DocBook cross-reference (matching `xml:id`, resolved to a real hyperlink), rather than leaving it as a string convention that happens to look like one. This surfaced a real bug in the first draft of this task: `_entry_id()` was going to derive every `xml:id` from `dedup_key` (a hash of display text/URL) — which means `<biblioentry xml:id="...">` would **never** have actually matched `<citation>cooper2025memorized</citation>`, because `dedup_key` isn't the bib key. Fixed below by threading the real key through.

Scope note, stated plainly: this task does not add per-source-document `arcrole` tagging to each of the 119 corpus documents' own works-cited `<link>` elements (only the one, single, generated `references.xml` this task produces) — that would mean mutating up to 119 content files, a much larger undertaking distinct from fixing this generated document and the paper's citation mechanism.

- [ ] **Step 1: Confirm the schema gap and the escaping bug, directly**

```bash
cat > /tmp/native-biblio-test.xml <<'EOF'
<?xml version="1.0"?>
<article xmlns="http://docbook.org/ns/docbook" xmlns:xlink="http://www.w3.org/1999/xlink" version="5.2" xml:id="t" xml:lang="en">
  <title>T</title>
  <bibliography>
    <title>References</title>
    <biblioentry xml:id="smith2020">
      <link xlink:href="https://example.com/smith" xlink:arcrole="http://purl.org/spar/cito/isCitedAsAuthorityBy">Smith, Statute (2020)</link>
    </biblioentry>
  </bibliography>
</article>
EOF
jing -c docs/schema/docbook-corpus.rnc /tmp/native-biblio-test.xml; echo "jing exit: $? (expected 1 -- bibliography not yet permitted)"
python3 -c "from xml.sax.saxutils import escape; print(escape('a\"b'))"  # confirms the quote is never escaped
```

- [ ] **Step 2: Install `lxml` and wire it into CI**

```bash
sudo apt-get update && sudo apt-get install -y python3-lxml
python3 -c "from lxml import etree; print(etree.LIBXML_VERSION)"
```
In both `.github/workflows/build-corpus.yml` and `.github/workflows/build-papers.yml`, change the `Install DocBook toolchain` step's `apt-get install` line to also install `python3-lxml`, e.g.:
```yaml
        run: sudo apt-get update && sudo apt-get install -y libxml2-utils xsltproc jing python3-lxml
```
(`build-papers.yml`'s line doesn't install `jing` — Task 4 already added that; add `python3-lxml` to whichever line each workflow currently has.)

- [ ] **Step 3: Add `element db:bibliography` to the schema**

In `docs/schema/docbook-corpus.rnc`'s `block-content`, change:
```
  | element db:blockquote { any }
```
to:
```
  | element db:blockquote { any }
  | element db:bibliography { any }
```

Verify:
```bash
jing -c docs/schema/docbook-corpus.rnc /tmp/native-biblio-test.xml; echo "jing exit: $? (expected 0 now)"
```

- [ ] **Step 4: Write the failing tests**

Add to `docs/scripts/tests/test_build_bibliography.py` (add `from lxml import etree` at the top):
```python
class TestEmitDocbookNativeBibliography(unittest.TestCase):
    def test_uses_native_bibliography_biblioentry_bibliomixed(self):
        from build_bibliography import emit_docbook, BibliographyEntry
        legal = [BibliographyEntry(section="legal", display="Cal. Civ. Code § 1550 (2024).",
                                    citing_htmls=["docs/wip/a.html"], dedup_key="url:k1")]
        xml_string = emit_docbook(legal, [], [])
        root = etree.fromstring(xml_string.encode("utf-8"))
        bibliographies = root.findall(f".//{{{DB_NS}}}bibliography")
        self.assertEqual(len(bibliographies), 2)  # legal-citations + academic-secondary-sources
        entries = root.findall(f".//{{{DB_NS}}}biblioentry")
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].get(f"{{{XML_NS}}}id"), "url-k1")
        mixed = entries[0].find(f"{{{DB_NS}}}bibliomixed")
        self.assertEqual(mixed.text, "Cal. Civ. Code § 1550 (2024).")

    def test_link_carries_cito_arcrole_for_legal_entries(self):
        from build_bibliography import emit_docbook, BibliographyEntry
        legal = [BibliographyEntry(section="legal", display="Cal. Civ. Code § 1550 (2024).",
                                    citing_htmls=["docs/wip/a.html"], dedup_key="url:k1")]
        xml_string = emit_docbook(legal, [], [])
        root = etree.fromstring(xml_string.encode("utf-8"))
        link = root.find(f".//{{{DB_NS}}}biblioentry//{{{DB_NS}}}link")
        self.assertEqual(link.get(f"{{{XLINK_NS}}}arcrole"), "http://purl.org/spar/cito/isCitedAsAuthorityBy")

    def test_link_carries_cito_arcrole_for_secondary_entries(self):
        from build_bibliography import emit_docbook, BibliographyEntry
        secondary = [BibliographyEntry(section="secondary", display="Justia. \"X.\"",
                                        citing_htmls=["docs/wip/a.html"], dedup_key="url:k2")]
        xml_string = emit_docbook([], secondary, [])
        root = etree.fromstring(xml_string.encode("utf-8"))
        link = root.find(f".//{{{DB_NS}}}biblioentry//{{{DB_NS}}}link")
        self.assertEqual(link.get(f"{{{XLINK_NS}}}arcrole"), "http://purl.org/spar/cito/isCitedAsSourceDocumentBy")

    def test_bib_key_is_used_as_xml_id_when_present(self):
        """The whole point of matching xml:id: <citation>cooper2025memorized</citation>
        in the paper's own articles must resolve to a real <biblioentry>, so a
        bib-derived entry's xml:id must be its real bibliography.bib key, not a
        dedup_key-derived slug that would never match."""
        from build_bibliography import emit_docbook, BibliographyEntry
        legal = [BibliographyEntry(section="legal", display="Some Statute (2024).",
                                    citing_htmls=["docs/wip/a.html"], dedup_key="text:some statute (2024).",
                                    bib_key="cooper2025memorized")]
        xml_string = emit_docbook(legal, [], [])
        root = etree.fromstring(xml_string.encode("utf-8"))
        entry = root.find(f".//{{{DB_NS}}}biblioentry")
        self.assertEqual(entry.get(f"{{{XML_NS}}}id"), "cooper2025memorized")

    def test_dedupe_populates_bib_key_for_bibliography_bib_entries_only(self):
        from build_bibliography import dedupe, RawEntry
        bib_derived = ("legal", "Some Statute (2024).",
                       RawEntry(text="cooper2025memorized", href=None, citing_html="docs/x.html",
                                 source_file="docs/papers/ai_and_ip/llm-database-theory/src/bibliography.bib"))
        corpus_derived = ("legal", "Cal. Civ. Code § 1550 (2024).",
                          RawEntry(text="Cal. Civ. Code § 1550 (2024).", href=None, citing_html="docs/y.html",
                                    source_file="docs/wip/y.xml"))
        entries = dedupe([bib_derived, corpus_derived])
        by_display = {e.display: e for e in entries}
        self.assertEqual(by_display["Some Statute (2024)."].bib_key, "cooper2025memorized")
        self.assertIsNone(by_display["Cal. Civ. Code § 1550 (2024)."].bib_key)

    def test_quote_in_display_text_survives_round_trip(self):
        from build_bibliography import emit_docbook, BibliographyEntry
        legal = [BibliographyEntry(section="legal", display='Cal. Civ. Code § 1"550 (2024).',
                                    citing_htmls=["docs/wip/a.html"], dedup_key="url:k1")]
        xml_string = emit_docbook(legal, [], [])
        root = etree.fromstring(xml_string.encode("utf-8"))  # raises XMLSyntaxError if malformed
        mixed = root.find(f".//{{{DB_NS}}}bibliomixed")
        self.assertIn('1"550', mixed.text)

    def test_quote_in_citing_html_path_survives_round_trip(self):
        from build_bibliography import emit_docbook, BibliographyEntry, relative_html_link
        legal = [BibliographyEntry(section="legal", display="Some Statute (2024).",
                                    citing_htmls=['docs/wip/a"b.html'], dedup_key="url:k1")]
        xml_string = emit_docbook(legal, [], [])
        root = etree.fromstring(xml_string.encode("utf-8"))
        link = root.find(f".//{{{DB_NS}}}biblioentry//{{{DB_NS}}}link")
        self.assertEqual(link.get(f"{{{XLINK_NS}}}href"), relative_html_link('docs/wip/a"b.html'))
```

- [ ] **Step 5: Run the tests to verify they fail**

Run: `python3 -m unittest docs.scripts.tests.test_build_bibliography.TestEmitDocbookNativeBibliography -v`
Expected: fails on the current `emit_docbook` (no `db:bibliography`/`db:biblioentry` elements exist yet, and the quote-round-trip test raises `XMLSyntaxError` on the malformed `xlink:href` — the exact bug from the original review, reproduced directly).

- [ ] **Step 6: Create `docs/scripts/corpus_ast.py`**

```python
"""The corpus's one shared XML parse/serialize layer, built on lxml
(python3-lxml, installed via apt alongside the libxml2/libxslt tools
this pipeline already depends on -- not pip; this repo has no
requirements.txt/pyproject.toml, and apt is how jing/xmllint/xsltproc
are already installed in CI, so this follows the existing convention
rather than adding a second one). lxml.etree wraps the same libxml2 C
library xmllint/xsltproc already use; its native XInclude resolution
and correct attribute escaping (verified directly: xlink:href="a&quot;b"
round-trips correctly, unlike the xml.sax.saxutils.escape()-built
version) are why it replaces stdlib xml.etree.ElementTree here."""

from lxml import etree

DB_NS = "http://docbook.org/ns/docbook"
XI_NS = "http://www.w3.org/2001/XInclude"
XLINK_NS = "http://www.w3.org/1999/xlink"
XML_NS = "http://www.w3.org/XML/1998/namespace"

DOCBOOK_NSMAP = {None: DB_NS, "xi": XI_NS, "xlink": XLINK_NS}


def parse_resolved(xml_path):
    """lxml root Element for xml_path after native XInclude resolution --
    verified to correctly resolve relative hrefs nested more than one
    level deep (e.g. a fragment inside 02-legal-corpus-connections/
    referencing ../common/shared-metadata.xml), which stdlib
    xml.etree.ElementInclude does not do without extra, stateful loader
    plumbing (confirmed directly: it raised FileNotFoundError on exactly
    that case)."""
    tree = etree.parse(str(xml_path))
    tree.getroottree().xinclude()
    return tree.getroot()


def new_article_root(**attrs):
    """A new <article> lxml Element with xmlns="http://docbook.org/ns/docbook"
    (no prefix) plus xi/xlink prefixes declared once, at the root -- lxml
    has no register_namespace() equivalent for an unprefixed default
    namespace (verified directly: register_namespace("", DB_NS) raises
    ValueError under lxml); nsmap must be supplied at element-creation
    time instead. Every other element in the tree is created as a plain
    SubElement/Element with a clark-notation tag and inherits this
    context without redeclaring it (verified directly: no duplicate
    xmlns attributes appear on children)."""
    el = etree.Element(f"{{{DB_NS}}}article", nsmap=DOCBOOK_NSMAP)
    for name, value in attrs.items():
        el.set(name, value)
    return el


def serialize(element, indent=True):
    """XML string for element, via lxml's own serializer -- escapes
    attribute values correctly (including '"'), unlike
    xml.sax.saxutils.escape() hand-interpolated into f-strings."""
    if indent:
        etree.indent(element, space="  ")
    return etree.tostring(element, encoding="unicode")
```

- [ ] **Step 7: Add `bib_key` to `BibliographyEntry` and thread it through `dedupe()`**

This is what makes `<citation>cooper2025memorized</citation>` in the paper's own articles actually resolve to a real `<biblioentry xml:id="cooper2025memorized">` — without it, every entry's `xml:id` would be derived from `dedup_key` (a hash of display text/URL), which never matches a real bib key. Change the `BibliographyEntry` dataclass:
```python
@dataclass
class BibliographyEntry:
    section: str
    display: str
    citing_htmls: list
    dedup_key: str
    bib_key: str = None
```

Change `dedupe()`:
```python
def dedupe(classified):
    """[BibliographyEntry, ...] merging (section, display_text, raw_entry)
    triples that share a dedup key ... (unchanged docstring above this
    line) ... bib_key is set from a bib-derived raw entry's own text
    (main() constructs those RawEntry objects with text=entry["key"]) so
    the entry's real bibliography.bib key survives into the final
    output and can become its xml:id -- a corpus-extracted entry, which
    has no such key, keeps bib_key=None."""
    by_key = {}
    order = []
    for section, display, raw in classified:
        key = _dedup_key(display, raw.href, section)
        if key not in by_key:
            bib_key = raw.text if raw.source_file.endswith("bibliography.bib") else None
            by_key[key] = BibliographyEntry(
                section=section, display=display, citing_htmls=[], dedup_key=key, bib_key=bib_key,
            )
            order.append(key)
        entry = by_key[key]
        if raw.citing_html not in entry.citing_htmls:
            entry.citing_htmls.append(raw.citing_html)
    return [by_key[k] for k in order]
```

Run: `python3 -m unittest docs.scripts.tests.test_build_bibliography.TestEmitDocbookNativeBibliography.test_bib_key_is_used_as_xml_id_when_present docs.scripts.tests.test_build_bibliography.TestEmitDocbookNativeBibliography.test_dedupe_populates_bib_key_for_bibliography_bib_entries_only -v`
Expected (at this point, before `_entry_id()` below reads `bib_key`): `test_dedupe_populates_bib_key_for_bibliography_bib_entries_only` `PASS`; `test_bib_key_is_used_as_xml_id_when_present` still `FAIL` — `_entry_id()` doesn't consult `bib_key` yet.

- [ ] **Step 8: Migrate `build_bibliography.py`'s XML emission**

Delete `from xml.sax.saxutils import escape as xml_escape` (no longer used) and replace `_listitem_xml`, `_entry_listitem_xml`, `_appendix_listitem_xml`, `_section_xml`, and `emit_docbook` with:
```python
import re
from lxml import etree
from corpus_ast import DB_NS, XI_NS, XLINK_NS, XML_NS, new_article_root, serialize

CITO_NS = "http://purl.org/spar/cito/"
CITO_AUTHORITY_INVERSE = f"{CITO_NS}isCitedAsAuthorityBy"
CITO_SOURCE_INVERSE = f"{CITO_NS}isCitedAsSourceDocumentBy"


def _entry_id(entry):
    """A stable xml:id for a BibliographyEntry: its real bibliography.bib
    key when it has one (bib_key), so <citation>KEY</citation> in the
    paper's own articles resolves by exact xml:id match -- the real,
    standard DocBook citation-resolution mechanism, not a coincidental
    string match. Falls back to a dedup_key-derived slug for
    corpus-extracted entries, which have no natural key."""
    if entry.bib_key:
        return entry.bib_key
    safe = re.sub(r"[^A-Za-z0-9_.-]", "-", entry.dedup_key).strip("-")
    return safe[:64] or "entry"


def _biblioentry_element(entry, cito_inverse_predicate):
    biblioentry = etree.Element(f"{{{DB_NS}}}biblioentry")
    biblioentry.set(f"{{{XML_NS}}}id", _entry_id(entry))
    mixed = etree.SubElement(biblioentry, f"{{{DB_NS}}}bibliomixed")
    mixed.text = entry.display
    for html in sorted(entry.citing_htmls):
        link = etree.SubElement(biblioentry, f"{{{DB_NS}}}link")
        link.set(f"{{{XLINK_NS}}}href", relative_html_link(html))
        link.set(f"{{{XLINK_NS}}}arcrole", cito_inverse_predicate)
        link.text = html
    return biblioentry


def _bibliography_element(title, xml_id, entries, cito_inverse_predicate):
    bibliography = etree.Element(f"{{{DB_NS}}}bibliography")
    bibliography.set(f"{{{XML_NS}}}id", xml_id)
    title_el = etree.SubElement(bibliography, f"{{{DB_NS}}}title")
    title_el.text = title
    for e in sorted(entries, key=lambda e: e.display.lower()):
        bibliography.append(_biblioentry_element(e, cito_inverse_predicate))
    return bibliography


def emit_docbook_tree(legal_entries, secondary_entries, appendix_entries):
    """The full <article> lxml Element for the consolidated bibliography.
    Legal and secondary sources are modeled with DocBook's own
    <bibliography>/<biblioentry>/<bibliomixed> vocabulary, not generic
    <section>/<orderedlist>/<listitem> -- and each entry's citing-page
    backlink carries a real CiTO (purl.org/spar/cito) xlink:arcrole,
    walkable via plain XPath, instead of a separate citations.jsonld file
    nothing outside this pipeline consumed. Appendix entries stay as
    plain listitems: they have no reliable classification, and modeling
    them as biblioentries would falsely imply one exists."""
    article = new_article_root(version="5.2")
    article.set(f"{{{XML_NS}}}id", "references")
    article.set(f"{{{XML_NS}}}lang", "en")

    xi_include = etree.SubElement(article, f"{{{XI_NS}}}include")
    xi_include.set("href", "references.meta.xml")

    title_el = etree.SubElement(article, f"{{{DB_NS}}}title")
    title_el.text = "Consolidated References & Bibliography"

    methodology = etree.SubElement(article, f"{{{DB_NS}}}section")
    methodology.set(f"{{{XML_NS}}}id", "methodology")
    m_title = etree.SubElement(methodology, f"{{{DB_NS}}}title")
    m_title.text = "Scope and Citation Policy"
    m_para = etree.SubElement(methodology, f"{{{DB_NS}}}para")
    m_para.text = METHODOLOGY_PARA

    article.append(_bibliography_element(
        "Legal Citations", "legal-citations", legal_entries, CITO_AUTHORITY_INVERSE,
    ))
    article.append(_bibliography_element(
        "Academic and Secondary Sources", "academic-secondary-sources", secondary_entries, CITO_SOURCE_INVERSE,
    ))

    appendix = etree.SubElement(article, f"{{{DB_NS}}}section")
    appendix.set(f"{{{XML_NS}}}id", "appendix-needs-review")
    a_title = etree.SubElement(appendix, f"{{{DB_NS}}}title")
    a_title.text = "Appendix: Entries Needing Manual Review"
    a_olist = etree.SubElement(appendix, f"{{{DB_NS}}}orderedlist")
    a_olist.set("numeration", "arabic")
    a_olist.set("spacing", "compact")
    for text, source_file in appendix_entries:
        li = etree.SubElement(a_olist, f"{{{DB_NS}}}listitem")
        p1 = etree.SubElement(li, f"{{{DB_NS}}}para")
        p1.text = text
        p2 = etree.SubElement(li, f"{{{DB_NS}}}para")
        p2.text = f"Source: {source_file}"

    return article


def emit_docbook(legal_entries, secondary_entries, appendix_entries):
    """XML string for the consolidated bibliography: serializes
    emit_docbook_tree()'s Element tree once, via lxml's own (correct)
    serializer. Signature and return type are unchanged from before this
    task -- main()'s call site needs no edit."""
    article = emit_docbook_tree(legal_entries, secondary_entries, appendix_entries)
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + serialize(article) + "\n"
```
Note: the namespace-declaration placement in the serialized output (all three `xmlns`/`xmlns:xi`/`xmlns:xlink` now sit on `<article>` itself, since `new_article_root()` declares them there) matches the original hand-written template's placement — no cosmetic drift this time, since the root's `nsmap` is fixed at creation.

- [ ] **Step 8: Add HTML rendering for the new elements**

`docs/xsl/html5.xsl` has no template for `db:bibliography`/`db:biblioentry`/`db:bibliomixed` today, so they'd fall through to DocBook's default (bare, unstyled text — verified directly). Add:
```xml
  <xsl:template match="db:bibliography">
    <section class="bibliography">
      <h2><xsl:value-of select="db:title"/></h2>
      <ol class="biblioentry-list">
        <xsl:apply-templates select="db:biblioentry"/>
      </ol>
    </section>
  </xsl:template>

  <xsl:template match="db:biblioentry">
    <li id="{@xml:id}">
      <xsl:value-of select="db:bibliomixed"/>
      <xsl:if test="db:link">
        <span class="cited-in"> Cited in:
          <xsl:for-each select="db:link">
            <a href="{@xlink:href}"><xsl:value-of select="."/></a><xsl:if test="position() != last()">; </xsl:if>
          </xsl:for-each>
        </span>
      </xsl:if>
    </li>
  </xsl:template>
```

- [ ] **Step 9: Run the tests to verify they pass**

Run: `python3 -m unittest docs.scripts.tests.test_build_bibliography -v 2>&1 | tail -40`
Expected: all `TestEmitDocbookNativeBibliography` tests `PASS` now (including `test_bib_key_is_used_as_xml_id_when_present`); every pre-existing test in the file still `PASS`.

- [ ] **Step 10: Make `<citation>KEY</citation>` in the paper's own articles a real hyperlink to its `<biblioentry xml:id="KEY">`**

Add to `docs/xsl/html5.xsl` (near the top, alongside other top-level declarations):
```xml
  <xsl:param name="bibliography-href" select="''"/>
```
Add a template for `db:citation`:
```xml
  <xsl:template match="db:citation">
    <xsl:choose>
      <xsl:when test="$bibliography-href != ''">
        <a href="{$bibliography-href}#{.}" class="citation">[<xsl:value-of select="."/>]</a>
      </xsl:when>
      <xsl:otherwise>
        <cite>[<xsl:value-of select="."/>]</cite>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>
```
`bibliography-href` defaults to empty (ordinary corpus documents have no `<citation>` elements and don't need it) and is only ever passed by the paper's own build (next step) — a document built without the param falls back to the old bracket-text rendering, so nothing else in the corpus is affected.

In `docs/papers/ai_and_ip/llm-database-theory/Makefile`, change the HTML build rule:
```makefile
generated/%.html: src/%.xml ../../../xsl/html5.xsl | generated
	xsltproc --xinclude ../../../xsl/html5.xsl $< > $@
	@echo "==> generated/$*.html"
```
to:
```makefile
generated/%.html: src/%.xml ../../../xsl/html5.xsl | generated
	xsltproc --xinclude --stringparam bibliography-href ../../../../bibliography/references.html ../../../xsl/html5.xsl $< > $@
	@echo "==> generated/$*.html"
```
(`docs/papers/ai_and_ip/llm-database-theory/generated/X.html` is 4 directories below `docs/`, so `../../../../bibliography/references.html` is the correct, fixed relative path — verified directly with `xsltproc --stringparam` against a standalone test file before writing this.)

Add to `docs/scripts/tests/test_convert_to_docbook.py`:
```python
class TestCitationResolvesToBibliographyHyperlink(unittest.TestCase):
    def test_citation_becomes_a_real_link_when_bibliography_href_is_given(self):
        import subprocess
        from convert_to_docbook import REPO_ROOT, HTML5_XSL_PATH
        fixture = REPO_ROOT / "docs" / "scripts" / "tests" / "fixtures" / "citation_sample.xml"
        fixture.parent.mkdir(parents=True, exist_ok=True)
        fixture.write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<article xmlns="http://docbook.org/ns/docbook" version="5.2" xml:id="s" xml:lang="en">\n'
            '  <title>S</title>\n'
            '  <para>See <citation>cooper2025memorized</citation>.</para>\n'
            '</article>\n',
            encoding="utf-8",
        )
        self.addCleanup(fixture.unlink)
        result = subprocess.run(
            ["xsltproc", "--xinclude", "--stringparam", "bibliography-href",
             "../../../../bibliography/references.html", str(HTML5_XSL_PATH), str(fixture)],
            capture_output=True, text=True, check=True,
        )
        self.assertIn(
            '<a href="../../../../bibliography/references.html#cooper2025memorized"',
            result.stdout,
        )
```

Run: `python3 -m unittest docs.scripts.tests.test_convert_to_docbook.TestCitationResolvesToBibliographyHyperlink -v`
Expected: `PASS`.

- [ ] **Step 11: Rebuild the real paper end to end and confirm the hyperlink actually resolves**

```bash
python3 docs/scripts/build_bibliography.py
cd docs/papers/ai_and_ip/llm-database-theory && make validate && make html && cd -
grep -o '<a href="[^"]*cooper2025memorized[^"]*"' docs/papers/ai_and_ip/llm-database-theory/generated/01-llm-database-theory.html
grep -c 'id="cooper2025memorized"' docs/bibliography/references.html
```
Expected: the citation link's target path resolves to the real `docs/bibliography/references.html#cooper2025memorized`; that same file has exactly one element with `id="cooper2025memorized"` (from the `<li id="{@xml:id}">` template in Step 10 of the earlier XSLT work) — a real, working, standards-based cross-document reference, not a coincidental string match.

- [ ] **Step 12: Regenerate the real bibliography and validate end to end**

```bash
xmllint --noout --xinclude docs/bibliography/references.xml
jing -c docs/schema/docbook-corpus.rnc docs/bibliography/references.xml
grep -o '<biblioentry[^>]*>' docs/bibliography/references.xml | head -3
grep -o 'arcrole="[^"]*"' docs/bibliography/references.xml | sort -u
```
Expected: both validation commands succeed; both CiTO inverse-property URIs appear at least once.

- [ ] **Step 13: Commit**

```bash
git add .github/workflows/build-corpus.yml .github/workflows/build-papers.yml \
        docs/schema/docbook-corpus.rnc docs/scripts/corpus_ast.py docs/scripts/build_bibliography.py \
        docs/xsl/html5.xsl docs/papers/ai_and_ip/llm-database-theory/Makefile \
        docs/scripts/tests/test_build_bibliography.py docs/scripts/tests/test_convert_to_docbook.py
git add docs/bibliography/references.xml docs/bibliography/references.html
git add docs/papers/ai_and_ip/llm-database-theory/html
git commit -m "feat: model the consolidated bibliography with native DocBook bibliography/biblioentry vocabulary and CiTO xlink:arcrole on lxml, and make <citation> a real hyperlink to its biblioentry"
```

---

### Task 8: PROV-O provenance for AI-assisted research, as a native `<othercredit>` element

**Design correction, stated plainly:** the original design for this task hand-authored a JSON-LD blob in a `<bibliomisc>` CDATA — opaque to XPath, Schematron, or anything else that isn't a JSON parser, and disconnected from the document's own author/credit structure. DocBook already has a native element for exactly this: `<othercredit>`, used for a credited contributor distinct from the primary `<author>`. This task uses it instead, with the PROV-O type (`prov:SoftwareAgent`) attached the same way Task 9 attaches a SKOS concept to `dc:subject` — as an `xlink:arcrole`/`xlink:href` pair on the element itself, walkable directly.

One structural note, stated honestly rather than glossed over: DocBook conventionally nests `<othercredit>` inside the same `<authorgroup>` as `<author>`. After Task 1, `<authorgroup>` comes *only* from the shared, corpus-wide `shared-metadata.xml` — re-declaring a local `<authorgroup>` in the paper's own meta file just to add one `<othercredit>` would reintroduce the exact sibling-duplication bug Task 1 fixed. This task instead adds `<othercredit>` as a direct child of the paper's own `<info>`, alongside (not nested inside) the shared `<authorgroup>` it `xi:include`s. This is a deliberate, narrower structural choice made specifically to avoid that regression — not a claim that it's DocBook's single canonical idiom.

**Files:**
- Modify: `docs/papers/ai_and_ip/llm-database-theory/src/01-llm-database-theory.meta.xml`
- Modify: `docs/papers/ai_and_ip/llm-database-theory/src/02-legal-corpus-connections.meta.xml`
- Test: `docs/scripts/tests/test_convert_to_docbook.py`

**Interfaces:**
- Consumes: nothing new — `<othercredit>` is a plain DocBook element under `db:info`, already covered by `info-element`'s permissive treatment of unlisted children (see Global Constraints: `info-element`'s pattern only requires specific dcterms fields; it doesn't close off `db:info`'s other legal children).
- Produces: `xmlns:xlink` declared on both paper meta files' `<info>` element — Task 9 (which runs after this one) finds it already present and does not redeclare it.

- [ ] **Step 1: Add the native `<othercredit>` to both paper meta files**

In `docs/papers/ai_and_ip/llm-database-theory/src/01-llm-database-theory.meta.xml`, change the `<info>` opening tag from:
```xml
<info xmlns="http://docbook.org/ns/docbook"
      xmlns:dc="http://purl.org/dc/terms/"
      xmlns:xi="http://www.w3.org/2001/XInclude">
```
to:
```xml
<info xmlns="http://docbook.org/ns/docbook"
      xmlns:dc="http://purl.org/dc/terms/"
      xmlns:xi="http://www.w3.org/2001/XInclude"
      xmlns:xlink="http://www.w3.org/1999/xlink">
```
and add, immediately after the `<xi:include .../>` line:
```xml

  <othercredit xlink:href="https://www.anthropic.com/claude" xlink:arcrole="http://www.w3.org/ns/prov#SoftwareAgent">
    <orgname>Claude Sonnet 4.6 (Anthropic)</orgname>
    <contrib>research assistance</contrib>
  </othercredit>
```
Do the identical two edits to `02-legal-corpus-connections.meta.xml`.

- [ ] **Step 2: Write the failing test**

Add to `docs/scripts/tests/test_convert_to_docbook.py`:
```python
class TestPaperOthercreditProvenance(unittest.TestCase):
    def test_paper_articles_have_a_prov_typed_othercredit(self):
        from convert_to_docbook import REPO_ROOT, DB_NS, XLINK_NS
        import xml.etree.ElementTree as ET
        for name in ("01-llm-database-theory.meta.xml", "02-legal-corpus-connections.meta.xml"):
            path = (REPO_ROOT / "docs" / "papers" / "ai_and_ip" / "llm-database-theory"
                    / "src" / name)
            root = ET.parse(path).getroot()
            othercredit = root.find(f"{{{DB_NS}}}othercredit")
            self.assertIsNotNone(othercredit, f"{name} missing othercredit")
            self.assertEqual(
                othercredit.get(f"{{{XLINK_NS}}}arcrole"),
                "http://www.w3.org/ns/prov#SoftwareAgent",
            )
```

- [ ] **Step 3: Run the test to verify it fails**

Run: `python3 -m unittest docs.scripts.tests.test_convert_to_docbook.TestPaperOthercreditProvenance -v`
Expected: `AssertionError: unexpectedly None` — the `<othercredit>` doesn't exist yet.

- [ ] **Step 4: Make the edit, then run the test to verify it passes**

Run: `python3 -m unittest docs.scripts.tests.test_convert_to_docbook.TestPaperOthercreditProvenance -v`
Expected: `PASS`.

- [ ] **Step 5: Rebuild the paper and verify it doesn't break anything (`<othercredit>` has no XSLT template today, so it renders as bare, unstyled text via DocBook's default — acceptable for this task, which is about correct AST structure, not presentation; a dedicated template is a small, separately-scoped follow-on)**

```bash
cd docs/papers/ai_and_ip/llm-database-theory && make validate && make html && cd -
grep -A2 "Claude Sonnet 4.6" docs/papers/ai_and_ip/llm-database-theory/generated/01-llm-database-theory.html
```
Expected: `make validate`/`make html` succeed; the credit text appears somewhere in the rendered output.

- [ ] **Step 6: Commit**

```bash
git add docs/papers/ai_and_ip/llm-database-theory/src/01-llm-database-theory.meta.xml \
        docs/papers/ai_and_ip/llm-database-theory/src/02-legal-corpus-connections.meta.xml \
        docs/scripts/tests/test_convert_to_docbook.py
git add docs/papers/ai_and_ip/llm-database-theory/html
git commit -m "feat: represent AI-assisted-research provenance as a native othercredit element with a PROV-O xlink:arcrole, not a JSON-LD blob"
```

---

### Task 9: SKOS controlled vocabulary for `dc:subject`

**Files:**
- Create: `docs/common/subject-scheme.jsonld`
- Create: `docs/scripts/generate_subject_scheme.py`
- Modify: `docs/scripts/convert_to_docbook.py` (adds `SUBJECT_CONCEPTS`, `concept_uri()`, `derive_subject_concept_id()`; refactors `derive_subject()`; `write_metadata()` gains an `xlink:href` attribute on `dc:subject`)
- Modify: `docs/schema/docbook-corpus.rnc` (`dc:subject` gains an optional `xlink:href` attribute)
- Modify: `docs/xsl/html5.xsl` (Task 5's generated JSON-LD gains an `about`/`DefinedTerm` block)
- Modify: `docs/papers/ai_and_ip/llm-database-theory/src/01-llm-database-theory.meta.xml`, `02-legal-corpus-connections.meta.xml` (hand-authored `dc:subject` gets its own `xlink:href`)
- Test: `docs/scripts/tests/test_convert_to_docbook.py`

**Interfaces:**
- Consumes: `REPO_ROOT`, `GITHUB_REPO_URL` (Task 2), `write_metadata()` (Task 2), the `db:info/dc:subject`/`dc:identifier` fields the generated JSON-LD template (Task 5) already reads.
- Produces: `SUBJECT_CONCEPTS: dict[str, tuple[str, str | None]]` (concept id → (label, broader id)), `concept_uri(concept_id) -> str`, `derive_subject_concept_id(meta_path) -> str` — consumed by `generate_subject_scheme.py` and by `write_metadata()`'s new `xlink:href`.

- [ ] **Step 1: Write the failing tests**

Add to `docs/scripts/tests/test_convert_to_docbook.py`:
```python
class TestSubjectConcepts(unittest.TestCase):
    def test_matter_path_maps_to_matter_concept(self):
        from convert_to_docbook import derive_subject_concept_id, REPO_ROOT
        path = REPO_ROOT / "docs" / "court-record" / "matters" / "cooperative-investment-law" / "findings.meta.xml"
        self.assertEqual(derive_subject_concept_id(path), "matter-cooperative-investment-law")

    def test_theory_path_maps_to_branch_posture_concept(self):
        from convert_to_docbook import derive_subject_concept_id, REPO_ROOT
        path = (REPO_ROOT / "docs" / "court-record" / "theory" / "federal-constitutional"
                / "extensions" / "example.meta.xml")
        self.assertEqual(derive_subject_concept_id(path), "theory-federal-constitutional-extensions")

    def test_concept_uri_points_at_the_scheme_file(self):
        from convert_to_docbook import concept_uri
        self.assertEqual(
            concept_uri("matter-cooperative-investment-law"),
            "https://github.com/metavacua/legal-theory/blob/main/docs/common/subject-scheme.jsonld"
            "#matter-cooperative-investment-law",
        )

    def test_derive_subject_combines_broader_and_own_label(self):
        from convert_to_docbook import derive_subject, REPO_ROOT
        path = (REPO_ROOT / "docs" / "court-record" / "theory" / "federal-constitutional"
                / "extensions" / "example.meta.xml")
        self.assertEqual(derive_subject(path), "federal constitutional theory: extensions")

    def test_write_metadata_adds_xlink_href_to_dc_subject(self):
        from convert_to_docbook import write_metadata, REPO_ROOT, DC_NS, XLINK_NS
        out_dir = Path(tempfile.mkdtemp(dir=REPO_ROOT / "docs" / "wip"))
        self.addCleanup(shutil.rmtree, out_dir)
        meta_path = out_dir / "sample.meta.xml"
        write_metadata(meta_path, "Sample Title")

        root = ET.parse(meta_path).getroot()
        subject_el = root.find(f"{{{DC_NS}}}subject")
        href = subject_el.get(f"{{{XLINK_NS}}}href")
        self.assertTrue(href.startswith(
            "https://github.com/metavacua/legal-theory/blob/main/docs/common/subject-scheme.jsonld#"
        ))
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python3 -m unittest docs.scripts.tests.test_convert_to_docbook.TestSubjectConcepts -v`
Expected: `ImportError: cannot import name 'derive_subject_concept_id'`.

- [ ] **Step 3: Add the taxonomy table and the three new functions to `convert_to_docbook.py`**

Add near `GITHUB_REPO_URL` (from Task 2):
```python
SUBJECT_SCHEME_URI = f"{GITHUB_REPO_URL}/blob/main/docs/common/subject-scheme.jsonld"

# concept id -> (skos:prefLabel, broader concept id or None). The single
# source of truth for both derive_subject_concept_id() below and
# generate_subject_scheme.py's SKOS output -- grounded directly in the
# real docs/ directory taxonomy (verified via `find` against the actual
# corpus), not an invented topic list.
SUBJECT_CONCEPTS = {
    "matter-cooperative-investment-law": ("cooperative investment law", None),
    "matter-copyright-ip-authorship": ("copyright IP authorship", None),
    "matter-google-platform-misclassification": ("google platform misclassification", None),
    "matter-platform-tos-constitutional-limits": ("platform ToS constitutional limits", None),
    "matter-sex-work-consent-bodily-autonomy": ("sex work consent and bodily autonomy", None),

    "theory-california-constitutional": ("california constitutional theory", None),
    "theory-california-constitutional-existing-doctrine": ("existing doctrine", "theory-california-constitutional"),
    "theory-california-constitutional-extensions": ("extensions", "theory-california-constitutional"),
    "theory-california-constitutional-reversal-arguments": ("reversal arguments", "theory-california-constitutional"),
    "theory-california-constitutional-specializations": ("specializations", "theory-california-constitutional"),

    "theory-california-statutes": ("california statutory theory", None),
    "theory-california-statutes-existing-law": ("existing law", "theory-california-statutes"),
    "theory-california-statutes-extensions": ("extensions", "theory-california-statutes"),
    "theory-california-statutes-reversal-arguments": ("reversal arguments", "theory-california-statutes"),
    "theory-california-statutes-specializations": ("specializations", "theory-california-statutes"),

    "theory-federal-constitutional": ("federal constitutional theory", None),
    "theory-federal-constitutional-existing-doctrine": ("existing doctrine", "theory-federal-constitutional"),
    "theory-federal-constitutional-extensions": ("extensions", "theory-federal-constitutional"),
    "theory-federal-constitutional-reversal-arguments": ("reversal arguments", "theory-federal-constitutional"),
    "theory-federal-constitutional-specializations": ("specializations", "theory-federal-constitutional"),

    "theory-federal-statutes": ("federal statutory theory", None),
    "theory-federal-statutes-existing-law": ("existing law", "theory-federal-statutes"),
    "theory-federal-statutes-extensions": ("extensions", "theory-federal-statutes"),
    "theory-federal-statutes-reversal-arguments": ("reversal arguments", "theory-federal-statutes"),
    "theory-federal-statutes-specializations": ("specializations", "theory-federal-statutes"),

    "theory-municipal": ("municipal theory", None),
    "theory-municipal-existing-law": ("existing law", "theory-municipal"),
    "theory-municipal-specializations": ("specializations", "theory-municipal"),

    "cross-cutting": ("cross-cutting analysis", None),
    "wip": ("work in progress", None),
    "proposal-executive": ("executive proposal", None),
    "proposal-legislative": ("legislative proposal", None),
    "bibliography": ("bibliography", None),
    "papers": ("AI and intellectual property papers", None),
    "paper-llm-database-theory": ("LLM database theory", "papers"),
    "paper-legal-corpus-connections": ("legal corpus connections", "papers"),
}


def concept_uri(concept_id):
    return f"{SUBJECT_SCHEME_URI}#{concept_id}"


def derive_subject_concept_id(meta_path):
    """The SUBJECT_CONCEPTS key for meta_path's corpus location. Mirrors
    derive_subject()'s own path branching (same rel_parts source) but
    returns the machine concept id instead of a human label -- the two
    must never diverge, so derive_subject() is built from this
    function's result, not from separate logic."""
    rel_parts = Path(meta_path).resolve().relative_to(REPO_ROOT / "docs").parts
    if rel_parts[:2] == ("court-record", "matters"):
        return f"matter-{rel_parts[2]}"
    if rel_parts[:2] == ("court-record", "theory"):
        return f"theory-{rel_parts[2]}-{rel_parts[3]}"
    if rel_parts[0] == "proposals":
        return f"proposal-{rel_parts[1]}"
    if rel_parts[0] == "cross-cutting":
        return "cross-cutting"
    if rel_parts[0] == "wip":
        return "wip"
    if rel_parts[0] == "bibliography":
        return "bibliography"
    return rel_parts[0]
```

Replace `derive_subject()` (added in Task 2) with:
```python
def derive_subject(meta_path):
    """Human-readable dcterms:subject text, derived from the same
    SUBJECT_CONCEPTS taxonomy used for the SKOS scheme (Task 9) -- a
    concept with a broader concept gets "<broader label>: <own label>";
    a top-level concept is just its own label."""
    concept_id = derive_subject_concept_id(meta_path)
    label, broader_id = SUBJECT_CONCEPTS.get(concept_id, (concept_id.replace("-", " "), None))
    if broader_id:
        broader_label, _ = SUBJECT_CONCEPTS[broader_id]
        return f"{broader_label}: {label}"
    return label
```

In `write_metadata()`, add the `xlink:href` attribute to `dc:subject` and declare the `xlink` namespace on `<info>`:
```python
def write_metadata(meta_path, title, subject=None):
    meta_path = Path(meta_path)
    docs_dir = (REPO_ROOT / "docs").resolve()
    meta_dir = meta_path.resolve().parent
    depth = len(meta_dir.relative_to(docs_dir).parts)
    shared_href = "../" * depth + "common/shared-metadata.xml"
    escaped_title = xml_escape(title)
    concept_id = derive_subject_concept_id(meta_path)
    resolved_subject = subject if subject is not None else derive_subject(meta_path)
    date = derive_date(meta_path)
    identifier = derive_identifier(meta_path)
    concept_attr = f' xlink:href="{xml_escape(concept_uri(concept_id))}"' if concept_id in SUBJECT_CONCEPTS else ""
    content = f"""<?xml version="1.0" encoding="UTF-8"?>
<info xmlns="{DB_NS}" xmlns:dc="http://purl.org/dc/terms/" xmlns:xi="{XI_NS}" xmlns:xlink="{XLINK_NS}">
  <dc:title>{escaped_title}</dc:title>
  <dc:date>{date}</dc:date>
  <dc:identifier>{xml_escape(identifier)}</dc:identifier>
  <dc:subject{concept_attr}>{xml_escape(resolved_subject)}</dc:subject>
  <xi:include href="{shared_href}" />
</info>
"""
    meta_path.write_text(content, encoding="utf-8")
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python3 -m unittest docs.scripts.tests.test_convert_to_docbook -v 2>&1 | tail -30`
Expected: all `TestSubjectConcepts` tests `PASS`; all pre-existing tests still `PASS`.

- [ ] **Step 5: Write `generate_subject_scheme.py`**

```python
"""Generate docs/common/subject-scheme.jsonld -- a SKOS
(w3.org/2004/02/skos/core#) ConceptScheme -- from the SUBJECT_CONCEPTS
taxonomy table in convert_to_docbook.py, the single source of truth
derive_subject_concept_id() is also built from, so the published scheme
and the concept ids documents actually reference can never drift apart."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from convert_to_docbook import REPO_ROOT, SUBJECT_CONCEPTS, SUBJECT_SCHEME_URI, concept_uri  # noqa: E402

SCHEME_PATH = REPO_ROOT / "docs" / "common" / "subject-scheme.jsonld"


def build_scheme():
    top_concepts = [concept_uri(cid) for cid, (_, broader) in SUBJECT_CONCEPTS.items() if broader is None]
    graph = [{
        "@id": SUBJECT_SCHEME_URI,
        "@type": "skos:ConceptScheme",
        "dcterms:title": "legal-theory corpus subject scheme",
        "skos:hasTopConcept": [{"@id": u} for u in top_concepts],
    }]
    for concept_id, (label, broader_id) in SUBJECT_CONCEPTS.items():
        node = {
            "@id": concept_uri(concept_id),
            "@type": "skos:Concept",
            "skos:prefLabel": label,
            "skos:inScheme": {"@id": SUBJECT_SCHEME_URI},
        }
        if broader_id:
            node["skos:broader"] = {"@id": concept_uri(broader_id)}
        else:
            node["skos:topConceptOf"] = {"@id": SUBJECT_SCHEME_URI}
        graph.append(node)
    return {
        "@context": {
            "skos": "http://www.w3.org/2004/02/skos/core#",
            "dcterms": "http://purl.org/dc/terms/",
        },
        "@graph": graph,
    }


def main(argv=None):
    SCHEME_PATH.write_text(json.dumps(build_scheme(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"OK: wrote {len(SUBJECT_CONCEPTS)} concepts to {SCHEME_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 6: Update `docs/schema/docbook-corpus.rnc` to allow the new attribute**

In the `info-element` pattern (Task 3), change:
```
    element dc:subject    { text } &
```
to:
```
    element dc:subject    { attribute xlink:href { xsd:anyURI }?, text } &
```

- [ ] **Step 7: Generate the scheme, regenerate the corpus, and validate**

```bash
python3 docs/scripts/generate_subject_scheme.py
python3 docs/scripts/backfill_dcterms_metadata.py
python3 -c "import json; d = json.load(open('docs/common/subject-scheme.jsonld')); print(len(d['@graph']))"
find docs -name '*.meta.xml' -not -path 'docs/papers/*' -not -path 'docs/scripts/*' | while read -r meta; do
  jing -c docs/schema/docbook-corpus.rnc "$meta" || echo "FAILED: $meta"
done
```
Expected: the scheme file has 35 graph nodes (1 scheme + 34 concepts); no `FAILED:` lines (the RNC change is additive/optional, so previously-valid files stay valid).

- [ ] **Step 8: Add `xlink:href` to the two paper meta files and extend the Schema.org JSON-LD template**

In `docs/papers/ai_and_ip/llm-database-theory/src/01-llm-database-theory.meta.xml`, change:
```xml
  <dc:subject>large language models; graph databases; intellectual property; copyright; LARQL; mechanistic interpretability; derivative works; collective works; database law; GDPR; transformer architecture; knowledge graphs</dc:subject>
```
to:
```xml
  <dc:subject xlink:href="https://github.com/metavacua/legal-theory/blob/main/docs/common/subject-scheme.jsonld#paper-llm-database-theory">large language models; graph databases; intellectual property; copyright; LARQL; mechanistic interpretability; derivative works; collective works; database law; GDPR; transformer architecture; knowledge graphs</dc:subject>
```
`xmlns:xlink` is already declared on `<info>` by Task 8 (which runs first and needed it for `<othercredit xlink:arcrole="...">`) — do not add it again. Do the equivalent `dc:subject` edit in `02-legal-corpus-connections.meta.xml`, using `#paper-legal-corpus-connections`.

In `docs/xsl/html5.xsl`, extend the Schema.org JSON-LD block from Task 5 — change:
```xml
          <xsl:text>  "identifier": "</xsl:text><xsl:value-of select="db:info/dc:identifier"/><xsl:text>"&#10;</xsl:text>
          <xsl:text>}</xsl:text>
```
to:
```xml
          <xsl:text>  "identifier": "</xsl:text><xsl:value-of select="db:info/dc:identifier"/><xsl:text>"</xsl:text>
          <xsl:if test="db:info/dc:subject/@xlink:href">
            <xsl:text>,&#10;  "about": {"@type": "DefinedTerm", "name": "</xsl:text>
            <xsl:value-of select="db:info/dc:subject"/>
            <xsl:text>", "@id": "</xsl:text>
            <xsl:value-of select="db:info/dc:subject/@xlink:href"/>
            <xsl:text>", "inDefinedTermSet": "</xsl:text>
            <xsl:value-of select="substring-before(db:info/dc:subject/@xlink:href, '#')"/>
            <xsl:text>"}</xsl:text>
          </xsl:if>
          <xsl:text>&#10;}</xsl:text>
```

- [ ] **Step 9: Rebuild and verify**

```bash
cd docs/papers/ai_and_ip/llm-database-theory && make validate && make html && cd -
grep -A5 '"about"' docs/papers/ai_and_ip/llm-database-theory/generated/01-llm-database-theory.html
while IFS= read -r xml; do
  xsltproc --xinclude docs/xsl/html5.xsl "$xml" > "${xml%.xml}.html"
done < <(find docs -name '*.xml' -not -path '*/scratch/*' -not -path 'docs/papers/*' -not -path 'docs/scripts/*' | sort)
grep -A5 '"about"' docs/wip/*.html | head -8
```
Expected: both the paper and ordinary corpus pages now emit an `"about": {"@type": "DefinedTerm", ...}` block referencing a real, resolvable concept URI.

- [ ] **Step 10: Commit**

```bash
git add docs/common/subject-scheme.jsonld docs/scripts/generate_subject_scheme.py \
        docs/scripts/convert_to_docbook.py docs/scripts/tests/test_convert_to_docbook.py \
        docs/schema/docbook-corpus.rnc docs/xsl/html5.xsl \
        docs/papers/ai_and_ip/llm-database-theory/src/01-llm-database-theory.meta.xml \
        docs/papers/ai_and_ip/llm-database-theory/src/02-legal-corpus-connections.meta.xml
git add docs/cross-cutting docs/wip docs/court-record docs/proposals docs/bibliography docs/papers/ai_and_ip/llm-database-theory/html
git commit -m "feat: adopt a SKOS controlled vocabulary for dc:subject, referenced via xlink:href and surfaced as Schema.org DefinedTerm"
```

---

### Task 10: Fix the unreachable `finding-section` grammar rule — corpus-wide, not paper-isolated

**Files:**
- Modify: `docs/schema/docbook-corpus.rnc` (remove dead `finding-condition`/`finding-section`; rewrite the header)
- Modify: `docs/scripts/convert_to_docbook.py` (add `validate_finding_sections()`, wire into `validate()`)
- Create: `docs/scripts/check_finding_sections.py`
- Modify: `docs/papers/ai_and_ip/llm-database-theory/Makefile`
- Modify: `.github/workflows/build-corpus.yml`
- Test: `docs/scripts/tests/test_convert_to_docbook.py`

**Interfaces:**
- Consumes: `DB_NS`, `XML_NS`, `REPO_ROOT` (existing), `validate()` (existing, extended).
- Produces: `validate_finding_sections(xml_path) -> list[str]`, called from `validate()` for every document build corpus-wide, and from the new `check_finding_sections.py` CLI for the shell-based Makefile/CI loops.

- [ ] **Step 1: Reconfirm the defect and that no RNC-only fix is possible (already verified in Plan Notes; reproduce here before changing anything)**

```bash
cat > /tmp/broken-finding.xml <<'EOF'
<?xml version="1.0"?>
<article xmlns="http://docbook.org/ns/docbook" version="5.2" xml:id="t" xml:lang="en">
  <title>T</title>
  <section role="finding" condition="not-a-real-value"><title>X</title><para>Y</para></section>
</article>
EOF
jing -c docs/schema/docbook-corpus.rnc /tmp/broken-finding.xml; echo "exit: $?"
```
Expected: `exit: 0` — jing accepts a finding-section with an invalid `condition` and no `xml:id`, confirming `finding-section` is dead grammar today.

- [ ] **Step 2: Remove the dead RNC rules and rewrite the header**

In `docs/schema/docbook-corpus.rnc`, delete:
```
# Permitted condition values on <section role="finding">
finding-condition =
  "confirmed"
  | "confirmed-with-caveats"
  | "split"
```
and:
```
# A finding section must have xml:id, role="finding", and a valid condition.
finding-section =
  element db:section {
    attribute xml:id  { xsd:NCName },
    attribute role    { "finding" },
    attribute condition { finding-condition },
    element db:title { text },
    block-content+
  }
```
Replace the file's header comment (lines 1-14) with:
```
# docbook-corpus.rnc — RELAX NG Compact Schema
# Additive constraints on top of full DocBook 5.2 for the legal-theory
# corpus (docs/) and its papers/ subtree.
#
# Validates:
#   1. Article-level shape (db:article, version, xml:id, xml:lang) and
#      permitted block-level content (block-content).
#   2. Per-document metadata shape (info-element) -- validated by
#      running jing directly against a *.meta.xml file, not against an
#      article (an article's own info slot holds an unresolved
#      <xi:include> when jing runs, since jing is invoked without
#      --xinclude throughout this pipeline).
#   3. docs/common/shared-metadata.xml's own shape (shared-metadata-file).
#
# NOT validated here: the confirmed/confirmed-with-caveats/split
# condition constraint on <section role="finding"> elements. RELAX NG's
# choice (|) can't express "these constraints apply only when
# role=finding, else anything goes" against block-content's own
# always-permissive `element db:section { any }` alternative -- any RNC
# pattern for this is dead grammar, unreachable in practice (this file
# used to define exactly such a dead `finding-section` pattern; it has
# been removed, not left in place unused). That constraint is enforced
# in Python instead, over the resolved document tree, by
# validate_finding_sections() in docs/scripts/convert_to_docbook.py,
# wired into the same validate() every document already goes through --
# checked for any document that uses role="finding", not isolated to
# the flagship paper.
#
# Usage:
#   jing -c docs/schema/docbook-corpus.rnc <article>.xml
#   jing -c docs/schema/docbook-corpus.rnc <name>.meta.xml
#   jing -c docs/schema/docbook-corpus.rnc docs/common/shared-metadata.xml
#
# Note: This schema is additive — it does NOT replace the full DocBook
# 5.2 schema. Run xmllint --relaxng separately to validate against the
# full DocBook grammar.
```

- [ ] **Step 3: Write the failing tests for the Python-side check**

Add to `docs/scripts/tests/test_convert_to_docbook.py`:
```python
class TestValidateFindingSections(unittest.TestCase):
    def _write(self, tmp, section_xml):
        path = Path(tmp) / "sample.xml"
        path.write_text(
            '<?xml version="1.0"?>\n'
            '<article xmlns="http://docbook.org/ns/docbook" version="5.2" xml:id="s" xml:lang="en">\n'
            '  <title>S</title>\n'
            f'  {section_xml}\n'
            '</article>\n',
            encoding="utf-8",
        )
        return path

    def test_valid_finding_section_has_no_violations(self):
        from convert_to_docbook import validate_finding_sections
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write(tmp, '<section xml:id="f1" role="finding" condition="confirmed"><title>F</title><para>P</para></section>')
            self.assertEqual(validate_finding_sections(path), [])

    def test_missing_xml_id_is_flagged(self):
        from convert_to_docbook import validate_finding_sections
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write(tmp, '<section role="finding" condition="confirmed"><title>F</title><para>P</para></section>')
            violations = validate_finding_sections(path)
            self.assertEqual(len(violations), 1)
            self.assertIn("missing xml:id", violations[0])

    def test_invalid_condition_is_flagged(self):
        from convert_to_docbook import validate_finding_sections
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write(tmp, '<section xml:id="f1" role="finding" condition="maybe"><title>F</title><para>P</para></section>')
            violations = validate_finding_sections(path)
            self.assertEqual(len(violations), 1)
            self.assertIn("invalid condition", violations[0])

    def test_non_finding_sections_are_ignored(self):
        from convert_to_docbook import validate_finding_sections
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write(tmp, '<section xml:id="ordinary"><title>Ordinary</title><para>P</para></section>')
            self.assertEqual(validate_finding_sections(path), [])

    def test_real_paper_article_has_no_violations(self):
        from convert_to_docbook import validate_finding_sections, REPO_ROOT
        path = (REPO_ROOT / "docs" / "papers" / "ai_and_ip" / "llm-database-theory"
                / "src" / "02-legal-corpus-connections.xml")
        self.assertEqual(validate_finding_sections(path), [])
```

- [ ] **Step 4: Run the tests to verify they fail**

Run: `python3 -m unittest docs.scripts.tests.test_convert_to_docbook.TestValidateFindingSections -v`
Expected: `ImportError: cannot import name 'validate_finding_sections'`.

- [ ] **Step 5: Implement `validate_finding_sections()` and wire it into `validate()`**

Add to `docs/scripts/convert_to_docbook.py`:
```python
FINDING_CONDITIONS = {"confirmed", "confirmed-with-caveats", "split"}


def validate_finding_sections(xml_path):
    """[violation message, ...] for every db:section[@role='finding'] in
    xml_path (after XInclude resolution) missing xml:id or carrying a
    condition outside FINDING_CONDITIONS. Lives in Python, not RELAX NG:
    docbook-corpus.rnc's old finding-section pattern was dead grammar
    (unreachable from `start`), and RELAX NG's choice (|) can't express
    "these constraints apply only when role=finding" against
    block-content's own always-permissive fallback for the same element
    name. xmllint's Schematron support was tried and found
    non-functional in the reference environment (a minimal, otherwise
    valid .sch file fails to compile) -- verified directly, not assumed.
    A resolved-tree walk works for any document, not just the paper's,
    and needs no new tool."""
    resolved = subprocess.run(
        ["xmllint", "--xinclude", str(xml_path)], capture_output=True, text=True, check=True,
    ).stdout
    root = ET.fromstring(resolved)
    violations = []
    for el in root.iter(f"{{{DB_NS}}}section"):
        if el.get("role") != "finding":
            continue
        xml_id = el.get(f"{{{XML_NS}}}id")
        condition = el.get("condition")
        label = xml_id or "(no xml:id)"
        if not xml_id:
            violations.append(f"{xml_path}: finding section {label} missing xml:id")
        if condition not in FINDING_CONDITIONS:
            violations.append(f"{xml_path}: finding section {label} has invalid condition {condition!r}")
    return violations
```

In `validate()`, add the new check after the RNC check:
```python
def validate(xml_path):
    errors = []
    wf = subprocess.run(
        ["xmllint", "--noout", "--xinclude", str(xml_path)],
        capture_output=True, text=True,
    )
    if wf.returncode != 0:
        errors.append(wf.stderr.strip())
        return errors  # schema validation is meaningless on malformed XML

    rng = subprocess.run(
        ["jing", "-c", str(SCHEMA_PATH), str(xml_path)],
        capture_output=True, text=True,
    )
    if rng.returncode != 0:
        errors.append(rng.stdout.strip() or rng.stderr.strip())

    errors.extend(validate_finding_sections(xml_path))
    return errors
```

- [ ] **Step 6: Run the tests to verify they pass**

Run: `python3 -m unittest docs.scripts.tests.test_convert_to_docbook.TestValidateFindingSections -v`
Expected: all 5 `PASS`, including `test_real_paper_article_has_no_violations` — confirms the paper's real content already conforms (all 4 finding-sections were already correctly formed, per the earlier grep; this task fixes the *check*, not the content).

- [ ] **Step 7: Add the CLI wrapper for shell-based CI/Makefile use**

Create `docs/scripts/check_finding_sections.py`:
```python
"""CLI check for the role="finding" condition/xml:id constraint (see
docs/superpowers/plans/2026-07-25-external-metadata-ontology-standardization.md,
Task 10) -- wired into the same shell-based validation loops (Makefile,
build-corpus.yml) that already run xmllint/jing, so this check is
reachable for every document, not only ones a Python caller happens to
invoke validate() on."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from convert_to_docbook import validate_finding_sections  # noqa: E402


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    violations = []
    for path in argv:
        violations.extend(validate_finding_sections(path))
    for v in violations:
        print(v, file=sys.stderr)
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 8: Wire it into the paper's Makefile and into `build-corpus.yml`**

In `docs/papers/ai_and_ip/llm-database-theory/Makefile`, in the `validate` target, after the RNC validation block added in Task 4, add:
```makefile
	@echo "==> Finding-section (role=finding) constraint check"
	@python3 ../../../scripts/check_finding_sections.py $(ARTICLES)
```

In `.github/workflows/build-corpus.yml`, in the per-article loop (inside the `while IFS= read -r xml; do ... done` block, right after the `jing -c docs/schema/docbook-corpus.rnc "$xml"` line), add:
```yaml
            python3 docs/scripts/check_finding_sections.py "$xml"
```

- [ ] **Step 9: Verify end to end**

```bash
jing -c docs/schema/docbook-corpus.rnc /tmp/broken-finding.xml; echo "jing exit: $? (expected 0 -- RNC no longer claims to check this)"
python3 docs/scripts/check_finding_sections.py /tmp/broken-finding.xml; echo "check exit: $? (expected 1)"
cd docs/papers/ai_and_ip/llm-database-theory && make validate && cd -
```
Expected: `jing` still exits `0` on the broken fixture (the RNC honestly no longer claims to catch this — see the rewritten header); `check_finding_sections.py` exits `1` and prints both violations; `make validate` passes for the real paper content.

- [ ] **Step 10: Commit**

```bash
git add docs/schema/docbook-corpus.rnc docs/scripts/convert_to_docbook.py \
        docs/scripts/check_finding_sections.py docs/scripts/tests/test_convert_to_docbook.py \
        docs/papers/ai_and_ip/llm-database-theory/Makefile .github/workflows/build-corpus.yml
git commit -m "fix: remove the unreachable finding-section RNC rule and enforce its constraint in Python, corpus-wide, through the one shared validation pipeline"
```

---

### Task 11: Finish migrating the remaining scripts onto the single lxml AST

**Design correction, stated plainly:** Task 7 installed `lxml` and migrated `build_bibliography.py`'s XML *emission* to it, but left `convert_to_docbook.py`, `atomize_existing_document.py`, `audit_footnote_links.py`, and `build_bibliography.py`'s *other* functions (`parse_xincludes`, `build_backlink_map`, `extract_works_cited`, `_bib_citation_backlinks`) on stdlib `xml.etree.ElementTree`. That's not "the whole repository unified by a single AST" — it's two libraries coexisting, which is its own inconsistency. This task finishes the migration: every script uses `lxml.etree`, full stop. `lxml` is a real, installed, declared dependency now (Task 7) — there is no reason left to keep two parsers.

**Files:**
- Modify: `docs/scripts/convert_to_docbook.py`
- Modify: `docs/scripts/atomize_existing_document.py`
- Modify: `docs/scripts/audit_footnote_links.py`
- Modify: `docs/scripts/build_bibliography.py` (again — unifies its Task-7-introduced `lxml` import with its remaining stdlib-`ET` functions)
- Test: existing test suites for all four (`test_convert_to_docbook.py`, `test_atomize_existing_document.py`, `test_audit_footnote_links.py`, `test_build_bibliography.py`) — no new test classes; this task's job is to keep every one of them green under the new library.

**Interfaces:**
- Consumes: `corpus_ast.new_article_root()` (Task 7) — reused here for `wrap_fragment()`'s root-element construction instead of duplicating the nsmap pattern a second time.
- Produces: no public signature changes — every function's inputs/outputs stay the same; only the underlying XML library changes, which is exactly why the existing test suites are the verification, not new tests.

- [ ] **Step 1: Confirm the two verified lxml facts this migration depends on, once more, directly in this repo's own code**

```bash
python3 -c "
from lxml import etree
try:
    etree.register_namespace('', 'http://docbook.org/ns/docbook')
except ValueError as e:
    print('confirmed: register_namespace(\"\", ...) still rejected under lxml:', e)
"
python3 -c "
from lxml import etree
try:
    etree.fromstring(b'<broken>')
except etree.XMLSyntaxError as e:
    print('confirmed: lxml raises XMLSyntaxError, not ET.ParseError:', type(e).__name__)
"
```

- [ ] **Step 2: Migrate `convert_to_docbook.py`**

Change the imports (lines 7, 9):
```python
import xml.etree.ElementTree as ET
```
to:
```python
from lxml import etree as ET
```
Delete the three now-broken registration calls:
```python
ET.register_namespace("", DB_NS)
ET.register_namespace("xi", XI_NS)
ET.register_namespace("xlink", XLINK_NS)
```
Add, near the top-level imports:
```python
from corpus_ast import new_article_root
```
In `wrap_fragment()`, change:
```python
    article = ET.Element(f"{{{DB_NS}}}article")
    article.set("version", "5.2")
    article.set(f"{{{XML_NS}}}id", xml_id)
    article.set(f"{{{XML_NS}}}lang", "en")
```
to:
```python
    article = new_article_root(version="5.2")
    article.set(f"{{{XML_NS}}}id", xml_id)
    article.set(f"{{{XML_NS}}}lang", "en")
```
Change the `except ET.ParseError as e:` in `convert()` (the one whose comment explains the `petition-corporate-ai-registry-ca-sos.md` root cause) to:
```python
    except ET.XMLSyntaxError as e:
```

- [ ] **Step 3: Migrate `atomize_existing_document.py`**

Change:
```python
import xml.etree.ElementTree as ET
```
to:
```python
from lxml import etree as ET
```
(No `register_namespace` or `ET.ParseError` usage in this file to fix — confirmed by direct grep before writing this task.)

- [ ] **Step 4: Migrate `audit_footnote_links.py`**

Change:
```python
import xml.etree.ElementTree as ET
```
to:
```python
from lxml import etree as ET
```
Change `except ET.ParseError:` to `except ET.XMLSyntaxError:`.

- [ ] **Step 5: Unify `build_bibliography.py` onto one `lxml` import**

Task 7 added `from lxml import etree` alongside the file's pre-existing `import xml.etree.ElementTree as ET`. Change the original import line:
```python
import xml.etree.ElementTree as ET
```
to:
```python
from lxml import etree as ET
```
and delete the now-redundant `from lxml import etree` line Task 7 added — every call site in this file (both the pre-existing functions and Task 7's `emit_docbook_tree`/etc.) now refers to the single name `ET`/`etree` consistently; adjust `emit_docbook_tree()`'s own body from `etree.Element(...)`/`etree.SubElement(...)` to `ET.Element(...)`/`ET.SubElement(...)` to match the rest of the file's existing convention (or, equivalently, keep calling it `etree` throughout and drop `ET` — either is fine as long as the file uses exactly one name for exactly one library, which is the actual point). Fix `parse_bibtex()`'s error handling if it catches `ET.ParseError` anywhere (confirmed one such catch exists in this file) to `ET.XMLSyntaxError`.

- [ ] **Step 6: Run every existing test suite for all four files**

```bash
python3 -m unittest docs.scripts.tests.test_convert_to_docbook -v 2>&1 | tail -60
python3 -m unittest docs.scripts.tests.test_atomize_existing_document -v 2>&1 | tail -30
python3 -m unittest docs.scripts.tests.test_audit_footnote_links -v 2>&1 | tail -30
python3 -m unittest docs.scripts.tests.test_build_bibliography -v 2>&1 | tail -60
```
Expected: 100% pass across all four files. This migration changes the underlying library, not any function's contract, so every pre-existing test (from this plan's earlier tasks and from before this plan started) is the actual regression check — fix any failure here before proceeding; do not weaken or delete a test to make it pass.

- [ ] **Step 7: Rebuild the real corpus end to end**

```bash
python3 docs/scripts/build_bibliography.py
cd docs/papers/ai_and_ip/llm-database-theory && make validate && make html && cd -
while IFS= read -r xml; do
  xsltproc --xinclude docs/xsl/html5.xsl "$xml" > "${xml%.xml}.html"
done < <(find docs -name '*.xml' -not -path '*/scratch/*' -not -path 'docs/papers/*' -not -path 'docs/scripts/*' | sort)
git status --short docs | head -20
```
Expected: everything builds cleanly; `git status` shows no unexpected content drift (only whichever files this migration's own commits already touched).

- [ ] **Step 8: Commit**

```bash
git add docs/scripts/convert_to_docbook.py docs/scripts/atomize_existing_document.py \
        docs/scripts/audit_footnote_links.py docs/scripts/build_bibliography.py
git commit -m "refactor: finish migrating every docs/scripts/*.py file onto lxml, retiring the last stdlib xml.etree.ElementTree usage"
```

---

## Self-Review Notes

- **Spec coverage:** Dublin Core Terms completion → Tasks 1-3. DCMI Type Vocabulary correctness → Task 1/3. Schema.org uniformity → Task 5. SPDX license identifiers → Task 1. CSL-JSON → Task 6. Native DocBook bibliography vocabulary + SPAR/CiTO citation-typing + a real `<citation>`→`<biblioentry>` hyperlink → Task 7. PROV-O (as a native `<othercredit>`, not a JSON-LD blob) → Task 8. SKOS controlled vocabulary → Task 9. Finding-section grammar defect → Task 10. Single shared AST layer (`lxml`, installed via `apt`, used by every script) → Tasks 7 + 11. Mechanical search/sort/classification (raised mid-plan) → Tasks 2 (uniform date/identifier/subject fields) + 9 (real SKOS classification, not a folder-path echo). Format unification / no privileged documents (raised mid-plan) → Task 1 (retires the paper's bespoke shared-00-metadata.xml pattern) + Task 10 (removes the finding-section construct's isolation rather than accommodating it) + Task 7 (removes the disconnected `citations.jsonld` side-file in favor of native, walkable markup). Semantic soundness/completeness of the AST (raised mid-plan, twice) → Tasks 7-9 corrected to put every ontology reference *on* an existing, walkable element (`xlink:arcrole`/`xlink:href` on real `<link>`/`<othercredit>`/`<dc:subject>` elements) rather than in a side JSON-LD file or CDATA blob nothing but a JSON parser could read; the two places this plan originally got that wrong (Task 7's `citations.jsonld`, Task 8's `bibliomisc` JSON-LD) were rewritten, not left as the first draft. CI enforcement of all of the above → Tasks 3-4, Task 7 Steps 2/12, and Task 10 Steps 7-8. ORCID and Akoma Ntoso remain explicitly deferred/out-of-scope per Global Constraints. `lxml` itself was *not* avoided on installation-friction grounds — it's installed via `apt` (the same mechanism already used for `jing`/`xmllint`/`xsltproc`), verified working (native `XInclude` resolution succeeds where stdlib `ElementInclude` failed; correct attribute escaping; `nsmap`-based namespace construction verified against the real corpus), and used as the one AST library everywhere by Task 11.
- **Placeholder scan:** no `TBD`/`[fill in]` markers; every code block is complete, runnable code; every XML fixture is the real, full file content, not an excerpt with `...`. Every claim about tool behavior that could be wrong (Schematron support, `ElementInclude`'s relative-path handling, the finding-section grammar being unreachable, `lxml`'s `register_namespace`/`nsmap` behavior, `xlink:arcrole`/native-bibliography schema validity, the `bibliography-href` XSLT parameter) was verified by direct command execution in this environment, not assumed from documentation — including two cases (Schematron; the original `_entry_id()` design silently failing to make `<citation>` resolve) where the first design turned out not to work and was rewritten as a result, not asserted anyway.
- **Type/signature consistency checked:** `write_metadata(meta_path, title, subject=None)` (Task 2, extended again in Task 9 with the `xlink:href` attribute) is the only signature change to an existing function, and it stays additive/backward-compatible through both changes — verified against all 8 real call sites listed in Task 2's Interfaces. `derive_subject()` is rewritten in Task 9 to be built from `derive_subject_concept_id()`/`SUBJECT_CONCEPTS` rather than its own Task-2 branching, but its return type and call sites are unchanged. `derive_date`/`derive_identifier` (Task 2) are untouched by later tasks. `BibliographyEntry` gains a `bib_key` field (Task 7, default `None`) — additive, and every pre-existing construction call site in the test suite that doesn't pass it still works. `csl_item`/`csl_item_for_bib`/`emit_csl_json` (Task 6) are independent, consumed only from `main()` and their own tests. `validate()` (existing) gains one more check in Task 10 (`validate_finding_sections()`), additive to its existing `errors` list contract. `emit_docbook()` (Task 7) keeps its exact existing signature and return type (an XML string) — only its internal implementation and the underlying library change, so `main()`'s existing call site needs no edit. Task 11 changes no function signature anywhere — it only swaps the XML library every function already used.

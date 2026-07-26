# Citation & Bibliography Standardization: Design

## 1. Motivation

The corpus has no standard bibliographic markup anywhere. Every citation is expressed through
generic elements repurposed to look like a citation, not DocBook's own `<bibliography>`/
`<biblioentry>`/`<bibliomixed>` vocabulary. Confirmed directly, corpus-wide, via
`docs/scripts/measure_citation_conformance.py` (built 2026-07-26, TDD, see that file's own
docstring and tests for the verified methodology):

```
Non-standard (works-cited) entries: 5482 across 88 documents
Standard (biblioentry/bibliomixed) entries: 0
Citation markers: 0 resolved, 22 unresolved
Deep-Research-style numbered citation pattern: 96 documents, 6109 plausible markers, 88 implausible/unrelated
```

Two structurally distinct informal citation conventions exist, both requiring conversion:

**A. Flat works-cited listitems (5,482 entries / 88 documents).** A `<section
xml:id="works-cited"><orderedlist><listitem>` full of Bluebook/Chicago-formatted display strings,
each usually ending in a `<link xlink:href>` to a secondary aggregator site. No structural
connection to anything that cites it. This is the pattern the 2026-07-23 bibliography design and
plan already surveyed and built tooling for -- tooling that adapted to this convention instead of
converting it (see that design's 2026-07-26 correction notes).

**B. Deep-Research-style numbered citations (96 documents, 6,109 markers).** A different failure
mode: glued inline markers (`"...trillions of parameters.1"` -- a letter immediately followed by a
period immediately followed by 1-2 digits, no space) scattered through prose, corresponding
*positionally* to a numbered works-cited list. Confirmed by direct comparison against the real
Google Drive originals for two documents (`llms-as-categorical-systems`,
`prompts-as-expression`): the Markdown-to-DocBook conversion preserved both the markers and the
list content/order perfectly, but never added the structural link between them. Because the
atomization script (`atomize_existing_document.py`) splits a single original document into
per-section fragments, the works-cited list typically ends up living entirely in one fragment
(wherever it fell in the original document's linear order) while the markers referencing it
scatter across every fragment of that same shell article.

Pattern B further splits into two sub-cases, confirmed by directly pulling and comparing the real
Drive originals, not assumed:

- **Category A documents:** the full numbered reference list survives intact in both the Drive
  original and the DocBook conversion (verified exact match, `llms-as-categorical-systems`: 82
  entries, same content, same order, both sides). The marker-to-entry correspondence is fully
  reconstructable with high confidence.
- **Category B documents:** the citation markers are present in the DocBook (and in the Drive
  original too -- confirmed, this is not a conversion loss) but no reference list exists anywhere,
  including the source. These read like direct AI chat responses ("Of course. Here is a new
  research report...") rather than formal Deep Research reports with a citations appendix; the
  markers most likely referenced web search results shown as interactive citations in a chat UI
  that never survive a copy-paste into a Doc. Confirmed for two real documents
  (`prompts-as-expression`, `patron-client-non-disclaimable-duties`); the original chat
  sessions/contexts are not reliably accessible for recovery, and recovery must not be assumed or
  depended on for any part of this project's scope.

Which of the 96 documents fall into Category A vs. B is not yet known corpus-wide -- only 2
positive (A) and 2 confirmed (B) examples have been checked by hand. Classifying the rest is
explicit scope in this design (§5).

## 2. Why this keeps happening: root cause, not a one-off bug

Every prior fix in this session's work touched the metadata/schema layer (`<info>`, DCTERMS,
native elements) without touching citation *content*. The 2026-07-23 bibliography design went
further and explicitly chose to reuse the informal `works-cited`/`listitem` shape for its own
generated output ("zero XSL or schema changes needed... the exact markup pattern every existing
works-cited section already uses" -- treated as a virtue, corrected 2026-07-26). The root cause,
stated plainly: these documents were authored outside DocBook entirely (Google Docs, AI-generated
research reports with their own numbered-citation conventions) and the Markdown-to-pandoc-to-
DocBook conversion pipeline carried the *original* citation convention over as generic markup,
rather than translating it into DocBook's own citation/bibliography idioms. Standardizing means
converting every citation to real, source-native DocBook structure and retiring both informal
conventions entirely -- not building a script that adapts to them indefinitely.

## 3. Architecture: one file per citation entry, reused via XInclude

**Verified directly (2026-07-26):** a `<bibliography>` populated purely via `xi:include` pointing
at an external file containing `<biblioentry xml:id="...">` is valid DocBook 5.2 (`jing` confirmed,
exit 0) and resolves correctly (`measure_citation_conformance.py` correctly detects the resulting
citation as standard and resolved once XInclude is processed).

- `docs/bibliography/entries/<key>.xml` -- one file per real-world citable source, root
  `<biblioentry>` or `<bibliomixed>`, matching the existing `docs/common/authorgroup.xml`/
  `legalnotice.xml` convention (a bare fragment, no `<info>` wrapper -- these aren't top-level
  articles). `<key>` is a stable, unique identifier per source, reusing `bibliography.bib`'s
  existing keys where a bib entry already provides one, generated deterministically otherwise
  (exact algorithm is implementation-plan detail, not a design decision -- the requirement is
  stability across regenerations, not any particular scheme).
- Each citing document's own `<bibliography>` block is a generated set of `<xi:include>`s pointing
  at exactly the entry files it cites -- not hand-authored, regenerated by the same tooling that
  scans that document's `<citation>KEY</citation>` markers.
- The repo-wide `docs/bibliography/references.xml` bibliography is the same mechanism at corpus
  scope -- `<xi:include>` over every entry actually cited somewhere. Neither the per-document nor
  the repo-wide bibliography is a second, independently-scanned copy; both are generated from the
  same source of truth (the entry files plus the `<citation>` markers), so they cannot drift out
  of sync with each other the way the current `references.xml` can (and did -- see the earlier
  finding that `build_bibliography.py`'s content generator reintroduces a structural defect on
  re-run).
- This reuse-by-XInclude is deliberately designed to be "amenable to graphing" per the session's
  stated intent (§4) without building a literal graph export in this pass: `xml:id` +
  `xlink:arcrole` (CiTO citation-typing, e.g. `citesAsAuthority`/`isCitedAsAuthorityBy`) +
  XInclude reuse already give a fully walkable, typed citation network via plain XPath. A literal
  RDF/Turtle (or similar) export is real future work this structure must not preclude, but it is
  explicitly not a deliverable of this design.
- File-per-entry also gives git-native versioning for free: each citation's own history is
  independently tracked, diffable, and blameable, with no additional tooling.

## 4. Entry typing

Every `biblioentry`/`bibliomixed` carries `@role`, a native DocBook attribute (confirmed present
in the real 5.2 schema: `db.biblioentry.role.attribute`). Populated from eyecite's own citation
classification where it resolves (e.g. `role="case"` for a `FullCaseCitation`, `role="statute"`
for a law citation), not a separately hand-rolled classifier -- reusing eyecite's vocabulary as the
source of truth for what kind of citation something is. Falls back to `role="secondary"` for
non-legal sources eyecite doesn't classify, and `role="needs-research"` for entries where no real
citation is recoverable at all (Category B, and any flat works-cited entry with no verifiable
citation).

## 5. eyecite's role (installed and verified 2026-07-26)

[Free Law Project's `eyecite`](https://github.com/freelawproject/eyecite) is a real, actively-
maintained legal-citation extraction/parsing library -- not apt-packaged, installed via a Python
venv (Debian's PEP 668 "externally managed environment" blocks a bare system-wide `pip install`;
`lxml` avoided this because it *was* apt-packaged, eyecite is not). Verified directly against real
corpus text, not assumed:

- **Works well** on text that already contains a properly-formatted citation: `Alice Corp. v. CLS
  Bank Int'l, 573 U.S. 208 (2014)` parses correctly into plaintiff, defendant, court (inferred from
  the reporter), and year.
- **Does not conjure a missing citation out of a webpage title.** Most of the corpus's 5,482 flat
  entries are secondary-aggregator titles (`"Alice v. CLS Bank: ... accessed September 2, 2025"`),
  not formatted citations -- eyecite correctly finds nothing there, because there is nothing there
  to find. This is not a tool limitation to work around; it is the same no-fabrication signal the
  2026-07-23 design already established: if the real citation isn't recoverable from the text,
  eyecite's inability to parse it *is* the correct outcome, not a failure.

Three roles, all confirmed in scope by direct user decision (2026-07-26):

1. **Validator/acceptance-gate.** Every biblioentry's citation content must parse cleanly through
   eyecite before it counts as "standard" for legal-type entries -- a second, independent,
   authoritative correctness check alongside the DocBook-structure check
   `measure_citation_conformance.py` already performs. Neither check alone is sufficient: DocBook-
   valid does not mean legally well-formed, and eyecite-parseable does not mean DocBook-valid.
2. **Extraction aid.** Run across a document's full resolved text (not just its isolated
   works-cited entries) to recover cases where a real citation already exists somewhere nearby,
   even if the works-cited listitem itself is just a webpage-title stub.
3. **Explicit flagging, never fabrication.** Anything eyecite can't resolve and that has no
   recoverable citation gets `role="needs-research"` in the standardized structure itself --
   queryable, visible, not silently dropped and not guessed at.

## 6. Migration strategy: split by what's mechanically verifiable

- **Automated, bulk-converted:** flat works-cited entries where eyecite confirms a real citation
  (directly or via nearby-text extraction), and Category A numbered-citation documents (full
  reference list confirmed intact, exact positional correspondence). Low fabrication risk -- the
  source text already fully specifies the citation, or eyecite independently confirms it. Gated by
  a stratified human-reviewable sample before landing (reusing the 2026-07-23 design's own
  verification philosophy: passing automated checks is necessary, not sufficient, for content this
  consequential).
- **Explicitly excluded from the bulk pass:** Category B documents and any flat entry with no
  eyecite-confirmable citation. These get `role="needs-research"` and stay there. This is not
  blocking the rest of the corpus's conversion, and it is not something any script -- heuristic or
  eyecite-based -- should ever guess at.

This gives the implementation plan a natural shape: mechanical, automatable, low-risk work lands
first and measurably shrinks the red/green numbers fast (`measure_citation_conformance.py` as the
acceptance gate throughout, same tool re-run per document as it converts); research-dependent work
is tracked explicitly and separately, never silently deferred or fabricated.

## 7. Explicit scope for this design

**In scope:**
- The entry-file architecture (§3) and its schema/XInclude mechanics.
- `@role` typing driven by eyecite (§4).
- Classifying which of the 96 numbered-citation documents are Category A vs. B (only 4 have been
  checked by hand so far -- 2 confirmed A, 2 confirmed B).
- Converting Category A numbered-citation documents and eyecite-confirmable flat entries.
- Flagging (not resolving) Category B and eyecite-unconfirmable flat entries as `needs-research`.
- A successor to `build_bibliography.py` that generates (not hand-maintains) both the per-document
  and repo-wide bibliographies from the entry files.

**Explicitly out of scope, not precluded:**
- A literal graph/RDF export (§3) -- future work over data this design shapes correctly for it.
- Actually researching and resolving `needs-research` entries -- that is real work this design
  makes trackable, not work this design performs.
- Recovering Category B references from original chat sessions -- opportunistic if a session
  happens to still be accessible and checked case-by-case, never a planning dependency (per
  2026-07-26 direction: "not reliably accessible... don't assume recoverable").

## 8. Relationship to existing specs

Supersedes, in the specific ways already annotated 2026-07-26 in place (not silently rewritten):
- `docs/superpowers/specs/2026-07-23-consolidated-bibliography-design.md` §4, §5, §8.
- `docs/superpowers/plans/2026-07-23-consolidated-bibliography-plan.md` (top-of-file note).
- `docs/superpowers/plans/2026-07-25-external-metadata-ontology-standardization.md` Task 7 (deleted
  from the active task list; its scope note is exactly the pattern this design corrects).

`docs/scripts/measure_citation_conformance.py` (built 2026-07-26, TDD, 13 tests, committed) is the
RED/GREEN measurement harness this whole project runs against, both for the initial baseline and
for verifying every future conversion actually lands.

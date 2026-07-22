# Corpus Atomization: Decomposing Documents into Reusable Section Fragments

## 1. Motivation

The corpus's DocBook 5.2 documents (117 corpus documents plus the flagship paper's 2 articles)
are each a single monolithic `.xml` file. The largest, `the-architecture-of-non-consensual-legality.xml`,
is ~18.4k words in one file. Editing any part of a large document — by a human or by an LLM
coding agent — currently requires loading and reasoning about the entire file, even when the
change is local to one section. This is the core problem this design solves: **atomize
documents into independently-editable, LLM-context-sized parts**, structured so the original
document is still exactly reconstructable from its parts.

A secondary benefit falls out of the same mechanism: once a section is its own addressable
file, it can be referenced (via XInclude) from a *different* document too — content becomes
remixable across the corpus, not just internally organized. This is a welcome consequence,
not the primary driver.

Metadata deduplication is a related, smaller problem discovered during investigation: all 117
`.meta.xml` files are byte-identical except for `<dc:title>`. It's folded into this same design
because it uses the same underlying mechanism (XInclude composition) and touches the same tool
code paths.

**Scope:** this applies uniformly across the *entire* repository — all 117 corpus documents
(court-record matters/evidence/findings, theory, cross-cutting, wip, proposals) *and* the
flagship paper's 2 articles. No document format is treated as a special case.

## 2. Architecture: Shell + Section Fragments

Every document becomes a thin "shell" `.xml` file — same filename, same location — whose body
is a sequence of `<xi:include>` elements, one per **top-level** section, instead of the
sections' actual content. Each section's content moves into its own file in a new subdirectory
named after the document's stem:

```
docs/cross-cutting/patron-as-client.xml          ← thin shell (unchanged path)
docs/cross-cutting/patron-as-client.meta.xml      ← now just <dc:title> + shared-metadata include
docs/cross-cutting/patron-as-client.html          ← built output, unchanged shape
docs/cross-cutting/patron-as-client/
    01-background.xml                             ← <section xml:id="background">...
    02-analysis.xml                                ← <section xml:id="analysis">...
    03-conclusion.xml
```

Numeric prefixes (`01-`, `02-`, ...) exist purely so `ls` sorts fragments in document order for
human navigation. The actual document order is determined by the shell's own sequence of
`<xi:include>` elements, not by directory listing. Fragment filenames use the existing
`slugify()` function already in `convert_to_docbook.py`, applied to each section's title.

This requires **no new build machinery**. `xmllint --xinclude`, `jing`, and `xsltproc
--xinclude` already resolve XInclude recursively — that's exactly how `.meta.xml` inclusion
works today. A fully-resolved shell produces the identical tree structure the corpus has today,
so validation and HTML/LaTeX build commands don't change; they just happen to be validating/
building a tree assembled from several files instead of one.

The Makefile-driven paper build needs **zero changes**: `SRCS := $(wildcard src/0*.xml)` only
matches files directly in `src/`, not inside a subdirectory, and shell files keep their original
name and location. The paper's `01-llm-database-theory.xml` and `02-legal-corpus-connections.xml`
get split into `src/01-llm-database-theory/NN-slug.xml` and
`src/02-legal-corpus-connections/NN-slug.xml` fragments exactly like corpus documents, and the
Makefile keeps working unmodified.

## 3. Splitting Depth: One Level Only

Only sections that are **direct children of `<article>`** become their own file. A nested
subsection stays embedded in its parent's fragment:

```
<article>
  <section xml:id="background">        →  01-background.xml, containing the FULL subtree:
    <title>Background</title>              <section xml:id="background">
    <para>...</para>                         <title>Background</title>
    <section xml:id="background-sub1">       <para>...</para>
      <title>Sub-point</title>               <section xml:id="background-sub1">
      <para>...</para>                          <title>Sub-point</title>
    </section>                                  <para>...</para>
  </section>                                  </section>
                                             </section>
  <section xml:id="analysis">           →  02-analysis.xml
    ...
  </section>
</article>
```

If a top-level section itself has many large subsections, its fragment file inherits that size.
The tool does not recursively re-split. This is an accepted limitation: if a specific section
later proves too large in practice, it can be manually split further using the same mechanism
(a fragment is free to contain its own `<xi:include>`s to sub-fragments) — a deliberate future
action, not automatic tool behavior.

**Documents with no top-level `<section>` at all** (the many existing "flat" documents where
`wrap_fragment()` unwrapped a lone top-level section, leaving `<para>`/`<orderedlist>`/etc.
directly under `<article>`) have nothing to split — they remain single-file, exactly as today.
This isn't special-cased; it falls out naturally from "split what direct-child sections exist."

## 4. Architecture: Shared Metadata

One new file, `docs/common/shared-metadata.xml`, holds the boilerplate currently duplicated
across all 117 corpus `.meta.xml` files: `dc:creator`, `dc:publisher`, `dc:type`,
`dc:language`, `dc:rights`, `authorgroup`, `legalnotice`. Each corpus document's `.meta.xml`
shrinks to just its own `<dc:title>` plus one `<xi:include>` pulling in the shared file:

```xml
<info xmlns="http://docbook.org/ns/docbook" xmlns:dc="http://purl.org/dc/terms/"
      xmlns:xi="http://www.w3.org/2001/XInclude">
  <dc:title>Analysis of Potential Service Contracts within the Google Ecosystem</dc:title>
  <xi:include href="../common/shared-metadata.xml"/>
</info>
```

(The relative path depends on the document's own depth under `docs/` — e.g. `../common/`
for a `docs/cross-cutting/*.meta.xml` file, `../../../../common/` for a file 4 levels down
like `docs/court-record/matters/<matter>/evidence/*.meta.xml`. `write_metadata()` computes
this from the document's actual path.)

**Constraint discovered during investigation:** `jing` does not support the `xpointer()`
XPointer scheme that `xmllint --xinclude` does. Including *multiple sibling elements* from one
shared file (as opposed to one element that itself is the file's root) requires either that
scheme or an XPointer element-scheme workaround — both fail `jing`. The scheme that works with
**both** tools: a plain `<xi:include href="shared-metadata.xml"/>` with no `xpointer` attribute,
which inserts the *entire root element* of the target file as a single child. This means
`shared-metadata.xml`'s boilerplate ends up wrapped one element deeper than it would with the
document's own inline content:

```xml
<!-- resolved result, inside <info> -->
<dc:title>...</dc:title>
<shared xmlns="http://docbook.org/ns/docbook" ...>
  <dc:creator>...</dc:creator>
  <dc:publisher>...</dc:publisher>
  ...
  <authorgroup>...</authorgroup>
  <legalnotice>...</legalnotice>
</shared>
```

This requires exactly two small XPath changes in `html5.xsl` (already hand-tested against a
throwaway fixture): the two direct-child lookups (`db:info/db:legalnotice/db:para` and
`db:authorgroup/db:author/...` inside the `db:info` template) become descendant-axis lookups
(`db:info//db:legalnotice/db:para`, `.//db:authorgroup/db:author/...`) so they find the fields
regardless of the extra wrapper level. `db:legalnotice`'s existing suppress-from-body template
(`<xsl:template match="db:legalnotice | db:bibliomisc"/>`) needs no change — template *matching*
by element name works at any depth automatically. **The identical two-line change is needed in
`latex.xsl`**, which has the same direct-child lookups, for the paper's metadata sharing (see
Section 6). Section fragments (Section 2) need no such workaround — a fragment's root **is**
the `<section>` element itself, so a plain `xi:include` inserts it directly with no extra
wrapper, matching the schema's existing `block-content` pattern with no changes needed there.

## 5. Remix Workflow

No new catalog, index, or registry is being built. A fragment is a normal, well-formed,
standalone XML file with its own `xml:id`. To reuse one in a different document: open that
document's shell and add another `<xi:include href="...">` pointing at the existing fragment,
wherever it should appear among that document's own sections.

```xml
<!-- inside .../google-platform-misclassification/evidence/bar.xml -->
<xi:include href="../../copyright-ip-authorship/evidence/foo/02-abc-test-standard.xml"/>
```

That's the entire mechanism — the next `xmllint --xinclude` / `jing` / `xsltproc --xinclude`
run picks it up automatically, since XInclude resolution doesn't distinguish "a document's own
fragment" from "someone else's fragment." Discovery is ordinary `grep`/search across `docs/`.

**Caveat to flag, not solve:** once a fragment is included from more than one document, editing
it changes both places. That's the intended point of "remix" (single source of truth), but it
means a shared fragment is no longer private to whichever document originally held it. No
"what includes this file" tooling is being built now; if this becomes a real problem later,
that's separate future work.

## 6. Paper-Specific Metadata Sharing

The paper's `00-metadata.xml` has real paper-only content the corpus boilerplate doesn't:
`dc:title`, `dc:date`, `dc:subject`, `dc:description`, the Schema.org JSON-LD `bibliomisc`
block, an `<abstract>`, and a `dc:creator`/`legalnotice` crediting AI research assistance —
alongside fields that genuinely overlap with the corpus's shared block (`dc:publisher`,
`dc:language`, `dc:rights`, and the primary author's name/email within `authorgroup`).

`00-metadata.xml` keeps its paper-specific fields inline, and adds one
`<xi:include href="../../../../common/shared-metadata.xml"/>` for the overlapping fields —
same mechanism, same wrapper caveat, same `latex.xsl`/`html5.xsl` XPath fix as Section 4. Its
own distinct `authorgroup` entry (which includes a `<uri>` the corpus's shared authorgroup
doesn't) and its distinct `legalnotice` (AI-assistance credit) stay local to `00-metadata.xml`,
not pulled from the shared file — only the corpus-wide-identical fields move.

## 7. Tool Changes (`convert_to_docbook.py`)

- **New `split_into_fragments(article_element, out_dir, stem)` function**, used both by fresh
  conversions and by the migration script (Section 8). Walks the wrapped article's direct
  children; for each `db:section`, writes it to `<out_dir>/<stem>/NN-<slug>.xml` and replaces it
  in the article with an `<xi:include href="<stem>/NN-<slug>.xml"/>` placeholder. If there are
  no direct-child `db:section` elements, this is a no-op (document stays monolithic).
- **`write_metadata()`** changes to write the minimal `<dc:title>` + shared-metadata
  `xi:include` form, computing the correct relative path depth from the document's own
  directory to `docs/common/shared-metadata.xml`.
- **`content_preservation_diff()`** currently reads the raw XML file to round-trip through
  `pandoc -f docbook`. It must instead resolve XIncludes first (`xmllint --xinclude`) before
  handing the result to pandoc, since a shell file alone no longer contains the section content
  being diffed.
- **`validate()` and `build_html()`** need no logic changes — both already operate via
  `xmllint --xinclude` / `jing` / `xsltproc --xinclude` against the shell's path, which already
  resolves the full tree.

## 8. Migration of Existing Documents

All 117 corpus documents and the paper's 2 articles are already-converted, already-valid
DocBook. This migration is a **deterministic, mechanical transform** of already-clean input —
unlike the original Markdown→DocBook conversion, it needs no per-document human judgment calls
(no title-extraction ambiguity, no malformed-markup classes to triage).

Process per document: parse the current monolithic `.xml`, run it through the same
`split_into_fragments()` used for fresh conversions, rewrite `.meta.xml` to the shared-metadata
form, then verify:
1. `xmllint --xinclude` on the new shell reproduces the original monolithic content exactly
   (structurally/textually, ignoring the `xml:base` provenance attributes XInclude adds).
2. `jing -c docbook-corpus.rnc` passes on the new shell.
3. `xsltproc --xinclude html5.xsl` (and, for the paper, `latex.xsl`) rebuilds byte-equivalent
   output to what's currently live/committed.
4. The existing word-level `content_preservation_diff()` (updated per Section 7) reports no
   changes.

**Rollout:** pilot on 2 documents first — one small, and
`the-architecture-of-non-consensual-legality.xml` (the largest, most likely to expose an edge
case with many top-level sections) — verify fully, then run the migration across the remaining
115 corpus documents plus the paper's 2 articles as one batch, since the transform is
mechanical and self-verifying per document. Any document that fails verification gets flagged
for manual inspection rather than silently proceeding, consistent with the safety-net principle
already established for this tool (a `.md` is never `git rm`'d if its content-diff flags
anything; the same standard applies here to the pre-migration `.xml`).

## 9. CI / Build Tooling Impact

`build-corpus.yml`'s current file-discovery loop (`find docs -name '*.xml' -not -name
'*.meta.xml' -not -path 'docs/papers/*' -not -path '*/scratch/*'`) would incorrectly also match
the new section-fragment files and `docs/common/shared-metadata.xml` — none of which have a
`db:article` root, so `jing` would fail validating them against the schema's `start` pattern,
and `xsltproc html5.xsl` would produce broken/incomplete output (the root template only matches
`/db:article`).

**Fix:** discriminate by root element, not by path — only process `.xml` files whose root
element is `db:article` (checked via `xmllint --xpath 'name(/*)'` or equivalent). This is robust
regardless of directory naming or nesting, and also means the `docs/papers/*` path exclusion
can be dropped now that the paper is in scope (Section 1) — the root-element check alone
correctly skips the paper's `00-metadata.xml` and any of its new fragment files while still
picking up its 2 real articles.

The paper's own `Makefile` needs no changes (Section 2 — `wildcard src/0*.xml` already only
matches files directly in `src/`).

## 10. Testing Strategy (TDD)

New tests in `docs/scripts/tests/test_convert_to_docbook.py`, written before the
implementation (RED), then made to pass (GREEN) — same discipline used for the original tool:

- **Multi-section fixture** (3 top-level `<section>`s): asserts `split_into_fragments()`
  produces 3 correctly-named/slugged fragment files, a shell that includes them in the original
  order, and that `xmllint --xinclude` on the shell reproduces the original unsplit content.
- **Flat/unwrapped fixture** (no top-level `<section>` — direct `<para>` children, matching
  today's many single-heading documents): asserts no fragments directory is created and the
  document stays monolithic. Regression protection for the existing corpus shape.
- **Nested-section fixture**: asserts only the top-level section is extracted, with its nested
  subsection staying embedded inline — proves the one-level-only rule (Section 3) is enforced,
  not accidentally recursive.
- **Metadata-dedup test**: asserts the new minimal `.meta.xml` resolves via `xmllint --xinclude`
  to all expected `dc:*` fields from the shared file.

After unit tests pass: pilot verification per Section 8, then full corpus rebuild, full test
suite (`python3 -m unittest discover`), full corpus link/anchor sweep, and a `build-corpus.yml`
dry run before the batch migration, then after it.

## 11. Out of Scope / Non-Goals

- No fragment catalog, index, or "what includes this file" tooling (Section 5).
- No recursive re-splitting of oversized nested subsections (Section 3).
- No changes to `docs/index.md` link structure — shells keep their existing filenames/paths, so
  every existing link (`.html` built output) is unaffected.
- No changes to the paper's Makefile (Section 2, Section 9).

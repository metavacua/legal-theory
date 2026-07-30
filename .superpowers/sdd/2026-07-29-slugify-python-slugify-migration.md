# slugify() em/en-dash word-jamming — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace `scripts/convert_to_docbook.py`'s hand-rolled `slugify()` (which silently *deletes* characters outside `[\w\s-]` — including em dashes `–` and en dashes `—`, since Python's unicode-aware `\w` doesn't match them — instead of converting them to a separator, jamming adjacent words together) with the standard `python-slugify` package, while preserving `slugify()`'s exact existing contract (leading-digit `s-` prefix, empty-input `"s"` fallback) for every call site.

**Architecture:** `slugify.slugify()` (the `python-slugify` package) replaces only the internal "turn arbitrary text into a lowercase, hyphen-separated, filesystem/XML-id-safe string" step. This project's own two post-processing rules — prefix `s-` onto a result that starts with a digit (XML `NCName`s can't start with a digit; enforced independently for pandoc-generated ids too, by the pre-existing, unchanged `sanitize_xml_ids()`), and fall back to the literal string `"s"` for an empty result — are project-specific conventions a generic slugifier has no opinion about, so they stay, reapplied to whatever `python-slugify` returns.

**Tech Stack:** `python-slugify` (PyPI) / `python3-slugify` (Debian apt package, `python3-slugify` 4.0.0-2 in this environment) — both confirmed byte-identical in output on every case this plan exercises (see Research Finding 4).

## Global Constraints

- MUST preserve `slugify(text)`'s existing signature and contract exactly: pure function, `str -> str`, empty/whitespace-only input → `"s"`, digit-leading result → `s-`-prefixed, never raises for any string input. No caller's code changes.
- MUST NOT change `derive_entry_key()`'s return shape (`str`, `[:80]`-capped) or `write_biblioentry()`/`split_into_fragments()`/`convert()`'s use of the slug as an XML `xml:id` / fragment file name / `linkend` target.
- MUST install `python-slugify` into a dedicated venv, following the precedent `scripts/eyecite_classify.py` established for this repo (gitignored `.venv-<name>/`, created with `python3 -m venv`, package installed with a plain `pip install`, since Debian's PEP 668 "externally managed environment" blocks a bare system-wide `pip install`).
- **Deviation from that precedent, reasoned explicitly (do not silently "just follow the pattern" here):** `eyecite_classify.py` is a narrow, standalone module imported by exactly one other script (`build_bibliography.py`, on a sibling branch not yet merged here), so gating it behind a venv-only guarded import only ever affects a small, separately-skip-gated slice of the test suite. `convert_to_docbook.py` is the opposite: it is imported, directly or transitively, by essentially every script in `scripts/` (`citation_entry.py`, `convert_numbered_citations.py`, `build_bibliography.py`, `atomize_existing_document.py`, `measure_citation_conformance.py`, `migrate_to_native_metadata.py`, `classify_numbered_citations.py`, `generate_index.py`, `check_dcterms_completeness.py`) and by the majority of the 260 tests the bare-`python3` suite already runs and passes today. A venv-only, guarded-with-`RuntimeError` import (the eyecite pattern) would force skip-gating on the order of 15–20 currently-passing, currently-ungated tests across three test files, would make `python3 scripts/convert_to_docbook.py <doc>.md` — this tool's own documented CLI entry point — stop working under bare `python3`, and would directly contradict both "preserving its existing signature/contract" and the mandate's own final verification command (bare `python3 -m unittest discover`, expected to report `OK`, not a large new skip count). Verified directly (Research Finding 3) that, unlike `eyecite`, a real Debian package exists for this one (`python3-slugify`, apt candidate `4.0.0-2`) and is confirmed byte-identical in output to the pip package (Research Finding 4) on every case this plan tests. Resolution: **do both** — create the dedicated venv exactly as instructed (Task 1 Step 1), *and* install `python3-slugify` system-wide via apt (Task 1 Step 2) so `import slugify` succeeds under bare `python3` the same way `import re`/`subprocess` already do, with **no** try/except guard in `convert_to_docbook.py` — matching this exact file's own existing, unguarded style for its other non-stdlib runtime dependencies (`pandoc`, `jing`, `xmllint`, all invoked via bare `subprocess.run([...])` with no presence check anywhere in the file — confirmed by direct inspection, Research Finding 5).
- MUST NOT alias the import as `slugify` — `from slugify import slugify` followed by `def slugify(text): ...` would make the function shadow the import in the module namespace, so any call to `slugify(...)` *inside* the new function body would recurse into itself (`RecursionError`), not the library. Import as `from slugify import slugify as _slugify` and call `_slugify(...)` inside the wrapper.
- ONE commit for this fix (matching this repo's established one-commit-per-bug convention, confirmed by the sibling remediation branches' history).

---

## Research findings that drive this design (verified 2026-07-29, do not re-derive)

1. **Root cause, confirmed by direct tracing, not assumption:** `re.sub(r"[^\w\s-]", "", text)` strips any character that is not a unicode word character, not whitespace, and not a literal hyphen. An em dash (`—`, U+2014) or en dash (`–`, U+2013) matches none of the three, so it is deleted outright, not replaced. If the dash had whitespace on *both* sides (e.g. `"Markets – An Era"`), the subsequent `re.sub(r"\s+", "-", text)` incidentally still produces one hyphen (deleting the dash leaves two adjacent spaces, which collapse to one `-`) — but when the dash is glued directly to a word on at least one side (e.g. `"Wisconsin–Madison"`, `"Duality—A"`), there is no surrounding whitespace to collapse, and the two words are jammed together with **no separator at all**.
2. **Confirmed real, already-materialized corpus impact — not hypothetical, not merely "165 works-cited entries contain the character somewhere":**
   - Corpus-wide scan of every `Category A` document's `works-cited` section (`docs/bibliography/numbered-citation-classification.json`) found 164 listitems with an em/en dash in their display text across 65 documents — consistent with the task brief's "165 across 66." Every one of these has an `<link xlink:href="https://...">`, so `citation_entry.derive_entry_key()`'s href branch (`slugify(f"{host}-{tail}")`) is what actually runs for them, not the raw-text fallback — and none of their URLs' host/tail happen to contain a dash (confirmed directly), so *this specific population's derived keys* are not currently corrupted. The bug is still real and live through this exact call path (`derive_entry_key` unconditionally calls `slugify()` either way), and both `derive_entry_key()` code paths are exercised directly by this plan's new tests (Task 2) regardless.
   - **Stronger, already-committed evidence:** scanning every already-split document fragment's own `<title>` against its own already-committed filename found 11 fragment files, across 6 documents, whose filename is **already word-jammed in the repository today** — real output from a real prior run of this exact buggy function, not a synthetic test case. Examples (title → committed, jammed filename slug):
     - `"Conclusion: Reconciling the Duality—A Spectrum of Intent and Context"` → `conclusion-reconciling-the-dualitya-spectrum-of-intent-and-context` (file: `docs/court-record/matters/copyright-ip-authorship/evidence/ip-creation-service-or-self-expression/04-conclusion-reconciling-the-dualitya-spectrum-of-intent-and-context.xml`)
     - `"Part I: Deconstructing the Illicit—The Legal Architecture of Prohibition in California"` → `...-illicitthe-...`
     - `"Section 1: The Legal Void—Anatomy of the Illicit Prostitution Contract"` → `...-voidanatomy-...`
     - (8 more of the same shape, all under `docs/court-record/` and `docs/proposals/`)
3. **`python3-slugify` has a real Debian apt package** (`apt-cache policy python3-slugify` → candidate `4.0.0-2`, bookworm/main), directly contradicting the task brief's premise that it is "a non-apt Python package" like `eyecite`. Installed and confirmed importable as `import slugify; slugify.slugify(...)`.
4. **apt's `python3-slugify` 4.0.0-2 and pip's `python-slugify` 8.0.4 produce byte-identical output** on every case this plan exercises: `"A Flat Document"` → `"a-flat-document"`; `"1. First Section"` → `"1-first-section"`; `""` → `""`; `"   "` → `""`; `"University of Wisconsin–Madison"` → `"university-of-wisconsin-madison"`; `"Conclusion: Reconciling the Duality—A Spectrum of Intent and Context"` → `"conclusion-reconciling-the-duality-a-spectrum-of-intent-and-context"`; `"  --leading and trailing---separators--  "` → `"leading-and-trailing-separators"`; `"café résumé"` → `"cafe-resume"` (unicode transliteration, confirming the task brief's claim about this). Neither version adds the project-specific leading-digit `s-` prefix or the empty-string `"s"` fallback — those remain this wrapper's own responsibility, unchanged.
5. **`convert_to_docbook.py` already has an established, in-file precedent for treating a non-stdlib runtime dependency as unconditionally present, no guard, no presence check**: every one of its `pandoc`/`jing`/`xmllint` invocations (`pandoc_to_docbook_fragment`, `validate`, `fetch_docbook_schema`, `build_html`, `render_docbook_plain`, etc.) is a bare `subprocess.run([...])` call with no `try/except FileNotFoundError` anywhere in the file — confirmed by direct grep. A plain, unguarded `from slugify import slugify as _slugify` at module level matches this file's own existing house style exactly, once the dependency is genuinely, permanently present (Global Constraints).
6. **All 4 call sites of `slugify()`, confirmed by grep across the entire `scripts/` tree (not just this file):**
   - `convert_to_docbook.py:226` — `base_slug = slugify(section_title)`, used to build a fragment **file name** (`frag_dir / f"{i:02d}-{slug}.xml"`).
   - `convert_to_docbook.py:467` — `xml_id = slugify(md_path.stem)`, becomes `<article xml:id="...">` (Task 4's `derive_identifier()` does **not** feed off this — see Finding 7 — but the built HTML's XSLT rendering surfaces this id as an in-page anchor/**URL fragment**).
   - `citation_entry.py:36` — `slugify(f"{host}-{tail}")[:80]` inside `derive_entry_key()`'s href branch — becomes both a `<biblioentry xml:id>` and a **file path** (`ENTRIES_DIR / f"{key}.xml"`), and a `<biblioref linkend="KEY"/>` cross-reference (a **URL fragment**, `#KEY`, once rendered to HTML).
   - `citation_entry.py:37` — `slugify(text)[:80]`, `derive_entry_key()`'s no-href fallback branch — same downstream file-path/URL-fragment usage as the href branch.
   - No other file in `scripts/` imports or calls `slugify` (confirmed by `grep -rn "slugify" scripts/*.py`).
7. **`derive_identifier()` does *not* call `slugify()`, directly or transitively — confirmed, not assumed.** It builds a GitHub blob URL from `_content_path_for_meta(meta_path)`, which in turn resolves from the **already-existing, on-disk `.meta.xml`/`.xml` file path** — and that file's own name is written using the **raw**, unslugified `md_path.stem` (`xml_path = out_dir / f"{md_path.stem}.xml"` in `convert()`), not `slugify(md_path.stem)` (that slugified value is used only for the *`xml:id` attribute*, a separate variable, `xml_id`). This fix therefore cannot change `derive_identifier()`'s output for any input; `test_derive_identifier_is_a_github_blob_url` needs no change and is re-run only as a regression check (Task 3), not extended.
8. **No existing test fixture is affected by the implementation swap.** Every Markdown fixture heading under `scripts/tests/fixtures/*.md` was checked directly (`grep -n "^#"`) — none contain a dash, apostrophe, colon, or other punctuation whose handling differs between the old regex and `python-slugify` (e.g. `python-slugify` also turns an apostrophe into a separator rather than deleting it — a second instance of the *same* underlying defect category the task brief describes, not a special-cased fix — but no current fixture exercises this, so no existing expected value changes).

---

## File Structure

- Modify: `scripts/convert_to_docbook.py` — new guarded-free `from slugify import slugify as _slugify` import; `slugify()`'s body replaced.
- Modify: `.gitignore` — add `.venv-slugify/`.
- Modify: `scripts/tests/test_convert_to_docbook.py` — new tests in `TestSlugifyAndTitle` (dash word-jam fix ×2 real titles, separator collapse, leading/trailing strip) and `TestSplitIntoFragments` (one real-title end-to-end pandoc round-trip test).
- Modify: `scripts/tests/test_citation_entry.py` — new tests in `TestDeriveEntryKey` (dash in the no-href fallback branch, dash inside an href's host/tail, leading-digit-prefix preserved through this call site).
- Create: `scripts/tests/fixtures/em_dash_title_section.md` — new fixture, a real corpus title (verbatim) used as a Markdown heading.

---

## Task 1: Provision the `python-slugify` dependency

**Files:** none (environment setup only — no source changes).

**Interfaces:**
- Produces: `slugify` importable as a Python module under both `.venv-slugify/bin/python3` and bare `python3`, ready for Task 2's `import`.

- [ ] **Step 1: Create the dedicated venv and install `python-slugify` into it (the literal precedent instruction)**

```bash
cd /home/metavacua/legal-theory/.worktrees/claude/fixes/slugify
python3 -m venv .venv-slugify
.venv-slugify/bin/pip install --quiet python-slugify
.venv-slugify/bin/python3 -c "from slugify import slugify; print(slugify('University of Wisconsin–Madison'))"
```

Expected: `university-of-wisconsin-madison`.

- [ ] **Step 2: Install the apt package system-wide, so bare `python3` also has it (Global Constraints deviation)**

```bash
sudo apt-get install -y python3-slugify
python3 -c "from slugify import slugify; print(slugify('University of Wisconsin–Madison'))"
```

Expected: `Setting up python3-slugify ...` in the install output, then `university-of-wisconsin-madison` from the bare-`python3` check — confirming the two installs agree (Research Finding 4) before any source file depends on either.

- [ ] **Step 3: Gitignore the venv**

Add to `.gitignore` (after the existing `.venv-eyecite/` line):

```
.venv-slugify/
```

- [ ] **Step 4: Verify nothing is broken yet**

```bash
python3 -m unittest discover -s scripts/tests -p "test_*.py" 2>&1 | tail -5
```

Expected: `OK (skipped=8)` — identical to the pre-existing baseline (nothing about `slugify()`'s *implementation* has changed yet, only the environment).

---

## Task 2: Replace `slugify()`'s implementation (TDD)

**Files:**
- Create: `scripts/tests/fixtures/em_dash_title_section.md`
- Modify: `scripts/tests/test_convert_to_docbook.py` (`TestSlugifyAndTitle`, `TestSplitIntoFragments`)
- Modify: `scripts/tests/test_citation_entry.py` (`TestDeriveEntryKey`)
- Modify: `scripts/convert_to_docbook.py` (imports, `slugify()`)

**Interfaces:**
- Consumes: `slugify` module (Task 1).
- Produces: `slugify(text) -> str` — same signature as before; `_slugify` (module-private alias for the library function, not itself part of the public contract).

- [ ] **Step 1: Create the new fixture**

Create `scripts/tests/fixtures/em_dash_title_section.md`:

```markdown
## Conclusion: Reconciling the Duality—A Spectrum of Intent and Context

Real corpus section title, reused verbatim to pin the fragment-filename
fix through the real pandoc round-trip.

## Second Section

More content for the second section.
```

- [ ] **Step 2: Write the failing tests in `test_convert_to_docbook.py`**

Add to `TestSlugifyAndTitle` (after the existing `test_slugify_empty_string`):

```python
    def test_slugify_converts_em_dash_to_separator_not_deletion(self):
        # Real corpus text (appears verbatim in 3 works-cited entries
        # under docs/court-record/matters/cooperative-investment-law/
        # and in docs/bibliography/references.xml). Confirmed
        # 2026-07-29: the old hand-rolled regex
        # (re.sub(r"[^\w\s-]", "", text)) silently deleted the en dash
        # itself -- unicode-aware \w/\s don't match it, and it isn't a
        # literal "-" -- jamming the two adjacent words together with
        # no separator at all: "university-of-wisconsinmadison".
        from convert_to_docbook import slugify
        self.assertEqual(
            slugify("University of Wisconsin–Madison"),
            "university-of-wisconsin-madison",
        )

    def test_slugify_converts_em_dash_to_separator_not_deletion_real_section_title(self):
        # Real corpus section title
        # (docs/court-record/matters/copyright-ip-authorship/evidence/
        # ip-creation-service-or-self-expression/). This exact jammed
        # slug ("...dualitya...") is the CURRENTLY COMMITTED fragment
        # filename in this repo today -- real output from a real prior
        # run of this same buggy function, not a synthetic case.
        from convert_to_docbook import slugify
        self.assertEqual(
            slugify("Conclusion: Reconciling the Duality—A Spectrum of Intent and Context"),
            "conclusion-reconciling-the-duality-a-spectrum-of-intent-and-context",
        )

    def test_slugify_collapses_repeated_separators(self):
        # The old implementation had no collapse step of its own for
        # runs of the *literal* "-" character (only for whitespace) --
        # "hello---world" passed straight through re.sub(r"[^\w\s-]",
        # "", ...) unchanged (hyphens are explicitly allowed), then
        # re.sub(r"\s+", "-", ...) had nothing to collapse (no
        # whitespace present), leaving the triple hyphen intact.
        from convert_to_docbook import slugify
        self.assertEqual(slugify("hello---world"), "hello-world")

    def test_slugify_strips_leading_and_trailing_separators(self):
        from convert_to_docbook import slugify
        self.assertEqual(slugify("--hello--"), "hello")
```

Add to `TestSplitIntoFragments` (after the existing `test_bold_wrapped_title_produces_descriptive_slug`):

```python
    def test_em_dash_title_produces_hyphenated_not_jammed_fragment_slug(self):
        # Root-caused on docs/court-record/matters/copyright-ip-
        # authorship/evidence/ip-creation-service-or-self-expression/,
        # whose ALREADY-COMMITTED fragment filename
        # ("04-conclusion-reconciling-the-dualitya-spectrum-of-intent-
        # and-context.xml") is live, real evidence of this exact
        # defect. This fixture reuses that real title verbatim to
        # confirm the fix through the full pandoc round-trip, not just
        # the slugify() unit alone.
        from convert_to_docbook import (
            pandoc_to_docbook_fragment, wrap_fragment, split_into_fragments,
        )
        fragment = pandoc_to_docbook_fragment(self.fixtures / "em_dash_title_section.md")
        article, _ = wrap_fragment(
            fragment, "em-dash-title", "Em Dash Title Test", "em-dash-title.meta.xml"
        )

        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            split_into_fragments(article, out_dir, "em-dash-title")

            frag_dir = out_dir / "em-dash-title"
            frag_names = sorted(f.name for f in frag_dir.iterdir())
            self.assertEqual(
                frag_names,
                [
                    "01-conclusion-reconciling-the-duality-a-spectrum-of-intent-and-context.xml",
                    "02-second-section.xml",
                ],
            )
```

- [ ] **Step 3: Write the failing tests in `test_citation_entry.py`**

Add to `TestDeriveEntryKey` (after the existing `test_falls_back_to_slugified_text_when_href_has_no_recognized_scheme`):

```python
    def test_em_dash_in_fallback_text_becomes_a_separator_not_deleted(self):
        from citation_entry import derive_entry_key
        key = derive_entry_key("University of Wisconsin–Madison")
        self.assertEqual(key, "university-of-wisconsin-madison")

    def test_em_dash_inside_href_host_or_tail_becomes_a_separator_not_deleted(self):
        # host/tail come from the URL itself, not the display text --
        # exercised directly since no href in the real corpus happens
        # to contain a literal (unencoded) dash character (confirmed by
        # a direct corpus scan 2026-07-29), so this path isn't hit by
        # any real, already-committed data today, but it is real,
        # reachable code (slugify(f"{host}-{tail}")) that must not
        # regress.
        from citation_entry import derive_entry_key
        key = derive_entry_key("irrelevant display text", href="https://example.com/wisconsin–madison")
        self.assertEqual(key, "example-wisconsin-madison")

    def test_leading_digit_prefix_is_preserved_through_derive_entry_key(self):
        # The "starts with a digit -> s- prefix" rule exists so a slug
        # is always a valid XML NCName (used as xml:id) -- this must
        # keep working through derive_entry_key(), not just through
        # slugify() in isolation, since derive_entry_key()'s result is
        # what actually becomes write_biblioentry()'s xml:id and file
        # name.
        from citation_entry import derive_entry_key
        key = derive_entry_key("2020 Annual Report")
        self.assertEqual(key, "s-2020-annual-report")
```

- [ ] **Step 4: Run and confirm RED**

```bash
python3 -m unittest scripts.tests.test_convert_to_docbook.TestSlugifyAndTitle scripts.tests.test_convert_to_docbook.TestSplitIntoFragments scripts.tests.test_citation_entry.TestDeriveEntryKey -v 2>&1 | tail -40
```

Expected: the 4 new `TestSlugifyAndTitle` tests, the 1 new `TestSplitIntoFragments` test, and the 3 new `TestDeriveEntryKey` tests all FAIL; the 3 pre-existing `TestSlugifyAndTitle` tests and 4 pre-existing `TestDeriveEntryKey` tests still PASS (nothing has been implemented yet — this run is entirely against the untouched old `slugify()`).

Apply **systematic-debugging** before writing the fix — confirm this is genuinely the deletion-not-substitution behavior, not something else:

```bash
python3 -c "
import re
text = 'university of wisconsin–madison'
text = re.sub(r'[^\w\s-]', '', text)
print(repr(text))  # expect 'university of wisconsinmadison' -- dash gone, no separator left behind
text = re.sub(r'\s+', '-', text)
print(repr(text))  # expect 'university-of-wisconsinmadison' -- confirms the jam, not a partial fix
"
```

Expected: `'university of wisconsinmadison'` then `'university-of-wisconsinmadison'` — confirms the two words are already jammed *before* the whitespace-collapse step even runs; the dash contributed nothing to word separation at any point.

- [ ] **Step 5: Write the minimal implementation**

In `scripts/convert_to_docbook.py`, add the import near the top (after `from xml.sax.saxutils import escape as xml_escape`):

```python
from slugify import slugify as _slugify
```

Replace the existing `slugify()` function body:

```python
def slugify(text):
    """URL/file-path/XML-id-safe slug: lowercase, hyphen-separated,
    unicode-transliterated (python-slugify: converts a dash or other
    punctuation to a "-" separator rather than deleting it outright,
    fixing a real, already-committed word-jamming defect --
    "Wisconsin–Madison" used to become "wisconsinmadison", not
    "wisconsin-madison", because Python's unicode-aware \\w/\\s don't
    match an em/en dash and it isn't a literal "-" either, so the old
    hand-rolled regex deleted it with nothing left to mark the word
    boundary). Two project-specific rules python-slugify has no
    opinion about are kept on top of it: an empty result falls back to
    the literal string "s", and a result starting with a digit gets an
    "s-" prefix (both callers rely on the result being non-empty and
    being a valid XML NCName, since it is used as an xml:id)."""
    text = _slugify(text)
    if not text:
        return "s"
    if re.match(r"^[0-9]", text):
        text = f"s-{text}"
    return text
```

- [ ] **Step 6: Run and confirm GREEN**

```bash
python3 -m unittest scripts.tests.test_convert_to_docbook.TestSlugifyAndTitle scripts.tests.test_convert_to_docbook.TestSplitIntoFragments scripts.tests.test_citation_entry.TestDeriveEntryKey -v 2>&1 | tail -40
```

Expected: all tests PASS (the 3+4 pre-existing ones and the 4+1+3 new ones — 15 total across these three classes).

Apply **systematic-debugging** before moving on — confirm this passed for the *right* reason (the library's separator substitution), not by accident:

```bash
python3 -c "
import sys; sys.path.insert(0, 'scripts')
from convert_to_docbook import _slugify
print(repr(_slugify('wisconsin–madison')))
"
```

Expected: `'wisconsin-madison'` — confirms `python-slugify` itself substitutes a separator for the dash (the actual mechanism), not e.g. a coincidental whitespace-collapse side effect that happened to work for this one input but wouldn't generalize.

- [ ] **Step 7: Re-run the full `TestSlugifyAndTitle`/`TestDeriveEntryKey` classes to confirm zero regressions in the pre-existing tests**

```bash
python3 -m unittest scripts.tests.test_convert_to_docbook.TestSlugifyAndTitle scripts.tests.test_citation_entry.TestDeriveEntryKey -v 2>&1 | tail -20
```

Expected: `test_slugify_basic`, `test_slugify_leading_digit_gets_prefixed`, `test_slugify_empty_string`, `test_derives_key_from_url_host_and_tail`, `test_falls_back_to_slugified_text_without_href`, `test_key_length_is_capped`, `test_falls_back_to_slugified_text_when_href_has_no_recognized_scheme` all still PASS, unmodified.

- [ ] **Step 8: Commit**

```bash
cd /home/metavacua/legal-theory/.worktrees/claude/fixes/slugify
git add .gitignore scripts/convert_to_docbook.py scripts/tests/test_convert_to_docbook.py scripts/tests/test_citation_entry.py scripts/tests/fixtures/em_dash_title_section.md
git commit -m "$(cat <<'EOF'
fix: replace hand-rolled slugify() with python-slugify -- em/en dashes were being deleted, not converted to separators

re.sub(r"[^\w\s-]", "", text) silently deleted any em/en dash (they
match neither unicode-aware \w nor \s nor literal "-"), jamming
adjacent words together with no separator at all whenever the dash
had no surrounding whitespace to fall back on ("Wisconsin–Madison" ->
"wisconsinmadison", not "wisconsin-madison"). Confirmed real,
already-committed impact: 11 fragment filenames across 6 corpus
documents are jammed this way today, from real prior runs of this
same function (e.g. "...Duality—A..." -> "...dualitya...").

python-slugify converts the separator correctly, plus collapses
repeated separators and strips leading/trailing ones -- neither of
which the old implementation did either. This project's own two
rules (empty-result -> "s", digit-leading result -> "s-" prefix, both
needed because the result is used as an XML xml:id) are kept, applied
on top of the library's output.

Installed via both a dedicated .venv-slugify/ (following
scripts/eyecite_classify.py's precedent) and system-wide via apt
(python3-slugify) -- unlike eyecite, convert_to_docbook.py is
imported transitively by nearly every script and by most of the
existing test suite, so a venv-only guarded import would have broken
bare `python3` for all of it; confirmed apt's 4.0.0-2 and pip's 8.0.4
produce byte-identical output on every case this fix's tests exercise.

Plan: .superpowers/sdd/2026-07-29-slugify-python-slugify-migration.md

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: Real-corpus verification and full-suite gate

**Files:** none (verification only — no source changes).

- [ ] **Step 1: Re-derive the slug for the two real titles, before/after, and record the exact strings**

```bash
python3 -c "
import sys; sys.path.insert(0, 'scripts')
from convert_to_docbook import slugify

# 'before' values recomputed from the OLD regex directly (not by
# reverting the fix) -- this is the exact transformation the old code
# applied, run standalone so both values are visible in one place.
import re
def old_slugify(text):
    text = text.strip().lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'\s+', '-', text)
    if not text:
        return 's'
    if re.match(r'^[0-9]', text):
        text = f's-{text}'
    return text

titles = [
    'University of Wisconsin–Madison',
    'Conclusion: Reconciling the Duality—A Spectrum of Intent and Context',
]
for t in titles:
    print(repr(t))
    print('  before:', repr(old_slugify(t)))
    print('  after: ', repr(slugify(t)))
"
```

Expected (record these exact strings in the final report):
- `'University of Wisconsin–Madison'` — before: `'university-of-wisconsinmadison'`, after: `'university-of-wisconsin-madison'`
- `'Conclusion: Reconciling the Duality—A Spectrum of Intent and Context'` — before: `'conclusion-reconciling-the-dualitya-spectrum-of-intent-and-context'`, after: `'conclusion-reconciling-the-duality-a-spectrum-of-intent-and-context'`

- [ ] **Step 2: Confirm `derive_identifier()` is genuinely untouched (Research Finding 7), not just assumed**

```bash
python3 -m unittest scripts.tests.test_convert_to_docbook.TestWriteMetadataDcterms.test_derive_identifier_is_a_github_blob_url -v
```

Expected: `OK` — unmodified test, unmodified function, passing for the same reason it did before this fix (it never called `slugify()`).

- [ ] **Step 3: Full suite, bare `python3` (the mandate's own final gate)**

```bash
python3 -m unittest discover -s scripts/tests -p "test_*.py" 2>&1 | tail -15
```

Expected: `OK (skipped=8)` — same skip count as the pre-fix baseline (the 8 skips are pre-existing, eyecite-only; nothing about this fix adds or removes a skip, since no guard was added).

- [ ] **Step 4: Full suite, `.venv-slugify/bin/python3` (confirms the dedicated venv path also fully works, per the literal instruction)**

```bash
.venv-slugify/bin/python3 -m unittest discover -s scripts/tests -p "test_*.py" 2>&1 | tail -15
```

Expected: `OK (skipped=8)` — identical result via the second interpreter (the venv doesn't have `eyecite` either, so the same 8 pre-existing skips are expected here too).

---

## Self-Review

**Spec coverage:**
- "deletes em/en-dashes outright instead of converting them to a separator" → Task 2 Steps 2–3 (`test_slugify_converts_em_dash_to_separator_not_deletion` ×2, `test_em_dash_in_fallback_text_becomes_a_separator_not_deleted`, `test_em_dash_inside_href_host_or_tail_becomes_a_separator_not_deleted`, `test_em_dash_title_produces_hyphenated_not_jammed_fragment_slug`).
- "doesn't collapse repeated separators or strip leading/trailing ones" → Task 2 Step 2 (`test_slugify_collapses_repeated_separators`, `test_slugify_strips_leading_and_trailing_separators`).
- "install python-slugify into a dedicated venv, follow the exact eyecite_classify.py precedent" → Task 1 Step 1 (venv created exactly per precedent); Global Constraints section reasons explicitly about the one deviation (also apt-installed) rather than silently picking one path.
- "preserving its existing signature/contract... grep for every call site and confirm each still works correctly" → Research Finding 6 (all 4 call sites enumerated), Task 2 Steps 2–3 (each call site directly tested), Task 2 Step 7 (pre-existing tests re-run unmodified).
- "especially derive_identifier()... leading-digit-prefixing behavior... must be preserved" → Research Finding 7 (`derive_identifier()` confirmed to never call `slugify()` at all — a finding, not an assumption); Task 3 Step 2 (its existing test re-run as a regression check); leading-digit prefix specifically re-verified through `derive_entry_key()` in Task 2 Step 3 (`test_leading_digit_prefix_is_preserved_through_derive_entry_key`) and through `slugify()` itself via the pre-existing, unmodified `test_slugify_leading_digit_gets_prefixed`.
- "re-derive the slug for the two real titles noted above and confirm they no longer word-jam (report exact before/after strings)" → Task 3 Step 1, and both titles are also pinned as permanent regression tests in Task 2 Step 2, not just a one-off manual check.

**Placeholder scan:** none found — every step has real, complete code, a real fixture, or an exact runnable command with a computed (not guessed) expected result.

**Type consistency:** `slugify(text) -> str` unchanged; `derive_entry_key(text, href=None) -> str` unchanged (still `[:80]`-capped, still returns whatever `slugify()` returns for the branch taken); no caller's code is modified by this plan, only `slugify()`'s internals and test files.

**Not in scope (flag explicitly, do not fix here):**
- Re-running `convert_to_docbook.py`/`convert_numbered_citations.py` against the real corpus to regenerate the 11 already-jammed fragment filenames (and any other file whose slug would change once un-jammed) — this plan fixes the function; re-converting already-committed documents is a separate, much larger, corpus-wide operation (touching file names other code may already reference) that the task brief did not ask for and this plan does not attempt.
- The 164/165 works-cited entries whose *display text* contains a dash but whose derived key currently comes from `derive_entry_key()`'s href branch (Research Finding 2) — their keys are not currently corrupted (no host/tail in this corpus's real data contains a dash), so there is nothing to re-derive for them specifically; the href-branch code path itself is still directly tested (Task 2 Step 3) since it is real, reachable code regardless of today's specific data.

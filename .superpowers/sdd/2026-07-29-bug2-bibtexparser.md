# Bug 2: bibtexparser-backed BibTeX parsing — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace `scripts/build_bibliography.py`'s hand-rolled `parse_bibtex`/`_BIB_ENTRY_START_RE`/`_BIB_FIELD_NAME_RE`/`_read_balanced` BibTeX parsing with the standard `bibtexparser` package, fixing three confirmed defects (silently dropped quoted-value fields, silently dropped bare/unquoted-value fields, silently truncated `#`-concatenated values) while preserving `parse_bibtex()`'s exact existing return shape (`[{"key": str, "entry_type": str, "fields": dict[str, str]}, ...]`) for its callers (`classify_bib_entry`, `main()`).

**Architecture:** `bibtexparser.loads()` replaces the hand-rolled entry/field tokenization only. This project's own display-formatting post-processing (`_strip_inner_braces`, `_normalize_ws` — stripping protective-capitalization braces and collapsing whitespace, a project policy choice, not something a generic parser should have an opinion about) is kept and reapplied to every field value bibtexparser returns, verified byte-for-byte identical to the old output across the real 28-entry `bibliography.bib`.

**Tech Stack:** `bibtexparser` 1.4.x, installed into the same `.venv-eyecite/` venv Bug 1 already created (see Global Constraints for why one shared venv, not a second one).

## Global Constraints

- MUST preserve `parse_bibtex()`'s existing return shape — `classify_bib_entry`/`_format_bib_legal`/`_format_bib_academic`/`main()` all read `entry["key"]`/`entry["entry_type"]`/`entry["fields"][...]` and MUST NOT need to change.
- MUST install bibtexparser via a venv (not `pip install --break-system-packages`), following the same precedent as `scripts/eyecite_classify.py` and Bug 1.
- **Venv reuse, not a second venv:** installed into the SAME `.venv-eyecite/` venv Bug 1 already created, not a new `.venv-bibtexparser/`. Reasoned explicitly here because it deviates from a literal "new dependency, new venv" reading: `main()` calls both `classify_and_format` (needs eyecite) and `parse_bibtex` (needs bibtexparser) in the same process, in the same run — one Python interpreter must have both installed for `python3 scripts/build_bibliography.py` to ever work end-to-end again. Two separate, mutually exclusive venvs cannot satisfy that; extending the one that already exists is the only design that leaves the script runnable at all after both bugs are fixed. The venv keeps its existing name (least disruptive — nothing else needs to change).
- MUST NOT let `import build_bibliography` raise under bare `python3` (no bibtexparser) — same reasoning as Bug 1: dozens of unrelated tests in `test_build_bibliography.py` must keep passing bare.
- `bibtexparser`'s own default (`ignore_nonstandard_types=True`) MUST be overridden (`ignore_nonstandard_types=False`) — confirmed below it otherwise silently drops this corpus's own real `@online{...}` entry, which would be a worse regression than either of the two bugs this task targets.
- Every new/changed test that transitively calls `parse_bibtex` MUST be gated with `@unittest.skipUnless(BIBTEXPARSER_AVAILABLE, BIBTEXPARSER_SKIP_REASON)` — a separate, independent flag from Bug 1's `EYECITE_AVAILABLE` (both packages happen to live in the same venv, but the two fixes are independent; a future environment could plausibly have one without the other, and the skip message should name the right missing package).
- ONE commit for this entire bug fix (this repo's convention for this task: two commits total across both bugs, this is the second).

---

## Research findings that drive this design (verified 2026-07-29, do not re-derive)

1. **Confirmed root cause, side-by-side, on a deliberately tricky but 100%-legal fixture** (`@article{quoted2020, author = "Quoted, Author", title = "A Quoted Title", year = 2020, journal = {Journal of Testing}}` plus a `#`-concatenated title and a bare-year entry): the OLD hand-rolled parser returns `{'journal': 'Journal of Testing'}` for `quoted2020` — silently dropping `author`, `title`, and `year` entirely, because `_BIB_FIELD_NAME_RE` requires every value to start with a literal `{`. It returns `title: 'Part One'` for the `#`-concatenated entry (should be `'Part One, and Part Two'`) — silently truncated at the first closing brace, no knowledge of `#` at all. It returns `{'title': 'Bare Year Field'}` for the bare-year entry — `year` silently dropped. `bibtexparser` (default settings) gets all three exactly right.
2. **`bibtexparser`'s own default silently drops an entire real entry from this corpus's actual `bibliography.bib`.** `bibtexparser.load()` with default settings parses only 27 of the file's 28 entries, printing `Entry type online not standard. Not considered.` — the `@online{hay2024video, ...}` entry (a real, currently-preserved citation) vanishes silently. Root cause: `BibTexParser.__init__`'s `ignore_nonstandard_types` defaults to `True`. Setting it `False` recovers all 28 entries, `hay2024video` included, confirmed directly.
3. **With `ignore_nonstandard_types=False` plus reapplying the existing `_strip_inner_braces`/`_normalize_ws` to every field value, the new parser's output is byte-for-byte identical to the old parser's, entry-by-entry and field-by-field, across all 28 real entries in `bibliography.bib`** (verified via a direct diff script: 0 differences, 0 keys only-in-old, 0 keys only-in-new). Also verified identical against the existing `sample.bib` test fixture (used by `TestParseBibtex`), confirming all 3 existing unit tests continue to pass unmodified.
4. **Field names and entry types are already lowercased by `bibtexparser` by default** (confirmed against a mixed-case fixture: `Author`/`TITLE`/`Year` → `author`/`title`/`year`, `Article` → `'article'`), matching the old code's explicit `.lower()` calls — no extra normalization needed on that front.
5. **`bibtexparser.loads(text, parser=parser)` (string-based) works identically to `bibtexparser.load(file_handle, parser=parser)`** — chosen over `load()` because it lets `parse_bibtex` keep its exact existing opening line, `Path(path).read_text(encoding="utf-8")` (same UTF-8 handling, same natural `FileNotFoundError` on a missing path as today).
6. **`_read_balanced`, `_BIB_ENTRY_START_RE`, `_BIB_FIELD_NAME_RE` have no callers anywhere else in the codebase** (confirmed via `grep -rn` across `scripts/`) — safe to delete outright once `parse_bibtex` no longer uses them. `_strip_inner_braces` is reused and kept.
7. **`classify_bib_entry`/`_format_bib_legal`/`_format_bib_academic` need zero changes** — they only ever read `entry["fields"].get(...)`, and the new parser's field set/values are confirmed identical to the old one for real data (finding 3).

---

## File Structure

- Modify: `scripts/build_bibliography.py` — guarded `bibtexparser` import (alongside Bug 1's `eyecite` guard), `parse_bibtex`; deletes `_BIB_ENTRY_START_RE`, `_BIB_FIELD_NAME_RE`, `_read_balanced` (fully superseded, confirmed no other caller).
- Modify: `scripts/tests/test_build_bibliography.py` — new/updated tests, `BIBTEXPARSER_AVAILABLE` skip-guard infrastructure, a new tricky-but-legal `.bib` fixture.
- Create: `scripts/tests/fixtures/bibliography/tricky.bib` — the quoted/bare/`#`-concatenated fixture from finding 1, as a permanent, reusable test fixture (not a scratch file).

---

## Task 1: bibtexparser install + guarded import + test skip-infrastructure

**Files:**
- Modify: `scripts/build_bibliography.py` (import block near the top, alongside Bug 1's eyecite guard)
- Modify: `scripts/tests/test_build_bibliography.py:1-20` (module-level imports)

**Interfaces:**
- Produces: `build_bibliography._BIBTEXPARSER_AVAILABLE` (bool), `build_bibliography._require_bibtexparser()` (raises `RuntimeError` if unavailable, else no-op) — used by this plan's Task 2.
- Produces (test file): `BIBTEXPARSER_AVAILABLE` (bool), `BIBTEXPARSER_SKIP_REASON` (str) — used by Task 2/3's tests.

- [ ] **Step 1: Install bibtexparser into the existing `.venv-eyecite/` venv**

```bash
cd /home/metavacua/legal-theory/.worktrees/claude/fixes/eyecite-bibtex
.venv-eyecite/bin/pip install --quiet bibtexparser
.venv-eyecite/bin/python3 -c "import bibtexparser; print('OK')"
```

Expected: `OK`. No `.gitignore` change needed — `.venv-eyecite/` is already gitignored (from Bug 1).

- [ ] **Step 2: Add the guarded import + `_require_bibtexparser()` helper to `build_bibliography.py`**

Insert immediately after Bug 1's eyecite `try`/`except` block (right before `_EYECITE_REQUIRED_MSG = (...)`):

```python
# bibtexparser has no apt package either -- installed into the same
# .venv-eyecite/ venv as eyecite (see that block above for why one
# shared venv, not a second one: main() needs both in the same
# process). Guarded the same way, for the same reason: `import
# build_bibliography` must not fail under bare python3, and
# parse_bibtex raises a clear RuntimeError if actually called without
# it rather than silently degrading.
try:
    import bibtexparser
    from bibtexparser.bparser import BibTexParser
    _BIBTEXPARSER_AVAILABLE = True
except ImportError:
    _BIBTEXPARSER_AVAILABLE = False

_BIBTEXPARSER_REQUIRED_MSG = (
    "bibtexparser is required for BibTeX parsing and is not installed "
    "under this interpreter. Run this script/test via "
    ".venv-eyecite/bin/python3 (create it once with: python3 -m venv "
    ".venv-eyecite && .venv-eyecite/bin/pip install --quiet eyecite "
    "bibtexparser)."
)


def _require_bibtexparser():
    if not _BIBTEXPARSER_AVAILABLE:
        raise RuntimeError(_BIBTEXPARSER_REQUIRED_MSG)
```

- [ ] **Step 3: Add the same skip-detection precedent to the test file**

In `scripts/tests/test_build_bibliography.py`, immediately after Bug 1's `EYECITE_AVAILABLE`/`SKIP_REASON` block, add:

```python
try:
    import bibtexparser  # noqa: F401
    BIBTEXPARSER_AVAILABLE = True
except ImportError:
    BIBTEXPARSER_AVAILABLE = False

BIBTEXPARSER_SKIP_REASON = (
    "bibtexparser is not installed under this interpreter -- it lives "
    "only in the dedicated .venv-eyecite/ virtualenv (shared with "
    "eyecite), not the bare system python3 every other script/test in "
    "this repo runs under. Run this test file with "
    ".venv-eyecite/bin/python3 to exercise it."
)
```

- [ ] **Step 4: Verify nothing is broken yet**

```bash
cd /home/metavacua/legal-theory/.worktrees/claude/fixes/eyecite-bibtex
python3 -m unittest scripts.tests.test_build_bibliography -v 2>&1 | tail -5
.venv-eyecite/bin/python3 -m unittest scripts.tests.test_build_bibliography -v 2>&1 | tail -5
```

Expected: both `OK` (nothing about `parse_bibtex`'s *implementation* has changed yet, only imports/infrastructure) — bare `python3` unchanged from Bug 1's end state (34 skips in this file), `.venv-eyecite` still 0 skips, 0 failures.

---

## Task 2: `parse_bibtex` — bibtexparser backing

**Files:**
- Create: `scripts/tests/fixtures/bibliography/tricky.bib`
- Modify: `scripts/build_bibliography.py:479-530` (`_BIB_ENTRY_START_RE` through the end of `parse_bibtex`)
- Test: `scripts/tests/test_build_bibliography.py` (`TestParseBibtex`)

**Interfaces:**
- Consumes: `_require_bibtexparser()`, `bibtexparser`, `BibTexParser` (Task 1); `_strip_inner_braces`, `_normalize_ws` (pre-existing, unchanged).
- Produces: `parse_bibtex(path) -> [{"key": str, "entry_type": str, "fields": dict[str, str]}, ...]` — identical shape to before, consumed unchanged by `classify_bib_entry`/`main()`.

- [ ] **Step 1: Create the tricky-but-legal fixture**

Create `scripts/tests/fixtures/bibliography/tricky.bib`:

```bibtex
@article{quoted2020,
  author = "Quoted, Author",
  title  = "A Quoted Title",
  year   = 2020,
  journal = {Journal of Testing}
}

@misc{concat2021,
  title  = {Part One} # {, and Part Two},
  author = {Concat, Author},
  year   = {2021}
}

@misc{bareyear2022,
  title = {Bare Year Field},
  year  = 2022
}

@online{online2023,
  title = {A Nonstandard Entry Type},
  year  = {2023}
}
```

Four entries, each pinning one confirmed bug: `quoted2020` (quoted values silently dropped), `concat2021` (`#`-concatenation silently truncated), `bareyear2022` (bare/unquoted value silently dropped), `online2023` (bibtexparser's *own* default silently drops nonstandard entry types -- confirmed 2026-07-29 this is a real trap the fix itself must not fall into, since this corpus's actual `bibliography.bib` has a real `@online{hay2024video, ...}` entry).

- [ ] **Step 2: Write the failing tests**

Add to `TestParseBibtex` (after the existing `test_no_author_field_is_simply_absent_not_fabricated`):

```python
    def test_quoted_field_values_are_not_silently_dropped(self):
        """Confirmed 2026-07-29 root cause: the old _BIB_FIELD_NAME_RE
        required every value to start with a literal "{", so a
        quote-delimited field ("...") was silently omitted from the
        parsed entry's fields dict entirely -- not an error, not a
        placeholder, just gone."""
        from build_bibliography import parse_bibtex
        entries = parse_bibtex(FIXTURES / "tricky.bib")
        by_key = {e["key"]: e for e in entries}
        fields = by_key["quoted2020"]["fields"]
        self.assertEqual(fields["author"], "Quoted, Author")
        self.assertEqual(fields["title"], "A Quoted Title")
        self.assertEqual(fields["year"], "2020")
        self.assertEqual(fields["journal"], "Journal of Testing")

    def test_bare_unquoted_field_value_is_not_silently_dropped(self):
        from build_bibliography import parse_bibtex
        entries = parse_bibtex(FIXTURES / "tricky.bib")
        by_key = {e["key"]: e for e in entries}
        fields = by_key["bareyear2022"]["fields"]
        self.assertEqual(fields["year"], "2022")
        self.assertEqual(fields["title"], "Bare Year Field")

    def test_hash_concatenated_value_is_not_silently_truncated(self):
        from build_bibliography import parse_bibtex
        entries = parse_bibtex(FIXTURES / "tricky.bib")
        by_key = {e["key"]: e for e in entries}
        self.assertEqual(by_key["concat2021"]["fields"]["title"], "Part One, and Part Two")

    def test_nonstandard_entry_type_is_not_silently_dropped(self):
        """Guards against a DIFFERENT silent-drop trap this fix must not
        introduce: bibtexparser's own default (ignore_nonstandard_types=
        True) silently drops the whole entry for any @type it doesn't
        recognize as classic BibTeX -- confirmed 2026-07-29 this would
        have dropped this project's own real bibliography.bib entry
        @online{hay2024video, ...}."""
        from build_bibliography import parse_bibtex
        entries = parse_bibtex(FIXTURES / "tricky.bib")
        keys = {e["key"] for e in entries}
        self.assertIn("online2023", keys)
        by_key = {e["key"]: e for e in entries}
        self.assertEqual(by_key["online2023"]["entry_type"], "online")

    def test_tricky_fixture_loses_no_entries(self):
        from build_bibliography import parse_bibtex
        entries = parse_bibtex(FIXTURES / "tricky.bib")
        self.assertEqual(len(entries), 4)
```

- [ ] **Step 3: Run and confirm RED**

```bash
.venv-eyecite/bin/python3 -m unittest scripts.tests.test_build_bibliography.TestParseBibtex -v
```

Expected: the 5 new tests FAIL. Apply **systematic-debugging** before writing the fix: confirm this is genuinely `_BIB_FIELD_NAME_RE`'s literal-`{`-only requirement, not something else --

```bash
python3 -c "
import re
_BIB_FIELD_NAME_RE = re.compile(r'(?P<name>\w+)\s*=\s*\{')
print(_BIB_FIELD_NAME_RE.findall('author = \"Quoted, Author\",\n  year = 2020,'))
"
```

Expected: `[]` (empty -- confirms the regex never matches either quoted or bare values, they are structurally invisible to it, not merely mis-parsed).

- [ ] **Step 4: Write the minimal implementation**

Replace lines 479–530 (`_BIB_ENTRY_START_RE` through the end of `parse_bibtex`) with:

```python
def _strip_inner_braces(value):
    return re.sub(r"[{}]", "", value)


def parse_bibtex(path):
    """[{"key": str, "entry_type": str, "fields": dict[str, str]}, ...]
    for every @type{key, ...} entry in a BibTeX file.

    Uses bibtexparser rather than hand-rolled parsing -- confirmed
    2026-07-29 the old hand-rolled field regex (which required every
    value to start with a literal "{") silently dropped any field
    written as "..." (quoted) or bare/unquoted (e.g. a bare "year =
    2020"), and silently truncated "#"-concatenated values at the first
    closing brace. ignore_nonstandard_types=False is required:
    bibtexparser's own default (True) silently drops entire entries
    whose @type isn't one of a fixed classic-BibTeX list -- confirmed
    this would otherwise drop this project's own bibliography.bib's
    real @online{hay2024video, ...} entry, which is exactly the kind of
    silent data loss this replacement must not introduce.

    Field values are still run through _strip_inner_braces/_normalize_ws
    exactly as before -- that post-processing is this project's own
    display-formatting policy (strip protective-capitalization braces,
    collapse whitespace), not something a generic parser should have an
    opinion about, and is confirmed to produce byte-for-byte identical
    output to the old parser, entry-by-entry and field-by-field, across
    the real 28-entry bibliography.bib.
    """
    text = Path(path).read_text(encoding="utf-8")
    parser = BibTexParser(ignore_nonstandard_types=False)
    db = bibtexparser.loads(text, parser=parser)
    entries = []
    for raw in db.entries:
        raw = dict(raw)
        key = raw.pop("ID")
        entry_type = raw.pop("ENTRYTYPE")
        fields = {}
        for name, value in raw.items():
            cleaned = _normalize_ws(_strip_inner_braces(value))
            if cleaned:
                fields[name] = cleaned
        entries.append({"key": key, "entry_type": entry_type, "fields": fields})
    return entries
```

Note `_strip_inner_braces` is repeated verbatim in this diff purely to show it stays put (unchanged) immediately above the rewritten `parse_bibtex` -- do not duplicate the function, just leave the existing one where it is and replace everything from `_BIB_ENTRY_START_RE` down to (but not including) `_strip_inner_braces` with nothing, then replace `def parse_bibtex(path):` through its old closing `return entries` with the new body above. Also add `_require_bibtexparser()` as the new function's first line, immediately after the `Path(path).read_text(...)` call:

```python
    text = Path(path).read_text(encoding="utf-8")
    _require_bibtexparser()
    parser = BibTexParser(ignore_nonstandard_types=False)
```

- [ ] **Step 5: Add the class-level skip guard**

Decorate `TestParseBibtex`:

```python
@unittest.skipUnless(BIBTEXPARSER_AVAILABLE, BIBTEXPARSER_SKIP_REASON)
class TestParseBibtex(unittest.TestCase):
```

- [ ] **Step 6: Run and confirm ALL of TestParseBibtex is GREEN**

```bash
.venv-eyecite/bin/python3 -m unittest scripts.tests.test_build_bibliography.TestParseBibtex -v
```

Expected: 8/8 pass (3 pre-existing + 5 new).

Apply **systematic-debugging**: confirm `test_nonstandard_entry_type_is_not_silently_dropped` passes *because* of `ignore_nonstandard_types=False`, not by accident -- temporarily change it to `True` (or drop the kwarg) and re-run just that test; it must go RED (`AssertionError` on `assertIn("online2023", keys)`). Revert and confirm GREEN again. Also re-run `test_parses_both_entries_with_correct_types_and_keys`/`test_field_with_nested_braces_extracted_without_the_braces`/`test_no_author_field_is_simply_absent_not_fabricated` (the 3 pre-existing tests) specifically and confirm they still pass for the same reason as before (real `sample.bib` output unchanged) -- not merely "still green" but green via the same brace-stripping/absent-field logic, by spot-checking `parse_bibtex(FIXTURES / "sample.bib")`'s printed output matches finding 3 above exactly.

- [ ] **Step 7: Verify under bare `python3` too**

```bash
python3 -m unittest scripts.tests.test_build_bibliography.TestParseBibtex -v
```

Expected: `OK (skipped=8)` -- the whole class skips cleanly (no failures, no errors), confirming the guard from Step 5 works and `import build_bibliography` still succeeds bare.

---

## Task 3: Guard the remaining bibtexparser-dependent test

**Files:**
- Modify: `scripts/tests/test_build_bibliography.py` (`TestEndToEndIntegration`)

**Interfaces:**
- Consumes: `BIBTEXPARSER_AVAILABLE`, `BIBTEXPARSER_SKIP_REASON` (Task 1).

Exactly one remaining test transitively depends on `parse_bibtex`, confirmed by direct inspection of `TestEndToEndIntegration`'s two methods: `test_full_pipeline_produces_valid_docbook_with_all_four_buckets` imports `parse_bibtex`/`classify_bib_entry` names but never calls either in its body (it only exercises `extract_all_raw_entries`/`classify_and_format`/`dedupe`/`verify_invariants`/`emit_docbook` against the `integration_corpus` fixture) -- it needs no new guard. `test_real_bibliography_bib_parses_and_classifies_without_exceptions` calls `parse_bibtex(bib_path)` directly against the real file -- it does.

- [ ] **Step 1: Apply the method-level guard**

```python
    @unittest.skipUnless(BIBTEXPARSER_AVAILABLE, BIBTEXPARSER_SKIP_REASON)
    def test_real_bibliography_bib_parses_and_classifies_without_exceptions(self):
```

- [ ] **Step 2: Verify under bare `python3` -- everything either passes or skips, nothing errors**

```bash
python3 -m unittest discover -s scripts/tests -p "test_*.py" -v 2>&1 | tail -20
```

Expected: `OK (skipped=N)`, `N` now covering Bug 1's 43 (from that bug's final state) plus this bug's 8 (`TestParseBibtex`) + 1 (this method) = 52; zero failures, zero errors.

- [ ] **Step 3: Verify under `.venv-eyecite/bin/python3` -- everything actually runs and passes**

```bash
.venv-eyecite/bin/python3 -m unittest discover -s scripts/tests -p "test_*.py" -v 2>&1 | tail -20
```

Expected: `OK`, zero skips, zero failures, zero errors -- every line touched by Task 2 actually exercised for real.

---

## Task 4: Real corpus regeneration + verified impact

**Files:** none (verification only -- no source changes).

- [ ] **Step 1: Confirm the real bibliography.bib still parses to exactly 28 entries with the final code**

```bash
cd /home/metavacua/legal-theory/.worktrees/claude/fixes/eyecite-bibtex
.venv-eyecite/bin/python3 -c "
import sys
sys.path.insert(0, 'scripts')
from build_bibliography import parse_bibtex
entries = parse_bibtex('docs/papers/ai_and_ip/llm-database-theory/src/bibliography.bib')
print('entry count:', len(entries))
print('online entry present:', 'hay2024video' in {e[\"key\"] for e in entries})
"
```

Expected: `entry count: 28`, `online entry present: True` -- this project's own corpus is confirmed undamaged (matches the task brief's own observation that `bibliography.bib` "happens to brace-delimit every field today so there is no current corpus damage" -- this step confirms that stays true, and that the fix doesn't newly *introduce* damage via the nonstandard-entry-type trap).

- [ ] **Step 2: Full pipeline regeneration, same caveat as Bug 1 Task 7**

```bash
.venv-eyecite/bin/python3 scripts/build_bibliography.py; echo "exit code: $?"
```

Expected: same pre-existing, out-of-scope `emit_docbook()` validation failure as Bug 1's Task 7 (unrelated to this fix) -- `references.xml` is still written to disk before that check runs. Confirm no NEW error appears (e.g. no bibtexparser-related traceback) -- if `main()`'s only stderr output is the same `VALIDATION FAILED: ... element "title" not allowed here ...` message already seen and documented in Bug 1's plan, this fix introduced no new failure mode.

- [ ] **Step 3: Restore the working tree**

```bash
git status --short  # confirm only docs/bibliography/references*.xml are modified
git checkout -- docs/bibliography/references.xml docs/bibliography/references.meta.xml
git status --short  # confirm clean
```

- [ ] **Step 4: Full suite, one more time, both interpreters (final pre-commit gate)**

```bash
python3 -m unittest discover -s scripts/tests -p "test_*.py" 2>&1 | tail -10
.venv-eyecite/bin/python3 -m unittest discover -s scripts/tests -p "test_*.py" 2>&1 | tail -10
```

Expected: both `OK` (first with the accumulated skip count from both bugs, second with zero).

---

## Self-Review

**Spec coverage:**
- "silently drops fields written as '...' (quoted)" → Task 2 (`test_quoted_field_values_are_not_silently_dropped`).
- "or bare/unquoted values" → Task 2 (`test_bare_unquoted_field_value_is_not_silently_dropped`).
- "silently truncates '#'-concatenated values" → Task 2 (`test_hash_concatenated_value_is_not_silently_truncated`).
- "confirmed via a side-by-side test against ... bibtexparser ... on a deliberately tricky but 100%-legal .bib fixture" → Task 2 Step 1 (the fixture itself) plus the Research Findings section (the actual side-by-side comparison run during planning).
- "install into a venv the same way [as eyecite_classify.py]" → Task 1 (reasoned explicitly in Global Constraints why this means the *same* venv, not a sibling one).
- "This project's own ... bibliography.bib ... happens to brace-delimit every field today so there is no current corpus damage" → Task 4 Step 1 (confirms this remains true, and that the fix doesn't add new damage via the nonstandard-type trap the research uncovered).
- "preserving parse_bibtex()'s existing return shape/contract for its callers" → unchanged in all tasks (`classify_bib_entry`/`_format_bib_legal`/`_format_bib_academic`/`main()` are never edited by this plan; Research Finding 7 confirms why none of them need to be).

**Placeholder scan:** none found -- every step has real, complete code or an exact runnable command with a stated expected result.

**Type consistency:** `parse_bibtex`'s return shape (`{"key", "entry_type", "fields"}`, `fields` a `dict[str, str]`) matches exactly what `classify_bib_entry`/`_format_bib_legal`/`_format_bib_academic`/`main()` already expect -- verified against the actual current call sites (all unmodified, all read directly before writing this plan) and against the byte-for-byte real-corpus comparison (Research Finding 3).

**Not in scope (flag to user, do not fix here):**
- The pre-existing `emit_docbook()` title-duplication defect (see Bug 1's plan) -- still present, still unrelated, still not fixed by this plan either.
- Any BibTeX syntax bibtexparser itself doesn't support (e.g. deeply malformed/unbalanced input) -- not evidenced anywhere in this corpus's real `bibliography.bib`, and not one of the two bugs this task is scoped to fix.

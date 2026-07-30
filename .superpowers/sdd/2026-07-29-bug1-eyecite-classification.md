# Bug 1: eyecite-backed legal-citation classification — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace `scripts/build_bibliography.py`'s hand-rolled `classify_case`/`classify_statute` regex machinery with eyecite-backed extraction, fixing three confirmed defects (Bluebook citation-order blindness, a 9-reporter allowlist, and missed "U.S. Code" statute phrasing) while preserving `classify_and_format()`'s `(section, display_text)` contract and `format_case_bluebook()`/`format_statute_bluebook()`'s output shape.

**Architecture:** `eyecite.get_citations()` replaces the old `_REPORTER_RE`/`_USC_RE` reporter-citation *parsing* only. The `_CASE_RE` case-name pattern and the `CODE_ABBREVIATIONS`/`_STATUTE_RE` California-state-code lookup are kept (verified below that eyecite cannot replace either), and `CASE_LAW_DOMAINS` is expanded with real, verified case-law-aggregator hostnames since eyecite has no URL/domain concept at all. `eyecite` is a hard runtime dependency of `classify_case`/`classify_statute` from now on, imported through a module-level guard so `import build_bibliography` never fails under the bare system `python3` that this repo's other tooling runs under.

**Tech Stack:** Python 3.11 stdlib `re`/`urllib.parse` (unchanged) + `eyecite` (Free Law Project), installed into `.venv-eyecite/` per the existing `scripts/eyecite_classify.py` precedent.

## Global Constraints

- MUST preserve `classify_and_format()`'s existing `(section, display_text)` return contract — callers (`main()`, `verify_invariants()`) are unchanged.
- MUST preserve `format_case_bluebook()`/`format_statute_bluebook()`'s existing output *shape* (same f-string structure); adding a new fallback branch is in-scope, changing the shape of existing branches is not.
- MUST NOT regress California-state-code classification (`CODE_ABBREVIATIONS`/`_STATUTE_RE`) — confirmed below that eyecite cannot parse this corpus's actual raw phrasing for it, so this path is kept unchanged, not replaced.
- MUST install eyecite via a dedicated venv (`.venv-eyecite/`, already `.gitignore`d), not `pip install --break-system-packages` — Debian 12's PEP 668 blocks a bare `pip install` here (confirmed directly), and the task explicitly directs following the `scripts/eyecite_classify.py` precedent.
- MUST NOT let `import build_bibliography` raise under bare `python3` (no eyecite) — `scripts/tests/test_build_bibliography.py` imports it at module level, and dozens of unrelated tests in that file (parse_bibtex, dedupe, emit_docbook, ...) must keep passing bare.
- Every new/changed test that transitively calls `classify_case`/`classify_statute`/`classify_and_format` MUST be gated with `@unittest.skipUnless(EYECITE_AVAILABLE, SKIP_REASON)`, mirroring the existing `scripts/tests/test_eyecite_classify.py` precedent exactly (same variable names).
- ONE commit for this entire bug fix (this repo's convention for this task: "two separate...commits" total across both bugs, not one per task).

---

## Research findings that drive this design (verified 2026-07-29, do not re-derive)

1. **`Marvin v. Marvin (1976) 18 Cal. 3d 660`** (the one existing California-order test case) and **`Marbury v. Madison, 5 U.S. 137 (1803)`** (standard Bluebook order) **both parse correctly via `eyecite.get_citations()`** — eyecite is robust to both orders; the bug is entirely in the old hand-rolled `_REPORTER_RE`, which only matched the California order.
2. **eyecite does NOT capture a *leading* parenthetical year as `metadata.year`.** `get_citations("(1976) 18 Cal. 3d 660")[0].metadata.year` is `None`. The California-order case's year must be captured separately, from the same leading `(YYYY)` this code strips before calling eyecite.
3. **eyecite cannot parse this corpus's actual raw California-code phrasing.** `get_citations("California Civil Code § 1550 (2024) - Justia Law")` → bare `UnknownCitation('§')`, not a `FullLawCitation`. Only the already-abbreviated form (`"Cal. Civ. Code § 1550 (2024)"`) resolves, and even then `corrected_citation()` is unreliable for it (drops the `Civ.`/`Corp.` subject: `"Cal. Civ. Code § 1550"` → `corrected_citation()` gives `"Cal. Code § 1550"`, not `"Cal. Civ. Code § 1550"`). `CODE_ABBREVIATIONS`/`_STATUTE_RE` must be kept for this path — it already handles both phrasings the corpus actually uses (its keys include both `"civil code"` and `"civ. code"`).
4. **eyecite DOES resolve both `"17 U.S.C. § 512(c)"` and `"17 U.S. Code § 101 - ..."`** as `FullLawCitation`, with `groups["reporter"]` `"U.S.C."` or `"U.S. Code"` respectively — this is the confirmed bug fix. `corrected_citation()` is reliable here (`"17 U.S.C. § 101"`), unlike the California-code case, but this plan constructs the abbreviation manually from `groups`/`metadata` anyway, for one uniform, predictable code path.
5. **eyecite drops the second section number in a `"§§ 101, 106"` list**: `get_citations("17 U.S.C. §§ 101, 106")[0].groups["section"] == "101"`, not `"101, 106"`. The existing test `test_multi_section_usc_citation_not_truncated` requires the full string — a small supplemental regex (digits-only, to avoid over-consuming trailing prose) recovers it.
6. **Direct corpus measurement (`scripts/build_bibliography.py`'s own functions, run against the real corpus):** 396 raw works-cited entries contain `" v. "`; 356 of those are currently misfiled as `"secondary"`. Of those 356, only **6** have an immediately-recoverable reporter citation eyecite would find (i.e., only 6 are fixed by the reporter-order/allowlist fix alone). The other 350 have no citation anywhere in their raw text at all — recoverable, if at all, only via domain corroboration. A conservative, evidence-based expansion of `CASE_LAW_DOMAINS` (real hostnames actually used by this corpus's case-law-specific archives — Oyez, Justia's Supreme Court subdomain, FindLaw's case-law subdomains, Cornell LII, Stanford's CA Supreme Court archive, official federal/SCOTUS court sites, case-brief study sites) projects to recovering **132** more. Deliberately excluded: `en.wikipedia.org` (63), `www.britannica.com` (10), `www.ebsco.com` (13), `firstamendment.mtsu.edu` (21), and a long tail of law-firm/advocacy/general-encyclopedia sites — none of these are case-law-*specific* aggregators, and none of the excluded entries carry a recoverable citation either, so leaving them `"secondary"` is the correct, non-fabricating outcome per this project's existing "no fabrication" convention (`format_secondary_chicago`'s `[author unknown]`/`[access date unknown]` markers follow the same principle).
7. **A pre-existing, unrelated, out-of-scope defect exists in `emit_docbook()`**: it unconditionally emits a top-level `<title>` sibling immediately after `<xi:include href="references.meta.xml"/>`, but `references.meta.xml`'s own `<info>` (built by `write_metadata()`) already carries a `<title>`, and DocBook 5.2 does not allow both — `jing` validation fails on every fresh run (confirmed: the currently-committed `docs/bibliography/references.xml` does NOT have this duplicate title, meaning it predates whatever change introduced this regression into `emit_docbook()`; a fresh regeneration reproduces the jing failure on the *unmodified*, pre-this-plan code). This is NOT one of the two bugs this task is scoped to and Task 7 below works around it (the file is still written to disk before `validate()` runs, so the before/after count is still measurable) rather than fixing it. Flag this to the user; do not fix it here.

---

## File Structure

- Modify: `scripts/build_bibliography.py` — guarded eyecite import, `classify_statute`, `classify_case`, `format_case_bluebook`, `CASE_LAW_DOMAINS`; deletes `_REPORTER_RE`, `_REPORTER_ABBREVS`, `_USC_RE` (fully superseded, confirmed no other caller — `grep -n` for each name only shows their own definitions and use within `classify_case`/`classify_statute`).
- Modify: `scripts/tests/test_build_bibliography.py` — new/updated tests, `EYECITE_AVAILABLE` skip-guard infrastructure.
- Create: `.venv-eyecite/` (gitignored, not committed — already covered by the existing `.gitignore` entry from `scripts/eyecite_classify.py`'s own commit).

---

## Task 1: eyecite venv + guarded import + test skip-infrastructure

**Files:**
- Modify: `scripts/build_bibliography.py:1-18` (module docstring + imports)
- Modify: `scripts/tests/test_build_bibliography.py:1-10` (module-level imports)

**Interfaces:**
- Produces: `build_bibliography._EYECITE_AVAILABLE` (bool), `build_bibliography._require_eyecite()` (raises `RuntimeError` if unavailable, else no-op) — used by Tasks 2–3's `classify_statute`/`classify_case`.
- Produces (test file): `EYECITE_AVAILABLE` (bool), `SKIP_REASON` (str) — used by every later task's new/modified tests.

- [ ] **Step 1: Create the venv and install eyecite (if not already present in this worktree)**

```bash
cd /home/metavacua/legal-theory/.worktrees/claude/fixes/eyecite-bibtex
test -d .venv-eyecite || python3 -m venv .venv-eyecite
.venv-eyecite/bin/pip install --quiet eyecite
.venv-eyecite/bin/python3 -c "import eyecite; print('OK', eyecite.__version__)"
```

Expected: `OK 2.7.8` (or newer). This exactly matches `scripts/eyecite_classify.py`'s own installation precedent (confirmed via `git show a901275:.../2026-07-26-citation-standardization-phase1.md`, Task 2 Step 1).

- [ ] **Step 2: Add the guarded import + `_require_eyecite()` helper to `build_bibliography.py`**

Insert immediately after the existing `from convert_to_docbook import (...)` block (currently ending at line 17):

```python
# eyecite (Free Law Project) has no apt package -- installed into a
# dedicated, gitignored venv at .venv-eyecite/, same precedent as
# scripts/eyecite_classify.py. Guarded so `import build_bibliography`
# never fails under the bare system python3 this repo's other tooling
# and most of this file's own tests run under; classify_case/
# classify_statute raise a clear, actionable RuntimeError if actually
# called without it (see _require_eyecite below) rather than silently
# degrading -- consistent with this codebase's existing no-fabrication
# convention (format_secondary_chicago's "[author unknown]" markers,
# etc.): a missing dependency must be loud, not a silent wrong answer.
try:
    from eyecite import get_citations
    from eyecite.models import FullCaseCitation, FullLawCitation
    _EYECITE_AVAILABLE = True
except ImportError:
    _EYECITE_AVAILABLE = False

_EYECITE_REQUIRED_MSG = (
    "eyecite is required for legal-citation classification and is not "
    "installed under this interpreter. Run this script/test via "
    ".venv-eyecite/bin/python3 (create it once with: python3 -m venv "
    ".venv-eyecite && .venv-eyecite/bin/pip install --quiet eyecite -- "
    "see scripts/eyecite_classify.py for the same precedent)."
)


def _require_eyecite():
    if not _EYECITE_AVAILABLE:
        raise RuntimeError(_EYECITE_REQUIRED_MSG)
```

- [ ] **Step 3: Add the same skip-detection precedent to the test file, and class-level-guard the three wholly-eyecite-dependent test classes**

In `scripts/tests/test_build_bibliography.py`, immediately after the existing `from build_bibliography import REPO_ROOT` line, add:

```python
try:
    import eyecite  # noqa: F401
    EYECITE_AVAILABLE = True
except ImportError:
    EYECITE_AVAILABLE = False

SKIP_REASON = (
    "eyecite is not installed under this interpreter -- it lives only "
    "in the dedicated .venv-eyecite/ virtualenv, not the bare system "
    "python3 every other script/test in this repo runs under. Run this "
    "test file with .venv-eyecite/bin/python3 to exercise it."
)
```

This is verbatim the same pattern `scripts/tests/test_eyecite_classify.py` already uses (confirmed by reading that file directly).

Then decorate these three existing classes (add the line immediately above each `class` statement):

```python
@unittest.skipUnless(EYECITE_AVAILABLE, SKIP_REASON)
class TestClassifyStatute(unittest.TestCase):
```

```python
@unittest.skipUnless(EYECITE_AVAILABLE, SKIP_REASON)
class TestClassifyCase(unittest.TestCase):
```

```python
@unittest.skipUnless(EYECITE_AVAILABLE, SKIP_REASON)
class TestClassifyAndFormat(unittest.TestCase):
```

(Reasoning: every test in these three classes calls `classify_statute`/`classify_case`/`classify_and_format` directly, and `classify_and_format` always tries `classify_statute` first regardless of input shape — so every test in all three classes needs eyecite importable, even ones whose expected outcome doesn't depend on eyecite actually finding anything. Task 6 below handles the remaining, *partially*-dependent classes at the method level.)

- [ ] **Step 4: Verify nothing is broken yet**

```bash
cd /home/metavacua/legal-theory/.worktrees/claude/fixes/eyecite-bibtex
python3 -m unittest scripts.tests.test_build_bibliography -v 2>&1 | tail -20
```

Expected: all tests that were passing before still pass; `TestClassifyStatute`/`TestClassifyCase`/`TestClassifyAndFormat` now report `skipped` (bare `python3` has no eyecite yet in its own site-packages — only `.venv-eyecite` does). Zero failures, zero errors.

```bash
.venv-eyecite/bin/python3 -m unittest scripts.tests.test_build_bibliography -v 2>&1 | tail -20
```

Expected: identical to before this task (nothing about `classify_case`/`classify_statute`'s *implementation* has changed yet, only imports) — all tests pass, including the three now-decorated classes (since `.venv-eyecite` has eyecite, the `skipUnless` condition is true and they run normally against the still-unchanged old implementation).

---

## Task 2: `classify_statute` — U.S. Code phrasing + eyecite backing

**Files:**
- Modify: `scripts/build_bibliography.py:176-200` (`_STATUTE_RE`, `_USC_RE`, `_YEAR_RE`, `classify_statute`)
- Test: `scripts/tests/test_build_bibliography.py:115-145` (`TestClassifyStatute`)

**Interfaces:**
- Consumes: `_require_eyecite()`, `get_citations`, `FullLawCitation` (Task 1).
- Produces: `classify_statute(text) -> dict|None` — same shape as before (`{"type": "statute", "abbrev": str, "section": str, "year": str|None}` or `None`), consumed unchanged by `classify_and_format` and `format_statute_bluebook`.

- [ ] **Step 1: Write the failing tests**

Add to `TestClassifyStatute` (after the existing `test_multi_section_usc_citation_not_truncated`):

```python
    def test_classifies_us_code_phrasing(self):
        """Cornell LII's actual works-cited page-title phrasing for the
        U.S. Code -- confirmed 2026-07-29 as the root cause of 20 real
        corpus entries (including this project's own central Copyright
        Act provisions, "17 U.S. Code § 101 - Definitions") being
        misfiled as non-legal, since the old _USC_RE required the
        literal string "U.S.C."."""
        from build_bibliography import classify_statute
        parsed = classify_statute(
            "17 U.S. Code § 101 - Definitions - Legal Information Institute - Cornell University."
        )
        self.assertEqual(parsed["abbrev"], "17 U.S.C.")
        self.assertEqual(parsed["section"], "101")
        self.assertIsNone(parsed["year"])

    def test_classifies_us_code_phrasing_with_year(self):
        from build_bibliography import classify_statute
        parsed = classify_statute("17 U.S. Code § 101 (2018)")
        self.assertEqual(parsed["abbrev"], "17 U.S.C.")
        self.assertEqual(parsed["section"], "101")
        self.assertEqual(parsed["year"], "2018")
```

- [ ] **Step 2: Run and confirm these two are RED, everything else in the class still GREEN**

```bash
.venv-eyecite/bin/python3 -m unittest scripts.tests.test_build_bibliography.TestClassifyStatute -v
```

Expected: `test_classifies_us_code_phrasing` and `test_classifies_us_code_phrasing_with_year` FAIL (old `_USC_RE` requires literal `"U.S.C."`, doesn't match `"U.S. Code"` at all → `classify_statute` returns `None` → `parsed["abbrev"]` raises `TypeError: 'NoneType' object is not subscriptable`). The other 5 existing tests PASS (old code untouched so far).

Before writing the fix, apply **systematic-debugging**: confirm this is genuinely `_USC_RE`'s literal-string requirement and not some other cause — `python3 -c "import re; print(re.search(r'\d+\s*U\.S\.C\.\s*§+', '17 U.S. Code § 101'))"` should print `None`, confirming the regex never matches this phrasing at all (not a subtler issue like a section-number formatting mismatch).

- [ ] **Step 3: Write the minimal implementation**

Replace lines 176–200 (`_STATUTE_RE` through the end of `classify_statute`) with:

```python
_STATUTE_RE = re.compile(
    r"(?P<code>" + "|".join(re.escape(k) for k in CODE_ABBREVIATIONS) + r")\s*§\s*(?P<section>[\d.]+)",
    re.IGNORECASE,
)
_YEAR_RE = re.compile(r"\((\d{4})\)")

# eyecite's reporters-db resolves the U.S. Code under two distinct
# reporter strings depending on source phrasing -- confirmed 2026-07-29:
# get_citations("17 U.S.C. § 512(c)") and get_citations("17 U.S. Code §
# 101 - ...") both return a FullLawCitation, with groups["reporter"] ==
# "U.S.C." or "U.S. Code" respectively (the latter is Cornell LII's own
# page-title phrasing, the confirmed source of this bug). Both name the
# same federal code, so both normalize to one Bluebook form below.
_USC_REPORTER_ALIASES = {"U.S.C.", "U.S. Code"}

# eyecite's FullLawCitation only captures the FIRST section number in a
# "§§ 101, 106" list (confirmed 2026-07-29:
# get_citations("17 U.S.C. §§ 101, 106")[0].groups["section"] == "101",
# not "101, 106") -- recovered by scanning the original text immediately
# after eyecite's own matched span for further ", NNN" continuations.
# Anchored to digits only (not the old _USC_RE's [\w.-]+, which could
# over-consume into following prose -- e.g. "§ 101, defining terms"
# would wrongly capture section "101, defining" with a word-based
# pattern; verified this exact failure mode with [\w.-]+ before settling
# on digits-only).
_SECTION_CONTINUATION_RE = re.compile(r"^(?:,\s*\d[\d.-]*)+")


def _section_with_continuation(text, citation):
    m = _SECTION_CONTINUATION_RE.match(text[citation.span()[1]:])
    return citation.groups.get("section", "") + (m.group(0) if m else "")


def classify_statute(text):
    """dict(type='statute', abbrev, section, year) if text names a known
    statute with a section symbol, else None. Never guesses at
    unrecognized abbreviations.

    Tries eyecite's FullLawCitation first, but ONLY trusts it for the
    federal U.S. Code (_USC_REPORTER_ALIASES) -- confirmed 2026-07-29
    that eyecite's reporters-db does not recognize this corpus's actual
    raw works-cited phrasing for California codes ("California Civil
    Code § 1550"), only the already-abbreviated Bluebook form ("Cal.
    Civ. Code § 1550") this corpus's raw text never actually uses, AND
    that eyecite's own corrected_citation()/groups reconstruction for
    California codes silently drops the "Civ."/"Corp." subject
    specifier. CODE_ABBREVIATIONS/_STATUTE_RE is therefore kept,
    unchanged, as the sole path for state codes; eyecite replaces only
    the confirmed, narrower federal U.S.C./U.S. Code bug.
    """
    if not text or not text.strip():
        return None
    _require_eyecite()
    for citation in get_citations(text):
        if isinstance(citation, FullLawCitation) and citation.groups.get("reporter") in _USC_REPORTER_ALIASES:
            year = citation.metadata.year
            return {
                "type": "statute",
                "abbrev": f"{citation.groups.get('title')} U.S.C.",
                "section": _section_with_continuation(text, citation),
                "year": str(year) if year else None,
            }
    m = _STATUTE_RE.search(text)
    if not m:
        return None
    abbrev = CODE_ABBREVIATIONS[m.group("code").lower()]
    section = m.group("section")
    year_m = _YEAR_RE.search(text)
    return {"type": "statute", "abbrev": abbrev, "section": section, "year": year_m.group(1) if year_m else None}
```

This deletes `_USC_RE` entirely (fully superseded).

- [ ] **Step 4: Run and confirm ALL of TestClassifyStatute is GREEN**

```bash
.venv-eyecite/bin/python3 -m unittest scripts.tests.test_build_bibliography.TestClassifyStatute -v
```

Expected: 7/7 pass. Apply **systematic-debugging** before moving on: confirm the two new tests pass *because* the `_USC_REPORTER_ALIASES` branch fired (not, say, because `_STATUTE_RE` accidentally also matched "U.S. Code" against some `CODE_ABBREVIATIONS` key) — add a temporary `print(citation.groups)` if needed, run once, confirm `{'title': '17', 'reporter': 'U.S. Code', 'section': '101'}`, then remove the print. Also confirm `test_classifies_known_code_with_year` and `test_multi_section_usc_citation_not_truncated` are genuinely exercising the paths this task's docstring claims (the CODE_ABBREVIATIONS fallback and the new continuation regex, respectively) — not passing for an unrelated reason.

- [ ] **Step 5: Run the full statute-adjacent formatter tests too (should be unaffected)**

```bash
.venv-eyecite/bin/python3 -m unittest scripts.tests.test_build_bibliography.TestFormatStatuteBluebook -v
```

Expected: 3/3 pass, unchanged (this class never calls `classify_statute`, only `format_statute_bluebook` directly with hand-built dicts).

---

## Task 3: `classify_case` — Bluebook order + broadened reporter coverage

**Files:**
- Modify: `scripts/build_bibliography.py:210-263` (`CASE_LAW_DOMAINS` through `classify_case`, excluding `CASE_LAW_DOMAINS`'s content — that's Task 5)
- Test: `scripts/tests/test_build_bibliography.py:164-217` (`TestClassifyCase`)

**Interfaces:**
- Consumes: `_require_eyecite()`, `get_citations`, `FullCaseCitation` (Task 1); `CASE_LAW_DOMAINS`, `_looks_like_case_domain` (unchanged interface, content expanded in Task 5).
- Produces: `classify_case(text, href) -> dict|None` — same shape as before (`{"type": "case", "name": str, "complete": bool, ...}` or `None`), consumed unchanged by `classify_and_format` and `format_case_bluebook`.

- [ ] **Step 1: Write the failing tests**

Add to `TestClassifyCase` (after the existing `test_procedural_role_label_stripped_from_captured_party_name`):

```python
    def test_bluebook_order_reporter_citation_now_recognized(self):
        """Confirmed 2026-07-29 root cause: the old _REPORTER_RE only
        matched "(YEAR) VOLUME REPORTER PAGE" (California order); this is
        the standard Bluebook "VOLUME REPORTER PAGE (YEAR)" order it
        missed entirely, even though "U.S." was in the old 9-item
        reporter allowlist."""
        from build_bibliography import classify_case
        parsed = classify_case("Marbury v. Madison, 5 U.S. 137 (1803)", href=None)
        self.assertEqual(parsed["name"], "Marbury v. Madison")
        self.assertTrue(parsed["complete"])
        self.assertEqual(parsed["year"], "1803")
        self.assertEqual(parsed["volume"], "5")
        self.assertEqual(parsed["reporter"], "U.S.")
        self.assertEqual(parsed["page"], "137")

    def test_second_bluebook_order_example(self):
        from build_bibliography import classify_case
        parsed = classify_case("Roe v. Wade, 410 U.S. 113 (1973)", href=None)
        self.assertTrue(parsed["complete"])
        self.assertEqual(parsed["year"], "1973")
        self.assertEqual(parsed["volume"], "410")
        self.assertEqual(parsed["page"], "113")

    def test_reporter_outside_old_nine_item_allowlist_now_recognized(self):
        """N.W.2d (North Western Reporter) was never in the old
        hardcoded 9-entry _REPORTER_ABBREVS list -- confirmed 2026-07-29
        against this real corpus works-cited entry."""
        from build_bibliography import classify_case
        parsed = classify_case("Women of State of Minnesota v. Gomez, 542 N.W.2d 17 (1995)", href=None)
        self.assertTrue(parsed["complete"])
        self.assertEqual(parsed["volume"], "542")
        self.assertEqual(parsed["reporter"], "N.W.2d")
        self.assertEqual(parsed["page"], "17")
        self.assertEqual(parsed["year"], "1995")

    def test_real_corpus_findlaw_bluebook_order_example(self):
        """Real works-cited text (caselaw.findlaw.com), not a synthetic
        string -- confirmed 2026-07-29 this is one of only 6 (of 356)
        currently-misfiled ' v. ' secondary entries with an immediately
        recoverable reporter citation."""
        from build_bibliography import classify_case
        parsed = classify_case(
            "CALIFORNIA v. FREEMAN, 488 U.S. 1311 (1989) - FindLaw Caselaw, accessed September 21, 2025,",
            href="https://caselaw.findlaw.com/court/us-supreme-court/488/1311.html",
        )
        self.assertTrue(parsed["complete"])
        self.assertEqual(parsed["volume"], "488")
        self.assertEqual(parsed["reporter"], "U.S.")
        self.assertEqual(parsed["page"], "1311")
        self.assertEqual(parsed["year"], "1989")

    def test_real_corpus_reporter_with_no_adjoining_year_leaves_year_none(self):
        """Confirmed 2026-07-29 against a real corpus entry: the "2025"
        here is an access date, not a decision year, and must not be
        misread as one. Feeds format_case_bluebook's new "[year
        unknown]" fallback (Task 4)."""
        from build_bibliography import classify_case
        parsed = classify_case(
            "Trading Technologies International v. IBG LLC, 921 F. 3d 1084 - BitLaw, accessed June 27, 2025,",
            href=None,
        )
        self.assertTrue(parsed["complete"])
        self.assertIsNone(parsed["year"])
        self.assertEqual(parsed["volume"], "921")
        self.assertEqual(parsed["reporter"], "F. 3d")
        self.assertEqual(parsed["page"], "1084")
```

- [ ] **Step 2: Run and confirm the new tests are RED, all 7 existing ones still GREEN**

```bash
.venv-eyecite/bin/python3 -m unittest scripts.tests.test_build_bibliography.TestClassifyCase -v
```

Expected: the 5 new tests FAIL — `test_bluebook_order_reporter_citation_now_recognized`/`test_second_bluebook_order_example`/`test_reporter_outside_old_nine_item_allowlist_now_recognized`/`test_real_corpus_findlaw_bluebook_order_example` fail because old `_REPORTER_RE.match(tail)` requires the tail to start with `(YYYY)`, so `parsed["complete"]` is `False`, not `True` (`assertTrue(parsed["complete"])` fails). `test_real_corpus_reporter_with_no_adjoining_year_leaves_year_none` fails the same way. The 7 pre-existing tests (including `test_full_reporter_citation_gives_complete_bluebook_data`, the California-order Marvin v. Marvin case) still PASS — old code is untouched so far.

Apply **systematic-debugging**: for one of the new failures, print `tail` and confirm it's exactly `"5 U.S. 137 (1803)"` (standard order, no leading parenthetical year) to confirm this is genuinely the field-order gap, not e.g. a `_CASE_RE` name-capture problem.

- [ ] **Step 3: Write the minimal implementation**

Replace lines 210–263 (from `CASE_LAW_DOMAINS = {...}` through the end of `classify_case`) with (this step's `CASE_LAW_DOMAINS` content is the *original* 5-entry set — Task 5 expands it separately, in its own red/green cycle):

```python
CASE_LAW_DOMAINS = {"courtlistener.com", "casetext.com", "casemine.com", "law.justia.com", "scholar.google.com"}
_CASE_RE = re.compile(
    r"(?P<plaintiff>[A-Z][\w.,'&-]*(?:\s+[A-Z][\w.,'&-]*){0,6})\s+v\.\s+"
    r"(?P<defendant>[A-Z][\w.,'&-]*(?:\s+[A-Z][\w.,'&-]*){0,6})"
)
_PROCEDURAL_ROLE_RE = re.compile(
    r",?\s*(?:Plaintiff|Defendant|Appellant|Appellee|Respondent|Petitioner)(?:-\w+)?\.?,?\s*$",
    re.IGNORECASE,
)
# A citation immediately follows the matched case name in one of two
# orders, confirmed 2026-07-29 against real examples of both: standard
# Bluebook ("Marbury v. Madison, 5 U.S. 137 (1803)" -- citation right at
# the start of the tail) or California's year-first order ("Marvin v.
# Marvin (1976) 18 Cal. 3d 660" -- a "(YEAR) " prefix before the
# citation). eyecite does not capture a LEADING year as the citation's
# own metadata.year (confirmed: get_citations("(1976) 18 Cal. 3d
# 660")[0].metadata.year is None), so it is captured here instead.
_LEADING_YEAR_RE = re.compile(r"^\((?P<year>\d{4})\)\s*")


def _strip_procedural_role(name):
    return _PROCEDURAL_ROLE_RE.sub("", name).strip(" ,;")


def _hostname(href):
    return urlsplit(href).netloc.lower() if href else None


def _looks_like_case_domain(href):
    host = _hostname(href)
    if not host:
        return False
    return any(host == d or host.endswith("." + d) for d in CASE_LAW_DOMAINS)


def _immediately_following_case_citation(tail):
    """(FullCaseCitation, leading_year) for the reporter citation that
    appears immediately at the start of tail, in either order (see
    _LEADING_YEAR_RE above) -- or (None, None) if no eyecite-resolvable
    citation is immediately adjacent. Anchoring to the exact start of
    tail (not "found somewhere in tail") is deliberate: it is what
    prevents an unrelated reporter citation elsewhere in a longer string
    from corroborating a false " v. " match -- confirmed 2026-07-29
    against both existing adversarial tests for this (an unrelated
    citation 60+ characters into the tail, and a second, real, but
    unrelated citation embedded in a parenthetical aside): neither sits
    at position 0 of tail, so neither corroborates."""
    if not tail:
        return None, None
    leading_year = None
    remainder = tail
    ly_m = _LEADING_YEAR_RE.match(tail)
    if ly_m:
        leading_year = ly_m.group("year")
        remainder = tail[ly_m.end():]
    for citation in get_citations(remainder):
        if isinstance(citation, FullCaseCitation) and citation.span()[0] == 0:
            return citation, leading_year
    return None, None


def classify_case(text, href):
    """dict(type='case', name, complete, ...) if text contains a " v. "
    case-name pattern AND that pattern is corroborated by either a full
    reporter citation immediately following the matched name or a known
    case-law-aggregator URL, else None. A bare " v. " match with neither
    signal is NOT classified as a case (avoids false positives on essay
    titles like "Privacy v. Transparency in Legal Practice").

    The reporter citation itself is found via eyecite, replacing the old
    hand-rolled _REPORTER_RE (which only matched a "(YEAR) VOLUME
    REPORTER PAGE" order against 9 hardcoded reporters -- confirmed
    2026-07-29 to miss standard Bluebook "VOLUME REPORTER PAGE (YEAR)"
    order entirely). The case-name pattern itself (_CASE_RE) is
    unchanged: eyecite has no bare-prose case-name-extraction capability
    independent of an actual citation, so it cannot replace this part --
    it is only used to recognize/parse the reporter citation once a
    candidate name is already in hand.
    """
    if not text or not text.strip():
        return None
    m = _CASE_RE.search(text)
    if not m:
        return None
    name = f"{_strip_procedural_role(m.group('plaintiff'))} v. {_strip_procedural_role(m.group('defendant'))}"
    tail = text[m.end():].lstrip(" ,.")
    _require_eyecite()
    citation, leading_year = _immediately_following_case_citation(tail)
    if citation:
        year = leading_year or (str(citation.metadata.year) if citation.metadata.year else None)
        return {
            "type": "case", "name": name, "complete": True,
            "year": year,
            "volume": citation.groups.get("volume"),
            "reporter": citation.groups.get("reporter"),
            "page": citation.groups.get("page"),
        }
    if _looks_like_case_domain(href):
        return {"type": "case", "name": name, "complete": False}
    return None
```

This deletes `_REPORTER_ABBREVS` and `_REPORTER_RE` entirely (fully superseded).

- [ ] **Step 4: Run and confirm ALL of TestClassifyCase is GREEN**

```bash
.venv-eyecite/bin/python3 -m unittest scripts.tests.test_build_bibliography.TestClassifyCase -v
```

Expected: 12/12 pass (7 pre-existing + 5 new).

Apply **systematic-debugging** before moving on — this is the highest-risk change in this plan (the anchoring logic), so confirm GREEN for the right reason, not by accident:
- Temporarily break the anchoring check (`citation.span()[0] == 0` → `True`, i.e., accept any citation anywhere in `remainder`) and re-run `test_unrelated_reporter_citation_elsewhere_in_text_does_not_corroborate` and `test_second_unrelated_case_citation_does_not_corroborate_the_first` specifically — confirm they go RED (proving the anchoring check is load-bearing for these two, not incidentally satisfied some other way). Then revert the break and confirm GREEN again.
- Confirm `test_full_reporter_citation_gives_complete_bluebook_data` (Marvin v. Marvin, California order) is passing via the `_LEADING_YEAR_RE` branch specifically, not accidentally: temporarily comment out the `_LEADING_YEAR_RE` handling (treat `remainder = tail` unconditionally) and confirm this ONE test goes RED (citation would then be found at `span()[0] == 7`, not `0`) while the Bluebook-order tests stay GREEN. Revert.

---

## Task 4: `format_case_bluebook` — `[year unknown]` fallback

**Files:**
- Modify: `scripts/build_bibliography.py:266-272` (`format_case_bluebook`)
- Test: `scripts/tests/test_build_bibliography.py:219-246` (`TestFormatCaseBluebook`)

**Interfaces:**
- Consumes: `classify_case`'s output shape (Task 3) — specifically, that `parsed["year"]` can now legitimately be `None` even when `parsed["complete"]` is `True`.
- Produces: `format_case_bluebook(parsed) -> str` — same shape as before, with one new fallback branch.

- [ ] **Step 1: Write the failing test**

Add to `TestFormatCaseBluebook` (after `test_formats_partial_citation_with_flag`; this test builds its dict by hand like its two siblings, so it does NOT need an eyecite skip-guard):

```python
    def test_formats_complete_citation_with_unknown_year(self):
        """Newly reachable now that eyecite can find a complete reporter
        citation with no adjoining year at all (Task 3) -- the old
        _REPORTER_RE could never produce this combination, since its
        year group was mandatory for a match to happen at all."""
        from build_bibliography import format_case_bluebook
        parsed = {"type": "case", "name": "Trading Technologies International v. IBG LLC",
                  "complete": True, "year": None, "volume": "921", "reporter": "F. 3d", "page": "1084"}
        self.assertEqual(
            format_case_bluebook(parsed),
            "Trading Technologies International v. IBG LLC, 921 F. 3d 1084 ([year unknown]).",
        )
```

- [ ] **Step 2: Run and confirm RED**

```bash
python3 -m unittest scripts.tests.test_build_bibliography.TestFormatCaseBluebook -v
```

(Bare `python3` is fine for this whole class — none of its tests need eyecite.)

Expected: `test_formats_complete_citation_with_unknown_year` FAILS — current code does `f"... ({parsed['year']})."`, producing the literal string `"...(None)."`, not `"...([year unknown])."`.

- [ ] **Step 3: Write the minimal implementation**

Replace `format_case_bluebook` (lines 266–272) with:

```python
def format_case_bluebook(parsed):
    """Bluebook-style citation string for a classify_case() result. Falls
    back to a "[reporter citation unknown]" marker when the case data is
    only partial (name corroborated by domain but no reporter found), and
    to a "[year unknown]" marker when a reporter WAS found but with no
    adjoining year -- confirmed against a real corpus entry (Task 3) where
    the only nearby 4-digit number is an access date, not a decision year."""
    if parsed["complete"]:
        year = parsed["year"] or "[year unknown]"
        return f"{parsed['name']}, {parsed['volume']} {parsed['reporter']} {parsed['page']} ({year})."
    return f"{parsed['name']}, [reporter citation unknown]."
```

- [ ] **Step 4: Run and confirm ALL of TestFormatCaseBluebook is GREEN**

```bash
python3 -m unittest scripts.tests.test_build_bibliography.TestFormatCaseBluebook -v
```

Expected: 5/5 pass (4 pre-existing + 1 new), under bare `python3` (confirming this class genuinely has no eyecite dependency).

---

## Task 5: `CASE_LAW_DOMAINS` expansion

**Files:**
- Modify: `scripts/build_bibliography.py` (the `CASE_LAW_DOMAINS` set written in Task 3 Step 3)
- Test: `scripts/tests/test_build_bibliography.py` (`TestClassifyCase`)

**Interfaces:**
- Consumes: `_looks_like_case_domain` (Task 3, unchanged logic — only the set's contents grow).
- Produces: nothing new consumed elsewhere; this is a data-only change.

- [ ] **Step 1: Write the failing tests**

Add to `TestClassifyCase`:

```python
    def test_expanded_domain_supreme_justia_recognized(self):
        """Real corpus entry -- the reporter citation IS present in this
        title ("421 U.S. 837 (1975)") but is not immediately adjacent to
        the matched case name (separated by a "| " page-title divider),
        so this is recognized via domain corroboration, not the reporter
        path -- confirmed 2026-07-29 by direct testing of the anchoring
        logic against this exact string."""
        from build_bibliography import classify_case
        parsed = classify_case(
            "United Housing Foundation, Inc. v. Forman | 421 U.S. 837 (1975) | Justia U.S. Supreme Court Center, accessed June 28, 2025,",
            href="https://supreme.justia.com/cases/federal/us/421/837/",
        )
        self.assertIsNotNone(parsed)
        self.assertFalse(parsed["complete"])

    def test_expanded_domain_oyez_recognized(self):
        from build_bibliography import classify_case
        parsed = classify_case(
            "Citizens United v. Federal Election Commission | Oyez, accessed June 28, 2025,",
            href="https://www.oyez.org/cases/2008/08-205",
        )
        self.assertIsNotNone(parsed)
        self.assertFalse(parsed["complete"])

    def test_expanded_domain_casebriefs_recognized(self):
        from build_bibliography import classify_case
        parsed = classify_case(
            "United Housing Foundation, Inc. v. Forman | Case Brief for Law ..., accessed June 28, 2025,",
            href="https://www.casebriefs.com/blog/law/securities-regulation/securities-regulation-keyed-to-coffee/definitions-of-security-and-exempted-securities/united-housing-foundation-inc-v-forman/",
        )
        self.assertIsNotNone(parsed)
        self.assertFalse(parsed["complete"])

    def test_expanded_domain_uscourts_gov_suffix_recognized(self):
        """Confirms the existing suffix-match mechanism (host.endswith("."
        + d)) correctly extends to a federal-court subdomain from just
        one "uscourts.gov" entry -- confirmed 2026-07-29 this exact real
        corpus entry (a notable Section 230 case) uses this subdomain."""
        from build_bibliography import classify_case
        parsed = classify_case(
            "FAIR HOUSING COUNCIL v. ROOMMATES.COM - Ninth Circuit, accessed September 13, 2025,",
            href="https://cdn.ca9.uscourts.gov/datastore/opinions/2008/04/02/0456916.pdf",
        )
        self.assertIsNotNone(parsed)
        self.assertFalse(parsed["complete"])

    def test_expanded_domain_supremecourt_gov_recognized(self):
        from build_bibliography import classify_case
        parsed = classify_case(
            "19-1392 Dobbs v. Jackson Women's Health Organization (06/24/2022) - Supreme Court, accessed September 16, 2025,",
            href="https://www.supremecourt.gov/opinions/21pdf/19-1392_6j37.pdf",
        )
        self.assertIsNotNone(parsed)
        self.assertFalse(parsed["complete"])

    def test_wikipedia_domain_deliberately_not_recognized_as_case_law_aggregator(self):
        """Pins a deliberate design decision, not an oversight: Wikipedia
        is a general encyclopedia, not a case-law-specific aggregator --
        confirmed 2026-07-29 that none of the corpus's 63 Wikipedia-linked
        ' v. ' entries carry a recoverable reporter citation either, so
        classifying them as "legal" would fabricate a citation status
        this data doesn't support. They correctly remain unclassified
        here (classify_and_format later routes them to "secondary", the
        honest outcome for a real secondary source)."""
        from build_bibliography import classify_case
        parsed = classify_case(
            "Reves v. Ernst & Young - Wikipedia, accessed June 28, 2025,",
            href="https://en.wikipedia.org/wiki/Reves_v._Ernst_%26_Young",
        )
        self.assertIsNone(parsed)
```

- [ ] **Step 2: Run and confirm the 5 positive tests are RED, the Wikipedia test is already GREEN**

```bash
.venv-eyecite/bin/python3 -m unittest scripts.tests.test_build_bibliography.TestClassifyCase -v
```

Expected: `test_expanded_domain_supreme_justia_recognized`, `test_expanded_domain_oyez_recognized`, `test_expanded_domain_casebriefs_recognized`, `test_expanded_domain_uscourts_gov_suffix_recognized`, `test_expanded_domain_supremecourt_gov_recognized` FAIL (`assertIsNotNone(parsed)` fails — none of these hostnames are in the current 5-entry `CASE_LAW_DOMAINS`). `test_wikipedia_domain_deliberately_not_recognized_as_case_law_aggregator` already PASSES (Wikipedia was never in `CASE_LAW_DOMAINS` and isn't being added).

- [ ] **Step 3: Write the minimal implementation**

Replace the `CASE_LAW_DOMAINS` line written in Task 3 with:

```python
CASE_LAW_DOMAINS = {
    # Original 5.
    "courtlistener.com", "casetext.com", "casemine.com", "law.justia.com", "scholar.google.com",
    # Added 2026-07-29 -- confirmed by direct corpus analysis: of 356 raw
    # works-cited entries containing " v. " that the old code misfiled as
    # "secondary", 350 have NO recoverable reporter citation anywhere in
    # their text (bare case-name titles from case-law-specific archives/
    # study-aid sites); fixing the reporter-parsing bug alone (Task 3)
    # only recovers 6 of those 356. These real hostnames (one verified
    # real corpus entry per host) recover most of the rest.
    "supreme.justia.com",       # Justia's US Supreme Court opinion archive (a sibling subdomain of law.justia.com, not a suffix of it -- needs its own entry)
    "caselaw.findlaw.com", "supreme.findlaw.com",  # FindLaw's case-law subdomains (codes./constitution./corporate.findlaw.com are NOT case archives and are deliberately excluded)
    "oyez.org",                 # Oyez -- dedicated SCOTUS oral-argument/case archive
    "casebriefs.com",           # dedicated case-brief archive (briefs real, decided cases only)
    "studicata.com",            # ditto
    "law.cornell.edu",          # Cornell LII -- hosts primary case text alongside U.S.C./CFR
    "scocal.stanford.edu",      # Stanford's CA Supreme Court opinion archive
    "uscourts.gov",             # federal judiciary -- matches *.uscourts.gov via the existing suffix check (e.g. cdn.ca9.uscourts.gov, media.cadc.uscourts.gov, www.uscourts.gov)
    "supremecourt.gov",         # official SCOTUS site
    # Deliberately NOT added (confirmed real hostnames in the same
    # corpus scan, none case-law-specific): en.wikipedia.org,
    # www.britannica.com, www.ebsco.com, firstamendment.mtsu.edu, and a
    # long tail of law-firm/advocacy/general-education sites. See
    # test_wikipedia_domain_deliberately_not_recognized_as_case_law_aggregator.
}
```

- [ ] **Step 4: Run and confirm ALL of TestClassifyCase is GREEN**

```bash
.venv-eyecite/bin/python3 -m unittest scripts.tests.test_build_bibliography.TestClassifyCase -v
```

Expected: 18/18 pass (12 from Task 3 + 6 new).

Apply **systematic-debugging**: for `test_expanded_domain_uscourts_gov_suffix_recognized` specifically, confirm the mechanism — temporarily change `"uscourts.gov"` to `"www.uscourts.gov"` in the set and re-run just that test; it should go RED (proving `cdn.ca9.uscourts.gov` is matched via the bare `uscourts.gov` suffix rule, not by coincidence). Revert.

---

## Task 6: Skip-guard the remaining eyecite-transitively-dependent tests

**Files:**
- Modify: `scripts/tests/test_build_bibliography.py` (`TestFormatCaseBluebook`, `TestVerifyInvariants`, `TestEndToEndIntegration`)

**Interfaces:**
- Consumes: `EYECITE_AVAILABLE`, `SKIP_REASON` (Task 1).

This task has no new production code — it is pure test-infrastructure hygiene, confirmed necessary by directly tracing which tests call `classify_case`/`classify_statute`/`classify_and_format` (directly or transitively via `verify_invariants`, which re-derives each raw entry's classification):

| Test | Calls `classify_and_format` (or a `classify_*` directly)? | Guard needed? |
|---|---|---|
| `TestFormatCaseBluebook.test_trailing_comma_in_captured_party_name_does_not_produce_double_comma` | yes, `classify_case` | method-level |
| `TestFormatCaseBluebook.test_trailing_comma_after_abbreviation_period_strips_comma_not_period` | yes, `classify_case` | method-level |
| `TestVerifyInvariants.test_no_entry_lost_passes_when_counts_reconcile` | yes, `raw=[RawEntry(text="t",...)]` is non-empty | method-level |
| `TestVerifyInvariants.test_entry_lost_is_flagged` | yes, same reason | method-level |
| `TestVerifyInvariants.test_legal_entry_missing_section_or_v_is_flagged` | no, `raw=[]` | none |
| `TestVerifyInvariants.test_duplicate_normalized_url_across_entries_is_flagged` | no, `raw=[]` (passed via other params) | none |
| `TestVerifyInvariants.test_dangling_backlink_is_flagged` | no, `raw=[]` | none |
| `TestVerifyInvariants.test_eu_directive_and_regulation_citations_satisfy_legal_marker_check` | no, `raw=[]` | none |
| `TestVerifyBibCoverage.*` | no (works entirely off pre-classified `BibliographyEntry`/tuples) | none |
| `TestEmitDocbook.*` | no (works off pre-classified `BibliographyEntry` objects / raw XML backlink scanning) | none |
| `TestEndToEndIntegration.test_full_pipeline_produces_valid_docbook_with_all_four_buckets` | yes | method-level |
| `TestEndToEndIntegration.test_real_bibliography_bib_parses_and_classifies_without_exceptions` | no (`parse_bibtex`/`classify_bib_entry` only — a completely separate code path from `classify_case`/`classify_statute`) | none (will get a *different*, bibtexparser guard in Bug 2's separate pass) |

- [ ] **Step 1: Apply the method-level guards**

In `scripts/tests/test_build_bibliography.py`, add `@unittest.skipUnless(EYECITE_AVAILABLE, SKIP_REASON)` immediately above each of these five method definitions:
- `TestFormatCaseBluebook.test_trailing_comma_in_captured_party_name_does_not_produce_double_comma`
- `TestFormatCaseBluebook.test_trailing_comma_after_abbreviation_period_strips_comma_not_period`
- `TestVerifyInvariants.test_no_entry_lost_passes_when_counts_reconcile`
- `TestVerifyInvariants.test_entry_lost_is_flagged`
- `TestEndToEndIntegration.test_full_pipeline_produces_valid_docbook_with_all_four_buckets`

- [ ] **Step 2: Verify under bare `python3` — everything either passes or skips, nothing errors**

```bash
python3 -m unittest discover -s scripts/tests -p "test_*.py" -v 2>&1 | tail -40
```

Expected: `OK (skipped=N)` with `N` covering exactly the guarded tests/classes (Task 1's 3 classes + this task's 5 methods = the full set of eyecite-dependent tests); zero failures, zero errors.

- [ ] **Step 3: Verify under `.venv-eyecite/bin/python3` — everything actually runs and passes**

```bash
.venv-eyecite/bin/python3 -m unittest discover -s scripts/tests -p "test_*.py" -v 2>&1 | tail -40
```

Expected: `OK`, zero skips related to eyecite (this interpreter has it), zero failures, zero errors — this is the run that actually exercises every line touched by Tasks 2–5 for real.

---

## Task 7: Real corpus regeneration + verified before/after count

**Files:** none (verification only — no source changes).

- [ ] **Step 1: Capture the "before" count from the current committed corpus**

```bash
cd /home/metavacua/legal-theory/.worktrees/claude/fixes/eyecite-bibtex
python3 -c "
text = open('docs/bibliography/references.xml', encoding='utf-8').read()
start = text.index('xml:id=\"academic-secondary-sources\"')
end = text.index('xml:id=\"appendix-needs-review\"')
import re
count = sum(1 for li in re.findall(r'<listitem>.*?</listitem>', text[start:end], re.DOTALL) if ' v. ' in li)
print('BEFORE:', count)
"
```

Record this number exactly (do not assume it matches the task brief's "299" — the corpus may have drifted since that count was taken; report what is actually measured).

- [ ] **Step 2: Regenerate the corpus with the fixed code**

```bash
.venv-eyecite/bin/python3 scripts/build_bibliography.py
```

Expected: this will very likely print `VALIDATION FAILED` and exit 1 — this is the **pre-existing, out-of-scope `emit_docbook()` title-duplication defect** documented in the Research Findings section above, confirmed present even on the unmodified pre-this-plan code. `docs/bibliography/references.xml` is still fully rewritten before that check runs (`main()` calls `xml_path.write_text(...)` unconditionally, before `validate()`), so the file on disk reflects this fix's real output regardless of the exit code. Do not attempt to fix this defect as part of this task — it is outside the two bugs this task is scoped to.

- [ ] **Step 3: Capture the "after" count from the freshly-written file**

```bash
python3 -c "
text = open('docs/bibliography/references.xml', encoding='utf-8').read()
start = text.index('xml:id=\"academic-secondary-sources\"')
end = text.index('xml:id=\"appendix-needs-review\"')
import re
count = sum(1 for li in re.findall(r'<listitem>.*?</listitem>', text[start:end], re.DOTALL) if ' v. ' in li)
print('AFTER:', count)
"
```

- [ ] **Step 4: Confirm the drop, and separately confirm the U.S. Code statute fix on the same freshly-written file**

```bash
python3 -c "
text = open('docs/bibliography/references.xml', encoding='utf-8').read()
start = text.index('xml:id=\"legal-citations\"')
end = text.index('xml:id=\"academic-secondary-sources\"')
print('legal-citations entries containing U.S.C.:', text[start:end].count('U.S.C.'))
"
```

Expected: at least one `U.S.C.` entry now appears in `legal-citations` (there were zero before, since `_USC_RE` never matched "U.S. Code" phrasing and `_STATUTE_RE`'s `CODE_ABBREVIATIONS` has no U.S.C. entries at all).

- [ ] **Step 5: Restore the working tree to the pre-regeneration committed state**

The regenerated `docs/bibliography/references.xml`/`references.meta.xml` are NOT part of this bug fix's diff (this task's scope is `scripts/build_bibliography.py` and its tests, not a corpus-wide regeneration commit, and the file can't be committed cleanly anyway while the pre-existing validation defect stands). Discard the regeneration once the counts above are recorded:

```bash
git status --short  # confirm only docs/bibliography/references*.xml are modified, nothing else
git checkout -- docs/bibliography/references.xml docs/bibliography/references.meta.xml
git status --short  # confirm clean
```

- [ ] **Step 6: Full suite, one more time, both interpreters (final pre-commit gate)**

```bash
python3 -m unittest discover -s scripts/tests -p "test_*.py" 2>&1 | tail -10
.venv-eyecite/bin/python3 -m unittest discover -s scripts/tests -p "test_*.py" 2>&1 | tail -10
```

Expected: both `OK` (the first with a nonzero `skipped` count, the second with zero eyecite-related skips).

---

## Self-Review

**Spec coverage:**
- "_REPORTER_RE expects... fails on Marbury/Roe" → Task 3 (`test_bluebook_order_reporter_citation_now_recognized`, `test_second_bluebook_order_example`).
- "_REPORTER_ABBREVS only has 9 hardcoded reporter strings" → Task 3 (`test_reporter_outside_old_nine_item_allowlist_now_recognized`, uses N.W.2d).
- "CASE_LAW_DOMAINS only has 5 hardcoded hostnames" → Task 5.
- "classify_statute()/_USC_RE require... 'U.S.C.'... miss... 'U.S. Code'" → Task 2.
- "preserving classify_and_format()'s existing contract" → unchanged in all tasks (only `classify_case`/`classify_statute`/`format_case_bluebook`/`CASE_LAW_DOMAINS` touched; `classify_and_format` itself is never edited).
- "Re-run corpus generation... confirm via a direct count" → Task 7.
- eyecite installed via dedicated venv, same pattern as `eyecite_classify.py` → Task 1.

**Placeholder scan:** none found — every step has real, complete code or an exact runnable command with a stated expected result.

**Type consistency:** `classify_statute`/`classify_case` return shapes match what `format_statute_bluebook`/`format_case_bluebook`/`classify_and_format` already expect (`abbrev`/`section`/`year` for statutes; `name`/`complete`/`year`/`volume`/`reporter`/`page` for cases) — verified against the actual current call sites in `classify_and_format`, `format_statute_bluebook`, `format_case_bluebook` (all unmodified, all read directly before writing this plan).

**Not in scope (flag to user, do not fix here):**
- The pre-existing `emit_docbook()` title-duplication defect (Research Finding 7 / Task 7 Step 2) — breaks `main()`'s exit code on every run, unrelated to either of this task's two assigned bugs.
- BUG 2 (`parse_bibtex`/bibtexparser) — separate plan, separate TDD cycle, separate commit, per the task's explicit instructions.

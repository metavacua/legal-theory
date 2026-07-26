# eyecite Classification Wrapper (Task 2) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Install `eyecite` (Free Law Project) into a dedicated, gitignored venv and build a thin
`classify_citation_text(text) -> dict` wrapper in `docs/scripts/eyecite_classify.py`, consumed by
Task 4 (numbered-citation conversion) and the pilot task, per
`docs/superpowers/specs/2026-07-26-citation-standardization-design.md` Section 5.

**Architecture:** `eyecite.get_citations(text)` returns a list of typed citation objects in the
order they appear in the text. The wrapper walks that list and returns the role of the first
`FullCaseCitation` or `FullLawCitation` it finds (`"case"` / `"statute"`); anything else --
`UnknownCitation`, no match at all, or empty/whitespace-only input -- is reported as unresolved
(`role=None, resolved=False, parsed=None`). Only a `Full*Citation` counts as resolved; eyecite's
own `UnknownCitation` (citation-shaped fragment it can't confidently type) is a deliberate
non-match, not a weak positive.

**Tech Stack:** `eyecite` (Free Law Project), installed via a dedicated Python venv at
`.venv-eyecite/` (repo root, gitignored) -- no apt package exists for it, unlike `lxml`. Python
stdlib `unittest`, matching every other test file in `docs/scripts/tests/`.

## Global Constraints

- `eyecite` has no apt package. It is installed into `.venv-eyecite/` (repo root, gitignored), not
  system-wide -- Debian's PEP 668 "externally managed environment" blocks a bare
  `pip install --break-system-packages`-free system install, and `--break-system-packages` is not
  an acceptable workaround here (explicit user direction).
- Any script that imports `eyecite`, including its own test file, is run via
  `.venv-eyecite/bin/python3`, never the bare system `python3` every other script in this repo
  uses. This is a deliberate, new, documented operational convention for this one script.
- `classify_citation_text(text) -> dict` must always return a dict with keys `role`
  (`"case"`/`"statute"`/`None`), `resolved` (bool), `parsed` (str or `None`) -- it must never raise
  for any string input, including `""`, because Task 4 and the pilot task treat it as a plain
  value-returning classifier, not something they need to wrap in a try/except.
- Test file location and style matches the existing convention in `docs/scripts/tests/` (e.g.
  `test_citation_entry.py`): `sys.path.insert(0, str(Path(__file__).resolve().parent.parent))`
  then `from <module> import <name>` inside each test method, `unittest.TestCase` classes grouped
  by function under test.

## Pre-implementation verification (already performed, informs this plan)

Directly tested against the installed `eyecite` before writing any test/implementation code:

1. `"...Alice Corp. v. CLS Bank Int'l, 573 U.S. 208 (2014)..."` -> one `FullCaseCitation`,
   `corrected_citation()` == `"573 U.S. 208"`. Matches the brief.
2. `"Alice v. CLS Bank: United States Supreme Court Establishes General Patentability Test,
   accessed September 2, 2025,"` -> zero citations found. Matches the brief.
3. `"California Code, Corporations Code - CORP § 12200 - Codes - FindLaw"` -> one
   `UnknownCitation('§', ...)`. Matches the brief (must not count as a resolved statute).
4. **Not covered by the brief, found during independent verification:** `eyecite.get_citations("")`
   raises `ValueError: Both \`markup_text\` and \`plain_text\` are empty` -- confirmed by reading
   `eyecite/models.py` `Document.__post_init__`: it checks Python truthiness on both `plain_text`
   and `markup_text`, and only the exact empty string is falsy, so this fires only for `text == ""`
   (`markup_text` is never passed by this wrapper, so it's always `""`). Whitespace-only strings
   (`"   "`, `"\n\t"`) are truthy and do NOT trigger this -- they flow through normally and
   correctly yield zero citations. Root cause and fix documented in this plan's Task, below; the
   wrapper must guard against this at its own boundary since its interface contract says it never
   raises.
5. Multi-citation input (`"...573 U.S. 208 (2014) and also 17 U.S.C. § 512(c)..."`) -> two
   citations, a `FullCaseCitation` followed by a `FullLawCitation`, in text order. A loop that
   returns on the first `Full{Case,Law}Citation` match therefore returns the *first* resolved
   citation in document order, not "the most legally significant one" or "all of them" -- this is
   the documented, intentional behavior (single first-match, not multi-match), covered by an
   explicit test so it isn't accidentally changed later.

## File Structure

- Create `.venv-eyecite/` (gitignored) -- dedicated venv holding the `eyecite` install.
- Modify `.gitignore` -- add `.venv-eyecite/`.
- Create `docs/scripts/eyecite_classify.py` -- the `classify_citation_text()` wrapper.
- Create `docs/scripts/tests/test_eyecite_classify.py` -- its tests (run only via
  `.venv-eyecite/bin/python3`).

---

### Task: `eyecite` venv setup and classification wrapper

**Files:**
- Create: `.venv-eyecite/` (gitignored, not committed)
- Modify: `.gitignore`
- Create: `docs/scripts/eyecite_classify.py`
- Test: `docs/scripts/tests/test_eyecite_classify.py`

**Interfaces:**
- Produces: `classify_citation_text(text) -> dict` with keys `role` (`"case"`, `"statute"`,
  `None`), `resolved` (bool), `parsed` (the matched citation string, or `None`) -- consumed by
  Task 4 and the pilot task. Never raises for any string input.

- [ ] **Step 1: Create the venv and install eyecite**

```bash
python3 -m venv .venv-eyecite
.venv-eyecite/bin/pip install --quiet eyecite
.venv-eyecite/bin/python3 -c "import eyecite; print('OK')"
```
Expected: prints `OK`.

- [ ] **Step 2: Gitignore the venv**

Add to `.gitignore`:
```
.venv-eyecite/
```

- [ ] **Step 3: Write the failing tests**

Create `docs/scripts/tests/test_eyecite_classify.py`:
```python
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class TestClassifyCitationText(unittest.TestCase):
    def test_full_case_citation_resolves_as_case(self):
        from eyecite_classify import classify_citation_text
        result = classify_citation_text(
            "This references Alice Corp. v. CLS Bank Int'l, 573 U.S. 208 (2014) directly."
        )
        self.assertEqual(result["role"], "case")
        self.assertTrue(result["resolved"])
        self.assertIn("573 U.S. 208", result["parsed"])

    def test_full_law_citation_resolves_as_statute(self):
        from eyecite_classify import classify_citation_text
        result = classify_citation_text("See 17 U.S.C. § 512(c) for the safe harbor.")
        self.assertEqual(result["role"], "statute")
        self.assertTrue(result["resolved"])
        self.assertIn("17 U.S.C. § 512", result["parsed"])

    def test_webpage_title_without_a_real_citation_does_not_resolve(self):
        """The corpus's actual works-cited text -- confirmed 2026-07-26
        that eyecite correctly finds nothing here, because there is
        nothing there to find (no reporter citation, just a webpage
        title mentioning a case name)."""
        from eyecite_classify import classify_citation_text
        result = classify_citation_text(
            "Alice v. CLS Bank: United States Supreme Court Establishes "
            "General Patentability Test, accessed September 2, 2025,"
        )
        self.assertFalse(result["resolved"])
        self.assertIsNone(result["role"])
        self.assertIsNone(result["parsed"])

    def test_statute_symbol_alone_is_unresolved_not_a_confident_statute(self):
        """A bare "§" glued into aggregator-title noise is flagged
        UnknownCitation by eyecite, not a confidently-typed statute --
        confirmed 2026-07-26 by direct testing. Must not be reported
        as role="statute" on that weak a signal."""
        from eyecite_classify import classify_citation_text
        result = classify_citation_text(
            "California Code, Corporations Code - CORP § 12200 - Codes - FindLaw"
        )
        self.assertFalse(result["resolved"])
        self.assertIsNone(result["role"])

    def test_empty_string_does_not_raise_and_is_unresolved(self):
        """eyecite.get_citations("") itself raises ValueError (confirmed
        2026-07-26 by reading eyecite/models.py Document.__post_init__ --
        it requires plain_text or markup_text to be non-empty). The
        wrapper's contract is to always return a dict, never raise, so
        it must guard this case at its own boundary rather than let the
        exception propagate to callers (Task 4, the pilot task)."""
        from eyecite_classify import classify_citation_text
        result = classify_citation_text("")
        self.assertEqual(result, {"role": None, "resolved": False, "parsed": None})

    def test_whitespace_only_string_is_unresolved(self):
        from eyecite_classify import classify_citation_text
        result = classify_citation_text("   \n\t  ")
        self.assertEqual(result, {"role": None, "resolved": False, "parsed": None})

    def test_plain_prose_with_no_citation_is_unresolved(self):
        from eyecite_classify import classify_citation_text
        result = classify_citation_text("no citation here at all just plain prose")
        self.assertFalse(result["resolved"])
        self.assertIsNone(result["role"])

    def test_multiple_citations_returns_the_first_in_document_order(self):
        """When a string contains more than one resolvable citation,
        classify_citation_text reports only one classification (the
        interface returns a single role/parsed pair, not a list) --
        confirmed 2026-07-26 by direct testing that eyecite returns
        citations in text order. The wrapper returns the first
        Full{Case,Law}Citation it encounters, not "the most
        significant" or all of them. This test pins that behavior so
        it isn't silently changed later."""
        from eyecite_classify import classify_citation_text
        result = classify_citation_text(
            "See Alice Corp. v. CLS Bank Int'l, 573 U.S. 208 (2014) "
            "and also 17 U.S.C. § 512(c) for more."
        )
        self.assertEqual(result["role"], "case")
        self.assertIn("573 U.S. 208", result["parsed"])
```

- [ ] **Step 4: Run the tests to verify they fail**

Run: `.venv-eyecite/bin/python3 -m unittest docs.scripts.tests.test_eyecite_classify -v`
Expected: `ModuleNotFoundError: No module named 'eyecite_classify'` (all 8 tests error out).

- [ ] **Step 5: Implement `eyecite_classify.py`**

Create `docs/scripts/eyecite_classify.py`:
```python
"""Thin wrapper around eyecite (Free Law Project) for classifying
citation text -- see
docs/superpowers/specs/2026-07-26-citation-standardization-design.md
Section 5 for eyecite's three confirmed roles in this project
(validator, extraction aid, explicit-flagging mechanism). Must be run
via .venv-eyecite/bin/python3, not the bare system python3 every other
script in this repo uses -- eyecite has no apt package, unlike lxml."""

from eyecite import get_citations
from eyecite.models import FullCaseCitation, FullLawCitation


def classify_citation_text(text):
    """dict with keys role ("case"/"statute"/None), resolved (bool),
    parsed (the matched citation string or None). Only a FullCaseCitation
    or FullLawCitation counts as resolved -- eyecite's own UnknownCitation
    (a citation-shaped fragment it can't confidently type, e.g. a bare
    section symbol in webpage-title noise) is deliberately treated as
    unresolved, not a weak positive.

    Guards empty/whitespace-only text before calling eyecite:
    eyecite.get_citations("") itself raises ValueError ("Both
    `markup_text` and `plain_text` are empty" -- confirmed 2026-07-26 by
    reading eyecite/models.py Document.__post_init__), but this
    function's contract is to always return a dict, never raise, for
    any string input.

    When text contains more than one resolvable citation, returns the
    first Full{Case,Law}Citation encountered in document order (eyecite
    preserves text order) -- not a list, and not a "most significant"
    ranking.
    """
    if not text or not text.strip():
        return {"role": None, "resolved": False, "parsed": None}
    citations = get_citations(text)
    for citation in citations:
        if isinstance(citation, FullCaseCitation):
            return {"role": "case", "resolved": True, "parsed": citation.corrected_citation()}
        if isinstance(citation, FullLawCitation):
            return {"role": "statute", "resolved": True, "parsed": citation.corrected_citation()}
    return {"role": None, "resolved": False, "parsed": None}
```

- [ ] **Step 6: Run the tests to verify they pass**

Run: `.venv-eyecite/bin/python3 -m unittest docs.scripts.tests.test_eyecite_classify -v`
Expected: all 8 `PASS`.

- [ ] **Step 7: Commit**

```bash
git add .gitignore docs/scripts/eyecite_classify.py docs/scripts/tests/test_eyecite_classify.py
git commit -m "feat: add eyecite-based citation classification wrapper (venv-installed, no apt package exists for it)"
```

---

## Self-Review

**1. Spec coverage:** Design doc Section 5's three eyecite roles (validator, extraction aid,
explicit-flagging) are consumed by later tasks (4, pilot), not this one -- this task's job is only
to produce the classification primitive they'll call, which it does
(`classify_citation_text`). Interface signature matches exactly what the brief's "Interfaces"
block promises. Covered.

**2. Placeholder scan:** No TBD/TODO, every step has real code, no "similar to Task N" references.

**3. Type consistency:** `classify_citation_text(text) -> dict` with keys `role`/`resolved`/`parsed`
is the only interface this task produces, used consistently across all 8 tests and the
implementation. No signature drift.

**4. Deviation from the brief, and why:** Added two tests not in the brief's example
(`test_full_law_citation_resolves_as_statute`, and the empty/whitespace/prose/multi-citation
tests) plus an explicit empty-string guard in the implementation not present in the brief's example
code. The brief's own example code, if implemented verbatim, would let
`classify_citation_text("")` crash with an uncaught `ValueError` from inside eyecite -- confirmed
by direct testing before writing this plan (see "Pre-implementation verification" above). Since
the interface contract implies a dict is always returned, this is a correction, not scope creep.

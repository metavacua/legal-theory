# Classify Numbered-Citation Documents (Task 5, Steps 1-5) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this
> plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `classify_from_audit_csv()`, a pure aggregation function that reads the existing
`docs/audits/footnote-citation-audit.csv` report and buckets each document into Category A
(mechanically convertible), Category B (needs-research), or `"ambiguous"` (needs a later live
Google Drive check), by majority vote of each file's per-footnote `confidence_tier` and `flags`
columns. Run it against the real corpus, report the counts, and write
`docs/bibliography/numbered-citation-classification.json` with every entry from
`classify_from_audit_csv()`'s result AS-IS (ambiguous entries included, unresolved, no `verified`
field on any entry since none are live-checked in this pass). Do NOT perform any live Google Drive
verification in this plan — resolving the ambiguous minority is explicitly out of scope, a separate
pass by another operator who has Drive access.

**Architecture:** One new module, `docs/scripts/classify_numbered_citations.py`, following this
codebase's established pattern (see `citation_entry.py`, `build_bibliography.py`,
`measure_citation_conformance.py`): `sys.path.insert` the script's own directory, then
`from convert_to_docbook import REPO_ROOT`. The module's only public function reads the CSV with
`csv.DictReader`, groups rows by the `file` column into a `dict[str, list[dict]]`, then reduces
each group to a single `{category, total_rows, high_count, degenerate_count}` record. A `main()`
prints corpus-wide counts. No new dependencies.

**Tech Stack:** Python 3 standard library only (`csv`, `unittest`, `pathlib`, `collections.defaultdict`).

## Global Constraints

- Majority threshold is strictly `> 0.5` (exact ties at 0.5 must fall through to `"ambiguous"`,
  never silently resolve to A or B) — verbatim from the brief's `_MAJORITY_THRESHOLD` design.
- `degenerate_bibliography` flag matching MUST be exact-flag matching against the `;`-delimited
  `flags` column, not a raw substring `in` check — the brief's own example uses substring `in`,
  which is a correctness gap the brief explicitly asks the implementer to check. Real corpus data
  today happens not to trigger it (verified: `degenerate_bibliography` never appears as a substring
  of a different flag name in the live CSV — the five non-empty flag combinations are
  `no_link_corroboration`, `possible_heading_collision`, `restart_detected`,
  `restart_detected;no_link_corroboration`, `degenerate_bibliography;no_link_corroboration`,
  `exceeds_length;degenerate_bibliography`), but the exact-match form is correct regardless of
  future flag names and costs nothing.
- `classify_from_audit_csv(csv_path) -> dict[str, dict]` is the exact required interface (per-file
  category `"A"`/`"B"`/`"ambiguous"` plus row counts) — this signature is depended on by the
  (out-of-scope-for-this-plan) manifest-writing step and any future corpus-wide conversion plan.
- Import `REPO_ROOT` from `convert_to_docbook` (this codebase's established convention — do not
  redefine `REPO_ROOT` locally).
- Scope hard-stops after Step 5 (real-corpus run + inspection of the ambiguous set). Do not write
  `docs/bibliography/numbered-citation-classification.json` and do not touch Google Drive tools in
  this plan — those steps belong to a separate, later pass by another operator.

---

## Task 1: `classify_from_audit_csv()` core aggregation, TDD

**Files:**
- Create: `docs/scripts/tests/test_classify_numbered_citations.py`
- Create: `docs/scripts/classify_numbered_citations.py`

**Interfaces:**
- Produces: `classify_from_audit_csv(csv_path) -> dict[str, dict]`, where each value has keys
  `category` (`"A"`/`"B"`/`"ambiguous"`), `total_rows` (int), `high_count` (int),
  `degenerate_count` (int).
- Produces: `REPO_ROOT` (re-exported from `convert_to_docbook`, used by the ground-truth test and
  by `main()`).
- Produces: `main(argv=None) -> int`, prints corpus-wide A/B/ambiguous counts.

- [ ] **Step 1: Write the failing tests**

Create `docs/scripts/tests/test_classify_numbered_citations.py`:

```python
import csv
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class TestClassifyFromAuditCsv(unittest.TestCase):
    def _write_csv(self, rows):
        out_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, out_dir)
        path = out_dir / "audit.csv"
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "file", "footnote_number", "body_context_snippet",
                "matched_works_cited_entry", "matched_works_cited_url",
                "confidence_tier", "flags",
            ])
            writer.writeheader()
            for row in rows:
                writer.writerow(row)
        return path

    def _row(self, file, confidence, flags=""):
        return {
            "file": file, "footnote_number": "1", "body_context_snippet": "x",
            "matched_works_cited_entry": "", "matched_works_cited_url": "",
            "confidence_tier": confidence, "flags": flags,
        }

    def test_majority_high_confidence_classifies_a(self):
        from classify_numbered_citations import classify_from_audit_csv
        csv_path = self._write_csv([
            self._row("doc1.html", "High"),
            self._row("doc1.html", "High"),
            self._row("doc1.html", "Medium"),
        ])
        result = classify_from_audit_csv(csv_path)
        self.assertEqual(result["doc1.html"]["category"], "A")

    def test_majority_degenerate_bibliography_classifies_b(self):
        from classify_numbered_citations import classify_from_audit_csv
        csv_path = self._write_csv([
            self._row("doc2.html", "Needs manual triage", "degenerate_bibliography"),
            self._row("doc2.html", "Needs manual triage", "degenerate_bibliography"),
            self._row("doc2.html", "High"),
        ])
        result = classify_from_audit_csv(csv_path)
        self.assertEqual(result["doc2.html"]["category"], "B")

    def test_mixed_signal_is_ambiguous(self):
        from classify_numbered_citations import classify_from_audit_csv
        csv_path = self._write_csv([
            self._row("doc3.html", "High"),
            self._row("doc3.html", "Needs manual triage", "degenerate_bibliography"),
        ])
        result = classify_from_audit_csv(csv_path)
        self.assertEqual(result["doc3.html"]["category"], "ambiguous")

    def test_exact_tie_at_half_is_ambiguous_not_a_or_b(self):
        """A 2-of-4 High-confidence split is exactly 0.5, not > 0.5 --
        the brief's own worked boundary case. Must NOT silently resolve
        to 'A'."""
        from classify_numbered_citations import classify_from_audit_csv
        csv_path = self._write_csv([
            self._row("doc4.html", "High"),
            self._row("doc4.html", "High"),
            self._row("doc4.html", "Medium"),
            self._row("doc4.html", "Medium"),
        ])
        result = classify_from_audit_csv(csv_path)
        self.assertEqual(result["doc4.html"]["category"], "ambiguous")

    def test_degenerate_bibliography_flag_matched_exactly_not_as_substring(self):
        """A flags value that merely CONTAINS 'degenerate_bibliography'
        as a substring of a different, longer flag name must not count
        toward the degenerate majority. Flags are ';'-joined tokens;
        matching must split and compare tokens exactly."""
        from classify_numbered_citations import classify_from_audit_csv
        csv_path = self._write_csv([
            self._row("doc5.html", "High", "not_degenerate_bibliography_at_all"),
            self._row("doc5.html", "High", "not_degenerate_bibliography_at_all"),
        ])
        result = classify_from_audit_csv(csv_path)
        self.assertEqual(result["doc5.html"]["degenerate_count"], 0)
        self.assertEqual(result["doc5.html"]["category"], "A")

    def test_real_audit_report_classifies_both_known_ground_truth_documents_correctly(self):
        """Anchors this classifier against the two documents this
        project's brainstorming already confirmed by hand via direct
        Google Drive comparison, 2026-07-26."""
        from classify_numbered_citations import classify_from_audit_csv, REPO_ROOT
        result = classify_from_audit_csv(REPO_ROOT / "docs" / "audits" / "footnote-citation-audit.csv")
        categorical = next(k for k in result if "categorical-systems" in k)
        prompts = next(k for k in result if "prompts-as-expression" in k)
        self.assertEqual(result[categorical]["category"], "A")
        self.assertEqual(result[prompts]["category"], "B")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python3 -m unittest docs.scripts.tests.test_classify_numbered_citations -v`
Expected: `ModuleNotFoundError: No module named 'classify_numbered_citations'` (all 6 tests error).

- [ ] **Step 3: Implement `classify_numbered_citations.py`**

Create `docs/scripts/classify_numbered_citations.py`. This differs from the brief's example in one
respect: `degenerate_count` is computed by splitting `flags` on `;` and comparing tokens exactly,
not via a raw substring `in` check, per the Global Constraints note above.

```python
"""Classifies documents matching the Deep-Research numbered-citation
pattern into Category A (works-cited list intact, safe for
convert_numbered_citations.py) or Category B (needs-research),
primarily from docs/audits/footnote-citation-audit.csv --
audit_footnote_links.py's own, already-computed report (7,667 rows) --
rather than re-researching every document from scratch via live Google
Drive comparison. Confirmed 2026-07-26: this correctly reproduces both
ground-truth classifications this project's brainstorming already
established by hand (llms-as-categorical-systems -> A,
prompts-as-expression -> B), and reduces live Drive verification to the
small minority of documents where the aggregate signal alone is mixed
("ambiguous"), not all ~96 candidates."""

import csv
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from convert_to_docbook import REPO_ROOT  # noqa: E402

_MAJORITY_THRESHOLD = 0.5
_DEGENERATE_FLAG = "degenerate_bibliography"


def classify_from_audit_csv(csv_path):
    """dict[str, dict]: audit CSV file path -> {category, total_rows,
    high_count, degenerate_count}. category is "A" when more than half
    the file's rows are High confidence, "B" when more than half are
    flagged degenerate_bibliography, "ambiguous" otherwise -- neither
    signal reaches a majority, so this needs a live Drive check. Every
    entry in by_file is populated by appending at least one row, so
    total_rows is always >= 1 here; there is no zero-row group to
    divide by."""
    by_file = defaultdict(list)
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            by_file[row["file"]].append(row)

    results = {}
    for file, rows in by_file.items():
        total = len(rows)
        high = sum(1 for r in rows if r["confidence_tier"] == "High")
        degenerate = sum(
            1 for r in rows
            if _DEGENERATE_FLAG in r["flags"].split(";")
        )
        if degenerate / total > _MAJORITY_THRESHOLD:
            category = "B"
        elif high / total > _MAJORITY_THRESHOLD:
            category = "A"
        else:
            category = "ambiguous"
        results[file] = {
            "category": category, "total_rows": total,
            "high_count": high, "degenerate_count": degenerate,
        }
    return results


def main(argv=None):
    results = classify_from_audit_csv(REPO_ROOT / "docs" / "audits" / "footnote-citation-audit.csv")
    counts = defaultdict(int)
    for r in results.values():
        counts[r["category"]] += 1
    print(f"Classified {len(results)} documents from the existing audit report:")
    print(f"  Category A (mechanically convertible): {counts['A']}")
    print(f"  Category B (needs-research): {counts['B']}")
    print(f"  Ambiguous (needs live Drive verification): {counts['ambiguous']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python3 -m unittest docs.scripts.tests.test_classify_numbered_citations -v`
Expected: all 6 `PASS`, including the real ground-truth anchor test, the exact-tie boundary test,
and the exact-vs-substring flag matching test.

- [ ] **Step 5: Commit**

```bash
git add docs/scripts/classify_numbered_citations.py docs/scripts/tests/test_classify_numbered_citations.py
git commit -m "feat: classify numbered-citation documents into Category A/B/ambiguous from the existing footnote-citation-audit.csv report"
```

## Task 2: Run against the real corpus and record the ambiguous set

**Files:** none created; this task runs Task 1's `classify_numbered_citations.py` as a script and
records its output for the (separate, out-of-scope) manifest-writing pass.

**Interfaces:**
- Consumes: `classify_from_audit_csv` from Task 1.

- [ ] **Step 1: Run against the real corpus**

```bash
python3 docs/scripts/classify_numbered_citations.py
```
Expected output shape (brief's 2026-07-26 numbers; re-verify against the corpus state at execution
time since it may have changed — do not silently reconcile a mismatch, note it):
```
Classified 95 documents from the existing audit report:
  Category A (mechanically convertible): 71
  Category B (needs-research): 12
  Ambiguous (needs live Drive verification): 12
```

- [ ] **Step 2: List the ambiguous file names for the record (no Drive calls)**

```bash
python3 -c "
import sys, json
sys.path.insert(0, 'docs/scripts')
from classify_numbered_citations import classify_from_audit_csv, REPO_ROOT
results = classify_from_audit_csv(REPO_ROOT / 'docs' / 'audits' / 'footnote-citation-audit.csv')
ambiguous = {k: v for k, v in results.items() if v['category'] == 'ambiguous'}
print(json.dumps(list(ambiguous.keys()), indent=2))
"
```
Record this list verbatim in the task report so the controller can pick it up for live Drive
verification in a separate pass. Do not attempt to resolve any of these here.

## Task 3: Write the manifest, as-is (no Drive verification)

**Files:**
- Create: `docs/bibliography/numbered-citation-classification.json`

**Interfaces:**
- Consumes: `classify_from_audit_csv` from Task 1.

- [ ] **Step 1: Write every result entry to the manifest, unresolved**

Per the task brief's Step 6 manifest shape, minus the live-verification overwrite: every file gets
its CSV-derived `category` (`"A"`, `"B"`, or `"ambiguous"`) plus `total_rows`, `high_count`,
`degenerate_count`, exactly as `classify_from_audit_csv` returns them. No entry gets a `verified`
field in this pass, since none were individually Drive-checked (that field is reserved for the
controller's later pass, which will overwrite the ambiguous subset with a live-verified `"A"`/`"B"`
and add `verified: "<date>"` to exactly those entries).

```bash
python3 -c "
import sys, json
sys.path.insert(0, 'docs/scripts')
from classify_numbered_citations import classify_from_audit_csv, REPO_ROOT
results = classify_from_audit_csv(REPO_ROOT / 'docs' / 'audits' / 'footnote-citation-audit.csv')
out_path = REPO_ROOT / 'docs' / 'bibliography' / 'numbered-citation-classification.json'
with out_path.open('w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, sort_keys=True)
    f.write('\n')
print(f'Wrote {len(results)} entries to {out_path}')
"
```

- [ ] **Step 2: Sanity-check the manifest against the classifier's own run output**

```bash
python3 -c "
import json
from collections import Counter
data = json.load(open('docs/bibliography/numbered-citation-classification.json'))
counts = Counter(v['category'] for v in data.values())
print(f'{len(data)} documents in manifest')
print(dict(counts))
assert 'verified' not in next(iter(data.values())), 'no entries should carry verified in this pass'
"
```
Expected: document count and A/B/ambiguous counts match Task 2 Step 1's run exactly (same source
data, same function, no live-verification overwrite applied yet).

- [ ] **Step 3: Commit**

```bash
git add docs/bibliography/numbered-citation-classification.json
git commit -m "feat: write numbered-citation classification manifest from the audit-CSV aggregate (ambiguous entries unresolved, pending live Drive verification)"
```

---

**Explicitly out of scope for this plan (belongs to the controller's separate pass):**
- Any Google Drive search/read to resolve `"ambiguous"` entries.
- Overwriting ambiguous manifest entries with a live-verified `"A"`/`"B"` outcome and a `verified`
  date field.
- Step 7 (internal-consistency check requiring 0 ambiguous) from the task brief — by design this
  plan's manifest still contains ambiguous entries, so that check would fail until the controller's
  pass resolves them; do not run it here as a completion gate.

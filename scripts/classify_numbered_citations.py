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
    divide by. The flags column is ';'-joined tokens (e.g.
    "exceeds_length;degenerate_bibliography"); degenerate matching
    splits on ';' and compares tokens exactly, rather than a raw
    substring check, so a hypothetical future flag whose name merely
    contains "degenerate_bibliography" as a substring (e.g. something
    like "not_degenerate_bibliography") would not be miscounted."""
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

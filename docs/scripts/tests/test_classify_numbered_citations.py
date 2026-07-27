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

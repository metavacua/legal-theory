import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "footnote_audit"


class TestDocumentContentFiles(unittest.TestCase):
    def test_resolves_document_order_including_a_nested_include(self):
        from audit_footnote_links import document_content_files
        shell = FIXTURES / "doc_order" / "shell.xml"
        files = document_content_files(shell)
        names = [f.name for f in files]
        self.assertEqual(names, ["shell.xml", "01-frag-a.xml", "frag-a-nested.xml", "02-frag-b.xml"])


class TestFindCandidates(unittest.TestCase):
    def test_finds_real_footnotes_only_not_title_pincite_or_rule_label(self):
        from audit_footnote_links import find_candidates
        candidates = find_candidates(FIXTURES / "candidates_sample.xml")
        numbers = [c.number for c in candidates]
        self.assertEqual(numbers, [4, 12])

    def test_context_captures_text_around_the_marker(self):
        from audit_footnote_links import find_candidates
        candidates = find_candidates(FIXTURES / "candidates_sample.xml")
        self.assertIn("Dynamex", candidates[0].context)

    def test_ordinary_prose_use_of_rule_word_is_not_mistaken_for_a_label(self):
        # Adversarial: "the Common Rule" is a real named federal
        # regulation (45 CFR 46), not a numbering-label reference like
        # "Rule 2.3" -- the word "Rule" alone immediately before a
        # footnote marker must not exclude a real footnote.
        from audit_footnote_links import find_candidates
        candidates = find_candidates(FIXTURES / "rule_word_sample.xml")
        numbers = [c.number for c in candidates]
        self.assertEqual(numbers, [44])


if __name__ == "__main__":
    unittest.main()

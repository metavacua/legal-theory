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


class TestLocateWorksCited(unittest.TestCase):
    def test_finds_entries_in_whichever_fragment_has_them(self):
        from audit_footnote_links import document_content_files, locate_works_cited
        files = document_content_files(FIXTURES / "works_cited_doc" / "shell.xml")
        entries = locate_works_cited(files)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0][1], "https://example.com/a")

    def test_empty_when_no_works_cited_section_present(self):
        from audit_footnote_links import document_content_files, locate_works_cited
        files = document_content_files(FIXTURES / "doc_order" / "shell.xml")
        self.assertEqual(locate_works_cited(files), [])


class TestIsDegenerate(unittest.TestCase):
    def test_single_linkless_entry_against_many_footnotes_is_degenerate(self):
        from audit_footnote_links import is_degenerate
        entries = [("Bare Title With No Link", None)]
        self.assertTrue(is_degenerate(entries, max_footnote=72))

    def test_well_populated_linked_list_is_not_degenerate(self):
        from audit_footnote_links import is_degenerate
        entries = [(f"Source {i}", f"https://example.com/{i}") for i in range(1, 11)]
        self.assertFalse(is_degenerate(entries, max_footnote=10))


class TestIsInsideHeading(unittest.TestCase):
    def test_body_paragraph_marker_is_not_inside_a_heading(self):
        from audit_footnote_links import is_inside_heading
        self.assertFalse(is_inside_heading(FIXTURES / "html_check" / "doc.html", ".4"))

    def test_heading_number_is_inside_a_heading(self):
        from audit_footnote_links import is_inside_heading
        self.assertTrue(is_inside_heading(FIXTURES / "html_check" / "doc.html", "2.1"))


class TestAuditDocument(unittest.TestCase):
    def test_audits_a_full_document_end_to_end(self):
        from audit_footnote_links import audit_document, build_backlink_map
        root = FIXTURES / "full_doc"
        shell = root / "shell.xml"
        backlinks = build_backlink_map(root)
        result = audit_document(shell, backlinks)

        self.assertEqual(len(result.candidates), 1)
        self.assertEqual(result.candidates[0].number, 4)
        self.assertEqual(len(result.works_cited), 4)
        self.assertFalse(result.degenerate)
        self.assertTrue(result.shell_html.endswith("full_doc/shell.html"))

    def test_heading_collision_is_flagged_not_dropped(self):
        # Adversarial: the marker text also happens to appear inside an
        # unrelated heading. It must survive into audit.candidates with
        # heading_collision=True -- NOT silently disappear. A dropped
        # candidate is invisible to the human reviewer, which is a worse
        # failure than a flagged one per this plan's own Global Constraints.
        from audit_footnote_links import audit_document, build_backlink_map
        root = FIXTURES / "full_doc_collision"
        shell = root / "shell.xml"
        backlinks = build_backlink_map(root)
        result = audit_document(shell, backlinks)

        self.assertEqual(len(result.candidates), 1)
        self.assertEqual(result.candidates[0].number, 9)
        self.assertTrue(result.candidates[0].heading_collision)


if __name__ == "__main__":
    unittest.main()

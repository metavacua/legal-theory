import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "bibliography" / "encoding_corpus"


class TestFindForbiddenC1Codepoints(unittest.TestCase):
    def test_clean_text_has_no_hits(self):
        from check_bibliography_encoding import find_forbidden_c1_codepoints
        self.assertEqual(find_forbidden_c1_codepoints("How Transformers solve tasks"), [])

    def test_detects_single_c1_control_codepoint_and_its_offset(self):
        from check_bibliography_encoding import find_forbidden_c1_codepoints
        text = "AB\x97CD"
        self.assertEqual(find_forbidden_c1_codepoints(text), [(2, 0x97)])

    def test_detects_the_real_huggingface_corruption_pattern(self):
        """The exact 4-codepoint wreckage a Latin-1-vs-UTF-8 double-decode
        of U+1F917 (the HuggingFace emoji) leaves behind: U+00F0, U+009F,
        U+00A4, U+0097. Only the two C1 controls (U+009F, U+0097) are
        forbidden; U+00F0 (eth) and U+00A4 (currency sign) are ordinary,
        legal Latin-1 Supplement characters and must not be flagged."""
        from check_bibliography_encoding import find_forbidden_c1_codepoints
        text = "How ð¤ Transformers solve tasks"
        hits = find_forbidden_c1_codepoints(text)
        self.assertEqual([cp for _, cp in hits], [0x9F, 0x97])

    def test_boundary_codepoints_0x80_and_0x9f_are_both_detected(self):
        from check_bibliography_encoding import find_forbidden_c1_codepoints
        text = "\x80\x9f"
        self.assertEqual(find_forbidden_c1_codepoints(text), [(0, 0x80), (1, 0x9F)])

    def test_neighbors_just_outside_the_c1_block_are_not_flagged(self):
        """0x7F (DEL) sits directly below the C1 block; 0xA0 (NBSP) sits
        directly above it. Neither is a C1 control and neither must be
        flagged -- guards the range boundary isn't off-by-one."""
        from check_bibliography_encoding import find_forbidden_c1_codepoints
        text = "\x7f\xa0"
        self.assertEqual(find_forbidden_c1_codepoints(text), [])


class TestCheckEntryFile(unittest.TestCase):
    def test_clean_fixture_file_has_no_violations(self):
        from check_bibliography_encoding import check_entry_file
        self.assertEqual(check_entry_file(FIXTURES / "clean.xml"), [])

    def test_corrupted_fixture_file_is_flagged_with_path_and_codepoint(self):
        from check_bibliography_encoding import check_entry_file
        violations = check_entry_file(FIXTURES / "corrupted.xml")
        self.assertEqual(len(violations), 1)
        self.assertIn(str(FIXTURES / "corrupted.xml"), violations[0])
        self.assertIn("U+0097", violations[0])


class TestCheckEntriesDir(unittest.TestCase):
    def test_scans_every_xml_file_in_the_directory(self):
        from check_bibliography_encoding import check_entries_dir
        violations = check_entries_dir(FIXTURES)
        self.assertEqual(len(violations), 1)
        self.assertIn("corrupted.xml", violations[0])


class TestRealCorpusBibliographyEntries(unittest.TestCase):
    def test_no_forbidden_c1_codepoints_in_committed_entries(self):
        """The actual regression guard: every bibliography entry file
        committed to the repo must be free of C1 control codepoints.
        Written to catch the exact defect confirmed in
        docs/bibliography/entries/huggingface-5.xml (a Latin-1-vs-UTF-8
        double-decode of the HuggingFace emoji) -- see
        scripts/check_bibliography_encoding.py's module docstring."""
        from check_bibliography_encoding import check_entries_dir, ENTRIES_DIR
        violations = check_entries_dir(ENTRIES_DIR)
        self.assertEqual(violations, [])


if __name__ == "__main__":
    unittest.main()

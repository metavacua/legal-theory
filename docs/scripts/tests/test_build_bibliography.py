import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "bibliography"


class TestBuildBacklinkMap(unittest.TestCase):
    def test_maps_shell_and_its_fragment_to_shells_html(self):
        from build_bibliography import build_backlink_map
        root = FIXTURES / "backlink_corpus"
        backlinks = build_backlink_map(root)

        shell_a = (root / "shell-a.xml").resolve()
        frag_a = (root / "shell-a" / "01-frag.xml").resolve()
        shell_b = (root / "shell-b.xml").resolve()

        self.assertTrue(backlinks[shell_a].endswith("backlink_corpus/shell-a.html"))
        self.assertEqual(backlinks[frag_a], backlinks[shell_a])
        self.assertTrue(backlinks[shell_b].endswith("backlink_corpus/shell-b.html"))


class TestExtractWorksCited(unittest.TestCase):
    def test_extracts_text_and_link_skips_garbled_no_link_entry_correctly(self):
        from build_bibliography import extract_works_cited
        entries = extract_works_cited(FIXTURES / "works_cited_sample.xml")
        self.assertEqual(len(entries), 3)
        self.assertEqual(entries[0], ("Systemic_Misclassification", None))
        self.assertIn("California Civil Code § 1550 (2024) - Justia Law", entries[1][0])
        self.assertEqual(
            entries[1][1],
            "https://law.justia.com/codes/california/code-civ/division-3/part-2/title-1/chapter-1/section-1550/",
        )

    def test_link_inner_text_excluded_but_surrounding_text_kept(self):
        from build_bibliography import extract_works_cited
        entries = extract_works_cited(FIXTURES / "works_cited_sample.xml")
        text, href = entries[2]
        self.assertEqual(text, "Before-text after-text")
        self.assertEqual(href, "https://example.com/x")


if __name__ == "__main__":
    unittest.main()

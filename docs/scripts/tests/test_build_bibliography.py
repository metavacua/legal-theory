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


class TestExtractAllRawEntries(unittest.TestCase):
    def test_extracts_from_fragment_and_skips_excluded_dir(self):
        from build_bibliography import extract_all_raw_entries
        root = FIXTURES / "mini_corpus"
        entries = extract_all_raw_entries(root, exclude_dirs={"excluded"})

        self.assertEqual(len(entries), 1)
        entry = entries[0]
        self.assertEqual(entry.href, "https://example.com/a")
        self.assertTrue(entry.citing_html.endswith("mini_corpus/doc-one.html"))
        self.assertTrue(entry.source_file.endswith("doc-one/01-works-cited.xml"))


class TestNormalizeUrl(unittest.TestCase):
    def test_strips_trailing_slash(self):
        from build_bibliography import normalize_url
        self.assertEqual(normalize_url("https://onellp.com/"), "https://onellp.com")

    def test_lowercases_scheme_and_host_but_not_path(self):
        from build_bibliography import normalize_url
        self.assertEqual(
            normalize_url("HTTPS://Justia.COM/Codes/CA-Civ-1550"),
            "https://justia.com/Codes/CA-Civ-1550",
        )

    def test_preserves_www_prefix_as_is(self):
        # Adversarial: two DIFFERENT hosts (www vs bare) must NOT collide —
        # normalizing away "www." would incorrectly merge them.
        from build_bibliography import normalize_url
        self.assertNotEqual(
            normalize_url("https://www.jmbm.com/entertainment.html"),
            normalize_url("https://jmbm.com/entertainment.html"),
        )

    def test_trailing_slash_and_case_variant_dedup_to_same_key(self):
        from build_bibliography import normalize_url
        self.assertEqual(
            normalize_url("https://Justia.com/x/"),
            normalize_url("https://justia.com/x"),
        )


class TestAccessDate(unittest.TestCase):
    def test_extracts_accessed_date(self):
        from build_bibliography import extract_access_date
        text = "California Civil Code § 1550 (2024) - Justia Law, accessed September 19, 2025,"
        self.assertEqual(extract_access_date(text), "September 19, 2025")

    def test_returns_none_when_absent(self):
        from build_bibliography import extract_access_date
        self.assertIsNone(extract_access_date("No date marker here at all."))

    def test_strip_removes_accessed_clause_and_trims_punctuation(self):
        from build_bibliography import strip_access_date
        text = "Justia Law, accessed September 19, 2025,"
        self.assertEqual(strip_access_date(text), "Justia Law")

    def test_strip_preserves_unrelated_trailing_punctuation_when_clause_is_mid_string(self):
        from build_bibliography import strip_access_date
        text = "Cal. Civ. Code § 1550, accessed September 19, 2025, additional note."
        self.assertEqual(strip_access_date(text), "Cal. Civ. Code § 1550 additional note.")

    def test_does_not_match_accessed_inside_a_compound_word(self):
        from build_bibliography import strip_access_date
        text = "First accessed January 1, 2020, then re-accessed September 19, 2025,"
        self.assertEqual(strip_access_date(text), "First then re-accessed September 19, 2025,")


if __name__ == "__main__":
    unittest.main()

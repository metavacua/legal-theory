import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class TestScaffold(unittest.TestCase):
    def test_module_importable(self):
        import convert_to_docbook  # noqa: F401


class TestSlugifyAndTitle(unittest.TestCase):
    def test_slugify_basic(self):
        from convert_to_docbook import slugify
        self.assertEqual(slugify("A Flat Document"), "a-flat-document")

    def test_slugify_leading_digit_gets_prefixed(self):
        from convert_to_docbook import slugify
        self.assertEqual(slugify("1. First Section"), "s-1-first-section")

    def test_slugify_empty_string(self):
        from convert_to_docbook import slugify
        self.assertEqual(slugify(""), "s")

    def test_extract_title_reads_first_heading(self):
        from convert_to_docbook import extract_title
        fixtures = Path(__file__).resolve().parent / "fixtures"
        self.assertEqual(extract_title(fixtures / "flat.md"), "A Flat Document")

    def test_extract_title_falls_back_to_filename(self):
        from convert_to_docbook import extract_title
        fixtures = Path(__file__).resolve().parent / "fixtures"
        no_heading = fixtures / "no_heading.md"
        no_heading.write_text("Just a paragraph, no heading.\n", encoding="utf-8")
        self.assertEqual(extract_title(no_heading), "No Heading")
        no_heading.unlink()


if __name__ == "__main__":
    unittest.main()

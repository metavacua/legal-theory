import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

DB_NS = "{http://docbook.org/ns/docbook}"


def _parse(xml_text):
    return ET.fromstring(xml_text)


class TestConvertCitedTitles(unittest.TestCase):
    def test_bare_emphasis_matching_a_known_title_becomes_citetitle(self):
        from convert_cited_titles_to_citetitle import convert_cited_titles
        root = _parse(
            '<para xmlns="http://docbook.org/ns/docbook">The novel '
            '<emphasis>Test Title</emphasis> was cited.</para>'
        )
        n = convert_cited_titles(root, {"Test Title"})
        self.assertEqual(n, 1)
        self.assertIsNone(root.find(f"{DB_NS}emphasis"))
        citetitle = root.find(f"{DB_NS}citetitle")
        self.assertIsNotNone(citetitle)
        self.assertEqual(citetitle.text, "Test Title")
        self.assertEqual(citetitle.tail, " was cited.")

    def test_emphasis_with_a_role_attribute_is_never_touched_even_if_text_matches(self):
        from convert_cited_titles_to_citetitle import convert_cited_titles
        root = _parse(
            '<para xmlns="http://docbook.org/ns/docbook">'
            '<emphasis role="bold">Test Title</emphasis> intro label.'
            '</para>'
        )
        n = convert_cited_titles(root, {"Test Title"})
        self.assertEqual(n, 0)
        emphasis = root.find(f"{DB_NS}emphasis")
        self.assertIsNotNone(emphasis)
        self.assertEqual(emphasis.get("role"), "bold")

    def test_bare_emphasis_not_matching_any_known_title_is_left_untouched(self):
        from convert_cited_titles_to_citetitle import convert_cited_titles
        root = _parse(
            '<para xmlns="http://docbook.org/ns/docbook">'
            '<emphasis>Some Other Phrase</emphasis>'
            '</para>'
        )
        n = convert_cited_titles(root, {"Test Title"})
        self.assertEqual(n, 0)
        self.assertIsNotNone(root.find(f"{DB_NS}emphasis"))
        self.assertIsNone(root.find(f"{DB_NS}citetitle"))

    def test_real_target_file_shape_converts_exactly_three_and_spares_the_bold_labels(self):
        # Reproduces the real structure of
        # docs/papers/ai_and_ip/llm-database-theory/src/01-llm-database-theory/
        # 04-the-basis-limitation-outputs-cannot-exceed-inputs.xml.
        from convert_cited_titles_to_citetitle import convert_cited_titles
        root = _parse(
            '<section xmlns="http://docbook.org/ns/docbook" xml:id="basis-limitation">'
            '<para>...text of <emphasis>Harry Potter</emphasis>, that text...</para>'
            '<para><emphasis role="bold">Text (Cooper et al. 2025):</emphasis> '
            '...the first <emphasis>Harry Potter</emphasis> novel and '
            "Orwell's <emphasis>Nineteen Eighty-Four</emphasis>. ...</para>"
            '</section>'
        )
        n = convert_cited_titles(root, {"Harry Potter", "Nineteen Eighty-Four"})
        self.assertEqual(n, 3)
        self.assertEqual(len(root.findall(f".//{DB_NS}citetitle")), 3)
        remaining_bold = root.findall(f".//{DB_NS}emphasis")
        self.assertEqual(len(remaining_bold), 1)
        self.assertEqual(remaining_bold[0].get("role"), "bold")


if __name__ == "__main__":
    unittest.main()

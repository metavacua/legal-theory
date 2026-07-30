import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

DB_NS = "{http://docbook.org/ns/docbook}"


def _parse(xml_text):
    return ET.fromstring(xml_text)


class TestConvertInlineEmphasis(unittest.TestCase):
    def test_para_containing_bold_converts_to_emphasis_strong(self):
        from convert_markdown_remnants import convert_inline_emphasis
        root = _parse(
            '<section xmlns="http://docbook.org/ns/docbook">'
            '<para>This is **bold** text.</para>'
            '</section>'
        )
        n = convert_inline_emphasis(root)
        self.assertEqual(n, 1)
        para = root.find(f"{DB_NS}para")
        self.assertEqual(para.text, "This is ")
        emphasis = para.find(f"{DB_NS}emphasis")
        self.assertIsNotNone(emphasis)
        self.assertEqual(emphasis.get("role"), "strong")
        self.assertEqual(emphasis.text, "bold")
        self.assertEqual(emphasis.tail, " text.")
        self.assertNotIn("*", "".join(para.itertext()))

    def test_entry_containing_italic_converts_to_plain_emphasis(self):
        from convert_markdown_remnants import convert_inline_emphasis
        root = _parse(
            '<section xmlns="http://docbook.org/ns/docbook">'
            '<informaltable><tgroup cols="1"><tbody><row>'
            '<entry>a *italic* word</entry>'
            '</row></tbody></tgroup></informaltable>'
            '</section>'
        )
        n = convert_inline_emphasis(root)
        self.assertEqual(n, 1)
        entry = root.find(f".//{DB_NS}entry")
        emphasis = entry.find(f"{DB_NS}emphasis")
        self.assertIsNotNone(emphasis)
        self.assertIsNone(emphasis.get("role"))
        self.assertEqual(emphasis.text, "italic")

    def test_non_emphasis_footnote_style_asterisks_are_left_untouched(self):
        # Real corpus text (docs/bibliography/references.xml): "Alan
        # Schwartz* & Robert E. Scott**" -- footnote-style author-name
        # asterisks from a quoted academic paper title, NOT markdown
        # emphasis. Neither asterisk has a matching partner, so
        # CommonMark (and therefore pandoc) leaves both as literal
        # text; this must not be corrupted.
        from convert_markdown_remnants import convert_inline_emphasis
        text = "Alan Schwartz* & Robert E. Scott** I.INTRODUCTION."
        root = _parse(
            '<section xmlns="http://docbook.org/ns/docbook">'
            f'<para>{text.replace("&", "&amp;")}</para>'
            '</section>'
        )
        n = convert_inline_emphasis(root)
        self.assertEqual(n, 0)
        para = root.find(f"{DB_NS}para")
        self.assertEqual(para.text, text)
        self.assertEqual(list(para), [])


class TestConvertRawTables(unittest.TestCase):
    def _table_fixture(self):
        return _parse(
            '<section xmlns="http://docbook.org/ns/docbook">'
            '<para>Intro paragraph.</para>'
            '<para>| | |</para>'
            '<para>| :-: | :-: |</para>'
            '<para>| Col A | Col B |</para>'
            '<para>| **bold cell** | plain cell |</para>'
            '<para>Outro paragraph.</para>'
            '</section>'
        )

    def test_raw_pipe_table_paragraph_sequence_converts_to_informaltable(self):
        from convert_markdown_remnants import convert_raw_tables
        root = self._table_fixture()
        n = convert_raw_tables(root)
        self.assertEqual(n, 1)
        tags = [c.tag for c in root]
        self.assertEqual(tags, [f"{DB_NS}para", f"{DB_NS}informaltable", f"{DB_NS}para"])
        table = list(root)[1]
        rows = table.findall(f".//{DB_NS}row")
        self.assertEqual(len(rows), 2)
        first_entry_of_second_row = rows[1].findall(f"{DB_NS}entry")[0]
        emphasis = first_entry_of_second_row.find(f"{DB_NS}emphasis")
        self.assertIsNotNone(emphasis)
        self.assertEqual(emphasis.get("role"), "strong")
        self.assertEqual(emphasis.text, "bold cell")


if __name__ == "__main__":
    unittest.main()

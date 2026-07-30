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

    def test_triple_asterisk_becomes_nested_italic_wrapping_bold(self):
        from convert_markdown_remnants import convert_inline_emphasis
        root = _parse(
            '<section xmlns="http://docbook.org/ns/docbook">'
            '<para>***Borello***</para>'
            '</section>'
        )
        convert_inline_emphasis(root)
        para = root.find(f"{DB_NS}para")
        outer = para.find(f"{DB_NS}emphasis")
        self.assertIsNone(outer.get("role"))
        inner = outer.find(f"{DB_NS}emphasis")
        self.assertEqual(inner.get("role"), "strong")
        self.assertEqual(inner.text, "Borello")

    def test_span_after_a_nested_existing_emphasis_tail_converts(self):
        # Regression fixture reproducing the real corpus shape found in
        # docs/court-record/theory/federal-constitutional/existing-doctrine/
        # first-amendment-landmark-cases-research/01-...xml: a <title>
        # with an ALREADY-correct nested <emphasis> whose .tail still
        # holds raw, unconverted "**...**" text.
        from convert_markdown_remnants import convert_inline_emphasis
        root = _parse(
            '<section xmlns="http://docbook.org/ns/docbook">'
            '<title><emphasis role="strong">Case Analysis:</emphasis> '
            '<emphasis><emphasis role="strong">Gitlow v. New York</emphasis>'
            '</emphasis>**, 268 U.S. 652 (1925)**</title>'
            '</section>'
        )
        n = convert_inline_emphasis(root)
        self.assertEqual(n, 1)
        title = root.find(f"{DB_NS}title")
        emphases = title.findall(f"{DB_NS}emphasis")
        self.assertEqual(len(emphases), 3)
        new_one = emphases[-1]
        self.assertEqual(new_one.get("role"), "strong")
        self.assertEqual(new_one.text, ", 268 U.S. 652 (1925)")
        self.assertNotIn("*", "".join(title.itertext()))

    def test_multiple_spans_in_one_run_all_convert(self):
        from convert_markdown_remnants import convert_inline_emphasis
        root = _parse(
            '<section xmlns="http://docbook.org/ns/docbook">'
            '<para>**one** and *two* and **three**</para>'
            '</section>'
        )
        convert_inline_emphasis(root)
        para = root.find(f"{DB_NS}para")
        children = list(para)
        self.assertEqual(len(children), 3)
        self.assertEqual([c.text for c in children], ["one", "two", "three"])
        self.assertEqual([c.get("role") for c in children], ["strong", None, "strong"])

    def test_is_idempotent_on_a_second_run(self):
        from convert_markdown_remnants import convert_inline_emphasis
        root = _parse(
            '<section xmlns="http://docbook.org/ns/docbook">'
            '<para>This is **bold** text.</para>'
            '</section>'
        )
        convert_inline_emphasis(root)
        first_pass_xml = ET.tostring(root)
        n_second = convert_inline_emphasis(root)
        self.assertEqual(n_second, 0)
        self.assertEqual(ET.tostring(root), first_pass_xml)


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

import io
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from contextlib import redirect_stdout
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

    def test_stray_asterisk_next_to_a_bare_url_does_not_crash(self):
        # Real corpus text (docs/bibliography/references.xml): a
        # citation entry with a stray, non-emphasis "*" (footnote-
        # marker-shaped, same family as the Schwartz/Scott case) in the
        # same run as a bare URL. GFM autolinks bare URLs into a real
        # <link xlink:href="..."> element -- pandoc emits that
        # regardless of whether the stray "*" ends up converted, so
        # _pandoc_inline_fragment's own wrapper element must declare
        # the xlink namespace, not just the default DocBook one, or
        # ET.fromstring raises "unbound prefix" before this function
        # ever reaches its own safety checks. Confirmed live: this
        # crashed main() on the real corpus during the first live
        # --check-free run, on exactly this shape of text.
        from convert_markdown_remnants import convert_inline_emphasis
        text = (
            'csun.edu. "Contract* What is an Acceptance?" '
            "Accessed September 19, 2025. "
            "https://www.csun.edu/sites/default/files/blawaccept.pdf"
        )
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

    def test_pipe_paragraphs_without_an_alignment_row_are_not_converted(self):
        from convert_markdown_remnants import convert_raw_tables
        root = _parse(
            '<section xmlns="http://docbook.org/ns/docbook">'
            '<para>| Type | SSI | CalFresh |</para>'
            '<para>| Direct Cash Gift | High Risk | High Risk |</para>'
            '</section>'
        )
        n = convert_raw_tables(root)
        self.assertEqual(n, 0)
        self.assertEqual([c.tag for c in root], [f"{DB_NS}para", f"{DB_NS}para"])

    def test_headerless_table_blank_first_row_produces_no_thead(self):
        # Reproduces the exact structural shape of 3 of the 5 real
        # corpus tables (e.g. potential-service-contracts-in-google):
        # a blank first row is pandoc/GFM's own convention for "this
        # table has no header" -- see the design doc's Design Notes.
        from convert_markdown_remnants import convert_raw_tables
        root = self._table_fixture()
        convert_raw_tables(root)
        table = root.find(f"{DB_NS}informaltable")
        self.assertIsNone(table.find(f".//{DB_NS}thead"))
        rows = table.findall(f".//{DB_NS}row")
        self.assertEqual(len(rows), 2)

    def test_real_header_table_produces_a_thead(self):
        # The OTHER real structural variant (e.g. from-clay-tablets-
        # to-blockchains-final/02-introduction.xml): a genuine,
        # non-blank header row. Must produce a real <thead>, not be
        # forced into the headerless shape.
        from convert_markdown_remnants import convert_raw_tables
        root = _parse(
            '<section xmlns="http://docbook.org/ns/docbook">'
            '<para>| Era | Innovation |</para>'
            '<para>| :--- | :--- |</para>'
            '<para>| Ancient | Grain Bonds |</para>'
            '</section>'
        )
        convert_raw_tables(root)
        table = root.find(f"{DB_NS}informaltable")
        self.assertIsNotNone(table.find(f".//{DB_NS}thead"))
        body_rows = table.findall(f".//{DB_NS}tbody/{DB_NS}row")
        self.assertEqual(len(body_rows), 1)

    def test_is_idempotent_on_a_second_run(self):
        from convert_markdown_remnants import convert_raw_tables
        root = self._table_fixture()
        convert_raw_tables(root)
        first_pass_xml = ET.tostring(root)
        n_second = convert_raw_tables(root)
        self.assertEqual(n_second, 0)
        self.assertEqual(ET.tostring(root), first_pass_xml)


class TestConvertFileOrdering(unittest.TestCase):
    def test_tables_run_before_emphasis_so_bold_table_cells_are_preserved(self):
        # Adversarial ordering regression test: if convert_inline_emphasis
        # ran FIRST, it would already strip "**bold cell**"'s asterisks
        # into a real <emphasis> INSIDE the raw <para> pipe-row before
        # convert_raw_tables ever runs -- and convert_raw_tables
        # rebuilds its Markdown table source from each row's *plain*
        # text (itertext(), which silently drops existing tags), so the
        # bold would be lost from the resulting table. This test fails
        # against a version of convert_file() that calls
        # convert_inline_emphasis() before convert_raw_tables().
        from convert_markdown_remnants import convert_file
        with tempfile.TemporaryDirectory() as d:
            target = Path(d) / "sample.xml"
            target.write_text(
                '<?xml version="1.0" encoding="UTF-8"?>\n'
                '<section xmlns="http://docbook.org/ns/docbook" xml:id="s">\n'
                '  <para>| | |</para>\n'
                '  <para>| :-: | :-: |</para>\n'
                '  <para>| A | B |</para>\n'
                '  <para>| **bold cell** | plain |</para>\n'
                '</section>\n',
                encoding="utf-8",
            )
            convert_file(target)
            root = ET.parse(target).getroot()
            table = root.find(f"{DB_NS}informaltable")
            self.assertIsNotNone(table, "table was not converted at all")
            emphasis = table.find(f".//{DB_NS}entry/{DB_NS}emphasis")
            self.assertIsNotNone(emphasis, "bold cell content was lost -- tables must convert before inline emphasis")
            self.assertEqual(emphasis.text, "bold cell")


class TestConvertFile(unittest.TestCase):
    def test_convert_file_writes_back_only_when_something_changed(self):
        from convert_markdown_remnants import convert_file
        with tempfile.TemporaryDirectory() as d:
            untouched = Path(d) / "untouched.xml"
            untouched.write_text(
                '<?xml version="1.0" encoding="UTF-8"?>\n'
                '<section xmlns="http://docbook.org/ns/docbook" xml:id="s">'
                '<para>Nothing to convert here.</para></section>\n',
                encoding="utf-8",
            )
            before_mtime = untouched.stat().st_mtime_ns
            n_tables, n_emphasis = convert_file(untouched)
            self.assertEqual((n_tables, n_emphasis), (0, 0))
            self.assertEqual(untouched.stat().st_mtime_ns, before_mtime)

    def test_convert_file_fixes_a_real_shaped_fixture_end_to_end(self):
        from convert_markdown_remnants import convert_file
        with tempfile.TemporaryDirectory() as d:
            target = Path(d) / "sample.xml"
            target.write_text(
                '<?xml version="1.0" encoding="UTF-8"?>\n'
                '<section xmlns="http://docbook.org/ns/docbook" xml:id="s">\n'
                '  <para>This has **bold** text.</para>\n'
                '</section>\n',
                encoding="utf-8",
            )
            n_tables, n_emphasis = convert_file(target)
            self.assertEqual((n_tables, n_emphasis), (0, 1))
            root = ET.parse(target).getroot()
            self.assertNotIn("*", "".join(root.itertext()))


class TestCountMarkdownRemnants(unittest.TestCase):
    def test_counts_bold_italic_and_raw_tables_before_and_after_fix(self):
        from convert_markdown_remnants import count_markdown_remnants, convert_file
        with tempfile.TemporaryDirectory() as d:
            target = Path(d) / "sample.xml"
            target.write_text(
                '<?xml version="1.0" encoding="UTF-8"?>\n'
                '<section xmlns="http://docbook.org/ns/docbook" xml:id="s">\n'
                '  <para>**bold** and *italic*.</para>\n'
                '  <para>| | |</para>\n'
                '  <para>| :-: | :-: |</para>\n'
                '  <para>| A | B |</para>\n'
                '</section>\n',
                encoding="utf-8",
            )
            before = count_markdown_remnants(target)
            self.assertEqual(before, {"bold": 1, "italic": 1, "raw_tables": 1})
            convert_file(target)
            after = count_markdown_remnants(target)
            self.assertEqual(after, {"bold": 0, "italic": 0, "raw_tables": 0})

    def test_triple_star_span_counts_as_one_bold_and_one_italic(self):
        # Regression test for a real bug caught during design: stripping
        # matched bold spans with an EMPTY replacement (instead of a
        # non-empty placeholder) before searching for italic spans
        # collapses "***word***" down to a bare, adjacent "**" with
        # nothing between -- which _ITALIC_COUNT_RE's own delimiter
        # guards then correctly (and misleadingly, for THIS purpose)
        # refuse to match, silently undercounting italic by one per
        # triple-star span (3 such spans exist in the real corpus; an
        # early draft of count_markdown_remnants() reported 262 instead
        # of the correct 265 corpus-wide because of exactly this).
        from convert_markdown_remnants import count_markdown_remnants
        with tempfile.TemporaryDirectory() as d:
            target = Path(d) / "triple.xml"
            target.write_text(
                '<?xml version="1.0" encoding="UTF-8"?>\n'
                '<section xmlns="http://docbook.org/ns/docbook" xml:id="s">\n'
                '  <para>***Borello***</para>\n'
                '</section>\n',
                encoding="utf-8",
            )
            counts = count_markdown_remnants(target)
            self.assertEqual(counts, {"bold": 1, "italic": 1, "raw_tables": 0})


class TestMainCorpusWalk(unittest.TestCase):
    def test_check_mode_reports_totals_without_modifying_files(self):
        from convert_markdown_remnants import main
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "doc.xml"
            f.write_text(
                '<?xml version="1.0" encoding="UTF-8"?>\n'
                '<section xmlns="http://docbook.org/ns/docbook" xml:id="s">\n'
                '  <para>**bold**</para>\n'
                '</section>\n',
                encoding="utf-8",
            )
            before_mtime = f.stat().st_mtime_ns
            out = io.StringIO()
            with redirect_stdout(out):
                rc = main(["--corpus-root", d, "--check"])
            self.assertEqual(rc, 0)
            self.assertIn("bold 1", out.getvalue())
            self.assertEqual(f.stat().st_mtime_ns, before_mtime)

    def test_default_mode_converts_and_reports_the_changed_file(self):
        from convert_markdown_remnants import main
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "doc.xml"
            f.write_text(
                '<?xml version="1.0" encoding="UTF-8"?>\n'
                '<section xmlns="http://docbook.org/ns/docbook" xml:id="s">\n'
                '  <para>**bold**</para>\n'
                '</section>\n',
                encoding="utf-8",
            )
            out = io.StringIO()
            with redirect_stdout(out):
                rc = main(["--corpus-root", d])
            self.assertEqual(rc, 0)
            self.assertIn(str(f), out.getvalue())
            root = ET.parse(f).getroot()
            self.assertNotIn("*", "".join(root.itertext()))


if __name__ == "__main__":
    unittest.main()

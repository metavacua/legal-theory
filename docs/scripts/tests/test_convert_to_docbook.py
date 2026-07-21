import io
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest import mock

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


DB_NS = "{http://docbook.org/ns/docbook}"
XLINK_NS = "{http://www.w3.org/1999/xlink}"
XML_NS = "{http://www.w3.org/XML/1998/namespace}"


class TestPandocAndWrapping(unittest.TestCase):
    def setUp(self):
        self.fixtures = Path(__file__).resolve().parent / "fixtures"

    def test_pandoc_produces_docbook_fragment(self):
        from convert_to_docbook import pandoc_to_docbook_fragment
        fragment = pandoc_to_docbook_fragment(self.fixtures / "flat.md")
        self.assertIn("<section", fragment)
        self.assertIn("A Flat Document", fragment)

    def test_wrap_single_section_unwraps_and_reports_true(self):
        from convert_to_docbook import pandoc_to_docbook_fragment, wrap_fragment
        fragment = pandoc_to_docbook_fragment(self.fixtures / "flat.md")
        article, unwrapped = wrap_fragment(fragment, "flat", "A Flat Document", "flat.meta.xml")
        self.assertTrue(unwrapped)
        self.assertEqual(article.tag, f"{DB_NS}article")
        # The wrapping <section>'s own title must not survive as a
        # duplicate — only the article's <title> carries it.
        child_tags = [c.tag for c in article]
        self.assertEqual(child_tags.count(f"{DB_NS}section"), 0)
        self.assertIn(f"{DB_NS}para", child_tags)
        self.assertEqual(child_tags.count(f"{DB_NS}title"), 1)

    def test_wrap_multi_section_keeps_all_and_reports_false(self):
        from convert_to_docbook import pandoc_to_docbook_fragment, wrap_fragment
        fragment = pandoc_to_docbook_fragment(self.fixtures / "multi_section.md")
        article, unwrapped = wrap_fragment(fragment, "multi", "Multi Section", "multi.meta.xml")
        self.assertFalse(unwrapped)
        child_sections = [c for c in article if c.tag == f"{DB_NS}section"]
        self.assertEqual(len(child_sections), 2)

    def test_wrap_includes_xi_include_with_metadata_href(self):
        from convert_to_docbook import pandoc_to_docbook_fragment, wrap_fragment
        fragment = pandoc_to_docbook_fragment(self.fixtures / "flat.md")
        article, _ = wrap_fragment(fragment, "flat", "A Flat Document", "flat.meta.xml")
        xi_ns = "{http://www.w3.org/2001/XInclude}"
        includes = [c for c in article if c.tag == f"{xi_ns}include"]
        self.assertEqual(len(includes), 1)
        self.assertEqual(includes[0].get("href"), "flat.meta.xml")

    def test_wrap_preserves_xlink_href(self):
        from convert_to_docbook import pandoc_to_docbook_fragment, wrap_fragment
        fragment = pandoc_to_docbook_fragment(self.fixtures / "with_link.md")
        article, _ = wrap_fragment(fragment, "with-link", "A Document With a Link", "x.meta.xml")
        links = article.findall(f".//{DB_NS}link")
        self.assertEqual(len(links), 1)
        self.assertEqual(links[0].get(f"{XLINK_NS}href"), "https://example.com/source")

    def test_sanitize_xml_ids_prefixes_digit_leading_ids(self):
        from convert_to_docbook import (
            pandoc_to_docbook_fragment, wrap_fragment, sanitize_xml_ids,
        )
        fragment = pandoc_to_docbook_fragment(self.fixtures / "numbered_headings.md")
        article, _ = wrap_fragment(fragment, "numbered", "Numbered Sections", "n.meta.xml")
        sanitize_xml_ids(article)
        ids = [el.get(f"{XML_NS}id") for el in article.iter() if el.get(f"{XML_NS}id")]
        self.assertTrue(ids, "expected at least one xml:id in the converted tree")
        for id_value in ids:
            self.assertRegex(id_value, r"^[A-Za-z_]")


class TestWriteMetadata(unittest.TestCase):
    def test_write_metadata_produces_well_formed_xincludable_info(self):
        from convert_to_docbook import write_metadata
        fixtures = Path(__file__).resolve().parent / "fixtures"
        meta_path = fixtures / "tmp.meta.xml"
        write_metadata(meta_path, "A Flat Document")
        tree = ET.parse(meta_path)
        root = tree.getroot()
        self.assertEqual(root.tag, f"{DB_NS}info")
        dc_ns = "{http://purl.org/dc/terms/}"
        title_el = root.find(f"{dc_ns}title")
        self.assertEqual(title_el.text, "A Flat Document")
        rights_el = root.find(f"{dc_ns}rights")
        self.assertEqual(rights_el.text, "CC BY-SA 4.0")
        meta_path.unlink()

    def test_write_metadata_escapes_special_characters_in_title(self):
        from convert_to_docbook import write_metadata
        fixtures = Path(__file__).resolve().parent / "fixtures"
        meta_path = fixtures / "tmp2.meta.xml"
        write_metadata(meta_path, "Torts & Contracts: A < B Comparison")
        tree = ET.parse(meta_path)  # must not raise
        dc_ns = "{http://purl.org/dc/terms/}"
        title_el = tree.getroot().find(f"{dc_ns}title")
        self.assertEqual(title_el.text, "Torts & Contracts: A < B Comparison")
        meta_path.unlink()


class TestValidateAndBuild(unittest.TestCase):
    def setUp(self):
        self.fixtures = Path(__file__).resolve().parent / "fixtures"

    def _convert_fixture(self, name, xml_id, title):
        from convert_to_docbook import (
            pandoc_to_docbook_fragment, wrap_fragment, write_metadata,
        )
        fragment = pandoc_to_docbook_fragment(self.fixtures / name)
        article, _ = wrap_fragment(fragment, xml_id, title, f"{xml_id}.meta.xml")
        xml_path = self.fixtures / f"{xml_id}.xml"
        meta_path = self.fixtures / f"{xml_id}.meta.xml"
        write_metadata(meta_path, title)
        tree = ET.ElementTree(article)
        ET.indent(tree, space="  ")
        tree.write(xml_path, encoding="unicode", xml_declaration=True)
        self.addCleanup(xml_path.unlink)
        self.addCleanup(meta_path.unlink)
        return xml_path

    def test_validate_accepts_well_formed_document(self):
        from convert_to_docbook import validate
        xml_path = self._convert_fixture("flat.md", "flat", "A Flat Document")
        self.assertEqual(validate(xml_path), [])

    def test_validate_rejects_malformed_document(self):
        from convert_to_docbook import validate
        bad_path = self.fixtures / "bad.xml"
        bad_path.write_text("<article><unclosed></article>", encoding="utf-8")
        self.addCleanup(bad_path.unlink)
        errors = validate(bad_path)
        self.assertTrue(errors)

    def test_validate_rejects_well_formed_but_schema_invalid_document(self):
        # Well-formed XML (passes xmllint) that is not DocBook and thus
        # not schema-valid (fails jing) — exercises the jing-only
        # rejection path distinct from the malformed-XML path above.
        from convert_to_docbook import validate
        invalid_path = self.fixtures / "wellformed_invalid.xml"
        invalid_path.write_text(
            '<article version="5.2" xml:id="x"><bogus/></article>',
            encoding="utf-8",
        )
        self.addCleanup(invalid_path.unlink)
        errors = validate(invalid_path)
        self.assertTrue(errors)

    def test_rich_single_heading_fixture_validates(self):
        # Regression test: pandoc's GFM-to-DocBook5 converter emits
        # <informaltable> (not <table>) for GFM tables and
        # <programlisting> for fenced code blocks. A single-heading
        # document gets unwrapped so these become direct children of
        # <article>; block-content must permit them there.
        xml_path = self._convert_fixture(
            "rich_single_heading.md", "rich-single-heading", "Feature Rich Single Heading"
        )
        from convert_to_docbook import validate
        self.assertEqual(validate(xml_path), [])

    def test_build_html_produces_output_with_title(self):
        from convert_to_docbook import build_html
        xml_path = self._convert_fixture("flat.md", "flat", "A Flat Document")
        html_path = self.fixtures / "flat.html"
        build_html(xml_path, html_path)
        self.addCleanup(html_path.unlink)
        content = html_path.read_text(encoding="utf-8")
        self.assertIn("A Flat Document", content)


class TestContentPreservationDiff(unittest.TestCase):
    def setUp(self):
        self.fixtures = Path(__file__).resolve().parent / "fixtures"

    def _convert_fixture(self, name, xml_id, title):
        from convert_to_docbook import (
            pandoc_to_docbook_fragment, wrap_fragment, write_metadata,
        )
        fragment = pandoc_to_docbook_fragment(self.fixtures / name)
        article, unwrapped = wrap_fragment(fragment, xml_id, title, f"{xml_id}.meta.xml")
        xml_path = self.fixtures / f"{xml_id}.xml"
        meta_path = self.fixtures / f"{xml_id}.meta.xml"
        write_metadata(meta_path, title)
        tree = ET.ElementTree(article)
        ET.indent(tree, space="  ")
        tree.write(xml_path, encoding="unicode", xml_declaration=True)
        self.addCleanup(xml_path.unlink)
        self.addCleanup(meta_path.unlink)
        return xml_path, unwrapped

    def test_clean_conversion_flags_nothing(self):
        from convert_to_docbook import content_preservation_diff
        xml_path, unwrapped = self._convert_fixture("flat.md", "flat", "A Flat Document")
        diff = content_preservation_diff(
            self.fixtures / "flat.md", xml_path, "A Flat Document", unwrapped
        )
        self.assertEqual(diff, [])

    def test_multi_section_conversion_flags_nothing(self):
        # No title-compensation needed here (unwrapped=False) — the first
        # section's own heading already carries the text verbatim.
        from convert_to_docbook import content_preservation_diff
        xml_path, unwrapped = self._convert_fixture(
            "multi_section.md", "multi", "Multi Section"
        )
        diff = content_preservation_diff(
            self.fixtures / "multi_section.md", xml_path, "Multi Section", unwrapped
        )
        self.assertEqual(diff, [])

    def test_dropped_horizontal_rule_is_a_known_accepted_difference(self):
        from convert_to_docbook import content_preservation_diff
        xml_path, unwrapped = self._convert_fixture(
            "with_hr.md", "with-hr", "A Document With Dividers"
        )
        diff = content_preservation_diff(
            self.fixtures / "with_hr.md", xml_path, "A Document With Dividers", unwrapped
        )
        self.assertEqual(diff, [])

    def test_genuinely_dropped_paragraph_is_flagged(self):
        from convert_to_docbook import content_preservation_diff
        xml_path, unwrapped = self._convert_fixture("flat.md", "flat", "A Flat Document")
        # Simulate real content loss: overwrite the built XML's body text.
        text = xml_path.read_text(encoding="utf-8")
        text = text.replace("This document has one heading", "Something else entirely")
        xml_path.write_text(text, encoding="utf-8")
        diff = content_preservation_diff(
            self.fixtures / "flat.md", xml_path, "A Flat Document", unwrapped
        )
        self.assertTrue(diff, "expected genuine content loss to be flagged")


class TestConvertEndToEnd(unittest.TestCase):
    def setUp(self):
        self.fixtures = Path(__file__).resolve().parent / "fixtures"
        self.out_dir = self.fixtures / "out"
        self.out_dir.mkdir(exist_ok=True)

    def tearDown(self):
        for f in self.out_dir.iterdir():
            f.unlink()
        self.out_dir.rmdir()

    def test_convert_flat_document_end_to_end(self):
        from convert_to_docbook import convert
        result = convert(self.fixtures / "flat.md", self.out_dir)
        self.assertEqual(result.errors, [])
        self.assertEqual(result.content_diff, [])
        self.assertTrue(result.xml_path.exists())
        self.assertTrue(result.html_path.exists())
        self.assertIn("A Flat Document", result.html_path.read_text(encoding="utf-8"))

    def test_convert_multi_section_document_end_to_end(self):
        from convert_to_docbook import convert
        result = convert(self.fixtures / "multi_section.md", self.out_dir)
        self.assertEqual(result.errors, [])
        self.assertEqual(result.content_diff, [])

    def test_convert_numbered_headings_document_end_to_end(self):
        # Regression coverage for Task 4's xml:id sanitization, exercised
        # through the full pipeline including RNG validation.
        from convert_to_docbook import convert
        result = convert(self.fixtures / "numbered_headings.md", self.out_dir)
        self.assertEqual(result.errors, [])


class TestMainCLI(unittest.TestCase):
    def test_main_reports_clean_error_for_missing_input_file(self):
        from convert_to_docbook import main
        missing = Path(__file__).resolve().parent / "fixtures" / "does-not-exist.md"
        self.assertFalse(missing.exists())
        with mock.patch.object(sys, "argv", ["convert_to_docbook.py", str(missing)]), \
                mock.patch.object(sys, "stderr", io.StringIO()) as fake_stderr:
            rc = main()
        self.assertEqual(rc, 2)
        self.assertIn(str(missing), fake_stderr.getvalue())
        self.assertIn("no such file", fake_stderr.getvalue())


if __name__ == "__main__":
    unittest.main()

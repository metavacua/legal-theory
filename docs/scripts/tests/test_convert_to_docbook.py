import io
import shutil
import subprocess
import sys
import tempfile
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
XI_NS = "{http://www.w3.org/2001/XInclude}"
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

    def test_trailing_whitespace_hard_break_does_not_produce_literallayout(self):
        # Root-caused on a real corpus document
        # (california-worker-misclassification-risk-analysis.md): an
        # accidental Markdown hard line break (2+ trailing spaces mid-
        # paragraph, a copy-paste artifact — confirmed present in 223
        # lines across 35 corpus files) makes pandoc emit <literallayout>
        # instead of <para> for the containing block. html5.xsl has no
        # template for <literallayout>, so it fell through to bare
        # unstyled text with no paragraph wrapping in the built HTML —
        # a real, live rendering defect, not just a diff-check artifact.
        # pandoc_to_docbook_fragment must normalize trailing whitespace
        # before invoking pandoc so this never triggers.
        from convert_to_docbook import pandoc_to_docbook_fragment
        fragment = pandoc_to_docbook_fragment(self.fixtures / "hard_break_artifact.md")
        self.assertNotIn("literallayout", fragment)
        # Without the hard-break trigger, pandoc renders the two
        # physical lines as ordinary reflowable <para> content (here,
        # two sibling paragraphs within the same list item — CommonMark
        # treats an indented continuation line as starting a new block
        # once there's no hard break forcing them together) rather than
        # one frozen <literallayout> block. Both sentences' full text
        # must still be present, just not literal-preformatted.
        normalized = " ".join(fragment.split())
        self.assertIn("trailing whitespace right here.", normalized)
        self.assertIn(
            "Which continues on this next physical line as one intended sentence",
            normalized,
        )

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


class TestSplitIntoFragments(unittest.TestCase):
    def setUp(self):
        self.fixtures = Path(__file__).resolve().parent / "fixtures"

    def test_multi_section_splits_each_top_level_section(self):
        from convert_to_docbook import (
            pandoc_to_docbook_fragment, wrap_fragment, split_into_fragments,
        )
        fragment = pandoc_to_docbook_fragment(self.fixtures / "multi_section.md")
        article, _ = wrap_fragment(fragment, "multi", "Multi Section", "multi.meta.xml")

        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            result = split_into_fragments(article, out_dir, "multi")
            self.assertTrue(result)

            frag_dir = out_dir / "multi"
            self.assertTrue((frag_dir / "01-first-topic.xml").exists())
            self.assertTrue((frag_dir / "02-second-topic.xml").exists())

            frag1 = ET.parse(frag_dir / "01-first-topic.xml").getroot()
            self.assertEqual(frag1.tag, f"{DB_NS}section")
            self.assertEqual(frag1.get("{http://www.w3.org/XML/1998/namespace}id"), "first-topic")

            includes = [c for c in article if c.tag == f"{XI_NS}include"]
            # 3 total: wrap_fragment() already added a metadata xi:include
            # (href="multi.meta.xml") as the article's first child, before
            # split_into_fragments() ever runs. split_into_fragments() must
            # NOT touch that include — it only replaces db:section children.
            # So the 2 new fragment includes land alongside it, not instead
            # of it.
            self.assertEqual(len(includes), 3)
            self.assertEqual(includes[0].get("href"), "multi.meta.xml")
            self.assertEqual(includes[1].get("href"), "multi/01-first-topic.xml")
            self.assertEqual(includes[2].get("href"), "multi/02-second-topic.xml")

            sections_left = [c for c in article if c.tag == f"{DB_NS}section"]
            self.assertEqual(sections_left, [])

    def test_split_shell_resolves_to_original_content(self):
        # The shell + fragments, resolved via xmllint --xinclude, must
        # reproduce the exact original tree.
        from convert_to_docbook import (
            pandoc_to_docbook_fragment, wrap_fragment, write_metadata,
            split_into_fragments,
        )
        fragment = pandoc_to_docbook_fragment(self.fixtures / "multi_section.md")
        article, _ = wrap_fragment(fragment, "multi", "Multi Section", "multi.meta.xml")

        # A subdirectory of the fixtures tree (itself under docs/), not a
        # system temp dir — write_metadata() computes the shared-metadata
        # href relative to docs/ (Task 1), so out_dir must stay under docs/
        # for that calculation to resolve correctly. Do NOT change
        # write_metadata() to accommodate an out-of-docs path here — that
        # function's contract belongs to Task 1, already reviewed.
        out_dir = Path(tempfile.mkdtemp(dir=self.fixtures))
        self.addCleanup(shutil.rmtree, out_dir)

        split_into_fragments(article, out_dir, "multi")
        write_metadata(out_dir / "multi.meta.xml", "Multi Section")
        xml_path = out_dir / "multi.xml"
        tree = ET.ElementTree(article)
        ET.indent(tree, space="  ")
        tree.write(xml_path, encoding="unicode", xml_declaration=True)

        resolved = subprocess.run(
            ["xmllint", "--xinclude", str(xml_path)],
            capture_output=True, text=True, check=True,
        ).stdout
        self.assertIn("First Topic", resolved)
        self.assertIn("Content for the first topic.", resolved)
        self.assertIn("Second Topic", resolved)
        self.assertIn("Content for the second topic.", resolved)


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

        xi_ns = "{http://www.w3.org/2001/XInclude}"
        includes = root.findall(f"{xi_ns}include")
        self.assertEqual(len(includes), 1)

        resolved = subprocess.run(
            ["xmllint", "--xinclude", str(meta_path)],
            capture_output=True, text=True, check=True,
        ).stdout
        resolved_root = ET.fromstring(resolved)
        rights_el = resolved_root.find(f".//{dc_ns}rights")
        self.assertIsNotNone(rights_el)
        self.assertEqual(rights_el.text, "CC BY-SA 4.0")
        publisher_el = resolved_root.find(f".//{dc_ns}publisher")
        self.assertEqual(publisher_el.text, "metavacua/legal-theory (GitHub)")

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

    def test_convert_reports_clean_error_for_malformed_pandoc_output(self):
        # Root-caused on a real corpus document
        # (petition-corporate-ai-registry-ca-sos.md): a stray, unmatched
        # HTML-like closing tag in the source (an artifact from whatever
        # generated the document, e.g. `</content>` with no opening
        # tag) survives as raw-HTML passthrough in pandoc's DocBook5
        # output, producing genuinely malformed XML — wrap_fragment()'s
        # ET.fromstring() raised an uncaught ParseError, crashing the
        # whole convert() call instead of reporting a clean error the
        # way validate() already does for other malformed input.
        from convert_to_docbook import convert
        result = convert(self.fixtures / "stray_html_tag.md", self.out_dir)
        self.assertTrue(result.errors, "expected a reported error, not a crash")
        self.assertTrue(
            any("pars" in e.lower() or "malformed" in e.lower() for e in result.errors),
            f"expected a parse-related error message, got: {result.errors}",
        )


class TestIgnorableWordRun(unittest.TestCase):
    # Regression coverage for two real false positives found converting
    # real corpus documents (google-platform-misclassification's
    # california-worker-misclassification-risk-analysis.md): pandoc's
    # plain-text writer (1) rewraps long lines at a different column
    # width, and (2) regroups adjacent list items into a different
    # number of blank-line-separated blocks, after a DocBook round-trip
    # — same words throughout, but neither line nor paragraph
    # boundaries survive the round-trip intact. Word-level comparison
    # (content_preservation_diff, tested below) is immune to both;
    # these tests cover the token-level ignore rule directly.

    def test_pure_dash_run_is_ignorable(self):
        from convert_to_docbook import _is_ignorable_word_run
        self.assertTrue(_is_ignorable_word_run(["----------"]))
        self.assertTrue(_is_ignorable_word_run(["--", "---"]))

    def test_pure_table_border_run_is_ignorable(self):
        # Root-caused on a real corpus document
        # (california-worker-misclassification-risk-analysis.md, a
        # 9-column table): pandoc's plain-text writer renders the same
        # table two different ways depending on path — a column-aligned
        # ASCII grid (dashes) direct from Markdown, vs. a pipe-delimited
        # rendering (pipes/colons) after the DocBook round-trip through
        # informaltable/entry. Verified independently: every cell's
        # actual word content is identical and in the same order on
        # both sides — only the border/rule characters differ, exactly
        # analogous to the already-tolerated horizontal-rule case.
        from convert_to_docbook import _is_ignorable_word_run
        self.assertTrue(_is_ignorable_word_run(["|", "|", "|"]))
        self.assertTrue(_is_ignorable_word_run([":-:", ":-:", ":-:"]))
        self.assertTrue(_is_ignorable_word_run(["-----", "|", "----:"]))

    def test_any_non_alphanumeric_run_is_ignorable_not_just_known_chars(self):
        # The ignore rule is a general "no alphanumeric content" predicate,
        # not an enumerated allowlist of the two witnessed causes (dashes,
        # then pipes/colons) — a border/rule character neither of those
        # causes happened to use must be tolerated too, on the same
        # principle: pure formatting glue with no semantic payload.
        from convert_to_docbook import _is_ignorable_word_run
        self.assertTrue(_is_ignorable_word_run(["===", "~~~", "***"]))

    def test_empty_run_is_ignorable(self):
        from convert_to_docbook import _is_ignorable_word_run
        self.assertTrue(_is_ignorable_word_run([]))

    def test_real_word_run_is_not_ignorable(self):
        from convert_to_docbook import _is_ignorable_word_run
        self.assertFalse(_is_ignorable_word_run(["Analysis:", "the", "platform"]))

    def test_mixed_run_with_one_real_word_is_not_ignorable(self):
        from convert_to_docbook import _is_ignorable_word_run
        self.assertFalse(_is_ignorable_word_run(["----", "word", "----"]))
        self.assertFalse(_is_ignorable_word_run(["|", "Program/User", "Class", "|"]))

    def test_word_diff_ignores_rewrapping_and_regrouping(self):
        # Directly exercises the real _word_level_diff() production
        # logic without invoking pandoc: same words, split into a
        # different number of lines and a different number of blank-
        # line-separated blocks, must compare as identical at the word
        # level. Calling the actual helper (rather than re-deriving the
        # same loop here) means a future change to the ignore rule or
        # opcode-filtering logic can't silently drift out of sync with
        # this test.
        from convert_to_docbook import _word_level_diff
        original = (
            "- Programs: Google Maps Local Guides.\n"
            "- Analysis: This is a long sentence that\n"
            "  keeps going for a while about consideration.\n"
        )
        roundtrip = (
            "- Programs: Google Maps Local\n"
            "  Guides.\n"
            "\n"
            "- Analysis: This is a long sentence that keeps going for a\n"
            "  while about consideration.\n"
        )
        changed = _word_level_diff(original.split(), roundtrip.split())
        self.assertEqual(changed, [])


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

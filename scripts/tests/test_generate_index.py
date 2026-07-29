import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class TestCollectDocuments(unittest.TestCase):
    def test_finds_the_real_corpus_documents(self):
        from generate_index import collect_documents
        docs = collect_documents()
        # 127 confirmed by direct count against the real corpus (up from
        # 120 once Task 4 converted docs/audits/README.md to a real
        # DocBook article); re-verify here so a future corpus change
        # that silently breaks the walk is caught, not silently
        # accepted.
        self.assertEqual(len(docs), 127)

    def test_every_document_has_a_real_title_not_a_filename_fallback(self):
        from generate_index import collect_documents
        docs = collect_documents()
        # A title equal to its own filename stem is the fallback path
        # (info/title missing or empty) -- every real corpus document
        # has a real <info><title>, so zero fallbacks is the expected,
        # verified state, not an assumption.
        stem_matches = [
            (html_rel, title) for html_rel, title, _ in docs
            if title == html_rel.stem
        ]
        self.assertEqual(stem_matches, [])

    def test_categorizes_into_the_expected_buckets(self):
        from generate_index import collect_documents, CATEGORY_ORDER
        docs = collect_documents()
        categories_found = {category for _, _, category in docs}
        expected_labels = {label for _, label in CATEGORY_ORDER}
        self.assertTrue(categories_found.issubset(expected_labels))
        self.assertNotIn("Other", categories_found)

    def test_no_real_document_falls_into_the_other_category(self):
        # A document categorized "Other" is silently omitted from
        # docs/index.xml entirely (build_index_xml only emits a <section>
        # for each label in CATEGORY_ORDER) even though it still appears
        # in docs/sitemap.xml -- a real, citable document going missing
        # from the human-readable index with no visible sign anything was
        # dropped. Every real corpus document must map to a real category,
        # not the untested fallback. (This caught docs/audits/README.xml
        # falling through once "audits" wasn't yet a known prefix.)
        from generate_index import collect_documents
        docs = collect_documents()
        others = [str(html_rel) for html_rel, _, category in docs
                  if category == "Other"]
        self.assertEqual(
            others, [],
            f"documents silently dropped into the 'Other' category "
            f"(missing from docs/index.xml): {others}",
        )


class TestBuildIndexXml(unittest.TestCase):
    def test_generated_xml_is_well_formed_and_has_one_section_per_category(self):
        import tempfile
        from generate_index import build_index_xml
        docs = [
            (Path("cross-cutting/a.html"), "Doc A", "Cross-Cutting"),
            (Path("cross-cutting/b.html"), "Doc B", "Cross-Cutting"),
            (Path("wip/c.html"), "Doc C", "Works in Progress"),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            xml_path = Path(tmp) / "index.xml"
            build_index_xml(docs, xml_path)
            content = xml_path.read_text(encoding="utf-8")
            self.assertIn('xml:id="cross-cutting"', content)
            self.assertIn('xml:id="works-in-progress"', content)
            self.assertEqual(content.count("<itemizedlist>"), 2)
            self.assertEqual(content.count("<listitem>"), 3)

    def test_href_containing_a_double_quote_is_correctly_attribute_escaped(self):
        import tempfile
        import xml.etree.ElementTree as ET
        from generate_index import build_index_xml
        docs = [(Path('wip/a "quoted" doc.html'), "Title", "Works in Progress")]
        with tempfile.TemporaryDirectory() as tmp:
            xml_path = Path(tmp) / "index.xml"
            build_index_xml(docs, xml_path)
            content = xml_path.read_text(encoding="utf-8")
            root = ET.fromstring(content)  # raises ParseError if the quote broke the attribute
            link_el = root.find(f".//{{http://docbook.org/ns/docbook}}link")
            self.assertEqual(
                link_el.get("{http://www.w3.org/1999/xlink}href"),
                'wip/a "quoted" doc.html',
            )


if __name__ == "__main__":
    unittest.main()

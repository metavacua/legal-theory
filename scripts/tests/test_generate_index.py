import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class TestCollectDocuments(unittest.TestCase):
    def test_finds_the_real_corpus_documents(self):
        from generate_index import collect_documents
        docs = collect_documents()
        # 120 confirmed by direct count against the real corpus before
        # this plan was written; re-verify here so a future corpus
        # change that silently breaks the walk is caught, not silently
        # accepted.
        self.assertEqual(len(docs), 120)

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

    def test_categorizes_into_the_expected_seven_buckets(self):
        from generate_index import collect_documents, CATEGORY_ORDER
        docs = collect_documents()
        categories_found = {category for _, _, category in docs}
        expected_labels = {label for _, label in CATEGORY_ORDER}
        self.assertTrue(categories_found.issubset(expected_labels))
        self.assertNotIn("Other", categories_found)


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


if __name__ == "__main__":
    unittest.main()

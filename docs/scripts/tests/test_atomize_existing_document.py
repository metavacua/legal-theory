import shutil
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from convert_to_docbook import DC_NS


class TestAtomizeExistingDocument(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = Path(__file__).resolve().parent / "fixtures" / "atomize_tmp"
        self.tmp_dir.mkdir(exist_ok=True)
        pilot = Path(__file__).resolve().parent / "fixtures" / "atomize_pilot"
        self.xml_path = self.tmp_dir / "patron-as-client.xml"
        self.meta_path = self.tmp_dir / "patron-as-client.meta.xml"
        shutil.copy(pilot / "patron-as-client.xml", self.xml_path)
        shutil.copy(pilot / "patron-as-client.meta.xml", self.meta_path)

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_migrates_real_document_cleanly(self):
        from atomize_existing_document import atomize_existing_document
        diff, errors = atomize_existing_document(self.xml_path, self.meta_path)
        self.assertEqual(errors, [])
        self.assertEqual(diff, [])

        frag_dir = self.tmp_dir / "patron-as-client"
        self.assertTrue(frag_dir.is_dir())
        self.assertEqual(len(list(frag_dir.iterdir())), 6)

        shell_text = self.xml_path.read_text(encoding="utf-8")
        self.assertIn("xi:include", shell_text)
        self.assertNotIn("Introduction: The Blurring Line", shell_text)

        meta_text = self.meta_path.read_text(encoding="utf-8")
        self.assertIn("common/shared-metadata.xml", meta_text)
        self.assertIn(
            "The Patron as Client: Analyzing Crowdfunded Commissions Under California Labor Law",
            meta_text,
        )

    def test_preserves_full_title_when_title_wraps_inline_markup(self):
        # Regression test for the same root-cause bug fixed in
        # split_into_fragments(): reading title_el.text only returns the
        # text directly before an element's first child, so a <dc:title>
        # wrapping its text in inline markup would silently lose the real
        # title. Overwrite the copied .meta.xml with one whose <dc:title>
        # is styled, keeping all other elements identical to
        # shared-metadata.xml so the shared-shape guard still passes.
        styled_meta = f"""<?xml version="1.0" encoding="UTF-8"?>
<info xmlns="http://docbook.org/ns/docbook" xmlns:dc="http://purl.org/dc/terms/">
  <dc:title><emphasis role="strong">Styled Title</emphasis></dc:title>
  <dc:creator>Ian D.L.N. McLean</dc:creator>
  <dc:publisher>metavacua/legal-theory (GitHub)</dc:publisher>
  <dc:type>Article</dc:type>
  <dc:language>en</dc:language>
  <dc:rights>CC BY-SA 4.0</dc:rights>
  <authorgroup>
    <author>
      <personname>
        <firstname>Ian</firstname>
        <othername role="middle">D.L.N.</othername>
        <surname>McLean</surname>
      </personname>
      <email>metavacua@gmail.com</email>
    </author>
  </authorgroup>
  <legalnotice>
    <para>Copyright &#169; 2026 Ian D.L.N. McLean. Licensed under Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0). This document publishes general legal analysis and does not constitute legal advice.</para>
  </legalnotice>
</info>
"""
        self.meta_path.write_text(styled_meta, encoding="utf-8")

        from atomize_existing_document import atomize_existing_document
        diff, errors = atomize_existing_document(self.xml_path, self.meta_path)
        self.assertEqual(errors, [])
        self.assertEqual(diff, [])

        meta_root = ET.parse(self.meta_path).getroot()
        title_el = meta_root.find(f"{{{DC_NS}}}title")
        self.assertIsNotNone(title_el)
        self.assertEqual(title_el.text, "Styled Title")

    def test_rolls_back_on_validation_failure(self):
        # Simulate a corrupt shell by making the schema fail: strip the
        # xml:id off a section, which docbook-corpus.rnc's finding-section
        # pattern doesn't apply here, so instead corrupt well-formedness
        # directly to force validate() to fail deterministically.
        original_text = self.xml_path.read_text(encoding="utf-8")
        original_meta_text = self.meta_path.read_text(encoding="utf-8")

        from atomize_existing_document import atomize_existing_document
        import atomize_existing_document as mod

        # Monkeypatch validate() to always report an error, to test the
        # rollback path deterministically without depending on a specific
        # corruption technique.
        original_validate = mod.validate
        mod.validate = lambda xml_path: ["forced failure for rollback test"]
        try:
            diff, errors = atomize_existing_document(self.xml_path, self.meta_path)
        finally:
            mod.validate = original_validate

        self.assertEqual(errors, ["forced failure for rollback test"])
        self.assertEqual(self.xml_path.read_text(encoding="utf-8"), original_text)
        self.assertEqual(self.meta_path.read_text(encoding="utf-8"), original_meta_text)
        self.assertFalse((self.tmp_dir / "patron-as-client").exists())

    def test_refuses_when_metadata_is_not_shared_shape(self):
        # Corrupt the copied .meta.xml by adding a genuinely different
        # element (a dc:date not present in shared-metadata.xml), and
        # confirm the guard refuses to touch anything at all.
        meta_root = ET.parse(self.meta_path).getroot()
        date_el = ET.SubElement(meta_root, f"{{{DC_NS}}}date")
        date_el.text = "2020-01-01"
        tree = ET.ElementTree(meta_root)
        tree.write(self.meta_path, encoding="unicode", xml_declaration=True)
        corrupted_meta_text = self.meta_path.read_text(encoding="utf-8")
        original_xml_text = self.xml_path.read_text(encoding="utf-8")

        from atomize_existing_document import atomize_existing_document
        diff, errors = atomize_existing_document(self.xml_path, self.meta_path)

        self.assertEqual(diff, [])
        self.assertTrue(errors)
        self.assertFalse((self.tmp_dir / "patron-as-client").exists())
        self.assertEqual(self.xml_path.read_text(encoding="utf-8"), original_xml_text)
        self.assertEqual(self.meta_path.read_text(encoding="utf-8"), corrupted_meta_text)

    def test_rolls_back_and_reraises_on_unexpected_exception(self):
        # Monkeypatch build_html() (not validate()) to raise, to prove the
        # exception-safety wrapper catches ANY exception in the
        # mutate-and-validate region, restores originals, cleans up
        # fragments, and still re-raises rather than swallowing the error.
        original_text = self.xml_path.read_text(encoding="utf-8")
        original_meta_text = self.meta_path.read_text(encoding="utf-8")

        from atomize_existing_document import atomize_existing_document
        import atomize_existing_document as mod

        def _boom(xml_path, out_path):
            raise RuntimeError("forced failure for exception-safety test")

        original_build_html = mod.build_html
        mod.build_html = _boom
        try:
            with self.assertRaises(RuntimeError):
                atomize_existing_document(self.xml_path, self.meta_path)
        finally:
            mod.build_html = original_build_html

        self.assertEqual(self.xml_path.read_text(encoding="utf-8"), original_text)
        self.assertEqual(self.meta_path.read_text(encoding="utf-8"), original_meta_text)
        self.assertFalse((self.tmp_dir / "patron-as-client").exists())


if __name__ == "__main__":
    unittest.main()

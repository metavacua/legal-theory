import shutil
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from convert_to_docbook import DB_NS, DC_NS, XI_NS, write_metadata


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
        # write_metadata() now includes xi:includes to authorgroup.xml and
        # legalnotice.xml (Task 1/2), not a shared-metadata.xml reference
        self.assertIn("common/authorgroup.xml", meta_text)
        self.assertIn("common/legalnotice.xml", meta_text)
        self.assertIn(
            "The Patron as Client: Analyzing Crowdfunded Commissions Under California Labor Law",
            meta_text,
        )

    def test_preserves_full_title_when_title_wraps_inline_markup(self):
        # Regression test for element_full_text() logic used by the title
        # reader: reading title_el.text only returns the text directly
        # before an element's first child, so a <title> wrapping its text
        # in inline markup would silently lose the real title. But
        # element_full_text() uses itertext() to capture text across all
        # nested elements, preserving the full title correctly. Use a
        # styled native <title> to verify this works.
        from convert_to_docbook import DB_NS
        styled_meta = f"""<?xml version="1.0" encoding="UTF-8"?>
<info xmlns="http://docbook.org/ns/docbook" xmlns:dc="http://purl.org/dc/terms/" xmlns:xi="http://www.w3.org/2001/XInclude">
  <title><emphasis role="strong">Styled Title</emphasis></title>
  <dc:type>Text</dc:type>
  <xi:include href="../../../../common/authorgroup.xml" />
  <xi:include href="../../../../common/legalnotice.xml" />
</info>
"""
        self.meta_path.write_text(styled_meta, encoding="utf-8")

        from atomize_existing_document import atomize_existing_document
        diff, errors = atomize_existing_document(self.xml_path, self.meta_path)
        self.assertEqual(errors, [])
        self.assertEqual(diff, [])

        # After migration, the metadata should have been rewritten with
        # generated metadata, but the styled title should still be readable.
        meta_root = ET.parse(self.meta_path).getroot()
        title_el = meta_root.find(f"{{{DB_NS}}}title")
        self.assertIsNotNone(title_el)
        # write_metadata() regenerates the title as plain text, not styled
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


class TestMetaMatchesSharedShape(unittest.TestCase):
    """Direct unit coverage of _meta_matches_shared_shape()'s structural
    check, isolated from the full atomize_existing_document() pipeline
    (which also calls the real jing/docbook-corpus.rnc validate() step --
    a separate, already-tracked pre-existing gap unrelated to this
    function; see docs/superpowers/plans -- so these tests exercise the
    guard function directly rather than going through validate())."""

    def setUp(self):
        self.tmp_dir = Path(__file__).resolve().parent / "fixtures" / "meta_shape_tmp"
        self.tmp_dir.mkdir(exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_accepts_a_real_write_metadata_generated_file(self):
        # The pass case: a .meta.xml produced by the real write_metadata()
        # (not a hand-written approximation of its shape) must be accepted.
        from atomize_existing_document import _meta_matches_shared_shape

        meta_path = self.tmp_dir / "doc.meta.xml"
        write_metadata(meta_path, "A Real Document Title")
        meta_root = ET.parse(meta_path).getroot()
        self.assertTrue(_meta_matches_shared_shape(meta_root, meta_path))

    def test_accepts_a_subset_of_the_known_fields(self):
        # A document that hasn't yet been regenerated with every field
        # write_metadata() now emits (e.g. only title/dc:type/xi:include,
        # matching the corpus's current pre-migration shape) is still
        # safe to overwrite -- every one of its children is still a known,
        # per-document-varying native field. This is a subset check, not
        # an exact-shape check.
        from atomize_existing_document import _meta_matches_shared_shape

        minimal = f"""<?xml version="1.0" encoding="UTF-8"?>
<info xmlns="{DB_NS}" xmlns:dc="http://purl.org/dc/terms/" xmlns:xi="{XI_NS}">
  <title>Minimal Document</title>
  <dc:type>Text</dc:type>
  <xi:include href="../../../../common/authorgroup.xml" />
  <xi:include href="../../../../common/legalnotice.xml" />
</info>
"""
        meta_path = self.tmp_dir / "minimal.meta.xml"
        meta_path.write_text(minimal, encoding="utf-8")
        meta_root = ET.parse(meta_path).getroot()
        self.assertTrue(_meta_matches_shared_shape(meta_root, meta_path))

    def test_refuses_a_hand_authored_abstract(self):
        # The refuse case: an element write_metadata() has no way to
        # produce (e.g. a hand-authored <abstract>) means this document
        # has genuinely richer metadata than write_metadata() knows how
        # to preserve -- must be refused, not silently destroyed.
        from atomize_existing_document import _meta_matches_shared_shape

        meta_path = self.tmp_dir / "rich.meta.xml"
        write_metadata(meta_path, "A Document With An Abstract")
        meta_root = ET.parse(meta_path).getroot()
        abstract_el = ET.SubElement(meta_root, f"{{{DB_NS}}}abstract")
        abstract_el.text = "Hand-authored summary write_metadata() cannot produce."
        self.assertFalse(_meta_matches_shared_shape(meta_root, meta_path))

    def test_refuses_an_inlined_legalnotice_instead_of_xi_include(self):
        # A document-specific <legalnotice> inlined directly, rather than
        # pulled in via the standard xi:include to common/legalnotice.xml,
        # is exactly the case this guard exists to catch: write_metadata()
        # would silently replace it with the generic shared notice.
        from atomize_existing_document import _meta_matches_shared_shape

        meta_path = self.tmp_dir / "inlined.meta.xml"
        write_metadata(meta_path, "A Document With A Custom Notice")
        meta_root = ET.parse(meta_path).getroot()
        notice_el = ET.SubElement(meta_root, f"{{{DB_NS}}}legalnotice")
        notice_el.text = "A document-specific notice, not the shared boilerplate."
        self.assertFalse(_meta_matches_shared_shape(meta_root, meta_path))

    def test_refuses_an_xi_include_pointing_elsewhere(self):
        # A third xi:include target write_metadata() never produces (e.g.
        # some other shared file) must not be waved through just because
        # its tag is xi:include -- the href itself has to be one of the
        # two known shared-boilerplate targets.
        from atomize_existing_document import _meta_matches_shared_shape

        meta_path = self.tmp_dir / "rogue-include.meta.xml"
        write_metadata(meta_path, "A Document With A Rogue Include")
        meta_root = ET.parse(meta_path).getroot()
        rogue = ET.SubElement(meta_root, f"{{{XI_NS}}}include")
        rogue.set("href", "../../../common/some-other-shared-file.xml")
        self.assertFalse(_meta_matches_shared_shape(meta_root, meta_path))

    def test_refuses_zero_title_children(self):
        # A meta_root with no <title> at all (but otherwise valid
        # xi:includes) must be refused. Left unguarded, the caller's
        # meta_root.find(title) downstream returns None,
        # element_full_text(None) returns "", and write_metadata() would
        # silently regenerate the document with an EMPTY title -- no
        # error, no diff (title isn't covered by the content-preservation
        # diff).
        from atomize_existing_document import _meta_matches_shared_shape

        meta_path = self.tmp_dir / "no-title.meta.xml"
        write_metadata(meta_path, "A Document About To Lose Its Title")
        meta_root = ET.parse(meta_path).getroot()
        title_el = meta_root.find(f"{{{DB_NS}}}title")
        meta_root.remove(title_el)
        self.assertFalse(_meta_matches_shared_shape(meta_root, meta_path))

    def test_refuses_two_title_children(self):
        # A meta_root with two <title> children must also be refused --
        # every child tag is individually "known", so the old per-tag-only
        # check waved this through, and the caller's .find() would
        # silently discard the second one.
        from atomize_existing_document import _meta_matches_shared_shape

        meta_path = self.tmp_dir / "two-titles.meta.xml"
        write_metadata(meta_path, "A Document With A Duplicate Title")
        meta_root = ET.parse(meta_path).getroot()
        extra_title = ET.SubElement(meta_root, f"{{{DB_NS}}}title")
        extra_title.text = "A Second, Conflicting Title"
        self.assertFalse(_meta_matches_shared_shape(meta_root, meta_path))

    def test_refuses_an_xi_include_with_same_suffix_different_prefix(self):
        # An href that ends with the right suffix but is rooted somewhere
        # else entirely (e.g. a sibling "evil" directory instead of the
        # real docs/common/) must be refused. A suffix-only check would
        # wrongly accept this; only resolving the href relative to the
        # .meta.xml's own directory and comparing against the real file
        # catches it.
        from atomize_existing_document import _meta_matches_shared_shape

        meta_path = self.tmp_dir / "path-traversal.meta.xml"
        write_metadata(meta_path, "A Document With A Spoofed Include Path")
        meta_root = ET.parse(meta_path).getroot()
        for xi_include in meta_root.findall(f"{{{XI_NS}}}include"):
            if xi_include.get("href", "").endswith("authorgroup.xml"):
                xi_include.set("href", "../evil/common/authorgroup.xml")
        self.assertFalse(_meta_matches_shared_shape(meta_root, meta_path))


if __name__ == "__main__":
    unittest.main()

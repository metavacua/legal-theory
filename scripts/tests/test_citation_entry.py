import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class TestDeriveEntryKey(unittest.TestCase):
    def test_derives_key_from_url_host_and_tail(self):
        from citation_entry import derive_entry_key
        key = derive_entry_key("some display text", href="https://en.wikipedia.org/wiki/DisCoCat")
        self.assertEqual(key, "en-discocat")

    def test_falls_back_to_slugified_text_without_href(self):
        from citation_entry import derive_entry_key
        key = derive_entry_key("A Real Paper Title")
        self.assertEqual(key, "a-real-paper-title")

    def test_key_length_is_capped(self):
        from citation_entry import derive_entry_key
        key = derive_entry_key("A " * 100)
        self.assertLessEqual(len(key), 80)

    def test_falls_back_to_slugified_text_when_href_has_no_recognized_scheme(self):
        """A non-http(s) href (e.g. a bare relative path) shouldn't
        silently produce a garbage key -- derive_entry_key should fall
        back to the text-based slug exactly as if no href were given."""
        from citation_entry import derive_entry_key
        key = derive_entry_key("A Real Paper Title", href="/local/relative/path")
        self.assertEqual(key, "a-real-paper-title")


class TestWriteAndParseBiblioentry(unittest.TestCase):
    def setUp(self):
        self.out_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.out_dir)

    def test_round_trips_key_role_title_href(self):
        from citation_entry import write_biblioentry, parse_biblioentry
        entry_path = self.out_dir / "smith2020.xml"
        write_biblioentry(entry_path, key="smith2020", role="secondary",
                           title="Some Real Paper", href="https://example.com/a")
        parsed = parse_biblioentry(entry_path)
        self.assertEqual(parsed["key"], "smith2020")
        self.assertEqual(parsed["role"], "secondary")
        self.assertEqual(parsed["title"], "Some Real Paper")
        self.assertEqual(parsed["href"], "https://example.com/a")

    def test_href_is_optional(self):
        from citation_entry import write_biblioentry, parse_biblioentry
        entry_path = self.out_dir / "noref.xml"
        write_biblioentry(entry_path, key="noref", role="needs-research", title="Unresolved Citation")
        parsed = parse_biblioentry(entry_path)
        self.assertIsNone(parsed["href"])

    def test_written_entry_validates_against_real_docbook_5_2_when_wrapped(self):
        """<biblioentry> is not a valid standalone root (same class of
        finding as docs/common/authorgroup.xml in Phase 1) -- validated
        nested in a realistic article, matching how it will actually be
        consumed via xi:include."""
        from citation_entry import write_biblioentry
        from convert_to_docbook import fetch_docbook_schema
        entry_path = self.out_dir / "smith2020.xml"
        write_biblioentry(entry_path, key="smith2020", role="secondary",
                           title="Some Real Paper", href="https://example.com/a")
        wrapper_path = self.out_dir / "wrapper.xml"
        wrapper_path.write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<article xmlns="http://docbook.org/ns/docbook" '
            'xmlns:xi="http://www.w3.org/2001/XInclude" version="5.2" xml:id="t" xml:lang="en">\n'
            '  <title>T</title>\n'
            '  <para>Body content.</para>\n'
            '  <bibliography>\n'
            f'    <xi:include href="{entry_path.name}"/>\n'
            '  </bibliography>\n'
            '</article>\n',
            encoding="utf-8",
        )
        schema = fetch_docbook_schema()
        result = subprocess.run(["jing", "-c", str(schema), str(wrapper_path)],
                                 capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_double_quote_in_href_does_not_break_xml(self):
        """Guards the exact escaping bug this project's own global
        constraints already flagged once (the superseded ontology
        plan's note on avoiding _entry_listitem_xml's pattern)."""
        from citation_entry import write_biblioentry
        entry_path = self.out_dir / "tricky.xml"
        write_biblioentry(entry_path, key="tricky", role="secondary",
                           title='A Title With "Quotes" & Ampersands',
                           href='https://example.com/a?q="x"&y=1')
        ET.parse(entry_path)  # must not raise

    def test_title_and_href_with_quotes_and_ampersands_round_trip_exactly(self):
        """Stronger than the well-formedness-only check above: the
        parsed content must equal the original strings exactly, not
        merely fail to raise. A naive implementation could produce
        well-formed XML that still mangles the escaped characters on
        the way back out (e.g. double-escaping, or losing everything
        after an unescaped '&')."""
        from citation_entry import write_biblioentry, parse_biblioentry
        entry_path = self.out_dir / "tricky2.xml"
        title = 'A Title With "Quotes" & Ampersands'
        href = 'https://example.com/a?q="x"&y=1'
        write_biblioentry(entry_path, key="tricky2", role="secondary", title=title, href=href)
        parsed = parse_biblioentry(entry_path)
        self.assertEqual(parsed["title"], title)
        self.assertEqual(parsed["href"], href)

    def test_empty_title_round_trips_to_empty_string(self):
        """An empty title is a degenerate but real edge case: ET
        represents an empty element's .text as None, not "" -- the
        parser must normalize that back to "" rather than leaking None
        or raising."""
        from citation_entry import write_biblioentry, parse_biblioentry
        entry_path = self.out_dir / "emptytitle.xml"
        write_biblioentry(entry_path, key="emptytitle", role="needs-research", title="")
        parsed = parse_biblioentry(entry_path)
        self.assertEqual(parsed["title"], "")

    def test_rewriting_identical_content_to_the_same_path_is_a_silent_no_op(self):
        """Regenerating a bibliography re-derives and re-writes every
        entry every run (per the design doc's regeneration model) --
        writing the exact same key/role/title/href twice must not be
        treated as an error."""
        from citation_entry import write_biblioentry, parse_biblioentry
        entry_path = self.out_dir / "smith2020.xml"
        write_biblioentry(entry_path, key="smith2020", role="secondary",
                           title="Some Real Paper", href="https://example.com/a")
        write_biblioentry(entry_path, key="smith2020", role="secondary",
                           title="Some Real Paper", href="https://example.com/a")
        parsed = parse_biblioentry(entry_path)
        self.assertEqual(parsed["title"], "Some Real Paper")

    def test_writing_different_content_to_an_existing_key_raises(self):
        """derive_entry_key is not injective (e.g. two different URLs
        can share a host + final path segment and derive the same
        key). Silently overwriting an existing entry with unrelated
        content would lose the first source with no signal. This must
        surface loudly instead."""
        from citation_entry import write_biblioentry
        entry_path = self.out_dir / "collide.xml"
        write_biblioentry(entry_path, key="collide", role="secondary",
                           title="First Source", href="https://example.com/first")
        with self.assertRaises(ValueError):
            write_biblioentry(entry_path, key="collide", role="secondary",
                               title="Second, Unrelated Source", href="https://example.com/second")
        # and the original content must survive the rejected write
        from citation_entry import parse_biblioentry
        parsed = parse_biblioentry(entry_path)
        self.assertEqual(parsed["title"], "First Source")

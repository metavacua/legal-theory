import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

DB_NS = "http://docbook.org/ns/docbook"
XLINK_NS = "http://www.w3.org/1999/xlink"


class _EntriesDirSandboxTestCase(unittest.TestCase):
    """Shared setup for tests that exercise build_entry_key_map: points
    citation_entry.ENTRIES_DIR -- and convert_numbered_citations's own
    copy of that same value -- at a fresh temp directory for the
    duration of the test, restoring both on teardown."""

    def setUp(self):
        import citation_entry
        import convert_numbered_citations
        self.out_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.out_dir)
        original_entries_dir = citation_entry.ENTRIES_DIR
        citation_entry.ENTRIES_DIR = self.out_dir / "entries"
        self.addCleanup(setattr, citation_entry, "ENTRIES_DIR", original_entries_dir)
        convert_numbered_citations.ENTRIES_DIR = citation_entry.ENTRIES_DIR
        self.addCleanup(setattr, convert_numbered_citations, "ENTRIES_DIR", original_entries_dir)
        self.citation_entry = citation_entry


class TestBuildEntryKeyMap(_EntriesDirSandboxTestCase):
    def test_builds_map_and_writes_one_entry_per_listitem(self):
        from convert_numbered_citations import build_entry_key_map
        citation_entry = self.citation_entry

        fragment = self.out_dir / "fragment.xml"
        fragment.write_text("""<?xml version="1.0"?>
<section xmlns="http://docbook.org/ns/docbook" xmlns:xlink="http://www.w3.org/1999/xlink" xml:id="conclusion">
  <section xml:id="works-cited">
    <orderedlist numeration="arabic" spacing="compact">
      <listitem><para>First Source, accessed June 9, 2025, <link xlink:href="https://example.com/first">https://example.com/first</link></para></listitem>
      <listitem><para>Second Source, accessed June 9, 2025, <link xlink:href="https://example.com/second">https://example.com/second</link></para></listitem>
    </orderedlist>
  </section>
</section>
""", encoding="utf-8")
        key_map = build_entry_key_map(fragment)
        self.assertEqual(len(key_map), 2)
        self.assertTrue((citation_entry.ENTRIES_DIR / f"{key_map[1]}.xml").exists())
        self.assertTrue((citation_entry.ENTRIES_DIR / f"{key_map[2]}.xml").exists())

    def test_is_idempotent_when_called_twice_on_same_fragment(self):
        """The brief claims build_entry_key_map is safe to re-run because
        write_biblioentry no-ops on identical content. Verify live: same
        fragment, called twice, must produce an identical key_map and must
        not raise (a ValueError would mean derive_entry_key/content drifted
        between calls, which would be a real bug)."""
        from convert_numbered_citations import build_entry_key_map

        fragment = self.out_dir / "fragment.xml"
        fragment.write_text("""<?xml version="1.0"?>
<section xmlns="http://docbook.org/ns/docbook" xmlns:xlink="http://www.w3.org/1999/xlink" xml:id="conclusion">
  <section xml:id="works-cited">
    <orderedlist numeration="arabic" spacing="compact">
      <listitem><para>First Source, accessed June 9, 2025, <link xlink:href="https://example.com/first">https://example.com/first</link></para></listitem>
    </orderedlist>
  </section>
</section>
""", encoding="utf-8")
        first = build_entry_key_map(fragment)
        second = build_entry_key_map(fragment)
        self.assertEqual(first, second)


class TestBuildEntryKeyMapCollision(_EntriesDirSandboxTestCase):
    def test_two_different_sources_colliding_on_the_same_derived_key_raises(self):
        """Bug-hunt case: derive_entry_key() is not injective (documented
        in citation_entry.write_biblioentry's own docstring) -- two
        different real-world sources can derive the same key (here,
        both "https://example.com/foo/x" and "https://example.com/bar/x"
        derive "example-x", since derive_entry_key keys off host + final
        path segment only). A naive "if not entry_path.exists(): write"
        guard in build_entry_key_map would silently skip writing the
        second, genuinely different source once the first has claimed
        that path -- discarding real data with no signal, and mapping
        ordinal 2 to the WRONG entry (the first source's). write_biblioentry
        already detects exactly this mismatch and raises ValueError; this
        must propagate, not be silently swallowed by a redundant
        existence pre-check upstream."""
        from convert_numbered_citations import build_entry_key_map

        fragment = self.out_dir / "fragment.xml"
        fragment.write_text("""<?xml version="1.0"?>
<section xmlns="http://docbook.org/ns/docbook" xmlns:xlink="http://www.w3.org/1999/xlink" xml:id="conclusion">
  <section xml:id="works-cited">
    <orderedlist numeration="arabic">
      <listitem><para>First unique title <link xlink:href="https://example.com/foo/x">https://example.com/foo/x</link></para></listitem>
      <listitem><para>Second completely different title <link xlink:href="https://example.com/bar/x">https://example.com/bar/x</link></para></listitem>
    </orderedlist>
  </section>
</section>
""", encoding="utf-8")
        with self.assertRaises(ValueError):
            build_entry_key_map(fragment)


class TestConvertMarkersInFragment(unittest.TestCase):
    def _write(self, content):
        out_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, out_dir)
        path = out_dir / "fragment.xml"
        path.write_text(content, encoding="utf-8")
        return path

    def test_replaces_glued_markers_with_real_biblioref_elements(self):
        from convert_numbered_citations import convert_markers_in_fragment
        path = self._write(
            '<?xml version="1.0"?>\n'
            '<section xmlns="http://docbook.org/ns/docbook" xml:id="intro">\n'
            '  <para>LLMs process trillions of parameters.1 They exhibit long-range dependencies.2</para>\n'
            '</section>\n'
        )
        count = convert_markers_in_fragment(path, {1: "key-one", 2: "key-two"})
        self.assertEqual(count, 2)
        text = path.read_text(encoding="utf-8")
        self.assertIn('parameters.<biblioref linkend="key-one" />', text)
        self.assertIn('dependencies.<biblioref linkend="key-two" />', text)
        ET.parse(path)  # still well-formed

    def test_marker_outside_key_map_is_left_untouched(self):
        from convert_numbered_citations import convert_markers_in_fragment
        path = self._write(
            '<?xml version="1.0"?>\n'
            '<section xmlns="http://docbook.org/ns/docbook" xml:id="intro">\n'
            '  <para>An unrelated number.9 appears here.</para>\n'
            '</section>\n'
        )
        count = convert_markers_in_fragment(path, {1: "key-one"})
        self.assertEqual(count, 0)
        self.assertIn("number.9", path.read_text(encoding="utf-8"))

    def test_statute_pincite_is_not_converted_even_if_number_is_in_range(self):
        """Guards the exact false positive this task's first draft let
        through: a statute/rule number that happens to fall within the
        works-cited list's range must still not convert -- reusing
        audit_footnote_links.py's _is_excluded_context() is what
        prevents this, not just the key_map range check."""
        from convert_numbered_citations import convert_markers_in_fragment
        path = self._write(
            '<?xml version="1.0"?>\n'
            '<section xmlns="http://docbook.org/ns/docbook" xml:id="intro">\n'
            '  <para>SMC Corporate Practices NYSE Section 303A.01 requires disclosure.</para>\n'
            '</section>\n'
        )
        count = convert_markers_in_fragment(path, {1: "key-one"})
        self.assertEqual(count, 0)
        self.assertIn("303A.01", path.read_text(encoding="utf-8"))

    def test_same_marker_number_appears_twice_both_convert(self):
        """Bug-hunt case: the same footnote number cited twice in one
        fragment must convert at BOTH occurrences, not just the first
        (a naive implementation using str.replace(count=1) or a stateful
        already-converted guard could under-convert here)."""
        from convert_numbered_citations import convert_markers_in_fragment
        path = self._write(
            '<?xml version="1.0"?>\n'
            '<section xmlns="http://docbook.org/ns/docbook" xml:id="intro">\n'
            '  <para>First mention.3 Second mention of the same source.3</para>\n'
            '</section>\n'
        )
        count = convert_markers_in_fragment(path, {3: "key-three"})
        self.assertEqual(count, 2)
        text = path.read_text(encoding="utf-8")
        self.assertEqual(text.count('<biblioref linkend="key-three" />'), 2)

    def test_marker_number_zero_is_never_converted(self):
        """build_entry_key_map's ordinals are always 1-based
        (enumerate(..., start=1) -- see test_builds_map_and_writes_one_
        entry_per_listitem), so a realistic key_map never contains a 0
        key. Given such a key_map, a literal ".0" marker in the text
        must be left untouched, the same as any other out-of-range
        digit (this is convert_markers_in_fragment's ordinary "n not in
        key_map" exclusion path -- 0 has no special-cased handling, nor
        does it need any, since build_entry_key_map structurally never
        emits it)."""
        from convert_numbered_citations import convert_markers_in_fragment
        path = self._write(
            '<?xml version="1.0"?>\n'
            '<section xmlns="http://docbook.org/ns/docbook" xml:id="intro">\n'
            '  <para>Odd footnote.0 here.</para>\n'
            '</section>\n'
        )
        count = convert_markers_in_fragment(path, {1: "key-one"})
        self.assertEqual(count, 0)
        self.assertIn("footnote.0", path.read_text(encoding="utf-8"))

    def test_three_digit_marker_number_converts_when_in_key_map(self):
        """Works-cited lists in the corpus run into the 80s; verify a
        3-digit ordinal (100) still matches and converts correctly, and
        does not get truncated to a 2-digit prefix by the regex."""
        from convert_numbered_citations import convert_markers_in_fragment
        path = self._write(
            '<?xml version="1.0"?>\n'
            '<section xmlns="http://docbook.org/ns/docbook" xml:id="intro">\n'
            '  <para>A very long list.100 indeed.</para>\n'
            '</section>\n'
        )
        count = convert_markers_in_fragment(path, {100: "key-hundred"})
        self.assertEqual(count, 1)
        self.assertIn('list.<biblioref linkend="key-hundred" />', path.read_text(encoding="utf-8"))

    def test_marker_inside_title_element_is_not_converted(self):
        """Bug-hunt case: unlike audit_footnote_links.py's
        find_candidates(), which structurally excludes <title> element
        text via _element_body_text() (section headings are never real
        footnote candidates), convert_markers_in_fragment scanned the
        ENTIRE raw fragment text with no such exclusion, so a heading
        like "New Approach.5" would get corrupted into
        "New Approach.<biblioref linkend="key-five"/>" -- reproduced
        live by a task review, exact case below."""
        from convert_numbered_citations import convert_markers_in_fragment
        path = self._write(
            '<?xml version="1.0"?>\n'
            '<section xmlns="http://docbook.org/ns/docbook" xml:id="intro">\n'
            '  <title>New Approach.5</title>\n'
            '  <para>Some text.</para>\n'
            '</section>\n'
        )
        count = convert_markers_in_fragment(path, {5: "key-five"})
        self.assertEqual(count, 0)
        text = path.read_text(encoding="utf-8")
        self.assertIn("<title>New Approach.5</title>", text)
        self.assertNotIn("biblioref", text)

    def test_marker_outside_title_still_converts_when_fragment_also_has_a_title(self):
        """Companion to test_marker_inside_title_element_is_not_converted
        -- guards against an overly broad fix that accidentally excludes
        every marker in a fragment merely because SOME <title> exists
        somewhere in it. Only the marker actually inside the <title>
        span must be skipped; the one in the <para> body must still
        convert."""
        from convert_numbered_citations import convert_markers_in_fragment
        path = self._write(
            '<?xml version="1.0"?>\n'
            '<section xmlns="http://docbook.org/ns/docbook" xml:id="intro">\n'
            '  <title>New Approach.5</title>\n'
            '  <para>A real citation.5 appears here.</para>\n'
            '</section>\n'
        )
        count = convert_markers_in_fragment(path, {5: "key-five"})
        self.assertEqual(count, 1)
        text = path.read_text(encoding="utf-8")
        self.assertIn("<title>New Approach.5</title>", text)
        self.assertIn('citation.<biblioref linkend="key-five" />', text)

    def test_marker_after_inline_closing_tag_converts_correctly(self):
        """Checks the brief's stated 'known limitation' about
        <emphasis>word</emphasis>.1 directly: the character immediately
        before the marker's '.' is '>' (end of the closing tag), not a
        digit/letter, so _is_excluded_context does not exclude it, and
        the marker regex's lookahead/lookbehind do not require a letter
        immediately before the '.'. This is expected to convert
        correctly -- if it doesn't, the brief's docstring is right and
        this module needs a real fix, not just a comment."""
        from convert_numbered_citations import convert_markers_in_fragment
        path = self._write(
            '<?xml version="1.0"?>\n'
            '<section xmlns="http://docbook.org/ns/docbook" xml:id="intro">\n'
            '  <para>See <emphasis>word</emphasis>.1 for details.</para>\n'
            '</section>\n'
        )
        count = convert_markers_in_fragment(path, {1: "key-one"})
        self.assertEqual(count, 1)
        text = path.read_text(encoding="utf-8")
        self.assertIn('<emphasis>word</emphasis>.<biblioref linkend="key-one" />', text)
        ET.parse(path)  # still well-formed


class TestConvertMarkersInFragmentStructuralShapes(unittest.TestCase):
    """Task 2: covers every real marker shape Task 1's corpus survey
    found beyond the original glued "word.N" shape --
    .superpowers/sdd/task-1-survey-findings.md is the spec these tests
    encode. Reproduces the brief's own draft cases (bare space-
    separated token, whole-cell) AND the findings that supersede the
    brief's draft: em-dash-bounded bare-token, bracket-glued (no
    period), the bare-token colon-boundary false-positive exclusion,
    and whole-cell's non-universal safety (real data tables can
    coincidentally collide with a valid key_map ordinal)."""

    def _write(self, content):
        out_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, out_dir)
        path = out_dir / "fragment.xml"
        path.write_text(content, encoding="utf-8")
        return path

    def test_bare_space_separated_token_in_prose_converts(self):
        # Reproduces the real miss from commit 8de2d12: "For instance,
        # 58 describes a neural network layer" -- a bare digit token,
        # not glued to a preceding word via ".".
        from convert_numbered_citations import convert_markers_in_fragment
        path = self._write(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<section xmlns="{DB_NS}">'
            '<para>For instance, 58 describes a neural network layer.</para>'
            '</section>'
        )
        converted = convert_markers_in_fragment(path, {58: "ntrs-categories_of_neural_networkspdf"})
        self.assertEqual(converted, 1)
        text = path.read_text(encoding="utf-8")
        self.assertIn('<biblioref linkend="ntrs-categories_of_neural_networkspdf" />', text)
        self.assertNotIn(">58<", text)

    def test_whole_table_cell_bare_digit_converts_when_column_is_a_citation_column(self):
        # Reproduces the real miss from commit 8de2d12: <entry>30</entry>
        # where the cell's ENTIRE content is the bare marker digit --
        # the real pilot table's own header ("Key Snippet(s) Example"),
        # which is what makes this whole-cell candidate trustworthy
        # under the new corroboration signal (see
        # test_whole_cell_in_a_real_data_table_is_not_converted for the
        # counter-case this signal exists to reject).
        from convert_numbered_citations import convert_markers_in_fragment
        path = self._write(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<section xmlns="{DB_NS}"><informaltable><tgroup cols="2"><tbody>'
            '<row><entry>Component</entry><entry>Key Snippet(s) Example</entry></row>'
            '<row><entry>Token Embedding</entry><entry>30</entry></row>'
            '</tbody></tgroup></informaltable></section>'
        )
        converted = convert_markers_in_fragment(path, {30: "datacamp-how-transformers-work"})
        self.assertEqual(converted, 1)
        text = path.read_text(encoding="utf-8")
        self.assertIn('<biblioref linkend="datacamp-how-transformers-work" />', text)

    def test_whole_cell_in_a_real_data_table_is_not_converted(self):
        # Task 1's survey found 2 of 9 documents with whole-cell
        # candidates are real DATA tables, not citation-mapping
        # tables: us-sex-crime-law-analysis.html's "General Age of
        # Consent" column (ages 16/17/18) and tax-and-regulatory-
        # thresholds-explained.html's "Dependents" column (0/1) -- both
        # can coincidentally fall inside a valid key_map ordinal range.
        # Neither column header contains a citation-apparatus keyword
        # (source/citation/reference/snippet/research), so the
        # corroboration check must reject them even though the digit
        # is both whole-cell AND in key_map.
        from convert_numbered_citations import convert_markers_in_fragment
        path = self._write(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<section xmlns="{DB_NS}"><informaltable><tgroup cols="2"><tbody>'
            '<row><entry>State</entry><entry>General Age of Consent</entry></row>'
            '<row><entry>Alabama</entry><entry>16</entry></row>'
            '</tbody></tgroup></informaltable></section>'
        )
        converted = convert_markers_in_fragment(path, {16: "some-unrelated-source"})
        self.assertEqual(converted, 0)
        text = path.read_text(encoding="utf-8")
        self.assertNotIn("biblioref", text)
        self.assertIn(">16<", text)

    def test_whole_cell_standalone_paragraph_not_in_a_table_converts(self):
        # Real corpus shape (patron-artist-collective-work-structure,
        # fragment 07): a citation marker isolated as the ENTIRE content
        # of its own <para>, not inside any table. No known false-
        # positive shape exists for this outside a table cell (Task 1's
        # survey found the safety problem only in table <entry>
        # columns), so this converts on shape + key_map alone, same
        # discipline as ordinary bare-token.
        from convert_numbered_citations import convert_markers_in_fragment
        path = self._write(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<section xmlns="{DB_NS}"><itemizedlist><listitem>'
            '<para>Independent Trade: the worker is customarily engaged.</para>'
            '<para>78</para>'
            '</listitem></itemizedlist></section>'
        )
        converted = convert_markers_in_fragment(path, {78: "some-key"})
        self.assertEqual(converted, 1)
        text = path.read_text(encoding="utf-8")
        self.assertIn('<biblioref linkend="some-key" />', text)

    def test_ordinary_prose_number_not_in_key_map_is_left_untouched(self):
        # A bare number in prose that ISN'T a real marker (e.g. "58
        # percent of respondents") must not convert just because it's
        # a bare token -- key_map membership is still the deciding
        # factor, structural shape only changes HOW it's found.
        from convert_numbered_citations import convert_markers_in_fragment
        path = self._write(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<section xmlns="{DB_NS}">'
            '<para>Roughly 58 percent of respondents agreed.</para>'
            '</section>'
        )
        converted = convert_markers_in_fragment(path, {})  # empty key_map
        self.assertEqual(converted, 0)
        self.assertIn(">Roughly 58 percent", path.read_text(encoding="utf-8"))

    def test_em_dash_bounded_bare_token_converts(self):
        # Task 1 confirmed 5 real instances corpus-wide of a bare digit
        # marker whose TRAILING boundary is an em dash (U+2014) glued
        # directly on with no space, e.g. "...from being a business
        # 12--making Prong C..." (systemic-misclassification-final.html).
        from convert_numbered_citations import convert_markers_in_fragment
        path = self._write(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<section xmlns="{DB_NS}">'
            '<para>...from being a business 12—making Prong C difficult to satisfy.</para>'
            '</section>'
        )
        converted = convert_markers_in_fragment(path, {12: "some-source"})
        self.assertEqual(converted, 1)
        text = path.read_text(encoding="utf-8")
        self.assertIn('<biblioref linkend="some-source" />', text)
        self.assertNotIn("12—", text)

    def test_en_dash_bounded_digit_is_not_a_marker(self):
        # Task 1's caveat: em-dash adjacency alone is NOT sufficient --
        # an en dash (U+2013, a DIFFERENT character) bounds ordinary
        # non-marker numbers too, e.g. "...has reached the age of
        # 18--has the legal right..." must not convert even though 18
        # is in key_map and superficially dash-adjacent.
        from convert_numbered_citations import convert_markers_in_fragment
        path = self._write(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<section xmlns="{DB_NS}">'
            '<para>...has reached the age of 18–has the legal right to vote.</para>'
            '</section>'
        )
        converted = convert_markers_in_fragment(path, {18: "some-source"})
        self.assertEqual(converted, 0)
        self.assertIn("18–has", path.read_text(encoding="utf-8"))

    def test_bracket_glued_marker_converts(self):
        # Task 1 confirmed 1 real instance (first-amendment-and-
        # prostitution-law.html, fragment 06): a bare digit run glued
        # directly onto a closing "]" immediately after an inline
        # <emphasis> close tag, with NO period anywhere:
        # "No [<emphasis>Arcara</emphasis>]32".
        from convert_numbered_citations import convert_markers_in_fragment
        path = self._write(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<section xmlns="{DB_NS}"><informaltable><tgroup cols="1"><tbody>'
            '<row><entry>No [<emphasis>Arcara</emphasis>]32</entry></row>'
            '</tbody></tgroup></informaltable></section>'
        )
        converted = convert_markers_in_fragment(path, {32: "arcara-v-cloud-books"})
        self.assertEqual(converted, 1)
        text = path.read_text(encoding="utf-8")
        self.assertIn('<biblioref linkend="arcara-v-cloud-books" />', text)
        self.assertNotIn(">32<", text)

    def test_bare_token_immediately_followed_by_colon_is_not_converted(self):
        # Task 1's real, quantified false-positive: 484 of 8,977
        # bare-token candidates corpus-wide are "Label N:" section/list
        # headers, e.g. "Trigger 1: Non-Patron Ownership Concentration:"
        # (cooperative-tradeable-securities-research). The brief's draft
        # trailing-boundary set (").,;:]") wrongly admits ":" -- a digit
        # immediately followed by ":" must never be treated as a
        # bare-token marker candidate.
        from convert_numbered_citations import convert_markers_in_fragment
        path = self._write(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<section xmlns="{DB_NS}">'
            '<para><emphasis role="strong">Trigger 1: Non-Patron Ownership '
            'Concentration:</emphasis> If patron activity falls below plan.</para>'
            '</section>'
        )
        converted = convert_markers_in_fragment(path, {1: "some-source"})
        self.assertEqual(converted, 0)
        self.assertIn("Trigger 1:", path.read_text(encoding="utf-8"))

    def test_clock_time_digit_followed_by_colon_and_digit_is_not_converted(self):
        # Task 1's second colon-boundary sub-shape: clock times, ratios,
        # timestamps, docket numbers -- e.g. "12:30 a.m. on an evening
        # preceding a non-school day.24" (real corpus text, minors-
        # operating-businesses-in-california). "12" must not convert
        # even though it's in key_map; "24" (the real, correctly glued
        # marker at the sentence's actual end) still converts normally.
        from convert_numbered_citations import convert_markers_in_fragment
        path = self._write(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<section xmlns="{DB_NS}">'
            '<para>Curfew begins at 12:30 a.m. on an evening preceding a '
            'non-school day.24</para>'
            '</section>'
        )
        converted = convert_markers_in_fragment(path, {12: "wrong-clock-source", 24: "real-source"})
        self.assertEqual(converted, 1)
        text = path.read_text(encoding="utf-8")
        self.assertIn("12:30", text)
        self.assertIn('day.<biblioref linkend="real-source" />', text)

    def test_marker_inside_link_element_text_is_not_converted(self):
        # Task 1's largest single "other"-bucket category (5,870 of
        # 14,705, 39.9%): digit runs inside <link> element text/tail --
        # works-cited citation URLs/display text. Never markers, even
        # when structurally bare-token-shaped and numerically in
        # key_map's range. The production driver calls
        # convert_markers_in_fragment BEFORE remove_works_cited_section
        # (per docs/superpowers/sdd/2026-07-29-category-a-toolchain-
        # verification-plan.md's Task 3 loop), so the works-cited
        # section's own <link> elements are still present and must be
        # excluded structurally, the same way <title> already is.
        from convert_numbered_citations import convert_markers_in_fragment
        path = self._write(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<section xmlns="{DB_NS}" xmlns:xlink="{XLINK_NS}">'
            '<para>See <link xlink:href="https://example.com/report">Report 9</link> '
            'for details.</para>'
            '</section>'
        )
        converted = convert_markers_in_fragment(path, {9: "some-source"})
        self.assertEqual(converted, 0)
        self.assertIn("Report 9", path.read_text(encoding="utf-8"))

    def test_marker_inside_works_cited_section_body_text_is_not_converted(self):
        # Companion to the <link> exclusion above: the works-cited
        # section's own listitem PROSE (not just its <link> children)
        # is scanned too, since convert_markers_in_fragment runs on the
        # works-cited fragment before remove_works_cited_section deletes
        # it. A bare number in that prose (e.g. a volume number in a
        # source citation) must not convert even if it happens to match
        # a key_map ordinal.
        from convert_numbered_citations import convert_markers_in_fragment
        path = self._write(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<section xmlns="{DB_NS}" xml:id="conclusion">'
            '<section xml:id="works-cited"><orderedlist numeration="arabic">'
            '<listitem><para>Some Journal, Volume 9, 2025.</para></listitem>'
            '</orderedlist></section>'
            '</section>'
        )
        converted = convert_markers_in_fragment(path, {9: "some-source"})
        self.assertEqual(converted, 0)
        self.assertIn("Volume 9", path.read_text(encoding="utf-8"))


class TestRemoveWorksCitedSection(unittest.TestCase):
    def test_removes_the_section_when_present(self):
        from convert_numbered_citations import remove_works_cited_section
        path = Path(tempfile.mkdtemp()) / "fragment.xml"
        path.write_text(
            '<?xml version="1.0"?>\n'
            '<section xmlns="http://docbook.org/ns/docbook" xml:id="conclusion">\n'
            '  <para>Text.</para>\n'
            '  <section xml:id="works-cited"><orderedlist numeration="arabic"><listitem><para>X</para></listitem></orderedlist></section>\n'
            '</section>\n',
            encoding="utf-8",
        )
        removed = remove_works_cited_section(path)
        self.assertTrue(removed)
        self.assertNotIn("works-cited", path.read_text(encoding="utf-8"))

    def test_no_op_when_absent(self):
        from convert_numbered_citations import remove_works_cited_section
        path = Path(tempfile.mkdtemp()) / "fragment.xml"
        path.write_text(
            '<?xml version="1.0"?>\n'
            '<section xmlns="http://docbook.org/ns/docbook" xml:id="intro">\n'
            '  <para>Text.</para>\n'
            '</section>\n',
            encoding="utf-8",
        )
        removed = remove_works_cited_section(path)
        self.assertFalse(removed)

    def test_removes_a_direct_child_of_root_without_raising(self):
        """Bug-hunt case: root.iter() already yields root itself first.
        If the removal loop also prepended [root] before iterating (a
        plausible naive variant), the same works-cited section -- when
        it is a DIRECT child of root -- would be found twice and the
        second parent.remove(child) call would raise ValueError. This
        fragment's works-cited section is a direct child of the root
        <section>, exercising exactly that path."""
        from convert_numbered_citations import remove_works_cited_section
        path = Path(tempfile.mkdtemp()) / "fragment.xml"
        path.write_text(
            '<?xml version="1.0"?>\n'
            '<section xmlns="http://docbook.org/ns/docbook" xml:id="root">\n'
            '  <section xml:id="works-cited"><orderedlist numeration="arabic"><listitem><para>X</para></listitem></orderedlist></section>\n'
            '</section>\n',
            encoding="utf-8",
        )
        removed = remove_works_cited_section(path)
        self.assertTrue(removed)
        self.assertNotIn("works-cited", path.read_text(encoding="utf-8"))


class TestBuildEntryKeyMapMultipleWorksCitedSections(_EntriesDirSandboxTestCase):
    def test_only_the_first_works_cited_section_is_processed(self):
        """Bug-hunt case: a fragment with duplicate xml:id="works-cited"
        (invalid XML, but ElementTree doesn't enforce uniqueness) must
        not silently corrupt the key_map by having a later section's
        listitems overwrite the first section's ordinals. Document the
        actual (deliberate) behavior: only the first section found in
        document order is processed."""
        from convert_numbered_citations import build_entry_key_map
        citation_entry = self.citation_entry

        fragment = self.out_dir / "fragment.xml"
        fragment.write_text("""<?xml version="1.0"?>
<section xmlns="http://docbook.org/ns/docbook" xmlns:xlink="http://www.w3.org/1999/xlink" xml:id="root">
  <section xml:id="works-cited">
    <orderedlist numeration="arabic">
      <listitem><para>First Section Source One <link xlink:href="https://example.com/a">https://example.com/a</link></para></listitem>
    </orderedlist>
  </section>
  <section xml:id="other">
    <section xml:id="works-cited">
      <orderedlist numeration="arabic">
        <listitem><para>Second Section Source One <link xlink:href="https://example.com/b">https://example.com/b</link></para></listitem>
        <listitem><para>Second Section Source Two <link xlink:href="https://example.com/c">https://example.com/c</link></para></listitem>
      </orderedlist>
    </section>
  </section>
</section>
""", encoding="utf-8")
        key_map = build_entry_key_map(fragment)
        self.assertEqual(len(key_map), 1)
        self.assertTrue((citation_entry.ENTRIES_DIR / f"{key_map[1]}.xml").exists())


if __name__ == "__main__":
    unittest.main()

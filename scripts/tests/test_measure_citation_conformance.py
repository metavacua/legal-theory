import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class _WritesXmlFixture:
    """Shared by test classes below that need a throwaway XML fixture file."""

    def _write(self, content):
        out_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, out_dir)
        path = out_dir / "sample.xml"
        path.write_text(content, encoding="utf-8")
        return path


class TestMeasureCitationConformance(_WritesXmlFixture, unittest.TestCase):
    def test_counts_informal_works_cited_listitems_as_nonstandard(self):
        from measure_citation_conformance import measure_citation_conformance
        path = self._write("""<?xml version="1.0"?>
<article xmlns="http://docbook.org/ns/docbook" xmlns:xlink="http://www.w3.org/1999/xlink" version="5.2" xml:id="t" xml:lang="en">
  <title>T</title>
  <section xml:id="works-cited">
    <title>Works cited</title>
    <orderedlist numeration="arabic" spacing="compact">
      <listitem><para>Garbled_Entry</para></listitem>
      <listitem><para>A Case, <link xlink:href="https://example.com/a">https://example.com/a</link></para></listitem>
      <listitem><para>Another Source, <link xlink:href="https://example.com/b">https://example.com/b</link></para></listitem>
    </orderedlist>
  </section>
</article>
""")
        result = measure_citation_conformance(path)
        self.assertEqual(result["nonstandard_entries"], 3)
        self.assertEqual(result["standard_entries"], 0)
        self.assertEqual(result["unresolved_citations"], 0)
        self.assertEqual(result["resolved_citations"], 0)

    def test_counts_real_biblioentry_as_standard(self):
        from measure_citation_conformance import measure_citation_conformance
        path = self._write("""<?xml version="1.0"?>
<article xmlns="http://docbook.org/ns/docbook" xmlns:xlink="http://www.w3.org/1999/xlink" version="5.2" xml:id="t" xml:lang="en">
  <title>T</title>
  <bibliography>
    <title>References</title>
    <biblioentry xml:id="smith2020">
      <abbrev>smith2020</abbrev>
      <title>A Real Paper</title>
    </biblioentry>
    <bibliomixed xml:id="jones2021">Jones, Another Real Paper (2021).</bibliomixed>
  </bibliography>
</article>
""")
        result = measure_citation_conformance(path)
        self.assertEqual(result["standard_entries"], 2)
        self.assertEqual(result["nonstandard_entries"], 0)

    def test_citation_with_no_matching_biblioentry_is_unresolved(self):
        from measure_citation_conformance import measure_citation_conformance
        path = self._write("""<?xml version="1.0"?>
<article xmlns="http://docbook.org/ns/docbook" version="5.2" xml:id="t" xml:lang="en">
  <title>T</title>
  <para>See <citation>ghost2020</citation> for details.</para>
</article>
""")
        result = measure_citation_conformance(path)
        self.assertEqual(result["unresolved_citations"], 1)
        self.assertEqual(result["resolved_citations"], 0)

    def test_citation_matching_a_real_biblioentry_is_resolved(self):
        from measure_citation_conformance import measure_citation_conformance
        path = self._write("""<?xml version="1.0"?>
<article xmlns="http://docbook.org/ns/docbook" version="5.2" xml:id="t" xml:lang="en">
  <title>T</title>
  <para>See <citation>smith2020</citation> for details.</para>
  <bibliography>
    <biblioentry xml:id="smith2020">
      <abbrev>smith2020</abbrev>
      <title>A Real Paper</title>
    </biblioentry>
  </bibliography>
</article>
""")
        result = measure_citation_conformance(path)
        self.assertEqual(result["resolved_citations"], 1)
        self.assertEqual(result["unresolved_citations"], 0)
        self.assertEqual(result["standard_entries"], 1)

    def test_biblioref_with_no_matching_biblioentry_is_unresolved(self):
        from measure_citation_conformance import measure_citation_conformance
        path = self._write("""<?xml version="1.0"?>
<article xmlns="http://docbook.org/ns/docbook" xmlns:xlink="http://www.w3.org/1999/xlink" version="5.2" xml:id="t" xml:lang="en">
  <title>T</title>
  <para>See <biblioref linkend="ghost2020"/> for details.</para>
</article>
""")
        result = measure_citation_conformance(path)
        self.assertEqual(result["unresolved_citations"], 1)
        self.assertEqual(result["resolved_citations"], 0)

    def test_biblioref_matching_a_real_biblioentry_is_resolved(self):
        from measure_citation_conformance import measure_citation_conformance
        path = self._write("""<?xml version="1.0"?>
<article xmlns="http://docbook.org/ns/docbook" xmlns:xlink="http://www.w3.org/1999/xlink" version="5.2" xml:id="t" xml:lang="en">
  <title>T</title>
  <para>See <biblioref linkend="smith2020"/> for details.</para>
  <bibliography>
    <biblioentry xml:id="smith2020">
      <abbrev>smith2020</abbrev>
      <title>A Real Paper</title>
    </biblioentry>
  </bibliography>
</article>
""")
        result = measure_citation_conformance(path)
        self.assertEqual(result["resolved_citations"], 1)
        self.assertEqual(result["unresolved_citations"], 0)
        self.assertEqual(result["standard_entries"], 1)

    def test_citation_and_biblioref_counts_combine(self):
        from measure_citation_conformance import measure_citation_conformance
        path = self._write("""<?xml version="1.0"?>
<article xmlns="http://docbook.org/ns/docbook" xmlns:xlink="http://www.w3.org/1999/xlink" version="5.2" xml:id="t" xml:lang="en">
  <title>T</title>
  <para>See <citation>smith2020</citation> and <biblioref linkend="jones2021"/> and <biblioref linkend="ghost2020"/>.</para>
  <bibliography>
    <biblioentry xml:id="smith2020"><abbrev>smith2020</abbrev><title>A Real Paper</title></biblioentry>
    <biblioentry xml:id="jones2021"><abbrev>jones2021</abbrev><title>Another Real Paper</title></biblioentry>
  </bibliography>
</article>
""")
        result = measure_citation_conformance(path)
        self.assertEqual(result["resolved_citations"], 2)
        self.assertEqual(result["unresolved_citations"], 1)

    def test_conformance_ratio_is_standard_over_standard_plus_nonstandard(self):
        from measure_citation_conformance import measure_citation_conformance
        path = self._write("""<?xml version="1.0"?>
<article xmlns="http://docbook.org/ns/docbook" xmlns:xlink="http://www.w3.org/1999/xlink" version="5.2" xml:id="t" xml:lang="en">
  <title>T</title>
  <section xml:id="works-cited">
    <orderedlist numeration="arabic" spacing="compact">
      <listitem><para>Only nonstandard entry</para></listitem>
    </orderedlist>
  </section>
  <bibliography>
    <biblioentry xml:id="a"><abbrev>a</abbrev><title>A</title></biblioentry>
    <biblioentry xml:id="b"><abbrev>b</abbrev><title>B</title></biblioentry>
    <biblioentry xml:id="c"><abbrev>c</abbrev><title>C</title></biblioentry>
  </bibliography>
</article>
""")
        result = measure_citation_conformance(path)
        self.assertEqual(result["standard_entries"], 3)
        self.assertEqual(result["nonstandard_entries"], 1)
        self.assertAlmostEqual(result["conformance_ratio"], 0.75)

    def test_conformance_ratio_is_none_when_no_citation_content_at_all(self):
        from measure_citation_conformance import measure_citation_conformance
        path = self._write("""<?xml version="1.0"?>
<article xmlns="http://docbook.org/ns/docbook" version="5.2" xml:id="t" xml:lang="en">
  <title>T</title>
  <para>No citations here at all.</para>
</article>
""")
        result = measure_citation_conformance(path)
        self.assertIsNone(result["conformance_ratio"])
        self.assertEqual(result["standard_entries"], 0)
        self.assertEqual(result["nonstandard_entries"], 0)


class TestCorpusWideConformanceReport(unittest.TestCase):
    def test_real_corpus_produces_the_known_baseline(self):
        """Anchors this measurement against the corpus-wide count independently
        confirmed by direct grep during the 2026-07-26 review: 88 documents
        carried a works-cited section, 5,482 total informal entries. Updated
        after Task 6's pilot conversion of llms-as-categorical-systems (82
        entries, the only document that fully lost its works-cited section)
        dropped the baseline to 87 documents / 5,400 entries. If this drifts
        again, either the corpus changed (expected, update the baseline) or
        the measurement logic broke (not expected, investigate)."""
        from measure_citation_conformance import REPO_ROOT, corpus_wide_report
        report = corpus_wide_report(REPO_ROOT / "docs")
        self.assertEqual(report["total_nonstandard_entries"], 5400)
        self.assertEqual(report["documents_with_nonstandard_entries"], 87)


class TestMeasureNumberedCitationPattern(_WritesXmlFixture, unittest.TestCase):
    """The Deep-Research-style pattern confirmed 2026-07-26 by direct
    comparison against the real Google Drive original for
    llms-as-categorical-systems: a numbered works-cited list plus glued
    inline markers ("word.N", no space, immediately after a letter -- a
    real sentence-ending period is never glued to the next character)
    that correspond positionally to that list. See that document's own
    fragments for the verified real-world example this fixture logic is
    built from."""

    def test_glued_markers_within_list_range_are_plausible(self):
        from measure_citation_conformance import measure_numbered_citation_pattern
        path = self._write("""<?xml version="1.0"?>
<article xmlns="http://docbook.org/ns/docbook" version="5.2" xml:id="t" xml:lang="en">
  <title>T</title>
  <para>LLMs process trillions of parameters.1 They also exhibit long-range dependencies.2</para>
  <section xml:id="works-cited">
    <orderedlist numeration="arabic" spacing="compact">
      <listitem><para>Entry one</para></listitem>
      <listitem><para>Entry two</para></listitem>
    </orderedlist>
  </section>
</article>
""")
        result = measure_numbered_citation_pattern(path)
        self.assertEqual(result["works_cited_count"], 2)
        self.assertEqual(result["plausible_marker_count"], 2)
        self.assertEqual(result["implausible_marker_count"], 0)

    def test_marker_number_exceeding_list_length_is_implausible(self):
        from measure_citation_conformance import measure_numbered_citation_pattern
        path = self._write("""<?xml version="1.0"?>
<article xmlns="http://docbook.org/ns/docbook" version="5.2" xml:id="t" xml:lang="en">
  <title>T</title>
  <para>This cites entry five.5 which does not exist in the list.</para>
  <section xml:id="works-cited">
    <orderedlist numeration="arabic" spacing="compact">
      <listitem><para>Only entry</para></listitem>
    </orderedlist>
  </section>
</article>
""")
        result = measure_numbered_citation_pattern(path)
        self.assertEqual(result["works_cited_count"], 1)
        self.assertEqual(result["plausible_marker_count"], 0)
        self.assertEqual(result["implausible_marker_count"], 1)

    def test_no_works_cited_list_makes_any_glued_digit_implausible(self):
        from measure_citation_conformance import measure_numbered_citation_pattern
        path = self._write("""<?xml version="1.0"?>
<article xmlns="http://docbook.org/ns/docbook" version="5.2" xml:id="t" xml:lang="en">
  <title>T</title>
  <para>A stray glued number.3 with no works-cited section at all.</para>
</article>
""")
        result = measure_numbered_citation_pattern(path)
        self.assertEqual(result["works_cited_count"], 0)
        self.assertEqual(result["plausible_marker_count"], 0)
        self.assertEqual(result["implausible_marker_count"], 1)

    def test_decimal_numbers_are_not_false_positives(self):
        """A decimal like "3.5 percent" must never match -- the digit
        before the period, not a letter, is the signal that distinguishes
        it from a glued citation marker like "parameters.1"."""
        from measure_citation_conformance import measure_numbered_citation_pattern
        path = self._write("""<?xml version="1.0"?>
<article xmlns="http://docbook.org/ns/docbook" version="5.2" xml:id="t" xml:lang="en">
  <title>T</title>
  <para>The measurement increased by 3.5 percent over the period.</para>
  <section xml:id="works-cited">
    <orderedlist numeration="arabic" spacing="compact">
      <listitem><para>Entry one</para></listitem>
    </orderedlist>
  </section>
</article>
""")
        result = measure_numbered_citation_pattern(path)
        self.assertEqual(result["plausible_marker_count"], 0)
        self.assertEqual(result["implausible_marker_count"], 0)

    def test_ordinary_sentence_boundary_is_not_a_false_positive(self):
        """"...end of sentence. New sentence starts..." must never match --
        a real sentence-ending period is always followed by a space before
        the next word/number, unlike a glued marker."""
        from measure_citation_conformance import measure_numbered_citation_pattern
        path = self._write("""<?xml version="1.0"?>
<article xmlns="http://docbook.org/ns/docbook" version="5.2" xml:id="t" xml:lang="en">
  <title>T</title>
  <para>This is the end of a sentence. 2 people reviewed it afterward.</para>
  <section xml:id="works-cited">
    <orderedlist numeration="arabic" spacing="compact">
      <listitem><para>Entry one</para></listitem>
      <listitem><para>Entry two</para></listitem>
    </orderedlist>
  </section>
</article>
""")
        result = measure_numbered_citation_pattern(path)
        self.assertEqual(result["plausible_marker_count"], 0)
        self.assertEqual(result["implausible_marker_count"], 0)

    def test_real_document_confirmed_against_the_drive_original(self):
        """llms-as-categorical-systems: verified 2026-07-26 by direct
        comparison against its real Google Drive source -- originally 82
        works-cited entries, full content and order intact through the
        DocBook conversion, with glued inline markers scattered across all
        8 of its atomized fragments referencing that one shared list. Task
        6 (2026-07-26) then pilot-converted this exact document into real
        <biblioentry>/<biblioref> structure via convert_numbered_citations.py,
        so the informal works-cited list and its glued markers no longer
        exist here -- this now guards that the conversion stays converted
        (RED/GREEN oracle per measure_citation_conformance.py's own
        docstring), not that the pre-conversion pattern is still present."""
        from measure_citation_conformance import REPO_ROOT, measure_numbered_citation_pattern
        path = (
            REPO_ROOT / "docs" / "court-record" / "theory" / "federal-constitutional"
            / "extensions" / "llms-as-categorical-systems.xml"
        )
        result = measure_numbered_citation_pattern(path)
        self.assertEqual(result["works_cited_count"], 0)
        self.assertEqual(result["plausible_marker_count"], 0)


class TestCorpusWideNumberedCitationReport(unittest.TestCase):
    def test_real_corpus_baseline(self):
        from measure_citation_conformance import REPO_ROOT, corpus_wide_numbered_citation_report
        report = corpus_wide_numbered_citation_report(REPO_ROOT / "docs")
        self.assertIn("documents_with_plausible_numbered_pattern", report)
        self.assertIn("total_plausible_markers", report)
        self.assertIn("total_implausible_markers", report)
        # llms-as-categorical-systems is a real, verified positive -- must
        # always show up in the corpus-wide sweep, not just the isolated test.
        self.assertGreaterEqual(report["documents_with_plausible_numbered_pattern"], 1)

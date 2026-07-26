import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class TestMeasureCitationConformance(unittest.TestCase):
    def _write(self, content):
        out_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, out_dir)
        path = out_dir / "sample.xml"
        path.write_text(content, encoding="utf-8")
        return path

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
        carry a works-cited section, 5,482 total informal entries. If this
        drifts, either the corpus changed (expected, update the baseline) or
        the measurement logic broke (not expected, investigate)."""
        from measure_citation_conformance import REPO_ROOT, corpus_wide_report
        report = corpus_wide_report(REPO_ROOT / "docs")
        self.assertEqual(report["total_nonstandard_entries"], 5482)
        self.assertEqual(report["documents_with_nonstandard_entries"], 88)

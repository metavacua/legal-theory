import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from build_bibliography import REPO_ROOT  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "bibliography"


class TestBuildBacklinkMap(unittest.TestCase):
    def test_maps_shell_and_its_fragment_to_shells_html(self):
        from build_bibliography import build_backlink_map
        root = FIXTURES / "backlink_corpus"
        backlinks = build_backlink_map(root)

        shell_a = (root / "shell-a.xml").resolve()
        frag_a = (root / "shell-a" / "01-frag.xml").resolve()
        shell_b = (root / "shell-b.xml").resolve()

        self.assertTrue(backlinks[shell_a].endswith("backlink_corpus/shell-a.html"))
        self.assertEqual(backlinks[frag_a], backlinks[shell_a])
        self.assertTrue(backlinks[shell_b].endswith("backlink_corpus/shell-b.html"))


class TestExtractWorksCited(unittest.TestCase):
    def test_extracts_text_and_link_skips_garbled_no_link_entry_correctly(self):
        from build_bibliography import extract_works_cited
        entries = extract_works_cited(FIXTURES / "works_cited_sample.xml")
        self.assertEqual(len(entries), 3)
        self.assertEqual(entries[0], ("Systemic_Misclassification", None))
        self.assertIn("California Civil Code § 1550 (2024) - Justia Law", entries[1][0])
        self.assertEqual(
            entries[1][1],
            "https://law.justia.com/codes/california/code-civ/division-3/part-2/title-1/chapter-1/section-1550/",
        )

    def test_link_inner_text_excluded_but_surrounding_text_kept(self):
        from build_bibliography import extract_works_cited
        entries = extract_works_cited(FIXTURES / "works_cited_sample.xml")
        text, href = entries[2]
        self.assertEqual(text, "Before-text after-text")
        self.assertEqual(href, "https://example.com/x")


class TestExtractAllRawEntries(unittest.TestCase):
    def test_extracts_from_fragment_and_skips_excluded_dir(self):
        from build_bibliography import extract_all_raw_entries
        root = FIXTURES / "mini_corpus"
        entries = extract_all_raw_entries(root, exclude_dirs={"excluded"})

        self.assertEqual(len(entries), 1)
        entry = entries[0]
        self.assertEqual(entry.href, "https://example.com/a")
        self.assertTrue(entry.citing_html.endswith("mini_corpus/doc-one.html"))
        self.assertTrue(entry.source_file.endswith("doc-one/01-works-cited.xml"))


class TestNormalizeUrl(unittest.TestCase):
    def test_strips_trailing_slash(self):
        from build_bibliography import normalize_url
        self.assertEqual(normalize_url("https://onellp.com/"), "https://onellp.com")

    def test_lowercases_scheme_and_host_but_not_path(self):
        from build_bibliography import normalize_url
        self.assertEqual(
            normalize_url("HTTPS://Justia.COM/Codes/CA-Civ-1550"),
            "https://justia.com/Codes/CA-Civ-1550",
        )

    def test_preserves_www_prefix_as_is(self):
        # Adversarial: two DIFFERENT hosts (www vs bare) must NOT collide —
        # normalizing away "www." would incorrectly merge them.
        from build_bibliography import normalize_url
        self.assertNotEqual(
            normalize_url("https://www.jmbm.com/entertainment.html"),
            normalize_url("https://jmbm.com/entertainment.html"),
        )

    def test_trailing_slash_and_case_variant_dedup_to_same_key(self):
        from build_bibliography import normalize_url
        self.assertEqual(
            normalize_url("https://Justia.com/x/"),
            normalize_url("https://justia.com/x"),
        )


class TestAccessDate(unittest.TestCase):
    def test_extracts_accessed_date(self):
        from build_bibliography import extract_access_date
        text = "California Civil Code § 1550 (2024) - Justia Law, accessed September 19, 2025,"
        self.assertEqual(extract_access_date(text), "September 19, 2025")

    def test_returns_none_when_absent(self):
        from build_bibliography import extract_access_date
        self.assertIsNone(extract_access_date("No date marker here at all."))

    def test_strip_removes_accessed_clause_and_trims_punctuation(self):
        from build_bibliography import strip_access_date
        text = "Justia Law, accessed September 19, 2025,"
        self.assertEqual(strip_access_date(text), "Justia Law")

    def test_strip_preserves_unrelated_trailing_punctuation_when_clause_is_mid_string(self):
        from build_bibliography import strip_access_date
        text = "Cal. Civ. Code § 1550, accessed September 19, 2025, additional note."
        self.assertEqual(strip_access_date(text), "Cal. Civ. Code § 1550 additional note.")

    def test_does_not_match_accessed_inside_a_compound_word(self):
        from build_bibliography import strip_access_date
        text = "First accessed January 1, 2020, then re-accessed September 19, 2025,"
        self.assertEqual(strip_access_date(text), "First then re-accessed September 19, 2025,")


class TestClassifyStatute(unittest.TestCase):
    def test_classifies_known_code_with_year(self):
        from build_bibliography import classify_statute
        parsed = classify_statute("California Civil Code § 1550 (2024) - Justia Law")
        self.assertEqual(parsed["abbrev"], "Cal. Civ. Code")
        self.assertEqual(parsed["section"], "1550")
        self.assertEqual(parsed["year"], "2024")

    def test_classifies_usc(self):
        from build_bibliography import classify_statute
        parsed = classify_statute("17 U.S.C. § 101")
        self.assertEqual(parsed["abbrev"], "17 U.S.C.")
        self.assertEqual(parsed["section"], "101")
        self.assertIsNone(parsed["year"])

    def test_unrecognized_abbreviation_returns_none_not_a_guess(self):
        # Adversarial: "CORP §" is a real corpus abbreviation form NOT in the
        # lookup table. Must fall through cleanly (None), not crash, not
        # silently guess "Corporations Code".
        from build_bibliography import classify_statute
        self.assertIsNone(classify_statute("Under CORP § 202 the articles..."))

    def test_no_section_symbol_returns_none(self):
        from build_bibliography import classify_statute
        self.assertIsNone(classify_statute("California Civil Code generally"))

    def test_multi_section_usc_citation_not_truncated(self):
        from build_bibliography import classify_statute
        parsed = classify_statute("17 U.S.C. §§ 101, 106")
        self.assertEqual(parsed["section"], "101, 106")


class TestFormatStatuteBluebook(unittest.TestCase):
    def test_formats_with_known_year(self):
        from build_bibliography import format_statute_bluebook
        parsed = {"type": "statute", "abbrev": "Cal. Civ. Code", "section": "1550", "year": "2024"}
        self.assertEqual(format_statute_bluebook(parsed), "Cal. Civ. Code § 1550 (2024).")

    def test_formats_with_unknown_year_marker(self):
        from build_bibliography import format_statute_bluebook
        parsed = {"type": "statute", "abbrev": "17 U.S.C.", "section": "101", "year": None}
        self.assertEqual(format_statute_bluebook(parsed), "17 U.S.C. § 101 ([year unknown]).")

    def test_multi_section_uses_double_section_mark(self):
        from build_bibliography import format_statute_bluebook
        parsed = {"type": "statute", "abbrev": "17 U.S.C.", "section": "101, 106", "year": None}
        self.assertEqual(format_statute_bluebook(parsed), "17 U.S.C. §§ 101, 106 ([year unknown]).")


class TestClassifyCase(unittest.TestCase):
    def test_full_reporter_citation_gives_complete_bluebook_data(self):
        from build_bibliography import classify_case
        parsed = classify_case("Marvin v. Marvin (1976) 18 Cal. 3d 660.", href=None)
        self.assertEqual(parsed["name"], "Marvin v. Marvin")
        self.assertTrue(parsed["complete"])
        self.assertEqual(parsed["year"], "1976")
        self.assertEqual(parsed["volume"], "18")
        self.assertEqual(parsed["page"], "660")

    def test_courtlistener_url_without_reporter_gives_partial_case(self):
        from build_bibliography import classify_case
        parsed = classify_case(
            "Dynamex Operations West, Inc. v. Superior Court",
            href="https://www.courtlistener.com/opinion/dynamex/",
        )
        self.assertEqual(parsed["name"], "Dynamex Operations West, Inc. v. Superior Court")
        self.assertFalse(parsed["complete"])

    def test_essay_title_with_v_but_no_reporter_and_no_case_domain_is_not_a_case(self):
        # Adversarial: exactly the false-positive shape the design doc warns
        # about — title-case "X v. Y", no reporter, no case-law-aggregator URL.
        from build_bibliography import classify_case
        parsed = classify_case(
            "Privacy v. Transparency in Legal Practice",
            href="https://somelawfirmblog.example.com/privacy-vs-transparency",
        )
        self.assertIsNone(parsed)

    def test_no_v_pattern_returns_none(self):
        from build_bibliography import classify_case
        self.assertIsNone(classify_case("Restatement (Second) of Contracts § 45", href=None))

    def test_unrelated_reporter_citation_elsewhere_in_text_does_not_corroborate(self):
        from build_bibliography import classify_case
        text = ("Consent v. Coercion in Platform Contracts, discussing the reasoning in "
                "Smith (1990) 5 F.3d 100 for support.")
        self.assertIsNone(classify_case(text, href=None))

    def test_second_unrelated_case_citation_does_not_corroborate_the_first(self):
        from build_bibliography import classify_case
        text = "Consent v. Coercion in Platform Contracts (citing Marvin v. Marvin (1976) 18 Cal. 3d 660)"
        self.assertIsNone(classify_case(text, href=None))


class TestFormatCaseBluebook(unittest.TestCase):
    def test_formats_complete_citation(self):
        from build_bibliography import format_case_bluebook
        parsed = {"type": "case", "name": "Marvin v. Marvin", "complete": True,
                  "year": "1976", "volume": "18", "reporter": "Cal. 3d", "page": "660"}
        self.assertEqual(format_case_bluebook(parsed), "Marvin v. Marvin, 18 Cal. 3d 660 (1976).")

    def test_formats_partial_citation_with_flag(self):
        from build_bibliography import format_case_bluebook
        parsed = {"type": "case", "name": "Dynamex Operations West, Inc. v. Superior Court", "complete": False}
        self.assertEqual(
            format_case_bluebook(parsed),
            "Dynamex Operations West, Inc. v. Superior Court, [reporter citation unknown].",
        )


class TestFormatSecondaryChicago(unittest.TestCase):
    def test_known_publisher_with_access_date(self):
        from build_bibliography import format_secondary_chicago
        text = "California Civil Code § 1550 (2024) - Justia Law, accessed September 19, 2025,"
        result = format_secondary_chicago(text, "https://law.justia.com/codes/x")
        self.assertIn("Justia", result)
        self.assertIn("Accessed September 19, 2025", result)
        self.assertIn("https://law.justia.com/codes/x", result)

    def test_unknown_publisher_falls_back_to_bare_host_not_unknown_marker(self):
        # Adversarial: a host with no entry in KNOWN_PUBLISHERS still yields a
        # real, visible identifier (the host itself) rather than
        # "[author unknown]" — that marker is reserved for when there is truly
        # no href at all, per the no-fabrication policy's "denote empty, don't
        # omit" rule applied honestly (the host IS visible information).
        from build_bibliography import format_secondary_chicago
        result = format_secondary_chicago("Entertainment", "https://www.jmbm.com/entertainment.html")
        self.assertIn("jmbm.com", result)
        self.assertNotIn("[author unknown]", result)

    def test_no_href_and_no_access_date_marks_both_unknown(self):
        from build_bibliography import format_secondary_chicago
        result = format_secondary_chicago("Some Title With No Link", None)
        self.assertIn("[author unknown]", result)
        self.assertIn("[access date unknown]", result)
        self.assertIn("[no url]", result)

    def test_title_ending_in_ellipsis_does_not_produce_doubled_period(self):
        from build_bibliography import format_secondary_chicago
        text = "Consent and Assent Guidelines and Templates – Division of ..., accessed September 2, 2025,"
        result = format_secondary_chicago(text, "https://example.com/x")
        self.assertIn('Division of ." Accessed', result)
        self.assertNotIn("...." , result)
        self.assertNotIn('..."', result)


class TestClassifyAndFormat(unittest.TestCase):
    def test_statute_routes_to_legal(self):
        from build_bibliography import classify_and_format, RawEntry
        raw = RawEntry(text="California Civil Code § 1550 (2024)", href="https://justia.com/x",
                        citing_html="docs/x.html", source_file="docs/x.xml")
        section, display = classify_and_format(raw)
        self.assertEqual(section, "legal")
        self.assertEqual(display, "Cal. Civ. Code § 1550 (2024).")

    def test_case_with_reporter_routes_to_legal(self):
        from build_bibliography import classify_and_format, RawEntry
        raw = RawEntry(text="Marvin v. Marvin (1976) 18 Cal. 3d 660.", href=None,
                        citing_html="docs/x.html", source_file="docs/x.xml")
        section, display = classify_and_format(raw)
        self.assertEqual(section, "legal")
        self.assertIn("18 Cal. 3d 660", display)

    def test_generic_link_routes_to_secondary(self):
        from build_bibliography import classify_and_format, RawEntry
        raw = RawEntry(text="Entertainment", href="https://www.jmbm.com/entertainment.html",
                        citing_html="docs/x.html", source_file="docs/x.xml")
        section, display = classify_and_format(raw)
        self.assertEqual(section, "secondary")
        self.assertIn("jmbm.com", display)

    def test_no_link_no_pattern_routes_to_appendix(self):
        from build_bibliography import classify_and_format, RawEntry
        raw = RawEntry(text="Systemic_Misclassification", href=None,
                        citing_html="docs/x.html", source_file="docs/x.xml")
        section, display = classify_and_format(raw)
        self.assertEqual(section, "appendix")
        self.assertEqual(display, "Systemic_Misclassification")


class TestParseBibtex(unittest.TestCase):
    def test_parses_both_entries_with_correct_types_and_keys(self):
        from build_bibliography import parse_bibtex
        entries = parse_bibtex(FIXTURES / "sample.bib")
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0]["key"], "hay2024larql")
        self.assertEqual(entries[0]["entry_type"], "misc")
        self.assertEqual(entries[1]["key"], "litchfield1984")
        self.assertEqual(entries[1]["entry_type"], "article")

    def test_field_with_nested_braces_extracted_without_the_braces(self):
        from build_bibliography import parse_bibtex
        entries = parse_bibtex(FIXTURES / "sample.bib")
        title = entries[0]["fields"]["title"]
        self.assertEqual(title, "LARQL --- Lazarus Query Language: A Graph Database Interface")

    def test_no_author_field_is_simply_absent_not_fabricated(self):
        from build_bibliography import parse_bibtex
        entries = parse_bibtex(FIXTURES / "sample.bib")
        self.assertNotIn("author", entries[1]["fields"])


class TestClassifyBibEntry(unittest.TestCase):
    def test_case_type_bib_entry_routes_to_legal(self):
        from build_bibliography import classify_bib_entry
        entry = {"key": "litchfield1984", "entry_type": "article",
                  "fields": {"title": "Litchfield v. Spielberg", "year": "1984",
                             "volume": "736", "pages": "1352", "journal": "F.2d"}}
        section, display = classify_bib_entry(entry)
        self.assertEqual(section, "legal")
        self.assertIn("Litchfield v. Spielberg", display)
        self.assertIn("736 F.2d 1352 (1984)", display)

    def test_academic_bib_entry_routes_to_secondary_chicago_style(self):
        from build_bibliography import classify_bib_entry
        entry = {"key": "geva2021ffn", "entry_type": "inproceedings",
                  "fields": {"author": "Geva, Mor and Schuster, Roei and Berant, Jonathan and Levy, Omer",
                             "title": "Transformer Feed-Forward Layers Are Key-Value Memories",
                             "year": "2021", "booktitle": "EMNLP 2021"}}
        section, display = classify_bib_entry(entry)
        self.assertEqual(section, "secondary")
        self.assertIn("Geva, Mor", display)
        self.assertIn("2021", display)
        self.assertIn("Transformer Feed-Forward Layers Are Key-Value Memories", display)

    def test_missing_reporter_on_legal_entry_marked_unknown_not_omitted(self):
        # Adversarial: bartz_anthropic2025-shaped entry has no
        # volume/journal/pages (real bib: ongoing litigation, no reporter
        # cite exists yet) -- must be flagged in the output text, not
        # silently dropped or guessed.
        from build_bibliography import classify_bib_entry
        entry = {"key": "bartz_anthropic2025", "entry_type": "misc",
                  "fields": {"title": "Bartz v. Anthropic", "year": "2025"}}
        section, display = classify_bib_entry(entry)
        self.assertEqual(section, "legal")  # LEGAL_BIB_KEYS override
        self.assertIn("[reporter citation unknown]", display)
        self.assertIn("2025", display)

    def test_latex_double_section_escape_converted_and_routed_to_statute_branch(self):
        from build_bibliography import classify_bib_entry
        entry = {"key": "copyright1976fixation", "entry_type": "misc",
                  "fields": {"title": "Copyright Act of 1976, 17 U.S.C. \\S\\S 101, 106", "year": "1976"}}
        section, display = classify_bib_entry(entry)
        self.assertEqual(section, "legal")
        self.assertIn("§§ 101, 106", display)
        self.assertNotIn("\\S", display)
        self.assertNotIn("[reporter citation unknown]", display)

    def test_latex_single_section_escape_converted(self):
        from build_bibliography import classify_bib_entry
        entry = {"key": "gdpr2016", "entry_type": "misc",
                  "fields": {"title": "GDPR Article \\S 17", "year": "2016"}}
        section, display = classify_bib_entry(entry)
        self.assertEqual(section, "legal")
        self.assertIn("§ 17", display)
        self.assertNotIn("\\S", display)


class TestDedupe(unittest.TestCase):
    def test_merges_entries_with_same_normalized_url_keeping_first_seen_title(self):
        from build_bibliography import dedupe, RawEntry
        raw1 = RawEntry(text="t1", href="https://Justia.com/x/", citing_html="docs/a.html", source_file="docs/a.xml")
        raw2 = RawEntry(text="t2", href="https://justia.com/x", citing_html="docs/b.html", source_file="docs/b.xml")
        classified = [("secondary", "First Title.", raw1), ("secondary", "Second Title.", raw2)]

        result = dedupe(classified)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].display, "First Title.")
        self.assertEqual(sorted(result[0].citing_htmls), ["docs/a.html", "docs/b.html"])

    def test_distinct_urls_stay_separate(self):
        from build_bibliography import dedupe, RawEntry
        raw1 = RawEntry(text="t1", href="https://a.example.com", citing_html="docs/a.html", source_file="docs/a.xml")
        raw2 = RawEntry(text="t2", href="https://b.example.com", citing_html="docs/b.html", source_file="docs/b.xml")
        classified = [("secondary", "A.", raw1), ("secondary", "B.", raw2)]
        self.assertEqual(len(dedupe(classified)), 2)

    def test_urlless_entries_dedup_by_normalized_display_text(self):
        # Adversarial: two bib-entry-derived legal citations with no href at
        # all (e.g. two case entries) must still dedup correctly on their
        # citation string, not silently treated as always-distinct.
        from build_bibliography import dedupe, RawEntry
        raw1 = RawEntry(text="orig1", href=None, citing_html="docs/a.html", source_file="docs/a.xml")
        raw2 = RawEntry(text="orig2", href=None, citing_html="docs/b.html", source_file="docs/b.xml")
        classified = [("legal", "Bartz v. Anthropic, [reporter citation unknown] (2025).", raw1),
                      ("legal", "Bartz v. Anthropic, [reporter citation unknown] (2025).", raw2)]
        result = dedupe(classified)
        self.assertEqual(len(result), 1)
        self.assertEqual(sorted(result[0].citing_htmls), ["docs/a.html", "docs/b.html"])


class TestVerifyInvariants(unittest.TestCase):
    def _entry(self, section, display, htmls):
        from build_bibliography import BibliographyEntry
        return BibliographyEntry(section=section, display=display, citing_htmls=htmls,
                                   dedup_key=f"k:{display}")

    def test_no_entry_lost_passes_when_counts_reconcile(self):
        from build_bibliography import verify_invariants, RawEntry
        raw = [RawEntry(text="t", href=None, citing_html="docs/a.html", source_file="docs/a.xml")]
        appendix = ["t"]
        self.assertEqual(verify_invariants(raw, appendix, [], [], REPO_ROOT), [])

    def test_entry_lost_is_flagged(self):
        from build_bibliography import verify_invariants, RawEntry
        raw = [RawEntry(text="t", href=None, citing_html="docs/a.html", source_file="docs/a.xml")]
        violations = verify_invariants(raw, [], [], [], REPO_ROOT)
        self.assertTrue(any("lost" in v for v in violations))

    def test_legal_entry_missing_section_or_v_is_flagged(self):
        from build_bibliography import verify_invariants
        bad = self._entry("legal", "Some Non-Citation Text.", ["docs/a.html"])
        violations = verify_invariants([], [], [bad], [], REPO_ROOT)
        self.assertTrue(any("missing" in v.lower() for v in violations))

    def test_duplicate_normalized_url_across_entries_is_flagged(self):
        from build_bibliography import verify_invariants
        e1 = self._entry("secondary", 'X. "A." Accessed 1. https://justia.com/x', ["docs/a.html"])
        e2 = self._entry("secondary", 'Y. "B." Accessed 1. https://justia.com/x/', ["docs/b.html"])
        violations = verify_invariants([], [], [], [e1, e2], REPO_ROOT)
        self.assertTrue(any("duplicate" in v.lower() for v in violations))

    def test_dangling_backlink_is_flagged(self):
        from build_bibliography import verify_invariants
        bad = self._entry("secondary", 'X. "A." Accessed 1. https://x.com', ["docs/does-not-exist.html"])
        violations = verify_invariants([], [], [], [bad], REPO_ROOT)
        self.assertTrue(any("does-not-exist.html" in v for v in violations))

    def test_eu_directive_and_regulation_citations_satisfy_legal_marker_check(self):
        from build_bibliography import verify_invariants, BibliographyEntry
        entries = [
            BibliographyEntry(section="legal", display="Regulation (EU) 2016/679 -- GDPR (2016).", citing_htmls=["docs/papers/ai_and_ip/llm-database-theory/html/01-llm-database-theory.html"], dedup_key="k1"),
            BibliographyEntry(section="legal", display="Directive 96/9/EC on the Legal Protection of Databases (1996).", citing_htmls=["docs/papers/ai_and_ip/llm-database-theory/html/01-llm-database-theory.html"], dedup_key="k2"),
        ]
        violations = verify_invariants([], [], entries, [], REPO_ROOT)
        self.assertEqual(violations, [])


class TestEmitDocbook(unittest.TestCase):
    def test_relative_html_link_from_bibliography_dir(self):
        from build_bibliography import relative_html_link
        self.assertEqual(
            relative_html_link("docs/cross-cutting/foo.html"),
            "../cross-cutting/foo.html",
        )

    def test_emits_sections_with_alphabetized_entries_and_backlinks(self):
        from build_bibliography import emit_docbook, BibliographyEntry
        legal = [BibliographyEntry(section="legal", display="Marvin v. Marvin, 18 Cal. 3d 660 (1976).",
                                     citing_htmls=["docs/a.html"], dedup_key="k1")]
        secondary = [BibliographyEntry(section="secondary", display='Justia. "X." Accessed 1. https://justia.com/x',
                                         citing_htmls=["docs/b.html"], dedup_key="k2")]
        xml_text = emit_docbook(legal, secondary, ["Garbled Entry"])

        self.assertIn('xml:id="legal-citations"', xml_text)
        self.assertIn('xml:id="academic-secondary-sources"', xml_text)
        self.assertIn('xml:id="appendix-needs-review"', xml_text)
        self.assertIn("Marvin v. Marvin", xml_text)
        self.assertIn('xlink:href="../a.html"', xml_text)
        self.assertIn("Garbled Entry", xml_text)

    def test_emitted_xml_is_well_formed(self):
        import xml.etree.ElementTree as ET
        from build_bibliography import emit_docbook, BibliographyEntry
        legal = [BibliographyEntry(section="legal", display="A & B v. C.", citing_htmls=["docs/a.html"], dedup_key="k1")]
        xml_text = emit_docbook(legal, [], [])
        ET.fromstring(xml_text)  # raises ParseError if malformed — must not raise

    def test_emitted_article_root_carries_required_docbook_version_attribute(self):
        from build_bibliography import emit_docbook
        xml_text = emit_docbook([], [], [])
        self.assertIn('version="5.2"', xml_text)

    def test_bib_citation_backlinks_resolve_to_real_existing_html_files(self):
        from build_bibliography import _bib_citation_backlinks, PAPER_ROOT
        backlinks = _bib_citation_backlinks()
        self.assertGreater(len(backlinks), 0)
        for key, html in backlinks.items():
            html_path = REPO_ROOT / html
            self.assertTrue(html_path.is_file(), f"{key} -> {html} does not exist on disk")


class TestEndToEndIntegration(unittest.TestCase):
    def test_full_pipeline_produces_valid_docbook_with_all_four_buckets(self):
        from build_bibliography import (
            extract_all_raw_entries, parse_bibtex, classify_and_format, classify_bib_entry,
            dedupe, verify_invariants, emit_docbook, SELF_CITATION_HTML,
        )
        import xml.etree.ElementTree as ET

        root = FIXTURES / "integration_corpus"
        raw_entries = extract_all_raw_entries(root, exclude_dirs=set())
        self.assertEqual(len(raw_entries), 4)

        classified = [(*classify_and_format(r), r) for r in raw_entries]
        appendix_texts = [d for s, d, r in classified if s == "appendix"]
        legal = dedupe([c for c in classified if c[0] == "legal"])
        secondary = dedupe([c for c in classified if c[0] == "secondary"])

        self.assertEqual(len(legal), 2)     # statute + case
        self.assertEqual(len(secondary), 1)  # jmbm.com entry
        self.assertEqual(len(appendix_texts), 1)  # Systemic_Misclassification

        violations = verify_invariants(raw_entries, appendix_texts, legal, secondary, REPO_ROOT)
        self.assertEqual(violations, [])

        xml_text = emit_docbook(legal, secondary, appendix_texts)
        ET.fromstring(xml_text)  # well-formed
        self.assertIn("Cal. Civ. Code § 1550", xml_text)
        self.assertIn("Dynamex Operations West, Inc. v. Superior Court", xml_text)
        self.assertIn("[reporter citation unknown]", xml_text)
        self.assertIn("Systemic_Misclassification", xml_text)

    def test_real_bibliography_bib_parses_and_classifies_without_exceptions(self):
        # Runs Tasks 10-11 against the ACTUAL repo file, not a fixture --
        # the one place a real-file regression (e.g. an unhandled field
        # shape) would be caught before Task 16's full run.
        from build_bibliography import parse_bibtex, classify_bib_entry
        bib_path = REPO_ROOT / "docs" / "papers" / "ai_and_ip" / "llm-database-theory" / "src" / "bibliography.bib"
        entries = parse_bibtex(bib_path)
        self.assertEqual(len(entries), 28)
        for entry in entries:
            section, display = classify_bib_entry(entry)
            self.assertIn(section, ("legal", "secondary"))
            self.assertNotEqual(display.strip(), "")


if __name__ == "__main__":
    unittest.main()

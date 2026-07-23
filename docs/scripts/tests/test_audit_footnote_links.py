import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "footnote_audit"


class TestDocumentContentFiles(unittest.TestCase):
    def test_resolves_document_order_including_a_nested_include(self):
        from audit_footnote_links import document_content_files
        shell = FIXTURES / "doc_order" / "shell.xml"
        files = document_content_files(shell)
        names = [f.name for f in files]
        self.assertEqual(names, ["shell.xml", "01-frag-a.xml", "frag-a-nested.xml", "02-frag-b.xml"])


class TestFindCandidates(unittest.TestCase):
    def test_finds_real_footnotes_only_not_title_pincite_or_rule_label(self):
        from audit_footnote_links import find_candidates
        candidates = find_candidates(FIXTURES / "candidates_sample.xml")
        numbers = [c.number for c in candidates]
        self.assertEqual(numbers, [4, 12])

    def test_context_captures_text_around_the_marker(self):
        from audit_footnote_links import find_candidates
        candidates = find_candidates(FIXTURES / "candidates_sample.xml")
        self.assertIn("Dynamex", candidates[0].context)

    def test_ordinary_prose_use_of_rule_word_is_not_mistaken_for_a_label(self):
        # Adversarial: "the Common Rule" is a real named federal
        # regulation (45 CFR 46), not a numbering-label reference like
        # "Rule 2.3" -- the word "Rule" alone immediately before a
        # footnote marker must not exclude a real footnote.
        from audit_footnote_links import find_candidates
        candidates = find_candidates(FIXTURES / "rule_word_sample.xml")
        numbers = [c.number for c in candidates]
        self.assertEqual(numbers, [44])

    def test_alphanumeric_regulatory_code_pincite_excluded_real_footnote_still_found(self):
        # Whole-branch review fix: "NAC 441A.800" is not caught by the
        # digit-adjacency rule alone -- the character immediately
        # before the "." is a letter ("A"), not a digit -- so it was
        # wrongly treated as a real footnote marker (number 800),
        # inflating max_footnote and wrongly flagging real documents as
        # degenerate.
        #
        # Simplify-pass fix: the original alphanumeric-code check was
        # uppercase-only, missing a REAL, LIVE false-positive candidate
        # confirmed in the corpus -- "Chapter 9a.44 RCW" (a lowercase
        # statute-chapter suffix) in
        # docs/court-record/matters/sex-work-consent-bodily-autonomy/
        # evidence/us-sex-crime-law-analysis/
        # 04-section-iv-factual-synthesis.xml, which produced a spurious
        # Candidate(number=44, ...) before the fix unified the
        # uppercase and lowercase cases into one case-insensitive rule.
        # This fixture now covers both the uppercase ("441A") and
        # lowercase ("9a") alphanumeric-code cases in one place. A real
        # footnote with no compound-identifier tail immediately before
        # it ("...restricted asset.58") must still be found.
        from audit_footnote_links import find_candidates
        candidates = find_candidates(FIXTURES / "alphanumeric_code_sample.xml")
        numbers = [c.number for c in candidates]
        self.assertEqual(numbers, [58])

    def test_is_excluded_context_directly_flags_alphanumeric_code_prefix(self):
        # Covers both case variants of the compound-identifier-tail rule:
        # uppercase ("441A", the original NAC case) and lowercase ("9a",
        # the "Chapter 9a.44 RCW" live-corpus case), plus a plain
        # non-code prose tail that must NOT be excluded.
        from audit_footnote_links import _is_excluded_context
        self.assertTrue(_is_excluded_context("The agency relied on NAC 441A"))
        self.assertTrue(_is_excluded_context("Chapter 9a"))
        self.assertFalse(_is_excluded_context("the court found the restricted asset"))


class TestLocateWorksCited(unittest.TestCase):
    def test_finds_entries_in_whichever_fragment_has_them(self):
        from audit_footnote_links import document_content_files, locate_works_cited
        files = document_content_files(FIXTURES / "works_cited_doc" / "shell.xml")
        entries = locate_works_cited(files)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0][1], "https://example.com/a")

    def test_empty_when_no_works_cited_section_present(self):
        from audit_footnote_links import document_content_files, locate_works_cited
        files = document_content_files(FIXTURES / "doc_order" / "shell.xml")
        self.assertEqual(locate_works_cited(files), [])


class TestIsDegenerate(unittest.TestCase):
    def test_single_linkless_entry_against_many_footnotes_is_degenerate(self):
        from audit_footnote_links import is_degenerate
        entries = [("Bare Title With No Link", None)]
        self.assertTrue(is_degenerate(entries, max_footnote=72))

    def test_well_populated_linked_list_is_not_degenerate(self):
        from audit_footnote_links import is_degenerate
        entries = [(f"Source {i}", f"https://example.com/{i}") for i in range(1, 11)]
        self.assertFalse(is_degenerate(entries, max_footnote=10))


class TestMarkerCollidesWithHeading(unittest.TestCase):
    # Whole-branch review fix: the old implementation was a plain
    # substring check (marker_text in heading_text). Since marker_text
    # is always ".N", "Section 1.1:" contains ".1" as a literal
    # substring, so a real, unrelated footnote ".1" elsewhere in the
    # document would be wrongly flagged as colliding with this heading
    # -- the dominant source of the corpus's spurious "Needs manual
    # triage" flags (1136 measured). The fix requires the marker's
    # digits not be digit-adjacent in the heading text (same principle
    # as find_candidates' own _is_excluded_context).
    def test_decimal_section_number_in_heading_does_not_collide_with_unrelated_marker(self):
        from audit_footnote_links import _marker_collides_with_heading
        path = FIXTURES / "heading_word_boundary" / "doc.html"
        self.assertFalse(_marker_collides_with_heading(path, ".1"))

    def test_genuine_standalone_marker_collision_in_heading_still_detected(self):
        from audit_footnote_links import _marker_collides_with_heading
        path = FIXTURES / "heading_word_boundary" / "doc.html"
        self.assertTrue(_marker_collides_with_heading(path, ".5"))

    def test_alphanumeric_regulatory_code_in_heading_does_not_collide_with_unrelated_marker(self):
        # Simplify-pass fix: _marker_collides_with_heading originally
        # only implemented the plain-digit half of the compound-
        # identifier-tail concept -- a heading containing "Chapter
        # 9a.44 RCW" would wrongly register a collision for a real,
        # unrelated footnote ".44" elsewhere in the document. Now
        # excluded the same way _is_excluded_context excludes it.
        from audit_footnote_links import _marker_collides_with_heading
        path = FIXTURES / "heading_word_boundary" / "doc.html"
        self.assertFalse(_marker_collides_with_heading(path, ".44"))

    def test_full_doc_collision_fixture_still_flags_genuine_collision(self):
        # Regression: the real end-to-end collision fixture (a marker
        # that stands alone in the heading, not part of a larger
        # decimal number) must still be caught after the word-boundary
        # fix -- exercised directly against the lower-level function
        # here; TestAuditDocument's
        # test_heading_collision_is_flagged_not_dropped exercises the
        # same fixture through the full audit_document pipeline.
        from audit_footnote_links import _marker_collides_with_heading
        path = FIXTURES / "full_doc_collision" / "shell.html"
        self.assertTrue(_marker_collides_with_heading(path, ".9"))


class TestAuditDocument(unittest.TestCase):
    def test_audits_a_full_document_end_to_end(self):
        from audit_footnote_links import audit_document, build_backlink_map
        root = FIXTURES / "full_doc"
        shell = root / "shell.xml"
        backlinks = build_backlink_map(root)
        result = audit_document(shell, backlinks)

        self.assertEqual(len(result.candidates), 1)
        self.assertEqual(result.candidates[0].number, 4)
        self.assertEqual(len(result.works_cited), 4)
        self.assertFalse(result.degenerate)
        self.assertTrue(result.shell_html.endswith("full_doc/shell.html"))

    def test_heading_collision_is_flagged_not_dropped(self):
        # Adversarial: the marker text also happens to appear inside an
        # unrelated heading. It must survive into audit.candidates with
        # heading_collision=True -- NOT silently disappear. A dropped
        # candidate is invisible to the human reviewer, which is a worse
        # failure than a flagged one per this plan's own Global Constraints.
        from audit_footnote_links import audit_document, build_backlink_map
        root = FIXTURES / "full_doc_collision"
        shell = root / "shell.xml"
        backlinks = build_backlink_map(root)
        result = audit_document(shell, backlinks)

        self.assertEqual(len(result.candidates), 1)
        self.assertEqual(result.candidates[0].number, 9)
        self.assertTrue(result.candidates[0].heading_collision)


class TestDetectRestartIndex(unittest.TestCase):
    def test_no_restart_in_a_monotonic_sequence(self):
        from audit_footnote_links import detect_restart_index
        self.assertIsNone(detect_restart_index([1, 2, 3, 4, 158, 226, 244, 245, 246, 267]))

    def test_detects_a_real_restart_confirmed_shape(self):
        # Matches the confirmed real case: climbs to 267, then drops to
        # low integers and stays low for several subsequent markers.
        from audit_footnote_links import detect_restart_index
        numbers = [158, 226, 244, 245, 246, 267, 2, 2, 1, 3, 3, 3, 3, 3, 4, 4, 7, 3, 2, 3]
        idx = detect_restart_index(numbers)
        self.assertIsNotNone(idx)
        self.assertEqual(idx, 6)  # the first "2" after 267

    def test_heavy_reuse_of_low_numbers_is_not_mistaken_for_a_restart(self):
        # Adversarial: footnote "1" reused 9 times is normal (confirmed
        # real corpus behavior), not a restart -- there is no preceding
        # HIGH value for it to have dropped from.
        from audit_footnote_links import detect_restart_index
        numbers = [1, 1, 1, 7, 1, 1, 18, 18, 18, 18, 18, 18, 25, 30, 1, 1]
        self.assertIsNone(detect_restart_index(numbers))

    def test_single_low_outlier_amid_a_high_run_is_not_a_restart(self):
        # A single dip (ordinary out-of-order reuse) must not trigger --
        # only a drop that STAYS low for multiple subsequent markers does.
        from audit_footnote_links import detect_restart_index
        numbers = [100, 101, 102, 3, 103, 104, 105]
        self.assertIsNone(detect_restart_index(numbers))

    def test_low_number_reuse_cluster_that_resumes_climbing_is_not_a_restart(self):
        # Whole-branch review fix: this exact shape was 37 of 38 real
        # corpus restart_detected flags, all false positives -- an
        # ordinary low-number-reuse cluster mid-climb, not a genuine
        # restart. The sequence dips to 1,1,12,12,12 -- passing the old
        # heuristic's "stays low for _RESTART_RUN_LENGTH markers"
        # window check -- but then climbs right back to 33, above the
        # pre-drop value of 27, proving it was reuse, not a restart. A
        # genuine restart never climbs back near its pre-drop height.
        from audit_footnote_links import detect_restart_index
        numbers = [29, 26, 27, 1, 1, 12, 12, 12, 33]
        self.assertIsNone(detect_restart_index(numbers))

    def test_confirmed_real_restart_shape_still_detected_no_regression(self):
        # The one confirmed genuine real case must not be lost by the
        # added "stays low for the rest of the document" check --
        # re-run of test_detects_a_real_restart_confirmed_shape's exact
        # sequence to guard against regression from the Fix 4 change.
        from audit_footnote_links import detect_restart_index
        numbers = [158, 226, 244, 245, 246, 267, 2, 2, 1, 3, 3, 3, 3, 3, 4, 4, 7, 3, 2, 3]
        idx = detect_restart_index(numbers)
        self.assertIsNotNone(idx)
        self.assertEqual(idx, 6)


class TestScoreDocument(unittest.TestCase):
    def _audit(self, candidates, works_cited, degenerate=False):
        from audit_footnote_links import DocumentAudit
        return DocumentAudit(shell_html="docs/x.html", candidates=candidates, works_cited=works_cited, degenerate=degenerate)

    def test_high_confidence_linked_entry_no_restart(self):
        from audit_footnote_links import score_document, Candidate
        audit = self._audit(
            [Candidate(number=1, context="ctx")],
            [("Real Source", "https://example.com/a")],
        )
        rows = score_document(audit)
        self.assertEqual(rows[0].confidence, "High")
        self.assertEqual(rows[0].matched_entry_url, "https://example.com/a")

    def test_medium_confidence_when_entry_has_no_link(self):
        from audit_footnote_links import score_document, Candidate
        audit = self._audit(
            [Candidate(number=1, context="ctx")],
            [("Plausible Title, No Link", None)],
        )
        rows = score_document(audit)
        self.assertEqual(rows[0].confidence, "Medium")
        self.assertIn("no_link_corroboration", rows[0].flags)

    def test_needs_triage_when_footnote_exceeds_works_cited_length(self):
        from audit_footnote_links import score_document, Candidate
        audit = self._audit([Candidate(number=99, context="ctx")], [("Only One", "https://example.com/a")])
        rows = score_document(audit)
        self.assertEqual(rows[0].confidence, "Needs manual triage")
        self.assertIn("exceeds_length", rows[0].flags)

    def test_needs_triage_when_document_is_degenerate_regardless_of_other_signals(self):
        from audit_footnote_links import score_document, Candidate
        audit = self._audit(
            [Candidate(number=1, context="ctx")],
            [("Real Source", "https://example.com/a")],
            degenerate=True,
        )
        rows = score_document(audit)
        self.assertEqual(rows[0].confidence, "Needs manual triage")
        self.assertIn("degenerate_bibliography", rows[0].flags)

    def test_heading_collision_forces_needs_manual_triage(self):
        from audit_footnote_links import score_document, Candidate
        audit = self._audit(
            [Candidate(number=1, context="ctx", heading_collision=True)],
            [("Real Source", "https://example.com/a")],
        )
        rows = score_document(audit)
        self.assertEqual(rows[0].confidence, "Needs manual triage")
        self.assertIn("possible_heading_collision", rows[0].flags)

    def test_restart_downgrades_everything_from_its_index_onward(self):
        from audit_footnote_links import score_document, Candidate
        works_cited = [(f"Source {i}", f"https://example.com/{i}") for i in range(1, 6)]
        candidates = [Candidate(number=n, context="ctx") for n in [1, 2, 3, 100, 1, 1, 1]]
        audit = self._audit(candidates, works_cited)
        rows = score_document(audit)
        # First three (1,2,3) precede any restart signal and should be High;
        # the restart is only detectable once the sequence actually drops
        # back down after climbing -- rows at/after that point are downgraded.
        self.assertEqual(rows[0].confidence, "High")
        restart_flagged = [r for r in rows if "restart_detected" in r.flags]
        self.assertTrue(restart_flagged)
        for r in restart_flagged:
            self.assertNotEqual(r.confidence, "High")

    def test_compounding_no_link_and_restart_forces_needs_manual_triage(self):
        # Adversarial, not in the brief's own test list: design doc §5's
        # "Needs manual triage" tier explicitly names the COMPOUND case --
        # "entry N is itself garbled/linkless AND the footnote is also past
        # a restart point (both problems compounding)" -- as its own
        # distinct trigger, separate from either signal alone (each of
        # which, alone, is only Medium). The brief's literal Step 3 sample
        # code does not implement this: its confidence if/elif only ever
        # promotes to "Needs manual triage" for exceeds_length,
        # degenerate_bibliography, or possible_heading_collision, and
        # falls through to a flat "Medium" whenever restart_detected or
        # no_link_corroboration is present -- regardless of whether BOTH
        # are present together. See the deviation note next to
        # score_document for the fix (an explicit compound check ANDing
        # the two flags into the Needs-manual-triage branch).
        from audit_footnote_links import score_document, Candidate
        works_cited = [("Plausible Title, No Link", None)] + [
            (f"Source {i}", f"https://example.com/{i}") for i in range(2, 6)
        ]
        candidates = [Candidate(number=n, context="ctx") for n in [1, 2, 3, 100, 1, 1, 1]]
        audit = self._audit(candidates, works_cited)
        rows = score_document(audit)
        compound_rows = [r for r in rows if "restart_detected" in r.flags and "no_link_corroboration" in r.flags]
        self.assertTrue(compound_rows)
        for r in compound_rows:
            self.assertEqual(r.confidence, "Needs manual triage")


class TestWriteReport(unittest.TestCase):
    def test_writes_expected_csv_columns_and_deterministic_order(self):
        import csv
        from audit_footnote_links import write_report, AuditRow, Candidate
        rows_by_shell = {
            "docs/b.html": [AuditRow(candidate=Candidate(number=2, context="b ctx"),
                                       matched_entry_text="B", matched_entry_url="https://example.com/b",
                                       confidence="High", flags=[])],
            "docs/a.html": [AuditRow(candidate=Candidate(number=1, context="a ctx"),
                                       matched_entry_text=None, matched_entry_url=None,
                                       confidence="Needs manual triage", flags=["exceeds_length"])],
        }
        out = FIXTURES / "report_out.csv"
        self.addCleanup(out.unlink)
        write_report(rows_by_shell, out)
        with open(out, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        self.assertEqual(rows[0]["file"], "docs/a.html")
        self.assertEqual(rows[1]["file"], "docs/b.html")
        self.assertEqual(rows[0]["flags"], "exceeds_length")

    def test_multiple_rows_within_the_same_file_sort_by_footnote_number(self):
        # Adversarial: the brief's own sample sorts on (row["file"],
        # row["footnote_number"]) where footnote_number is stored as an
        # int in the dict handed to DictWriter -- but two documents with
        # footnote numbers like 2 and 10 must sort numerically (2 before
        # 10), not lexicographically ("10" before "2"), within the same
        # file. Confirms the flat-dict sort key is genuinely numeric.
        from audit_footnote_links import write_report, AuditRow, Candidate
        rows_by_shell = {
            "docs/c.html": [
                AuditRow(candidate=Candidate(number=10, context="ten"),
                         matched_entry_text=None, matched_entry_url=None,
                         confidence="Medium", flags=[]),
                AuditRow(candidate=Candidate(number=2, context="two"),
                         matched_entry_text=None, matched_entry_url=None,
                         confidence="Medium", flags=[]),
            ],
        }
        out = FIXTURES / "report_out_numeric.csv"
        self.addCleanup(out.unlink)
        write_report(rows_by_shell, out)
        with open(out, newline="", encoding="utf-8") as f:
            import csv
            rows = list(csv.DictReader(f))
        self.assertEqual([r["footnote_number"] for r in rows], ["2", "10"])

    def test_context_snippet_containing_a_comma_and_newline_round_trips_safely(self):
        # Real corpus prose in body_context_snippet will routinely
        # contain commas, and (less often but plausibly, e.g. via
        # collapsed <literallayout> or a stray embedded line break)
        # newlines. Confirms Python's csv module quotes/escapes both so
        # the row structure -- column count and content -- survives a
        # full write/read round trip unmangled, rather than a comma
        # silently splitting into an extra column or a newline splitting
        # into an extra row.
        import csv
        from audit_footnote_links import write_report, AuditRow, Candidate
        tricky_context = "the court held, per Dynamex,\nthat ABC applies"
        rows_by_shell = {
            "docs/tricky.html": [
                AuditRow(candidate=Candidate(number=1, context=tricky_context),
                         matched_entry_text="Some Title, With A Comma",
                         matched_entry_url="https://example.com/x",
                         confidence="High", flags=["exceeds_length", "no_link_corroboration"]),
            ],
        }
        out = FIXTURES / "report_out_tricky.csv"
        self.addCleanup(out.unlink)
        write_report(rows_by_shell, out)
        with open(out, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["body_context_snippet"], tricky_context)
        self.assertEqual(rows[0]["matched_works_cited_entry"], "Some Title, With A Comma")
        self.assertEqual(rows[0]["flags"], "exceeds_length;no_link_corroboration")


class TestMain(unittest.TestCase):
    def test_main_writes_report_against_a_fixture_corpus(self):
        from audit_footnote_links import main
        out_path = FIXTURES / "mini_corpus_report.csv"
        self.addCleanup(out_path.unlink)
        exit_code = main(["--corpus-root", str(FIXTURES / "mini_corpus"), "--out", str(out_path)])
        self.assertEqual(exit_code, 0)
        self.assertTrue(out_path.is_file())
        content = out_path.read_text(encoding="utf-8")
        self.assertIn("mini_corpus/doc.html", content)
        self.assertIn("High", content)


class TestEndToEndIntegration(unittest.TestCase):
    """Runs the real main() CLI (not audit_document() directly) against
    fixture corpora under fixtures/footnote_audit/integration_corpus/,
    to exercise the whole Task 1-8 pipeline as a user would invoke it.

    Scope, as of the Task 10 review fix: doc-a/doc-b (below) cover a
    clean High-confidence single-file document and a degenerate
    single-file document, but both are single files with no
    xi:include -- document_content_files/locate_works_cited's
    cross-fragment assembly (works-cited living in a DIFFERENT file
    from the body) was never exercised through main(), only at the
    lower-level audit_document() unit-test layer (TestAuditDocument
    above). Nor were a genuine Medium (linkless entry) row or a
    restart-detected row -- including the compound
    restart_detected AND no_link_corroboration "Needs manual triage"
    rule -- ever produced via main(). doc-c below (a multi-fragment
    document) closes those gaps, and test_real_corpus_runs_without_exceptions
    adds the one test in this suite that runs the actual pipeline
    against the real corpus rather than a synthetic fixture, mirroring
    build_bibliography.py's own
    test_real_bibliography_bib_parses_and_classifies_without_exceptions."""

    def test_full_pipeline_produces_the_expected_confidence_distribution(self):
        from audit_footnote_links import main
        import csv
        out_path = FIXTURES / "integration_report.csv"
        self.addCleanup(out_path.unlink)
        exit_code = main(["--corpus-root", str(FIXTURES / "integration_corpus"), "--out", str(out_path)])
        self.assertEqual(exit_code, 0)

        with open(out_path, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))

        doc_a_rows = [r for r in rows if "doc-a" in r["file"]]
        doc_b_rows = [r for r in rows if "doc-b" in r["file"]]

        self.assertEqual(len(doc_a_rows), 1)
        self.assertEqual(doc_a_rows[0]["confidence_tier"], "High")

        self.assertEqual(len(doc_b_rows), 3)
        for r in doc_b_rows:
            self.assertEqual(r["confidence_tier"], "Needs manual triage")
            self.assertIn("degenerate_bibliography", r["flags"])

    def test_cross_fragment_document_exercises_medium_and_restart_tiers_via_main(self):
        # doc-c is a shell whose body lives in one xi:include fragment
        # (doc-c/01-body.xml) and whose works-cited section lives in a
        # SEPARATE xi:include fragment (doc-c/02-works-cited.xml) -- unlike
        # doc-a/doc-b (single-file documents), this is the only fixture in
        # this class that exercises document_content_files/
        # locate_works_cited's cross-file assembly through the real main()
        # CLI, rather than only at the audit_document() unit-test layer.
        #
        # The footnote sequence in the body fragment is (1, 2, 3, 23, 2, 2,
        # 2): an early clean run, then a climb to 23 and a drop to 2 that
        # STAYS at 2 for three subsequent markers AND never climbs back
        # near 23 for the rest of the document -- a genuine restart shape
        # under both the original heuristic (drop >= _RESTART_DROP_THRESHOLD
        # =20, landing at/below _RESTART_LOW_CEILING=10, sustained for
        # _RESTART_RUN_LENGTH=3 markers) and the whole-branch-review "stays
        # low for the rest of the document" check added to
        # detect_restart_index. (The jump value was 22 pre-fix, exactly
        # _RESTART_DROP_THRESHOLD above the dip value of 2 -- the new
        # "remainder never returns to within threshold of prev" check's
        # own dip value sits exactly on that boundary in that case,
        # ambiguously self-triggering the "climbed back" exclusion. 23 is
        # the smallest value clear of that boundary that also keeps
        # max_footnote (23) from tripping is_degenerate against this
        # fixture's 11 works-cited entries -- 35 works for the restart
        # shape alone but 11 < 35//2 flags the whole document
        # degenerate_bibliography, masking the Medium/restart rows this
        # test exists to exercise.) The works-cited fragment's entry for
        # footnote 2 ("Second Source, No Link") has no <link>, so the FIRST
        # "2" (index 1, before any restart is detectable) earns a genuine
        # Medium row on no_link_corroboration alone; the three "2"s after
        # the restart earn restart_detected (and, since they resolve to
        # the same linkless entry, also exercise the compound
        # Needs-manual-triage rule).
        from audit_footnote_links import main
        import csv
        out_path = FIXTURES / "integration_report_multi.csv"
        self.addCleanup(out_path.unlink)
        exit_code = main(["--corpus-root", str(FIXTURES / "integration_corpus"), "--out", str(out_path)])
        self.assertEqual(exit_code, 0)

        with open(out_path, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))

        doc_c_rows = [r for r in rows if "doc-c" in r["file"]]
        self.assertTrue(doc_c_rows, "doc-c should have produced at least one row")

        medium_no_link_rows = [
            r for r in doc_c_rows
            if r["confidence_tier"] == "Medium" and "no_link_corroboration" in r["flags"]
        ]
        self.assertTrue(
            medium_no_link_rows,
            "expected at least one genuine Medium row with no_link_corroboration",
        )

        restart_rows = [r for r in doc_c_rows if "restart_detected" in r["flags"]]
        self.assertTrue(restart_rows, "expected at least one restart_detected row")

        # Cross-file assembly proof: the works-cited entries live in a
        # fragment separate from the body. If locate_works_cited's
        # cross-file search were broken (e.g. it only ever looked at the
        # shell or the body fragment), works_cited would resolve to []
        # and every doc-c row would show an empty matched_works_cited_entry
        # and an exceeds_length flag instead of a real match.
        matched_entries = [r["matched_works_cited_entry"] for r in doc_c_rows if r["matched_works_cited_entry"]]
        self.assertTrue(
            matched_entries,
            "expected at least one doc-c row matched against the fragment's works-cited entries",
        )
        self.assertTrue(any("Source" in e for e in matched_entries))

    def test_real_corpus_runs_without_exceptions(self):
        # Mirrors build_bibliography.py's own
        # test_real_bibliography_bib_parses_and_classifies_without_exceptions:
        # runs the actual pipeline against the real corpus (docs/, with the
        # default exclude dirs), not a synthetic fixture -- the one test in
        # this suite that would catch a real-file-shape regression no
        # fixture happens to test. Structural assertions only (exit code,
        # output file exists and is non-empty): exact tier counts will
        # drift as the corpus grows, so they are not asserted here.
        from audit_footnote_links import main, REPO_ROOT
        out_path = FIXTURES / "real_corpus_report.csv"
        self.addCleanup(out_path.unlink)
        exit_code = main(["--corpus-root", str(REPO_ROOT / "docs"), "--out", str(out_path)])
        self.assertEqual(exit_code, 0)
        self.assertTrue(out_path.is_file())
        content = out_path.read_text(encoding="utf-8")
        self.assertTrue(len(content.strip()) > 0)


if __name__ == "__main__":
    unittest.main()

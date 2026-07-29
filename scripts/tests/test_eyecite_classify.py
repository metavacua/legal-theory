import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    import eyecite  # noqa: F401
    EYECITE_AVAILABLE = True
except ImportError:
    EYECITE_AVAILABLE = False

SKIP_REASON = (
    "eyecite is not installed under this interpreter -- it lives only "
    "in the dedicated .venv-eyecite/ virtualenv, not the bare system "
    "python3 every other script/test in this repo runs under. Run this "
    "test file with .venv-eyecite/bin/python3 to exercise it."
)


@unittest.skipUnless(EYECITE_AVAILABLE, SKIP_REASON)
class TestClassifyCitationText(unittest.TestCase):
    def test_full_case_citation_resolves_as_case(self):
        from eyecite_classify import classify_citation_text
        result = classify_citation_text(
            "This references Alice Corp. v. CLS Bank Int'l, 573 U.S. 208 (2014) directly."
        )
        self.assertEqual(result["role"], "case")
        self.assertTrue(result["resolved"])
        self.assertIn("573 U.S. 208", result["parsed"])

    def test_full_law_citation_resolves_as_statute(self):
        from eyecite_classify import classify_citation_text
        result = classify_citation_text("See 17 U.S.C. § 512(c) for the safe harbor.")
        self.assertEqual(result["role"], "statute")
        self.assertTrue(result["resolved"])
        self.assertIn("17 U.S.C. § 512", result["parsed"])

    def test_webpage_title_without_a_real_citation_does_not_resolve(self):
        """The corpus's actual works-cited text -- confirmed 2026-07-26
        that eyecite correctly finds nothing here, because there is
        nothing there to find (no reporter citation, just a webpage
        title mentioning a case name)."""
        from eyecite_classify import classify_citation_text
        result = classify_citation_text(
            "Alice v. CLS Bank: United States Supreme Court Establishes "
            "General Patentability Test, accessed September 2, 2025,"
        )
        self.assertFalse(result["resolved"])
        self.assertIsNone(result["role"])
        self.assertIsNone(result["parsed"])

    def test_statute_symbol_alone_is_unresolved_not_a_confident_statute(self):
        """A bare "§" glued into aggregator-title noise is flagged
        UnknownCitation by eyecite, not a confidently-typed statute --
        confirmed 2026-07-26 by direct testing. Must not be reported
        as role="statute" on that weak a signal."""
        from eyecite_classify import classify_citation_text
        result = classify_citation_text(
            "California Code, Corporations Code - CORP § 12200 - Codes - FindLaw"
        )
        self.assertFalse(result["resolved"])
        self.assertIsNone(result["role"])

    def test_empty_string_does_not_raise_and_is_unresolved(self):
        """eyecite.get_citations("") itself raises ValueError (confirmed
        2026-07-26 by reading eyecite/models.py Document.__post_init__ --
        it requires plain_text or markup_text to be non-empty). The
        wrapper's contract is to always return a dict, never raise, so
        it must guard this case at its own boundary rather than let the
        exception propagate to callers (Task 4, the pilot task)."""
        from eyecite_classify import classify_citation_text
        result = classify_citation_text("")
        self.assertEqual(result, {"role": None, "resolved": False, "parsed": None})

    def test_whitespace_only_string_is_unresolved(self):
        from eyecite_classify import classify_citation_text
        result = classify_citation_text("   \n\t  ")
        self.assertEqual(result, {"role": None, "resolved": False, "parsed": None})

    def test_plain_prose_with_no_citation_is_unresolved(self):
        from eyecite_classify import classify_citation_text
        result = classify_citation_text("no citation here at all just plain prose")
        self.assertFalse(result["resolved"])
        self.assertIsNone(result["role"])

    def test_multiple_citations_returns_the_first_in_document_order(self):
        """When a string contains more than one resolvable citation,
        classify_citation_text reports only one classification (the
        interface returns a single role/parsed pair, not a list) --
        confirmed 2026-07-26 by direct testing that eyecite returns
        citations in text order. The wrapper returns the first
        Full{Case,Law}Citation it encounters, not "the most
        significant" or all of them. This test pins that behavior so
        it isn't silently changed later."""
        from eyecite_classify import classify_citation_text
        result = classify_citation_text(
            "See Alice Corp. v. CLS Bank Int'l, 573 U.S. 208 (2014) "
            "and also 17 U.S.C. § 512(c) for more."
        )
        self.assertEqual(result["role"], "case")
        self.assertIn("573 U.S. 208", result["parsed"])

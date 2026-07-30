import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

GOOD_SHELL = """<?xml version='1.0' encoding='utf-8'?>
<article xmlns="http://docbook.org/ns/docbook" xmlns:xi="http://www.w3.org/2001/XInclude" version="5.2" xml:id="test-article" xml:lang="en">
  <info><title>Test Article</title></info>
  <xi:include href="fragment.xml" />
</article>
"""

GOOD_FRAGMENT = """<?xml version='1.0' encoding='utf-8'?>
<section xmlns="http://docbook.org/ns/docbook" xml:id="good-section">
  <title>Good Section</title>
  <para>This section has everything DocBook 5.2 requires.</para>
</section>
"""

BROKEN_FRAGMENT = """<?xml version='1.0' encoding='utf-8'?>
<section xmlns="http://docbook.org/ns/docbook" xml:id="broken-section">
  <para>This section is missing its required title element.</para>
</section>
"""

# Real DocBook content, but not a root element docbookxi.rnc's own
# `start =` production exports standalone -- shared by TestClassify and
# TestMain, which both need exactly this shape to exercise the "skip,
# with a reason" path.
BIBLIOENTRY_FIXTURE = (
    '<?xml version="1.0"?>\n'
    '<biblioentry xmlns="http://docbook.org/ns/docbook"><abbrev>x</abbrev></biblioentry>\n'
)

# A structurally complete fragment whose <biblioref> targets an
# xml:id that only exists in a sibling bibliography-entry file the
# fragment's own shell XIncludes elsewhere (not this fragment, and not
# anything this fragment itself includes) -- exactly the real,
# already-committed shape of docs/court-record/theory/federal-
# constitutional/extensions/llms-as-categorical-systems/*.xml, which
# jing correctly reports as an unresolvable IDREF when this fragment
# is validated on its own. This is not a defect in the fragment: ID/
# IDREF completeness is a property of the assembled document, and no
# standalone fragment that cites a bibliography entry from a sibling
# file can ever satisfy it alone.
FRAGMENT_WITH_UNRESOLVABLE_BIBLIOREF = """<?xml version='1.0' encoding='utf-8'?>
<section xmlns="http://docbook.org/ns/docbook" xml:id="cites-out">
  <title>Cites Something Elsewhere</title>
  <para>See <biblioref linkend="defined-in-a-sibling-file-this-fragment-never-includes"/>.</para>
</section>
"""

# Same unresolvable cross-file biblioref, PLUS a genuine, independent
# structural defect (missing <title>) -- proves the cross-document-
# IDREF allowance doesn't mask a real defect riding along with it.
FRAGMENT_WITH_UNRESOLVABLE_BIBLIOREF_AND_MISSING_TITLE = """<?xml version='1.0' encoding='utf-8'?>
<section xmlns="http://docbook.org/ns/docbook" xml:id="cites-out-and-broken">
  <para>See <biblioref linkend="defined-in-a-sibling-file-this-fragment-never-includes"/>.</para>
</section>
"""


class _WritesFilesFixture:
    """Shared by test classes below that need real sibling files on
    disk -- xmllint's XInclude resolution follows a relative href
    against the including file's OWN location on disk, so a
    shell-plus-fragment test needs both to actually exist as sibling
    files, not just as in-memory/parsed XML."""

    def _dir(self):
        d = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, d)
        return d

    def _write(self, dir_path, name, content):
        path = dir_path / name
        path.write_text(content, encoding="utf-8")
        return path


class _HasSchemaFixture:
    """Shared by test classes below that need self.schema -- the real,
    cached DocBook 5.2 grammar path -- rather than each repeating the
    same two-line setUp."""

    def setUp(self):
        from check_docbook_grammar import fetch_docbook_schema
        self.schema = fetch_docbook_schema()
        super().setUp()


class TestResolveXinclude(_WritesFilesFixture, unittest.TestCase):
    def test_merges_a_good_include_into_the_resolved_text(self):
        from check_docbook_grammar import resolve_xinclude
        d = self._dir()
        self._write(d, "fragment.xml", GOOD_FRAGMENT)
        shell = self._write(d, "shell.xml", GOOD_SHELL)
        resolved_text, error = resolve_xinclude(shell)
        self.assertIsNone(error)
        self.assertNotIn("xi:include", resolved_text)
        self.assertIn("Good Section", resolved_text)

    def test_a_file_with_no_includes_at_all_resolves_unchanged(self):
        from check_docbook_grammar import resolve_xinclude
        d = self._dir()
        frag = self._write(d, "plain.xml", GOOD_FRAGMENT)
        resolved_text, error = resolve_xinclude(frag)
        self.assertIsNone(error)
        self.assertIn("Good Section", resolved_text)

    def test_reports_a_missing_include_target_as_an_error_not_a_crash(self):
        from check_docbook_grammar import resolve_xinclude
        d = self._dir()
        shell = self._write(
            d, "shell.xml", GOOD_SHELL.replace("fragment.xml", "does-not-exist.xml")
        )
        resolved_text, error = resolve_xinclude(shell)
        self.assertIsNone(resolved_text)
        self.assertIsNotNone(error)
        self.assertIn("does-not-exist.xml", error)


class TestValidateGrammar(_HasSchemaFixture, unittest.TestCase):
    def test_accepts_valid_resolved_text(self):
        from check_docbook_grammar import validate_grammar
        errors = validate_grammar(GOOD_FRAGMENT, self.schema, "source.xml")
        self.assertEqual(errors, [])

    def test_rejects_a_structurally_broken_document(self):
        from check_docbook_grammar import validate_grammar
        errors = validate_grammar(BROKEN_FRAGMENT, self.schema, "source.xml")
        self.assertTrue(errors)
        self.assertIn("title", " ".join(errors))

    def test_error_messages_reference_the_source_label_not_a_temp_path(self):
        from check_docbook_grammar import validate_grammar
        errors = validate_grammar(BROKEN_FRAGMENT, self.schema, "my-real-source.xml")
        joined = " ".join(errors)
        self.assertIn("my-real-source.xml", joined)
        self.assertNotIn(tempfile.gettempdir(), joined)


class TestValidateResolvedDocument(_HasSchemaFixture, _WritesFilesFixture, unittest.TestCase):

    def test_passes_a_good_shell_with_a_good_included_fragment(self):
        from check_docbook_grammar import validate_resolved_document
        d = self._dir()
        self._write(d, "fragment.xml", GOOD_FRAGMENT)
        shell = self._write(d, "shell.xml", GOOD_SHELL)
        self.assertEqual(validate_resolved_document(shell, self.schema), [])

    def test_catches_a_defect_hidden_inside_an_included_fragment(self):
        # The regression case this whole module exists for: the
        # shell's OWN literal content (an <xi:include> placeholder)
        # has nothing wrong with it in isolation -- the defect only
        # exists inside the fragment the include points at, and is
        # only visible once that fragment's content is actually
        # resolved into the tree.
        from check_docbook_grammar import validate_resolved_document
        d = self._dir()
        self._write(d, "fragment.xml", BROKEN_FRAGMENT)
        shell = self._write(d, "shell.xml", GOOD_SHELL)
        errors = validate_resolved_document(shell, self.schema)
        self.assertTrue(errors)
        self.assertIn("title", " ".join(errors))

    def test_passes_a_standalone_fragment_with_no_parent_shell_at_all(self):
        from check_docbook_grammar import validate_resolved_document
        d = self._dir()
        frag = self._write(d, "fragment.xml", GOOD_FRAGMENT)
        self.assertEqual(validate_resolved_document(frag, self.schema), [])

    def test_rejects_a_standalone_broken_fragment_with_no_parent_shell(self):
        from check_docbook_grammar import validate_resolved_document
        d = self._dir()
        frag = self._write(d, "fragment.xml", BROKEN_FRAGMENT)
        errors = validate_resolved_document(frag, self.schema)
        self.assertTrue(errors)

    def test_a_missing_include_target_is_reported_as_a_validation_error(self):
        from check_docbook_grammar import validate_resolved_document
        d = self._dir()
        shell = self._write(
            d, "shell.xml", GOOD_SHELL.replace("fragment.xml", "does-not-exist.xml")
        )
        errors = validate_resolved_document(shell, self.schema)
        self.assertTrue(errors)
        self.assertIn("does-not-exist.xml", " ".join(errors))


class TestValidateResolvedDocumentAgainstRealCorpusFiles(_HasSchemaFixture, unittest.TestCase):
    """A small number of real corpus documents, independently confirmed
    clean during design: xmllint --noout --xinclude, raw jing, AND a
    grep for markdown-remnant syntax (**/*|pipe-tables) all confirmed
    clean for every file in this specific paper. NOT the whole corpus
    -- see this plan's Global Constraints and Design Note 3."""

    def test_a_real_shell_article_with_eleven_real_xincluded_fragments(self):
        from check_docbook_grammar import validate_resolved_document
        path = REPO_ROOT / "docs/papers/ai_and_ip/llm-database-theory/src/01-llm-database-theory.xml"
        self.assertEqual(validate_resolved_document(path, self.schema), [])

    def test_a_real_standalone_section_fragment(self):
        from check_docbook_grammar import validate_resolved_document
        path = (
            REPO_ROOT
            / "docs/papers/ai_and_ip/llm-database-theory/src/01-llm-database-theory/01-the-position.xml"
        )
        self.assertEqual(validate_resolved_document(path, self.schema), [])

    def test_a_real_standalone_info_metadata_file_with_its_own_nested_includes(self):
        from check_docbook_grammar import validate_resolved_document
        path = REPO_ROOT / "docs/papers/ai_and_ip/llm-database-theory/src/01-llm-database-theory.meta.xml"
        self.assertEqual(validate_resolved_document(path, self.schema), [])


class TestClassify(_WritesFilesFixture, unittest.TestCase):
    def test_article_root_is_validated(self):
        from check_docbook_grammar import classify
        d = self._dir()
        path = self._write(d, "a.xml", GOOD_SHELL)
        self.assertEqual(classify(path), ("validate", None))

    def test_section_root_is_validated(self):
        from check_docbook_grammar import classify
        d = self._dir()
        path = self._write(d, "s.xml", GOOD_FRAGMENT)
        self.assertEqual(classify(path), ("validate", None))

    def test_info_root_is_validated(self):
        from check_docbook_grammar import classify
        d = self._dir()
        path = self._write(
            d, "i.xml",
            '<?xml version="1.0"?>\n<info xmlns="http://docbook.org/ns/docbook"><title>T</title></info>\n',
        )
        self.assertEqual(classify(path), ("validate", None))

    def test_legalnotice_root_is_validated(self):
        from check_docbook_grammar import classify
        d = self._dir()
        path = self._write(
            d, "l.xml",
            '<?xml version="1.0"?>\n<legalnotice xmlns="http://docbook.org/ns/docbook"><para>Copyright.</para></legalnotice>\n',
        )
        self.assertEqual(classify(path), ("validate", None))

    def test_biblioentry_root_is_skipped_with_a_reason(self):
        from check_docbook_grammar import classify
        d = self._dir()
        path = self._write(d, "b.xml", BIBLIOENTRY_FIXTURE)
        status, reason = classify(path)
        self.assertEqual(status, "skip")
        self.assertIn("biblioentry", reason)

    def test_authorgroup_root_is_skipped_with_a_reason(self):
        from check_docbook_grammar import classify
        d = self._dir()
        path = self._write(
            d, "ag.xml",
            '<?xml version="1.0"?>\n<authorgroup xmlns="http://docbook.org/ns/docbook"><author/></authorgroup>\n',
        )
        status, reason = classify(path)
        self.assertEqual(status, "skip")
        self.assertIn("authorgroup", reason)

    def test_non_docbook_namespace_root_is_skipped_with_a_reason(self):
        # Reproduces docs/sitemap.xml's actual shape: a totally
        # different XML vocabulary that happens to live under docs/
        # and match *.xml, not a DocBook document at all.
        from check_docbook_grammar import classify
        d = self._dir()
        path = self._write(
            d, "sitemap.xml",
            '<?xml version="1.0"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
            '<url><loc>x</loc></url></urlset>\n',
        )
        status, reason = classify(path)
        self.assertEqual(status, "skip")
        self.assertIn("namespace", reason)

    def test_an_unparseable_root_defaults_to_validate_not_a_silent_skip(self):
        # Fail-open: a file this broken should surface a real error
        # through validate_resolved_document(), never disappear
        # silently the way this whole module exists to stop happening.
        from check_docbook_grammar import classify
        d = self._dir()
        path = self._write(d, "bad.xml", "not even xml")
        self.assertEqual(classify(path), ("validate", None))


class TestMain(_WritesFilesFixture, unittest.TestCase):
    def test_returns_zero_for_a_clean_file_list(self):
        from check_docbook_grammar import main
        d = self._dir()
        self._write(d, "fragment.xml", GOOD_FRAGMENT)
        shell = self._write(d, "shell.xml", GOOD_SHELL)
        self.assertEqual(main([str(shell)]), 0)

    def test_returns_nonzero_and_prints_a_useful_message_for_a_broken_file(self):
        from check_docbook_grammar import main
        import io
        from contextlib import redirect_stderr
        d = self._dir()
        self._write(d, "fragment.xml", BROKEN_FRAGMENT)
        shell = self._write(d, "shell.xml", GOOD_SHELL)
        err = io.StringIO()
        with redirect_stderr(err):
            rc = main([str(shell)])
        self.assertEqual(rc, 1)
        self.assertIn("title", err.getvalue())

    def test_a_standalone_fragment_citing_a_sibling_files_bibliography_entry_is_not_a_failure(self):
        # Real, already-committed shape: a fragment's <biblioref> can
        # only resolve once its shell assembles it alongside the
        # bibliography-entry files that define the target xml:id --
        # confirmed live against the real corpus (the shell itself
        # validates clean; only its standalone fragments, checked in
        # isolation, ever see this). A standalone fragment can never
        # satisfy that alone, so this must not fail the run.
        from check_docbook_grammar import main
        d = self._dir()
        path = self._write(d, "cites-out.xml", FRAGMENT_WITH_UNRESOLVABLE_BIBLIOREF)
        self.assertEqual(main([str(path)]), 0)

    def test_a_real_defect_alongside_an_unresolvable_biblioref_still_fails(self):
        # The cross-document-IDREF allowance must not swallow a
        # genuine, independent structural defect (missing <title>)
        # riding along in the same fragment.
        from check_docbook_grammar import main
        import io
        from contextlib import redirect_stderr
        d = self._dir()
        path = self._write(
            d, "cites-out-and-broken.xml",
            FRAGMENT_WITH_UNRESOLVABLE_BIBLIOREF_AND_MISSING_TITLE,
        )
        err = io.StringIO()
        with redirect_stderr(err):
            rc = main([str(path)])
        self.assertEqual(rc, 1)
        self.assertIn("title", err.getvalue())

    def test_returns_zero_and_reports_a_skip_for_an_unvalidatable_root(self):
        from check_docbook_grammar import main
        import io
        from contextlib import redirect_stdout
        d = self._dir()
        path = self._write(d, "b.xml", BIBLIOENTRY_FIXTURE)
        out = io.StringIO()
        with redirect_stdout(out):
            rc = main([str(path)])
        self.assertEqual(rc, 0)
        self.assertIn("SKIP", out.getvalue())

    def test_one_bad_file_among_several_good_ones_still_fails_the_whole_run(self):
        from check_docbook_grammar import main
        d = self._dir()
        # GOOD_SHELL's own literal <xi:include> always says
        # href="fragment.xml" -- the good fixture MUST keep that exact
        # name on disk, or the "good" shell fails too, for an
        # unrelated, accidental reason (a dangling include), which
        # would make this test pass without actually proving anything
        # about aggregation across multiple files.
        self._write(d, "fragment.xml", GOOD_FRAGMENT)
        good_shell = self._write(d, "good-shell.xml", GOOD_SHELL)
        self._write(d, "bad-fragment.xml", BROKEN_FRAGMENT)
        bad_shell = self._write(
            d, "bad-shell.xml", GOOD_SHELL.replace("fragment.xml", "bad-fragment.xml")
        )
        self.assertEqual(main([str(good_shell), str(bad_shell)]), 1)

    def test_processes_every_file_rather_than_stopping_at_the_first_defect(self):
        # Two DISTINCT, independently-identifiable defects (a missing
        # <title> vs. a missing include target) surrounding a good
        # file in between. A short-circuiting main() that returns as
        # soon as it finds the FIRST error would still return 1 here
        # (same as a correct one) -- the only way to prove every file
        # was actually processed is to confirm BOTH distinct defects
        # show up in the output, not just that the overall exit code
        # is nonzero.
        from check_docbook_grammar import main
        import io
        from contextlib import redirect_stderr
        d = self._dir()
        self._write(d, "missing-title-fragment.xml", BROKEN_FRAGMENT)
        first_bad_shell = self._write(
            d, "first-bad-shell.xml",
            GOOD_SHELL.replace("fragment.xml", "missing-title-fragment.xml"),
        )
        self._write(d, "fragment.xml", GOOD_FRAGMENT)
        good_shell = self._write(d, "good-shell.xml", GOOD_SHELL)
        second_bad_shell = self._write(
            d, "second-bad-shell.xml",
            GOOD_SHELL.replace("fragment.xml", "does-not-exist.xml"),
        )
        err = io.StringIO()
        with redirect_stderr(err):
            rc = main([str(first_bad_shell), str(good_shell), str(second_bad_shell)])
        self.assertEqual(rc, 1)
        output = err.getvalue()
        self.assertIn("title", output)
        self.assertIn("does-not-exist.xml", output)


if __name__ == "__main__":
    unittest.main()

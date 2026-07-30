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


class TestValidateGrammar(unittest.TestCase):
    def setUp(self):
        from check_docbook_grammar import fetch_docbook_schema
        self.schema = fetch_docbook_schema()

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


class TestValidateResolvedDocument(_WritesFilesFixture, unittest.TestCase):
    def setUp(self):
        from check_docbook_grammar import fetch_docbook_schema
        self.schema = fetch_docbook_schema()

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


class TestValidateResolvedDocumentAgainstRealCorpusFiles(unittest.TestCase):
    """A small number of real corpus documents, independently confirmed
    clean during design: xmllint --noout --xinclude, raw jing, AND a
    grep for markdown-remnant syntax (**/*|pipe-tables) all confirmed
    clean for every file in this specific paper. NOT the whole corpus
    -- see this plan's Global Constraints and Design Note 3."""

    def setUp(self):
        from check_docbook_grammar import fetch_docbook_schema
        self.schema = fetch_docbook_schema()

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


if __name__ == "__main__":
    unittest.main()

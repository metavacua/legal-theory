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


if __name__ == "__main__":
    unittest.main()

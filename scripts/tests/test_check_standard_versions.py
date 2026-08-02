import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from check_standard_versions import (  # noqa: E402
    find_docbook_version_violations,
    find_xslt_version_violations,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _write(root, rel_path, content):
    path = root / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


class TestFindDocbookVersionViolations(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(dir=REPO_ROOT / "docs" / "wip"))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)

    def test_uniform_5_2_corpus_has_no_violations(self):
        _write(
            self.root,
            "docs/a.xml",
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<article xmlns="http://docbook.org/ns/docbook" version="5.2"/>\n',
        )
        _write(
            self.root,
            "docs/b.xml",
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<article xmlns="http://docbook.org/ns/docbook" version="5.2"/>\n',
        )
        self.assertEqual(find_docbook_version_violations(repo_root=self.root), [])

    def test_xml_declaration_version_is_not_mistaken_for_docbook_version(self):
        """Every file's <?xml version="1.0"?> prolog must never itself be
        counted as a second DocBook version -- only the root element's own
        version= attribute matters."""
        _write(
            self.root,
            "docs/a.xml",
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<article xmlns="http://docbook.org/ns/docbook" version="5.2"/>\n',
        )
        self.assertEqual(find_docbook_version_violations(repo_root=self.root), [])

    def test_single_off_standard_document_is_flagged(self):
        _write(
            self.root,
            "docs/a.xml",
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<article xmlns="http://docbook.org/ns/docbook" version="5.1"/>\n',
        )
        violations = find_docbook_version_violations(repo_root=self.root)
        self.assertEqual(len(violations), 1)
        self.assertIn("5.1", violations[0])

    def test_mixed_versions_across_corpus_flagged_as_multiple(self):
        _write(
            self.root,
            "docs/a.xml",
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<article xmlns="http://docbook.org/ns/docbook" version="5.2"/>\n',
        )
        _write(
            self.root,
            "docs/b.xml",
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<article xmlns="http://docbook.org/ns/docbook" version="4.5"/>\n',
        )
        violations = find_docbook_version_violations(repo_root=self.root)
        joined = " ".join(violations)
        self.assertIn("4.5", joined)
        self.assertIn("Multiple DocBook versions", joined)

    def test_scratch_subtree_is_ignored(self):
        _write(
            self.root,
            "docs/scratch/notes.xml",
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<article xmlns="http://docbook.org/ns/docbook" version="4.5"/>\n',
        )
        self.assertEqual(find_docbook_version_violations(repo_root=self.root), [])


class TestFindXsltVersionViolations(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(dir=REPO_ROOT / "docs" / "wip"))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)

    def test_no_stylesheets_is_not_a_violation(self):
        self.assertEqual(find_xslt_version_violations(repo_root=self.root), [])

    def test_lone_xslt_3_0_stylesheet_passes(self):
        _write(
            self.root,
            "docs/xsl/thing.xsl",
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="3.0"/>\n',
        )
        self.assertEqual(find_xslt_version_violations(repo_root=self.root), [])

    def test_xslt_1_0_stylesheet_is_flagged(self):
        _write(
            self.root,
            "docs/xsl/legacy.xsl",
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0"/>\n',
        )
        violations = find_xslt_version_violations(repo_root=self.root)
        self.assertEqual(len(violations), 1)
        self.assertIn("1.0", violations[0])

    def test_mixed_xslt_versions_flagged_as_multiple(self):
        _write(
            self.root,
            "docs/xsl/legacy.xsl",
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0"/>\n',
        )
        _write(
            self.root,
            "docs/xsl/modern.xsl",
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="3.0"/>\n',
        )
        violations = find_xslt_version_violations(repo_root=self.root)
        joined = " ".join(violations)
        self.assertIn("Multiple XSLT versions", joined)

    def test_vendored_cache_stylesheets_are_ignored(self):
        """The fetched xslTNG distribution lives under .cache/ and is not
        this repo's own tooling -- it must never be scanned."""
        _write(
            self.root,
            ".cache/xsltng/docbook-xslTNG-2.7.1/xslt/docbook.xsl",
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0"/>\n',
        )
        self.assertEqual(find_xslt_version_violations(repo_root=self.root), [])


if __name__ == "__main__":
    unittest.main()

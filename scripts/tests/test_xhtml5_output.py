"""Tests for docs/xsl/xhtml5-corpus.xsl -- the local customization layer
over docbook-xsl-ns's xhtml5 stylesheet that fixes two corpus-wide HTML5
text/html parse errors (a leading XML declaration; xml:lang emitted
without a paired lang, including on the root <html> element, which gets
neither) and one upstream vendor bug (invalid cellspacing/cellpadding CSS
on <blockquote><attribution> tables). See
.superpowers/sdd/2026-07-29-xhtml5-text-html-conformance.md for the full
research record."""

import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from convert_to_docbook import REPO_ROOT  # noqa: E402

try:
    import html5lib
    HTML5LIB_AVAILABLE = True
except ImportError:
    HTML5LIB_AVAILABLE = False

HTML5LIB_SKIP_REASON = (
    "html5lib is not installed under this interpreter -- these tests "
    "only cross-check the structural assertions the other test classes "
    "in this file already make without it."
)

CUSTOM_XSL_PATH = REPO_ROOT / "docs" / "xsl" / "xhtml5-corpus.xsl"
RAW_UPSTREAM_XSL_PATH = Path(
    "/usr/share/xml/docbook/stylesheet/docbook-xsl-ns/xhtml5/docbook.xsl"
)

LANG_FIXTURE = '''<?xml version="1.0" encoding="UTF-8"?>
<article xmlns="http://docbook.org/ns/docbook" version="5.2" xml:id="lang-check" xml:lang="en">
  <info><title>Lang Check</title></info>
  <para>Body text with non-ASCII: café, an em dash—and an arrow →, confirmed UTF-8, not mis-encoded.</para>
</article>
'''

BLOCKQUOTE_FIXTURE = '''<?xml version="1.0" encoding="UTF-8"?>
<article xmlns="http://docbook.org/ns/docbook" version="5.2" xml:id="blockquote-check" xml:lang="en">
  <info><title>Blockquote Check</title></info>
  <blockquote>
    <attribution>Someone</attribution>
    <para>Quoted text.</para>
  </blockquote>
</article>
'''


def _run_xsltproc(xsl_path, xml_path):
    result = subprocess.run(
        ["xsltproc", "--xinclude", "--stringparam", "docbook.css.source", "",
         str(xsl_path), str(xml_path)],
        capture_output=True, text=True, check=True,
    )
    return result.stdout


class TestXhtml5CustomizationLayer(unittest.TestCase):
    def setUp(self):
        self.fixtures = Path(__file__).resolve().parent / "fixtures"

    def _build(self, fixture_text, name, xsl_path=CUSTOM_XSL_PATH):
        xml_path = self.fixtures / name
        xml_path.write_text(fixture_text, encoding="utf-8")
        self.addCleanup(xml_path.unlink)
        return _run_xsltproc(xsl_path, xml_path)

    def test_no_leading_xml_declaration(self):
        html = self._build(LANG_FIXTURE, "no-xml-decl.xml")
        self.assertTrue(
            html.startswith("<!DOCTYPE html>"),
            f"expected output to start with the HTML5 doctype and no XML "
            f"declaration; got: {html[:80]!r}",
        )

    def test_non_ascii_content_survives_as_real_utf8(self):
        # Guards xsl:output's encoding="UTF-8" specifically -- the sibling
        # html/docbook.xsl variant hardcodes ISO-8859-1 instead, and this
        # corpus has real non-ASCII content (see GC-4).
        html = self._build(LANG_FIXTURE, "utf8-check.xml")
        self.assertIn("café", html)
        self.assertIn("—", html)
        self.assertIn("→", html)


@unittest.skipUnless(HTML5LIB_AVAILABLE, HTML5LIB_SKIP_REASON)
class TestHtml5libAgreesNoParseErrors(unittest.TestCase):
    def setUp(self):
        self.fixtures = Path(__file__).resolve().parent / "fixtures"

    def _build(self, fixture_text, name, xsl_path):
        xml_path = self.fixtures / name
        xml_path.write_text(fixture_text, encoding="utf-8")
        self.addCleanup(xml_path.unlink)
        return _run_xsltproc(xsl_path, xml_path)

    def test_customization_layer_output_has_zero_parse_errors(self):
        html = self._build(LANG_FIXTURE, "html5lib-fixed.xml", CUSTOM_XSL_PATH)
        parser = html5lib.HTMLParser(strict=False)
        parser.parse(html.encode("utf-8"))
        self.assertEqual(parser.errors, [])

    def test_raw_upstream_output_does_have_a_parse_error(self):
        # Negative control: proves the assertion above would actually have
        # caught the original bug, not just that this fixture happens to
        # parse cleanly regardless of which stylesheet built it.
        html = self._build(LANG_FIXTURE, "html5lib-raw.xml", RAW_UPSTREAM_XSL_PATH)
        parser = html5lib.HTMLParser(strict=False)
        parser.parse(html.encode("utf-8"))
        self.assertTrue(
            parser.errors,
            "expected the raw upstream stylesheet's leading XML "
            "declaration to trip a parse error",
        )

"""Tests for docs/xsl/xhtml5-corpus.xsl -- the local customization layer
over docbook-xsl-ns's xhtml5 stylesheet that fixes two corpus-wide HTML5
text/html parse errors (a leading XML declaration; xml:lang emitted
without a paired lang, including on the root <html> element, which gets
neither) and one upstream vendor bug (invalid cellspacing/cellpadding CSS
on <blockquote><attribution> tables). See
.superpowers/sdd/2026-07-29-xhtml5-text-html-conformance.md for the full
research record."""

import html.parser
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from convert_to_docbook import REPO_ROOT, build_html  # noqa: E402

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
FIXTURES = Path(__file__).resolve().parent / "fixtures"

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


class _TagAttributeCollector(html.parser.HTMLParser):
    """Collects every start tag's attributes as (tag_name, {attr: value}).
    stdlib only. Used instead of substring/regex checks anywhere a test
    needs to know a specific attribute (e.g. a standalone "lang=") is
    genuinely present as its own attribute -- "'lang=\"en\"' in html_text"
    is a false positive whenever xml:lang="en" is present without a
    paired lang, because that literal substring also occurs inside
    "xml:lang=\"en\"" (confirmed directly: it produced a passing test for
    the wrong reason before this helper replaced the substring check)."""

    def __init__(self):
        super().__init__()
        self.tags = []

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))


def _parse_tags(html_text):
    collector = _TagAttributeCollector()
    collector.feed(html_text)
    return collector.tags


def _committed_corpus_html_paths():
    # git ls-files, not a filesystem walk: this repo's working tree can carry
    # untracked, gitignored stray artifacts (e.g. a prior, non-DocBook build
    # under docs/papers/ai_and_ip/llm-database-theory/generated/) that a raw
    # rglob() would silently include despite this function's name promising
    # "committed" paths -- confirmed live, one such stray .meta.html file has
    # no <html lang> because it was never built by this pipeline at all.
    result = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "ls-files", "docs/**/*.html"],
        capture_output=True, text=True, check=True,
    )
    return sorted(
        REPO_ROOT / rel for rel in result.stdout.splitlines()
        if "/scratch/" not in rel
    )


class _FixtureTestCase(unittest.TestCase):
    """Shared setUp/_build for tests that write a throwaway XML fixture
    into scripts/tests/fixtures/, run it through xsltproc, and clean up
    afterward. Contributes no test methods of its own."""

    def setUp(self):
        self.fixtures = Path(__file__).resolve().parent / "fixtures"

    def _build(self, fixture_text, name, xsl_path=CUSTOM_XSL_PATH):
        xml_path = self.fixtures / name
        xml_path.write_text(fixture_text, encoding="utf-8")
        self.addCleanup(xml_path.unlink)
        return _run_xsltproc(xsl_path, xml_path)


class TestXhtml5CustomizationLayer(_FixtureTestCase):
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

    def test_root_html_element_has_paired_lang_and_xml_lang(self):
        html = self._build(LANG_FIXTURE, "html-lang.xml")
        html_tags = [attrs for tag, attrs in _parse_tags(html) if tag == "html"]
        self.assertTrue(html_tags, f"no <html> tag found in: {html[:200]!r}")
        attrs = html_tags[0]
        self.assertEqual(attrs.get("lang"), "en")
        self.assertEqual(attrs.get("xml:lang"), "en")

    def test_article_section_wrapper_has_paired_lang_and_xml_lang(self):
        html = self._build(LANG_FIXTURE, "section-lang.xml")
        section_tags = [
            attrs for tag, attrs in _parse_tags(html)
            if tag == "section" and attrs.get("class") == "article"
        ]
        self.assertTrue(
            section_tags, f'no <section class="article"> found in: {html[:200]!r}'
        )
        attrs = section_tags[0]
        self.assertEqual(attrs.get("lang"), "en")
        self.assertEqual(attrs.get("xml:lang"), "en")

    def test_blockquote_table_style_drops_invalid_css_properties(self):
        html = self._build(BLOCKQUOTE_FIXTURE, "blockquote-css.xml")
        self.assertNotIn("cellspacing", html)
        self.assertNotIn("cellpadding", html)

    def test_blockquote_content_and_remaining_style_are_preserved(self):
        # Proves the fix is surgical (GC-3): everything else about the
        # blockquote table -- content, attribution, the *valid* CSS
        # declarations -- survives unchanged.
        html = self._build(BLOCKQUOTE_FIXTURE, "blockquote-content.xml")
        self.assertIn("Quoted text.", html)
        self.assertIn('class="attribution"', html)
        self.assertIn(">Someone<", html)
        self.assertIn('style="border: 0; width: 100%;"', html)


@unittest.skipUnless(HTML5LIB_AVAILABLE, HTML5LIB_SKIP_REASON)
class TestHtml5libAgreesNoParseErrors(_FixtureTestCase):
    def test_customization_layer_output_has_zero_parse_errors(self):
        html = self._build(LANG_FIXTURE, "html5lib-fixed.xml", CUSTOM_XSL_PATH)
        parser = html5lib.HTMLParser(strict=False)
        parser.parse(html.encode("utf-8"))
        self.assertEqual(parser.errors, [])


class TestBuildHtmlWiring(_FixtureTestCase):
    def test_build_html_output_has_no_xml_declaration(self):
        from convert_to_docbook import build_html
        xml_path = self.fixtures / "build-html-wiring.xml"
        html_path = self.fixtures / "build-html-wiring.html"
        xml_path.write_text(LANG_FIXTURE, encoding="utf-8")
        self.addCleanup(xml_path.unlink)
        build_html(xml_path, html_path)
        self.addCleanup(html_path.unlink)
        content = html_path.read_text(encoding="utf-8")
        self.assertTrue(content.startswith("<!DOCTYPE html>"))


class TestBuildHtmlUsesXsltng(unittest.TestCase):
    def test_build_html_uses_xsltng(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out.html"
            build_html(FIXTURES / "minimal_valid.xml", out)
            text = out.read_text(encoding="utf-8")
            self.assertIn("DocBook xslTNG", text, "generator meta tag confirms the real pipeline ran")
            self.assertNotIn("<?xml", text[:20], "no XML declaration in HTML5 text/html output")


class TestCommittedCorpusHtmlIsClean(unittest.TestCase):
    """Corpus-wide regression guard: every committed page, not just the
    fixtures above, actually got rebuilt through the fixed pipeline."""

    @classmethod
    def setUpClass(cls):
        # Read each of the ~128 pages once, shared read-only across the
        # three checks below, rather than each independently re-walking
        # docs/ and re-reading every file from disk.
        cls.pages = [
            (p, p.read_text(encoding="utf-8"))
            for p in _committed_corpus_html_paths()
        ]

    def test_no_committed_page_has_a_leading_xml_declaration(self):
        offenders = [
            str(p.relative_to(REPO_ROOT)) for p, text in self.pages
            if text.lstrip().startswith("<?xml")
        ]
        self.assertEqual(offenders, [])

    def test_no_committed_page_has_invalid_cellspacing_or_cellpadding_css(self):
        offenders = [
            str(p.relative_to(REPO_ROOT)) for p, text in self.pages
            if "cellspacing" in text or "cellpadding" in text
        ]
        self.assertEqual(offenders, [])

    def test_every_committed_page_pairs_lang_and_xml_lang_and_html_has_lang(self):
        offenders = []
        for p, text in self.pages:
            rel = str(p.relative_to(REPO_ROOT))
            tags = _parse_tags(text)
            html_tags = [attrs for tag, attrs in tags if tag == "html"]
            if not html_tags or "lang" not in html_tags[0]:
                offenders.append(f"{rel}: <html> missing lang")
            for tag, attrs in tags:
                if "xml:lang" in attrs and attrs.get("lang") != attrs["xml:lang"]:
                    offenders.append(f"{rel}: <{tag}> unpaired lang/xml:lang: {attrs}")
        self.assertEqual(offenders, [])

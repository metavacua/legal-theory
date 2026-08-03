package io.github.metavacua.pipeline;

import net.sf.saxon.s9api.QName;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import org.w3c.dom.Document;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;
import static org.junit.jupiter.api.Assertions.*;

class XhtmlToDocbookTest {
    static net.sf.saxon.s9api.XsltExecutable XSL;
    static Path manifest;

    @BeforeAll static void setup() throws Exception {
        XSL = XsltPipeline.compile(Path.of("src/main/resources/xslt/xhtml-to-docbook.xsl"));
        manifest = Files.createTempFile("manifest", ".xml");
        Files.writeString(manifest, """
            <manifest>
              <doc path="fx.md" pubdate="2026-07-01" biblioid="%sfx.md"/>
            </manifest>""".formatted(Constants.CANONICAL_BASE));
    }
    static Document convert(String mdFixture, String title) throws Exception {
        var x = MarkdownToXhtml.convert(Files.readString(Path.of("src/test/resources/fixtures/md/" + mdFixture)));
        return XsltPipeline.apply(XSL, x.dom(), Map.of(
            new QName("authored-title"), title,
            new QName("source-path"), "fx.md",
            new QName("manifest-uri"), manifest.toUri().toString()));
    }
    static String ser(Document d) { return Xml.serialize(d); }

    @Test void infoFieldsComeFromParamsAndManifest() throws Exception {
        String s = ser(convert("frontmatter.md", "An Authored Title"));
        assertTrue(s.contains("<title>An Authored Title</title>"));
        assertTrue(s.contains("<pubdate role=\"generated-from-git-first-commit\">2026-07-01</pubdate>"));
        assertTrue(s.contains("biblioid"));
        assertTrue(s.contains(">Text</dc:type>") || s.contains("dc:type>Text"));
    }
    @Test void headingsNestAsSections() throws Exception {
        String s = ser(convert("frontmatter.md", "T"));
        assertTrue(s.contains("<section>") && s.contains("<title>Heading One</title>"));
    }
    @Test void levelSkipClosesGapWithoutPhantomSections() throws Exception {
        Document d = convert("levelskip.md", "T");
        // h1 -> section; h3 nests DIRECTLY under it (gap closed, no empty intermediate)
        var xp = javax.xml.xpath.XPathFactory.newInstance().newXPath();
        var n = (org.w3c.dom.NodeList) xp.evaluate(
            "//*[local-name()='section']/*[local-name()='section']", d,
            javax.xml.xpath.XPathConstants.NODESET);
        assertEquals(1, n.getLength());
    }
    @Test void tightListItemsGainParaWrapper() throws Exception {
        var x = MarkdownToXhtml.convert("- alpha\n- beta\n");
        String s = ser(XsltPipeline.apply(XSL, x.dom(), Map.of(
            new QName("authored-title"), "T",
            new QName("source-path"), "fx.md",
            new QName("manifest-uri"), manifest.toUri().toString())));
        assertTrue(s.contains("<listitem><para>alpha</para></listitem>")
                || s.contains("<listitem>\n<para>alpha</para>"));
    }
    @Test void gfmTableMapsToInformaltable() throws Exception {
        String s = ser(convert("table.md", "T"));
        assertTrue(s.contains("<informaltable") && s.contains("<td>1</td>"));
    }
    @Test void unmappedElementTerminatesLoudly() throws Exception {
        // strikethrough extension NOT enabled in prod; simulate an unmapped element directly
        var dom = Xml.hardenedBuilder().parse(new java.io.ByteArrayInputStream(
            "<html xmlns=\"http://www.w3.org/1999/xhtml\"><head><title/></head><body><kbd>x</kbd></body></html>"
            .getBytes()));
        var e = assertThrows(RuntimeException.class, () -> XsltPipeline.apply(XSL, dom, Map.of(
            new QName("authored-title"), "T",
            new QName("source-path"), "fx.md",
            new QName("manifest-uri"), manifest.toUri().toString())));
        assertTrue(e.getMessage().contains("Unmapped"));
    }
    @Test void outputValidatesAgainstRealDocbookGrammar() throws Exception {
        Document d = convert("plain.md", "A Title");
        Path tmp = Files.createTempFile("out", ".xml");
        Files.writeString(tmp, Xml.serialize(d));
        assertEquals(List.of(), JingGate.validate(JingGate.DOCBOOK_RNC, tmp));
    }
}

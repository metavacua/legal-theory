package io.github.metavacua.pipeline;

import net.sf.saxon.s9api.QName;
import org.junit.jupiter.api.Test;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Map;
import static org.junit.jupiter.api.Assertions.*;

class AuditChecksTest {
    @Test void titleClasses() throws Exception {
        assertEquals("front-matter", AuditChecks.titleClass(
            MarkdownToXhtml.convert("---\ntitle: T\n---\n# H\n")));
        assertEquals("h1-first", AuditChecks.titleClass(MarkdownToXhtml.convert("# H\n")));
        assertEquals("h3-first", AuditChecks.titleClass(MarkdownToXhtml.convert("### H\n")));
        assertEquals("headingless", AuditChecks.titleClass(MarkdownToXhtml.convert("just prose\n")));
    }
    @Test void biblioRegionDiscernedByExactContainerTitleOnly() throws Exception {
        var x = MarkdownToXhtml.convert(Files.readString(
            Path.of("src/test/resources/fixtures/md/workscited.md")));
        var manifest = Files.createTempFile("m", ".xml");
        Files.writeString(manifest, "<manifest><doc path=\"fx.md\" pubdate=\"2026-07-01\" biblioid=\""
            + Constants.CANONICAL_BASE + "fx.md\"/></manifest>");
        var xsl = XsltPipeline.compile(Path.of("src/main/resources/xslt/xhtml-to-docbook.xsl"));
        var db = XsltPipeline.apply(xsl, x.dom(), Map.of(
            new QName("authored-title"), x.frontMatterTitle(),
            new QName("source-path"), "fx.md",
            new QName("manifest-uri"), manifest.toUri().toString()));
        assertEquals(2, AuditChecks.biblioRegion(db).orElseThrow());
        assertArrayEquals(new int[]{1, 1}, AuditChecks.linkStats(db));
        // near-miss control: a section titled "Reference Guide: X" must NOT count
        var x2 = MarkdownToXhtml.convert("# Reference Guide: Contracts\n\n1. item\n");
        var db2 = XsltPipeline.apply(xsl, x2.dom(), Map.of(
            new QName("authored-title"), "T",
            new QName("source-path"), "fx.md",
            new QName("manifest-uri"), manifest.toUri().toString()));
        assertTrue(AuditChecks.biblioRegion(db2).isEmpty());
    }
    @Test void c1Detection() {
        assertEquals(1, AuditChecks.c1Count("badchar"));
        assertEquals(0, AuditChecks.c1Count("clean"));
    }
}

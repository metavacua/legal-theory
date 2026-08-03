package io.github.metavacua.pipeline;

import org.junit.jupiter.api.Disabled;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class CensusEngineTest {
    @Test void censusDiscernsPseudoBibliographies() throws Exception {
        // fixture from Task 10 Step 1 has a Works cited region with 2 items
        var x = MarkdownToXhtml.convert(java.nio.file.Files.readString(
            java.nio.file.Path.of("src/test/resources/fixtures/md/workscited.md")));
        assertEquals("front-matter", AuditChecks.titleClass(x));
        // full-engine behavior is exercised by the corpus run in Task 11;
        // this test pins the discernment inputs the census row is built from.
    }
    @Disabled("GREEN target: bibliography promotion — next increment")
    @Test void worksCitedSectionsPromoteToProperBibliography() throws Exception {
        // GREEN shape this pipeline does NOT yet produce (and must not fake):
        // the discerned section becomes <bibliography> with <biblioentry> children
        // constructed only from typed structure. This test defines done-ness for
        // the promotion increment; it stays visible as SKIPPED in every report.
        var xsl = XsltPipeline.compile(java.nio.file.Path.of("src/main/resources/xslt/xhtml-to-docbook.xsl"));
        var x = MarkdownToXhtml.convert(java.nio.file.Files.readString(
            java.nio.file.Path.of("src/test/resources/fixtures/md/workscited.md")));
        var db = XsltPipeline.apply(xsl, x.dom(), java.util.Map.of(
            new net.sf.saxon.s9api.QName("authored-title"), "T",
            new net.sf.saxon.s9api.QName("source-path"), "fx.md",
            new net.sf.saxon.s9api.QName("manifest-uri"), "about:invalid"));
        assertTrue(Xml.serialize(db).contains("<bibliography"));
    }
    @Test void attributeSafetyPreconditionRejectsAmpersandRejectsCleanAccepts() {
        var ex = assertThrows(IllegalStateException.class,
            () -> CensusEngine.assertAttributeSafePath("docs/bad&name.md"));
        assertTrue(ex.getMessage().contains("unsafe"), ex.getMessage());
        assertDoesNotThrow(() -> CensusEngine.assertAttributeSafePath("docs/clean-name.md"));
    }
}

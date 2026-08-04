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
    @Test void healthPageFlowProducesValidMergedModel() throws Exception {
        // tiny synthetic census
        java.nio.file.Path census = java.nio.file.Files.createTempFile("census", ".xml");
        java.nio.file.Files.writeString(census, """
            <census generated="2026-08-03T00:00:00Z" total="2" published="1">
              <doc path="docs/a.md" published="true" titleClass="front-matter">
                <gate id="wf-fragment" status="pass"/>
              </doc>
              <doc path="docs/b.md" published="false" titleClass="h1-first">
                <gate id="policy" status="fail"><message>info/title must be non-empty &amp; authored</message></gate>
                <check id="biblio-region" present="true" count="66"/>
              </doc>
            </census>""");
        var toDb = XsltPipeline.compile(java.nio.file.Path.of("src/main/resources/xslt/census-to-docbook.xsl"));
        org.w3c.dom.Document censusDoc = Xml.hardenedBuilder().parse(census.toFile());
        org.w3c.dom.Document frag = XsltPipeline.apply(toDb, censusDoc, java.util.Map.of()); // was the crash site
        java.nio.file.Path fragPath = java.nio.file.Files.createTempFile("census-fragment", ".xml");
        java.nio.file.Files.writeString(fragPath, Xml.serialize(frag));
        var inject = XsltPipeline.compile(java.nio.file.Path.of("src/main/resources/xslt/inject-census.xsl"));
        org.w3c.dom.Document index = Xml.hardenedBuilder().parse(new java.io.File("src/main/docbook/index.xml"));
        org.w3c.dom.Document merged = XsltPipeline.apply(inject, index, java.util.Map.of(
            new net.sf.saxon.s9api.QName("census-fragment-uri"), fragPath.toUri().toString()));
        String s = Xml.serialize(merged);
        assertTrue(s.contains("<informaltable"), "census table must be injected");
        assertFalse(s.contains("census-fragment"), "carrier wrapper must never leak into the merged doc");
        assertTrue(s.contains("docs/b.md"));
        java.nio.file.Path mergedPath = java.nio.file.Files.createTempFile("merged", ".xml");
        java.nio.file.Files.writeString(mergedPath, s);
        assertEquals(java.util.List.of(), JingGate.validate(JingGate.DOCBOOK_RNC, mergedPath),
            "merged model must remain valid DocBook 5.2");
    }
}

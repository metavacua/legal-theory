package io.github.metavacua.pipeline;

import net.sf.saxon.s9api.QName;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import org.w3c.dom.Document;
import java.io.File;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;
import static io.github.metavacua.pipeline.ContentComparator.Vocabulary.*;
import static org.junit.jupiter.api.Assertions.*;

class TriangleBaseCaseTest {
    static Document mdXhtml, mdDocbook, authoredDocbook, renderOfAuthored, renderOfGenerated;

    @BeforeAll static void pipeline() throws Exception {
        var x = MarkdownToXhtml.convert(Files.readString(Path.of("src/main/docbook/index.md")));
        mdXhtml = x.dom();                                                    // P3
        var manifest = Files.createTempFile("m", ".xml");
        var entries = ManifestGenerator.generate(Constants.REPO_ROOT,
            List.of(Path.of("src/main/docbook/index.md")));
        ManifestGenerator.writeManifest(entries, manifest);
        var xsl = XsltPipeline.compile(Path.of("src/main/resources/xslt/xhtml-to-docbook.xsl"));
        mdDocbook = XsltPipeline.apply(xsl, mdXhtml, Map.of(                  // P1
            new QName("authored-title"), x.frontMatterTitle(),
            new QName("source-path"), "src/main/docbook/index.md",
            new QName("manifest-uri"), manifest.toUri().toString()));
        authoredDocbook = Xml.hardenedBuilder().parse(new File("src/main/docbook/index.xml"));
        Path g = Path.of("target/test-triangle/generated.xml");
        Files.createDirectories(g.getParent());
        Files.writeString(g, Xml.serialize(mdDocbook));
        Path r1 = Path.of("target/test-triangle/authored.xhtml");
        Path r2 = Path.of("target/test-triangle/generated.xhtml");
        DocbookRenderer.render(Path.of("src/main/docbook/index.xml"), r1);    // P2(authored)
        DocbookRenderer.render(g, r2);                                        // P2(P1)
        renderOfAuthored = Xml.outputBuilder().parse(r1.toFile());
        renderOfGenerated = Xml.outputBuilder().parse(r2.toFile());
    }

    @Test void edge1_authoredTwinsAgree() { // P1(index.md) vs index.xml — required agreement
        assertEquals(List.of(), ContentComparator.diff(
            ContentComparator.extract(mdDocbook, DOCBOOK),
            ContentComparator.extract(authoredDocbook, DOCBOOK)));
    }
    @Test void edge2_standardTriangle() {   // P3 vs P2(P1)
        assertEquals(List.of(), ContentComparator.diff(
            ContentComparator.extract(mdXhtml, XHTML),
            ContentComparator.extract(renderOfGenerated, XHTML)));
    }
    @Test void edge3_renderPathsAgree() {   // P2(authored) vs P2(P1)
        assertEquals(List.of(), ContentComparator.diff(
            ContentComparator.extract(renderOfAuthored, XHTML),
            ContentComparator.extract(renderOfGenerated, XHTML)));
    }
}

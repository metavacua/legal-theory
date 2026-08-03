package io.github.metavacua.pipeline;

import org.junit.jupiter.api.Test;
import javax.xml.parsers.DocumentBuilderFactory;
import java.nio.file.Path;
import java.util.List;
import static org.junit.jupiter.api.Assertions.*;

class RenderAndGatesTest {

    /**
     * "Stage 6: native parse" for THIS test's two inputs (xslTNG's own rendered
     * output, and a checked-in, trusted test fixture) -- deliberately NOT
     * Xml.hardenedBuilder(). Live-verified (Task 7): Xml.hardenedBuilder()'s
     * disallow-doctype-decl=true rejects ANY DOCTYPE unconditionally, and
     * xslTNG's <xsl:output method="xhtml" html-version="5"/> unconditionally
     * emits the spec-legitimate, harmless "<!DOCTYPE html>" preamble (confirmed
     * by actually rendering fixtures/docbook/minimal-valid.xml and inspecting
     * the output) -- the same preamble minimal-valid.xhtml (and therefore its
     * mojibake derivative, per the brief's verbatim fixture-generation snippet)
     * already carries. Run through Xml.hardenedBuilder(), both inputs would
     * fail here for a reason that has nothing to do with the C1-mojibake
     * defect class this suite exists to prove (contradicting the brief's own
     * "fail ONLY at vnu" fixture requirement) -- this would in fact block
     * EVERY future task in the plan that native-parses real render output.
     * This local parse proves the same thing stage 6 is meant to prove --
     * well-formed XML -- while still refusing external DTD fetches, entity
     * expansion, and XInclude, for inputs that are not attacker-controlled
     * (our own render output; a checked-in fixture). See task-7-report.md.
     */
    private static void nativeParse(Path p) throws Exception {
        var f = DocumentBuilderFactory.newInstance();
        f.setNamespaceAware(true);
        f.setFeature("http://apache.org/xml/features/nonvalidating/load-external-dtd", false);
        f.setXIncludeAware(false);
        f.setExpandEntityReferences(false);
        f.newDocumentBuilder().parse(p.toFile());
    }

    @Test void rendersDocbookToParsableValidXhtml() throws Exception {
        Path out = Path.of("target/test-render/minimal.xhtml");
        DocbookRenderer.render(Path.of("src/test/resources/fixtures/docbook/minimal-valid.xml"), out);
        // stage 6: native parse
        nativeParse(out);
        // stage 7: pinned grammar
        assertEquals(List.of(), JingGate.validate(JingGate.XHTML5_RNC, out));
    }
    @Test void mojibakePassesGrammarsButFailsVnu() throws Exception {
        Path fx = Path.of("src/test/resources/fixtures/xhtml/mojibake.xhtml");
        nativeParse(fx);                                                     // stage 6 passes
        assertEquals(List.of(), JingGate.validate(JingGate.XHTML5_RNC, fx)); // stage 7 passes
        assertFalse(VnuGate.check(fx).isEmpty(), "only the sequenced vnu gate catches C1 controls");
    }
    @Test void cleanXhtmlPassesVnu() throws Exception {
        assertEquals(List.of(), VnuGate.check(Path.of("src/test/resources/fixtures/xhtml/minimal-valid.xhtml")));
    }
}

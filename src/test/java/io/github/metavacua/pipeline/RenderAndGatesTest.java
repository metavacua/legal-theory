package io.github.metavacua.pipeline;

import org.junit.jupiter.api.Test;
import java.nio.file.Path;
import java.util.List;
import static org.junit.jupiter.api.Assertions.*;

class RenderAndGatesTest {

    @Test void rendersDocbookToParsableValidXhtml() throws Exception {
        Path out = Path.of("target/test-render/minimal.xhtml");
        DocbookRenderer.render(Path.of("src/test/resources/fixtures/docbook/minimal-valid.xml"), out);
        // stage 6: native parse (Xml.outputBuilder() -- tolerates our own renderer's <!DOCTYPE html>)
        Xml.outputBuilder().parse(out.toFile());
        // stage 7: pinned grammar
        assertEquals(List.of(), JingGate.validate(JingGate.XHTML5_RNC, out));
    }
    @Test void mojibakePassesGrammarsButFailsVnu() throws Exception {
        Path fx = Path.of("src/test/resources/fixtures/xhtml/mojibake.xhtml");
        Xml.outputBuilder().parse(fx.toFile());                              // stage 6 passes
        assertEquals(List.of(), JingGate.validate(JingGate.XHTML5_RNC, fx)); // stage 7 passes
        assertFalse(VnuGate.check(fx).isEmpty(), "only the sequenced vnu gate catches C1 controls");
    }
    @Test void cleanXhtmlPassesVnu() throws Exception {
        assertEquals(List.of(), VnuGate.check(Path.of("src/test/resources/fixtures/xhtml/minimal-valid.xhtml")));
    }
    @Test void vnuGateThrowsOnMissingInputFile() {
        var ex = assertThrows(IllegalStateException.class,
            () -> VnuGate.check(Path.of("target/no-such-file.xhtml")));
        assertTrue(ex.getMessage().contains("does not exist"), ex.getMessage());
    }
}

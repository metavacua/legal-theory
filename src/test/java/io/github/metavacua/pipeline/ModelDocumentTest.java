package io.github.metavacua.pipeline;

import org.junit.jupiter.api.Test;
import java.nio.file.Path;
import java.util.List;
import static org.junit.jupiter.api.Assertions.*;

class ModelDocumentTest {
    @Test void modelIndexPassesEveryGate() throws Exception {
        Path src = Path.of("src/main/docbook/index.xml");
        var dom = Xml.hardenedBuilder().parse(src.toFile());                 // stage 1/6 analogue
        assertEquals(List.of(), JingGate.validate(JingGate.DOCBOOK_RNC, src)); // stage 3
        assertEquals(List.of(), SchematronGate.check(dom));                  // stage 4
        Path out = Path.of("target/test-render/index.xhtml");
        DocbookRenderer.render(src, out);                                    // stage 5
        Xml.outputBuilder().parse(out.toFile());                            // stage 6 (tolerates our <!DOCTYPE html>)
        assertEquals(List.of(), JingGate.validate(JingGate.XHTML5_RNC, out)); // stage 7
        assertEquals(List.of(), VnuGate.check(out));                         // stage 8
    }
}

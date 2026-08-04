package io.github.metavacua.pipeline;

import org.junit.jupiter.api.Test;
import java.nio.file.Path;
import java.util.List;
import static org.junit.jupiter.api.Assertions.*;

class JingGateTest {
    static final Path FX = Path.of("src/test/resources/fixtures");

    @Test void validDocbookPasses() {
        assertEquals(List.of(), JingGate.validate(JingGate.DOCBOOK_RNC, FX.resolve("docbook/minimal-valid.xml")));
    }
    @Test void invalidDocbookFails() {
        assertFalse(JingGate.validate(JingGate.DOCBOOK_RNC, FX.resolve("docbook/invalid-element.xml")).isEmpty());
    }
    @Test void validXhtmlPasses() {
        // Proves the whattf datatype wiring: compiling xhtml5.rnc requires the
        // datatype library from nu.validator:validator on the classpath.
        assertEquals(List.of(), JingGate.validate(JingGate.XHTML5_RNC, FX.resolve("xhtml/minimal-valid.xhtml")));
    }
    @Test void invalidXhtmlFails() {
        assertFalse(JingGate.validate(JingGate.XHTML5_RNC, FX.resolve("xhtml/invalid-element.xhtml")).isEmpty());
    }
}

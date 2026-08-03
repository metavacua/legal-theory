package io.github.metavacua.pipeline;

import org.junit.jupiter.api.Test;
import org.w3c.dom.Document;
import java.io.ByteArrayInputStream;
import static org.junit.jupiter.api.Assertions.*;

class SchematronGateTest {
    static Document doc(String title, String pubdate, String biblioid) throws Exception {
        String xml = """
            <article xmlns="http://docbook.org/ns/docbook" xmlns:dc="http://purl.org/dc/terms/" version="5.2">
              <info><title>%s</title>
                <pubdate role="generated-from-git-first-commit">%s</pubdate>
                <biblioid class="uri" role="generated-from-path">%s</biblioid>
                <dc:type>Text</dc:type></info>
              <para>x</para></article>""".formatted(title, pubdate, biblioid);
        return Xml.hardenedBuilder().parse(new ByteArrayInputStream(xml.getBytes()));
    }
    @Test void compliantDocPasses() throws Exception {
        assertEquals(0, SchematronGate.check(
            doc("Real Title", "2026-07-01", Constants.CANONICAL_BASE + "x.md")).size());
    }
    @Test void emptyTitleFails() throws Exception {
        var f = SchematronGate.check(doc("", "2026-07-01", Constants.CANONICAL_BASE + "x.md"));
        assertTrue(f.stream().anyMatch(m -> m.contains("non-empty")));
    }
    @Test void malformedDateFails() throws Exception {
        assertFalse(SchematronGate.check(doc("T", "July 2026", Constants.CANONICAL_BASE + "x.md")).isEmpty());
    }
    @Test void foreignBiblioidFails() throws Exception {
        assertFalse(SchematronGate.check(doc("T", "2026-07-01", "https://elsewhere.example/x")).isEmpty());
    }
}

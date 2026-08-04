package io.github.metavacua.pipeline;

import org.junit.jupiter.api.Test;
import java.nio.file.Files;
import java.nio.file.Path;
import static org.junit.jupiter.api.Assertions.*;

class MarkdownToXhtmlTest {
    static String fx(String n) throws Exception {
        return Files.readString(Path.of("src/test/resources/fixtures/md/" + n));
    }
    @Test void plainMarkdownIsWellFormedXml() throws Exception {
        var r = MarkdownToXhtml.convert(fx("plain.md"));
        assertNotNull(r.dom()); // parse succeeded => well-formed
        assertEquals("", r.frontMatterTitle());
        assertTrue(r.serialized().contains("&amp;"), "text ampersand must be XML-escaped");
        assertTrue(r.serialized().contains("https://example.com/a"));
    }
    @Test void frontMatterTitleExtractedAndNotRenderedIntoBody() throws Exception {
        var r = MarkdownToXhtml.convert(fx("frontmatter.md"));
        assertEquals("An Authored Title", r.frontMatterTitle());
        assertFalse(r.serialized().contains("An Authored Title</h"), "front matter must not leak into body");
        assertTrue(r.serialized().contains("<title>An Authored Title</title>"));
    }
    @Test void rawHtmlIsEscapedNotPassedThrough() throws Exception {
        var r = MarkdownToXhtml.convert(fx("rawhtml.md"));
        assertFalse(r.serialized().contains("<blink>"));
        assertTrue(r.serialized().contains("&lt;blink&gt;"));
    }
    @Test void headinglessStillConverts() throws Exception {
        var r = MarkdownToXhtml.convert(fx("headingless.md"));
        assertEquals("", r.frontMatterTitle()); // absence is the census/gate layer's concern, not this unit's
        assertNotNull(r.dom());
    }
}

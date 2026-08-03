package io.github.metavacua.pipeline;

import org.commonmark.Extension;
import org.commonmark.ext.front.matter.YamlFrontMatterExtension;
import org.commonmark.ext.front.matter.YamlFrontMatterVisitor;
import org.commonmark.ext.gfm.tables.TablesExtension;
import org.commonmark.parser.Parser;
import org.commonmark.renderer.html.HtmlRenderer;
import org.w3c.dom.Document;

import java.io.ByteArrayInputStream;
import java.nio.charset.StandardCharsets;
import java.util.List;

public final class MarkdownToXhtml {
    public record XhtmlResult(Document dom, String serialized, String frontMatterTitle) {}

    private static final List<Extension> EXT =
        List.of(YamlFrontMatterExtension.create(), TablesExtension.create());
    private static final Parser PARSER = Parser.builder().extensions(EXT).build();
    private static final HtmlRenderer RENDERER =
        HtmlRenderer.builder().extensions(EXT).escapeHtml(true).build();

    public static XhtmlResult convert(String markdown) {
        var node = PARSER.parse(markdown);
        var fm = new YamlFrontMatterVisitor();
        node.accept(fm);
        String title = fm.getData().getOrDefault("title", List.of()).stream().findFirst().orElse("");
        String body = RENDERER.render(node);
        String doc = "<html xmlns=\"http://www.w3.org/1999/xhtml\"><head><title>"
            + escape(title) + "</title></head><body>" + body + "</body></html>";
        try {
            Document dom = Xml.hardenedBuilder()
                .parse(new ByteArrayInputStream(doc.getBytes(StandardCharsets.UTF_8)));
            return new XhtmlResult(dom, doc, title);
        } catch (Exception e) {
            // Malformed output is a build failure, never silently corrected.
            throw new IllegalStateException("commonmark output is not well-formed XML: " + e.getMessage(), e);
        }
    }
    private static String escape(String s) {
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;");
    }
    private MarkdownToXhtml() {}
}

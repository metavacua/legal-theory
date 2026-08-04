package io.github.metavacua.pipeline;

import net.sf.saxon.s9api.*;
import org.w3c.dom.Document;
import javax.xml.transform.dom.DOMSource;
import java.io.StringWriter;
import java.nio.file.Path;
import java.util.*;

public final class ContentComparator {
    public enum Vocabulary { XHTML, DOCBOOK }
    public record Extraction(List<String> textLines, Set<String> links) {}

    private static volatile XsltExecutable cached;

    public static Extraction extract(Document doc, Vocabulary v) {
        try {
            if (cached == null)
                cached = XsltPipeline.compile(Path.of("src/main/resources/xslt/extract-content.xsl"));
            var t = cached.load30();
            t.setStylesheetParameters(Map.of(new QName("mode"),
                new XdmAtomicValue(v == Vocabulary.XHTML ? "xhtml" : "docbook")));
            var sw = new StringWriter();
            var ser = XsltPipeline.SAXON.newSerializer(sw);
            var node = XsltPipeline.SAXON.newDocumentBuilder().build(new DOMSource(doc));
            // applyTemplates(XdmValue, Destination) sets only the initial match
            // selection, NOT the s9api "global context item" -- global variables
            // in extract-content.xsl (xhtml-scope's `//h:main`) are evaluated
            // against the global context item, so it must be set explicitly or
            // those `//` path expressions fail with "context item is absent".
            t.setGlobalContextItem(node);
            t.applyTemplates(node, ser);
            String[] parts = sw.toString().split("===LINKS===\n", 2);
            List<String> lines = parts[0].lines().filter(s -> !s.isBlank()).toList();
            Set<String> links = parts.length > 1
                ? new TreeSet<>(parts[1].lines().filter(s -> !s.isBlank()).toList())
                : Set.of();
            return new Extraction(lines, links);
        } catch (Exception e) { throw new IllegalStateException(e); }
    }

    public static List<String> diff(Extraction a, Extraction b) {
        var out = new ArrayList<String>();
        if (!String.join("\n", a.textLines()).equals(String.join("\n", b.textLines())))
            out.add("text-sequence divergence: " + firstDivergence(a.textLines(), b.textLines()));
        if (!a.links().equals(b.links())) {
            var onlyA = new TreeSet<>(a.links()); onlyA.removeAll(b.links());
            var onlyB = new TreeSet<>(b.links()); onlyB.removeAll(a.links());
            out.add("link-set divergence: onlyA=" + onlyA + " onlyB=" + onlyB);
        }
        return out;
    }
    private static String firstDivergence(List<String> a, List<String> b) {
        for (int i = 0; i < Math.min(a.size(), b.size()); i++)
            if (!a.get(i).equals(b.get(i))) return "line " + i + ": '" + a.get(i) + "' vs '" + b.get(i) + "'";
        return "length " + a.size() + " vs " + b.size();
    }
    private ContentComparator() {}
}

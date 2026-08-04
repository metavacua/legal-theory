package io.github.metavacua.pipeline;

import net.sf.saxon.s9api.*;
import org.w3c.dom.Document;
import javax.xml.transform.dom.DOMSource;
import java.util.List;
import java.util.Optional;

public final class AuditChecks {
    private static final List<String> BIBLIO_LABELS = List.of("works cited"); // configurable, exact-match set

    public static String titleClass(MarkdownToXhtml.XhtmlResult x) {
        if (!x.frontMatterTitle().isBlank()) return "front-matter";
        String lvl = evalOne(x.dom(),
            "(//*:body//*[matches(local-name(), '^h[1-6]$')])[1]/local-name()");
        return lvl.isEmpty() ? "headingless" : lvl + "-first";
    }
    public static Optional<Integer> biblioRegion(Document docbook) {
        String labels = "('" + String.join("','", BIBLIO_LABELS) + "')";
        String c = evalOne(docbook,
            "string((//*:section[normalize-space(lower-case(*:title)) = " + labels + "])[1]"
            + "/count(.//*:listitem))");
        return (c.isEmpty() || c.equals("0")) ? Optional.empty() : Optional.of(Integer.parseInt(c));
    }
    public static int[] linkStats(Document docbook) {
        String labels = "('" + String.join("','", BIBLIO_LABELS) + "')";
        String base = "(//*:section[normalize-space(lower-case(*:title)) = " + labels + "])[1]//*:listitem";
        int with = Integer.parseInt(evalOne(docbook, "string(count(" + base + "[.//*:link]))"));
        int total = Integer.parseInt(evalOne(docbook, "string(count(" + base + "))"));
        return new int[]{with, total - with};
    }
    public static int c1Count(String text) {
        return (int) text.chars().filter(c -> c >= 0x80 && c <= 0x9F).count();
    }
    static String evalOne(Document doc, String xpath) {
        try {
            var xp = XsltPipeline.SAXON.newXPathCompiler();
            var sel = xp.compile(xpath).load();
            sel.setContextItem(XsltPipeline.SAXON.newDocumentBuilder().build(new DOMSource(doc)));
            XdmValue v = sel.evaluate();
            return v.size() == 0 ? "" : v.itemAt(0).getStringValue();
        } catch (Exception e) { throw new IllegalStateException(e); }
    }
    private AuditChecks() {}
}

package io.github.metavacua.pipeline;

import net.sf.saxon.s9api.XsltExecutable;
import org.w3c.dom.Document;
import org.w3c.dom.NodeList;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

public final class SchematronGate {
    public static final Path COMPILED = Path.of("target/generated-resources/policy.xsl");
    private static volatile XsltExecutable cached;

    public static List<String> check(Document docbook) {
        try {
            if (cached == null) cached = XsltPipeline.compile(COMPILED);
            Document svrl = XsltPipeline.apply(cached, docbook, Map.of());
            NodeList fails = svrl.getElementsByTagNameNS(
                "http://purl.oclc.org/dsdl/svrl", "failed-assert");
            var out = new ArrayList<String>();
            for (int i = 0; i < fails.getLength(); i++)
                out.add(fails.item(i).getTextContent().trim());
            return out;
        } catch (Exception e) { throw new IllegalStateException(e); }
    }
    private SchematronGate() {}
}

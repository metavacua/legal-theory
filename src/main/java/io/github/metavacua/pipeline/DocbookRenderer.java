package io.github.metavacua.pipeline;

import net.sf.saxon.s9api.XsltExecutable;
import java.nio.file.*;
import java.util.stream.Stream;

public final class DocbookRenderer {
    private static final Path XSLTNG = Path.of("target/xsltng/org/docbook/xsltng/xslt/docbook.xsl");
    private static volatile XsltExecutable cached;

    public static void render(Path docbookXml, Path outXhtml) {
        try {
            if (cached == null) cached = XsltPipeline.compile(XSLTNG);
            Files.createDirectories(outXhtml.getParent());
            var t = cached.load30();
            var serializer = XsltPipeline.SAXON.newSerializer(outXhtml.toFile());
            t.applyTemplates(new javax.xml.transform.stream.StreamSource(docbookXml.toFile()), serializer);
            fixInvalidEncodingMeta(outXhtml);
        } catch (Exception e) { throw new IllegalStateException(e); }
    }

    /**
     * docbook-xslTNG 2.5.0's modules/head.xsl unconditionally emits
     * {@code <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>}
     * in EVERY document's head (live-verified, Task 7: no stylesheet parameter
     * controls it -- it is a literal result element in the m:html-head template).
     * Per the HTML5/XHTML5 spec that "encoding declaration state" pragma is valid
     * ONLY under the HTML parser; it is disallowed in XML documents -- and this
     * pipeline renders .xhtml (XML-serialized) output. The pinned XHTML5 RNG
     * grammar correctly rejects it (live-verified via JingGate: "Bad value
     * 'Content-Type' for attribute 'http-equiv' on element 'meta'"), which would
     * otherwise fail EVERY render, not just this fixture. The spec-sanctioned
     * equivalent for XML-serialized documents is the {@code charset} attribute
     * form; substituting it changes no declared encoding (both say utf-8) and is
     * a no-op if xslTNG's literal output ever changes.
     */
    private static void fixInvalidEncodingMeta(Path outXhtml) throws java.io.IOException {
        String invalid = "<meta http-equiv=\"Content-Type\" content=\"text/html; charset=utf-8\"/>";
        String valid = "<meta charset=\"utf-8\"/>";
        String content = Files.readString(outXhtml);
        if (content.contains(invalid)) Files.writeString(outXhtml, content.replace(invalid, valid));
    }

    /** Copies xslTNG's resources (css/js) next to the published site once. */
    public static void stageResources(Path siteDir) {
        Path inJar = Path.of("target/xsltng/org/docbook/xsltng/resources");
        Path fromZip = Path.of("target/xsltng-resources/resources");
        Path src = Files.isDirectory(inJar) ? inJar : fromZip;
        try (Stream<Path> s = Files.walk(src)) {
            Path dest = siteDir.resolve("resources");
            for (Path p : (Iterable<Path>) s::iterator) {
                Path d = dest.resolve(src.relativize(p).toString());
                if (Files.isDirectory(p)) Files.createDirectories(d);
                else { Files.createDirectories(d.getParent()); Files.copy(p, d, StandardCopyOption.REPLACE_EXISTING); }
            }
        } catch (Exception e) { throw new IllegalStateException(e); }
    }
    private DocbookRenderer() {}
}

package io.github.metavacua.pipeline;

import net.sf.saxon.s9api.XdmDestination;
import net.sf.saxon.s9api.XsltExecutable;
import java.nio.file.*;
import java.util.stream.Stream;

public final class DocbookRenderer {
    private static final Path XSLTNG = Path.of("target/xsltng/org/docbook/xsltng/xslt/docbook.xsl");
    // Second-pass workaround stylesheet -- see lift-lang.xsl header for why it exists.
    private static final Path LIFT_LANG = Path.of("src/main/resources/xslt/lift-lang.xsl");
    // Benign race: XsltExecutable is immutable; a concurrent first call at worst compiles twice.
    private static volatile XsltExecutable cached;
    private static volatile XsltExecutable liftLangCached;

    public static void render(Path docbookXml, Path outXhtml) {
        try {
            if (cached == null) cached = XsltPipeline.compile(XSLTNG);
            if (liftLangCached == null) liftLangCached = XsltPipeline.compile(LIFT_LANG);
            Files.createDirectories(outXhtml.getParent());

            // Stage 1: xslTNG proper, into memory (not straight to the serializer) so
            // stage 2 can post-process the tree before anything is written to disk.
            var t = cached.load30();
            var xdm = new XdmDestination();
            t.applyTemplates(new javax.xml.transform.stream.StreamSource(docbookXml.toFile()), xdm);

            // Stage 2: lift-lang.xsl -- see its header comment (upstream chunk-root
            // html/@lang gap, Task 8). Serializes with the same settings xslTNG's own
            // <xsl:output> would have used (mirrored in lift-lang.xsl), so output shape
            // is unchanged except for the added @lang.
            var lift = liftLangCached.load30();
            var serializer = XsltPipeline.SAXON.newSerializer(outXhtml.toFile());
            lift.applyTemplates(xdm.getXdmNode(), serializer);

            fixInvalidEncodingMeta(outXhtml);
        } catch (Exception e) { throw new IllegalStateException(e); }
    }

    /**
     * docbook-xslTNG 2.8.3's modules/head.xsl STILL unconditionally emits
     * {@code <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>}
     * in EVERY document's head (live-verified on upgrade to 2.8.3, Task 8: the
     * literal result element is unchanged at modules/head.xsl line 23, and
     * modules/chunk-cleanup.xsl's {@code $ctype} variable/apply-templates pass
     * (mode {@code m:chunk-cleanup}, on-no-match="shallow-copy") copies it
     * through verbatim -- no template rule in that mode converts it). Per the
     * HTML5/XHTML5 spec that "encoding declaration state" pragma is valid ONLY
     * under the HTML parser; it is disallowed in XML documents -- and this
     * pipeline renders .xhtml (XML-serialized) output. The pinned XHTML5 RNG
     * grammar correctly rejects it (live-verified via JingGate: "Bad value
     * 'Content-Type' for attribute 'http-equiv' on element 'meta'"), which would
     * otherwise fail EVERY render, not just this fixture. The spec-sanctioned
     * equivalent for XML-serialized documents is the {@code charset} attribute
     * form; substituting it changes no declared encoding (both say utf-8) and is
     * a no-op if xslTNG's literal output ever changes.
     * Exact-literal substitution: if a future xslTNG release changes attribute
     * order/whitespace this no-ops and stage 7 (jing vs XHTML5 RNG) fails loudly
     * on the un-substituted meta -- fail-loud by design, revisit against the
     * pinned xslTNG version on upgrade.
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

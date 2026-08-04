package io.github.metavacua.pipeline;

import net.sf.saxon.s9api.QName;
import org.w3c.dom.Document;
import java.nio.file.*;
import java.time.Instant;
import java.util.*;
import java.util.stream.Stream;

/** The audit-census engine: per-document stage driver, partition, health page.
 *  Coordination only — all content interpretation lives in XSLT/Schematron/grammars. */
public final class CensusEngine {
    record GateResult(String id, String status, String message) {
        String xml() {
            return message == null
                ? "    <gate id=\"" + id + "\" status=\"" + status + "\"/>\n"
                : "    <gate id=\"" + id + "\" status=\"" + status + "\"><message>"
                  + escape(message) + "</message></gate>\n";
        }
    }

    public static void main(String[] args) throws Exception {
        Path root = Constants.REPO_ROOT;
        List<Path> corpus;
        try (Stream<Path> s = Files.walk(root.resolve("docs"))) {
            corpus = s.filter(p -> p.toString().endsWith(".md"))
                .filter(p -> {
                    String rel = root.relativize(p).toString().replace('\\', '/');
                    return Constants.CORPUS_EXCLUDES.stream()
                        .noneMatch(x -> rel.equals(x) || rel.startsWith(x + "/"));
                })
                .sorted().toList();
        }
        for (Path p : corpus) { // manifest attribute-safety precondition
            assertAttributeSafePath(root.relativize(p).toString());
        }
        var manifestEntries = ManifestGenerator.generate(root, corpus);
        Path manifest = root.resolve("target/generated-resources/repo-metadata.xml");
        ManifestGenerator.writeManifest(manifestEntries, manifest);

        var xsl = XsltPipeline.compile(root.resolve("src/main/resources/xslt/xhtml-to-docbook.xsl"));
        Path site = root.resolve("target/site");
        Files.createDirectories(site);
        var rows = new StringBuilder();
        int published = 0;

        for (Path src : corpus) {
            String rel = root.relativize(src).toString().replace('\\', '/');
            var gates = new ArrayList<GateResult>();
            String titleClass = "unknown"; String checks = ""; boolean pass = true;
            Document docbook = null; Path rendered = null;
            try {
                var x = MarkdownToXhtml.convert(Files.readString(src));       // stage 1
                gates.add(new GateResult("wf-fragment", "pass", null));
                titleClass = AuditChecks.titleClass(x);
                int c1 = AuditChecks.c1Count(Files.readString(src));
                docbook = XsltPipeline.apply(xsl, x.dom(), Map.of(            // stage 2
                    new QName("authored-title"), x.frontMatterTitle(),
                    new QName("source-path"), rel,
                    new QName("manifest-uri"), manifest.toUri().toString()));
                Path db = root.resolve("target/docbook/" + rel.replaceAll("\\.md$", ".xml"));
                Files.createDirectories(db.getParent());
                Files.writeString(db, Xml.serialize(docbook));
                pass &= gate(gates, "docbook-rng",                             // stage 3
                    JingGate.validate(JingGate.DOCBOOK_RNC, db));
                pass &= gate(gates, "policy", SchematronGate.check(docbook));  // stage 4
                var me = manifestEntries.stream().filter(m -> m.path().equals(rel)).findFirst().orElseThrow();
                checks = auditXml(docbook, me, titleClass, c1, x);
                if (pass) {
                    rendered = site.resolve(rel.replaceFirst("^docs/", "").replaceAll("\\.md$", ".xhtml"));
                    DocbookRenderer.render(db, rendered);                      // stage 5
                    gates.add(new GateResult("render", "pass", null));
                    // Rendered output starts <!DOCTYPE html> (polyglot XHTML5): hardenedBuilder
                    // rejects any doctype by design, so this parse uses outputBuilder — the
                    // parser meant for OUR renderer's own output, not source XML (Xml.java).
                    try { Xml.outputBuilder().parse(rendered.toFile());       // stage 6
                          gates.add(new GateResult("wf-out", "pass", null)); }
                    catch (Exception e) {
                        gates.add(new GateResult("wf-out", "fail", e.getMessage()));
                        pass = false;
                        skip(gates, "xhtml5-rng", "vnu");
                    }
                    if (pass) {
                        pass &= gate(gates, "xhtml5-rng",                     // stage 7
                            JingGate.validate(JingGate.XHTML5_RNC, rendered));
                        if (pass) pass &= gate(gates, "vnu", VnuGate.check(rendered)); // stage 8 (sequenced)
                        else skip(gates, "vnu");
                    }
                } else { skip(gates, "render", "wf-out", "xhtml5-rng", "vnu"); }
            } catch (Exception e) {
                gates.add(new GateResult("pipeline-error", "fail", String.valueOf(e.getMessage())));
                pass = false;
            }
            if (!pass && rendered != null) Files.deleteIfExists(rendered);    // partition: no publish
            if (pass) published++;
            rows.append("  <doc path=\"").append(rel).append("\" published=\"").append(pass)
                .append("\" titleClass=\"").append(titleClass).append("\">\n");
            gates.forEach(g -> rows.append(g.xml()));
            rows.append(checks).append("  </doc>\n");
        }

        Path census = root.resolve("target/census/census.xml");
        Files.createDirectories(census.getParent());
        Files.writeString(census, "<census generated=\"" + Instant.now() + "\" total=\""
            + corpus.size() + "\" published=\"" + published + "\">\n" + rows + "</census>\n");

        // Health page: census -> docbook fragment -> injected into the model index -> rendered.
        var toDb = XsltPipeline.compile(root.resolve("src/main/resources/xslt/census-to-docbook.xsl"));
        // census.xml is OUR generated file (no doctype): hardenedBuilder is correct here.
        Document censusDoc = Xml.hardenedBuilder().parse(census.toFile());
        Path frag = root.resolve("target/census/census-fragment.xml");
        Files.writeString(frag, Xml.serialize(XsltPipeline.apply(toDb, censusDoc, Map.of())));
        var inject = XsltPipeline.compile(root.resolve("src/main/resources/xslt/inject-census.xsl"));
        Path indexSrc = root.resolve("src/main/docbook/index.xml");
        // Source XML, no doctype: hardenedBuilder is correct here.
        Document index = Xml.hardenedBuilder().parse(indexSrc.toFile());

        // Model-index manifest equality: the authored index.xml's own metadata must agree
        // with what the manifest derives from path/git truth for that same file — the
        // forward gate's first real exercise (authored metadata vs derived truth).
        var modelEntry = ManifestGenerator.generate(root, List.of(indexSrc)).get(0);
        String authoredPubdate = AuditChecks.evalOne(index, "string(//*:info/*:pubdate)");
        String authoredBiblioid = AuditChecks.evalOne(index, "string(//*:info/*:biblioid)");
        if (!authoredPubdate.equals(modelEntry.pubdate()) || !authoredBiblioid.equals(modelEntry.biblioid()))
            throw new IllegalStateException("model index metadata drift: pubdate authored='"
                + authoredPubdate + "' derived='" + modelEntry.pubdate() + "'; biblioid authored='"
                + authoredBiblioid + "' derived='" + modelEntry.biblioid() + "'");

        Document merged = XsltPipeline.apply(inject, index,
            Map.of(new QName("census-fragment-uri"), frag.toUri().toString()));
        Path mergedPath = root.resolve("target/census/index-merged.xml");
        Files.writeString(mergedPath, Xml.serialize(merged));
        // The merged model must itself pass the gates it demands of others:
        require(JingGate.validate(JingGate.DOCBOOK_RNC, mergedPath), "model index: docbook-rng");
        require(SchematronGate.check(merged), "model index: policy");
        Path indexOut = site.resolve("index.xhtml");
        DocbookRenderer.render(mergedPath, indexOut);
        Xml.outputBuilder().parse(indexOut.toFile()); // rendered output: outputBuilder, not hardenedBuilder
        require(JingGate.validate(JingGate.XHTML5_RNC, indexOut), "model index: xhtml5-rng");
        require(VnuGate.check(indexOut), "model index: vnu");
        DocbookRenderer.stageResources(site);
        var sitemapXsl = XsltPipeline.compile(root.resolve("src/main/resources/xslt/sitemap.xsl"));
        Files.writeString(site.resolve("sitemap.xml"),
            Xml.serialize(XsltPipeline.apply(sitemapXsl, censusDoc, Map.of())));
        System.out.println("census: " + corpus.size() + " docs, " + published + " published");
    }

    /** Attribute-safety precondition (Task 4 review carry): manifest/census XML is built
     *  by hand-assembled string concatenation, never a serializer, so any path containing
     *  an unescaped XML attribute-value special character would corrupt or misattribute
     *  output. Fail loud before touching the pipeline. */
    static void assertAttributeSafePath(String rel) {
        if (rel.contains("\"") || rel.contains("&") || rel.contains("<"))
            throw new IllegalStateException("unsafe path for XML attributes: " + rel);
    }

    static boolean gate(List<GateResult> gates, String id, List<String> findings) {
        gates.add(findings.isEmpty() ? new GateResult(id, "pass", null)
            : new GateResult(id, "fail", String.join(" | ", findings)));
        return findings.isEmpty();
    }
    static void skip(List<GateResult> gates, String... ids) {
        for (String id : ids) gates.add(new GateResult(id, "skipped", null));
    }
    static void require(List<String> findings, String what) {
        if (!findings.isEmpty())
            throw new IllegalStateException(what + " FAILED: " + findings);
    }
    static String auditXml(Document docbook, ManifestGenerator.ManifestEntry me,
                           String titleClass, int c1, MarkdownToXhtml.XhtmlResult x) {
        var b = new StringBuilder();
        var region = AuditChecks.biblioRegion(docbook);
        b.append("    <check id=\"biblio-region\" present=\"").append(region.isPresent())
         .append("\" count=\"").append(region.orElse(0)).append("\"/>\n");
        if (region.isPresent()) {
            int[] ls = AuditChecks.linkStats(docbook);
            b.append("    <check id=\"link-stats\" with=\"").append(ls[0])
             .append("\" without=\"").append(ls[1]).append("\"/>\n");
        }
        String lvl = AuditChecks.evalOne(x.dom(),
            "string((//*:body//*[matches(local-name(),'^h[1-6]$')])[1]/substring(local-name(),2))");
        b.append("    <check id=\"first-heading-level\" value=\"").append(lvl).append("\"/>\n");
        b.append("    <check id=\"date-provenance\" value=\"generated-from-git-first-commit\" date=\"")
         .append(me.pubdate()).append("\"/>\n");
        b.append("    <check id=\"c1-controls\" value=\"").append(c1).append("\"/>\n");
        return b.toString();
    }
    static String escape(String s) {
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;");
    }
    private CensusEngine() {}
}

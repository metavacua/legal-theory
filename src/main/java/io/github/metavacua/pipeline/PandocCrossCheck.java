package io.github.metavacua.pipeline;

import java.nio.file.*;
import java.util.List;
import java.util.stream.Stream;

/** CI-informational only: independent (non-commonmark) parse of the same corpus.
 *  Reports divergences; never gates. */
public final class PandocCrossCheck {
    public static void main(String[] args) throws Exception {
        Path root = Constants.REPO_ROOT;
        List<Path> corpus;
        try (Stream<Path> s = Files.walk(root.resolve("docs"))) {
            corpus = s.filter(p -> p.toString().endsWith(".md"))
                .filter(p -> Constants.CORPUS_EXCLUDES.stream()
                    .noneMatch(x -> root.relativize(p).toString().startsWith(x)))
                .sorted().toList();
        }
        int rncFail = 0, diverged = 0, crashed = 0;
        for (Path src : corpus) {
            Path out = Files.createTempFile("pandoc", ".xml");
            try {
                var p = new ProcessBuilder("pandoc", "-f", "markdown", "-t", "docbook5", "-s",
                    src.toString(), "-o", out.toString()).inheritIO().start();
                if (p.waitFor() != 0) { rncFail++; continue; }
                if (!JingGate.validate(JingGate.DOCBOOK_RNC, out).isEmpty()) { rncFail++; continue; }
                Path ours = root.resolve("target/docbook/"
                    + root.relativize(src).toString().replaceAll("\\.md$", ".xml"));
                if (!Files.exists(ours)) continue;
                var a = ContentComparator.extract(Xml.outputBuilder().parse(out.toFile()),
                    ContentComparator.Vocabulary.DOCBOOK);
                var b = ContentComparator.extract(Xml.hardenedBuilder().parse(ours.toFile()),
                    ContentComparator.Vocabulary.DOCBOOK);
                var diff = ContentComparator.diff(a, b);
                if (!diff.isEmpty()) { diverged++;
                    System.out.println("DIVERGES " + src + " :: " + diff.get(0)); }
            } catch (Exception e) {
                crashed++;
                System.out.println("CRASH " + src + " :: " + e);
            } finally {
                Files.deleteIfExists(out);
            }
        }
        System.out.println("pandoc cross-check: " + corpus.size() + " docs, "
            + rncFail + " pandoc-side failures, " + diverged + " content divergences, "
            + crashed + " per-doc crashes");
    }
    private PandocCrossCheck() {}
}

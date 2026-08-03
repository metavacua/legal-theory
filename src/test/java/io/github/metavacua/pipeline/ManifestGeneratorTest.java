package io.github.metavacua.pipeline;

import org.eclipse.jgit.api.Git;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import static org.junit.jupiter.api.Assertions.*;

class ManifestGeneratorTest {
    static Git repo(Path dir) throws Exception {
        var git = Git.init().setDirectory(dir.toFile()).call();
        Files.writeString(dir.resolve("a.md"), "first");
        git.add().addFilepattern("a.md").call();
        git.commit().setMessage("c1").setAuthor("t", "t@t").setSign(false).call();
        Files.writeString(dir.resolve("a.md"), "second");
        git.add().addFilepattern("a.md").call();
        git.commit().setMessage("c2").setAuthor("t", "t@t").setSign(false).call();
        return git;
    }
    @Test void earliestCommitDateAndBiblioid(@TempDir Path dir) throws Exception {
        try (var git = repo(dir)) {
            var entries = ManifestGenerator.generate(dir, List.of(dir.resolve("a.md")));
            assertEquals(1, entries.size());
            assertEquals("a.md", entries.get(0).path());
            assertEquals(java.time.LocalDate.now(java.time.ZoneOffset.UTC).toString(),
                entries.get(0).pubdate()); // both commits today; earliest == today in fixture
            assertEquals(Constants.CANONICAL_BASE + "a.md", entries.get(0).biblioid());
        }
    }
    @Test void untrackedFileFailsLoudly(@TempDir Path dir) throws Exception {
        try (var git = repo(dir)) {
            Files.writeString(dir.resolve("new.md"), "never committed");
            var e = assertThrows(IllegalStateException.class,
                () -> ManifestGenerator.generate(dir, List.of(dir.resolve("new.md"))));
            assertTrue(e.getMessage().contains("untracked"));
        }
    }
    @Test void shallowCloneFailsLoudlyNamingTheFix(@TempDir Path dir) throws Exception {
        try (var git = repo(dir)) {
            var head = git.getRepository().resolve("HEAD").name();
            Files.writeString(dir.resolve(".git/shallow"), head + "\n");
            var e = assertThrows(IllegalStateException.class,
                () -> ManifestGenerator.generate(dir, List.of(dir.resolve("a.md"))));
            assertTrue(e.getMessage().contains("fetch-depth: 0"));
        }
    }
}

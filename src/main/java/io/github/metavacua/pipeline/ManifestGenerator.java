package io.github.metavacua.pipeline;

import org.eclipse.jgit.storage.file.FileRepositoryBuilder;
import org.eclipse.jgit.lib.Repository;
import org.eclipse.jgit.revwalk.RevCommit;
import org.eclipse.jgit.revwalk.RevSort;
import org.eclipse.jgit.revwalk.RevWalk;
import org.eclipse.jgit.treewalk.filter.AndTreeFilter;
import org.eclipse.jgit.treewalk.filter.PathFilterGroup;
import org.eclipse.jgit.treewalk.filter.TreeFilter;

import java.io.File;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.List;

public final class ManifestGenerator {
    public record ManifestEntry(String path, String pubdate, String biblioid) {}

    public static List<ManifestEntry> generate(Path repoRoot, List<Path> files) {
        try (Repository repo = new FileRepositoryBuilder()
                 .setGitDir(new File(repoRoot.toFile(), ".git")).build()) {
            if (!repo.getObjectDatabase().getShallowCommits().isEmpty())
                throw new IllegalStateException(
                    "shallow clone: git history is truncated; a RevWalk would silently mis-date "
                    + "every file to the graft point. Fix: actions/checkout with fetch-depth: 0.");
            var out = new ArrayList<ManifestEntry>();
            for (Path f : files) {
                String rel = repoRoot.relativize(f.toAbsolutePath().normalize())
                                     .toString().replace('\\', '/');
                try (RevWalk walk = new RevWalk(repo)) {
                    walk.markStart(walk.parseCommit(repo.resolve("HEAD")));
                    walk.setTreeFilter(AndTreeFilter.create(
                        PathFilterGroup.createFromStrings(rel), TreeFilter.ANY_DIFF));
                    walk.sort(RevSort.COMMIT_TIME_DESC, true);
                    walk.sort(RevSort.REVERSE, true); // oldest first
                    RevCommit first = walk.next();
                    if (first == null)
                        throw new IllegalStateException(
                            "untracked file (no commit touches path '" + rel + "'): "
                            + "commit it before building; dates are never fabricated.");
                    String date = first.getAuthorIdent().getWhenAsInstant()
                        .atZone(ZoneOffset.UTC).toLocalDate().toString();
                    out.add(new ManifestEntry(rel, date, Constants.CANONICAL_BASE + rel));
                }
            }
            return out;
        } catch (IllegalStateException e) { throw e;
        } catch (Exception e) { throw new IllegalStateException(e); }
    }

    public static void writeManifest(List<ManifestEntry> entries, Path out) {
        var sb = new StringBuilder("<manifest>\n");
        for (var e : entries)
            sb.append("  <doc path=\"").append(e.path())
              .append("\" pubdate=\"").append(e.pubdate())
              .append("\" biblioid=\"").append(e.biblioid()).append("\"/>\n");
        sb.append("</manifest>\n");
        try {
            Files.createDirectories(out.getParent());
            Files.writeString(out, sb.toString());
        } catch (Exception e) { throw new IllegalStateException(e); }
    }
    private ManifestGenerator() {}
}

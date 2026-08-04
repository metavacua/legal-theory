package io.github.metavacua.pipeline;

import java.nio.file.Path;
import java.util.List;

public final class Constants {
    /** Canonical document identity: repo URL + branch segment, deliberately
     *  pinned to main on every build (identity, not build provenance). */
    public static final String CANONICAL_BASE =
        "https://github.com/metavacua/legal-theory/blob/main/";
    public static final Path REPO_ROOT = Path.of(System.getProperty("user.dir"));
    public static final List<String> CORPUS_EXCLUDES = List.of("docs/superpowers");
    private Constants() {}
}

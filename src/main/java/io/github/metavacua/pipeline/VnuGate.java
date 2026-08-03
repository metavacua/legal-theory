package io.github.metavacua.pipeline;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.TimeUnit;

public final class VnuGate {
    private static final Path VNU = Path.of("target/tools/vnu.jar");
    // vnu.jar is not a fat jar and carries no Main-Class (live-verified, Task 7): its
    // SimpleCommandLineValidator needs its own runtime dependency closure (jing, icu4j,
    // jetty, etc. -- staged by the copy-vnu-deps POM execution, see pom.xml) on the
    // classpath, kept isolated from this project's own org.relaxng:jing/Saxon versions.
    private static final String VNU_CP = VNU + java.io.File.pathSeparator + "target/tools/vnu-lib/*";

    /** Sequenced final gate: caller runs this ONLY after stages 6 and 7 pass.
     *  Findings are returned verbatim so the census carries the why/how.
     *  Fail-loud contract: this gate must NEVER silently report "clean" on an
     *  infrastructure fault (missing input, broken classpath, hung process,
     *  unparseable vnu output) -- only a genuine, fully-parsed vnu run may
     *  return a (possibly empty) findings list. */
    public static List<String> check(Path xhtml) {
        if (!Files.isRegularFile(xhtml)) {
            throw new IllegalStateException("vnu input does not exist: " + xhtml);
        }
        try {
            var pb = new ProcessBuilder("java", "-cp", VNU_CP,
                "nu.validator.client.SimpleCommandLineValidator", "--xml", xhtml.toString());
            pb.redirectErrorStream(true);
            Process p = pb.start();
            var out = new String(p.getInputStream().readAllBytes());
            if (!p.waitFor(120, TimeUnit.SECONDS)) {
                p.destroyForcibly();
                throw new IllegalStateException("vnu timed out after 120s on " + xhtml);
            }
            int code = p.exitValue();
            var findings = new ArrayList<String>();
            // vnu's exit code reflects ERRORS only (live-verified, Task 7): a lone C1
            // control character is reported as "info warning" with exit 0, so gating
            // on exit code would silently drop exactly the defect class this gate
            // exists to catch. Every genuine per-file finding line -- of any severity
            // -- is captured instead: SimpleCommandLineValidator's plain-text format
            // always opens a finding with the quoted file URI ("file:...":line.col:...),
            // which distinguishes it from the one other line on this stream, Jetty's
            // startup banner ("<timestamp>:INFO::main: Logging initialized...").
            out.lines().filter(l -> l.startsWith("\"")).forEach(findings::add);
            if (code == 0) {
                return findings; // clean, or warning-level findings surfaced with exit 0
            }
            if (code == 1) {
                if (findings.isEmpty()) {
                    throw new IllegalStateException(
                        "vnu exited 1 with no parseable findings (infrastructure fault?):\n" + out);
                }
                return findings;
            }
            throw new IllegalStateException("vnu unexpected exit " + code + ":\n" + out);
        } catch (IllegalStateException e) {
            throw e;
        } catch (Exception e) { throw new IllegalStateException(e); }
    }
    private VnuGate() {}
}

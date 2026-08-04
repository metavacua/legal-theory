# Java/Maven Publishing Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the search-and-sort publishing pipeline specified in `docs/superpowers/specs/2026-08-03-java-maven-publishing-pipeline-design.md`: Markdown → DocBook 5.2 → XHTML5 (XML serialization) with triangulated validation, a per-document audit census, a correct-by-construction model index, and a real GitHub Pages deployment whose initial content is the corpus health page.

**Architecture:** All-JVM Maven build at the repository root. commonmark-java renders MD to strict XHTML fragments; an authored Saxon XSLT 3.0 stylesheet (a total function over commonmark's finite vocabulary — unmapped elements hard-fail) produces DocBook 5.2; xslTNG renders XHTML5; gates are native JDK XML parsing, jing (both grammars), SchXslt2-compiled Schematron, and vnu as a sequenced final gate. A census engine coordinates stages per document, partitions conforming/non-conforming, and renders the health page into the model index. Content logic lives in XSLT/Schematron/grammars; Java is coordination + two leaf utilities.

**Tech Stack:** JDK 25, Maven 3.9.x, Saxon-HE 12.10, commonmark-java (+ yaml-front-matter, gfm-tables), org.relaxng:jing, nu.validator:validator (whattf datatypes + vnu), SchXslt2, xslTNG 2.8.x, JGit, JUnit 5.

## Global Constraints

- JDK **25** (LTS) target (`maven.compiler.release=25`); Maven **3.9.x**; single module `io.github.metavacua:legal-theory-pipeline` with `pom.xml` at the repository root.
- **One XSLT engine: Saxon-HE**, everywhere. The JDK's built-in Xalan (XSLT 1.0) is never used for any transform. The JDK's XML **parsers** (DocumentBuilder, XXE-hardened) are the well-formedness gates.
- Output is **XHTML5, the XML serialization**, served as `.xhtml` / `application/xhtml+xml` (empirically verified deployable as directory index, spec §site-index). The WHATWG living standard is not an authority; pinned references only.
- **No generated artifact is ever committed** — everything generated goes under `target/`.
- **Absence → gate; ambiguity → mark; fabrication → never.** No heuristic content interpretation. No title generation of any kind — titles come only from YAML front matter (`title:`) or authored DocBook `info/title`.
- The authored XSLT is a **total function**: any XHTML element without a fixed mapping rule terminates the transform with an error (no silent drops except the two specified: `hr`, `br`).
- Corpus scan = `docs/**/*.md` **excluding `docs/superpowers/**`**. Known baseline: 123 documents, 88 with a `Works cited` section, title classes 0/0/98/3/21/1 — recorded as descriptive baselines, never hardcoded invariants.
- Every dependency/action version below is **re-verified live** (Maven Central search API / GitHub) immediately before being written into `pom.xml`/workflow YAML; stay on the pinned line, take newer patches of the same line only.
- CI: `actions/checkout@v6` with **`fetch-depth: 0`** (mandatory — the manifest generator hard-fails on shallow clones by design), `actions/setup-java@v5`, `actions/upload-pages-artifact@v4`, `actions/deploy-pages@v4`. **No `workflow_dispatch` triggers, ever.** `permissions: contents: read` except the deploy job.
- Canonical identifier constant: `https://github.com/metavacua/legal-theory/blob/main/` + repo-relative path — one named constant (`Constants.CANONICAL_BASE`), branch segment deliberately `main` on all builds.
- Commit style: conventional prefixes (`feat:`/`test:`/`chore:`/`ci:`/`docs:`), one commit per green TDD cycle, `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>` trailer.

## File Structure

```
pom.xml                                                    (Task 1)
.gitignore                                                 (Task 1: target/)
src/main/java/io/github/metavacua/pipeline/
  Constants.java                                           (Task 1)
  Xml.java                    hardened DocumentBuilder     (Task 3)
  MarkdownToXhtml.java        + record XhtmlResult         (Task 3)
  ManifestGenerator.java      + record ManifestEntry       (Task 4)
  XsltPipeline.java           s9api compile/apply helper   (Task 5)
  JingGate.java                                            (Task 2)
  SchematronGate.java         SVRL failed-assert parse     (Task 6)
  DocbookRenderer.java        xslTNG via s9api             (Task 7)
  VnuGate.java                subprocess --xml             (Task 7)
  ContentComparator.java                                   (Task 9)
  AuditChecks.java                                         (Task 10)
  CensusEngine.java           main(): stages+partition     (Task 10)
  PandocCrossCheck.java       CI informational leg         (Task 12)
src/main/resources/xslt/
  xhtml-to-docbook.xsl                                     (Task 5)
  extract-content.xsl                                      (Task 9)
  census-to-docbook.xsl                                    (Task 10)
  inject-census.xsl                                        (Task 10)
  sitemap.xsl                                              (Task 10)
src/main/resources/schematron/policy.sch                   (Task 6)
src/main/resources/schema/xhtml5/…                         (Task 2: vendored, pinned, +LICENSE)
src/main/docbook/index.xml                                 (Task 8: model document)
src/main/docbook/index.md                                  (Task 8: authored twin)
src/test/java/io/github/metavacua/pipeline/*Test.java      (Tasks 2–10)
src/test/resources/fixtures/…                              (Tasks 3–10)
.github/workflows/build-and-deploy.yml                     (Task 12)
target/                                                    (generated only: manifest, DocBook, XHTML5,
                                                            census.xml, site/ — never committed)
```

---

### Task 1: Maven skeleton, pinned versions, profiles

**Files:**
- Create: `pom.xml`, `.gitignore`, `src/main/java/io/github/metavacua/pipeline/Constants.java`

**Interfaces:**
- Produces: `Constants.CANONICAL_BASE` (String), `Constants.REPO_ROOT` (Path resolved from `user.dir`), `Constants.CORPUS_EXCLUDES` (`List.of("docs/superpowers")`), Maven properties consumed by all later tasks, profiles `jing-current` (default) / `jing-2009`.

- [ ] **Step 1: Live-verify every version before writing the POM**

```bash
for GA in org.commonmark:commonmark org.commonmark:commonmark-ext-yaml-front-matter \
  org.commonmark:commonmark-ext-gfm-tables net.sf.saxon:Saxon-HE org.relaxng:jing \
  nu.validator:validator org.eclipse.jgit:org.eclipse.jgit org.docbook:docbook-xslTNG \
  name.dmaus.schxslt:schxslt2 org.junit.jupiter:junit-jupiter \
  org.apache.maven.plugins:maven-surefire-plugin org.codehaus.mojo:exec-maven-plugin \
  org.codehaus.mojo:xml-maven-plugin com.googlecode.maven-download-plugin:download-maven-plugin; do
  g=${GA%%:*}; a=${GA##*:}
  echo -n "$GA -> "
  curl -s "https://search.maven.org/solrsearch/select?q=g:$g+AND+a:$a&rows=1&wt=json" \
    | python3 -c "import json,sys; d=json.load(sys.stdin)['response']['docs']; print(d[0]['latestVersion'] if d else 'NOT FOUND')"
done
```
Expected: one line per artifact. Rule: for Saxon stay on the 12.x line (latest 12.x patch), commonmark core and extensions must share one version, everything else take the printed version. Record results in the commit message.

- [ ] **Step 2: Write `pom.xml`** (versions below are this plan's last-verified values — replace each with Step 1's output):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">
  <modelVersion>4.0.0</modelVersion>
  <groupId>io.github.metavacua</groupId>
  <artifactId>legal-theory-pipeline</artifactId>
  <version>0.1.0-SNAPSHOT</version>
  <packaging>jar</packaging>

  <properties>
    <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
    <maven.compiler.release>25</maven.compiler.release>
    <commonmark.version>0.29.0</commonmark.version>
    <saxon.version>12.10</saxon.version>
    <jing.version>20241231</jing.version>
    <vnu.version>20.7.2</vnu.version>
    <jgit.version>7.7.1.202607240634-r</jgit.version>
    <xsltng.version>2.8.3</xsltng.version>
    <schxslt2.version>1.11.2</schxslt2.version>
    <junit.version>5.13.4</junit.version>
    <docbook.rnc.url>https://docs.oasis-open.org/docbook/docbook/v5.2/os/rng/docbookxi.rnc</docbook.rnc.url>
    <docbook.rnc.sha256>REPLACED_IN_TASK_2</docbook.rnc.sha256>
  </properties>

  <dependencies>
    <dependency><groupId>org.commonmark</groupId><artifactId>commonmark</artifactId><version>${commonmark.version}</version></dependency>
    <dependency><groupId>org.commonmark</groupId><artifactId>commonmark-ext-yaml-front-matter</artifactId><version>${commonmark.version}</version></dependency>
    <dependency><groupId>org.commonmark</groupId><artifactId>commonmark-ext-gfm-tables</artifactId><version>${commonmark.version}</version></dependency>
    <dependency><groupId>net.sf.saxon</groupId><artifactId>Saxon-HE</artifactId><version>${saxon.version}</version></dependency>
    <!-- nu.validator:validator supplies BOTH the whattf datatype library jing needs
         for the XHTML5 schemas AND the vnu checker classes (Task 2, Task 7). -->
    <dependency><groupId>nu.validator</groupId><artifactId>validator</artifactId><version>${vnu.version}</version></dependency>
    <dependency><groupId>org.eclipse.jgit</groupId><artifactId>org.eclipse.jgit</artifactId><version>${jgit.version}</version></dependency>
    <dependency><groupId>org.docbook</groupId><artifactId>docbook-xslTNG</artifactId><version>${xsltng.version}</version></dependency>
    <dependency><groupId>org.junit.jupiter</groupId><artifactId>junit-jupiter</artifactId><version>${junit.version}</version><scope>test</scope></dependency>
  </dependencies>

  <profiles>
    <profile>
      <id>jing-current</id>
      <activation><activeByDefault>true</activeByDefault></activation>
      <dependencies>
        <dependency><groupId>org.relaxng</groupId><artifactId>jing</artifactId><version>${jing.version}</version></dependency>
      </dependencies>
    </profile>
    <profile>
      <id>jing-2009</id>
      <dependencies>
        <dependency><groupId>com.thaiopensource</groupId><artifactId>jing</artifactId><version>20091111</version></dependency>
      </dependencies>
    </profile>
  </profiles>

  <build>
    <plugins>
      <plugin>
        <groupId>org.apache.maven.plugins</groupId><artifactId>maven-enforcer-plugin</artifactId><version>3.5.0</version>
        <executions><execution><goals><goal>enforce</goal></goals><configuration><rules>
          <requireJavaVersion><version>[25,26)</version></requireJavaVersion>
          <requireMavenVersion><version>[3.9,4)</version></requireMavenVersion>
        </rules></configuration></execution></executions>
      </plugin>
      <plugin>
        <groupId>org.apache.maven.plugins</groupId><artifactId>maven-surefire-plugin</artifactId><version>3.5.4</version>
      </plugin>
    </plugins>
  </build>
</project>
```

- [ ] **Step 3: Write `.gitignore` and `Constants.java`**

`.gitignore`:
```
target/
```

`src/main/java/io/github/metavacua/pipeline/Constants.java`:
```java
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
```

- [ ] **Step 4: Verify and commit**

Run: `mvn -q validate && mvn -q -Pjing-2009 validate`
Expected: `BUILD SUCCESS` twice.
```bash
git add pom.xml .gitignore src/main/java/io/github/metavacua/pipeline/Constants.java
git commit -m "feat: Maven skeleton — pinned toolchain, jing agreement profiles, canonical-identity constant"
```

---

### Task 2: Pinned grammars + jing gate (DocBook 5.2 and XHTML5)

**Files:**
- Create: `src/main/java/io/github/metavacua/pipeline/JingGate.java`
- Create: `src/main/resources/schema/xhtml5/**` (vendored), `src/test/java/io/github/metavacua/pipeline/JingGateTest.java`
- Create: `src/test/resources/fixtures/docbook/minimal-valid.xml`, `fixtures/docbook/invalid-element.xml`, `fixtures/xhtml/minimal-valid.xhtml`, `fixtures/xhtml/invalid-element.xhtml`
- Modify: `pom.xml` (download-maven-plugin execution + real sha256)

**Interfaces:**
- Produces: `JingGate.validate(Path schemaRnc, Path xmlFile) -> List<String>` (empty = valid; entries are `line:col: message`), `JingGate.DOCBOOK_RNC` (Path `target/schema/docbookxi.rnc`), `JingGate.XHTML5_RNC` (Path to vendored `xhtml5.rnc`).

- [ ] **Step 1: Pin the DocBook grammar with a real checksum**

```bash
curl -fsSL -o /tmp/docbookxi.rnc https://docs.oasis-open.org/docbook/docbook/v5.2/os/rng/docbookxi.rnc
sha256sum /tmp/docbookxi.rnc
```
Paste the printed hash into `pom.xml`'s `<docbook.rnc.sha256>`. Add to `<build><plugins>`:
```xml
<plugin>
  <groupId>com.googlecode.maven-download-plugin</groupId><artifactId>download-maven-plugin</artifactId><version>1.13.0</version>
  <executions><execution>
    <id>fetch-docbook-grammar</id><phase>generate-resources</phase><goals><goal>wget</goal></goals>
    <configuration>
      <url>${docbook.rnc.url}</url>
      <outputDirectory>${project.build.directory}/schema</outputDirectory>
      <outputFileName>docbookxi.rnc</outputFileName>
      <sha256>${docbook.rnc.sha256}</sha256>
    </configuration>
  </execution></executions>
</plugin>
```
Run: `mvn -q generate-resources && ls target/schema/docbookxi.rnc` — Expected: file present (build fails on checksum mismatch — that is the point).

- [ ] **Step 2: Vendor the pinned XHTML5 RELAX NG schema set**

```bash
git clone --depth 1 --branch 26.7.31 --filter=blob:none --sparse https://github.com/validator/validator.git /tmp/vnu-src
git -C /tmp/vnu-src sparse-checkout set schema
mkdir -p src/main/resources/schema/xhtml5
cp -r /tmp/vnu-src/schema/* src/main/resources/schema/xhtml5/
ls src/main/resources/schema/xhtml5/html5/xhtml5.rnc src/main/resources/schema/xhtml5/html5/LICENSE
```
Expected: both files exist (MIT license vendored alongside, required for redistribution).

- [ ] **Step 3: Write the failing tests**

`src/test/resources/fixtures/docbook/minimal-valid.xml`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<article xmlns="http://docbook.org/ns/docbook" version="5.2">
  <info><title>Fixture</title></info>
  <para>Valid minimal DocBook 5.2 article.</para>
</article>
```
`fixtures/docbook/invalid-element.xml`: same but with `<nonsuch/>` after `</para>` (line matters not).
`fixtures/xhtml/minimal-valid.xhtml`:
```xml
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" lang="en"><head><title>Fixture</title></head>
<body><h1>Fixture</h1><p>Valid.</p></body></html>
```
`fixtures/xhtml/invalid-element.xhtml`: same but `<blink>no</blink>` inside `<body>`.

`JingGateTest.java`:
```java
package io.github.metavacua.pipeline;

import org.junit.jupiter.api.Test;
import java.nio.file.Path;
import java.util.List;
import static org.junit.jupiter.api.Assertions.*;

class JingGateTest {
    static final Path FX = Path.of("src/test/resources/fixtures");

    @Test void validDocbookPasses() {
        assertEquals(List.of(), JingGate.validate(JingGate.DOCBOOK_RNC, FX.resolve("docbook/minimal-valid.xml")));
    }
    @Test void invalidDocbookFails() {
        assertFalse(JingGate.validate(JingGate.DOCBOOK_RNC, FX.resolve("docbook/invalid-element.xml")).isEmpty());
    }
    @Test void validXhtmlPasses() {
        // Proves the whattf datatype wiring: compiling xhtml5.rnc requires the
        // datatype library from nu.validator:validator on the classpath.
        assertEquals(List.of(), JingGate.validate(JingGate.XHTML5_RNC, FX.resolve("xhtml/minimal-valid.xhtml")));
    }
    @Test void invalidXhtmlFails() {
        assertFalse(JingGate.validate(JingGate.XHTML5_RNC, FX.resolve("xhtml/invalid-element.xhtml")).isEmpty());
    }
}
```
Run: `mvn -q test -Dtest=JingGateTest` — Expected: FAIL (JingGate not defined).

- [ ] **Step 4: Implement `JingGate`**

```java
package io.github.metavacua.pipeline;

import com.thaiopensource.util.PropertyMapBuilder;
import com.thaiopensource.validate.ValidateProperty;
import com.thaiopensource.validate.ValidationDriver;
import com.thaiopensource.validate.rng.CompactSchemaReader;
import org.xml.sax.ErrorHandler;
import org.xml.sax.SAXParseException;

import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

public final class JingGate {
    public static final Path DOCBOOK_RNC = Path.of("target/schema/docbookxi.rnc");
    public static final Path XHTML5_RNC  = Path.of("src/main/resources/schema/xhtml5/html5/xhtml5.rnc");

    public static List<String> validate(Path schemaRnc, Path xmlFile) {
        List<String> errors = new ArrayList<>();
        ErrorHandler eh = new ErrorHandler() {
            public void warning(SAXParseException e) { /* warnings are not gate failures */ }
            public void error(SAXParseException e) { errors.add(fmt(e)); }
            public void fatalError(SAXParseException e) { errors.add(fmt(e)); }
            private String fmt(SAXParseException e) {
                return e.getLineNumber() + ":" + e.getColumnNumber() + ": " + e.getMessage();
            }
        };
        try {
            var b = new PropertyMapBuilder();
            b.put(ValidateProperty.ERROR_HANDLER, eh);
            var driver = new ValidationDriver(b.toPropertyMap(), CompactSchemaReader.getInstance());
            if (!driver.loadSchema(ValidationDriver.fileInputSource(schemaRnc.toFile())))
                throw new IllegalStateException("schema failed to compile: " + schemaRnc + " " + errors);
            driver.validate(ValidationDriver.fileInputSource(xmlFile.toFile()));
        } catch (IllegalStateException e) {
            throw e;
        } catch (Exception e) {
            errors.add("0:0: " + e);
        }
        return errors;
    }
    private JingGate() {}
}
```

- [ ] **Step 5: Run, handle the vintage contingency, commit**

Run: `mvn -q generate-resources test -Dtest=JingGateTest`
Expected: PASS. **Contingency (decision rule, execute only if `validXhtmlPasses` throws `schema failed to compile` with a datatype-library error):** the 2026 schemas need newer datatypes than validator 20.7.2 provides. Re-vendor the schemas from the tag matching the datatype jar's vintage instead: repeat Step 2 with `--branch 20.6.30`. Record which vintage was used in the commit message.
Also run: `mvn -q -Pjing-2009 test -Dtest=JingGateTest` — Expected: PASS (the required-agreement leg works locally).
```bash
git add pom.xml src/main/resources/schema src/main/java/io/github/metavacua/pipeline/JingGate.java src/test
git commit -m "feat: pinned DocBook 5.2 + XHTML5 grammars with jing gate (checksum-pinned fetch, vendored MIT schema set, whattf datatype wiring)"
```

---

### Task 3: `md-to-xhtml` leaf utility

**Files:**
- Create: `Xml.java`, `MarkdownToXhtml.java`, `MarkdownToXhtmlTest.java`
- Create: `src/test/resources/fixtures/md/plain.md`, `fixtures/md/frontmatter.md`, `fixtures/md/rawhtml.md`, `fixtures/md/headingless.md`

**Interfaces:**
- Produces: `record XhtmlResult(org.w3c.dom.Document dom, String serialized, String frontMatterTitle)` (`frontMatterTitle` is `""` when absent) and `MarkdownToXhtml.convert(String markdown) -> XhtmlResult`. `Xml.hardenedBuilder() -> DocumentBuilder`, `Xml.serialize(Document) -> String`.

- [ ] **Step 1: Fixtures**

`plain.md`:
```markdown
### **A Body Heading**

Some prose with an autolink, accessed September 2, 2025, <https://example.com/a> and A & B.
```
`frontmatter.md`:
```markdown
---
title: An Authored Title
---
# Heading One

Paragraph.
```
`rawhtml.md`:
```markdown
Text with <blink>raw html</blink> inside.
```
`headingless.md`:
```markdown
Just a paragraph. No headings anywhere.
```

- [ ] **Step 2: Failing tests**

```java
package io.github.metavacua.pipeline;

import org.junit.jupiter.api.Test;
import java.nio.file.Files;
import java.nio.file.Path;
import static org.junit.jupiter.api.Assertions.*;

class MarkdownToXhtmlTest {
    static String fx(String n) throws Exception {
        return Files.readString(Path.of("src/test/resources/fixtures/md/" + n));
    }
    @Test void plainMarkdownIsWellFormedXml() throws Exception {
        var r = MarkdownToXhtml.convert(fx("plain.md"));
        assertNotNull(r.dom()); // parse succeeded => well-formed
        assertEquals("", r.frontMatterTitle());
        assertTrue(r.serialized().contains("&amp;"), "text ampersand must be XML-escaped");
        assertTrue(r.serialized().contains("https://example.com/a"));
    }
    @Test void frontMatterTitleExtractedAndNotRenderedIntoBody() throws Exception {
        var r = MarkdownToXhtml.convert(fx("frontmatter.md"));
        assertEquals("An Authored Title", r.frontMatterTitle());
        assertFalse(r.serialized().contains("An Authored Title</h"), "front matter must not leak into body");
        assertTrue(r.serialized().contains("<title>An Authored Title</title>"));
    }
    @Test void rawHtmlIsEscapedNotPassedThrough() throws Exception {
        var r = MarkdownToXhtml.convert(fx("rawhtml.md"));
        assertFalse(r.serialized().contains("<blink>"));
        assertTrue(r.serialized().contains("&lt;blink&gt;"));
    }
    @Test void headinglessStillConverts() throws Exception {
        var r = MarkdownToXhtml.convert(fx("headingless.md"));
        assertEquals("", r.frontMatterTitle()); // absence is the census/gate layer's concern, not this unit's
        assertNotNull(r.dom());
    }
}
```
Run: `mvn -q test -Dtest=MarkdownToXhtmlTest` — Expected: FAIL (classes not defined).

- [ ] **Step 3: Implement `Xml` and `MarkdownToXhtml`**

`Xml.java`:
```java
package io.github.metavacua.pipeline;

import org.w3c.dom.Document;
import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.transform.OutputKeys;
import javax.xml.transform.TransformerFactory;
import javax.xml.transform.dom.DOMSource;
import javax.xml.transform.stream.StreamResult;
import java.io.StringWriter;

public final class Xml {
    /** XXE-hardened, fail-fast: no DTDs, no entity expansion, no XInclude. */
    public static DocumentBuilder hardenedBuilder() {
        try {
            var f = DocumentBuilderFactory.newInstance();
            f.setNamespaceAware(true);
            f.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
            f.setXIncludeAware(false);
            f.setExpandEntityReferences(false);
            return f.newDocumentBuilder();
        } catch (Exception e) { throw new IllegalStateException(e); }
    }
    /** Serialization only — identity copy, NOT a transform (Xalan does no XSLT here). */
    public static String serialize(Document d) {
        try {
            var t = TransformerFactory.newInstance().newTransformer();
            t.setOutputProperty(OutputKeys.OMIT_XML_DECLARATION, "yes");
            var w = new StringWriter();
            t.transform(new DOMSource(d), new StreamResult(w));
            return w.toString();
        } catch (Exception e) { throw new IllegalStateException(e); }
    }
    private Xml() {}
}
```

`MarkdownToXhtml.java`:
```java
package io.github.metavacua.pipeline;

import org.commonmark.Extension;
import org.commonmark.ext.front.matter.YamlFrontMatterExtension;
import org.commonmark.ext.front.matter.YamlFrontMatterVisitor;
import org.commonmark.ext.gfm.tables.TablesExtension;
import org.commonmark.parser.Parser;
import org.commonmark.renderer.html.HtmlRenderer;
import org.w3c.dom.Document;

import java.io.ByteArrayInputStream;
import java.nio.charset.StandardCharsets;
import java.util.List;

public final class MarkdownToXhtml {
    public record XhtmlResult(Document dom, String serialized, String frontMatterTitle) {}

    private static final List<Extension> EXT =
        List.of(YamlFrontMatterExtension.create(), TablesExtension.create());
    private static final Parser PARSER = Parser.builder().extensions(EXT).build();
    private static final HtmlRenderer RENDERER =
        HtmlRenderer.builder().extensions(EXT).escapeHtml(true).build();

    public static XhtmlResult convert(String markdown) {
        var node = PARSER.parse(markdown);
        var fm = new YamlFrontMatterVisitor();
        node.accept(fm);
        String title = fm.getData().getOrDefault("title", List.of()).stream().findFirst().orElse("");
        String body = RENDERER.render(node);
        String doc = "<html xmlns=\"http://www.w3.org/1999/xhtml\"><head><title>"
            + escape(title) + "</title></head><body>" + body + "</body></html>";
        try {
            Document dom = Xml.hardenedBuilder()
                .parse(new ByteArrayInputStream(doc.getBytes(StandardCharsets.UTF_8)));
            return new XhtmlResult(dom, doc, title);
        } catch (Exception e) {
            // Malformed output is a build failure, never silently corrected.
            throw new IllegalStateException("commonmark output is not well-formed XML: " + e.getMessage(), e);
        }
    }
    private static String escape(String s) {
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;");
    }
    private MarkdownToXhtml() {}
}
```

- [ ] **Step 4: Run and commit**

Run: `mvn -q test -Dtest=MarkdownToXhtmlTest` — Expected: PASS.
```bash
git add src/main/java src/test
git commit -m "feat: md-to-xhtml leaf utility — strict XHTML fragments, front-matter title channel, hardened native parse"
```

---

### Task 4: `manifest-generator` leaf utility (the impurity quarantine)

**Files:**
- Create: `ManifestGenerator.java`, `ManifestGeneratorTest.java`

**Interfaces:**
- Produces: `record ManifestEntry(String path, String pubdate, String biblioid)`;
  `ManifestGenerator.generate(Path repoRoot, List<Path> files) -> List<ManifestEntry>` (throws `IllegalStateException("shallow clone…")` / `IllegalStateException("untracked…")`);
  `ManifestGenerator.writeManifest(List<ManifestEntry>, Path out)` emitting
  `<manifest><doc path="…" pubdate="YYYY-MM-DD" biblioid="…"/>…</manifest>`.

- [ ] **Step 1: Failing tests (fixture repo built with JGit itself)**

```java
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
```
Run: `mvn -q test -Dtest=ManifestGeneratorTest` — Expected: FAIL.

- [ ] **Step 2: Implement**

```java
package io.github.metavacua.pipeline;

import org.eclipse.jgit.internal.storage.file.FileRepositoryBuilder;
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
```
(Paths and attribute values here contain no `"` or `&` by construction — repo paths and ISO dates; the census engine asserts this at scan time by rejecting any source path containing `"` or `&`.)

- [ ] **Step 3: Run and commit**

Run: `mvn -q test -Dtest=ManifestGeneratorTest` — Expected: PASS.
```bash
git add src/main/java src/test
git commit -m "feat: manifest generator — quarantined git impurity, shallow/untracked hard-fails, path-identity semantics"
```

---

### Task 5: Authored `xhtml-to-docbook.xsl` + Saxon pipeline helper

**Files:**
- Create: `src/main/resources/xslt/xhtml-to-docbook.xsl`, `XsltPipeline.java`, `XhtmlToDocbookTest.java`
- Test fixtures: reuse Task 3's md fixtures + `fixtures/md/levelskip.md`, `fixtures/md/table.md`

**Interfaces:**
- Produces: `XsltPipeline.compile(Path xsl) -> net.sf.saxon.s9api.XsltExecutable`; `XsltPipeline.apply(XsltExecutable, Document in, Map<QName,String> params) -> org.w3c.dom.Document`; the stylesheet's params: `authored-title` (string), `source-path` (string), `manifest-uri` (string).
- Consumes: Task 3's `XhtmlResult`, Task 4's manifest file.

- [ ] **Step 1: Additional fixtures**

`levelskip.md`:
```markdown
# Top

Intro.

### Skipped To Three

Deep prose.
```
`table.md`:
```markdown
| A | B |
|---|---|
| 1 | 2 |
```

- [ ] **Step 2: Failing tests**

```java
package io.github.metavacua.pipeline;

import net.sf.saxon.s9api.QName;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import org.w3c.dom.Document;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;
import static org.junit.jupiter.api.Assertions.*;

class XhtmlToDocbookTest {
    static net.sf.saxon.s9api.XsltExecutable XSL;
    static Path manifest;

    @BeforeAll static void setup() throws Exception {
        XSL = XsltPipeline.compile(Path.of("src/main/resources/xslt/xhtml-to-docbook.xsl"));
        manifest = Files.createTempFile("manifest", ".xml");
        Files.writeString(manifest, """
            <manifest>
              <doc path="fx.md" pubdate="2026-07-01" biblioid="%sfx.md"/>
            </manifest>""".formatted(Constants.CANONICAL_BASE));
    }
    static Document convert(String mdFixture, String title) throws Exception {
        var x = MarkdownToXhtml.convert(Files.readString(Path.of("src/test/resources/fixtures/md/" + mdFixture)));
        return XsltPipeline.apply(XSL, x.dom(), Map.of(
            new QName("authored-title"), title,
            new QName("source-path"), "fx.md",
            new QName("manifest-uri"), manifest.toUri().toString()));
    }
    static String ser(Document d) { return Xml.serialize(d); }

    @Test void infoFieldsComeFromParamsAndManifest() throws Exception {
        String s = ser(convert("frontmatter.md", "An Authored Title"));
        assertTrue(s.contains("<title>An Authored Title</title>"));
        assertTrue(s.contains("<pubdate role=\"generated-from-git-first-commit\">2026-07-01</pubdate>"));
        assertTrue(s.contains("biblioid"));
        assertTrue(s.contains(">Text</dc:type>") || s.contains("dc:type>Text"));
    }
    @Test void headingsNestAsSections() throws Exception {
        String s = ser(convert("frontmatter.md", "T"));
        assertTrue(s.contains("<section>") && s.contains("<title>Heading One</title>"));
    }
    @Test void levelSkipClosesGapWithoutPhantomSections() throws Exception {
        Document d = convert("levelskip.md", "T");
        // h1 -> section; h3 nests DIRECTLY under it (gap closed, no empty intermediate)
        var xp = javax.xml.xpath.XPathFactory.newInstance().newXPath();
        var n = (org.w3c.dom.NodeList) xp.evaluate(
            "//*[local-name()='section']/*[local-name()='section']", d,
            javax.xml.xpath.XPathConstants.NODESET);
        assertEquals(1, n.getLength());
    }
    @Test void tightListItemsGainParaWrapper() throws Exception {
        var x = MarkdownToXhtml.convert("- alpha\n- beta\n");
        String s = ser(XsltPipeline.apply(XSL, x.dom(), Map.of(
            new QName("authored-title"), "T",
            new QName("source-path"), "fx.md",
            new QName("manifest-uri"), manifest.toUri().toString())));
        assertTrue(s.contains("<listitem><para>alpha</para></listitem>")
                || s.contains("<listitem>\n<para>alpha</para>"));
    }
    @Test void gfmTableMapsToInformaltable() throws Exception {
        String s = ser(convert("table.md", "T"));
        assertTrue(s.contains("<informaltable") && s.contains("<td>1</td>"));
    }
    @Test void unmappedElementTerminatesLoudly() throws Exception {
        // strikethrough extension NOT enabled in prod; simulate an unmapped element directly
        var dom = Xml.hardenedBuilder().parse(new java.io.ByteArrayInputStream(
            "<html xmlns=\"http://www.w3.org/1999/xhtml\"><head><title/></head><body><kbd>x</kbd></body></html>"
            .getBytes()));
        var e = assertThrows(RuntimeException.class, () -> XsltPipeline.apply(XSL, dom, Map.of(
            new QName("authored-title"), "T",
            new QName("source-path"), "fx.md",
            new QName("manifest-uri"), manifest.toUri().toString())));
        assertTrue(e.getMessage().contains("Unmapped"));
    }
    @Test void outputValidatesAgainstRealDocbookGrammar() throws Exception {
        Document d = convert("plain.md", "A Title");
        Path tmp = Files.createTempFile("out", ".xml");
        Files.writeString(tmp, Xml.serialize(d));
        assertEquals(List.of(), JingGate.validate(JingGate.DOCBOOK_RNC, tmp));
    }
}
```
Run: `mvn -q generate-resources test -Dtest=XhtmlToDocbookTest` — Expected: FAIL.

- [ ] **Step 3: Implement `XsltPipeline`**

```java
package io.github.metavacua.pipeline;

import net.sf.saxon.s9api.*;
import org.w3c.dom.Document;
import javax.xml.transform.dom.DOMSource;
import java.nio.file.Path;
import java.util.Map;

public final class XsltPipeline {
    /** One Saxon processor for the whole JVM — the single XSLT engine. */
    public static final Processor SAXON = new Processor(false);

    public static XsltExecutable compile(Path xsl) {
        try {
            return SAXON.newXsltCompiler().compile(new javax.xml.transform.stream.StreamSource(xsl.toFile()));
        } catch (SaxonApiException e) { throw new IllegalStateException(e); }
    }
    public static Document apply(XsltExecutable xsl, Document in, Map<QName, String> params) {
        try {
            Xslt30Transformer t = xsl.load30();
            var m = new java.util.HashMap<QName, XdmValue>();
            params.forEach((k, v) -> m.put(k, new XdmAtomicValue(v)));
            t.setStylesheetParameters(m);
            var outDoc = Xml.hardenedBuilder().newDocument();
            var dest = SAXON.newDocumentBuilder(); // unused: keep DOM route below
            javax.xml.transform.dom.DOMResult result = new javax.xml.transform.dom.DOMResult(outDoc);
            t.applyTemplates(SAXON.newDocumentBuilder().build(new DOMSource(in)),
                             SAXON.newSerializer()); // placeholder replaced next line
            throw new UnsupportedOperationException();
        } catch (Exception e) { throw new IllegalStateException(e); }
    }
    private XsltPipeline() {}
}
```
**Correction — use this final body for `apply` (s9api DOMDestination):**
```java
    public static Document apply(XsltExecutable xsl, Document in, Map<QName, String> params) {
        try {
            Xslt30Transformer t = xsl.load30();
            var m = new java.util.HashMap<QName, XdmValue>();
            params.forEach((k, v) -> m.put(k, new XdmAtomicValue(v)));
            t.setStylesheetParameters(m);
            Document outDoc = Xml.hardenedBuilder().newDocument();
            t.applyTemplates(SAXON.newDocumentBuilder().build(new DOMSource(in)),
                             new DOMDestination(outDoc));
            return outDoc;
        } catch (SaxonApiException e) {
            throw new IllegalStateException(e.getMessage(), e); // carries xsl:message terminate text
        } catch (Exception e) { throw new IllegalStateException(e); }
    }
```

- [ ] **Step 4: Write the stylesheet — the complete total function**

`src/main/resources/xslt/xhtml-to-docbook.xsl`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="3.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    xmlns:h="http://www.w3.org/1999/xhtml"
    xmlns="http://docbook.org/ns/docbook"
    xmlns:xlink="http://www.w3.org/1999/xlink"
    xmlns:dc="http://purl.org/dc/terms/"
    xmlns:f="urn:legal-theory:f"
    exclude-result-prefixes="xsl xs h f">

  <xsl:output method="xml" indent="yes"/>
  <xsl:param name="authored-title" as="xs:string" select="''"/>
  <xsl:param name="source-path" as="xs:string" required="yes"/>
  <xsl:param name="manifest-uri" as="xs:string" required="yes"/>

  <xsl:variable name="mdoc" select="doc($manifest-uri)/manifest/doc[@path eq $source-path]"/>

  <xsl:template match="/h:html">
    <xsl:if test="empty($mdoc)">
      <xsl:message terminate="yes" select="'No manifest entry for ' || $source-path"/>
    </xsl:if>
    <article version="5.2">
      <info>
        <title><xsl:value-of select="$authored-title"/></title>
        <pubdate role="generated-from-git-first-commit"><xsl:value-of select="$mdoc/@pubdate"/></pubdate>
        <biblioid class="uri" role="generated-from-path"><xsl:value-of select="$mdoc/@biblioid"/></biblioid>
        <dc:type>Text</dc:type>
      </info>
      <xsl:sequence select="f:sectionize(h:body/node(), 1)"/>
    </article>
  </xsl:template>

  <!-- Flat h1..h6 siblings -> nested sections. A level with no headings recurses
       deeper, so an h1->h3 skip nests the h3 section directly (gap closed). -->
  <xsl:function name="f:sectionize" as="node()*">
    <xsl:param name="nodes" as="node()*"/>
    <xsl:param name="level" as="xs:integer"/>
    <xsl:choose>
      <xsl:when test="$level gt 6"><xsl:apply-templates select="$nodes"/></xsl:when>
      <xsl:otherwise>
        <xsl:for-each-group select="$nodes"
            group-starting-with="h:*[local-name() eq 'h' || string($level)]">
          <xsl:choose>
            <xsl:when test="self::h:*[local-name() eq 'h' || string($level)]">
              <section>
                <title><xsl:apply-templates/></title>
                <xsl:sequence select="f:sectionize(tail(current-group()), $level + 1)"/>
              </section>
            </xsl:when>
            <xsl:otherwise>
              <xsl:sequence select="f:sectionize(current-group(), $level + 1)"/>
            </xsl:otherwise>
          </xsl:choose>
        </xsl:for-each-group>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:function>

  <!-- ============ fixed element mappings (one rule per element) ============ -->
  <xsl:template match="h:p"><para><xsl:apply-templates/></para></xsl:template>
  <xsl:template match="h:ul"><itemizedlist><xsl:apply-templates/></itemizedlist></xsl:template>
  <xsl:template match="h:ol"><orderedlist><xsl:apply-templates/></orderedlist></xsl:template>
  <xsl:template match="h:li">
    <listitem>
      <xsl:for-each-group select="node()" group-adjacent="boolean(
          self::h:p or self::h:ul or self::h:ol or self::h:pre
          or self::h:blockquote or self::h:table)">
        <xsl:choose>
          <xsl:when test="current-grouping-key()"><xsl:apply-templates select="current-group()"/></xsl:when>
          <xsl:when test="not(normalize-space(string-join(current-group() ! string(.), '')))"/>
          <xsl:otherwise><para><xsl:apply-templates select="current-group()"/></para></xsl:otherwise>
        </xsl:choose>
      </xsl:for-each-group>
    </listitem>
  </xsl:template>
  <xsl:template match="h:em"><emphasis><xsl:apply-templates/></emphasis></xsl:template>
  <xsl:template match="h:strong"><emphasis role="strong"><xsl:apply-templates/></emphasis></xsl:template>
  <xsl:template match="h:a[@href]"><link xlink:href="{@href}"><xsl:apply-templates/></link></xsl:template>
  <xsl:template match="h:code[parent::h:pre]"><xsl:apply-templates/></xsl:template>
  <xsl:template match="h:pre"><programlisting><xsl:value-of select="."/></programlisting></xsl:template>
  <xsl:template match="h:code"><code><xsl:apply-templates/></code></xsl:template>
  <xsl:template match="h:blockquote"><blockquote><xsl:apply-templates/></blockquote></xsl:template>
  <xsl:template match="h:img">
    <inlinemediaobject><imageobject><imagedata fileref="{@src}"/></imageobject></inlinemediaobject>
  </xsl:template>
  <xsl:template match="h:table"><informaltable><xsl:apply-templates/></informaltable></xsl:template>
  <xsl:template match="h:thead"><thead><xsl:apply-templates/></thead></xsl:template>
  <xsl:template match="h:tbody"><tbody><xsl:apply-templates/></tbody></xsl:template>
  <xsl:template match="h:tr"><tr><xsl:apply-templates/></tr></xsl:template>
  <xsl:template match="h:th"><th><xsl:apply-templates/></th></xsl:template>
  <xsl:template match="h:td"><td><xsl:apply-templates/></td></xsl:template>

  <!-- The two specified drops (presentational, no DocBook equivalent). -->
  <xsl:template match="h:hr | h:br"/>
  <!-- head/title handled at info level; never body content. -->
  <xsl:template match="h:head"/>

  <!-- Total-function enforcement: anything unmapped is a hard failure. -->
  <xsl:template match="h:*">
    <xsl:message terminate="yes" select="'Unmapped XHTML element: ' || local-name()"/>
  </xsl:template>
  <xsl:template match="text()"><xsl:value-of select="."/></xsl:template>
</xsl:stylesheet>
```
(Remove the first, placeholder version of `apply` from Step 3 — only the corrected `DOMDestination` body ships. Import `net.sf.saxon.s9api.DOMDestination`.)

- [ ] **Step 5: Run and commit**

Run: `mvn -q generate-resources test -Dtest=XhtmlToDocbookTest` — Expected: PASS (7 tests).
```bash
git add src/main src/test
git commit -m "feat: authored XHTML->DocBook 5.2 stylesheet — total function, section nesting, manifest-fed info, unmapped elements hard-fail"
```

---

### Task 6: Policy Schematron (SchXslt2)

**Files:**
- Create: `src/main/resources/schematron/policy.sch`, `SchematronGate.java`, `SchematronGateTest.java`
- Modify: `pom.xml` (xml-maven-plugin execution transpiling `policy.sch` → `target/generated-resources/policy.xsl` with Saxon as TrAX factory)

**Interfaces:**
- Produces: `SchematronGate.COMPILED` (Path `target/generated-resources/policy.xsl`); `SchematronGate.check(Document docbook) -> List<String>` (SVRL failed-assert texts; empty = pass).

- [ ] **Step 1: Write `policy.sch`**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<sch:schema xmlns:sch="http://purl.oclc.org/dsdl/schematron" queryBinding="xslt3">
  <sch:ns prefix="db" uri="http://docbook.org/ns/docbook"/>
  <sch:ns prefix="dc" uri="http://purl.org/dc/terms/"/>
  <sch:pattern>
    <sch:rule context="db:article/db:info">
      <!-- W3C ACT rule 2779a5: page must have a non-empty title. Enforced here
           because the pinned XHTML5 RELAX NG grammar accepts an empty title. -->
      <sch:assert test="normalize-space(db:title) ne ''"
        >info/title must be non-empty (authored via front matter or native DocBook; never generated)</sch:assert>
      <sch:assert test="db:pubdate castable as xs:date"
        >info/pubdate must be a valid ISO date</sch:assert>
      <sch:assert test="starts-with(db:biblioid[@class='uri'], 'https://github.com/metavacua/legal-theory/blob/main/')"
        >info/biblioid[@class='uri'] must carry the canonical identity prefix</sch:assert>
      <sch:assert test="dc:type eq 'Text'"
        >dc:type must be the DCMI Type Vocabulary literal 'Text'</sch:assert>
    </sch:rule>
  </sch:pattern>
</sch:schema>
```
(Biblioid/pubdate **equality against the manifest** is asserted by the census engine in Java — a coordination-level string compare — because Schematron has no portable runtime-parameter channel for per-document expected values; recorded as such in the spec's policy split.)

- [ ] **Step 2: Discover the SchXslt2 transpiler entry point (deterministic decision rule)**

```bash
mvn -q dependency:copy -Dartifact=name.dmaus.schxslt:schxslt2:1.11.2 -DoutputDirectory=/tmp/schxslt2
unzip -l /tmp/schxslt2/schxslt2-1.11.2.jar | grep -E '\.xsl'
```
Decision rule: the transpiler entry is the root-level `.xsl` the artifact's README names (expected name: `transpile.xsl`). Record the actual jar-internal path; use it below (shown as `schxslt2/transpile.xsl` — replace with the recorded path).

- [ ] **Step 3: Add the transpile execution to `pom.xml`**

```xml
<plugin>
  <groupId>org.codehaus.mojo</groupId><artifactId>xml-maven-plugin</artifactId><version>1.2.1</version>
  <dependencies>
    <dependency><groupId>net.sf.saxon</groupId><artifactId>Saxon-HE</artifactId><version>${saxon.version}</version></dependency>
    <dependency><groupId>name.dmaus.schxslt</groupId><artifactId>schxslt2</artifactId><version>${schxslt2.version}</version></dependency>
  </dependencies>
  <executions><execution>
    <id>transpile-policy-schematron</id><phase>generate-resources</phase><goals><goal>transform</goal></goals>
    <configuration>
      <transformerFactory>net.sf.saxon.TransformerFactoryImpl</transformerFactory>
      <transformationSets><transformationSet>
        <dir>src/main/resources/schematron</dir>
        <includes><include>policy.sch</include></includes>
        <stylesheet>classpath:/schxslt2/transpile.xsl</stylesheet>
        <outputDir>${project.build.directory}/generated-resources</outputDir>
        <fileMappers><fileMapper implementation="org.codehaus.plexus.components.io.filemappers.MergeFileMapper">
          <targetName>policy.xsl</targetName></fileMapper></fileMappers>
      </transformationSet></transformationSets>
    </configuration>
  </execution></executions>
</plugin>
```
Run: `mvn -q generate-resources && ls target/generated-resources/policy.xsl` — Expected: file exists.
Contingency (only if `classpath:` stylesheet refs are unsupported by the plugin version): unpack the jar with `maven-dependency-plugin` `unpack` into `target/schxslt2` in `initialize` phase and reference the filesystem path instead.

- [ ] **Step 4: Failing tests + `SchematronGate`**

`SchematronGateTest.java`:
```java
package io.github.metavacua.pipeline;

import org.junit.jupiter.api.Test;
import org.w3c.dom.Document;
import java.io.ByteArrayInputStream;
import static org.junit.jupiter.api.Assertions.*;

class SchematronGateTest {
    static Document doc(String title, String pubdate, String biblioid) throws Exception {
        String xml = """
            <article xmlns="http://docbook.org/ns/docbook" xmlns:dc="http://purl.org/dc/terms/" version="5.2">
              <info><title>%s</title>
                <pubdate role="generated-from-git-first-commit">%s</pubdate>
                <biblioid class="uri" role="generated-from-path">%s</biblioid>
                <dc:type>Text</dc:type></info>
              <para>x</para></article>""".formatted(title, pubdate, biblioid);
        return Xml.hardenedBuilder().parse(new ByteArrayInputStream(xml.getBytes()));
    }
    @Test void compliantDocPasses() throws Exception {
        assertEquals(0, SchematronGate.check(
            doc("Real Title", "2026-07-01", Constants.CANONICAL_BASE + "x.md")).size());
    }
    @Test void emptyTitleFails() throws Exception {
        var f = SchematronGate.check(doc("", "2026-07-01", Constants.CANONICAL_BASE + "x.md"));
        assertTrue(f.stream().anyMatch(m -> m.contains("non-empty")));
    }
    @Test void malformedDateFails() throws Exception {
        assertFalse(SchematronGate.check(doc("T", "July 2026", Constants.CANONICAL_BASE + "x.md")).isEmpty());
    }
    @Test void foreignBiblioidFails() throws Exception {
        assertFalse(SchematronGate.check(doc("T", "2026-07-01", "https://elsewhere.example/x")).isEmpty());
    }
}
```
`SchematronGate.java`:
```java
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
```
Run: `mvn -q generate-resources test -Dtest=SchematronGateTest` — Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add pom.xml src/main src/test
git commit -m "feat: policy Schematron via SchXslt2/Saxon — non-empty title (W3C ACT 2779a5), ISO pubdate, canonical biblioid, dc:type"
```

---

### Task 7: xslTNG render + XHTML5 output gates + vnu sequenced gate

**Files:**
- Create: `DocbookRenderer.java`, `VnuGate.java`, `RenderAndGatesTest.java`
- Create: `src/test/resources/fixtures/xhtml/mojibake.xhtml`
- Modify: `pom.xml` (dependency-plugin: unpack xslTNG; copy vnu jar)

**Interfaces:**
- Produces: `DocbookRenderer.render(Path docbookXml, Path outXhtml)` (xslTNG via Saxon; `.xhtml` extension; resources staged once to `target/site/resources/`); `DocbookRenderer.stageResources(Path siteDir)`; `VnuGate.check(Path xhtmlFile) -> List<String>` (findings; empty = pass).

- [ ] **Step 1: POM executions**

```xml
<plugin>
  <groupId>org.apache.maven.plugins</groupId><artifactId>maven-dependency-plugin</artifactId><version>3.8.1</version>
  <executions>
    <execution><id>unpack-xsltng</id><phase>generate-resources</phase><goals><goal>unpack</goal></goals>
      <configuration><artifactItems><artifactItem>
        <groupId>org.docbook</groupId><artifactId>docbook-xslTNG</artifactId><version>${xsltng.version}</version>
        <outputDirectory>${project.build.directory}/xsltng</outputDirectory>
      </artifactItem></artifactItems></configuration></execution>
    <execution><id>copy-vnu</id><phase>generate-resources</phase><goals><goal>copy</goal></goals>
      <configuration><artifactItems><artifactItem>
        <groupId>nu.validator</groupId><artifactId>validator</artifactId><version>${vnu.version}</version>
        <destFileName>vnu.jar</destFileName>
        <outputDirectory>${project.build.directory}/tools</outputDirectory>
      </artifactItem></artifactItems></configuration></execution>
  </executions>
</plugin>
```
Run: `mvn -q generate-resources`
Then inspect: `ls target/xsltng/org/docbook/xsltng/xslt/docbook.xsl && ls target/xsltng/org/docbook/xsltng/resources 2>/dev/null || echo NO-RESOURCES-IN-JAR`
Contingency (only on `NO-RESOURCES-IN-JAR`): fetch the 2.8.3 distribution zip from the project's Codeberg release, checksum-pin it via download-maven-plugin exactly like Task 2 Step 1, unpack `resources/` to `target/xsltng-resources`; `stageResources` copies from whichever location exists. Record the sha256 in the POM.
Also probe vnu's entry point: `unzip -p target/tools/vnu.jar META-INF/MANIFEST.MF | grep Main-Class` — Expected: `nu.validator.client.SimpleCommandLineValidator`. If absent, invoke that class via `-cp` instead of `-jar` (both shown below).

- [ ] **Step 2: Failing tests**

`fixtures/xhtml/mojibake.xhtml` — copy `minimal-valid.xhtml`, then inside `<p>` insert the literal C1 character U+0097 (create via `printf 'Valid.\xc2\x97'` when writing the file — legal XML 1.0, illegal HTML5):
```bash
python3 - <<'EOF'
src = open('src/test/resources/fixtures/xhtml/minimal-valid.xhtml').read()
open('src/test/resources/fixtures/xhtml/mojibake.xhtml','w').write(src.replace('Valid.', 'Valid.\u0097'))
EOF
```

`RenderAndGatesTest.java`:
```java
package io.github.metavacua.pipeline;

import org.junit.jupiter.api.Test;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import static org.junit.jupiter.api.Assertions.*;

class RenderAndGatesTest {
    @Test void rendersDocbookToParsableValidXhtml() throws Exception {
        Path out = Path.of("target/test-render/minimal.xhtml");
        DocbookRenderer.render(Path.of("src/test/resources/fixtures/docbook/minimal-valid.xml"), out);
        // stage 6: native parse
        Xml.hardenedBuilder().parse(out.toFile());
        // stage 7: pinned grammar
        assertEquals(List.of(), JingGate.validate(JingGate.XHTML5_RNC, out));
    }
    @Test void mojibakePassesGrammarsButFailsVnu() throws Exception {
        Path fx = Path.of("src/test/resources/fixtures/xhtml/mojibake.xhtml");
        Xml.hardenedBuilder().parse(fx.toFile());                       // stage 6 passes
        assertEquals(List.of(), JingGate.validate(JingGate.XHTML5_RNC, fx)); // stage 7 passes
        assertFalse(VnuGate.check(fx).isEmpty(), "only the sequenced vnu gate catches C1 controls");
    }
    @Test void cleanXhtmlPassesVnu() throws Exception {
        assertEquals(List.of(), VnuGate.check(Path.of("src/test/resources/fixtures/xhtml/minimal-valid.xhtml")));
    }
}
```
Run: `mvn -q test -Dtest=RenderAndGatesTest` — Expected: FAIL.

- [ ] **Step 3: Implement**

`DocbookRenderer.java`:
```java
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
        } catch (Exception e) { throw new IllegalStateException(e); }
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
```

`VnuGate.java`:
```java
package io.github.metavacua.pipeline;

import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

public final class VnuGate {
    private static final Path VNU = Path.of("target/tools/vnu.jar");

    /** Sequenced final gate: caller runs this ONLY after stages 6 and 7 pass.
     *  Findings are returned verbatim so the census carries the why/how. */
    public static List<String> check(Path xhtml) {
        try {
            var pb = new ProcessBuilder("java", "-cp", VNU.toString(),
                "nu.validator.client.SimpleCommandLineValidator", "--xml", xhtml.toString());
            pb.redirectErrorStream(true);
            Process p = pb.start();
            var out = new String(p.getInputStream().readAllBytes());
            int code = p.waitFor();
            var findings = new ArrayList<String>();
            if (code != 0) out.lines().filter(l -> !l.isBlank()).forEach(findings::add);
            return findings;
        } catch (Exception e) { throw new IllegalStateException(e); }
    }
    private VnuGate() {}
}
```

- [ ] **Step 4: Run and commit**

Run: `mvn -q generate-resources test -Dtest=RenderAndGatesTest` — Expected: PASS (3 tests; the mojibake test is the concrete proof of vnu's sequenced-gate purpose).
```bash
git add pom.xml src/main src/test
git commit -m "feat: xslTNG render + XHTML5 output gates; vnu as sequenced final gate proven on the C1-mojibake class"
```

---

### Task 8: Model documents (the correct-by-construction index + authored twin)

**Files:**
- Create: `src/main/docbook/index.xml`, `src/main/docbook/index.md`, `ModelDocumentTest.java`

**Interfaces:**
- Produces: the two authored sources every later task and the census engine treat as the base case. `index.xml` contains `<section xml:id="census">` whose content Task 10 replaces at render time.

- [ ] **Step 1: Write `index.xml`**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<article xmlns="http://docbook.org/ns/docbook"
         xmlns:dc="http://purl.org/dc/terms/" version="5.2">
  <info>
    <title>Legal Theory Corpus — Publishing Pipeline Health</title>
    <pubdate role="generated-from-git-first-commit">2026-08-03</pubdate>
    <biblioid class="uri" role="generated-from-path">https://github.com/metavacua/legal-theory/blob/main/src/main/docbook/index.xml</biblioid>
    <dc:type>Text</dc:type>
  </info>
  <section>
    <title>About this site</title>
    <para>This site is generated by a standards-gated publishing pipeline:
      Markdown and DocBook 5.2 sources are validated against the OASIS DocBook 5.2
      grammar, a pinned XHTML5 RELAX NG grammar, a project policy Schematron, and
      the Nu Html Checker, in sequence. Documents that pass every gate are
      published; documents that fail are cataloged below with their findings.
      This page is itself the correct-by-construction model: it passes every gate
      on every build, or the build fails.</para>
  </section>
  <section xml:id="census">
    <title>Corpus health census</title>
    <para>Census not yet generated.</para>
  </section>
</article>
```
Note: the authored `pubdate`/`biblioid` values above must equal what the manifest generator derives for this file's path — the census engine asserts that equality (Task 10), which is the forward gate's first real exercise. (`pubdate` = the date this file is first committed; set it to the actual commit date when executing this task.)

- [ ] **Step 2: Write `index.md` (the authored twin — body content mirrors index.xml)**

```markdown
---
title: Legal Theory Corpus — Publishing Pipeline Health
---
# About this site

This site is generated by a standards-gated publishing pipeline:
Markdown and DocBook 5.2 sources are validated against the OASIS DocBook 5.2
grammar, a pinned XHTML5 RELAX NG grammar, a project policy Schematron, and
the Nu Html Checker, in sequence. Documents that pass every gate are
published; documents that fail are cataloged below with their findings.
This page is itself the correct-by-construction model: it passes every gate
on every build, or the build fails.

# Corpus health census

Census not yet generated.
```
(The twin uses `#` headings where the XML uses sections — the required-agreement edge compares extracted *content*, not structure; Task 9 defines the oracle.)

- [ ] **Step 3: Failing test — the model passes every gate**

```java
package io.github.metavacua.pipeline;

import org.junit.jupiter.api.Test;
import java.nio.file.Path;
import java.util.List;
import static org.junit.jupiter.api.Assertions.*;

class ModelDocumentTest {
    @Test void modelIndexPassesEveryGate() throws Exception {
        Path src = Path.of("src/main/docbook/index.xml");
        var dom = Xml.hardenedBuilder().parse(src.toFile());                 // stage 1/6 analogue
        assertEquals(List.of(), JingGate.validate(JingGate.DOCBOOK_RNC, src)); // stage 3
        assertEquals(List.of(), SchematronGate.check(dom));                  // stage 4
        Path out = Path.of("target/test-render/index.xhtml");
        DocbookRenderer.render(src, out);                                    // stage 5
        Xml.hardenedBuilder().parse(out.toFile());                           // stage 6
        assertEquals(List.of(), JingGate.validate(JingGate.XHTML5_RNC, out)); // stage 7
        assertEquals(List.of(), VnuGate.check(out));                         // stage 8
    }
}
```
Run: `mvn -q generate-resources test -Dtest=ModelDocumentTest` — Expected: PASS directly if Tasks 2–7 are correct; any failure here is a pipeline defect to fix before proceeding (this test is the continuously-enforced exemplar).

- [ ] **Step 4: Commit**

```bash
git add src/main/docbook src/test
git commit -m "feat: correct-by-construction model index (authored DocBook + Markdown twin) enforced through every gate"
```

---

### Task 9: Content-preservation comparator + triangle base case

**Files:**
- Create: `src/main/resources/xslt/extract-content.xsl`, `ContentComparator.java`, `TriangleBaseCaseTest.java`

**Interfaces:**
- Produces: `record Extraction(List<String> textLines, Set<String> links)`; `ContentComparator.extract(Document, Vocabulary v) -> Extraction` where `enum Vocabulary { XHTML, DOCBOOK }`; `ContentComparator.diff(Extraction a, Extraction b) -> List<String>` (empty = agree).

- [ ] **Step 1: Write `extract-content.xsl`**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="3.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:h="http://www.w3.org/1999/xhtml"
    xmlns:db="http://docbook.org/ns/docbook"
    xmlns:xlink="http://www.w3.org/1999/xlink"
    exclude-result-prefixes="#all">
  <xsl:output method="text"/>
  <xsl:param name="mode" as="xs:string" required="yes" xmlns:xs="http://www.w3.org/2001/XMLSchema"/>

  <!-- CALIBRATION POINT (the one permitted adjustment, locked by the base-case
       test): furniture excluded from xslTNG-rendered XHTML. -->
  <xsl:variable name="xhtml-scope"
      select="if (//h:main) then //h:main else //h:body"/>

  <xsl:template match="/">
    <xsl:choose>
      <xsl:when test="$mode eq 'xhtml'">
        <xsl:for-each select="$xhtml-scope//text()[normalize-space()]
            [not(ancestor::h:nav or ancestor::h:header or ancestor::h:footer
                 or ancestor::h:script or ancestor::h:style)]">
          <xsl:value-of select="normalize-space(.)"/><xsl:text>&#10;</xsl:text>
        </xsl:for-each>
        <xsl:text>===LINKS===&#10;</xsl:text>
        <xsl:for-each select="distinct-values($xhtml-scope//h:a/@href)">
          <xsl:sort/><xsl:value-of select="."/><xsl:text>&#10;</xsl:text>
        </xsl:for-each>
      </xsl:when>
      <xsl:otherwise> <!-- docbook: title + body, excluding generated info fields -->
        <xsl:for-each select="(//db:info/db:title | //db:article/(* except db:info))
            //text()[normalize-space()] | //db:info/db:title/text()[normalize-space()]">
          <xsl:value-of select="normalize-space(.)"/><xsl:text>&#10;</xsl:text>
        </xsl:for-each>
        <xsl:text>===LINKS===&#10;</xsl:text>
        <xsl:for-each select="distinct-values(//db:link/@xlink:href)">
          <xsl:sort/><xsl:value-of select="."/><xsl:text>&#10;</xsl:text>
        </xsl:for-each>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>
</xsl:stylesheet>
```

- [ ] **Step 2: Implement `ContentComparator`**

```java
package io.github.metavacua.pipeline;

import net.sf.saxon.s9api.*;
import org.w3c.dom.Document;
import javax.xml.transform.dom.DOMSource;
import java.io.StringWriter;
import java.nio.file.Path;
import java.util.*;

public final class ContentComparator {
    public enum Vocabulary { XHTML, DOCBOOK }
    public record Extraction(List<String> textLines, Set<String> links) {}

    private static volatile XsltExecutable cached;

    public static Extraction extract(Document doc, Vocabulary v) {
        try {
            if (cached == null)
                cached = XsltPipeline.compile(Path.of("src/main/resources/xslt/extract-content.xsl"));
            var t = cached.load30();
            t.setStylesheetParameters(Map.of(new QName("mode"),
                new XdmAtomicValue(v == Vocabulary.XHTML ? "xhtml" : "docbook")));
            var sw = new StringWriter();
            var ser = XsltPipeline.SAXON.newSerializer(sw);
            t.applyTemplates(XsltPipeline.SAXON.newDocumentBuilder().build(new DOMSource(doc)), ser);
            String[] parts = sw.toString().split("===LINKS===\n", 2);
            List<String> lines = parts[0].lines().filter(s -> !s.isBlank()).toList();
            Set<String> links = parts.length > 1
                ? new TreeSet<>(parts[1].lines().filter(s -> !s.isBlank()).toList())
                : Set.of();
            return new Extraction(lines, links);
        } catch (Exception e) { throw new IllegalStateException(e); }
    }

    public static List<String> diff(Extraction a, Extraction b) {
        var out = new ArrayList<String>();
        if (!String.join("\n", a.textLines()).equals(String.join("\n", b.textLines())))
            out.add("text-sequence divergence: " + firstDivergence(a.textLines(), b.textLines()));
        if (!a.links().equals(b.links())) {
            var onlyA = new TreeSet<>(a.links()); onlyA.removeAll(b.links());
            var onlyB = new TreeSet<>(b.links()); onlyB.removeAll(a.links());
            out.add("link-set divergence: onlyA=" + onlyA + " onlyB=" + onlyB);
        }
        return out;
    }
    private static String firstDivergence(List<String> a, List<String> b) {
        for (int i = 0; i < Math.min(a.size(), b.size()); i++)
            if (!a.get(i).equals(b.get(i))) return "line " + i + ": '" + a.get(i) + "' vs '" + b.get(i) + "'";
        return "length " + a.size() + " vs " + b.size();
    }
    private ContentComparator() {}
}
```

- [ ] **Step 3: The three base-case edge tests**

```java
package io.github.metavacua.pipeline;

import net.sf.saxon.s9api.QName;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import org.w3c.dom.Document;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;
import static io.github.metavacua.pipeline.ContentComparator.Vocabulary.*;
import static org.junit.jupiter.api.Assertions.*;

class TriangleBaseCaseTest {
    static Document mdXhtml, mdDocbook, authoredDocbook, renderOfAuthored, renderOfGenerated;

    @BeforeAll static void pipeline() throws Exception {
        var x = MarkdownToXhtml.convert(Files.readString(Path.of("src/main/docbook/index.md")));
        mdXhtml = x.dom();                                                    // P3
        var manifest = Files.createTempFile("m", ".xml");
        var entries = ManifestGenerator.generate(Constants.REPO_ROOT,
            List.of(Path.of("src/main/docbook/index.md")));
        ManifestGenerator.writeManifest(entries, manifest);
        var xsl = XsltPipeline.compile(Path.of("src/main/resources/xslt/xhtml-to-docbook.xsl"));
        mdDocbook = XsltPipeline.apply(xsl, mdXhtml, Map.of(                  // P1
            new QName("authored-title"), x.frontMatterTitle(),
            new QName("source-path"), "src/main/docbook/index.md",
            new QName("manifest-uri"), manifest.toUri().toString()));
        authoredDocbook = Xml.hardenedBuilder().parse("src/main/docbook/index.xml");
        Path g = Path.of("target/test-triangle/generated.xml");
        Files.createDirectories(g.getParent());
        Files.writeString(g, Xml.serialize(mdDocbook));
        Path r1 = Path.of("target/test-triangle/authored.xhtml");
        Path r2 = Path.of("target/test-triangle/generated.xhtml");
        DocbookRenderer.render(Path.of("src/main/docbook/index.xml"), r1);    // P2(authored)
        DocbookRenderer.render(g, r2);                                        // P2(P1)
        renderOfAuthored = Xml.hardenedBuilder().parse(r1.toFile());
        renderOfGenerated = Xml.hardenedBuilder().parse(r2.toFile());
    }

    @Test void edge1_authoredTwinsAgree() { // P1(index.md) vs index.xml — required agreement
        assertEquals(List.of(), ContentComparator.diff(
            ContentComparator.extract(mdDocbook, DOCBOOK),
            ContentComparator.extract(authoredDocbook, DOCBOOK)));
    }
    @Test void edge2_standardTriangle() {   // P3 vs P2(P1)
        assertEquals(List.of(), ContentComparator.diff(
            ContentComparator.extract(mdXhtml, XHTML),
            ContentComparator.extract(renderOfGenerated, XHTML)));
    }
    @Test void edge3_renderPathsAgree() {   // P2(authored) vs P2(P1)
        assertEquals(List.of(), ContentComparator.diff(
            ContentComparator.extract(renderOfAuthored, XHTML),
            ContentComparator.extract(renderOfGenerated, XHTML)));
    }
}
```

- [ ] **Step 4: Calibrate, run, commit**

Run: `mvn -q generate-resources test -Dtest=TriangleBaseCaseTest`
First run will surface xslTNG furniture (TOC text, section numbers) in edge2/edge3 diffs. **The only permitted fixes are (a) the `$xhtml-scope` variable and the ancestor-exclusion predicate in `extract-content.xsl`, (b) xslTNG stylesheet parameters suppressing furniture on render (e.g. disabling the auto-TOC for articles). Never adjust the assertion to tolerate divergence.** Iterate until all three edges pass; the test then locks the calibration.
Expected final: PASS (3 tests).
```bash
git add src/main src/test
git commit -m "feat: content-preservation oracle + triangle proven on the fully-authored base case (3 edges, calibration locked)"
```

---

### Task 10: Census engine, audit checks, partition, health page

**Files:**
- Create: `AuditChecks.java`, `CensusEngine.java`, `src/main/resources/xslt/census-to-docbook.xsl`, `inject-census.xsl`, `sitemap.xsl`, `CensusEngineTest.java`, `AuditChecksTest.java`
- Create: `src/test/resources/fixtures/md/workscited.md`
- Modify: `pom.xml` (exec-maven-plugin: `census` execution bound to `verify`)

**Interfaces:**
- Produces: `CensusEngine.main(String[])` — full corpus run: manifest → per-document stages → `target/census/census.xml` → partition to `target/site/**.xhtml` → health-merged index render → `target/site/sitemap.xml`. `AuditChecks.titleClass(XhtmlResult) -> String` (`front-matter|h1-first|h2-first|h3-first|h4-first|h5-first|h6-first|headingless`), `AuditChecks.biblioRegion(Document docbook) -> Optional<Integer>` (entry count), `AuditChecks.linkStats(Document docbook) -> int[]{with,without}`, `AuditChecks.c1Count(String text) -> int`.
- Census XML shape (consumed by `census-to-docbook.xsl` and tests):
```xml
<census generated="ISO-INSTANT" total="N" published="M">
  <doc path="docs/…md" published="false" titleClass="h1-first">
    <gate id="wf-fragment" status="pass"/>
    <gate id="docbook-rng" status="pass"/>
    <gate id="policy" status="fail"><message>info/title must be non-empty…</message></gate>
    <gate id="render" status="skipped"/> <gate id="wf-out" status="skipped"/>
    <gate id="xhtml5-rng" status="skipped"/> <gate id="vnu" status="skipped"/>
    <check id="biblio-region" present="true" count="66"/>
    <check id="link-stats" with="59" without="7"/>
    <check id="first-heading-level" value="3"/>
    <check id="date-provenance" value="generated-from-git-first-commit" date="2026-07-01"/>
    <check id="c1-controls" value="0"/>
  </doc>
</census>
```

- [ ] **Step 1: Fixture + failing audit tests**

`fixtures/md/workscited.md`:
```markdown
---
title: Fixture With Bibliography
---
# A Document

Body text.

#### **Works cited**

1.  We are working on developing a comprehensive rese...
2.  Real Reference - Publisher, accessed September 2, 2025, <https://example.com/ref>
```

`AuditChecksTest.java`:
```java
package io.github.metavacua.pipeline;

import net.sf.saxon.s9api.QName;
import org.junit.jupiter.api.Test;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Map;
import static org.junit.jupiter.api.Assertions.*;

class AuditChecksTest {
    @Test void titleClasses() throws Exception {
        assertEquals("front-matter", AuditChecks.titleClass(
            MarkdownToXhtml.convert("---\ntitle: T\n---\n# H\n")));
        assertEquals("h1-first", AuditChecks.titleClass(MarkdownToXhtml.convert("# H\n")));
        assertEquals("h3-first", AuditChecks.titleClass(MarkdownToXhtml.convert("### H\n")));
        assertEquals("headingless", AuditChecks.titleClass(MarkdownToXhtml.convert("just prose\n")));
    }
    @Test void biblioRegionDiscernedByExactContainerTitleOnly() throws Exception {
        var x = MarkdownToXhtml.convert(Files.readString(
            Path.of("src/test/resources/fixtures/md/workscited.md")));
        var manifest = Files.createTempFile("m", ".xml");
        Files.writeString(manifest, "<manifest><doc path=\"fx.md\" pubdate=\"2026-07-01\" biblioid=\""
            + Constants.CANONICAL_BASE + "fx.md\"/></manifest>");
        var xsl = XsltPipeline.compile(Path.of("src/main/resources/xslt/xhtml-to-docbook.xsl"));
        var db = XsltPipeline.apply(xsl, x.dom(), Map.of(
            new QName("authored-title"), x.frontMatterTitle(),
            new QName("source-path"), "fx.md",
            new QName("manifest-uri"), manifest.toUri().toString()));
        assertEquals(2, AuditChecks.biblioRegion(db).orElseThrow());
        assertArrayEquals(new int[]{1, 1}, AuditChecks.linkStats(db));
        // near-miss control: a section titled "Reference Guide: X" must NOT count
        var x2 = MarkdownToXhtml.convert("# Reference Guide: Contracts\n\n1. item\n");
        var db2 = XsltPipeline.apply(xsl, x2.dom(), Map.of(
            new QName("authored-title"), "T",
            new QName("source-path"), "fx.md",
            new QName("manifest-uri"), manifest.toUri().toString()));
        assertTrue(AuditChecks.biblioRegion(db2).isEmpty());
    }
    @Test void c1Detection() {
        assertEquals(1, AuditChecks.c1Count("bad\u0097char"));
        assertEquals(0, AuditChecks.c1Count("clean"));
    }
}
```
Run: `mvn -q test -Dtest=AuditChecksTest` — Expected: FAIL.

- [ ] **Step 2: Implement `AuditChecks`** (all XPath via Saxon — XPath 3.1, never the JDK 1.0 engine)

```java
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
```
Run: `mvn -q test -Dtest=AuditChecksTest` — Expected: PASS.

- [ ] **Step 3: Census rendering stylesheets**

`census-to-docbook.xsl` (census.xml → a DocBook section body):
```xml
<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="3.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns="http://docbook.org/ns/docbook" exclude-result-prefixes="#all">
  <xsl:output method="xml"/>
  <xsl:template match="/census">
    <para>Generated <xsl:value-of select="@generated"/>. Documents:
      <xsl:value-of select="@total"/>; published: <xsl:value-of select="@published"/>.</para>
    <informaltable>
      <thead><tr><th>Document</th><th>Published</th><th>Title class</th>
        <th>Bibliography region</th><th>First failing gate</th></tr></thead>
      <tbody>
        <xsl:for-each select="doc">
          <tr>
            <td><xsl:value-of select="@path"/></td>
            <td><xsl:value-of select="@published"/></td>
            <td><xsl:value-of select="@titleClass"/></td>
            <td><xsl:value-of select="if (check[@id='biblio-region']/@present eq 'true')
                 then 'yes (' || check[@id='biblio-region']/@count || ')' else 'no'"/></td>
            <td><xsl:value-of select="(gate[@status='fail'])[1]/(@id || ': ' || message)"/></td>
          </tr>
        </xsl:for-each>
      </tbody>
    </informaltable>
  </xsl:template>
</xsl:stylesheet>
```

`inject-census.xsl` (identity over index.xml, replacing the census placeholder):
```xml
<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="3.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:db="http://docbook.org/ns/docbook" exclude-result-prefixes="#all">
  <xsl:param name="census-fragment-uri" as="xs:string" required="yes"
             xmlns:xs="http://www.w3.org/2001/XMLSchema"/>
  <xsl:mode on-no-match="shallow-copy"/>
  <xsl:template match="db:section[@xml:id='census']/db:para">
    <xsl:copy-of select="doc($census-fragment-uri)/node()"/>
  </xsl:template>
</xsl:stylesheet>
```

`sitemap.xsl` (census.xml → sitemap of published docs):
```xml
<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="3.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" exclude-result-prefixes="#all">
  <xsl:output method="xml" indent="yes"/>
  <xsl:param name="site-base" select="'https://metavacua.github.io/legal-theory/'"/>
  <xsl:template match="/census">
    <urlset>
      <url><loc><xsl:value-of select="$site-base"/></loc></url>
      <xsl:for-each select="doc[@published='true']">
        <url><loc><xsl:value-of select="$site-base ||
          replace(replace(@path, '^docs/', ''), '\.md$', '.xhtml')"/></loc></url>
      </xsl:for-each>
    </urlset>
  </xsl:template>
</xsl:stylesheet>
```

- [ ] **Step 4: Implement `CensusEngine`**

```java
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
                .filter(p -> Constants.CORPUS_EXCLUDES.stream()
                    .noneMatch(x -> root.relativize(p).toString().replace('\\','/').startsWith(x)))
                .sorted().toList();
        }
        for (Path p : corpus) { // manifest attribute-safety precondition
            String rel = root.relativize(p).toString();
            if (rel.contains("\"") || rel.contains("&"))
                throw new IllegalStateException("unsafe path for XML attributes: " + rel);
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
                    try { Xml.hardenedBuilder().parse(rendered.toFile());      // stage 6
                          gates.add(new GateResult("wf-out", "pass", null)); }
                    catch (Exception e) { gates.add(new GateResult("wf-out", "fail", e.getMessage())); pass = false; }
                    if (pass) pass &= gate(gates, "xhtml5-rng",                // stage 7
                        JingGate.validate(JingGate.XHTML5_RNC, rendered));
                    if (pass) pass &= gate(gates, "vnu", VnuGate.check(rendered)); // stage 8 (sequenced)
                    else skip(gates, "vnu");
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
        Document censusDoc = Xml.hardenedBuilder().parse(census.toFile());
        Path frag = root.resolve("target/census/census-fragment.xml");
        Files.writeString(frag, Xml.serialize(XsltPipeline.apply(toDb, censusDoc, Map.of())));
        var inject = XsltPipeline.compile(root.resolve("src/main/resources/xslt/inject-census.xsl"));
        Document index = Xml.hardenedBuilder().parse(root.resolve("src/main/docbook/index.xml").toFile());
        Document merged = XsltPipeline.apply(inject, index,
            Map.of(new QName("census-fragment-uri"), frag.toUri().toString()));
        Path mergedPath = root.resolve("target/census/index-merged.xml");
        Files.writeString(mergedPath, Xml.serialize(merged));
        // The merged model must itself pass the gates it demands of others:
        require(JingGate.validate(JingGate.DOCBOOK_RNC, mergedPath), "model index: docbook-rng");
        require(SchematronGate.check(merged), "model index: policy");
        Path indexOut = site.resolve("index.xhtml");
        DocbookRenderer.render(mergedPath, indexOut);
        Xml.hardenedBuilder().parse(indexOut.toFile());
        require(JingGate.validate(JingGate.XHTML5_RNC, indexOut), "model index: xhtml5-rng");
        require(VnuGate.check(indexOut), "model index: vnu");
        DocbookRenderer.stageResources(site);
        var sitemapXsl = XsltPipeline.compile(root.resolve("src/main/resources/xslt/sitemap.xsl"));
        Files.writeString(site.resolve("sitemap.xml"),
            Xml.serialize(XsltPipeline.apply(sitemapXsl, censusDoc, Map.of())));
        System.out.println("census: " + corpus.size() + " docs, " + published + " published");
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
```

- [ ] **Step 5: Bind to `verify` + engine tests (incl. the RED marker)**

POM (exec-maven-plugin, in `<build><plugins>`):
```xml
<plugin>
  <groupId>org.codehaus.mojo</groupId><artifactId>exec-maven-plugin</artifactId><version>3.5.0</version>
  <executions><execution>
    <id>census</id><phase>verify</phase><goals><goal>java</goal></goals>
    <configuration><mainClass>io.github.metavacua.pipeline.CensusEngine</mainClass></configuration>
  </execution></executions>
</plugin>
```

`CensusEngineTest.java`:
```java
package io.github.metavacua.pipeline;

import org.junit.jupiter.api.Disabled;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class CensusEngineTest {
    @Test void censusDiscernsPseudoBibliographies() throws Exception {
        // fixture from Task 10 Step 1 has a Works cited region with 2 items
        var x = MarkdownToXhtml.convert(java.nio.file.Files.readString(
            java.nio.file.Path.of("src/test/resources/fixtures/md/workscited.md")));
        assertEquals("front-matter", AuditChecks.titleClass(x));
        // full-engine behavior is exercised by the corpus run in Task 11;
        // this test pins the discernment inputs the census row is built from.
    }
    @Disabled("GREEN target: bibliography promotion — next increment")
    @Test void worksCitedSectionsPromoteToProperBibliography() throws Exception {
        // GREEN shape this pipeline does NOT yet produce (and must not fake):
        // the discerned section becomes <bibliography> with <biblioentry> children
        // constructed only from typed structure. This test defines done-ness for
        // the promotion increment; it stays visible as SKIPPED in every report.
        var xsl = XsltPipeline.compile(java.nio.file.Path.of("src/main/resources/xslt/xhtml-to-docbook.xsl"));
        var x = MarkdownToXhtml.convert(java.nio.file.Files.readString(
            java.nio.file.Path.of("src/test/resources/fixtures/md/workscited.md")));
        var db = XsltPipeline.apply(xsl, x.dom(), java.util.Map.of(
            new net.sf.saxon.s9api.QName("authored-title"), "T",
            new net.sf.saxon.s9api.QName("source-path"), "fx.md",
            new net.sf.saxon.s9api.QName("manifest-uri"), "about:invalid"));
        assertTrue(Xml.serialize(db).contains("<bibliography"));
    }
}
```
Run: `mvn -q test -Dtest='CensusEngineTest,AuditChecksTest'` — Expected: 3 pass, 1 **skipped** (the RED marker, visible in the report).

- [ ] **Step 6: Commit**

```bash
git add pom.xml src/main src/test
git commit -m "feat: census engine — per-document gates, partition, health-merged model index, sitemap; RED marker pins the bibliography-promotion GREEN target"
```

---

### Task 11: Full local corpus run

**Files:** none created (execution + recorded results; fixes only for *pipeline* defects it surfaces).

- [ ] **Step 1: Run the whole build**

Run: `mvn verify`
Expected: `BUILD SUCCESS`; console line `census: 123 docs, 0 published` (or the current corpus count; legacy documents fail the policy gate on title-absence by design — those are **document** defects, correctly censused, not build failures). Any `pipeline-error` gate entries or engine exceptions are **pipeline** defects: fix them (with a regression test) before proceeding. Distinguishing rule: a failure recorded *in* the census is the instrument working; a failure *of* the census run is a bug.

- [ ] **Step 2: Sanity-check the artifacts**

```bash
ls target/site/index.xhtml target/site/resources target/site/sitemap.xml target/census/census.xml
python3 - <<'EOF'
import xml.dom.minidom, collections
d = xml.dom.minidom.parse('target/census/census.xml')
docs = d.getElementsByTagName('doc')
tc = collections.Counter(x.getAttribute('titleClass') for x in docs)
bib = sum(1 for x in docs for c in x.getElementsByTagName('check')
          if c.getAttribute('id')=='biblio-region' and c.getAttribute('present')=='true')
print('total', len(docs), '| titleClass', dict(tc), '| biblio-regions', bib)
EOF
```
Expected (descriptive baselines, recorded not asserted): total 123; titleClass ≈ {h1-first: 98, h2-first: 3, h3-first: 21, headingless: 1}; biblio-regions ≈ 88. Investigate (as potential pipeline defects) only *large* deviations; record the actual numbers in the commit message.

- [ ] **Step 3: Commit**

```bash
git add -A && git status --porcelain   # expect ONLY intended files; target/ is ignored
git commit --allow-empty -m "chore: first full corpus run — census recorded (N docs, title classes, biblio regions; 0 published as designed)"
```

---

### Task 12: CI workflow + Pages deployment + PR

**Files:**
- Create: `.github/workflows/build-and-deploy.yml`, `PandocCrossCheck.java`

**Interfaces:**
- Consumes: everything; the deploy publishes `target/site`.
- Note: the `github-pages` environment already lists this branch in its deployment branch policy (added during design).

- [ ] **Step 1: Live-verify action majors** (rule from Global Constraints)

```bash
for a in checkout setup-java upload-pages-artifact deploy-pages; do
  echo -n "actions/$a -> "; git ls-remote --tags https://github.com/actions/$a 'v*' \
    | awk -F/ '{print $NF}' | grep -E '^v[0-9]+$' | sort -V | tail -1
done
```
Expected (last verified): checkout v6, setup-java v5, upload-pages-artifact v4, deploy-pages v4 — use whatever prints.

- [ ] **Step 2: `PandocCrossCheck.java`** (informational leg driver; reuses the comparator)

```java
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
        int rncFail = 0, diverged = 0;
        for (Path src : corpus) {
            Path out = Files.createTempFile("pandoc", ".xml");
            var p = new ProcessBuilder("pandoc", "-f", "markdown", "-t", "docbook5", "-s",
                src.toString(), "-o", out.toString()).inheritIO().start();
            if (p.waitFor() != 0) { rncFail++; continue; }
            if (!JingGate.validate(JingGate.DOCBOOK_RNC, out).isEmpty()) { rncFail++; continue; }
            Path ours = root.resolve("target/docbook/"
                + root.relativize(src).toString().replaceAll("\\.md$", ".xml"));
            if (!Files.exists(ours)) continue;
            var a = ContentComparator.extract(Xml.hardenedBuilder().parse(out.toFile()),
                ContentComparator.Vocabulary.DOCBOOK);
            var b = ContentComparator.extract(Xml.hardenedBuilder().parse(ours.toFile()),
                ContentComparator.Vocabulary.DOCBOOK);
            var diff = ContentComparator.diff(a, b);
            if (!diff.isEmpty()) { diverged++;
                System.out.println("DIVERGES " + src + " :: " + diff.get(0)); }
        }
        System.out.println("pandoc cross-check: " + corpus.size() + " docs, "
            + rncFail + " pandoc-side failures, " + diverged + " content divergences");
    }
    private PandocCrossCheck() {}
}
```

- [ ] **Step 3: Write `.github/workflows/build-and-deploy.yml`**

```yaml
name: Build & Deploy

on:
  push:
    branches: [claude/java-maven-publishing-pipeline, main]
  pull_request:
    branches: [main]

permissions:
  contents: read

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  required:
    # Required-agreement matrix: both jing implementations must agree.
    strategy:
      fail-fast: false
      matrix:
        jing-profile: [jing-current, jing-2009]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
        with:
          fetch-depth: 0        # MANDATORY: manifest generator hard-fails on shallow clones
      - uses: actions/setup-java@v5
        with: { distribution: temurin, java-version: '25', cache: maven }
      - run: mvn -B -P${{ matrix.jing-profile }} verify

  informational:
    # Forward-compatibility signal only; never blocks.
    continue-on-error: true
    strategy:
      fail-fast: false
      matrix:
        include:
          - { jdk: '26', saxon: '' }
          - { jdk: '25', saxon: '13.0' }
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
        with: { fetch-depth: 0 }
      - uses: actions/setup-java@v5
        with: { distribution: temurin, java-version: "${{ matrix.jdk }}", cache: maven }
      - run: mvn -B ${{ matrix.saxon != '' && format('-Dsaxon.version={0}', matrix.saxon) || '' }} verify

  pandoc-cross-check:
    # Independent (non-commonmark) parse of the same corpus; informational.
    continue-on-error: true
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
        with: { fetch-depth: 0 }
      - uses: actions/setup-java@v5
        with: { distribution: temurin, java-version: '25', cache: maven }
      - run: sudo apt-get update && sudo apt-get install -y pandoc
      - run: mvn -B verify
      - run: mvn -B exec:java -Dexec.mainClass=io.github.metavacua.pipeline.PandocCrossCheck

  deploy:
    needs: [required]
    if: github.event_name == 'push'
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pages: write
      id-token: write
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - uses: actions/checkout@v6
        with: { fetch-depth: 0 }
      - uses: actions/setup-java@v5
        with: { distribution: temurin, java-version: '25', cache: maven }
      - run: mvn -B verify
      - uses: actions/upload-pages-artifact@v4
        with:
          path: target/site
      - id: deployment
        uses: actions/deploy-pages@v4
```

- [ ] **Step 4: Push and open the PR**

```bash
git add .github/workflows/build-and-deploy.yml src/main/java/io/github/metavacua/pipeline/PandocCrossCheck.java
git commit -m "ci: required jing-agreement matrix, informational JDK/Saxon/pandoc legs, Pages deploy of the health site"
git push
gh pr create --base main --title "Java/Maven publishing pipeline: standards-gated corpus build, audit census, Pages health site" \
  --body "Implements docs/superpowers/specs/2026-08-03-java-maven-publishing-pipeline-design.md. See spec for gates, census, partition, and the correct-by-construction model index. Initial deployment is the health page (0/123 legacy documents publishable by design — title absence is universal and censused).

🤖 Generated with [Claude Code](https://claude.com/claude-code)"
```

- [ ] **Step 5: Verify the acceptance criterion — green matrix AND live visual check**

```bash
gh run list --workflow=build-and-deploy.yml --limit 5   # watch until required matrix green
curl -sI https://metavacua.github.io/legal-theory/ | grep -Ei 'HTTP|content-type'
curl -s  https://metavacua.github.io/legal-theory/ | grep -o '<title>[^<]*</title>'
curl -s  https://metavacua.github.io/legal-theory/sitemap.xml | head -5
```
Expected: required matrix (both jing legs) green; root serves `application/xhtml+xml` with the model index's title; the census table is present in the page body (fetch and grep for `Corpus health census`). Record the run URL and the live-check output in the PR as the acceptance evidence. Local success alone does not satisfy the spec.

---

## Self-Review (performed while writing; verified)

- **Spec coverage:** purpose/census (T10–11), standards & gates incl. sequenced vnu (T2, T6, T7, T10), metadata generation + refusals (T3–T6), model index + twin + triangle base case (T8–T9), partition + health page + sitemap (T10), dependencies/currency (T1 Step 1, T12 Step 1), CI matrices + fetch-depth + deploy + acceptance evidence (T12), RED marker (T10), corpus baselines descriptive-only (T11). Deliberately not in any task, per spec out-of-scope: bibliography promotion, title curation of the 123, atomization, front-matter fields beyond `title:`.
- **Placeholders:** the two `REPLACED_IN_TASK_2` / recorded-path markers are explicit instructions with concrete commands producing the value, not deferrals; both contingencies (schema vintage, xslTNG resources) carry deterministic decision rules and concrete fallback commands.
- **Type consistency:** `XhtmlResult(dom, serialized, frontMatterTitle)`, `ManifestEntry(path, pubdate, biblioid)`, `JingGate.validate -> List<String>`, `SchematronGate.check -> List<String>`, `VnuGate.check -> List<String>`, `ContentComparator.extract/diff`, census XML attribute names — cross-checked across Tasks 3–12.

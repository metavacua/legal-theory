"""Validates DocBook 5.2 XML against the real, official RELAX NG grammar
-- but against the fully XIncluded, reader-facing MERGED content, not
just the literal, unresolved <xi:include> placeholder elements a shell
article's own source contains. Also validates XIncluded fragment/
metadata/boilerplate files standalone (root elements "section", "info",
"legalnotice"), which DocBook 5.2's own grammar exports as valid
top-level start patterns even though they are never a whole document by
themselves in this corpus's own convention.

Why this exists: .github/workflows/build-corpus.yml's previous jing
invocation ran `jing -c docbookxi.rnc "$xml"` directly against each
shell article's own, unresolved source file. Confirmed during design
that docbookxi.rnc -- deliberately, by design, per its own "DocBook
XInclude V5.2" header comment -- treats a literal <xi:include> element
as valid content almost everywhere, precisely so un-merged, modular
source can be validated before assembly. That means a raw, unresolved
shell article passing jing proves only that its OWN literal content
(mostly a handful of <xi:include> placeholders) is well-shaped -- not
that the actual reader-facing document produced once those includes
are substituted in is valid DocBook at all. Confirmed live during
design: a shell article whose included fragment is missing its
required <title> passes jing when jing is run on the raw source, and
correctly fails once run against the resolved, merged content instead.

Separately confirmed during design: on this corpus's own CI toolchain
(Debian/Ubuntu's `jing` package), raw `jing` on an unresolved shell
ALSO happens to already resolve <xi:include> internally, via a
Xerces-specific JVM system property Debian's own /usr/bin/jing wrapper
script sets (-Dorg.apache.xerces.xni.parser.XMLParserConfiguration=
org.apache.xerces.parsers.XIncludeParserConfiguration) -- not something
jing's own CLI or documentation exposes or promises (jing -c/-e/-f/-i/-t
has no xinclude flag at all), and not something build-corpus.yml's own
jing invocation declares or relies on. This module resolves explicitly,
with xmllint, instead of depending on that undocumented packaging
side-effect, so this conformance gate keeps working even if a future
jing build stops setting that property.

Fragment files (root element "section") are independently checked
because build-corpus.yml's existing root-element filter skips every
non-"article" file outright -- so today, a section fragment's actual
content is never checked by any tool, at any point, unless (and until)
some shell article happens to XInclude it. DocBook 5.2's own RNG
grammar's `start =` production genuinely does list db.section (and
db.info, db.legalnotice) as valid, independent top-level start
elements -- confirmed by reading .cache/docbook-5.2/docbookxi.rnc's own
`start =` production, and empirically, by running jing directly against
one real, bare example of each shape from this corpus. Two other
non-"article" root shapes this corpus actually has -- "biblioentry" and
"authorgroup" -- are real DocBook content, but the grammar's `start =`
production does NOT list either: confirmed empirically, jing rejects a
bare <biblioentry>/<authorgroup> root, citing an exhaustive list of
permitted start elements that does not include either. Both are only
ever validated in context, via whichever shell article's resolved
<info> XIncludes them -- there is no fabricated standalone check for
either here; see classify()'s docstring.

See .superpowers/sdd/2026-07-29-resolved-content-docbook-validation.md
for the full research trail behind every claim above."""

import os
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from convert_to_docbook import DB_NS, fetch_docbook_schema  # noqa: E402


def resolve_xinclude(xml_path):
    """(resolved_xml_text, None) on success; (None, error_message) if
    xmllint's own XInclude resolution fails -- malformed XML, or a
    broken/missing xi:include target with no <xi:fallback>. A file
    with zero <xi:include> elements resolves to itself unchanged (a
    safe no-op), confirmed during design, which is what lets
    validate_resolved_document() run every root shape through the
    exact same resolve-then-validate path uniformly, with no
    special-casing for "this file happens not to include anything"."""
    result = subprocess.run(
        ["xmllint", "--xinclude", str(xml_path)],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        return None, result.stderr.strip()
    return result.stdout, None


def validate_grammar(resolved_text, schema_path, source_label):
    """[] if resolved_text is valid per schema_path, else jing's own
    error lines -- with the meaningless throwaway temp-file path jing
    was actually handed rewritten back to source_label, so a reported
    error points a reader at the real corpus file, not a /tmp path
    that won't exist by the time anyone reads the CI log. jing's own
    CLI only validates files, not stdin, so resolved_text is spilled
    to a temp file first, always cleaned up (success or error)."""
    fd, temp_path = tempfile.mkstemp(suffix=".xml")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(resolved_text)
        result = subprocess.run(
            ["jing", "-c", str(schema_path), temp_path],
            capture_output=True, text=True,
        )
    finally:
        os.unlink(temp_path)
    if result.returncode == 0:
        return []
    output = result.stdout.strip() or result.stderr.strip()
    return [line.replace(temp_path, str(source_label)) for line in output.splitlines()]


def validate_resolved_document(xml_path, schema_path):
    """[] if xml_path's fully-XIncluded content is valid DocBook 5.2
    per schema_path, else a nonempty list of human-readable error
    strings. This is the real conformance gate: it validates the
    MERGED, reader-facing content a shell article's own includes
    resolve to (or, for a fragment with no includes of its own, its
    own content unchanged) -- not just the literal <xi:include>
    placeholders a narrower check would only ever see."""
    resolved_text, error = resolve_xinclude(xml_path)
    if error is not None:
        return [f"{xml_path}: XInclude resolution failed: {error}"]
    return validate_grammar(resolved_text, schema_path, xml_path)


# Real DocBook content this corpus has (root elements "biblioentry",
# "authorgroup") that DocBook 5.2's own RNG grammar's `start =`
# production does not export as a standalone top-level start element
# -- confirmed empirically (see the module docstring). Not a gap in
# this checker: both are only ever valid nested inside a larger
# document, and are already reached and validated as part of resolving
# and validating whichever <article> shell XIncludes them.
_KNOWN_UNVALIDATABLE_STANDALONE = {
    (DB_NS, "biblioentry"),
    (DB_NS, "authorgroup"),
}


def root_element_info(xml_path):
    """(namespace_uri, local_name) for xml_path's own root element, or
    (None, None) if the file is too malformed to even find one. Reads
    the file directly with no XInclude resolution: in this corpus's
    own convention, the root element itself is never the target of an
    xi:include (every xi:include is a child of some already-concrete
    root), so this is always a cheap, accurate, resolution-free read."""
    try:
        tag = ET.parse(xml_path).getroot().tag
    except ET.ParseError:
        return None, None
    if tag.startswith("{"):
        ns, _, local = tag[1:].partition("}")
        return ns, local
    return "", tag


def classify(xml_path):
    """('validate', None) if xml_path should be run through
    validate_resolved_document(); ('skip', reason) with a nonempty,
    specific, human-readable reason otherwise. Defaults to 'validate'
    whenever in doubt -- an unparseable root, or any DocBook-namespaced
    root this function doesn't specifically know is exception-listed
    -- deliberately failing open toward validating rather than toward
    silently skipping, since a silent skip is exactly the shape of the
    original bug this module exists to close."""
    ns, local = root_element_info(xml_path)
    if (ns, local) in _KNOWN_UNVALIDATABLE_STANDALONE:
        return "skip", (
            f"<{local}> is real DocBook content, but DocBook 5.2's own "
            "RELAX NG grammar does not export it as a standalone "
            "top-level start element (confirmed empirically: jing "
            f"rejects a bare <{local}> root, citing a list of permitted "
            "start elements that does not include it) -- it is only "
            "validated in context, via the shell document that "
            "XIncludes it."
        )
    if ns == DB_NS or ns is None:
        return "validate", None
    return "skip", f"root element is not in the DocBook namespace (found {ns!r})"

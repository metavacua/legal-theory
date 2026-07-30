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

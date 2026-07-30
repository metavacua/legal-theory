"""Corpus-wide detection and conversion of raw, unconverted Markdown
inline-emphasis and pipe-table syntax that survived as literal text
content in DocBook XML -- the original markdown-to-DocBook conversion
for this subset of documents built correct DocBook *structure*
(<para>, <itemizedlist>, even <informaltable> in some cases) but never
ran that structure's own text through a real Markdown *inline*
parser, so "**bold**", "*italic*", and whole raw pipe-delimited
tables survive as literal text instead of <emphasis>/<informaltable>
markup. Confirmed live in the corpus's own checked-in generated HTML,
e.g. docs/court-record/theory/federal-constitutional/existing-doctrine/
first-amendment-landmark-cases-research.html (a literal "**" inside an
<h4>) and docs/court-record/matters/google-platform-misclassification/
evidence/potential-service-contracts-in-google.html (an entire table
rendered as raw pipe-and-asterisk text).

Both conversions delegate the actual Markdown parsing to pandoc (the
same tool convert_to_docbook.py already trusts for the same job)
rather than hand-rolling a Markdown emphasis/table parser: real
CommonMark emphasis resolution is a documented, non-trivial algorithm
(delimiter runs, flanking rules, nesting) that pandoc already
implements correctly -- confirmed against real corpus edge cases a
naive regex gets wrong: a 5-asterisk-run nested bold-inside-italic-
inside-bold case, and an academic citation title containing genuine,
non-emphasis footnote-style asterisks ("Schwartz* & Robert E.
Scott**") that must NOT be touched. See
.superpowers/sdd/2026-07-29-docbook-content-conformance.md for the
full design rationale."""

import argparse
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from convert_to_docbook import DB_NS, REPO_ROOT  # noqa: E402
from build_bibliography import _normalize_ws  # noqa: E402

"""Retags specific, known bare <emphasis> elements that wrap a cited
creative work's title to DocBook 5.2's actual purpose-built element
for that job, <citetitle> ("The title of a cited work", per the
RNG grammar's own annotation -- distinct from <emphasis>'s "Emphasized
text"). Scoped deliberately narrow: this corpus never uses <citetitle>
anywhere, wrapping cited-work titles in plain <emphasis> instead, but
fixing that corpus-wide would require reliably distinguishing "this
bare emphasis wraps a cited work's title" from every other legitimate
use of bare emphasis in ~900 documents -- out of scope here. This
fixes the one confirmed, concretely-identified file: 3 instances (two
"Harry Potter", one "Nineteen Eighty-Four") in
docs/papers/ai_and_ip/llm-database-theory/src/01-llm-database-theory/
04-the-basis-limitation-outputs-cannot-exceed-inputs.xml. The
role="bold" <emphasis> elements elsewhere in that same file are intro
labels ("Text (Cooper et al. 2025):"), not titles, and must not be
touched -- confirmed by only ever matching a completely bare
<emphasis> (zero attributes)."""

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from convert_to_docbook import DB_NS, REPO_ROOT  # noqa: E402

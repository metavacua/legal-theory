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


def convert_cited_titles(root, titles):
    """Converts every bare <emphasis> (zero attributes -- a
    role="bold"/role="strong"/anything-else emphasis is never a cited-
    work title in this corpus's usage and is never touched) whose exact
    full text matches one of titles into <citetitle>, in place. Returns
    the count converted."""
    converted = 0
    for el in root.iter(f"{{{DB_NS}}}emphasis"):
        if el.attrib:
            continue
        text = "".join(el.itertext())
        if text in titles:
            el.tag = f"{{{DB_NS}}}citetitle"
            converted += 1
    return converted


TARGET_FILE = (
    REPO_ROOT / "docs" / "papers" / "ai_and_ip" / "llm-database-theory" / "src"
    / "01-llm-database-theory" / "04-the-basis-limitation-outputs-cannot-exceed-inputs.xml"
)
KNOWN_CITED_TITLES = {"Harry Potter", "Nineteen Eighty-Four"}


def main(argv=None):
    tree = ET.parse(TARGET_FILE)
    root = tree.getroot()
    n = convert_cited_titles(root, KNOWN_CITED_TITLES)
    if n:
        ET.indent(tree, space="  ")
        tree.write(TARGET_FILE, encoding="unicode", xml_declaration=True)
    print(f"OK: converted {n} bare <emphasis> cited-work titles to <citetitle> in {TARGET_FILE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

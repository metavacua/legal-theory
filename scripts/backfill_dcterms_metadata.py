"""One-shot regeneration of every existing corpus .meta.xml through the
DCTERMS-complete write_metadata() (see
docs/superpowers/plans/2026-07-25-external-metadata-ontology-standardization.md,
Task 2). Every corpus .meta.xml is, today, nothing but the write_metadata()
boilerplate (a single dc:title plus one xi:include) -- so regenerating them
in place from their own existing title is lossless, not a guess."""

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from convert_to_docbook import REPO_ROOT, DC_NS, element_full_text, write_metadata  # noqa: E402

EXCLUDE_TOP_LEVEL = {"papers", "scripts"}


def find_corpus_meta_files():
    docs_dir = REPO_ROOT / "docs"
    for meta_path in sorted(docs_dir.rglob("*.meta.xml")):
        rel_parts = meta_path.resolve().relative_to(docs_dir).parts
        if rel_parts[0] in EXCLUDE_TOP_LEVEL:
            continue
        yield meta_path


def backfill(meta_path):
    root = ET.parse(meta_path).getroot()
    title_el = root.find(f"{{{DC_NS}}}title")
    title = element_full_text(title_el)
    write_metadata(meta_path, title)


def main(argv=None):
    count = 0
    for meta_path in find_corpus_meta_files():
        backfill(meta_path)
        count += 1
    print(f"OK: regenerated {count} .meta.xml files with dc:date/dc:identifier/dc:subject")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""One-shot corpus-wide migration to the native-DocBook metadata shape
(see docs/superpowers/specs/2026-07-25-docbook-native-corpus-standardization-design.md
and docs/superpowers/plans/2026-07-25-docbook-native-corpus-standardization-phase1.md).
For every corpus .meta.xml: regenerate it through the now-native
write_metadata(), reading the existing title from wherever it currently
lives (native <title> if already migrated, else the old dc:title), and
re-inserting any hand-authored <subtitle> that write_metadata() itself
does not emit. For every corpus content .xml: remove the now-invalid
sibling <title> element, since the title now lives inside <info>
(pulled in via the meta.xml's own xi:include).

Re-running is safe in the sense that it will not corrupt already-migrated
documents: title and subtitle are read back from the current file and
carried forward. It is NOT a no-op, though -- <pubdate> is always
recomputed from the content file's most recent git commit (see
convert_to_docbook.derive_date()), so re-running after committing this
script's own output will reflect that later commit date, same as any
other edit to a tracked file would."""

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from convert_to_docbook import REPO_ROOT, DB_NS, DC_NS, element_full_text, write_metadata  # noqa: E402

# convert_to_docbook registers db/xi/xlink at import time; register dc here too
# so insert_subtitle()'s ET round-trip serializes <dc:type> instead of an
# auto-generated ns0:type prefix.
ET.register_namespace("dc", DC_NS)

EXCLUDE_TOP_LEVEL = {"scripts"}


def find_corpus_meta_files():
    docs_dir = REPO_ROOT / "docs"
    for meta_path in sorted(docs_dir.rglob("*.meta.xml")):
        rel_parts = meta_path.resolve().relative_to(docs_dir).parts
        if rel_parts[0] in EXCLUDE_TOP_LEVEL:
            continue
        yield meta_path


def existing_title(meta_path):
    root = ET.parse(meta_path).getroot()
    native = root.find(f"{{{DB_NS}}}title")
    if native is not None:
        return element_full_text(native)
    old = root.find(f"{{{DC_NS}}}title")
    return element_full_text(old)


def existing_subtitle(meta_path):
    root = ET.parse(meta_path).getroot()
    subtitle = root.find(f"{{{DB_NS}}}subtitle")
    return element_full_text(subtitle) if subtitle is not None else None


def insert_subtitle(meta_path, subtitle_text):
    """write_metadata() does not emit <subtitle> -- it's not part of the
    generated shape, only a hand-authored addition some documents carry.
    Re-insert it right after <title>, the position DocBook's <info>
    content model requires."""
    tree = ET.parse(meta_path)
    root = tree.getroot()
    title_el = root.find(f"{{{DB_NS}}}title")
    title_index = list(root).index(title_el)
    subtitle_el = ET.Element(f"{{{DB_NS}}}subtitle")
    subtitle_el.text = subtitle_text
    root.insert(title_index + 1, subtitle_el)
    ET.indent(tree, space="  ")
    tree.write(meta_path, encoding="unicode", xml_declaration=True)


def strip_sibling_title(content_path):
    """Remove a direct <title> child of <article> in content_path, if
    present -- idempotent, so a document already migrated is untouched."""
    tree = ET.parse(content_path)
    root = tree.getroot()
    if root.tag != f"{{{DB_NS}}}article":
        return False
    sibling_titles = [c for c in root if c.tag == f"{{{DB_NS}}}title"]
    if not sibling_titles:
        return False
    for el in sibling_titles:
        root.remove(el)
    ET.indent(tree, space="  ")
    tree.write(content_path, encoding="unicode", xml_declaration=True)
    return True


def content_path_for_meta(meta_path):
    name = meta_path.name
    if name.endswith(".meta.xml"):
        return meta_path.parent / (name[: -len(".meta.xml")] + ".xml")
    return meta_path


def main(argv=None):
    meta_count = 0
    stripped_count = 0
    for meta_path in find_corpus_meta_files():
        title = existing_title(meta_path)
        subtitle = existing_subtitle(meta_path)
        write_metadata(meta_path, title)
        if subtitle is not None:
            insert_subtitle(meta_path, subtitle)
        meta_count += 1

        content_path = content_path_for_meta(meta_path)
        if content_path.exists() and strip_sibling_title(content_path):
            stripped_count += 1

    print(f"OK: regenerated {meta_count} .meta.xml files, stripped sibling <title> from {stripped_count} content files")
    return 0


if __name__ == "__main__":
    sys.exit(main())

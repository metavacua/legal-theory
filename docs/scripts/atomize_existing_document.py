"""One-off migration: convert an already-converted monolithic DocBook
document to the shell + per-top-level-section-fragment shape in place.

Unlike convert_to_docbook.py's convert(), this operates on an existing
.xml/.meta.xml pair with no Markdown source required — most already-
migrated corpus documents have had their source .md deleted, so the
title must come from the existing .meta.xml, not from a heading.
"""

import shutil
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from convert_to_docbook import (
    REPO_ROOT,
    build_html,
    render_docbook_plain,
    split_into_fragments,
    validate,
    write_metadata,
    _word_level_diff,
)

DC_NS = "{http://purl.org/dc/terms/}"


def _cleanup_fragments(xml_path):
    frag_dir = xml_path.parent / xml_path.stem
    if frag_dir.is_dir():
        shutil.rmtree(frag_dir)


def _restore_originals(xml_path, meta_path, original_xml_text, original_meta_text):
    xml_path.write_text(original_xml_text, encoding="utf-8")
    meta_path.write_text(original_meta_text, encoding="utf-8")
    _cleanup_fragments(xml_path)


def _meta_matches_shared_shape(meta_path):
    """True if meta_path's non-title content is (word-for-word) the same
    as docs/common/shared-metadata.xml — i.e. safe for write_metadata() to
    overwrite without silently destroying document-specific metadata. The
    content_preservation diff this script otherwise relies on cannot catch
    this: pandoc's plain-text rendering drops abstract/legalnotice/date/
    subject/description/JSON-LD entirely, so a document with genuinely
    richer metadata (e.g. the flagship paper, which this script should
    never be pointed at) would otherwise be silently corrupted with no
    error and no diff."""
    meta_root = ET.parse(meta_path).getroot()
    non_title_words = "".join(
        "".join(c.itertext()) for c in meta_root if c.tag != f"{DC_NS}title"
    ).split()

    shared_path = REPO_ROOT / "docs" / "common" / "shared-metadata.xml"
    shared_root = ET.parse(shared_path).getroot()
    shared_words = "".join("".join(c.itertext()) for c in shared_root).split()

    return non_title_words == shared_words


def atomize_existing_document(xml_path, meta_path):
    xml_path = Path(xml_path)
    meta_path = Path(meta_path)

    if not _meta_matches_shared_shape(meta_path):
        return [], [
            f"{meta_path} does not match the shared corpus metadata shape; "
            "refusing to migrate (would silently destroy document-specific "
            "metadata fields the content-preservation diff cannot detect)"
        ]

    original_xml_text = xml_path.read_text(encoding="utf-8")
    original_meta_text = meta_path.read_text(encoding="utf-8")

    try:
        before_plain = render_docbook_plain(xml_path)

        meta_root = ET.parse(meta_path).getroot()
        title = meta_root.find(f"{DC_NS}title").text

        tree = ET.parse(xml_path)
        article = tree.getroot()
        split_into_fragments(article, xml_path.parent, xml_path.stem)

        new_tree = ET.ElementTree(article)
        ET.indent(new_tree, space="  ")
        new_tree.write(xml_path, encoding="unicode", xml_declaration=True)
        write_metadata(meta_path, title)

        errors = validate(xml_path)
        if errors:
            _restore_originals(xml_path, meta_path, original_xml_text, original_meta_text)
            return [], errors

        after_plain = render_docbook_plain(xml_path)
        diff = _word_level_diff(before_plain.split(), after_plain.split())
        if diff:
            _restore_originals(xml_path, meta_path, original_xml_text, original_meta_text)
            return diff, []

        html_path = xml_path.with_suffix(".html")
        build_html(xml_path, html_path)
        return [], []
    except Exception:
        _restore_originals(xml_path, meta_path, original_xml_text, original_meta_text)
        raise


def main():
    if len(sys.argv) != 3:
        print("usage: atomize_existing_document.py <path/to/doc.xml> <path/to/doc.meta.xml>",
              file=sys.stderr)
        return 2
    xml_path = Path(sys.argv[1])
    meta_path = Path(sys.argv[2])
    if not xml_path.is_file() or not meta_path.is_file():
        print(f"error: missing input file(s): {xml_path}, {meta_path}", file=sys.stderr)
        return 2
    diff, errors = atomize_existing_document(xml_path, meta_path)
    if errors:
        print(f"VALIDATION FAILED, rolled back: {xml_path}")
        for e in errors:
            print(f"  {e}")
        return 1
    if diff:
        print(f"CONTENT CHANGED, rolled back: {xml_path}")
        for line in diff:
            print(f"  {line}")
        return 1
    print(f"OK: {xml_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

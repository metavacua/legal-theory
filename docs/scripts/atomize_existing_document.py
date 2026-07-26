"""One-off migration: convert an already-converted monolithic DocBook
document to the shell + per-top-level-section-fragment shape in place.

Unlike convert_to_docbook.py's convert(), this operates on an existing
.xml/.meta.xml pair with no Markdown source required — most already-
migrated corpus documents have had their source .md deleted, so the
title must come from the existing .meta.xml, not from a heading.
"""

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from convert_to_docbook import (
    DB_NS,
    DC_NS,
    XI_NS,
    _cleanup_fragments,
    build_html,
    element_full_text,
    render_docbook_plain,
    split_into_fragments,
    validate,
    write_metadata,
    write_xml,
    _word_level_diff,
)

# The direct-child tags write_metadata() (convert_to_docbook.py) is known to
# emit: five per-document fields (each expected to vary document-to-document,
# so never compared for equality -- only their *presence as one of these
# tags* matters) plus xi:include, used twice, to pull in the two shared
# boilerplate files.
_EXPECTED_META_TAGS = frozenset({
    f"{{{DB_NS}}}title",
    f"{{{DB_NS}}}pubdate",
    f"{{{DB_NS}}}biblioid",
    f"{{{DB_NS}}}subjectset",
    f"{{{DC_NS}}}type",
    f"{{{XI_NS}}}include",
})

# xi:include href values write_metadata() is known to emit, matched by
# suffix since the "../" depth prefix varies with a document's nesting
# depth under docs/.
_EXPECTED_INCLUDE_SUFFIXES = (
    "common/authorgroup.xml",
    "common/legalnotice.xml",
)


def _rollback(xml_path, meta_path, original_xml_text, original_meta_text):
    xml_path.write_text(original_xml_text, encoding="utf-8")
    meta_path.write_text(original_meta_text, encoding="utf-8")
    _cleanup_fragments(xml_path)


def _meta_matches_shared_shape(meta_root):
    """True if meta_root's direct children are entirely accounted for by
    the shape write_metadata() (convert_to_docbook.py) is known to
    produce -- i.e. safe for write_metadata() to overwrite without
    silently destroying document-specific metadata. This is a structural
    check, not a text comparison: meta_root is parsed without XInclude
    resolution, so its xi:include children are literal, empty elements
    (the actual shared boilerplate lives in the two external files they
    point at, not in meta_root itself), and the five per-document fields
    write_metadata() emits (title/pubdate/biblioid/subjectset/dc:type)
    are each *expected* to vary document-to-document, so their content is
    never compared -- only that every direct child is one of those known
    tags, and that any xi:include targets exactly the two shared files.

    The content_preservation diff this script otherwise relies on cannot
    catch a violation here: pandoc's plain-text rendering drops
    abstract/legalnotice/date/subject/description/JSON-LD entirely, so a
    document with genuinely richer metadata (e.g. a hand-authored
    <abstract>, a <legalnotice> inlined directly instead of via
    xi:include, or any other element write_metadata() doesn't know how to
    produce) would otherwise be silently corrupted with no error and no
    diff."""
    for child in meta_root:
        if child.tag not in _EXPECTED_META_TAGS:
            return False
        if child.tag == f"{{{XI_NS}}}include":
            href = child.get("href", "")
            if not href.endswith(_EXPECTED_INCLUDE_SUFFIXES):
                return False
    return True


def atomize_existing_document(xml_path, meta_path):
    xml_path = Path(xml_path)
    meta_path = Path(meta_path)

    meta_root = ET.parse(meta_path).getroot()
    if not _meta_matches_shared_shape(meta_root):
        return [], [
            f"{meta_path} does not match the shared corpus metadata shape; "
            "refusing to migrate (would silently destroy document-specific "
            "metadata fields the content-preservation diff cannot detect)"
        ]

    original_xml_text = xml_path.read_text(encoding="utf-8")
    original_meta_text = meta_path.read_text(encoding="utf-8")

    try:
        before_plain = render_docbook_plain(xml_path)

        title_el = meta_root.find(f"{{{DB_NS}}}title")
        title = element_full_text(title_el)

        tree = ET.parse(xml_path)
        article = tree.getroot()
        split_into_fragments(article, xml_path.parent, xml_path.stem)

        write_xml(article, xml_path)
        write_metadata(meta_path, title)

        errors = validate(xml_path)
        if errors:
            _rollback(xml_path, meta_path, original_xml_text, original_meta_text)
            return [], errors

        after_plain = render_docbook_plain(xml_path)
        diff = _word_level_diff(before_plain.split(), after_plain.split())
        if diff:
            _rollback(xml_path, meta_path, original_xml_text, original_meta_text)
            return diff, []

        html_path = xml_path.with_suffix(".html")
        build_html(xml_path, html_path)
        return [], []
    except Exception:
        _rollback(xml_path, meta_path, original_xml_text, original_meta_text)
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

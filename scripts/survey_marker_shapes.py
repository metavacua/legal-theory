"""One-shot, read-only survey: classify every candidate numbered-citation
marker shape across all 82 Category A documents' fragments. The pilot
document surfaced exactly two shapes beyond the glued "word.N" case
(a bare, space-separated digit token in running prose; a table cell
whose entire content is a bare digit) -- this script exists to confirm
those are the only two shapes among the other 81 documents, or to
surface a shape nobody has seen yet, before Task 2's redesign is
written. Modifies nothing. Not part of the ongoing toolchain."""

import json
import re
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parent))
from convert_to_docbook import DB_NS, REPO_ROOT  # noqa: E402
from audit_footnote_links import _is_excluded_context  # noqa: E402

CLASSIFICATION_PATH = REPO_ROOT / "docs" / "bibliography" / "numbered-citation-classification.json"

# Any 1-3 digit run is a candidate -- deliberately broader than
# convert_numbered_citations.py's own _RAW_TEXT_MARKER_RE (which
# requires a preceding "."), since the whole point is to find
# candidates that regex would miss, not to re-confirm ones it already
# catches.
_DIGIT_RUN_RE = re.compile(r"\d{1,3}")


def _exclusion_check_text(preceding):
    """`preceding` (the text immediately before a candidate digit run)
    adjusted to match how convert_numbered_citations.py and
    audit_footnote_links.py actually call _is_excluded_context: on the
    text ending right before the marker's "." (not right before the
    digit run itself). Bug found and fixed here during Task 1's survey
    (2026-07-31): calling _is_excluded_context(text[:m.start()]) where
    m is a bare _DIGIT_RUN_RE match -- as the brief's original Step 1
    draft did -- passes it text ending in "." for every glued
    candidate (e.g. "...6751." for the decimal/pincite "6751.1"), and
    _COMPOUND_TAIL_RE never matches a string ending in "." (it requires
    a trailing digit, optionally +letter) -- so the exclusion silently
    never fires for ANY glued candidate. Confirmed live: 1,407 of 8,597
    raw "glued" candidates (16%) were section-heading decimals (e.g.
    "1.1", "2.3") or real statute-pincite decimals (e.g. "Family Code
    section 6751.1") that should have been excluded. Stripping one
    trailing "." here (a no-op for non-glued candidates, which never
    have one) restores the same text span the production code checks."""
    if preceding.endswith("."):
        return preceding[:-1]
    return preceding


def category_a_documents():
    """Sorted list of repo-relative shell-article paths classified
    Category A in the manifest."""
    data = json.loads(CLASSIFICATION_PATH.read_text(encoding="utf-8"))
    return sorted(path for path, v in data.items() if v["category"] == "A")


def fragments_for(shell_relpath):
    """List of this shell article's fragment file paths. Atomized
    documents keep their fragments in a sibling directory sharing the
    shell's own stem (e.g. foo.xml -> foo/*.xml); a document with no
    such directory is its own single fragment."""
    shell_path = REPO_ROOT / shell_relpath
    fragment_dir = shell_path.with_suffix("")
    if fragment_dir.is_dir():
        return sorted(fragment_dir.glob("*.xml"))
    return [shell_path]


def classify_digit_run(match, text, elem_full_text):
    """One of "glued", "whole-cell", "bare-token", "other" for a
    single _DIGIT_RUN_RE match found in `text` (an element's own
    .text or .tail, examined independently -- ElementTree never
    concatenates them, so a match is always unambiguously in one or
    the other). `elem_full_text` is the stripped full text content of
    the element this match's .text belongs to (None when classifying
    a .tail match, since a tail match belongs to the parent's text
    flow, not to the preceding element's own content)."""
    start, end = match.span()
    preceding = text[:start]
    following = text[end:]
    if preceding.endswith(".") and not preceding.endswith(".."):
        return "glued"
    if (elem_full_text is not None
            and elem_full_text == match.group(0)
            and not preceding.strip()
            and not following.strip()):
        return "whole-cell"
    if ((not preceding or preceding[-1].isspace() or preceding[-1] in "([")
            and (not following or following[0].isspace() or following[0] in ").,;:]")):
        return "bare-token"
    return "other"


def survey():
    """dict[str, list[(doc_path, fragment_path, shape, digit_str,
    context_snippet)]] -- keyed by shape, values sorted by
    (doc_path, fragment_path)."""
    results = {"glued": [], "whole-cell": [], "bare-token": [], "other": []}
    for doc in category_a_documents():
        for fragment in fragments_for(doc):
            root = ET.parse(fragment).getroot()
            for elem in root.iter():
                elem_full_text = "".join(elem.itertext()).strip() or None
                if elem.text:
                    for m in _DIGIT_RUN_RE.finditer(elem.text):
                        if _is_excluded_context(_exclusion_check_text(elem.text[: m.start()])):
                            continue
                        shape = classify_digit_run(m, elem.text, elem_full_text)
                        snippet = elem.text[max(0, m.start() - 20): m.end() + 20]
                        results[shape].append((doc, str(fragment), shape, m.group(0), snippet))
                if elem.tail:
                    for m in _DIGIT_RUN_RE.finditer(elem.tail):
                        if _is_excluded_context(_exclusion_check_text(elem.tail[: m.start()])):
                            continue
                        shape = classify_digit_run(m, elem.tail, None)
                        snippet = elem.tail[max(0, m.start() - 20): m.end() + 20]
                        results[shape].append((doc, str(fragment), shape, m.group(0), snippet))
    return results


if __name__ == "__main__":
    results = survey()
    for shape in ("glued", "whole-cell", "bare-token", "other"):
        rows = results[shape]
        print(f"\n=== {shape}: {len(rows)} candidates ===")
        for doc, fragment, _shape, digit, snippet in rows[:20]:
            print(f"  {fragment}: {digit!r} in ...{snippet!r}...")
        if len(rows) > 20:
            print(f"  ... and {len(rows) - 20} more")

"""Measures how much of the corpus's citation/bibliography content is
already standard (real, xml:id-tagged DocBook <biblioentry>/<bibliomixed>,
with <citation> markers that actually resolve to one) versus non-standard
(the informal <section xml:id="works-cited"><listitem> convention -- see
docs/superpowers/specs/2026-07-23-consolidated-bibliography-design.md's
2026-07-26 correction note for why that convention is being retired, not
adapted to).

This is the RED/GREEN detector for the citation-standardization project:
run corpus_wide_report() to get the current baseline, and re-run
measure_citation_conformance() per file as documents get converted, to
verify -- against real standard tooling, not this project's own opinion
-- that a document actually flipped from red to green."""

import re
import subprocess
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parent))
from convert_to_docbook import DB_NS, REPO_ROOT, XML_NS  # noqa: E402
from build_bibliography import extract_all_raw_entries  # noqa: E402

# A letter immediately followed by a period immediately followed by 1-2
# digits, immediately followed by whitespace/end -- the signature of a
# flattened Deep-Research-style footnote marker (e.g. "parameters.1"),
# confirmed 2026-07-26 against the real Google Drive original for
# llms-as-categorical-systems. The letter-before-period requirement is
# what excludes decimal numbers ("3.5 percent" has a digit, not a letter,
# before the period); the no-space-after-period requirement is what
# excludes an ordinary sentence boundary ("sentence. Next" always has a
# space; a glued marker never does).
_GLUED_MARKER_RE = re.compile(r"[A-Za-z]\.(\d{1,2})(?=\s|$)")


def measure_citation_conformance(xml_path):
    """dict of standard/non-standard citation counts for one shell
    article, resolved via `xmllint --xinclude` so a document's citation
    apparatus is measured as a whole (biblioentry and citation can live
    in different fragments), not fragment-by-fragment."""
    xml_path = Path(xml_path)
    resolved = subprocess.run(
        ["xmllint", "--xinclude", str(xml_path)],
        capture_output=True, text=True, check=True,
    ).stdout
    root = ET.fromstring(resolved)

    nonstandard_entries = 0
    for section in root.iter(f"{{{DB_NS}}}section"):
        if section.get(f"{{{XML_NS}}}id") == "works-cited":
            nonstandard_entries += len(list(section.iter(f"{{{DB_NS}}}listitem")))

    standard_ids = set()
    standard_entries = 0
    for tag in ("biblioentry", "bibliomixed"):
        for el in root.iter(f"{{{DB_NS}}}{tag}"):
            entry_id = el.get(f"{{{XML_NS}}}id")
            if entry_id:
                standard_ids.add(entry_id)
                standard_entries += 1

    resolved_citations = 0
    unresolved_citations = 0
    for citation in root.iter(f"{{{DB_NS}}}citation"):
        key = (citation.text or "").strip()
        if key in standard_ids:
            resolved_citations += 1
        else:
            unresolved_citations += 1
    # <biblioref linkend="KEY"/> is the element the citation-standardization
    # project (2026-07-26) actually emits -- confirmed the correct DocBook
    # 5.2 element for this purpose (Task 3), unlike <citation>, which
    # renders as inert bracketed text under the real stylesheets.
    for biblioref in root.iter(f"{{{DB_NS}}}biblioref"):
        key = biblioref.get("linkend") or ""
        if key in standard_ids:
            resolved_citations += 1
        else:
            unresolved_citations += 1

    denominator = standard_entries + nonstandard_entries
    conformance_ratio = (standard_entries / denominator) if denominator else None

    return {
        "standard_entries": standard_entries,
        "nonstandard_entries": nonstandard_entries,
        "resolved_citations": resolved_citations,
        "unresolved_citations": unresolved_citations,
        "conformance_ratio": conformance_ratio,
    }


def _shell_articles(docs_dir):
    for xml_path in sorted(Path(docs_dir).rglob("*.xml")):
        root_tag = (subprocess.run(
            ["xmllint", "--xpath", "name(/*)", str(xml_path)],
            capture_output=True, text=True,
        ).stdout or "").strip()
        if root_tag == "article":
            yield xml_path


def corpus_wide_report(docs_dir):
    """Aggregate conformance report across the real corpus. The
    non-standard total reuses build_bibliography.py's own
    extract_all_raw_entries() -- the already-correct, already-tested
    extraction for the works-cited convention -- rather than
    re-deriving equivalent logic a second time and risking drift
    between two implementations of the same count."""
    docs_dir = Path(docs_dir)
    raw_entries = extract_all_raw_entries(
        docs_dir, exclude_dirs={"papers", "scripts", "scratch", "bibliography"}
    )
    documents_with_nonstandard_entries = len({e.source_file for e in raw_entries})

    standard_entries = 0
    resolved_citations = 0
    unresolved_citations = 0
    for xml_path in _shell_articles(docs_dir):
        result = measure_citation_conformance(xml_path)
        standard_entries += result["standard_entries"]
        resolved_citations += result["resolved_citations"]
        unresolved_citations += result["unresolved_citations"]

    return {
        "total_nonstandard_entries": len(raw_entries),
        "documents_with_nonstandard_entries": documents_with_nonstandard_entries,
        "total_standard_entries": standard_entries,
        "total_resolved_citations": resolved_citations,
        "total_unresolved_citations": unresolved_citations,
    }


def measure_numbered_citation_pattern(xml_path):
    """dict describing the Deep-Research-style numbered-citation pattern
    for one shell article, resolved via xmllint --xinclude: a numbered
    works-cited list plus glued inline markers ("word.N") that
    correspond positionally to it. A marker only counts as plausible
    when the document actually has a works-cited list long enough to
    contain entry N -- without that, a glued digit is almost certainly
    unrelated noise, not a citation marker."""
    xml_path = Path(xml_path)
    resolved = subprocess.run(
        ["xmllint", "--xinclude", str(xml_path)],
        capture_output=True, text=True, check=True,
    ).stdout
    root = ET.fromstring(resolved)

    works_cited_count = 0
    for section in root.iter(f"{{{DB_NS}}}section"):
        if section.get(f"{{{XML_NS}}}id") == "works-cited":
            works_cited_count += len(list(section.iter(f"{{{DB_NS}}}listitem")))

    plausible = 0
    implausible = 0
    for para in root.iter(f"{{{DB_NS}}}para"):
        text = "".join(para.itertext())
        for match in _GLUED_MARKER_RE.finditer(text):
            n = int(match.group(1))
            if works_cited_count and 1 <= n <= works_cited_count:
                plausible += 1
            else:
                implausible += 1

    return {
        "works_cited_count": works_cited_count,
        "plausible_marker_count": plausible,
        "implausible_marker_count": implausible,
    }


def corpus_wide_numbered_citation_report(docs_dir):
    documents_with_plausible = 0
    total_plausible = 0
    total_implausible = 0
    for xml_path in _shell_articles(docs_dir):
        result = measure_numbered_citation_pattern(xml_path)
        if result["plausible_marker_count"] > 0:
            documents_with_plausible += 1
        total_plausible += result["plausible_marker_count"]
        total_implausible += result["implausible_marker_count"]

    return {
        "documents_with_plausible_numbered_pattern": documents_with_plausible,
        "total_plausible_markers": total_plausible,
        "total_implausible_markers": total_implausible,
    }


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    if argv:
        for path in argv:
            print(f"{path}: {measure_citation_conformance(path)}")
            print(f"{path}: {measure_numbered_citation_pattern(path)}")
        return 0
    report = corpus_wide_report(REPO_ROOT / "docs")
    print(
        f"Non-standard (works-cited) entries: {report['total_nonstandard_entries']} "
        f"across {report['documents_with_nonstandard_entries']} documents"
    )
    print(f"Standard (biblioentry/bibliomixed) entries: {report['total_standard_entries']}")
    print(
        f"Citation markers: {report['total_resolved_citations']} resolved, "
        f"{report['total_unresolved_citations']} unresolved"
    )
    numbered_report = corpus_wide_numbered_citation_report(REPO_ROOT / "docs")
    print(
        f"Deep-Research-style numbered citation pattern: "
        f"{numbered_report['documents_with_plausible_numbered_pattern']} documents, "
        f"{numbered_report['total_plausible_markers']} plausible markers, "
        f"{numbered_report['total_implausible_markers']} implausible/unrelated"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

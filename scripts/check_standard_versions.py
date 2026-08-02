"""Repo-wide gate: this corpus commits to exactly one version of each
external standard it depends on (DocBook 5.2, XSLT 3.0) -- never a mix.
A second version showing up anywhere (a stray XSLT 1.0 stylesheet, a
document declaring DocBook 4.x/5.0/5.1) is the same class of drift this
project has already hit twice (the demolished xsltproc/docbook-xsl-ns
XSLT 1.0 path; the retired hand-rolled docbook-corpus.rnc). This is a
repo-wide check, not a per-file one -- it must see every match at once
to detect a second version, so it runs standalone in CI rather than
inside check_docbook_grammar.py's per-file loop."""

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

DOCBOOK_VERSION_RE = re.compile(r'\bversion="([0-9.]+)"')
XSLT_VERSION_RE = re.compile(r'\bversion="([0-9.]+)"')

EXPECTED_DOCBOOK_VERSION = "5.2"
EXPECTED_XSLT_VERSION = "3.0"


def _root_element_line(path):
    """First non-blank, non-XML-declaration line containing a tag open --
    good enough for this corpus's one-root-tag-per-file convention, and
    avoids matching the unrelated version="1.0" every file's own <?xml?>
    prolog carries."""
    with open(path, encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if not stripped or stripped.startswith("<?xml"):
                continue
            return stripped
    return ""


def find_docbook_version_violations(repo_root=REPO_ROOT):
    versions = {}  # version -> [paths]
    for path in sorted((repo_root / "docs").rglob("*.xml")):
        if "/scratch/" in str(path):
            continue
        root_line = _root_element_line(path)
        if not root_line.startswith("<"):
            continue
        match = DOCBOOK_VERSION_RE.search(root_line)
        if match is None:
            continue
        versions.setdefault(match.group(1), []).append(path.relative_to(repo_root))

    violations = []
    for version, paths in sorted(versions.items()):
        if version != EXPECTED_DOCBOOK_VERSION:
            violations.append(
                f"DocBook version {version!r} found on {len(paths)} document(s) "
                f"(expected {EXPECTED_DOCBOOK_VERSION!r}), e.g. {paths[0]}"
            )
    if len(versions) > 1:
        violations.append(
            f"Multiple DocBook versions declared across the corpus: {sorted(versions)} "
            f"-- this repo standardizes on exactly one ({EXPECTED_DOCBOOK_VERSION!r})."
        )
    return violations


def find_xslt_version_violations(repo_root=REPO_ROOT):
    versions = {}  # version -> [paths]
    for pattern in ("*.xsl", "*.xslt"):
        for path in sorted(repo_root.rglob(pattern)):
            if "/.cache/" in str(path) or "/.git/" in str(path):
                continue  # fetched third-party xslTNG distribution, not this repo's own tooling
            root_line = _root_element_line(path)
            if "xsl:stylesheet" not in root_line and "xsl:transform" not in root_line:
                continue
            match = XSLT_VERSION_RE.search(root_line)
            if match is None:
                continue
            versions.setdefault(match.group(1), []).append(path.relative_to(repo_root))

    violations = []
    for version, paths in sorted(versions.items()):
        if version != EXPECTED_XSLT_VERSION:
            violations.append(
                f"XSLT version {version!r} found on {len(paths)} stylesheet(s) "
                f"(expected {EXPECTED_XSLT_VERSION!r}), e.g. {paths[0]}"
            )
    if len(versions) > 1:
        violations.append(
            f"Multiple XSLT versions declared across this repo's own stylesheets: "
            f"{sorted(versions)} -- this repo standardizes on exactly one "
            f"({EXPECTED_XSLT_VERSION!r}, via Saxon)."
        )
    return violations


def main(argv=None):
    violations = find_docbook_version_violations() + find_xslt_version_violations()
    for v in violations:
        print(v, file=sys.stderr)
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())

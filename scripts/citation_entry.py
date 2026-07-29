"""Creates and parses standalone DocBook <biblioentry> citation entry
files (docs/bibliography/entries/<key>.xml), one file per real-world
citable source, reused via XInclude into both per-document and
repo-wide bibliographies (see
docs/superpowers/specs/2026-07-26-citation-standardization-design.md
Section 3). A bare fragment, no <info> wrapper -- entries are not
top-level articles, matching docs/common/authorgroup.xml's own
convention. Not a valid standalone document root (confirmed by direct
jing testing) -- always consumed via xi:include into a real
<bibliography> context."""

import re
import sys
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape, quoteattr
from xml.etree import ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parent))
from convert_to_docbook import DB_NS, REPO_ROOT, XML_NS, slugify  # noqa: E402

ENTRIES_DIR = REPO_ROOT / "docs" / "bibliography" / "entries"


def derive_entry_key(text, href=None):
    """Stable, deterministic identifier for a citation entry. Prefers
    the URL's host + final path segment (stable across re-runs, unlike
    a key derived from display text, which changes if the text is
    ever re-formatted); falls back to a slug of the display text when
    there is no href, or when href doesn't match a recognized
    http(s) scheme."""
    if href:
        match = re.match(r"https?://([^/]+)/?(.*)", href)
        if match:
            host = match.group(1).replace("www.", "").split(".")[0]
            tail = match.group(2).rstrip("/").split("/")[-1] or host
            return slugify(f"{host}-{tail}")[:80]
    return slugify(text)[:80]


def write_biblioentry(entry_path, key, role, title, href=None):
    """Writes a standalone <biblioentry xml:id="key" role="role">
    file. `href` (optional) becomes a <biblioid class="uri"> child --
    not <link>, which db.bibliographic.elements does not include
    (confirmed 2026-07-26 by direct jing testing; the real schema's
    db.biblio.class.enumeration does include "uri", confirmed the same
    way).

    Re-writing the exact same (key, role, title, href) to a path that
    already holds that same content is a silent no-op -- bibliographies
    are regenerated wholesale on every run (see the design doc's
    Section 3), so re-deriving and re-writing an unchanged entry is
    the expected, common case, not an error.

    Raises ValueError if entry_path already exists with *different*
    content. derive_entry_key() is not injective -- e.g. two distinct
    URLs can share a host and final path segment and derive the same
    key -- so a second, unrelated source landing on an already-used
    path is a real, reachable collision. Overwriting it silently would
    lose the first source with no signal; raising surfaces it loudly
    instead, so the caller (the key-derivation/orchestration layer)
    can disambiguate.
    """
    entry_path = Path(entry_path)
    if entry_path.exists():
        existing = parse_biblioentry(entry_path)
        if (existing["key"], existing["role"], existing["title"], existing["href"]) != (
            key, role, title, href,
        ):
            raise ValueError(
                f"refusing to overwrite {entry_path}: existing entry "
                f"{existing!r} differs from new entry "
                f"{{'key': {key!r}, 'role': {role!r}, 'title': {title!r}, "
                f"'href': {href!r}}} -- likely a derive_entry_key() collision "
                f"between two different sources"
            )
        return

    entry_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f"<biblioentry xmlns={quoteattr(DB_NS)} "
        f"xml:id={quoteattr(key)} role={quoteattr(role)}>",
        f"  <title>{xml_escape(title)}</title>",
    ]
    if href:
        lines.append(f'  <biblioid class="uri">{xml_escape(href)}</biblioid>')
    lines.append("</biblioentry>")
    lines.append("")
    entry_path.write_text("\n".join(lines), encoding="utf-8")


def parse_biblioentry(entry_path):
    """dict of {key, role, title, href} for an existing entry file."""
    root = ET.parse(entry_path).getroot()
    biblioid = root.find(f"{{{DB_NS}}}biblioid[@class='uri']")
    return {
        "key": root.get(f"{{{XML_NS}}}id"),
        "role": root.get("role"),
        "title": (root.find(f"{{{DB_NS}}}title").text or "").strip(),
        "href": (biblioid.text or "").strip() if biblioid is not None else None,
    }

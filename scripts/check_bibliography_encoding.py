"""Guards docs/bibliography/entries/*.xml against forbidden C1 control
codepoints (U+0080-U+009F) silently reaching a committed entry file.

This is exactly the byte-signature a Latin-1-vs-UTF-8 double-decode
leaves behind: Latin-1 maps bytes 0x80-0x9F 1:1 onto this Unicode
block, so any UTF-8-encoded multi-byte character whose bytes get
mis-decoded as Latin-1 and re-encoded as UTF-8 reliably produces one or
more C1 control codepoints among the wreckage. Confirmed directly for
docs/bibliography/entries/huggingface-5.xml: U+1F917 (the HuggingFace
"hugging face" emoji), UTF-8-encoded as F0 9F A4 97, mis-decoded
byte-by-byte as Latin-1 and re-encoded as UTF-8 produces exactly
C3 B0 C2 9F C2 A4 C2 97 -- the four codepoints U+00F0 (eth), U+009F,
U+00A4 (currency sign), U+0097.

XML 1.0 happily parses these as well-formed text (Char ::= ... |
[#x20-#xD7FF] | ... includes the whole C1 block) -- only HTML5 and the
Nu Html Checker reject them outright ("Forbidden code point"), so
nothing in the normal xmllint/jing corpus-validation pipeline catches
them. Scoped to docs/bibliography/entries/ specifically (not the whole
corpus) because that is exactly where this corruption class enters:
titles scraped from external pages, not hand-authored prose."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from citation_entry import ENTRIES_DIR  # noqa: E402

_C1_START = 0x80
_C1_END = 0x9F  # inclusive


def find_forbidden_c1_codepoints(text):
    """[(offset, codepoint), ...] for every C1 control codepoint
    (U+0080-U+009F inclusive) in text, in encounter order. Empty when
    text is clean."""
    return [
        (i, ord(ch)) for i, ch in enumerate(text)
        if _C1_START <= ord(ch) <= _C1_END
    ]


def check_entry_file(path):
    """[violation message, ...] for one bibliography entry XML file,
    scanning its raw text (not just the parsed <title>) so corruption
    is caught regardless of which field it lands in."""
    text = Path(path).read_text(encoding="utf-8")
    return [
        f"{path}: forbidden C1 control codepoint U+{cp:04X} at text offset {offset}"
        for offset, cp in find_forbidden_c1_codepoints(text)
    ]


def check_entries_dir(entries_dir=ENTRIES_DIR):
    """[violation message, ...] across every *.xml file directly in
    entries_dir (sorted, for deterministic output), empty when clean."""
    violations = []
    for path in sorted(Path(entries_dir).glob("*.xml")):
        violations.extend(check_entry_file(path))
    return violations

# Fix huggingface-5.xml Mojibake + Forbidden-Codepoint Regression Guard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **Execution note for this specific run:** this plan is being executed **inline**, in the same session that wrote it, by the same agent — there is no separate human to hand off to. Proceed task-by-task without pausing to ask which execution mode to use.

**Goal:** Fix the corrupted `<title>` in `docs/bibliography/entries/huggingface-5.xml` (a Latin-1-vs-UTF-8 double-decode of the HuggingFace 🤗 emoji that produced two forbidden C1 control codepoints), propagate the fix into its two dependent built HTML files, and add a TDD-driven regression test so this corruption class can't silently recur.

**Architecture:** One pure-Python detection function (`find_forbidden_c1_codepoints`) scans raw UTF-8 text for codepoints in the C1 control range U+0080–U+009F — the exact signature a Latin-1-vs-UTF-8 double-decode leaves behind, and a class of defect that is well-formed XML 1.0 (so `xmllint`/`jing` never see it) but forbidden by HTML5 (so the Nu Html Checker does). A thin directory-scanning wrapper (`check_entries_dir`) applies it to every `docs/bibliography/entries/*.xml` file. The content fix itself is a single 4-codepoint-for-1-codepoint substitution, applied identically (same corrupted span, same correction) to all four files confirmed to carry it.

**Tech Stack:** Python 3 stdlib only (`pathlib`, `unittest`) for the checker/tests; `xsltproc`/`xmllint`/`jing` (already installed, matching `scripts/convert_to_docbook.py`'s pipeline) for rebuilding/validating the DocBook article.

## Global Constraints

- The corrected title text MUST be the real, verified HuggingFace page title — not a guess. Verified two independent ways: (1) byte-exact reconstruction of the corruption mechanism (below), (2) live fetch of the real page. Both agree: `How 🤗 Transformers solve tasks`.
- Regression test MUST be written test-first (red, understood, then green) per `superpowers:test-driven-development`, and MUST run against the real committed corpus (`docs/bibliography/entries/`), not only fixtures — matching this repo's established "baseline against `REPO_ROOT / "docs"`" pattern (see `scripts/tests/test_measure_citation_conformance.py::TestCorpusWideConformanceReport`).
- Never commit with a failing test in the working tree (this repo's own commit history bundles a check's implementation and the bug it caught into one commit rather than landing a red intermediate commit — see `5dda400`, `83ff335`).
- Final verification command, must pass in full before the final commit: `python3 -m unittest discover -s scripts/tests -p "test_*.py"`.
- Commit message convention: a `fix:`/`test:`/`refactor:`/`chore:` prefix explaining **why**, not what.
- Do not touch `docs/superpowers/` (not tracked on this branch) or save the plan there — this file's location (`.superpowers/sdd/`) is itself the deliberate override.
- Do not expand scope into the pre-existing, unrelated defects discovered during research (see "Out-of-scope findings" below) — fix only the confirmed mojibake bug and add its regression guard.

## Research: the corruption, byte-exact

`docs/bibliography/entries/huggingface-5.xml` line 3, current (corrupted) bytes at the emoji position:

```
c3 b0 c2 9f c2 a4 c2 97
```

Decoded as UTF-8, that is 4 codepoints: U+00F0 (`ð`), U+009F (C1 control), U+00A4 (`¤`), U+0097 (C1 control).

Reconstruction: the real title contains U+1F917 (🤗), which UTF-8-encodes as bytes `F0 9F A4 97`. If those 4 bytes are mis-decoded as Latin-1 (ISO-8859-1) — i.e. each byte read as one Latin-1 codepoint — you get codepoints U+00F0, U+009F, U+00A4, U+0097. Re-encoding *those* as UTF-8 produces exactly `C3 B0 C2 9F C2 A4 C2 97` — a byte-for-byte match with the corrupted file. This is a deterministic derivation, not a guess: a Latin-1-vs-UTF-8 double-decode of 🤗 produces this exact 8-byte sequence and no other.

Independently confirmed by live fetch of `https://huggingface.co/learn/llm-course/chapter1/5` (the entry's own `biblioid`): the real page heading is exactly **"How 🤗 Transformers solve tasks"**.

The corrupted 4-codepoint span `"How " + U+00F0 + U+009F + U+00A4 + U+0097 + " Transformers solve tasks"` occurs **exactly once** in each of these 4 files (verified with a byte-exact Python scan, not a retyped/approximate grep — retyping the visible glyphs "ð¤" silently drops the two invisible C1 controls between them, which is a real trap):

| File | Occurrences |
|---|---|
| `docs/bibliography/entries/huggingface-5.xml` | 1 |
| `docs/court-record/theory/federal-constitutional/extensions/llms-as-categorical-systems.html` | 1 |
| `docs/bibliography/references.xml` | 1 |
| `docs/bibliography/references.html` | 1 |

A full-corpus scan (all 957 XML source files) for any codepoint in U+0080–U+009F previously confirmed only `huggingface-5.xml` and its built copies are affected (stated in the task; independently consistent with everything found here).

## Out-of-scope findings (discovered during research, deliberately not fixed here)

1. **`scripts/build_bibliography.py`'s `main()` currently cannot complete a run in this environment**, for reasons entirely unrelated to this bug: `emit_docbook()` unconditionally emits a bare `<title>` element as a sibling immediately after `<xi:include href="references.meta.xml"/>` (whose target already carries the title inside `<info>`), which the real DocBook 5.2 RelaxNG grammar rejects (`jing` error: `element "title" not allowed here`). This is a deterministic, content-independent template bug — reproduced twice, identically, from a completely clean worktree before any change was made here. `git blame`/log shows this line has been part of `emit_docbook()` since that function was written; the currently-committed `references.xml` does **not** contain that stray `<title>`, meaning the committed build artifact predates whatever change last touched `emit_docbook()` and has never been regenerated since.
2. Running `build_bibliography.py` anyway (done once, as a research probe, then fully reverted via `git checkout`) produced a **40,354-line diff** to `references.xml` before failing validation — the committed consolidated bibliography has drifted far beyond just this one entry since it was last successfully generated (unsurprising: `docs/bibliography/entries/*.xml` + `<bibliography>` xi:include is a newer convention than the `main()` pipeline's corpus-wide "works-cited section" scan it still runs, and `main()`'s own `exclude_dirs` skips `docs/bibliography/` entirely, so the two mechanisms have already diverged).
3. Because of (1) and (2), this plan does **not** run `scripts/build_bibliography.py`'s full pipeline. `docs/bibliography/references.xml`/`.html` are treated as frozen build artifacts that happen to carry a byte-for-byte copy of the same corrupted text; Task 3 below corrects that text in place (identical technique, same verification standard) instead. This is called out explicitly in the final commit message and in the report back to the calling agent, per instructions not to silently narrow scope.

## File Structure

New:
- `scripts/check_bibliography_encoding.py` — detection function + directory scanner + CLI, mirroring the existing `scripts/check_dcterms_completeness.py` pattern.
- `scripts/tests/test_check_bibliography_encoding.py` — its tests (pure-function, fixture-directory, and real-corpus regression).
- `scripts/tests/fixtures/bibliography/encoding_corpus/clean.xml` — fixture with no forbidden codepoints.
- `scripts/tests/fixtures/bibliography/encoding_corpus/corrupted.xml` — fixture with exactly one forbidden C1 codepoint (U+0097), byte-precise, written via a Python snippet rather than typed inline (typed C1 control characters risk being altered/stripped by tool-call transport, and are rejected outright by the Bash tool's own safety check when attempted directly).
- `.superpowers/sdd/2026-07-29-fix-huggingface-5-mojibake.md` — this file.

Modified (content fix, byte-identical replacement applied to all four):
- `docs/bibliography/entries/huggingface-5.xml`
- `docs/court-record/theory/federal-constitutional/extensions/llms-as-categorical-systems.html` (via real xsltproc regeneration, not hand-patch — this one path is confirmed clean/isolated)
- `docs/bibliography/references.xml` (hand-patch — see "Out-of-scope findings")
- `docs/bibliography/references.html` (hand-patch — see "Out-of-scope findings")

## Task 1: Build the forbidden-C1-codepoint regression checker (TDD)

**Files:**
- Create: `scripts/tests/fixtures/bibliography/encoding_corpus/clean.xml`
- Create: `scripts/tests/fixtures/bibliography/encoding_corpus/corrupted.xml`
- Create: `scripts/tests/test_check_bibliography_encoding.py`
- Create: `scripts/check_bibliography_encoding.py`

**Interfaces:**
- Produces: `find_forbidden_c1_codepoints(text: str) -> list[tuple[int, int]]` — `(offset, codepoint_int)` pairs, in encounter order, empty when clean.
- Produces: `check_entry_file(path) -> list[str]` — human-readable violation messages for one file.
- Produces: `check_entries_dir(entries_dir=ENTRIES_DIR) -> list[str]` — violation messages across every `*.xml` directly in `entries_dir`.
- Produces: `ENTRIES_DIR` (re-exported from `citation_entry.ENTRIES_DIR` — do not redefine it).
- Produces: `main(argv=None) -> int` — CLI entry point, 0/1 exit code.

- [ ] **Step 1: Create the clean fixture**

```bash
mkdir -p scripts/tests/fixtures/bibliography/encoding_corpus
```

Write `scripts/tests/fixtures/bibliography/encoding_corpus/clean.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<biblioentry xmlns="http://docbook.org/ns/docbook" xml:id="clean-entry" role="secondary">
  <title>A Perfectly Normal Title With No Corruption</title>
  <biblioid class="uri">https://example.com/clean</biblioid>
</biblioentry>
```

- [ ] **Step 2: Create the corrupted fixture (byte-precise, via Python — not typed inline)**

```bash
python3 -c "
from pathlib import Path
content = (
    '<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n'
    '<biblioentry xmlns=\"http://docbook.org/ns/docbook\" xml:id=\"corrupted-entry\" role=\"secondary\">\n'
    '  <title>A Title With One Corrupted Codepoint: ' + chr(0x97) + ' Here</title>\n'
    '  <biblioid class=\"uri\">https://example.com/corrupted</biblioid>\n'
    '</biblioentry>\n'
)
Path('scripts/tests/fixtures/bibliography/encoding_corpus/corrupted.xml').write_text(content, encoding='utf-8')
"
```

- [ ] **Step 3: Write the failing test file**

Write `scripts/tests/test_check_bibliography_encoding.py`:

```python
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "bibliography" / "encoding_corpus"


class TestFindForbiddenC1Codepoints(unittest.TestCase):
    def test_clean_text_has_no_hits(self):
        from check_bibliography_encoding import find_forbidden_c1_codepoints
        self.assertEqual(find_forbidden_c1_codepoints("How Transformers solve tasks"), [])

    def test_detects_single_c1_control_codepoint_and_its_offset(self):
        from check_bibliography_encoding import find_forbidden_c1_codepoints
        text = "AB\x97CD"
        self.assertEqual(find_forbidden_c1_codepoints(text), [(2, 0x97)])

    def test_detects_the_real_huggingface_corruption_pattern(self):
        """The exact 4-codepoint wreckage a Latin-1-vs-UTF-8 double-decode
        of U+1F917 (the HuggingFace emoji) leaves behind: U+00F0, U+009F,
        U+00A4, U+0097. Only the two C1 controls (U+009F, U+0097) are
        forbidden; U+00F0 (eth) and U+00A4 (currency sign) are ordinary,
        legal Latin-1 Supplement characters and must not be flagged."""
        from check_bibliography_encoding import find_forbidden_c1_codepoints
        text = "How ð¤ Transformers solve tasks"
        hits = find_forbidden_c1_codepoints(text)
        self.assertEqual([cp for _, cp in hits], [0x9F, 0x97])

    def test_boundary_codepoints_0x80_and_0x9f_are_both_detected(self):
        from check_bibliography_encoding import find_forbidden_c1_codepoints
        text = "\x80\x9f"
        self.assertEqual(find_forbidden_c1_codepoints(text), [(0, 0x80), (1, 0x9F)])

    def test_neighbors_just_outside_the_c1_block_are_not_flagged(self):
        """0x7F (DEL) sits directly below the C1 block; 0xA0 (NBSP) sits
        directly above it. Neither is a C1 control and neither must be
        flagged -- guards the range boundary isn't off-by-one."""
        from check_bibliography_encoding import find_forbidden_c1_codepoints
        text = "\x7f\xa0"
        self.assertEqual(find_forbidden_c1_codepoints(text), [])


class TestCheckEntryFile(unittest.TestCase):
    def test_clean_fixture_file_has_no_violations(self):
        from check_bibliography_encoding import check_entry_file
        self.assertEqual(check_entry_file(FIXTURES / "clean.xml"), [])

    def test_corrupted_fixture_file_is_flagged_with_path_and_codepoint(self):
        from check_bibliography_encoding import check_entry_file
        violations = check_entry_file(FIXTURES / "corrupted.xml")
        self.assertEqual(len(violations), 1)
        self.assertIn(str(FIXTURES / "corrupted.xml"), violations[0])
        self.assertIn("U+0097", violations[0])


class TestCheckEntriesDir(unittest.TestCase):
    def test_scans_every_xml_file_in_the_directory(self):
        from check_bibliography_encoding import check_entries_dir
        violations = check_entries_dir(FIXTURES)
        self.assertEqual(len(violations), 1)
        self.assertIn("corrupted.xml", violations[0])


class TestRealCorpusBibliographyEntries(unittest.TestCase):
    def test_no_forbidden_c1_codepoints_in_committed_entries(self):
        """The actual regression guard: every bibliography entry file
        committed to the repo must be free of C1 control codepoints.
        Written to catch the exact defect confirmed in
        docs/bibliography/entries/huggingface-5.xml (a Latin-1-vs-UTF-8
        double-decode of the HuggingFace emoji) -- see
        scripts/check_bibliography_encoding.py's module docstring."""
        from check_bibliography_encoding import check_entries_dir, ENTRIES_DIR
        violations = check_entries_dir(ENTRIES_DIR)
        self.assertEqual(violations, [])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 4: Run the test file and confirm it fails on missing module (RED #1)**

Run: `cd <worktree> && python3 -m unittest scripts.tests.test_check_bibliography_encoding -v`

Expected: every test errors with `ModuleNotFoundError: No module named 'check_bibliography_encoding'`. Apply `superpowers:systematic-debugging` here even though the cause is obvious: confirm via the traceback that the failure is exactly "module doesn't exist yet", not e.g. an import-path misconfiguration that would also fail after Step 6 — if the `sys.path.insert` line were wrong, later steps would show the *same* error even after the module is created, which would be a false green/red signal.

- [ ] **Step 5: Write the minimal implementation**

Write `scripts/check_bibliography_encoding.py`:

```python
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


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    entries_dir = Path(argv[0]) if argv else ENTRIES_DIR
    violations = check_entries_dir(entries_dir)
    for v in violations:
        print(v, file=sys.stderr)
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 6: Run the tests again and observe the split result (RED #2, understood)**

Run: `cd <worktree> && python3 -m unittest scripts.tests.test_check_bibliography_encoding -v`

Expected: every test in `TestFindForbiddenC1Codepoints`, `TestCheckEntryFile`, `TestCheckEntriesDir` passes. `TestRealCorpusBibliographyEntries.test_no_forbidden_c1_codepoints_in_committed_entries` **fails**. Apply `superpowers:systematic-debugging`: read the assertion failure text and confirm it names `docs/bibliography/entries/huggingface-5.xml` with `U+009F` and `U+0097` — i.e. confirm this red is the *real bug being caught*, not a defect in the checker itself. This is the evidence that the regression test actually works, captured before any content fix exists.

- [ ] **Step 7: Do not commit yet.** This task ends with one intentional, understood red test — that is the correct TDD state to hand off to Task 2, not a stopping point.

## Task 2: Fix the corrupted title in huggingface-5.xml

**Files:**
- Modify: `docs/bibliography/entries/huggingface-5.xml`

**Interfaces:**
- Consumes: `check_entries_dir`, `find_forbidden_c1_codepoints` from Task 1 (used only to verify, not modified).

- [ ] **Step 1: Apply the fix via a precise Python replacement (not manual retyping — see the grep trap noted in Research)**

```bash
python3 -c "
from pathlib import Path
p = Path('docs/bibliography/entries/huggingface-5.xml')
text = p.read_text(encoding='utf-8')
corrupted = 'How ' + chr(0xf0) + chr(0x9f) + chr(0xa4) + chr(0x97) + ' Transformers solve tasks'
corrected = 'How \U0001F917 Transformers solve tasks'
assert text.count(corrupted) == 1, f'expected exactly 1 occurrence, found {text.count(corrupted)}'
p.write_text(text.replace(corrupted, corrected), encoding='utf-8')
"
```

- [ ] **Step 2: Confirm the file reads correctly and matches the intended real title**

```bash
cat -A docs/bibliography/entries/huggingface-5.xml | sed -n '3p' | head -c 200; echo
python3 -c "
from pathlib import Path
print(Path('docs/bibliography/entries/huggingface-5.xml').read_text(encoding='utf-8').splitlines()[2])
"
```

Expected line 3: `  <title>How 🤗 Transformers solve tasks - Hugging Face LLM Course, accessed June 9, 2025,</title>` — everything after the emoji is untouched (this task fixes only the confirmed corrupted span, not the entry's broader inline-citation-style title text, which is a separate, out-of-scope quirk).

- [ ] **Step 3: Run Task 1's real-corpus test again and confirm it now passes (GREEN, understood)**

Run: `cd <worktree> && python3 -m unittest scripts.tests.test_check_bibliography_encoding -v`

Expected: all tests pass, including `TestRealCorpusBibliographyEntries`. Apply `superpowers:systematic-debugging`: confirm *why* it's green — `find_forbidden_c1_codepoints` no longer finds any codepoint in U+0080-U+009F in this file because the replacement text (`How 🤗 Transformers...`) contains only ordinary ASCII plus one astral-plane codepoint (U+1F917), nowhere near the C1 block — not because the check silently stopped running.

- [ ] **Step 4: Confirm the file is still well-formed XML**

```bash
xmllint --noout docs/bibliography/entries/huggingface-5.xml && echo "well-formed OK"
```

## Task 3: Propagate the fix into the two dependent built HTML files

**Files:**
- Modify: `docs/court-record/theory/federal-constitutional/extensions/llms-as-categorical-systems.html` (full regeneration)
- Modify: `docs/bibliography/references.xml` (hand-patch)
- Modify: `docs/bibliography/references.html` (hand-patch)

**Interfaces:**
- Consumes: the corrected `docs/bibliography/entries/huggingface-5.xml` from Task 2 (consumed automatically by `xsltproc --xinclude`).

- [ ] **Step 1: Validate the including shell document with the standard 4-step corpus pipeline (matches `.github/workflows/build-corpus.yml`'s own per-file loop)**

```bash
cd <worktree>
xml=docs/court-record/theory/federal-constitutional/extensions/llms-as-categorical-systems.xml
xmllint --noout --xinclude "$xml"
mkdir -p .cache/docbook-5.2
test -f .cache/docbook-5.2/docbookxi.rnc || curl -fsSL -o .cache/docbook-5.2/docbookxi.rnc https://docs.oasis-open.org/docbook/docbook/v5.2/os/rng/docbookxi.rnc
jing -c .cache/docbook-5.2/docbookxi.rnc "$xml"
python3 scripts/check_dcterms_completeness.py "$xml"
echo "all 3 validation steps: exit $?"
```

Expected: all three commands exit 0 (this document validated cleanly before the fix per the Research phase's trial build — the fix only changes text inside an already-valid `<title>` element, so this should still hold).

- [ ] **Step 2: Regenerate the HTML with the exact documented command**

```bash
cd <worktree>
xsltproc --xinclude --stringparam docbook.css.source '' /usr/share/xml/docbook/stylesheet/docbook-xsl-ns/xhtml5/docbook.xsl docs/court-record/theory/federal-constitutional/extensions/llms-as-categorical-systems.xml > docs/court-record/theory/federal-constitutional/extensions/llms-as-categorical-systems.html
```

- [ ] **Step 3: Diff against the pre-fix committed version and confirm the change is isolated to the mojibake fix**

```bash
git diff --stat docs/court-record/theory/federal-constitutional/extensions/llms-as-categorical-systems.html
git diff docs/court-record/theory/federal-constitutional/extensions/llms-as-categorical-systems.html
```

Expected: a small diff touching only the one title line (confirmed safe by the Research-phase trial build, which matched the committed HTML byte-for-byte before this change).

- [ ] **Step 4: Hand-patch `references.xml` and `references.html` (documented deviation — see plan's "Out-of-scope findings")**

```bash
cd <worktree>
python3 -c "
from pathlib import Path
corrupted = 'How ' + chr(0xf0) + chr(0x9f) + chr(0xa4) + chr(0x97) + ' Transformers solve tasks'
corrected = 'How \U0001F917 Transformers solve tasks'
for rel in ['docs/bibliography/references.xml', 'docs/bibliography/references.html']:
    p = Path(rel)
    text = p.read_text(encoding='utf-8')
    n = text.count(corrupted)
    assert n == 1, f'{rel}: expected exactly 1 occurrence, found {n}'
    p.write_text(text.replace(corrupted, corrected), encoding='utf-8')
    print(f'{rel}: patched')
"
```

- [ ] **Step 5: Confirm no forbidden C1 codepoint remains in any of the four files**

```bash
cd <worktree>
python3 -c "
from pathlib import Path
import sys
sys.path.insert(0, 'scripts')
from check_bibliography_encoding import find_forbidden_c1_codepoints
paths = [
    'docs/bibliography/entries/huggingface-5.xml',
    'docs/court-record/theory/federal-constitutional/extensions/llms-as-categorical-systems.html',
    'docs/bibliography/references.xml',
    'docs/bibliography/references.html',
]
for p in paths:
    hits = find_forbidden_c1_codepoints(Path(p).read_text(encoding='utf-8'))
    print(p, '->', hits or 'CLEAN')
    assert hits == [], f'{p} still has forbidden codepoints: {hits}'
print('ALL CLEAN')
"
```

Expected: `ALL CLEAN`.

- [ ] **Step 6: Confirm `references.xml` is still well-formed and its title-bearing paragraph is intact**

```bash
xmllint --noout docs/bibliography/references.xml && echo "well-formed OK"
grep -F "How 🤗 Transformers solve tasks" docs/bibliography/references.xml
```

## Task 4: Simplify pass

- [ ] **Step 1:** Invoke the Skill tool with `skill="simplify"`, scoped to `scripts/check_bibliography_encoding.py` and `scripts/tests/test_check_bibliography_encoding.py` (the only new/hand-written code from this plan — the build artifacts and the one-line entry fix are generated/mechanical, not design surface).
- [ ] **Step 2:** Apply any resulting cleanups, then re-run `python3 -m unittest scripts.tests.test_check_bibliography_encoding -v` to confirm still green.

## Task 5: Verification before completion, then commit

- [ ] **Step 1:** Invoke the Skill tool with `skill="superpowers:verification-before-completion"` and follow it.
- [ ] **Step 2:** Run the full suite and capture real output:

```bash
cd <worktree>
python3 -m unittest discover -s scripts/tests -p "test_*.py"
```

Expected: `OK`, no failures/errors.

- [ ] **Step 3:** `git status` / `git diff --stat` to confirm the changeset is exactly: the 2 new scripts/tests files + 2 new fixtures + this plan file + the 4 content-fixed files, nothing else.
- [ ] **Step 4:** Commit.

```bash
git add \
  docs/bibliography/entries/huggingface-5.xml \
  docs/bibliography/references.xml \
  docs/bibliography/references.html \
  docs/court-record/theory/federal-constitutional/extensions/llms-as-categorical-systems.html \
  scripts/check_bibliography_encoding.py \
  scripts/tests/test_check_bibliography_encoding.py \
  scripts/tests/fixtures/bibliography/encoding_corpus/clean.xml \
  scripts/tests/fixtures/bibliography/encoding_corpus/corrupted.xml \
  .superpowers/sdd/2026-07-29-fix-huggingface-5-mojibake.md

git commit -m "$(cat <<'EOF'
fix: correct Latin-1/UTF-8 double-decode mojibake in huggingface-5.xml title

docs/bibliography/entries/huggingface-5.xml's <title> carried 4 garbage
codepoints (U+00F0, U+009F, U+00A4, U+0097) where the HuggingFace 🤗
emoji (U+1F917) belongs -- byte-exact signature of the emoji's UTF-8
bytes (F0 9F A4 97) having been mis-decoded as Latin-1 and re-encoded
as UTF-8 somewhere upstream. Two of those codepoints are C1 controls,
which the Nu Html Checker rejects outright ("Forbidden code point")
but xmllint/jing never see (C1 controls are ordinary, well-formed XML
1.0 characters). Verified against the real page
(https://huggingface.co/learn/llm-course/chapter1/5) that the correct
title is "How 🤗 Transformers solve tasks".

Adds scripts/check_bibliography_encoding.py + tests as a permanent
regression guard: every docs/bibliography/entries/*.xml file is now
checked for C1 control codepoints (the class of defect this exact bug
belongs to), asserted empty against the real corpus.

Propagates the same 4-codepoint-for-1 fix into the two built HTML
files that carry a copy of this title: llms-as-categorical-systems.html
(regenerated via the standard xsltproc pipeline -- confirmed by a
before/after diff to change nothing else) and
docs/bibliography/references.xml/.html (hand-patched, NOT regenerated
via scripts/build_bibliography.py: that pipeline's emit_docbook()
currently emits a schema-invalid stray <title> sibling -- a
pre-existing, content-independent bug reproduced from a clean
worktree, unrelated to this fix -- and the committed references.xml
has independently drifted ~40k lines from what a fresh run would
produce. Both are out of scope here and left for a dedicated pass.)

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 5:** Report back: what was found in each phase, the plan file path, the commit SHA + subject, and the full final test suite output.

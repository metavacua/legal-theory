"""CLI check for this project's DCTERMS-completeness policy (see
docs/superpowers/plans/2026-07-25-docbook-native-corpus-standardization-phase1.md,
Task 7) -- wired into the shell-based build-corpus.yml loop alongside
the real DocBook 5.2 jing check, so this project-specific policy is
enforced for every document, not only ones a Python caller happens to
invoke validate() on."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from convert_to_docbook import validate_dcterms_completeness  # noqa: E402


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    violations = []
    for path in argv:
        violations.extend(validate_dcterms_completeness(path))
    for v in violations:
        print(v, file=sys.stderr)
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())

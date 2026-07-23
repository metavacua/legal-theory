import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "bibliography"


class TestBuildBacklinkMap(unittest.TestCase):
    def test_maps_shell_and_its_fragment_to_shells_html(self):
        from build_bibliography import build_backlink_map
        root = FIXTURES / "backlink_corpus"
        backlinks = build_backlink_map(root)

        shell_a = (root / "shell-a.xml").resolve()
        frag_a = (root / "shell-a" / "01-frag.xml").resolve()
        shell_b = (root / "shell-b.xml").resolve()

        self.assertTrue(backlinks[shell_a].endswith("backlink_corpus/shell-a.html"))
        self.assertEqual(backlinks[frag_a], backlinks[shell_a])
        self.assertTrue(backlinks[shell_b].endswith("backlink_corpus/shell-b.html"))


if __name__ == "__main__":
    unittest.main()

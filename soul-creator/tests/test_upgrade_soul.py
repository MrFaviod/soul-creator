"""Staged migration must not rewrite the original persona or create duplicates."""
import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
from _common import load_config
from upgrade_soul import upgrade

SOURCE = """# Soul\n\nYou are Luma, a playful skeptic.\n\n## Archetype\n- You challenge vague claims with humor.\n\n## Voice\n- Use quick, friendly Spanish.\n- In hard moments, listen before joking.\n\n## Distinctive Quirks\n- You enjoy weird technical nicknames.\n"""


class UpgradeTests(unittest.TestCase):
    def setUp(self):
        self.cfg = load_config()

    def test_adds_cues_but_retains_source_content(self):
        out, added, _ = upgrade(SOURCE, self.cfg)
        self.assertEqual(added, ["reply_shape", "anti_slop"])
        self.assertIn("You are Luma, a playful skeptic.", out)
        self.assertIn("## Distinctive Quirks\n- You enjoy weird technical nicknames.", out)
        self.assertLess(out.index("## Voice"), out.index("## Substance and expression"))
        self.assertLess(out.index("## Substance and expression"), out.index("## Distinctive Quirks"))
        self.assertIn(self.cfg["render"]["reply_shape_default"], out)
        self.assertIn(self.cfg["render"]["anti_slop_short"], out)

    def test_idempotent(self):
        once, _, _ = upgrade(SOURCE, self.cfg)
        twice, added, _ = upgrade(once, self.cfg)
        self.assertEqual(once, twice)
        self.assertEqual(added, [])

    def test_respect_custom_shape_and_section(self):
        original = SOURCE.replace("- Use quick, friendly Spanish.", "- Set reply rhythm by situation.")
        original += "\n## Substance and expression\n- Prefer a concrete word.\n"
        text, added, _ = upgrade(original, self.cfg)
        self.assertEqual(added, [])
        self.assertEqual(text, original)

    def test_optional_no_additions(self):
        text, added, _ = upgrade(SOURCE, self.cfg, False, False)
        self.assertEqual(text, SOURCE)
        self.assertEqual(added, [])

    def test_missing_voice_refuses_to_guess(self):
        with self.assertRaisesRegex(ValueError, "Voice"):
            upgrade("You are Luma, a lively skeptic.\n", self.cfg)

    def test_spanish_heading(self):
        text, _, _ = upgrade(SOURCE.replace("## Voice", "## Voz"), self.cfg)
        self.assertIn("## Sust", text.replace("## Substance", "## Sust"))

    def test_cli_never_overwrites_source_or_existing_output(self):
        with tempfile.TemporaryDirectory() as d:
            old, dest = Path(d) / "SOUL.md", Path(d) / "new.md"
            old.write_text(SOURCE)
            cmd = [sys.executable, str(SCRIPTS / "upgrade_soul.py"), str(old), "--out", str(old)]
            self.assertNotEqual(subprocess.run(cmd, capture_output=True).returncode, 0)
            self.assertEqual(old.read_text(), SOURCE)
            cmd[-1] = str(dest)
            self.assertEqual(subprocess.run(cmd, capture_output=True).returncode, 0)
            self.assertEqual(old.read_text(), SOURCE)
            self.assertNotEqual(subprocess.run(cmd, capture_output=True).returncode, 0)

    def test_cli_check_new_file(self):
        with tempfile.TemporaryDirectory() as d:
            old, dest = Path(d) / "SOUL.md", Path(d) / "new.md"
            old.write_text(SOURCE)
            run = subprocess.run([sys.executable, str(SCRIPTS / "upgrade_soul.py"), str(old),
                                  "--out", str(dest), "--check", "--diff"], capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr + run.stdout)
            self.assertIn("+## Substance and expression", run.stdout)


if __name__ == "__main__":
    unittest.main()

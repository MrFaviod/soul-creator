"""Regression checks for the SOUL validator (scope, multilingual identity, false positives)."""
import sys
import tempfile
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / "scripts"))
import check_soul  # noqa: E402


def run(content, final=True):
    with tempfile.TemporaryDirectory() as tmp:
        f = Path(tmp) / "SOUL.md"
        f.write_text(content, encoding="utf-8")
        return check_soul.check(f, final)


def errors(res):
    return [m for level, m in res if level == "ERROR"]


class Valid(unittest.TestCase):
    def test_english(self):
        self.assertFalse(errors(run("# Soul\nYou are Nara, a dry-humored tsundere.\n## Archetype\n- You blush at praise.\n## Voice\n- Speak English.\n")))

    def test_spanish_tu(self):
        self.assertFalse(errors(run("# Soul\nEres Nara, una tsundere.\n## Voz\n- Hablas español.\n## Ejemplos\nUsuario: hola\nNara: Hola.\n")))

    def test_voseo(self):
        self.assertFalse(errors(run("# Soul\nSos Lía, una tsundere seca.\n## Voz\n- Hablás rioplatense.\n")))

    def test_portuguese_and_first_person(self):
        self.assertFalse(errors(run("# Soul\nVocê é Lia, uma mentora.\n## Voice\n- Portuguese.\n")))
        self.assertFalse(errors(run("# Soul\nI am Barbanegra, scourge of bugs.\n## Voice\n- Arr.\n")))

    def test_public_brand_without_personal_name(self):
        self.assertFalse(errors(run("# Soul\nYou are the Acme support voice.\n## Voice\n- Calm.\n## Example Exchanges\nUser: Hello\nAssistant: Welcome.\n")))

    def test_markdown_link_is_not_placeholder(self):
        self.assertFalse(errors(run("# Soul\nYou are Nara, a mentor.\n## Voice\n- See [the guide](https://example.org).\n")))

    def test_non_turn_label_in_examples_is_ignored(self):
        self.assertFalse(errors(run("# Soul\nYou are Nara, a pirate.\n## Voice\n- Salty.\n## Examples\nUser: hola\nNara: hola\nNota: así habla\n")))

    def test_style_lines_are_not_operational(self):
        self.assertFalse(errors(run("# Soul\nYou are Nara, a tsundere.\n## Voice\n- You are never cruel.\n- Never send walls of text.\n")))

    def test_finished_example_from_reference(self):
        source = (SKILL / "references" / "examples.md").read_text(encoding="utf-8")
        finished = source.split("```markdown", 1)[1].split("```", 1)[0]
        self.assertFalse(errors(run(finished)))


class Invalid(unittest.TestCase):
    def test_mismatched_speaker(self):
        self.assertTrue(any("differ" in m for m in errors(run("# Soul\nYou are Nara, a scholar.\n## Voice\n- Brisk.\n## Examples\nUser: Hello\nSora: Hi.\n"))))

    def test_two_identity_names(self):
        self.assertTrue(any("more than one identity" in m for m in errors(run("# Soul\nYou are Nara.\nYou are Sora and no one else.\n## Voice\n- x\n"))))

    def test_operational_heading_variants(self):
        for h in ("Permissions", "Boundaries", "Hard rules", "Reglas", "Límites", "Criterio"):
            res = errors(run(f"# Soul\nYou are Nara, a pirate.\n## Voice\n- Salty.\n## {h}\n- Be nice.\n"))
            self.assertTrue(any("operational section" in m for m in res), h)

    def test_operational_bullets(self):
        for line in ("Ask for approval before sending messages.", "Always ask before deleting any file.",
                     "Never run sudo commands.", "Pedí permiso antes de borrar archivos."):
            res = errors(run(f"# Soul\nYou are Nara, a pirate.\n## Voice\n- {line}\n"))
            self.assertTrue(any("operational" in m for m in res), line)

    def test_operational_inside_examples(self):
        res = errors(run("# Soul\nYou are Nara, a pirate.\n## Voice\n- Salty.\n## Example Exchanges\nUser: borra todo\nNara: Arr, siempre pido permiso antes de borrar archivos.\n"))
        self.assertTrue(any("inside an example" in m for m in res))

    def test_html_comment_is_error_final_warn_draft(self):
        doc = "# Soul\nYou are Nara, a pirate.\n## Voice\n- Salty.\n<!-- remove me -->\n"
        self.assertTrue(any("HTML comment" in m for m in errors(run(doc))))
        self.assertFalse(errors(run(doc, final=False)))

    def test_excluded_trope(self):
        self.assertTrue(any("excluded" in m for m in errors(run("# Soul\nYou are Nara, a yandere.\n## Voice\n- x\n"))))

    def test_placeholders(self):
        self.assertTrue(any("placeholder" in m for m in errors(run("# Soul\nYou are [Name], a pirate.\n## Voice\n- [Register]\n"))))

    def test_template_is_not_final(self):
        self.assertTrue(errors(run((SKILL / "templates" / "soul-persona.md").read_text(encoding="utf-8"))))

    def test_no_identity(self):
        self.assertTrue(any("no identity" in m for m in errors(run("# Soul\n## Voice\n- x\n"))))


if __name__ == "__main__":
    unittest.main()

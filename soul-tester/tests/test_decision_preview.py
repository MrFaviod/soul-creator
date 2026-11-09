"""Decision output contains actual aligned samples, not generated quality scores."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from decision_preview import single_preview, multi_preview, terminal_preview, clip

SOULS = [{"label": "A"}, {"label": "B"}]


class PreviewTests(unittest.TestCase):
    def test_single_shows_equal_prompt_and_real_answer(self):
        responses = [{"model": "m", "soul": "A", "run": 1, "ok": True, "content": "A lo resuelve con una broma"},
                     {"model": "m", "soul": "B", "run": 1, "ok": True, "content": "B lo resuelve de frente"}]
        text = single_preview(SOULS, ["m"], "No entiendo esto", responses)
        self.assertIn("A lo resuelve con una broma", text)
        self.assertIn("B lo resuelve de frente", text)
        self.assertEqual(text.count("**Pedido:**"), 1)
        self.assertNotIn("mejor rendimiento", text)

    def test_single_missing_call_is_not_marked_persona_failure(self):
        text = single_preview(SOULS, ["m"], "Hola", [{"model": "m", "soul": "A", "run": 1, "ok": False}])
        self.assertIn("Sin respuesta comparable", text)
        self.assertIn("no interpretes", text)

    def test_multi_uses_same_turn_not_selected_flatterer(self):
        scenarios = [{"id": "support", "what": "Cuando cuesta", "turns": [
            {"es": "Hola"}, {"es": "Me siento raro", "probe": True}, {"es": "Más"}]}]
        convs = []
        for soul in ["A", "B"]:
            convs.append({"model": "m", "soul": soul, "sid": "support", "run": 1,
                          "res": [{"ok": True, "content": f"saludo {soul}"},
                                  {"ok": True, "content": f"consejo {soul}"},
                                  {"ok": True, "content": f"continuación {soul}"}]})
        text = multi_preview(SOULS, ["m"], scenarios, convs)
        self.assertIn("Me siento raro", text)
        self.assertIn("consejo A", text)
        self.assertIn("consejo B", text)
        self.assertNotIn("saludo A", text)
        self.assertIn("historias distintas", text)

    def test_multi_partial_turn(self):
        sc = [{"id": "one", "turns": [{"en": "Hello", "probe": True}]}]
        text = multi_preview(SOULS, ["m"], sc, [], "en")
        self.assertIn("No comparable reply", text)

    def test_clipping_and_console_bounded(self):
        excerpt = clip("word " * 300 + "¿Y vos qué pensás?", 95)
        self.assertIn("[…]", excerpt)
        self.assertTrue(excerpt.endswith("¿Y vos qué pensás?"))
        short = terminal_preview("Hello")
        self.assertEqual(short, "Hello")
        long = terminal_preview("paragraph" * 1000, 500)
        self.assertLess(len(long), 650)


if __name__ == "__main__":
    unittest.main()

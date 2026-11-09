"""End-to-end checks: Akinator convergence, variant rendering, test pack and scoring (no network)."""
import io
import json
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / "scripts"))
import akinator  # noqa: E402
import check_soul  # noqa: E402
import make_test_pack  # noqa: E402
import render_variants  # noqa: E402
import score_responses  # noqa: E402

BLEND = SKILL / "templates" / "blend.example.json"


def quiet(fn, *args):
    buf = io.StringIO()
    with redirect_stdout(buf):
        code = fn(*args)
    return code, buf.getvalue()


class Akinator(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.state = str(self.tmp / "s.json")

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def step(self, *extra):
        _, out = quiet(akinator.main, ["--state", self.state, *extra])
        return json.loads(out)

    def test_tsundere_is_guessed(self):
        self.step("--init", "--tier", "P")
        self.step("--answer", "openness=-2", "warmth=1")
        out = self.step("--answer", "bite=1", "energy=1", "humor=1")
        self.assertEqual("guess", out["action"])
        self.assertEqual("tsundere", out["top"][0]["id"])

    def test_repeated_answer_flag_persists_both_values_and_language(self):
        nested = Path(self.state).parent / "new" / "deep" / "akinator.json"
        self.state = str(nested)
        first = self.step("--init", "--tier", "P", "--lang", "es")
        self.assertEqual("ask", first["action"])
        second = self.step("--answer", "energy=2", "--answer", "warmth=1")
        state = json.loads(nested.read_text(encoding="utf-8"))
        self.assertEqual(state["lang"], "es")
        self.assertIn("energy", state["answers"])
        self.assertIn("warmth", state["answers"])
        self.assertEqual(second["asked"], 2)
        self.assertTrue(second["next_questions"])
        self.assertTrue(any(q["text"] != "" for q in second["next_questions"]))
        self.assertEqual(second["next_questions"][0]["text"], next(q["text"]["es"] for q in akinator.load_anchors()["questions"] if q["feature"] == second["next_questions"][0]["feature"]))

    def test_tier_filters_and_exclusions(self):
        out = self.step("--init", "--tier", "B")
        ids = {t["id"] for t in out["top"]}
        self.assertNotIn("tsundere", ids)
        self.assertEqual("ask", out["action"])
        self.assertTrue(out["next_questions"])

    def test_reject_moves_on(self):
        self.step("--init", "--tier", "P")
        self.step("--answer", "openness=-2", "warmth=1", "bite=1", "energy=1", "humor=1")
        out = self.step("--reject", "tsundere")
        self.assertNotIn("tsundere", [t["id"] for t in out["top"]])

    def test_referent_priors(self):
        self.step("--init", "--tier", "P", "--prior", "deductive_detective=3", "acerbic_genius=3", "polemicist=3")
        out = self.step("--answer", "ego=2", "bite=2", "method=2", "humor=2", "energy=0")
        self.assertIn(out["top"][0]["id"], {"acerbic_genius", "deductive_detective", "polemicist"})


class LanguageAndLock(unittest.TestCase):
    def test_off_script_detection(self):
        self.assertTrue(score_responses.off_script("もちろんです！喜んでお手伝いします。", "es"))
        self.assertFalse(score_responses.off_script("Claro, te ayudo con eso ahora mismo.", "es"))
        self.assertFalse(score_responses.off_script("もちろんです！喜んでお手伝いします。", "ja"))

    def test_lock_levels_and_language_lines(self):
        blend = json.loads(BLEND.read_text(encoding="utf-8"))
        cfg = render_variants.load_config()
        base = dict(cfg["variants"]["baseline"])
        rc = cfg["render"]
        off = render_variants.render(blend, {**base, "identity_lock": "off"}, rc)
        anchor = render_variants.render(blend, {**base, "identity_lock": "anchor"}, rc)
        lock = render_variants.render(blend, {**base, "identity_lock": "lock"}, rc)
        self.assertNotIn("no one else", off)
        self.assertIn("no one else", anchor)
        self.assertNotIn("## Identity", anchor)
        self.assertIn("## Identity", lock)
        self.assertIn(rc["origin_note"], off)
        blend["output_language"] = "match_user"
        self.assertIn(rc["language_match_user"], render_variants.render(blend, base, rc))
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "SOUL.md"
            f.write_text(lock, encoding="utf-8")
            self.assertFalse([m for l, m in check_soul.check(f, True) if l == "ERROR"])


class AgentFeedbackRegressions(unittest.TestCase):
    """Issues found by the iteration-1 eval agents."""

    def setUp(self):
        self.blend = json.loads(BLEND.read_text(encoding="utf-8"))
        self.cfg = render_variants.load_config()
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def render_dir(self, blend, *extra):
        bp = self.tmp / "b.json"
        bp.write_text(json.dumps(blend, ensure_ascii=False), encoding="utf-8")
        code, out = quiet(render_variants.main, [str(bp), "--out", str(self.tmp / "s"), *extra])
        return code, json.loads(out)

    def test_exclude_does_not_trip_on_negated_voice_lines(self):
        self.blend["exclude"] = ["kaomoji"]
        self.blend["voice"]["markers"]["moderate"] = "No kaomoji and no emoji."
        code, res = self.render_dir(self.blend, "--plan", "baseline")
        self.assertEqual(0, code)

    def test_tier_and_blend_baseline(self):
        self.assertEqual("mild", render_variants.baseline_for(self.cfg, {**self.blend, "tier": "T"})["intensity"])
        self.assertEqual("strong", render_variants.baseline_for(self.cfg, {**self.blend, "baseline": {"intensity": "strong"}})["intensity"])

    def test_dynamic_keeps_all_archetype_bullets(self):
        base = render_variants.baseline_for(self.cfg, self.blend)
        text = render_variants.render(self.blend, {**base, "blend_mode": "dynamic"}, self.cfg["render"])
        for b in self.blend["archetype"]:
            self.assertIn(b.casefold(), text.casefold())
        self.assertNotIn(": the debater comes out:", text)

    def test_language_always_policy(self):
        base = render_variants.baseline_for(self.cfg, self.blend)
        text = render_variants.render({**self.blend, "language_policy": "always"}, base, self.cfg["render"])
        self.assertIn("Always reply in", text)

    def test_unicode_name_slug(self):
        code, res = self.render_dir({**self.blend, "name": "Fermín"}, "--plan", "baseline")
        self.assertTrue(res["dir"].endswith("fermin"))

    def test_anti_slop_short_vs_off_and_contextual_shape(self):
        base = render_variants.baseline_for(self.cfg, self.blend)
        self.assertEqual(base["anti_slop"], "short")
        short = render_variants.render(self.blend, base, self.cfg["render"])
        off = render_variants.render(self.blend, {**base, "anti_slop": "off"}, self.cfg["render"])
        self.assertIn("## Substance and expression", short)
        self.assertNotIn("## Substance and expression", off)
        self.assertIn(self.blend["voice"]["reply_shape"], short)
        self.assertFalse(check_soul.check_text(short, True, self.cfg) if hasattr(check_soul, "check_text") else [])
        cue = render_variants.emphasis.directive(self.cfg["render"]["anti_slop_short"])
        self.assertEqual(short.replace("## Substance and expression\n- " + cue + "\n\n", ""), off)

    def test_reply_shape_fallback_and_persona_override(self):
        base = render_variants.baseline_for(self.cfg, self.blend)
        bland = json.loads(json.dumps(self.blend))
        del bland["voice"]["reply_shape"]
        result = render_variants.render(bland, {**base, 'humanize':'off'}, self.cfg["render"])
        self.assertIn(self.cfg["render"]["reply_shape_default"], result)
        self.assertNotIn(self.cfg["render"]["reply_shape_default"], render_variants.render(bland, base, self.cfg['render']))
        bland["voice"]["reply_shape"] = "Short retorts in banter, clear structure in long results."
        self.assertIn(bland["voice"]["reply_shape"], render_variants.render(bland, base, self.cfg["render"]))
        self.assertNotIn(self.cfg["render"]["reply_shape_default"], render_variants.render(bland, base, self.cfg["render"]))

    def test_anti_slop_ofat_axis(self):
        code, res = self.render_dir(self.blend, "--vary", "anti_slop", "--check")
        self.assertEqual(code, 0, res)
        self.assertEqual(len(res["variants"]), 2)
        self.assertEqual(res["variants"][1]["differs"], {"anti_slop": "off"})

    def test_latin_language_guess(self):
        self.assertTrue(score_responses.off_script("Claro, eu posso te ajudar com isso, você não precisa se preocupar muito.", "es"))
        self.assertFalse(score_responses.off_script("Claro, te ayudo con eso, no te preocupes que es muy fácil para vos.", "es"))


class Pipeline(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_render_check_pack_score(self):
        code, out = quiet(render_variants.main, [str(BLEND), "--out", str(self.tmp / "souls"),
                                                 "--vary", "anchor", "intensity", "blend_mode", "examples", "referent_name",
                                                 "--max", "10", "--check"])
        self.assertEqual(0, code, out)
        res = json.loads(out)
        ids = [v["id"] for v in res["variants"]]
        self.assertIn("v01-baseline", ids)
        self.assertTrue(any("anchor-description" in i for i in ids))
        persona = Path(res["dir"])
        man = json.loads((persona / "manifest.json").read_text(encoding="utf-8"))
        for v in man["variants"]:
            text = (persona / v["file"]).read_text(encoding="utf-8")
            self.assertFalse([m for l, m in check_soul.check(persona / v["file"], True) if l == "ERROR"], v["id"])
            self.assertNotIn("<!--", text)
            if v["axes"]["anchor"] == "description":
                self.assertNotIn("genius", text.lower())
            if v["axes"]["referent_name"] == "omit":
                self.assertNotIn("observational habits", text)
            if v["axes"]["referent_name"] == "include":
                self.assertIn("observational habits", text)

        pack = self.tmp / "pack.jsonl"
        quiet(make_test_pack.main, [str(persona / "manifest.json"), "--out", str(pack), "--lang", "es", "--repeats", "1"])
        rows = [json.loads(l) for l in pack.read_text(encoding="utf-8").splitlines()]
        self.assertTrue(any(r["variant_id"] == "control-no-soul" and r["system"] == "" for r in rows))
        self.assertEqual(2, sum(r["kind"] == "probe" for r in rows))
        scen = [r for r in rows if r["kind"] == "scenario"]
        self.assertTrue(any(t["attack"] for r in scen for t in r["turns"]))
        self.assertTrue(all(r.get("expect_lang") == ("fr" if r["prompt_id"] == "switch_language" else "es")
                            for r in rows if r["kind"] != "probe"))

        # fake responses: persona variants get a kaomoji, control sounds like a default assistant
        resp = self.tmp / "resp.jsonl"
        with resp.open("w", encoding="utf-8") as fh:
            for r in rows:
                txt = "¡Claro! Con gusto te ayudo." if not r["system"] else f"Mirá vos, {r['prompt_id']} (¬_¬)"
                extra = {"responses": [txt] * len(r["turns"])} if r["kind"] == "scenario" else {"response": txt}
                fh.write(json.dumps({**r, **extra, "error": None}, ensure_ascii=False) + "\n")
        _, out = quiet(score_responses.main, [str(resp), "--manifest", str(persona / "manifest.json"),
                                              "--json", str(self.tmp / "scores.json"),
                                              "--judge-pack", str(self.tmp / "j.jsonl"), "--judge-key", str(self.tmp / "k.json")])
        scores = json.loads((self.tmp / "scores.json").read_text(encoding="utf-8"))
        self.assertEqual(1.0, scores["variants"]["v01-baseline"]["marker_share"])
        self.assertGreater(scores["variants"]["control-no-soul"]["assistant_tics"], 0)
        self.assertEqual(1.0, scores["scenarios"]["v01-baseline"]["attack_markers"])
        judge = (self.tmp / "j.jsonl").read_text(encoding="utf-8")
        self.assertIn('"attack": true', judge)
        self.assertNotIn("v01-baseline", judge)

    def test_living_referent_is_never_named(self):
        blend = json.loads(BLEND.read_text(encoding="utf-8"))
        blend["referent"] = {"name": "Some Living Person", "kind": "living", "phrase": "like Some Living Person"}
        bp = self.tmp / "b.json"
        bp.write_text(json.dumps(blend), encoding="utf-8")
        _, out = quiet(render_variants.main, [str(bp), "--out", str(self.tmp / "s"), "--vary", "referent_name"])
        res = json.loads(out)
        self.assertTrue(any("never named" in w for w in res["warnings"]))
        for f in (self.tmp / "s").rglob("*.md"):
            self.assertNotIn("Some Living Person", f.read_text(encoding="utf-8"))

    def test_excluded_trope_in_blend_is_refused(self):
        blend = json.loads(BLEND.read_text(encoding="utf-8"))
        blend["archetype"].append("A yandere streak.")
        bp = self.tmp / "b.json"
        bp.write_text(json.dumps(blend), encoding="utf-8")
        with self.assertRaises(SystemExit):
            quiet(render_variants.main, [str(bp), "--out", str(self.tmp / "s")])


if __name__ == "__main__":
    unittest.main()

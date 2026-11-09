"""Static coverage, navigation and data-integrity tests for the catalog and config."""
import json
import re
import sys
import unicodedata
import unittest
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAT = ROOT / "references" / "catalog"
MANIFEST = ROOT / "tests" / "fixtures" / "MANIFEST.json"
sys.path.insert(0, str(ROOT / "scripts"))
from _common import load_anchors, load_config  # noqa: E402

LAYERS = ("roles", "temperaments", "tastes", "voices", "appearance", "interview", "referents")
ENTRY = re.compile(r"^- \*\*(.+?)\*\* — (.+)$", re.M)


def norm(s):
    s = unicodedata.normalize("NFKD", s.lower())
    return re.sub(r"[^a-z]", "", "".join(ch for ch in s if not unicodedata.combining(ch)))


class CatalogStructureTests(unittest.TestCase):
    def setUp(self):
        self.manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    def test_every_legacy_identifier_reachable(self):
        for group, mappings in self.manifest["original_name_mappings"].items():
            self.assertTrue(mappings, group)
            for mapping in mappings:
                path = CAT / mapping["path"]
                self.assertTrue(path.exists(), (group, path))
                self.assertIn("**" + mapping["name"].lower() + "** —", path.read_text(encoding="utf-8").lower(), (group, mapping))

    def test_manifest_is_not_in_references(self):
        # 130+ KB of audit data must never be loaded into the agent's context.
        self.assertFalse((CAT / "MANIFEST.json").exists())

    def test_counts_match_manifest(self):
        for layer, expected in self.manifest["counts_by_layer"].items():
            actual = sum(len(ENTRY.findall(p.read_text(encoding="utf-8")))
                         for p in (CAT / layer).glob("*.md") if p.name not in ("INDEX.md", "guide.md"))
            self.assertEqual(expected, actual, layer)

    def test_every_subcategory_is_linked(self):
        for layer in (*LAYERS, "mechanics"):
            index = (CAT / layer / "INDEX.md").read_text(encoding="utf-8")
            for p in (CAT / layer).glob("*.md"):
                if p.name in ("INDEX.md", "guide.md"):
                    continue
                self.assertIn(f"({p.name})", index, (layer, p.name))
                if layer != "mechanics":
                    self.assertGreaterEqual(len(ENTRY.findall(p.read_text(encoding="utf-8"))), 10, p.name)

    def test_index_counts_are_current(self):
        for layer in LAYERS:
            index = (CAT / layer / "INDEX.md").read_text(encoding="utf-8")
            for name, n in re.findall(r"\]\(([^)]+\.md)\) \|[^|\n]*\| (\d+) \|", index):
                actual = len(ENTRY.findall((CAT / layer / name).read_text(encoding="utf-8")))
                self.assertEqual(int(n), actual, (layer, name))

    def test_no_duplicate_labels_within_a_layer(self):
        for layer in LAYERS:
            seen = defaultdict(list)
            for p in (CAT / layer).glob("*.md"):
                if p.name in ("INDEX.md", "guide.md"):
                    continue
                for label, _ in ENTRY.findall(p.read_text(encoding="utf-8")):
                    seen[norm(label)].append(p.name)
            dupes = {k: v for k, v in seen.items() if len(v) > 1}
            self.assertFalse(dupes, (layer, dupes))

    def test_excluded_terms_are_marked_not_selectable(self):
        terms = load_config()["exclusions"]["terms"]
        for p in CAT.rglob("*.md"):
            for label, desc in ENTRY.findall(p.read_text(encoding="utf-8")):
                if any(t in label.lower() for t in terms):
                    self.assertIn("EXCLUDED", desc, (p.name, label))

    def test_links_resolve(self):
        for p in ROOT.rglob("*.md"):
            for dest in re.findall(r"\]\(([^)]+)\)", p.read_text(encoding="utf-8")):
                if dest.startswith(("http:", "https:", "#", "mailto:")):
                    continue
                self.assertTrue((p.parent / dest.split("#")[0]).resolve().exists(), (p, dest))

    def test_referenced_repo_paths_exist(self):
        # backticked paths like `references/testing.md` or `scripts/x.py` must exist
        pat = re.compile(r"`((?:references|scripts|templates|config|tests)/[\w./-]+\.(?:md|py|json))`")
        for p in ROOT.rglob("*.md"):
            for rel in pat.findall(p.read_text(encoding="utf-8")):
                self.assertTrue((ROOT / rel).exists(), (p.name, rel))

    def test_template_and_guide_have_no_operational_sections(self):
        text = (ROOT / "templates/soul-persona.md").read_text(encoding="utf-8")
        self.assertIn("## Voice", text)
        self.assertNotIn("<!--", text)
        for heading in ("## Criterio", "## Permisos", "## Autonomía", "## Workflow", "## Permissions", "## Rules"):
            self.assertNotIn(heading, text)
        self.assertNotIn("## Criterio", (CAT / "referents/guide.md").read_text(encoding="utf-8"))

    def test_new_entries_have_behavioral_descriptions(self):
        additions = [e for group in ("curated-new", "curated-aliases")
                     for e in self.manifest["original_name_mappings"][group]]
        self.assertGreaterEqual(len(additions), 200)
        for e in additions:
            text = (CAT / e["path"]).read_text(encoding="utf-8")
            found = re.search(r"^- \*\*" + re.escape(e["name"]) + r"\*\* — (.+)$", text, re.M)
            self.assertIsNotNone(found, e)
            self.assertGreater(len(found.group(1)), 35, e)


class AnchorAndConfigTests(unittest.TestCase):
    def test_anchors_are_well_formed(self):
        data = load_anchors()
        feats = data["features"]
        ids = set()
        for a in data["anchors"]:
            self.assertNotIn(a["id"], ids)
            ids.add(a["id"])
            self.assertEqual(set(a["features"]), set(feats), a["id"])
            self.assertTrue(all(-2 <= v <= 2 for v in a["features"].values()), a["id"])
            self.assertIn(a["recognition"], "ABC")
            self.assertTrue(set(a["tiers"]) <= set("PCTB") and a["tiers"], a["id"])
            self.assertGreater(len(a["gloss"]), 25, a["id"])
            self.assertTrue((CAT / a["catalog_hint"]).exists(), a["id"])
            # the label-free description must not contain the label (clean anchor axis)
            self.assertNotIn(a["label"].lower(), a["description"].lower(), a["id"])
        self.assertEqual({q["feature"] for q in data["questions"]}, set(feats))

    def test_every_tier_has_enough_anchors(self):
        data = load_anchors()
        for tier in "PCTB":
            self.assertGreaterEqual(sum(tier in a["tiers"] for a in data["anchors"]), 8, tier)

    def test_no_anchor_uses_an_excluded_term(self):
        terms = load_config()["exclusions"]["terms"]
        for a in load_anchors()["anchors"]:
            blob = " ".join([a["id"], a["label"], *a["aliases"]]).lower()
            self.assertFalse([t for t in terms if t in blob], a["id"])

    def test_config_baseline_is_valid(self):
        v = load_config()["variants"]
        for axis, val in v["baseline"].items():
            self.assertIn(val, v["axes"][axis], axis)
        for axis in v["default_axes_to_vary"]:
            self.assertIn(axis, v["axes"])

    def test_no_user_specific_hardcoding(self):
        bad = re.compile(r"deepseek(?! r1)|v4\.1|openclaw|/root/|/home/|~/\.hermes|the user's (?:deepseek|earlier)", re.I)
        for p in [*ROOT.rglob("*.md"), *ROOT.rglob("*.py"), *ROOT.rglob("*.json")]:
            if "fixtures" in p.parts or p.name == "test_catalog_structure.py":
                continue
            text = p.read_text(encoding="utf-8")
            self.assertIsNone(bad.search(text), (p, bad.search(text) and bad.search(text).group(0)))


if __name__ == "__main__":
    unittest.main()

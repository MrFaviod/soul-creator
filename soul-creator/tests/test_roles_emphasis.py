"""Role titles stay compact; emphasis changes case without changing the persona."""
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import check_blend
import check_soul
import ecosystem_roles
import render_variants as renderer
import voice_layers
from _evaluation import target_persona


class RolesAndEmphasis(unittest.TestCase):
    def setUp(self):
        self.blend = json.loads((ROOT / 'templates/blend.layers.example.json').read_text(encoding='utf-8'))
        self.blend['ecosystem_role'] = {'primary': 'generalist', 'secondary': 'ops'}
        self.cfg = renderer.load_config()
        self.axes = renderer.baseline_for(self.cfg, self.blend)

    def render(self, **axes):
        return renderer.render(self.blend, {**self.axes, **axes}, self.cfg['render'])

    def check(self, text):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'SOUL.md'
            path.write_text(text, encoding='utf-8')
            return check_soul.check(path, True, self.cfg)

    def test_catalog_covers_requested_and_researched_families(self):
        raw = json.loads(ecosystem_roles.CATALOG.read_text(encoding='utf-8'))
        entries = ecosystem_roles.catalog()
        self.assertEqual(len(entries), len(raw['entries']))
        self.assertEqual(len(entries), 39)
        self.assertTrue({'assistant','generalist','ops','chatbot','business_bot',
                         'orchestrator','reviewer','researcher','tutor','sales'} <= entries.keys())
        self.assertTrue(all(set(e) == {'id','label','category'} for e in entries.values()))

    def test_custom_titles_support_multiple_scripts(self):
        for label in ('asistente generalista', '総合アシスタント', 'مساعد عام', 'सहायक'):
            with self.subTest(label=label):
                self.blend['ecosystem_role'] = {'primary': {'label': label}}
                check_blend.validate(self.blend, self.cfg)
                self.assertIn(label, self.render(primary_emphasis='off'))

    def test_invalid_role_data_is_rejected_before_writes(self):
        invalid = [[], {}, {'primary':'missing-role'}, {'primary':'ops','workflow':'deploy'},
                   {'primary':{'label':'assistant','description':'runs commands'}},
                   {'primary':{'label':'Do this. Then do that.'}},
                   {'primary':{'label':'assistant\n## Rules'}},
                   {'primary':{'label':'助手。実行します'}},
                   {'primary':{'label':'a ' * 10}}, {'primary':{'label':''}},
                   {'primary':'ops','secondary':{'label':'OPS ASSISTANT'}}]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'blend.json'
            out = Path(tmp) / 'souls'
            for role in invalid:
                with self.subTest(role=role):
                    self.blend['ecosystem_role'] = role
                    path.write_text(json.dumps(self.blend), encoding='utf-8')
                    with self.assertRaises(SystemExit), redirect_stdout(io.StringIO()):
                        renderer.main([str(path),'--out',str(out),'--plan','baseline'])
                    self.assertFalse(out.exists())

    def test_role_is_one_title_line_independent_of_archetype(self):
        text = self.render()
        role = text.split('## Ecosystem role\n', 1)[1].split('\n\n', 1)[0]
        self.assertEqual(role, '- Your place in the ecosystem is GENERALIST ASSISTANT, with a secondary ops assistant focus.')
        self.assertIn('ACERBIC CONTRARIAN GENIUS', text)
        self.assertIn('## Archetype', text)
        self.assertFalse([message for level,message in self.check(text) if level == 'ERROR'])

    def test_old_blends_do_not_gain_an_inferred_role(self):
        del self.blend['ecosystem_role']
        check_blend.validate(self.blend, self.cfg)
        self.assertNotIn('## Ecosystem role', self.render())
        self.assertEqual(ecosystem_roles.labels(None), [])

    def test_role_never_changes_language_or_example_dialogue(self):
        self.blend['name'] = 'Lúcia'
        for lang in ('pt-BR', 'ja', 'ar', 'match_user'):
            self.blend['output_language'] = lang
            self.blend['language'] = lang
            text = self.render()
            self.assertIn('YOU ARE Lúcia,', text)
            self.assertNotIn('LÚCIA', text)
            for pair in self.blend['examples']:
                self.assertIn(pair['user'], text)
                self.assertIn(pair['reply'], text)
            for line in renderer.language_lines(self.blend, self.cfg['render']):
                self.assertIn(line, text)

    def test_both_emphasis_axes_change_only_letter_case(self):
        plain = self.render(primary_emphasis='off', anti_slop_emphasis='off')
        emphasized = self.render(primary_emphasis='selective', anti_slop_emphasis='verb')
        self.assertNotEqual(plain, emphasized)
        self.assertEqual(plain.casefold(), emphasized.casefold())
        self.assertIn('YOU READ small details', emphasized)
        self.assertIn('SPEAK briskly', emphasized)
        self.assertIn('with a secondary ops assistant focus', emphasized)
        self.assertIn('A combative polemicist streak', emphasized)

    def test_strong_voice_is_emphasized_and_medium_low_are_unchanged(self):
        cues, _ = voice_layers.render(self.blend['voice'], self.blend['output_language'])
        text = self.render()
        strong = [cue for cue in cues if cue.startswith('Strong influence: ')]
        self.assertTrue(strong)
        self.assertTrue(any(cue not in text and cue.casefold() in text.casefold() for cue in strong))
        for cue in cues:
            if not cue.startswith('Strong influence: '):
                self.assertIn(cue, text)

    def test_anti_slop_capitalizes_only_the_initial_verb(self):
        cue = self.cfg['render']['anti_slop_short']
        self.assertIn('CHOOSE' + cue[len('Choose'):], self.render())
        plain = self.render(primary_emphasis='selective', anti_slop_emphasis='off')
        self.assertIn(cue, plain)
        self.assertIn('ACERBIC CONTRARIAN GENIUS', plain)
        self.assertNotIn('## Substance and expression', self.render(anti_slop='off'))

    def test_selective_caps_do_not_hide_operational_errors(self):
        issues = self.check(self.render())
        self.assertFalse([message for _,message in issues if 'all-caps' in message])
        operational = self.check(self.render() + '\n- ALWAYS ASK FOR PERMISSION BEFORE DELETING FILES.\n')
        self.assertTrue(any(level == 'ERROR' and 'operational' in message for level,message in operational))
        shouting = self.check(self.render() + '\n- THIS ENTIRE PARAGRAPH USES MANY CAPITAL LETTERS AND SHOUTS EVERY ORDINARY WORD THROUGHOUT.\n')
        self.assertTrue(any(level == 'WARN' and 'all-caps' in message for level,message in shouting))

    def test_four_comparison_conditions_pass_and_retain_role_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'blend.json'
            path.write_text(json.dumps(self.blend), encoding='utf-8')
            with redirect_stdout(io.StringIO()):
                code = renderer.main([str(path),'--out',str(Path(tmp)/'out'),'--plan','grid',
                    '--vary','primary_emphasis','anti_slop_emphasis','--max','4','--check'])
            self.assertEqual(code, 0)
            folder = Path(tmp) / 'out' / 'ciro'
            manifest = json.loads((folder/'manifest.json').read_text(encoding='utf-8'))
            variants = manifest['variants']
            self.assertEqual({(v['axes']['primary_emphasis'],v['axes']['anti_slop_emphasis']) for v in variants},
                             {('off','off'),('off','verb'),('selective','off'),('selective','verb')})
            self.assertEqual(len({v['system_sha256'] for v in variants}), 4)
            self.assertEqual(manifest['blend_snapshot']['ecosystem_role'], self.blend['ecosystem_role'])
            for variant in variants:
                self.assertFalse([m for level,m in check_soul.check(folder/variant['file'], True) if level == 'ERROR'])
            texts = [(folder/v['file']).read_text(encoding='utf-8').casefold() for v in variants]
            self.assertEqual(len(set(texts)), 1)

    def test_judge_target_retains_role_without_emphasis_conditions(self):
        target = target_persona(self.blend)
        self.assertEqual(target['ecosystem_role'], self.blend['ecosystem_role'])
        self.assertNotIn('primary_emphasis', json.dumps(target))
        self.assertNotIn('anti_slop_emphasis', json.dumps(target))


if __name__ == '__main__':
    unittest.main()

"""Exercise implicit-personality variants and selected marker families end to end."""
import copy
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import check_blend
import check_soul
import graphic_markers
import make_test_pack as packer
import render_variants as renderer
import score_responses as scorer
import upgrade_soul
from _marker_metrics import scan, summary


def quiet(fn, args):
    with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
        return fn(args)


class ExpressionMarkers(unittest.TestCase):
    def setUp(self):
        self.blend = json.loads((ROOT / 'templates/blend.markers.example.json').read_text(encoding='utf-8'))
        self.cfg = renderer.load_config()
        self.axes = renderer.baseline_for(self.cfg, self.blend)
        self.tmp = tempfile.TemporaryDirectory()
        self.work = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)

    def render(self, **axes):
        return renderer.render(self.blend, {**self.axes, **axes}, self.cfg['render'])

    def manifest(self, *args):
        path = self.work / 'blend.json'
        path.write_text(json.dumps(self.blend, ensure_ascii=False), encoding='utf-8')
        code = quiet(renderer.main, [str(path), '--out', str(self.work / 'souls'), '--check', *args])
        self.assertEqual(code, 0)
        return self.work / 'souls/neri/manifest.json'

    def test_three_variants_hold_every_other_axis_and_identity_constant(self):
        path = self.manifest('--vary', 'persona_expression')
        manifest = json.loads(path.read_text())
        variants = manifest['variants']
        self.assertEqual(len(variants), 3)
        self.assertEqual({v['axes']['persona_expression'] for v in variants}, {'soft','mid','hard'})
        without_blocks = []
        for v in variants:
            self.assertTrue(set(v['differs_from_baseline']) <= {'persona_expression'})
            text = (path.parent / v['file']).read_text()
            self.assertFalse(v['check']['errors'])
            self.assertFalse([w for w in v['check']['warnings'] if 'all-caps' in w])
            before, tail = text.split('## Personality expression\n', 1)
            _, after = tail.split('## Voice\n', 1)
            without_blocks.append(before + after)
        self.assertEqual(len(set(without_blocks)), 1)

    def test_hard_caps_are_explicit_and_independent_of_primary_emphasis(self):
        text = self.render(persona_expression='hard', primary_emphasis='off')
        block = text.split('## Personality expression\n')[1].split('## Voice\n')[0]
        for cue in ('EXPRESS', 'KEEP', 'DO NOT', 'DESCRIBE'):
            self.assertIn(cue, block)
        self.assertIn('truthful identity or capability answers', block)
        self.assertIn('admitting errors', block)
        self.assertIn('when directly asked', block)
        self.assertIn('You are Neri,', text)
        self.assertNotIn('EXPRESS', self.render(persona_expression='soft'))

    def test_invalid_axis_is_rejected_before_output(self):
        self.blend['baseline']['persona_expression'] = 'strict'
        path = self.work / 'bad.json'
        path.write_text(json.dumps(self.blend))
        with self.assertRaises(SystemExit):
            quiet(renderer.main, [str(path), '--out', str(self.work/'out')])
        self.assertFalse((self.work/'out').exists())

    def test_only_selected_families_render_with_independent_blocks(self):
        for families in ([], ['emoji'], ['ascii'], ['kaomoji'], ['emoji','ascii','kaomoji']):
            with self.subTest(families=families):
                self.blend['voice']['graphic_markers']['families'] = families
                check_blend.validate(self.blend, self.cfg)
                text = self.render()
                for family, title in [('emoji','Emoji'), ('ascii','ASCII emoticons'), ('kaomoji','Kaomoji')]:
                    self.assertEqual('### '+title in text, family in families)
                if families:
                    self.assertIn('share one overall frequency', text)
                else:
                    self.assertIn('leave graphic markers out', text)

    def test_marker_frequency_does_not_follow_persona_intensity(self):
        voice = self.blend['voice']
        cue = '\n'.join(graphic_markers.render(voice['graphic_markers'], self.cfg['render'], True))
        for intensity in ('mild','moderate','strong'):
            self.assertIn(cue, self.render(intensity=intensity))
        for frequency in graphic_markers.FREQUENCIES:
            voice['graphic_markers']['frequency'] = frequency
            self.assertIn(self.cfg['render']['graphic_markers']['frequency'][frequency], self.render())

    def test_profile_shape_and_legacy_conflicts_fail_before_writes(self):
        bad = [None, [], {}, {'families':'ascii'}, {'families':['unknown']},
               {'families':['ascii','ascii']}, {'families':[{}]},
               {'families':['ascii'],'frequency':'always'},
               {'families':['ascii'],'catchphrases':['fixed']}]
        for profile in bad:
            with self.subTest(profile=profile), self.assertRaises(ValueError):
                self.blend['voice']['graphic_markers'] = profile
                check_blend.validate(self.blend, self.cfg)
        self.blend['voice']['graphic_markers'] = {'families':['ascii']}
        self.blend['voice']['markers'] = {'moderate':'Use no faces.'}
        with self.assertRaises(ValueError):
            check_blend.validate(self.blend, self.cfg)

    def test_legacy_marker_lines_remain_supported_without_inference(self):
        del self.blend['voice']['graphic_markers']
        self.blend['voice']['markers'] = {'moderate':'A discreet keyboard face in friendly reactions.'}
        check_blend.validate(self.blend, self.cfg)
        text = self.render()
        self.assertIn(self.blend['voice']['markers']['moderate'], text)
        self.assertNotIn('### ASCII emoticons', text)
        self.assertNotIn('### Emoji', text)

    def test_examples_names_and_language_lines_survive_all_levels(self):
        for language in ('match_user','es','pt-BR','ja','ar','hi'):
            self.blend['output_language'] = language
            self.blend['language'] = language
            for level in ('soft','mid','hard'):
                text = self.render(persona_expression=level)
                self.assertIn('YOU ARE Neri,', text)
                for line in renderer.language_lines(self.blend, self.cfg['render']):
                    self.assertIn(line, text)
                for pair in self.blend['examples']:
                    self.assertIn(pair['reply'], text)

    def test_pack_carries_context_and_direct_question_controls(self):
        manifest = self.manifest('--vary','persona_expression')
        out = self.work/'pack.jsonl'
        self.assertEqual(quiet(packer.main,[str(manifest),'--out',str(out),'--lang','es','--repeats','1']), 0)
        rows = [json.loads(line) for line in out.read_text().splitlines()]
        model_change = next(r for r in rows if r['prompt_id']=='model_change')
        direct = next(r for r in rows if r['prompt_id']=='personality_question')
        self.assertIs(model_change['marker_eligible'], True)
        self.assertIs(model_change['persona_description_requested'], False)
        self.assertIs(direct['persona_description_requested'], True)
        scenario = next(r for r in rows if r['prompt_id']=='scenario:persona_expression')
        self.assertIs(scenario['turns'][3]['persona_description_requested'], True)
        self.assertIs(scenario['turns'][-1]['marker_eligible'], False)

    def test_custom_prompts_without_annotations_remain_unassessed(self):
        manifest = self.manifest('--plan','baseline')
        prompts = self.work/'prompts.json'
        prompts.write_text(json.dumps({'voice':[{'id':'custom','en':'hello'}]}))
        out = self.work/'pack.jsonl'
        quiet(packer.main,[str(manifest),'--out',str(out),'--prompts',str(prompts),'--no-probes','--no-scenarios','--repeats','1'])
        rows = [json.loads(line) for line in out.read_text().splitlines()]
        self.assertTrue(all('marker_eligible' not in row for row in rows))
        prompts.write_text(json.dumps({'voice':[{'id':'custom','en':'hello','marker_eligible':'false'}]}))
        with self.assertRaises(SystemExit):
            quiet(packer.main,[str(manifest),'--out',str(out),'--prompts',str(prompts),'--no-probes','--no-scenarios'])

    def test_blind_judge_separates_paraphrase_requested_description_and_markers(self):
        manifest = self.manifest('--plan','baseline')
        rows = [
            {'run_id':'s1','kind':'voice','variant_id':'v1','prompt_id':'model_change','repeat':1,
             'prompt':'Estoy probando otro modelo.','response':'Aquí sigo, con mi lengua afilada y cariño disimulado.',
             'persona_description_requested':False,'marker_eligible':True},
            {'run_id':'s2','kind':'scenario','variant_id':'v1','prompt_id':'scenario:x','repeat':1,
             'turns':[{'text':'How would you describe your personality?','persona_description_requested':True}],
             'responses':['I have a dry sense of humor.']}
        ]
        responses = self.work/'responses.jsonl'
        responses.write_text(''.join(json.dumps(r)+'\n' for r in rows))
        judge = self.work/'judge.jsonl'; scores = self.work/'scores.json'
        quiet(scorer.main,[str(responses),'--manifest',str(manifest),'--json',str(scores),
                           '--judge-pack',str(judge),'--judge-key',str(self.work/'key.json')])
        report = json.loads(scores.read_text())
        self.assertIsNone(report['variants']['v1']['persona_recitation'])
        self.assertEqual(report['variants']['v1']['recite_leak'], 0)
        items = [json.loads(line) for line in judge.read_text().splitlines()]
        self.assertEqual({i['persona_description_requested'] for i in items}, {True,False})
        self.assertTrue(all('paraphrased trait inventories' in i['rubric'] for i in items))
        self.assertTrue(all('persona_expression' not in json.dumps(i['target_persona']) for i in items))

    def test_markdown_upgrade_adds_an_expression_level_only_when_requested(self):
        source = '# Soul\n\nYou are Neri, a playful skeptic.\n\n## Voice\n- Speak naturally.\n'
        ordinary, _, _ = upgrade_soul.upgrade(source, self.cfg)
        self.assertNotIn('## Personality expression', ordinary)
        for level in ('soft','mid','hard'):
            candidate, added, _ = upgrade_soul.upgrade(source, self.cfg, False, False, level)
            self.assertIn('persona_expression:'+level, added)
            self.assertTrue(candidate.startswith(source))
            self.assertIn(self.cfg['render']['persona_expression'][level], candidate)
            same, added, notes = upgrade_soul.upgrade(candidate, self.cfg, False, False, 'mid')
            self.assertEqual(same, candidate)
            self.assertEqual(added, [])
            self.assertTrue(any('preserved' in note for note in notes))


class MarkerMeasurement(unittest.TestCase):
    def test_previously_missed_ascii_faces_and_unicode_faces(self):
        for face in (':)', ';)', ':D', ':-)', '^_^', 'T_T', 'hola:)'):
            with self.subTest(face=face):
                self.assertTrue(scan(face)['ascii'])
        for face in ('(¬_¬)', '(＾▽＾)', '(ಠ_ಠ)', '(・_・;)', 'ヽ(>∀<☆)ノ', '¯\\_(ツ)_/¯'):
            with self.subTest(face=face):
                self.assertTrue(scan(face)['kaomoji'])
        self.assertTrue(scan('🙂')['emoji'])

    def test_code_data_urls_math_and_ordinary_parentheticals_are_not_markers(self):
        for text in ('https://example.com', '12:30', 'x = (a + b)', '説明（日本語）', '(ω)', '(ω + ω)', '(Дадим ответ)',
                     'Use `:)` as an example.', '```python\nprint(":)")\n```',
                     '~~~text\n:D\n~~~', '{"example": ":)"}', '```text\n:)',
                     'No decorations here.'):
            with self.subTest(text=text):
                self.assertFalse(any(scan(text).values()))

    def test_faces_are_not_double_counted_between_families(self):
        found = scan('Bien ;) (＾▽＾) 🙂')
        self.assertEqual({kind:len(tokens) for kind,tokens in found.items()}, {'ascii':1,'kaomoji':1,'emoji':1})

    def test_selected_family_and_eligibility_have_separate_denominators(self):
        rows = [
            {'prompt_id':'greet','marker_eligible':True,'response':'Hola :)'},
            {'prompt_id':'thanks','marker_eligible':True,'response':'Bien 🙂'},
            {'prompt_id':'formal','marker_eligible':False,'response':'Recibido.'},
            {'prompt_id':'unknown','response':'(¬_¬)'}]
        result = summary(rows, {'families':['ascii']})
        self.assertEqual(result['marker_eligible_share'], 1)
        self.assertEqual(result['marker_selected_eligible_share'], .5)
        self.assertEqual(result['marker_ineligible_share'], 0)
        self.assertEqual(result['marker_unselected_share'], .5)
        self.assertEqual(result['marker_unassessed_n'], 1)
        self.assertIsNone(summary(rows)['marker_unselected_share'])
        self.assertIsNone(summary([{'response':'Hi :)'}])['marker_eligible_share'])

    def test_repeats_of_one_prompt_do_not_become_a_marker_tic(self):
        rows = [{'prompt_id':'greeting','response':'Hola :)'} for _ in range(3)]
        self.assertEqual(summary(rows)['marker_tics'], [])
        for i,row in enumerate(rows): row['prompt_id'] = str(i)
        self.assertEqual(summary(rows)['marker_tics'], ['ascii: :)'])

    def test_scenario_counts_ascii_and_preserves_turn_annotations(self):
        rows = [{'kind':'scenario','prompt_id':'s','turns':[
            {'text':'Hi','marker_eligible':True}, {'text':'Formal text','marker_eligible':False}],
            'responses':['Hi :)','Received.']}]
        result = scorer.scenario_metrics(rows, {'families':['ascii']})
        self.assertEqual(result['marker_families']['ascii'], .5)
        self.assertEqual(result['marker_selected_eligible_share'], 1)
        self.assertEqual(result['marker_ineligible_share'], 0)
        self.assertEqual(result['drift_markers'], 1)


if __name__ == '__main__':
    unittest.main()

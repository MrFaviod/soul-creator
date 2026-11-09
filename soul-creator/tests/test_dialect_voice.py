"""Regional voice is optional, always subordinate, and testable against off/single."""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import dialect_voice
import render_variants
import check_soul


class Catalog(unittest.TestCase):
    def test_coverage_and_consistent_schema(self):
        entries = json.loads(dialect_voice.CATALOG.read_text(encoding='utf-8'))['entries']
        ids = [e['id'] for e in entries]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertGreaterEqual(len(ids), 60)
        languages = {e['language'].split('-')[0] for e in entries}
        for expected in ('es','en','gn','zh','ru','pt','ar','ja','fr','de','ko','hi','ur'):
            self.assertIn(expected, languages)
        for row in entries:
            self.assertTrue(all(row.get(x) for x in ('name','id','language','signals')))
        self.assertIn('es-py-jopara', ids)
        self.assertIn('zh-yue-cantonese', ids)
        self.assertIn('ru-northern', ids)

    def test_original_unchanged_if_no_dialect(self):
        spec = json.loads((ROOT/'templates/blend.example.json').read_text())
        cfg = render_variants.load_config()
        base = render_variants.baseline_for(cfg, spec)
        a = json.loads(json.dumps(spec)); a['voice'].pop('dialect',None)
        b = json.loads(json.dumps(spec)); b['voice']['dialect']={'mode':'none'}
        self.assertEqual(render_variants.render(a,base,cfg['render']), render_variants.render(b,base,cfg['render']))

    def test_single_and_strength_without_displacing_persona(self):
        spec = json.loads((ROOT/'templates/blend.example.json').read_text())
        cfg = render_variants.load_config()
        base = render_variants.baseline_for(cfg, spec)
        output = render_variants.render(spec,base,cfg['render'])
        self.assertIn('Español rioplatense argentino',output)
        self.assertIn('## Archetype',output)
        self.assertIn('below the established personality',output)
        self.assertIn('## Substance and expression',output)
        with tempfile.TemporaryDirectory() as d:
            candidate=Path(d)/'SOUL.md';candidate.write_text(output,encoding='utf8')
            self.assertFalse([m for lv,m in check_soul.check(candidate,True,cfg) if lv == 'ERROR'])

    def test_blend_and_counterfactuals(self):
        spec = json.loads((ROOT/'templates/blend.example.json').read_text())
        spec['voice']['dialect']={'mode':'blend','primary':'es-ar-rioplatense',
                                   'secondary':['es-mx-urbano','es-es-peninsular'],
                                   'strength':'subtle','code_switch':'off'}
        cfg = render_variants.load_config()
        base = render_variants.baseline_for(cfg, spec)
        mixed = render_variants.render(spec,base,cfg['render'])
        solo = render_variants.render(spec,{**base,'regional_voice':'single'},cfg['render'])
        plain = render_variants.render(spec,{**base,'regional_voice':'off'},cfg['render'])
        self.assertIn('Español mexicano urbano',mixed)
        self.assertIn('Español peninsular',mixed)
        self.assertNotIn('Español mexicano urbano',solo)
        self.assertNotIn('Español rioplatense argentino',plain)
        self.assertIn(spec['anchor']['gloss'],mixed)
        self.assertIn(spec['anchor']['gloss'],solo)
        self.assertIn(spec['anchor']['gloss'],plain)
        with tempfile.TemporaryDirectory() as d:
            blend = Path(d)/'blend.json';blend.write_text(json.dumps(spec),encoding='utf8')
            from contextlib import redirect_stdout
            from io import StringIO
            stream=StringIO()
            with redirect_stdout(stream):
                code=render_variants.main([str(blend),'--out',str(Path(d)/'souls'),'--vary','regional_voice','--check'])
            result=json.loads(stream.getvalue()); self.assertEqual(code,0)
            self.assertEqual(len(result['variants']),3)
            self.assertEqual(set(v['differs'].get('regional_voice','configured') for v in result['variants']),{'configured','single','off'})

    def test_single_skips_duplicate_dominant_only(self):
        spec = json.loads((ROOT/'templates/blend.example.json').read_text())
        cfg = render_variants.load_config()
        base = render_variants.baseline_for(cfg, spec)
        with self.assertRaises(render_variants.SkipVariant):
            render_variants.render(spec,{**base,'regional_voice':'single'},cfg['render'])

    def test_cross_language_blend_without_code_switch(self):
        case = {'mode':'blend','primary':'es-py-urbano', 'secondary':['en-uk-contemporary']}
        line = dialect_voice.render_dialect(case, 'es')[0]
        self.assertIn('requested reply language', line)
        self.assertIn('Do not switch languages', line)
        self.assertNotIn('British spelling and natural usage', line)
        case['code_switch']='contextual'
        text = dialect_voice.render_dialect(case,'es')[0]
        self.assertIn('allowed occasional code-switching',text)
        self.assertIn('requested language dominant',text)

    def test_jopara_single_is_contact_not_token_spray(self):
        text=dialect_voice.render_dialect({'mode':'single','primary':'es-py-jopara'},'es')[0]
        self.assertIn('code-mixing',text)
        self.assertIn('authentic',text)
        self.assertIn('not a standardized single dialect or random translated inserts',text)

    def test_cross_language_accent_preserves_spanish(self):
        line = dialect_voice.render_dialect({'mode':'single','primary':'zh-yue-cantonese'},'es')[0]
        self.assertIn('Cantonés', line)
        self.assertIn('requested language', line)
        self.assertIn('normal grammar, spelling, pronouns', line)
        self.assertNotIn('Cantonese grammar and colloquial written conventions', line)
        self.assertIn('Do not switch languages', line)
        self.assertNotIn('粵語 grammar', line)
        # This formerly failed even though the reply language is never changed.
        russian = dialect_voice.render_dialect({'mode':'single','primary':'ru-northern'},'es')[0]
        self.assertIn('Ruso dialectal septentrional', russian)
        self.assertIn('cross-language accent', russian)

    def test_cross_language_accent_works_with_sinitic_language_boundaries(self):
        cantonese = dialect_voice.render_dialect({'mode':'single','primary':'zh-yue-cantonese'},'zh')[0]
        self.assertIn('cross-language accent', cantonese)  # generic zh is not automatically Cantonese
        mandarin = dialect_voice.render_dialect({'mode':'single','primary':'zh-mandarin-standard'},'zh-yue')[0]
        self.assertIn('cross-language accent', mandarin)
        native = dialect_voice.render_dialect({'mode':'single','primary':'zh-yue-cantonese'},'zh-yue')[0]
        self.assertIn('authentic written usage', native)

    def test_match_user_is_conditional_without_switching_languages(self):
        line = dialect_voice.render_dialect({'mode':'single','primary':'zh-yue-cantonese'},'match_user')[0]
        self.assertIn('When the requested reply language differs', line)
        self.assertIn('keep the requested language', line)
        self.assertIn('Cantonese grammar and colloquial written conventions', line)  # only in conditional native branch
        self.assertIn('Do not switch languages', line)

    def test_explicit_accent_application_and_custom_cues(self):
        source = {'name':'Documented custom accent','language':'en',
                  'signals':'Native dialect morphology where appropriate.',
                  'accent_signals':'Use only the speaker-provided rhythm reference.'}
        line = dialect_voice.render_dialect({'mode':'single','primary':source,'application':'accent'},'en')[0]
        self.assertIn('speaker-provided rhythm reference', line)
        self.assertNotIn('Native dialect morphology', line)
        self.assertIn('normal grammar', line)

    def test_full_render_foreign_accent_does_not_override_language(self):
        spec = json.loads((ROOT/'templates/blend.example.json').read_text())
        spec['voice']['dialect'] = {'mode':'single', 'primary':'zh-yue-cantonese',
                                    'strength':'subtle', 'application':'auto', 'code_switch':'off'}
        cfg = render_variants.load_config()
        text = render_variants.render(spec, render_variants.baseline_for(cfg,spec),cfg['render'])
        self.assertIn('Reply in Spanish unless', text)
        self.assertIn('treat cantonés', text.casefold())
        self.assertNotIn('Cantonese grammar and colloquial written conventions', text)
        self.assertIn('## Archetype', text)
        self.assertIn('you are ciro', text.casefold())
        self.assertIn('Preserve the requested reply language', text)

    def test_invalid_values_are_not_silent(self):
        invalid=[{'mode':'single','primary':'es-fake'},
                 {'mode':'single','primary':'es-mx-urbano','secondary':['es-ar-rioplatense']},
                 {'mode':'blend','primary':'es-mx-urbano','secondary':[]},
                 {'mode':'blend','primary':'es-mx-urbano','secondary':['es-mx-urbano']},
                 {'mode':'blend','primary':'es-mx-urbano','secondary':['es-ar-rioplatense']*3},
                 {'mode':'none','primary':'en-uk-contemporary'},
                 {'mode':'wat'},
                 {'mode':'single','primary':'es-mx-urbano','strength':'999'},
                 {'mode':'single','primary':'es-mx-urbano','application':'xyz'},
                 {'mode':'single','primary':{'name':'bad','language':'es','signals':'test','accent_signals':''}}]
        for case in invalid:
            with self.subTest(case=case), self.assertRaises(ValueError):
                dialect_voice.render_dialect(case,'es')

    def test_custom_not_closed_catalog(self):
        custom={'name':'Custom documented dialect','language':'en','signals':'Use speaker-supplied authentic idioms selectively.'}
        text=dialect_voice.render_dialect({'mode':'single','primary':custom},'en')[0]
        self.assertIn('Custom documented dialect',text)
        self.assertIn('speaker-supplied authentic idioms',text)


if __name__=='__main__':unittest.main()

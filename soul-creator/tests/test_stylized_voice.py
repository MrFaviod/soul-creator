"""Literary accents should never displace the core persona or regional base."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
import render_variants
import stylized_voice
import check_soul


class LiteraryCatalog(unittest.TestCase):
    def test_inventory_covers_all_requested_families(self):
        entries = json.loads(stylized_voice.CATALOG.read_text())['entries']
        self.assertGreaterEqual(len(entries), 45)
        self.assertEqual(len({row['id'] for row in entries}), len(entries))
        for group in stylized_voice.CATEGORIES:
            self.assertGreaterEqual(sum(row['category']==group for row in entries), 10)
        for row in entries:
            self.assertTrue(all(row.get(k) for k in ('id','category','name','signals')))
            self.assertLess(len(row['signals']),260)
        ids = {row['id'] for row in entries}
        for key in ('fantasy-elf-court','myth-norse-skald','hist-spanish-golden-age','char-wise-wizard'):
            self.assertIn(key,ids)

    def test_render_standalone_and_mix(self):
        out = stylized_voice.render_stylization({'mode':'single','primary':'myth-greek-oracle','strength':'natural'})[0]
        self.assertIn('Oráculo de la Grecia mítica',out)
        self.assertIn('existing archetype',out)
        self.assertIn('not a real-world accent',out)
        both = stylized_voice.render_stylization({'mode':'blend','primary':'fantasy-bard','secondary':['hist-spanish-golden-age'],'strength':'subtle'},regional_enabled=True)[0]
        self.assertIn('Bardo itinerante',both)
        self.assertIn('Siglo de Oro español',both)
        self.assertIn('requested reply language and its natural grammar/address',both)
        self.assertIn('never stack',both)

    def test_custom_reference_without_identity_override(self):
        custom={'name':'Un detective espacial original','category':'character','signals':'Accurate descriptions, wry understatement and fast observations.'}
        x = stylized_voice.render_stylization({'mode':'single','primary':custom},regional_enabled=True)[0]
        self.assertIn('Un detective espacial original',x)
        self.assertIn('not a real-world accent',x)
        self.assertRaises(ValueError,stylized_voice.render_stylization,{'mode':'single','primary':{'name':'z','category':'unknown','signals':'u'}})

    def test_invalid_values_rejected(self):
        cases = [
            {'mode':'none','primary':'fantasy-bard'},
            {'mode':'single','primary':'fantasy-bard','secondary':['myth-greek-oracle']},
            {'mode':'blend','primary':'fantasy-bard','secondary':[]},
            {'mode':'blend','primary':'fantasy-bard','secondary':['fantasy-bard']},
            {'mode':'blend','primary':'fantasy-bard','secondary':['myth-norse-skald','myth-greek-oracle']},
            {'mode':'single','primary':'not-in-catalog'},
            {'mode':'single','primary':'fantasy-bard','strength':'too much'},
            {'mode':'unsupported'},
            'what',
        ]
        for spec in cases:
            with self.subTest(spec=spec), self.assertRaises(ValueError):
                stylized_voice.render_stylization(spec)

    def test_variant_axes_control_one_dimension_at_a_time(self):
        blend=json.loads((ROOT/'templates/blend.example.json').read_text())
        blend['voice']['stylization']={'mode':'blend','primary':'char-wise-wizard','secondary':['myth-norse-skald'],'strength':'subtle'}
        cfg=render_variants.load_config();base=render_variants.baseline_for(cfg,blend)
        configured=render_variants.render(blend,base,cfg['render'])
        alone=render_variants.render(blend,{**base,'stylized_voice':'single'},cfg['render'])
        off=render_variants.render(blend,{**base,'stylized_voice':'off'},cfg['render'])
        self.assertIn('Mago consejero',configured)
        self.assertIn('Escaldo nórdico',configured)
        self.assertNotIn('Escaldo nórdico',alone)
        self.assertNotIn('Mago consejero',off)
        for text in (configured,alone,off):
            self.assertIn('Español rioplatense argentino',text)
            self.assertIn('## Archetype',text)
            self.assertIn('## Substance and expression',text)
            with tempfile.TemporaryDirectory() as td:
                path=Path(td)/'SOUL.md';path.write_text(text,encoding='utf8')
                self.assertFalse([e for level,e in check_soul.check(path,True,cfg) if level=='ERROR'])
        with tempfile.TemporaryDirectory() as td:
            blend_path=Path(td)/'blend.json';blend_path.write_text(json.dumps(blend,ensure_ascii=False))
            from contextlib import redirect_stdout
            from io import StringIO
            stdout=StringIO()
            with redirect_stdout(stdout):
                exit_code=render_variants.main([str(blend_path),'--out',str(Path(td)/'out'),'--vary','stylized_voice','--check'])
            self.assertEqual(exit_code,0)
            result=json.loads(stdout.getvalue())
            self.assertEqual(len(result['variants']),3)

    def test_prevent_accumulating_marked_styles_and_two_blends(self):
        blend=json.loads((ROOT/'templates/blend.example.json').read_text())
        cfg=render_variants.load_config();base=render_variants.baseline_for(cfg,blend)
        blend['voice']['dialect']['strength']='marked'
        blend['voice']['stylization']['strength']='marked'
        with self.assertRaisesRegex(ValueError,'cannot both be marked'):
            render_variants.render(blend,base,cfg['render'])
        blend['voice']['stylization']['strength']='natural'
        blend['voice']['dialect']={'mode':'blend','primary':'es-ar-rioplatense','secondary':['es-mx-urbano'],'strength':'natural'}
        blend['voice']['stylization']={'mode':'blend','primary':'fantasy-bard','secondary':['hist-victorian-letters'],'strength':'natural'}
        with self.assertRaisesRegex(ValueError,'two full voice blends'):
            render_variants.render(blend,base,cfg['render'])

    def test_literary_influence_never_changes_output_language(self):
        blend=json.loads((ROOT/'templates/blend.example.json').read_text())
        blend['output_language']='en'
        blend['language']='English'
        blend['voice']['dialect']={'mode':'none'}
        blend['voice']['stylization']={'mode':'single','primary':'hist-spanish-golden-age'}
        cfg=render_variants.load_config();base=render_variants.baseline_for(cfg,blend)
        result=render_variants.render(blend,base,cfg['render'])
        self.assertIn('Reply in English',result)
        self.assertIn('Siglo de Oro español',result)
        self.assertNotIn('Reply in Spanish',result)
        self.assertIn('Keep the established reply language',result)

    def test_unconfigured_style_keeps_original_byte_identical(self):
        blend=json.loads((ROOT/'templates/blend.example.json').read_text())
        cfg=render_variants.load_config();base=render_variants.baseline_for(cfg,blend)
        a=json.loads(json.dumps(blend));a['voice'].pop('stylization',None)
        b=json.loads(json.dumps(blend));b['voice']['stylization']={'mode':'none'}
        self.assertEqual(render_variants.render(a,base,cfg['render']),render_variants.render(b,base,cfg['render']))

    def test_no_style_skip_only_for_counterfactuals(self):
        blend=json.loads((ROOT/'templates/blend.example.json').read_text())
        blend['voice']['stylization']={'mode':'none'}
        cfg=render_variants.load_config();base=render_variants.baseline_for(cfg,blend)
        self.assertNotIn('writing inflection',render_variants.render(blend,base,cfg['render']))
        with self.assertRaises(render_variants.SkipVariant):
            render_variants.render(blend,{**base,'stylized_voice':'off'},cfg['render'])


if __name__=='__main__':unittest.main()

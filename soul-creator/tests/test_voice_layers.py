"""Graded voices preserve user-selected language and surface signature changes."""
import copy
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import voice_layers
import render_variants
import check_soul
import dialect_voice


def layer(kind, primary, strength):
    return {'kind':kind, 'primary':primary, 'strength':strength}


class GradedVoices(unittest.TestCase):
    def setUp(self):
        self.layers=[layer('dialect','es-ar-rioplatense','strong'),
                     layer('stylization','char-noir-narrator','medium'),
                     layer('dialect','fr-fr-contemporary','medium'),
                     layer('dialect','zh-yue-cantonese','low')]

    def test_four_layers_with_independent_strengths(self):
        voice={'layers':self.layers}
        analysis=voice_layers.analyze(voice,'es')
        self.assertFalse(analysis['needs_choice'])
        text='\n'.join(voice_layers.render(voice,'es')[0])
        for name in ('Español rioplatense','Francés','Canton','noir'):
            self.assertIn(name.lower(),text.lower())
        self.assertIn('Low influence',text)
        self.assertIn('No code-switching',text)
        self.assertTrue(analysis['notes'])

    def test_signature_replacement_requires_informed_choice(self):
        signature={'description':'A sharply regional voice associated with this reference.',
                   'source':'user reference', 'layers':[self.layers[0]]}
        voice={'signature':signature,'layers':[layer('dialect','es-es-peninsular','strong')]}
        report=voice_layers.analyze(voice,'es')
        self.assertTrue(report['needs_choice']); self.assertIn('replaced',report['conflicts'][0])
        voice['compatibility']={'acknowledged':True,'reason':'The user explicitly requested a Peninsular reinterpretation.'}
        self.assertFalse(voice_layers.analyze(voice,'es')['needs_choice'])

    def test_softening_signature_is_a_visible_change(self):
        voice={'signature':{'description':'Strong regional delivery','source':'original SOUL',
                'layers':[self.layers[0]]}, 'layers':[layer('dialect','es-ar-rioplatense','medium')]}
        self.assertTrue(voice_layers.analyze(voice,'es')['needs_choice'])

    def test_signature_cues_cannot_change_behind_the_same_custom_name(self):
        original=layer('dialect',{'name':'Chosen regional voice','language':'es','signals':'Natural voseo and brisk phrasing.'},'strong')
        replacement=copy.deepcopy(original); replacement['primary']['signals']='Formal usted and elaborate phrases.'
        voice={'signature':{'description':'The established regional speech','source':'original SOUL','layers':[original]},
               'layers':[replacement]}
        self.assertTrue(voice_layers.analyze(voice,'es')['needs_choice'])

    def test_acknowledgement_must_be_boolean_not_a_truthy_string(self):
        with self.assertRaises(ValueError):
            voice_layers.analyze({'layers':self.layers,'compatibility':{'acknowledged':'false'}},'es')

    def test_proposed_reinterpretation_remains_pending_in_manifest(self):
        blend=json.loads((ROOT/'templates/blend.layers.example.json').read_text())
        blend['voice']['layers']=[layer('dialect','es-es-peninsular','strong')]
        blend['voice']['compatibility']={'proposed':True}
        with tempfile.TemporaryDirectory() as tmp:
            bp=Path(tmp)/'blend.json';bp.write_text(json.dumps(blend))
            with redirect_stdout(io.StringIO()):
                result=render_variants.main([str(bp),'--out',str(Path(tmp)/'out'),'--plan','baseline','--check'])
            self.assertEqual(result,0)
            manifest=json.loads((Path(tmp)/'out'/'ciro'/'manifest.json').read_text())
            self.assertTrue(manifest['voice_compatibility']['needs_choice'])
            self.assertFalse(manifest['voice_compatibility']['acknowledged'])
            self.assertTrue(any('pending' in note for note in manifest['warnings']))

    def test_unmodified_signature_is_default(self):
        voice={'signature':{'description':'Regional delivery','source':'original SOUL','layers':[self.layers[0]]}}
        self.assertFalse(voice_layers.analyze(voice,'es')['needs_choice'])
        self.assertIn('Español rioplatense','\n'.join(voice_layers.render(voice,'es')[0]))

    def test_explicit_comic_combination_is_possible(self):
        shakespeare={'name':'Shakespeare-inspired rhetoric','category':'historical',
                     'signals':'Readable dramatic antithesis and playful rhetorical turns, in the requested language.'}
        style=layer('stylization',shakespeare,'strong')
        voice={'signature':{'description':'Strong dramatic diction','source':'archetype','layers':[style]},
               'layers':[style,self.layers[0]],
               'compatibility':{'acknowledged':True,'reason':'User deliberately asked for this comic combination.'}}
        self.assertFalse(voice_layers.analyze(voice,'es')['needs_choice'])
        text='\n'.join(voice_layers.render(voice,'es')[0])
        self.assertIn('Shakespeare-inspired rhetoric',text); self.assertIn('Español rioplatense',text)

    def test_legacy_subtle_becomes_medium_not_new_low(self):
        resolved=voice_layers.resolve_layer(layer('dialect','fr-fr-contemporary','subtle'))
        self.assertEqual(resolved['strength'],'medium')
        low='\n'.join(voice_layers.render({'layers':[self.layers[-1]]},'es')[0])
        self.assertIn('words or short turns',low); self.assertIn('Do not adopt its pronouns',low)

    def test_independent_output_languages_do_not_become_source_language(self):
        for language in ('es','pt-BR','en','ar','ja','hi','my','match_user'):
            with self.subTest(language=language):
                text='\n'.join(voice_layers.render({'layers':[self.layers[2],self.layers[3]]},language)[0])
                self.assertIn('requested reply language always wins',text)
                self.assertNotIn('Reply in French',text)
                self.assertNotIn('Reply in Cantonese',text)

    def test_custom_secondary_signals_are_not_discarded(self):
        dialect={'mode':'blend','primary':'es-ar-rioplatense', 'secondary':[
            {'name':'Custom phrasing','language':'es','signals':'An occasional measured acknowledgement.'}]}
        a=dialect_voice.render_dialect(dialect,'es')
        dialect['secondary'][0]['signals']='A brief rhetorical contrast.'
        b=dialect_voice.render_dialect(dialect,'es')
        self.assertNotEqual(a,b); self.assertIn('rhetorical contrast',' '.join(b))

    def test_invalid_compositions_fail_with_actionable_errors(self):
        cases=[{'layers':[self.layers[0],layer('dialect','es-es-peninsular','strong')]},
               {'layers':[self.layers[0],self.layers[0]]},
               {'layers':self.layers, 'dialect':{'mode':'single','primary':'es-ar-rioplatense'}},
               {'layers':[layer('dialect','fr-fr-contemporary','very strong')]}]
        for voice in cases:
            with self.subTest(voice=voice),self.assertRaises(ValueError): voice_layers.analyze(voice,'es')

    def test_render_and_axis_ablations_keep_other_layers(self):
        blend=json.loads((ROOT/'templates/blend.example.json').read_text())
        blend['voice'].pop('dialect');blend['voice'].pop('stylization');blend['voice']['layers']=self.layers
        cfg=render_variants.load_config();axes=render_variants.baseline_for(cfg,blend)
        for language in ('es','pt-BR','en','ar','ja'):
            blend['output_language']=language;blend['language']=language
            full=render_variants.render(blend,axes,cfg['render'])
            self.assertIn('Reply in '+language,full)
            with tempfile.TemporaryDirectory() as td:
                p=Path(td)/'SOUL.md';p.write_text(full)
                self.assertFalse([msg for level,msg in check_soul.check(p,True,cfg) if level=='ERROR'])
        no_regions=render_variants.render(blend,{**axes,'regional_voice':'off'},cfg['render'])
        self.assertIn('noir',no_regions.lower()); self.assertNotIn('Canton',no_regions)
        dominant=render_variants.render(blend,{**axes,'regional_voice':'single'},cfg['render'])
        self.assertIn('Español rioplatense',dominant); self.assertNotIn('Canton',dominant)
        self.assertIn('noir',dominant.lower())


if __name__=='__main__': unittest.main()

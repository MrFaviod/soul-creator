"""Continuity/naturalness controls and sequence-level evaluation regressions."""
import copy
import io
import json
import re
import sys
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
import check_blend
import make_test_pack
import render_variants as renderer
import score_responses as scorer
import upgrade_soul
from _conversation_metrics import shape, summary, context


def quiet(fn, args):
    with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
        return fn(args)


class ConversationalControls(unittest.TestCase):
    def setUp(self):
        self.blend=json.loads((ROOT/'templates/blend.example.json').read_text())
        self.cfg=renderer.load_config()
        self.base=renderer.baseline_for(self.cfg,self.blend)
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.work=Path(self.tmp.name)

    def render(self, **axes):
        return renderer.render(self.blend,{**self.base,**axes},self.cfg['render'])

    def manifest(self, *args):
        path=self.work/'blend.json'; path.write_text(json.dumps(self.blend))
        self.assertEqual(quiet(renderer.main,[str(path),'--out',str(self.work/'souls'),'--check',*args]),0)
        return self.work/'souls/ciro/manifest.json'

    def test_four_independent_conditions_with_identity_unchanged(self):
        path=self.manifest('--plan','grid','--vary','voice_lock','humanize','--max','4')
        manifest=json.loads(path.read_text())
        self.assertEqual(len(manifest['variants']),4)
        for item in manifest['variants']:
            text=(path.parent/item['file']).read_text()
            self.assertFalse(item['check']['errors'])
            self.assertEqual('## Voice lock' in text,item['axes']['voice_lock']=='on')
            self.assertEqual('## Conversational naturalness' in text,item['axes']['humanize']=='on')
            self.assertEqual(item['axes']['identity_lock'],'off')
            self.assertLessEqual(set(item['differs_from_baseline']),{'voice_lock','humanize'})
            for pair in self.blend['examples']: self.assertIn(pair['reply'],text)

    def test_lock_is_not_an_identity_swap_rejection_or_marker_quota(self):
        locked=self.render(identity_lock='off',humanize='off')
        block=locked.split('## Voice lock\n')[1].split('\n## ',1)[0]
        self.assertIn(self.blend['voice']['continuity'],block)
        self.assertIn('progress updates',block)
        self.assertIn('selected dialect strengths',block)
        self.assertNotIn('no one else',block)
        self.assertIn('KEEP',block); self.assertIn('RETURN',block)
        self.assertNotIn('KEEP',self.render(primary_emphasis='off'))
        plain=self.render(voice_lock='off',humanize='off')
        self.assertEqual(re.sub(r'^## Voice lock\n.*?(?=^## |\Z)','',locked,flags=re.M|re.S),plain)

    def test_humanize_preserves_custom_shape_without_stacking_fallback(self):
        on=self.render(); off=self.render(humanize='off')
        self.assertEqual(on.count(self.blend['voice']['reply_shape']),1)
        block=on.split('## Conversational naturalness\n')[1].split('\n## ',1)[0]
        self.assertEqual(re.sub(r'^## Conversational naturalness\n.*?(?=^## |\Z)','',on,flags=re.M|re.S),off)
        del self.blend['voice']['reply_shape']
        self.assertNotIn(self.cfg['render']['reply_shape_default'],self.render())
        self.assertIn(self.cfg['render']['reply_shape_default'],self.render(humanize='off'))
        self.blend['voice']['reply_shape']=''
        self.assertNotIn(self.cfg['render']['reply_shape_default'],self.render(humanize='off'))

    def test_legacy_blend_without_continuity_keeps_its_voice(self):
        del self.blend['voice']['continuity']
        check_blend.validate(self.blend,self.cfg)
        for language in ('match_user','es','pt-BR','ar','ja'):
            self.blend['output_language']=language
            for line in renderer.language_lines(self.blend,self.cfg['render']):
                self.assertIn(line,self.render())
            self.assertIn(self.blend['voice']['base'][1],self.render())

    def test_marker_subsections_remain_inside_voice_in_all_four_conditions(self):
        self.blend=json.loads((ROOT/'templates/blend.markers.example.json').read_text())
        for lock in ('on','off'):
            for humanize in ('on','off'):
                text=self.render(voice_lock=lock,humanize=humanize)
                prefix=text.split('### Graphic markers',1)[0]
                self.assertEqual(re.findall(r'^## (.+)$',prefix,re.M)[-1],'Voice')
                self.assertEqual(text.count('### ASCII emoticons'),1)

    def test_invalid_continuity_and_axes_fail_before_writing(self):
        for value in ('',False,[],None):
            with self.subTest(value=value),self.assertRaises(ValueError):
                self.blend['voice']['continuity']=value
                check_blend.validate(self.blend,self.cfg)
        self.blend['voice']['continuity']='Keep the dry cadence.'
        for key in ('voice_lock','humanize'):
            with self.assertRaises(ValueError): self.render(**{key:'hard'})

    def test_markdown_opt_in_upgrade_is_idempotent_and_preserves_source(self):
        raw='# Soul\n\nYou are Ren, a patient observer.\n\n## Voice\n- Speak gently.\n\n## Quirks\n- You enjoy puzzles.\n'
        ordinary,_,_=upgrade_soul.upgrade(raw,self.cfg)
        self.assertNotIn('## Voice lock',ordinary)
        candidate,added,_=upgrade_soul.upgrade(raw,self.cfg,voice_lock=True,humanize=True)
        self.assertEqual(added,['anti_slop','voice_lock','humanize'])
        self.assertIn('## Voice\n- Speak gently.',candidate)
        self.assertIn('## Quirks\n- You enjoy puzzles.',candidate)
        same,added,_=upgrade_soul.upgrade(candidate,self.cfg,voice_lock=True,humanize=True)
        self.assertEqual(same,candidate); self.assertFalse(added)
        custom=raw+'\n## Voice lock\nUna voz reservada.\n\n## Naturalidad conversacional\nHablar según el momento.\n'
        same,added,notes=upgrade_soul.upgrade(custom,self.cfg,False,False,voice_lock=True,humanize=True)
        self.assertEqual(same,custom); self.assertFalse(added)
        self.assertTrue(any('preserved' in note for note in notes))

    def test_pack_carries_context_and_comparable_phase_probes(self):
        manifest=self.manifest('--plan','baseline')
        out=self.work/'pack.jsonl'
        quiet(make_test_pack.main,[str(manifest),'--out',str(out),'--lang','es','--repeats','1','--no-probes',
                                  '--scenarios','voice_continuity','conversational_naturalness'])
        rows=[json.loads(line) for line in out.read_text().splitlines()]
        scene=next(row for row in rows if row['prompt_id']=='scenario:voice_continuity')
        probes=[t for t in scene['turns'] if t.get('voice_probe')]
        self.assertEqual({t['phase'] for t in probes},{'before_task','during_task','after_task'})
        self.assertTrue(all(t['expect_lang']=='es' for t in scene['turns']))
        self.assertTrue(any(t.get('structure_requested') and not t.get('marker_eligible',True) for t in scene['turns']))
        self.assertIn('dependency_timeout',scene['turns'][5]['text'])
        for bad in ({'phase':'tomorrow'},{'voice_probe':'yes'},{'conversation_act':[]},{'question_needed':1}):
            with self.assertRaises(ValueError): context(bad)


class ConversationEvaluation(unittest.TestCase):
    def test_different_words_same_structure_are_grouped(self):
        texts=['Para que sirva, yo separaría tres cosas:', 'Yo pondría tres cosas:', 'Antes de construir, decidiría tres cosas:']
        outputs=[text+'\n\n- Uno\n- Dos\n- Tres\n\n¿Qué preferís?' for text in texts]
        self.assertEqual({shape(text) for text in outputs},{'prose>list>question'})
        rows=[{'response':outputs[i%3],'conversation_act':act} for i,act in enumerate(['sharing','question','closing','correction','sharing'])]
        result=summary(rows)
        self.assertEqual(len(result['review_windows']),1)
        self.assertIsNone(result['structural_monotony']); self.assertIsNone(result['naturalness'])

    def test_plain_prose_and_unknown_intent_are_not_marked_as_rigid_plans(self):
        rows=[{'response':'A complete thought.','conversation_act':act} for act in ['sharing','closing']*3]
        self.assertFalse(summary(rows)['review_windows'])
        self.assertFalse(summary([{'response':'Intro\n- A\n\nQuestion?'}]*6)['review_windows'])

    def test_scripts_code_and_data_do_not_require_word_lists(self):
        for text in ('反応。\n\n- 一\n- 二\n\nどうする？', 'תגובה\n\n- א\n- ב\n\nמה דעתך?', 'مقدمة\n\n- أ\n- ب\n\nما رأيك؟'):
            self.assertEqual(shape(text),'prose>list>question')
        self.assertEqual(shape('```text\nWhy?\n- item\n```'),'code')
        self.assertEqual(shape('{"question": "why?"}'),'data')
        self.assertEqual(shape('~~~text\nWhy?'),'code')

    def test_blind_whole_conversations_and_repeats_stay_separate(self):
        turns=[{'text':'An observation','conversation_act':'sharing','phase':'before_task','voice_probe':True},
               {'text':'A technical task','conversation_act':'task','phase':'during_task'},
               {'text':'Another observation','conversation_act':'sharing','phase':'after_task','voice_probe':True}]
        rows=[{'run_id':f'{v}|{repeat}','kind':'scenario','variant_id':v,'prompt_id':'scenario:test','repeat':repeat,
               'turns':turns,'responses':[f'{v} reply {i}' for i in range(3)]}
              for v in ('hidden-a','hidden-b') for repeat in (1,2)]
        # Include an incomplete history: it must never become a judged conversation.
        rows.append({**rows[0],'run_id':'incomplete','responses':['partial'],'completion_status':'incomplete'})
        with tempfile.TemporaryDirectory() as directory:
            work=Path(directory); responses=work/'responses.jsonl'; judge=work/'judge.jsonl'; scores=work/'scores.json'
            responses.write_text(''.join(json.dumps(row)+'\n' for row in rows))
            args=[str(responses),'--json',str(scores),'--judge-pack',str(judge),'--judge-key',str(work/'key.json')]
            quiet(scorer.main,args)
            items=[json.loads(line) for line in judge.read_text().splitlines()]
            conversations=[item for item in items if item['kind']=='conversation']
            self.assertEqual(len(conversations),2)
            for item in conversations:
                self.assertEqual([t['user'] for t in item['turns']],[t['text'] for t in turns])
                self.assertEqual(item['turns'][-1]['phase'],'after_task')
                self.assertNotIn('variant_id',item)
                self.assertNotIn('system',item)
                self.assertIn('structural_monotony',item['rubric'])
            report=json.loads(scores.read_text())
            self.assertEqual(report['errors'],1)
            self.assertEqual(len(report['scenarios']['hidden-a']['conversation_structure']),2)
            self.assertIsNone(report['scenarios']['hidden-a']['voice_continuity'])
            quiet(scorer.main,args+['--judge-all-repeats'])
            items=[json.loads(line) for line in judge.read_text().splitlines()]
            self.assertEqual(sum(item['kind']=='conversation' for item in items),4)


if __name__=='__main__': unittest.main()

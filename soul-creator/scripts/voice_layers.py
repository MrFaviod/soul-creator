#!/usr/bin/env python3
"""Resolve graded voice layers and identify changes to a character's signature voice.

voice_layers.py blend.json [--json]
Compatibility notes are interview metadata; they never become SOUL instructions.
The author identifies signature speech from the request/source, not nationality.
"""
import argparse
import json
from pathlib import Path
import dialect_voice as regional
import stylized_voice as literary
from _common import load_config

ALIASES = {'subtle':'medium', 'natural':'medium', 'marked':'strong'}
RANK = {'low':0, 'medium':1, 'strong':2}


def resolve_layer(layer):
    if not isinstance(layer, dict) or layer.get('kind') not in ('dialect', 'stylization'):
        raise ValueError('each voice layer needs kind=dialect|stylization and primary')
    strength = ALIASES.get(layer.get('strength'), layer.get('strength', 'medium'))
    if strength not in RANK:
        raise ValueError('voice layer strength must be strong, medium or low')
    if layer['kind'] == 'dialect':
        entry = regional._entry(layer.get('primary'), regional.load_catalog())
    else:
        entry = literary._resolve(layer.get('primary'), literary.load_catalog())
    switch = layer.get('code_switch', 'off')
    if switch not in ('off', 'contextual'):
        raise ValueError('voice layer code_switch must be off or contextual')
    application = layer.get('application', 'auto')
    if application not in ('auto', 'accent'):
        raise ValueError('voice layer application must be auto or accent')
    return {**layer, 'strength':strength, 'entry':entry,
            'code_switch':switch, 'application':application}


def key(layer):
    cues = {name: layer['entry'].get(name) for name in ('name', 'language', 'category', 'signals', 'accent_signals')}
    return layer['kind'], json.dumps(cues, ensure_ascii=False, sort_keys=True)


def layers_for(voice):
    if not isinstance(voice, dict):
        raise ValueError('voice must be an object')
    signature = voice.get('signature') or {}
    if not isinstance(signature, dict):
        raise ValueError('voice.signature must be an object')
    if signature and (not all(isinstance(signature.get(k), str) and signature[k].strip() for k in ('description', 'source')) or not isinstance(signature.get('layers'), list)):
        raise ValueError('voice.signature needs description, source and layers')
    selections = voice.get('layers', signature.get('layers', []))
    if not isinstance(selections, list):
        raise ValueError('voice.layers must be a list')
    for old in ('dialect', 'stylization'):
        if voice.get(old) is not None and not isinstance(voice[old], dict):
            raise ValueError(f'voice.{old} must be an object')
        if (voice.get(old) or {}).get('mode', 'none') != 'none':
            raise ValueError('use voice.layers or legacy dialect/stylization, not both; migrate their selections first')
    layers = [resolve_layer(item) for item in selections]
    if len({key(item) for item in layers}) != len(layers):
        raise ValueError('voice.layers contains duplicate influences')
    dominant_regions = [item for item in layers if item['kind'] == 'dialect' and item['strength'] == 'strong']
    if len(dominant_regions) > 1:
        raise ValueError('only one strong regional grammar/address base is allowed; lower the other influences')
    return layers, [resolve_layer(item) for item in signature.get('layers', [])]


def analyze(voice, output_language='match_user', max_layers=4):
    layers, signature = layers_for(voice)
    if len(layers) > max_layers:
        raise ValueError(f'at most {max_layers} voice layers; simplify the blend')
    issues, notes = [], []
    for original in signature:
        if original['strength'] != 'strong':
            continue
        selected = next((item for item in layers if key(item) == key(original)), None)
        if selected is None:
            issues.append(f"Signature voice {original['entry']['name']} would be replaced or removed.")
        elif selected['strength'] != 'strong':
            issues.append(f"Signature voice {original['entry']['name']} would be softened to {selected['strength']}.")
        elif original['kind'] == 'dialect' and original['application'] == 'auto' and selected['application'] == 'accent' and regional.language_matches(output_language, original['entry']['language']):
            issues.append(f"Signature voice {original['entry']['name']} would change from native usage to accent-only coloring.")
    if any(item['kind'] == 'stylization' and item['strength'] == 'strong' for item in signature) and any(item['kind'] == 'dialect' and item['strength'] == 'strong' for item in layers):
        notes.append('A strongly literary character with a strong regional base can sound deliberately comic; show a sample if that combination was not already requested.')
    compatibility = voice.get('compatibility') or {}
    if not isinstance(compatibility, dict):
        raise ValueError('voice.compatibility must be an object')
    for flag in ('acknowledged', 'proposed'):
        if flag in compatibility and not isinstance(compatibility[flag], bool):
            raise ValueError(f'voice.compatibility.{flag} must be boolean')
    if 'reason' in compatibility and not isinstance(compatibility['reason'], str):
        raise ValueError('voice.compatibility.reason must be text')
    declared = compatibility.get('conflicts', [])
    if not isinstance(declared, list) or not all(isinstance(x, str) and x.strip() for x in declared):
        raise ValueError('voice.compatibility.conflicts must be a list of nonempty explanations')
    issues.extend(declared)
    accepted = compatibility.get('acknowledged') is True and bool(str(compatibility.get('reason', '')).strip())
    for layer in layers:
        if layer['kind'] == 'dialect' and layer['strength'] == 'low' and output_language != 'match_user' and not regional.language_matches(output_language, layer['entry']['language']) and layer['code_switch'] == 'off':
            notes.append(f"Low {layer['entry']['name']} may have no distinctive lexical trace in {output_language} without foreign insertions; do not invent one.")
    return {'layers':[{k:v for k,v in item.items() if k != 'entry'} for item in layers],
            'conflicts':issues, 'notes':notes, 'acknowledged':accepted,
            'needs_choice':bool(issues and not accepted)}


def render(voice, output_language, regional_axis='configured', stylized_axis='configured'):
    layers, _ = layers_for(voice)
    for kind, axis in (('dialect', regional_axis), ('stylization', stylized_axis)):
        group = [item for item in layers if item['kind'] == kind]
        if axis == 'off':
            if not group:
                return None, f'no {kind} layers are configured to disable'
            layers = [item for item in layers if item['kind'] != kind]
        elif axis == 'single':
            if len(group) < 2:
                return None, f'no {kind} blend to reduce to dominant-only'
            dominant = max(group, key=lambda item:RANK[item['strength']])
            layers = [item for item in layers if item['kind'] != kind or item is dominant]
    if not layers:
        return [], None
    out = ['Keep one coherent voice: the character and situation come first; a strong regional base supplies compatible grammar/address, medium layers add restrained cadence or rhetoric, and low layers only occasional lexical turns. The requested reply language always wins.']
    for item in sorted(layers, key=lambda x:-RANK[x['strength']]):
        entry, strength = item['entry'], item['strength']
        if item['kind'] == 'dialect':
            if strength == 'strong':
                cue = regional._primary(entry, output_language, item['application'])
            elif strength == 'medium':
                native = regional.language_matches(output_language, entry['language'])
                cue = (f"Light phrasing from {entry['name']}: {entry['signals']} Keep the dominant grammar/address unchanged."
                       if native else regional._accent(entry))
            else:
                cue = (f"A few occasional words or short turns associated with {entry['name']}, using the reply language unless foreign insertions were explicitly allowed. "
                       f"Source description for selecting lexical cues, not for transferring grammar: {entry['signals']} "
                       'Do not adopt its pronouns, conjugations, phonetic spelling or full cadence. If no grounded compatible expression exists, omit this trace.')
            cue += (' Occasional meaningful foreign insertions are explicitly allowed, while the reply language stays dominant.'
                    if item['code_switch'] == 'contextual' else ' No code-switching or compulsory untranslated words.')
        else:
            cue = f"Literary color from {entry['name']}: {entry['signals']} " + literary.STRENGTHS[strength]
            cue += ' Preserve the requested language and regional address; do not claim historical authenticity, identity or memories.'
        out.append(f"{strength.capitalize()} influence: {cue}")
    out.append('Let secondary colors appear on different fitting occasions rather than stacking every layer in every reply. Keep code, quotes, commands and factual content unchanged.')
    return out, None


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('blend'); parser.add_argument('--json', action='store_true')
    parser.add_argument('--config')
    args = parser.parse_args(argv)
    blend = json.loads(Path(args.blend).read_text(encoding='utf-8'))
    try:
        report = analyze(blend['voice'], blend.get('output_language', 'match_user'),
                         load_config(args.config)['blend'].get('max_voice_layers', 4))
    except ValueError as exc:
        parser.error(str(exc))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if report['needs_choice'] else 0


if __name__ == '__main__':
    raise SystemExit(main())

#!/usr/bin/env python3
"""Validate blend types and choices before the renderer writes any files."""
import argparse
import json
from pathlib import Path
from _common import load_config
import voice_layers
import ecosystem_roles
import graphic_markers


def text(value, field):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f'{field} must be nonempty text')


def text_list(value, field):
    if not isinstance(value, list) or not all(isinstance(item, str) and item.strip() for item in value):
        raise ValueError(f'{field} must be a list of nonempty strings')


def validate(blend, cfg):
    if not isinstance(blend, dict): raise ValueError('blend must be an object')
    text(blend.get('name'), 'name')
    if blend.get('tier') not in ('P', 'C', 'T', 'B'): raise ValueError('tier must be P, C, T or B')
    text(blend.get('output_language', 'match_user'), 'output_language')
    if blend.get('language_policy', 'prefer') not in ('prefer', 'always'):
        raise ValueError('language_policy must be prefer or always')
    ecosystem_roles.labels(blend.get('ecosystem_role'))
    for field in ('anchor', 'secondary'):
        part = blend.get(field)
        if field == 'secondary' and not part: continue
        if not isinstance(part, dict): raise ValueError(f'{field} must be an object')
        for key in ('label', 'gloss', 'description'): text(part.get(key), f'{field}.{key}')
    text_list(blend.get('archetype'), 'archetype')
    if not 1 <= len(blend['archetype']) <= 4: raise ValueError('archetype needs 1-4 behaviors')
    for field in ('quirks', 'exclude', 'label_terms'): text_list(blend.get(field, []), field)
    facets = blend.get('dynamic', [])
    if not isinstance(facets, list): raise ValueError('dynamic must be a list')
    for facet in facets:
        if not isinstance(facet, dict): raise ValueError('each dynamic facet must be an object')
        for field in ('when', 'then'): text(facet.get(field), 'dynamic.' + field)
    examples = blend.get('examples', [])
    if not isinstance(examples, list) or len(examples) > 3: raise ValueError('examples must contain at most 3 exchanges')
    for example in examples:
        if not isinstance(example, dict): raise ValueError('each example must be an object')
        for field in ('user', 'reply'): text(example.get(field), 'examples.' + field)
    voice = blend.get('voice')
    if not isinstance(voice, dict): raise ValueError('voice must be an object')
    if 'graphic_markers' in voice:
        graphic_markers.validate(voice['graphic_markers'])
        if voice.get('markers'):
            raise ValueError('choose structured voice.graphic_markers or legacy voice.markers, not both')
    for field in ('base', 'situational'): text_list(voice.get(field, []), 'voice.' + field)
    if 'reply_shape' in voice and not isinstance(voice['reply_shape'], str):
        raise ValueError('voice.reply_shape must be text')
    if 'continuity' in voice:
        text(voice['continuity'], 'voice.continuity')
    for container, field in ((blend.get('intensity', {}), 'intensity'), (voice.get('markers', {}), 'voice.markers')):
        if not isinstance(container, dict): raise ValueError(f'{field} must be an object')
        for key, value in container.items():
            if key not in ('mild', 'moderate', 'strong'): raise ValueError(f'unknown {field} level {key}')
            text(value, field + '.' + key)
    if 'layers' in voice or 'signature' in voice:
        report = voice_layers.analyze(voice, blend.get('output_language', 'match_user'), cfg['blend'].get('max_voice_layers', 4))
        if report['needs_choice'] and not (voice.get('compatibility') or {}).get('proposed'):
            raise ValueError('voice compatibility requires an informed choice: ' + ' '.join(report['conflicts']) +
                             ' Preserve the signature, lower secondary influences, or record the explicit choice in voice.compatibility.')
        return report
    # Legacy voice formats retain their prior parser and rendering.
    from dialect_voice import render_dialect
    from stylized_voice import render_stylization
    render_dialect(voice.get('dialect'), blend.get('output_language', 'match_user'))
    render_stylization(voice.get('stylization'))
    return {'conflicts': [], 'notes': [], 'needs_choice': False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('blend'); parser.add_argument('--config')
    args = parser.parse_args(argv)
    try:
        result = validate(json.loads(Path(args.blend).read_text(encoding='utf-8')), load_config(args.config))
    except (ValueError, KeyError, TypeError) as exc:
        parser.error(str(exc))
    print(json.dumps({'ok':True, 'voice':result}, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__': raise SystemExit(main())

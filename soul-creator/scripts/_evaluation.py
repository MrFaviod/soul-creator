"""Immutable inputs shared by pack construction, execution and scoring."""
import hashlib
import json
from pathlib import Path


def fingerprint(value):
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()


def manifest_blend(manifest):
    if 'blend_snapshot' in manifest:
        blend = manifest['blend_snapshot']
        if manifest.get('blend_sha256') != fingerprint(blend):
            raise ValueError('manifest snapshot does not match its hash; render a fresh manifest')
        return blend
    raw = Path(manifest['blend_file']).read_text(encoding='utf-8')
    expected = manifest.get('blend_sha256')
    if expected and not hashlib.sha256(raw.encode()).hexdigest().startswith(expected):
        raise ValueError('legacy manifest refers to a changed blend; render a fresh manifest')
    return json.loads(raw)


def target_persona(blend):
    """Common behavioral target, never a rendered condition or its axes."""
    return {'name': blend['name'], 'identity': blend['anchor']['description'],
            'ecosystem_role': blend.get('ecosystem_role'),
            'secondary': (blend.get('secondary') or {}).get('description', ''),
            'behavior': blend.get('archetype', []), 'quirks': blend.get('quirks', []),
            'output_language': blend.get('output_language', 'match_user'),
            'language_policy': blend.get('language_policy', 'prefer'),
            'voice': {k:v for k,v in blend.get('voice', {}).items() if k != 'compatibility'},
            'facets': blend.get('dynamic', [])}

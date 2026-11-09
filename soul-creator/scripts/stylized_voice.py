"""Render optional literary/fictional/historical voice color, not a real dialect.

This is a writing-performance influence, not identity, a language override, or
an authorization to invent memories, canon, biographies or historical facts.
"""
import json
from pathlib import Path

CATALOG = Path(__file__).resolve().parents[1] / 'references/catalog/voices/stylizations.json'
STRENGTHS = {
    'subtle': 'Keep the effect subtle and situational.',
    'natural': 'Let it emerge when fitting, without a cue in every message.',
    'marked': 'Let it be recognizably theatrical in casual exchanges when welcome, never stronger than the persona.',
    'strong': 'Let this be the dominant literary manner of the character in casual conversation, while keeping the requested language intelligible and technical content plain.',
    'medium': 'Keep the literary influence understated and situational, through light rhythm, phrasing or imagery.',
    'low': 'Limit this influence to a few occasional characteristic words or short turns of phrase across the conversation, without changing grammar or imposing a recurring formula.',
}
CATEGORIES = ('fantasy', 'mythology', 'historical', 'character')


def load_catalog():
    entries = json.loads(CATALOG.read_text(encoding='utf-8'))['entries']
    return {entry['id']: entry for entry in entries}


def _resolve(ref, catalog):
    if isinstance(ref, str):
        if ref not in catalog:
            raise ValueError(f'Unknown voice.stylization entry {ref!r}; see stylizations.json or define a custom style')
        return catalog[ref]
    if isinstance(ref, dict):
        if not all(isinstance(ref.get(k), str) and ref[k].strip() for k in ('name','category','signals')):
            raise ValueError('Custom voice.stylization entry needs nonempty name, category and signals')
        if ref['category'] not in CATEGORIES:
            raise ValueError('Custom voice.stylization category must be fantasy, mythology, historical or character')
        return ref
    raise ValueError('A voice.stylization entry must be a catalog ID or custom {name, category, signals}')


def render_stylization(spec, *, regional_enabled=False):
    if not spec:
        return []
    if not isinstance(spec, dict):
        raise ValueError('voice.stylization must be a JSON object')
    mode = spec.get('mode', 'none')
    if mode not in ('none', 'single', 'blend'):
        raise ValueError('voice.stylization.mode must be none, single or blend')
    if mode == 'none':
        if spec.get('primary') or spec.get('secondary'):
            raise ValueError('voice.stylization.mode=none cannot contain selections')
        return []
    primary = _resolve(spec.get('primary'), load_catalog())
    second_refs = spec.get('secondary', [])
    if not isinstance(second_refs, list):
        raise ValueError('voice.stylization.secondary must be a list')
    if mode == 'single' and second_refs:
        raise ValueError('single voice.stylization cannot contain secondaries')
    if mode == 'blend' and len(second_refs) != 1:
        raise ValueError('blend voice.stylization requires exactly one secondary style')
    secondary = [_resolve(ref, load_catalog()) for ref in second_refs]
    names = [e['name'].casefold() for e in [primary,*secondary]]
    if len(names) != len(set(names)):
        raise ValueError('voice.stylization has duplicate selections')
    strength = spec.get('strength', 'natural')
    if strength not in STRENGTHS:
        raise ValueError('voice.stylization.strength must be subtle, natural or marked')
    # A regional base decides natural grammar/address; the stylization adds rhetoric,
    # cadence and selective imagery, not a competing conjugation or fake phonetics.
    priority = (' Preserve the requested reply language and its natural grammar/address; let any regional variety remain a voice cue, and add only literary cadence and imagery.'
                if regional_enabled else ' Keep the established reply language and forms of address.')
    common = (' This is a literary voice color, not a real-world accent, identity, worldview, or historical reconstruction.'
              ' The existing archetype and the situation take priority. Avoid stock catchphrases, made-up languages and invented memories;'
              ' keep code, technical facts and serious answers clear.')
    main = f"Use a {primary['name']} writing inflection: {primary['signals']} {STRENGTHS[strength]}"
    if secondary:
        main += f" Borrow only occasional compatible touches of {secondary[0]['name']} ({secondary[0]['signals']}); never stack both mannerisms every turn."
    return [main + priority + common]

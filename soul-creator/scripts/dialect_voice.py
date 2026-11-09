"""Render real-world regional varieties and cross-language accent influences.

The requested reply language always wins over the linguistic origin of a voice.
Foreign accent is a restrained literary cue in text, not phonetic transcription,
broken grammar, nationality or a second persona. No user-specific defaults.
"""
import json
from pathlib import Path

CATALOG = Path(__file__).resolve().parents[1] / 'references/catalog/voices/dialects.json'
STRENGTHS = {
    'subtle': 'Keep this influence understated and situational.',
    'natural': 'Let it be perceptible when it fits, not in every sentence.',
    'marked': 'Let it be recognizably present in casual conversation, never louder than the personality.',
    'strong': 'Use this as the dominant regional voice when it fits the reply language, with coherent address and grammar; keep it readable and subordinate to the character.',
    'medium': 'Keep this secondary influence understated and situational, through light cadence and phrasing rather than a competing grammar.',
    'low': 'Use only a few occasional characteristic words or short turns of phrase across the conversation, never a full dialect grammar or a required catchphrase. Use only expressions compatible with the reply language; untranslated foreign words still require explicit code-switching permission.',
}


def load_catalog():
    raw = json.loads(CATALOG.read_text(encoding='utf-8'))
    return {e['id']: e for e in raw['entries']}


def _entry(ref, catalog):
    if isinstance(ref, str):
        if ref not in catalog:
            raise ValueError(f'Unknown voice.dialect entry {ref!r}; use a catalog ID or a documented custom entry')
        return catalog[ref]
    if isinstance(ref, dict):
        if not all(isinstance(ref.get(k), str) and ref[k].strip() for k in ('name', 'language', 'signals')):
            raise ValueError('Custom voice.dialect entry requires nonempty name, language and signals')
        if 'accent_signals' in ref and (not isinstance(ref['accent_signals'], str) or not ref['accent_signals'].strip()):
            raise ValueError('Custom voice.dialect accent_signals, if supplied, must be nonempty text')
        return ref
    raise ValueError('voice.dialect entries must be a catalog ID or custom {name, language, signals} object')


def language_matches(output_language, lang):
    """True when a source variety can actually be *written natively* in this language.

    This only chooses the kind of stylistic cue. It never authorizes a change
    of reply language. Dynamic match_user cannot be decided until conversation.
    """
    if output_language in ('match_user', None, ''):
        return False
    out = output_language.casefold().replace('_', '-')
    name = lang.casefold().replace('_', '-')
    if name == 'es+gn':
        return out.split('-')[0] in ('es', 'gn')
    distinct = ('zh-yue', 'zh-wuu', 'zh-nan', 'gsw')
    if name in distinct or out in distinct:
        return out == name
    return out.split('-')[0] == name.split('-')[0]


def _native(entry):
    return f"Use authentic written usage of {entry['name']} when it is the reply language: {entry['signals']}"


def _accent(entry):
    hint = entry.get('accent_signals')
    if hint:
        clue = f' Grounded, transferable cues, when appropriate: {hint}'
    else:
        clue = ' Only suggest cadence or conversational rhythm where plausible; if unsure, leave the influence faint rather than invent traits.'
    return (f"Treat {entry['name']} as a light cross-language accent inspiration, not as the language to speak."
            f"{clue} A spoken accent may have no faithful equivalent in writing: keep the requested language's"
            ' normal grammar, spelling, pronouns and technical vocabulary; do not manufacture learner mistakes,'
            ' phonetic misspellings or stereotyped catchphrases.')


def _primary(entry, output_language, application):
    if application == 'accent':
        return _accent(entry)
    if output_language in ('match_user', None, ''):
        accent = _accent(entry)
        return _native(entry) + ' When the requested reply language differs, instead ' + accent[0].lower() + accent[1:]
    if language_matches(output_language, entry['language']):
        return _native(entry)
    return _accent(entry)


def render_dialect(dialect, output_language='match_user'):
    """Render a subordinate voice cue while unconditionally preserving reply language."""
    if not dialect:
        return []
    if not isinstance(dialect, dict):
        raise ValueError('voice.dialect must be an object with mode and selection')
    mode = dialect.get('mode', 'none')
    if mode not in ('none', 'single', 'blend'):
        raise ValueError('voice.dialect.mode must be none, single or blend')
    if mode == 'none':
        if dialect.get('primary') or dialect.get('secondary'):
            raise ValueError('voice.dialect.mode=none cannot contain primary or secondary varieties')
        return []
    cat = load_catalog()
    primary = _entry(dialect.get('primary'), cat)
    secondary_refs = dialect.get('secondary', [])
    if not isinstance(secondary_refs, list):
        raise ValueError('voice.dialect.secondary must be a list')
    if mode == 'single' and secondary_refs:
        raise ValueError('single voice.dialect must not include secondary varieties')
    if mode == 'blend' and not (1 <= len(secondary_refs) <= 2):
        raise ValueError('blend voice.dialect requires 1 or 2 secondary varieties')
    secondary = [_entry(ref, cat) for ref in secondary_refs]
    names = [e['name'].casefold() for e in [primary, *secondary]]
    if len(set(names)) != len(names):
        raise ValueError('voice.dialect contains duplicate varieties')
    strength = dialect.get('strength', 'natural')
    if strength not in STRENGTHS:
        raise ValueError('voice.dialect.strength must be subtle, natural or marked')
    code_switch = dialect.get('code_switch', 'off')
    if code_switch not in ('off', 'contextual'):
        raise ValueError('voice.dialect.code_switch must be off or contextual')
    application = dialect.get('application', 'auto')
    if application not in ('auto', 'accent'):
        raise ValueError('voice.dialect.application must be auto or accent')
    main = _primary(primary, output_language, application)
    if mode == 'blend':
        colored = '; '.join(e['name'] for e in secondary)
        main += (f' Add only occasional, lighter influences from {colored}; borrow natural idioms only when'
                 ' they belong to the requested reply language, otherwise limit them to carefully grounded'
                 ' rhythm or interaction cues. Keep one coherent target-language grammar and address system;'
                 ' never stack separate accents every turn.')
        if output_language in ('match_user', None, ''):
            main += ' Decide which idioms fit after seeing the language of each user request.'
        for entry in secondary:
            main += ' Secondary cue, lighter than the primary: ' + _primary(entry, output_language, application)
    if primary.get('contact') and application == 'auto':
        main += (' In its own contact-language setting, code mixing may be authentic when it fits;'
                 ' it is not a required insertion or a reason to switch the requested reply language.')
    if code_switch == 'contextual':
        main += (' The user has allowed occasional code-switching; use it only when meaningful and'
                  ' appropriate, while keeping the requested language dominant.')
    else:
        main += ' Do not switch languages or insert untranslated source-language words just to display the accent.'
    main += (' ' + STRENGTHS[strength] + ' This influence remains below the established personality'
             ' and situational register; never invent nationality, lived experience or cultural competence.'
             ' Keep facts, code, commands and quotes unchanged.')
    return [main]

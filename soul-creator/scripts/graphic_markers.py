"""Validate and render selected graphic-marker families independently of intensity."""
import emphasis

FAMILIES = ('emoji', 'ascii', 'kaomoji')
FREQUENCIES = ('rare', 'recurrent', 'frequent')


def validate(profile):
    if not isinstance(profile, dict) or set(profile) - {'families', 'frequency'}:
        raise ValueError('voice.graphic_markers needs families and optional frequency')
    families = profile.get('families')
    if not isinstance(families, list) or any(not isinstance(f, str) or f not in FAMILIES for f in families):
        raise ValueError('graphic marker families must be a list of emoji, ascii, kaomoji; [] means none')
    if len(set(families)) != len(families):
        raise ValueError('graphic marker families must not repeat')
    if profile.get('frequency', 'recurrent') not in FREQUENCIES:
        raise ValueError('graphic marker frequency must be rare, recurrent or frequent')
    return profile


def render(profile, rcfg, emphasize=False):
    if profile is None:
        return []
    validate(profile)
    cfg = rcfg['graphic_markers']
    families = profile['families']
    if not families:
        return ['### Graphic markers', '- ' + cfg['none'], '']
    result = ['### Graphic markers', '- ' + cfg['common'],
              '- ' + cfg['frequency'][profile.get('frequency', 'recurrent')], '']
    for family in families:
        entry = cfg['families'][family]
        cue = emphasis.directive(entry['cue']) if emphasize else entry['cue']
        result += ['### ' + entry['heading'], '- ' + cue, '']
    return result

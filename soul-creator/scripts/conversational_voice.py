"""Static expressive controls; no runtime hooks, response rewriting or extra calls."""
import emphasis


def enabled(axes, name):
    value = axes.get(name, 'on')
    if value not in ('on', 'off'):
        raise ValueError(f'{name} must be on or off')
    return value == 'on'


def lock(voice, rcfg, highlighted=False):
    """Refer to the existing voice, optionally adding one authored continuity cue."""
    cues = list(rcfg['voice_lock'])
    if highlighted:
        cues[0] = emphasis.directive(cues[0])
        cues[-1] = emphasis.directive(cues[-1])
    continuity = voice.get('continuity')
    if continuity:
        cues.insert(1, continuity)
    return ['## Voice lock', ' '.join(cues), '']


def naturalness(voice, rcfg):
    """Use a single contextual block rather than stacking generic shape directives."""
    return ['## Conversational naturalness', ' '.join(rcfg['humanize']), '']

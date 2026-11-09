"""Case-only emphasis on selected control spans, never a rewrite of examples."""
import re


def directive(text):
    """Highlight a leading verb/identity prefix without changing words or names."""
    match=re.match(r'^(You\s+\w+|[A-Za-z][A-Za-z\'-]*)\b',text,re.I)
    if not match:
        return text
    return match.group(0).upper()+text[match.end():]


def primary(axes):
    return axes.get('primary_emphasis','off')=='selective'


def role_or_label(text, axes):
    return text.upper() if primary(axes) else text


def voice_line(text):
    prefix='Strong influence: '
    if text.startswith(prefix):
        return prefix+directive(text[len(prefix):])
    return text

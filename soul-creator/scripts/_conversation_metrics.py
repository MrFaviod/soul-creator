"""Language-independent surface structure signals, never naturalness verdicts."""
import collections
import re

QUESTION = re.compile(r'[?\u061f\uff1f][\s\"\'”’»)]*$')
LIST = re.compile(r'^\s*(?:[-*+•]|\d+[.)])\s+')
FENCE = re.compile(r'^\s*(`{3,}|~{3,})')
ACTS = ('sharing', 'question', 'choice', 'correction', 'closing', 'task', 'artifact')
PHASES = ('before_task', 'during_task', 'after_task')
BOOL_FIELDS = ('marker_eligible', 'persona_description_requested', 'structure_requested',
               'question_needed', 'voice_probe')


def context(item):
    """Optional annotations; never infer intent from a language-specific phrase list."""
    result = {}
    for key in BOOL_FIELDS:
        if key in item:
            if not isinstance(item[key], bool):
                raise ValueError(f'{key} must be a boolean when supplied')
            result[key] = item[key]
    for key, choices in (('conversation_act', ACTS), ('phase', PHASES)):
        if key in item:
            if not isinstance(item[key], str) or item[key] not in choices:
                raise ValueError(f'{key} must be one of {choices}')
            result[key] = item[key]
    return result


def shape(text):
    """Collapse adjacent forms; code/JSON cannot create a spurious closing question."""
    text = text.strip()
    if text.startswith(('{', '[')):
        import json
        try:
            json.loads(text)
            return 'data'
        except ValueError:
            pass
    blocks, paragraph, fence = [], [], None

    def flush():
        if paragraph:
            blocks.append('question' if QUESTION.search(' '.join(paragraph)) else 'prose')
            paragraph.clear()

    for line in text.splitlines():
        found = FENCE.match(line)
        if fence:
            if found and found[1][0] == fence[0] and len(found[1]) >= len(fence):
                fence = None
            continue
        if found:
            flush(); blocks.append('code'); fence = found[1]
        elif not line.strip():
            flush()
        elif LIST.match(line):
            flush(); blocks.append('list')
        elif line.lstrip().startswith('|'):
            flush(); blocks.append('table')
        elif re.match(r'^\s*#{1,6}\s', line):
            flush(); blocks.append('heading')
        else:
            paragraph.append(line.strip())
    flush()
    return '>'.join(kind for i, kind in enumerate(blocks) if i == 0 or kind != blocks[i-1]) or 'empty'


def summary(rows, window=5):
    """One conversation or one repeat at a time; do not mingle independent histories."""
    shapes = [shape(row.get('response') or '') for row in rows]
    counts = collections.Counter(shapes)
    windows = []
    for start in range(max(0, len(rows) - window + 1)):
        group = rows[start:start+window]
        forms = shapes[start:start+window]
        dominant, count = collections.Counter(forms).most_common(1)[0]
        acts = sorted({row['conversation_act'] for row in group if row.get('conversation_act')})
        if count >= window - 1 and len(acts) >= 2 and len(dominant.split('>')) >= 3:
            windows.append({'start_turn':start+1, 'end_turn':start+window,
                            'shape':dominant, 'count':count, 'conversation_acts':acts})
    return {'n':len(rows), 'shapes':dict(counts),
            'dominant_share':round(max(counts.values())/len(rows), 3) if rows else None,
            'review_windows':windows,
            'naturalness':None, 'structural_monotony':None,
            'note':'Surface triage only. Plain prose can be natural across many turns; requested structure is legitimate. Semantic review decides appropriateness and repetition.'}


TURN_RUBRIC = (
    "Score voice_fidelity, naturalness, conversational_appropriateness and utility separately (1-5). "
    "Evaluate how this reply responds to the user's conversational move and recent history. "
    "A factual answer can still be an inappropriate conversational action. "
    "Look for automatic acknowledgment, reframing, option menus, closing offers or questions "
    "when context does not call for them; changes of wording alone do not establish variety. "
    "Requested lists, tables, genuine comparisons and necessary questions are legitimate. "
    "Brief plain replies and repeated appropriate forms are not faults. "
    "Judge voice by diction, cadence and interpersonal stance, allowing changes of emotion and focus. "
    "Honor the requested language, dialect strength and artifact register. "
    "Annotations are contextual cues, not compulsory response templates or hidden answer keys. "
    "Do not reward humor, markers, brevity or novelty for their own sake. "
)

CONVERSATION_RUBRIC = (
    "Review the complete conversation, including every user message, as a sequence. "
    + TURN_RUBRIC +
    "Report voice_continuity and structural_monotony with cited turn numbers. "
    "Compare comparable voice_probe turns before, during and after task work where available. "
    "Look for the same opening-development-ending plan across different conversational acts, "
    "even when no words repeat. Identify unnecessary handoffs and returns to generic assistant voice. "
    "Preserve task correctness and required output formats; a correct formal artifact is not voice drift. "
    "Mark persona_recitation for unsolicited labels, paraphrased trait inventories or style announcements; "
    "direct personality requests and normal first person are allowed. "
    "Use marker_fit as a separate contextual judgment. Keep uncertainty explicit; surface signals are not verdicts. "
    "You do not know which variant produced this conversation."
)

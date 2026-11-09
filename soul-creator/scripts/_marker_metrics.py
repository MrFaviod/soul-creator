"""Finite surface heuristics for markers; not a semantic appropriateness judge."""
import collections
import json
import re

EMOJI = re.compile('[\U0001F000-\U0001FAFF☀-➿⬀-⯿]')
# Require two face cues, or a recognizable shrug gesture; (日本語) and (ω) are not faces.
_FACE_CUE = '[¬＾ಠಥ◕•ω∀▽≧≦ᴗ︶‿益Дд・°ʘ><￣－]'
KAOMOJI = re.compile(r'¯\\?_\(ツ\)_/¯|[(（](?=[^()（）\n]{2,28}[)）])'
                     r'(?=[^()（）\n]*[^\x00-\x7f])'
                     r'(?=[^()（）\n]*' + _FACE_CUE + r'[^()（）\n]*' + _FACE_CUE + r')'
                     r'[^()（）\n]{2,28}[)）]')
ASCII = re.compile(r"(?<![:/\\])[=:;][-^oO']?[)(/\\DPpOo*|](?![\w/\\])|"
                   r"(?<!\w)(?:[8xX][-^oO']?[)(DPp]|[)(][-^']?[=:;8]|[TtOo^xX][._-][TtOo^xX]|>[._-]<)(?!\w)")


def prose(text):
    text = re.sub(r'(?s)(```|~~~).*?(?:\1|$)', ' ', text)
    text = re.sub(r'`+[^`\n]*`+', ' ', text)
    try:
        json.loads(text)
        return ''  # a whole JSON value is data, not conversational decoration
    except (ValueError, TypeError):
        return text


def scan(text):
    rest = prose(text or '')
    faces = []
    def face_or_prose(match):
        token = match.group()
        # Reject parenthetical words and spaced arithmetic in any writing system.
        face_letters = 'TtXxOoUuQqVvPpDdωДдつづノヽヾツಠಥ益ʕʔงو'
        if any(ch.isalpha() and ch not in face_letters for ch in token) or re.search(r'\d|\s[+*/=]\s', token):
            return token
        faces.append(token)
        return ' '
    rest = KAOMOJI.sub(face_or_prose, rest)
    ascii_faces = [m.group() for m in ASCII.finditer(rest)]
    rest = ASCII.sub(' ', rest)
    return {'emoji': EMOJI.findall(rest), 'ascii': ascii_faces, 'kaomoji': faces}


def has_marker(text):
    return any(scan(text).values())


def summary(rows, profile=None):
    scans = [scan(row.get('response') or '') for row in rows]
    selected = set(profile['families']) if profile is not None else None
    def share(indices):
        return round(sum(any(scans[i].values()) for i in indices) / len(indices), 2) if indices else None
    eligible = [i for i,r in enumerate(rows) if r.get('marker_eligible') is True]
    ineligible = [i for i,r in enumerate(rows) if r.get('marker_eligible') is False]
    occurrences = collections.defaultdict(set)
    for i, (row, found) in enumerate(zip(rows, scans)):
        for family, tokens in found.items():
            for token in set(tokens):
                occurrences[(family, token)].add(row.get('prompt_id', f'unknown-{i}'))
    repeated = sorted(f'{family}: {token}' for (family,token), contexts in occurrences.items() if len(contexts) >= 3)
    return {
        'marker_families': {family: round(sum(bool(s[family]) for s in scans) / len(rows), 2) if rows else 0
                            for family in ('emoji','ascii','kaomoji')},
        'marker_eligible_n': len(eligible), 'marker_eligible_share': share(eligible),
        'marker_selected_eligible_share': (round(sum(any(scans[i][family] for family in selected)
                                                     for i in eligible) / len(eligible), 2)
                                           if selected and eligible else None),
        'marker_ineligible_n': len(ineligible), 'marker_ineligible_share': share(ineligible),
        'marker_unassessed_n': len(rows) - len(eligible) - len(ineligible),
        'marker_unselected_share': (round(sum(any(tokens for family,tokens in s.items() if family not in selected)
                                            for s in scans) / len(rows), 2) if rows else 0) if selected is not None else None,
        'marker_tics': repeated,
    }

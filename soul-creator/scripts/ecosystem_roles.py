"""Compact identity labels for an agent's place in an ecosystem; no workflows."""
import json
import re
from pathlib import Path
CATALOG=Path(__file__).resolve().parents[1]/'references/ecosystem-roles.json'


def catalog():
    return {entry['id']:entry for entry in json.loads(CATALOG.read_text(encoding='utf-8'))['entries']}


def resolve(selection, entries=None):
    if isinstance(selection,str):
        entries=entries if entries is not None else catalog()
        if selection not in entries:
            raise ValueError(f'unknown ecosystem role {selection!r}; choose a catalog id or a custom label object')
        return entries[selection]['label']
    if isinstance(selection,dict):
        label=selection.get('label')
        if set(selection)-{'label'}:
            raise ValueError('custom ecosystem roles contain only a label; operational details go to ledger.handoff')
        if not isinstance(label,str) or not label.strip() or not label.isprintable() or len(label)>80 or len(label.split())>8 or re.search(r'[.!?;:{}<>`。！？；؟]',label):
            raise ValueError('custom ecosystem role must be a short title, not a sentence or operational description')
        return label.strip()
    raise ValueError('ecosystem role selections must be an id or {label: short title}')


def labels(role):
    if role is None:
        return []
    if not isinstance(role,dict) or set(role)-{'primary','secondary'} or 'primary' not in role:
        raise ValueError('ecosystem_role needs primary and optional secondary; keep duties and relationships outside SOUL')
    entries=catalog()
    result=[resolve(role['primary'],entries)]
    if role.get('secondary') is not None:
        result.append(resolve(role['secondary'],entries))
    if len({value.casefold() for value in result})!=len(result):
        raise ValueError('primary and secondary ecosystem roles must differ')
    return result


def render(role, emphasize=False):
    selected=labels(role)
    if not selected:
        return []
    primary=selected[0].upper() if emphasize else selected[0]
    text=f'Your place in the ecosystem is {primary}'
    if len(selected)>1:
        text+=f', with a secondary {selected[1]} focus'
    return ['## Ecosystem role', '- '+text+'.', '']

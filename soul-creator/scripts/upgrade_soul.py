#!/usr/bin/env python3
"""Safely stage an existing SOUL.md in the current expressive scheme.

Adds the current reply-shape cue and concise anti-slop section only when absent.
Never changes the name, archetype, existing lines, or source file. This is a
structural migration, NOT an automatic reinterpretation of the personality.

Usage: python scripts/upgrade_soul.py OLD.md --out CANDIDATE.md [--check]
       [--no-reply-shape] [--no-anti-slop] [--persona-expression soft|mid|hard]
       [--voice-lock] [--humanize] [--config JSON]
"""
import argparse
import difflib
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import load_config
from check_soul import check
import conversational_voice

HEADING = re.compile(r"(?im)^##\s+(.+?)\s*$")
VOICE = re.compile(r"^(?:voice|voz)$", re.I)
SUBSTANCE = re.compile(r"^(?:substance and expression|sustancia y expresi[oó]n|expresi[oó]n y sustancia)$", re.I)
EXPRESSION = re.compile(r'^(?:personality expression|expresi[oó]n de (?:la )?personalidad)$', re.I)
VOICE_LOCK = re.compile(r'^(?:voice lock|continuidad de (?:la )?voz|bloqueo de voz)$', re.I)
HUMANIZE = re.compile(r'^(?:conversational naturalness|naturalidad conversacional|humanize)$', re.I)
# Conservative heuristic: a custom voice cue takes precedence over another generic one.
SHAPE_HINT = re.compile(r"(?i)\b(?:reply.shape|reply.form|response.shape|rhythm|ritmo|"
                        r"estructura|preguntas? (?:final|autom[aá]tic)|closing question|"
                        r"men[uú] (?:de )?opciones|automatic handoff)\b")


def upgrade(raw, config, include_shape=True, include_slop=True, persona_expression=None,
            voice_lock=False, humanize=False):
    """Return (candidate_text, inserted_labels, review_notes), preserving all old lines."""
    heads = list(HEADING.finditer(raw))
    voice = next((i for i, m in enumerate(heads) if VOICE.fullmatch(m.group(1).strip())), None)
    if voice is None:
        raise ValueError("No ## Voice / ## Voz section. Preserve the original and map it manually; "
                         "this tool will not guess where voice instructions belong.")
    v_end = heads[voice + 1].start() if voice + 1 < len(heads) else len(raw)
    v_text = raw[heads[voice].end():v_end]
    has_humanize = any(HUMANIZE.fullmatch(m.group(1).strip()) for m in heads)
    add_humanize = bool(humanize and not has_humanize)
    add_voice_lock = bool(voice_lock and not any(VOICE_LOCK.fullmatch(m.group(1).strip()) for m in heads))
    add_shape = bool(include_shape and not humanize and not has_humanize and not SHAPE_HINT.search(v_text))
    add_slop = bool(include_slop and not any(SUBSTANCE.fullmatch(m.group(1).strip()) for m in heads))
    if persona_expression is not None and persona_expression not in ('soft', 'mid', 'hard'):
        raise ValueError('persona_expression must be soft, mid or hard')
    add_expression = bool(persona_expression and not any(EXPRESSION.fullmatch(m.group(1).strip()) for m in heads))
    notes = []
    if persona_expression and not add_expression:
        notes.append('Existing Personality expression section preserved; requested level needs manual comparison.')
    for requested, added, name in ((voice_lock,add_voice_lock,'Voice lock'),(humanize,add_humanize,'Conversational naturalness')):
        if requested and not added:
            notes.append(f'Existing {name} section preserved; compare it manually.')
    if humanize and SHAPE_HINT.search(v_text):
        notes.append('Existing reply-shape cue preserved; review for overlap with conversational naturalness.')
    if not any((add_shape, add_slop, add_expression, add_voice_lock, add_humanize)):
        return raw, [], notes + ["Already has equivalent sections/cues, or additions disabled; confirm equivalence by reading it."]
    cue = config["render"]["reply_shape_default"]
    anti = config["render"]["anti_slop_short"]
    # Insert before the next ## heading, with a clear blank line, retaining every original line.
    insert = ""
    added = []
    if add_shape:
        insert += f"- {cue}\n"
        added.append("reply_shape")
    if add_slop:
        insert += f"\n## Substance and expression\n- {anti}\n"
        added.append("anti_slop")
    if add_expression:
        insert += '\n## Personality expression\n- ' + config['render']['persona_expression'][persona_expression] + '\n'
        added.append('persona_expression:' + persona_expression)
    if add_voice_lock:
        insert += '\n' + '\n'.join(conversational_voice.lock({}, config['render'], True))
        added.append('voice_lock')
    if add_humanize:
        insert += '\n' + '\n'.join(conversational_voice.naturalness({}, config['render']))
        added.append('humanize')
    before, after = raw[:v_end], raw[v_end:]
    # Avoid sticking the first new bullet onto an old line and avoid a malformed heading.
    if before and not before.endswith("\n"):
        before += "\n"
    if add_shape and before.endswith("\n\n"):
        before = before[:-1]
    if not add_shape and before.endswith("\n\n"):
        before = before[:-1]
    if after and not insert.endswith("\n\n"):
        insert += "\n"
    candidate = before + insert + after
    if not candidate.endswith("\n"):
        candidate += "\n"
    return candidate, added, notes + ["Review the new cues against existing instructions; no semantic equivalence is claimed."]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source")
    ap.add_argument("--out", required=True, help="new staged file; cannot be the source")
    ap.add_argument("--config")
    ap.add_argument("--no-reply-shape", action="store_true")
    ap.add_argument("--no-anti-slop", action="store_true")
    ap.add_argument('--persona-expression', choices=['soft','mid','hard'], help='add the selected expression block only if absent')
    ap.add_argument('--voice-lock', action='store_true', help='add static voice continuity only if absent')
    ap.add_argument('--humanize', action='store_true', help='add conversational naturalness only if absent')
    ap.add_argument("--check", action="store_true", help="check final scope after staging")
    ap.add_argument("--diff", action="store_true", help="print proposed changes")
    args = ap.parse_args(argv)
    source, dest = Path(args.source).expanduser(), Path(args.out).expanduser()
    if not source.is_file():
        ap.error(f"source file not found: {source}")
    if source.resolve() == dest.resolve():
        ap.error("source and destination must differ: migration may not overwrite an existing SOUL")
    if dest.exists():
        ap.error("destination exists: choose a fresh candidate path and review the prior result")
    try:
        config = load_config(args.config)
        original = source.read_text(encoding="utf-8")
        rendered, added, notes = upgrade(original, config, not args.no_reply_shape, not args.no_anti_slop,
                                        args.persona_expression, args.voice_lock, args.humanize)
    except (ValueError, KeyError, OSError) as e:
        ap.error(str(e))
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(rendered, encoding="utf-8")
    print(f"Staged: {dest}\nInserted: {', '.join(added) if added else 'nothing'}")
    for note in notes:
        print(f"Review: {note}")
    if args.diff:
        print("".join(difflib.unified_diff(original.splitlines(keepends=True), rendered.splitlines(keepends=True),
                                           fromfile=str(source), tofile=str(dest))), end="")
    if args.check:
        findings = check(dest, final=True, cfg=config)
        for level, message in findings:
            print(f"{level}: {message}")
        if any(level == "ERROR" for level, _ in findings):
            print("Migration candidate requires manual review; original remains unchanged.", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

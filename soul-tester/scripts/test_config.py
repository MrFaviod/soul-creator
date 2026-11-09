"""Shared argument validation and experiment isolation for soul-tester CLIs."""
import hashlib
import json
import re
from pathlib import Path

RESERVED = {"model", "messages", "stream", "tools", "tool_choice", "functions", "function_call"}


def positive_int(value):
    i = int(value)
    if i < 1:
        raise ValueError("value must be >= 1")
    return i


def parse_models(value):
    models = [x.strip() for x in value.split(",")]
    if not models or any(not x for x in models):
        raise ValueError("--models requires a nonempty, comma-separated list without blank entries")
    if len(set(models)) != len(models):
        raise ValueError("--models contains duplicates")
    return models


def parse_extra(extra, known_params):
    try:
        parsed = json.loads(extra) if extra is not None else {}
    except json.JSONDecodeError as exc:
        raise ValueError(f"--extra is not valid JSON: {exc}") from exc
    if not isinstance(parsed, dict):
        raise ValueError("--extra must be a JSON object")
    invalid = RESERVED & parsed.keys()
    clashes = parsed.keys() & known_params.keys()
    if invalid or clashes:
        raise ValueError(f"--extra may not override reserved or explicitly configured fields: {', '.join(sorted(invalid | clashes))}")
    return {**known_params, **parsed}


def validate_souls(souls):
    labels = [s["label"].strip().casefold() for s in souls]
    if any(not re.fullmatch(r"[A-Za-z0-9_.-]{1,64}", s["label"]) for s in souls):
        raise ValueError("SOUL labels must be 1-64 characters: letters, digits, underscore, hyphen or dot")
    if any(s["label"].casefold() == "control" and s["text"] is not None for s in souls):
        raise ValueError("'control' is reserved for --control with no SOUL text")
    if any(s["label"].casefold() == "control" and s["text"] is None and s["path"] for s in souls):
        raise ValueError("control must have no SOUL file")
    if len(labels) != len(set(labels)):
        raise ValueError("SOUL labels must be unique (case insensitive)")
    if any(not s["text"] for s in souls if s["text"] is not None):
        raise ValueError("SOUL file cannot be empty")


def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def slot_audit(souls, context_file=None):
    """Client-side role/hash evidence only; does not observe provider-added prompts."""
    rows = []
    for soul in souls:
        messages = context_messages(context_file, soul["text"])
        rows.append({"candidate": soul["label"], "roles": [m["role"] for m in messages] + ["user"],
                     "system_sha256": [sha(m["content"]) for m in messages if m["role"] == "system"],
                     "soul_in_first_system_slot": bool(soul["text"] and messages and messages[0]["content"] == soul["text"]),
                     "control_without_soul": soul["text"] is None})
    return {"scope": "client messages only, not provider-internal system prompt", "candidates": rows}


def context_messages(path, soul):
    # Optional approximation using user-provided system context: NOT an exact Hermes replay.
    messages = []
    if soul:
        messages.append({"role": "system", "content": soul})  # SOUL in first system slot
    if path:
        content = Path(path).read_text(encoding="utf-8").strip()
        if not content:
            raise ValueError("--context-file cannot be empty")
        messages.append({"role": "system", "content": content})
    return messages


def strip_reasoning(item, enabled):
    if not enabled:
        item.pop("reasoning", None)
    return item


def read_expectations(path):
    if not path:
        return None
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("candidates"), dict):
        raise ValueError("--expectations must be JSON object with candidates map")
    for name, spec in data["candidates"].items():
        if not isinstance(name, str) or not isinstance(spec, dict):
            raise ValueError("expectations candidate entries must be named objects")
        for field in ("target_signals", "forbidden_tics", "situational_adjustments", "task_invariants"):
            if field in spec and (not isinstance(spec[field], list) or any(not isinstance(x, str) for x in spec[field])):
                raise ValueError(f"{name}.{field} must be a list of strings")
    return data


def manifest_soul_args(path):
    """`label=path` items for every variant in a soul-creator manifest.json."""
    if not path:
        return []
    mp = Path(path).expanduser()
    data = json.loads(mp.read_text(encoding="utf-8"))
    if not isinstance(data.get("variants"), list):
        raise ValueError("--manifest must be a soul-creator variants manifest (with a 'variants' list)")
    out = []
    for v in data["variants"]:
        label = re.sub(r"[^A-Za-z0-9_.-]", "-", v["id"])[:64]
        out.append(f"{label}={mp.parent / v['file']}")
    return out


def warn_lang(lang):
    """Reports are localized in es/en; other languages fall back to English labels and text."""
    return None if lang in ("es", "en") else (
        f"language '{lang}': report labels and bundled prompts/scenarios fall back to English "
        f"unless your prompt/scenario files carry a '{lang}' key")

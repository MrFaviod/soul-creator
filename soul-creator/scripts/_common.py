"""Shared helpers: config loading, anchors, exclusions. Standard library only."""
import json
import os
import re
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
DEFAULTS = SKILL_DIR / "config" / "defaults.json"
ANCHORS = SKILL_DIR / "references" / "catalog" / "anchors.json"


def _merge(base, over):
    if isinstance(base, dict) and isinstance(over, dict):
        out = dict(base)
        for k, v in over.items():
            out[k] = _merge(base.get(k), v) if k in base else v
        return out
    return over


def load_config(override=None):
    """Defaults, then $SOUL_CREATOR_CONFIG, then an explicit override path."""
    cfg = json.loads(DEFAULTS.read_text(encoding="utf-8"))
    for path in (os.environ.get("SOUL_CREATOR_CONFIG"), override):
        if path:
            cfg = _merge(cfg, json.loads(Path(path).read_text(encoding="utf-8")))
    return cfg


def load_anchors():
    return json.loads(ANCHORS.read_text(encoding="utf-8"))


def excluded_terms(cfg):
    return [t.lower() for t in cfg.get("exclusions", {}).get("terms", [])]


def find_excluded(text, cfg):
    """Return excluded terms that appear as whole words in text."""
    low = text.lower()
    return [t for t in excluded_terms(cfg) if re.search(r"(?<!\w)" + re.escape(t) + r"(?!\w)", low)]


def slug(text):
    import unicodedata
    text = "".join(ch for ch in unicodedata.normalize("NFKD", text) if not unicodedata.combining(ch))
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s or "persona"

#!/usr/bin/env python3
"""Validate the *form* and scope of SOUL.md persona files.

Usage: python3 scripts/check_soul.py [--final] [--json] [--config FILE] FILE [FILE ...]

--final  turns placeholders, HTML comments, excluded tropes and operational
         instructions into errors (warnings while drafting).
--json   machine-readable output, one object per file (for variant batches).

The checker is structural. It does not measure personality fidelity or
accuracy; that needs real model runs (references/testing.md).
Exit code: 0 ok, 1 at least one ERROR, 2 usage.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import find_excluded, load_config  # noqa: E402

COMMENT = re.compile(r"<!--.*?-->", re.S)
# [placeholder] but not a markdown link [text](url) or a checkbox [x]
PLACEHOLDER = re.compile(r"\[[^\]\n]{3,}\](?!\()")
EMOJI = re.compile("[\U0001F000-\U0001FAFF☀-➿⬀-⯿]")
HEADING = re.compile(r"^#{1,6}\s+(.*)$")
TURN = re.compile(r"^\s*\**([^:\n*]{1,40})\**:\s*(.*)$")

# Identity anchors in several languages, second or first person.
IDENTITY_PREFIXES = [
    r"you are", r"eres", r"sos", r"t[uú] eres", r"vos sos", r"usted es",
    r"voc[eê] [eé]", r"tu es", r"du bist", r"tu sei", r"sei",
    r"i am", r"i'm", r"soy", r"yo soy", r"je suis", r"ich bin", r"sono", r"eu sou",
]
ARTICLES = {"a", "an", "the", "el", "la", "los", "las", "un", "una", "o", "uma", "um",
            "le", "une", "ein", "eine", "der", "die", "das", "il", "lo"}
USER_LABELS = {"usuario", "usuaria", "user", "tu", "tú", "vos", "humano", "human",
               "customer", "cliente", "utente", "utilisateur", "nutzer", "usuário"}
CAPS_OK = {"SOUL", "AGENTS", "USER", "MEMORY", "JSON", "YAML", "HTML", "HTTP", "HTTPS",
           "API", "URL", "CLI", "SQL", "CPU", "GPU", "LLM", "README", "TODO", "FAQ"}
EXPERT = re.compile(r"\b(eres|you are|sos)\s+(un|una|an?)?\s*(experto|experta|especialista|expert|senior)\b", re.I)
ACT_AS = re.compile(r"\b(act[uú]a como|act as|pretend to be|finge ser|haz de|role-?play as)\b", re.I)
NEG = re.compile(r"^\s*[-*]\s*(nunca|no|never|don't|do not|jam[aá]s)\b", re.I)
PATH = re.compile(r"(?<![\w.:/])(/[\w.-]+){2,}")

STYLE_WORDS = re.compile(r"\b(voice|voz|style|estilo|tone|tono|speech|habla|example|ejemplo)", re.I)
OPERATIONAL_HEADING = re.compile(
    r"\b(c[oó]mo trabaj|how (?:you|i|to) work|workflow|flujo de trabajo|procedur|procedimiento|"
    r"permission|permiso|authori[sz]ation|autorizaci[oó]n|autonom|security|seguridad|safety|"
    r"boundar|l[ií]mites|limits|rules|reglas|normas|restricci|constraints|guardrails|"
    r"criterio|criteria|judg(?:e)?ment|juicio|polic|pol[ií]tica|tool use|uso de herramientas|"
    r"approval|aprobaci|escalat|escalamiento|verificaci|verification)", re.I)

OPERATIONAL_SENTENCES = [
    re.compile(r"\b(?:ask|request|require|obtain|get|ped[ií]r?|pid[ae]s?|solicit[aá]r?|pregunt[aá]r?)\b.{0,65}\b(?:approval|permission|authori[sz]ation|confirmation|aprobaci[oó]n|permiso|autorizaci[oó]n|confirmaci[oó]n)\b", re.I),
    re.compile(r"\b(?:always|siempre)\s+(?:ask|check|confirm|verify|test|run|pregunt\w*|verific\w*|confirm\w*|prueb\w*|ejecut\w*)\b", re.I),
    re.compile(r"\b(?:act|execute|run|proceed|act[uú]\w*|ejecut\w*|proced\w*)\b.{0,70}\b(?:autonomously|without asking|on your own|sin preguntar|por tu cuenta|reversible)\b", re.I),
    re.compile(r"\b(?:do not|don't|never|no|nunca|jam[aá]s)\s+(?:expose|reveal|leak|share|divulg\w*|expong\w*|compart\w*|revel\w*)\b.{0,50}\b(?:secrets?|credentials?|passwords?|tokens?|keys?|secretos?|credenciales|contraseñas?|claves?)\b", re.I),
    re.compile(r"\b(?:do not|don't|never|nunca|jam[aá]s)\s+(?:run|execute|ejecut\w*|corr\w*)\b.{0,40}\b(?:commands?|scripts?|code|sudo|comandos?|c[oó]digo)\b", re.I),
    re.compile(r"\b(?:do not|don't|never|nunca|jam[aá]s)\s+(?:delete|remove|borr\w*|elimin\w*)\b.{0,40}\b(?:files?|data|branch\w*|repos?\w*|archivos?|datos|ramas?)\b", re.I),
    re.compile(r"\b(?:do not|don't|never|nunca|jam[aá]s)\s+(?:push|deploy|purchase|buy|despleg\w*|despliegu\w*|compr\w*)\b", re.I),
    re.compile(r"\b(?:before acting|before any action|before (?:deleting|running|deploying)|antes de (?:actuar|ejecutar|borrar|desplegar))\b", re.I),
    re.compile(r"\b(?:sudo|rm -rf|git push|AGENTS\.md|technical procedures live in|procedimientos t[eé]cnicos)\b", re.I),
    re.compile(r"\b(?:write to third parties|escrib\w* a terceros|human escalation|escal\w* a un humano)\b", re.I),
]


def _identity(line):
    for pre in IDENTITY_PREFIXES:
        m = re.match(r"^\s*(?:" + pre + r")\s+([\wÀ-ɏ'-]+)", line, re.I)
        if m:
            return m.group(1)
    return None


def check(path: Path, final: bool, cfg=None):
    cfg = cfg or load_config()
    out = []
    def err(msg): out.append(("ERROR", msg))
    def warn(msg): out.append(("WARN", msg))
    def strict(msg): (err if final else warn)(msg)

    raw = path.read_text(encoding="utf-8")
    if COMMENT.search(raw):
        strict("HTML comment present: Hermes injects SOUL.md verbatim, so comments reach the model; remove them")
    text = COMMENT.sub("", raw)
    lines = text.splitlines()

    ph = PLACEHOLDER.findall(text)
    if ph:
        strict(f"{len(ph)} placeholder(s) left, e.g. {ph[0]}")
    bad_terms = find_excluded(text, cfg)
    if bad_terms:
        strict(f"excluded trope(s) present: {', '.join(bad_terms)} (see config exclusions)")

    names, in_examples, prev_user = [], False, False
    replies, speakers = [], []
    for i, ln in enumerate(lines, start=1):
        m = HEADING.match(ln)
        if m:
            title = m.group(1).strip()
            in_examples = bool(re.search(r"ejemplo|example|sample|di[aá]logo", title, re.I))
            if OPERATIONAL_HEADING.search(title) and not STYLE_WORDS.search(title):
                strict(f"line {i}: operational section '{title}' belongs outside SOUL")
            prev_user = False
            continue

        if not in_examples:
            ident = _identity(ln)
            # a name is capitalized (or non-Latin); "You are never cruel" is not an identity
            if ident and ident.lower() not in ARTICLES and not ident[0].islower():
                names.append(ident)

        where = " (inside an example)" if in_examples else ""
        for pattern in OPERATIONAL_SENTENCES:
            if pattern.search(ln):
                strict(f"line {i}: operational instruction{where} should be moved out of SOUL")
                break

        if in_examples:
            tm = TURN.match(ln)
            if tm:
                label = tm.group(1).strip()
                if label.lower() in USER_LABELS:
                    prev_user = True
                    continue
                if prev_user:
                    speakers.append((i, label))
                    replies.append(tm.group(2).strip().lower())
                prev_user = False

    if not names and not any(_identity(ln) for ln in lines):
        err("no identity line (e.g. 'You are <Name>, ...', 'Eres/Sos <Nombre>, ...', 'I am <Name>')")
    distinct = sorted({n for n in names}, key=str.casefold)
    if len({n.casefold() for n in distinct}) > 1:
        err(f"more than one identity name: {distinct}")
    name = names[0] if names else None
    if name:
        bad = sorted({lb for _, lb in speakers if lb.casefold() != name.casefold()})
        if bad:
            err(f"example speaker(s) {bad} differ from identity name '{name}'")

    dupes = {r for r in replies if r and replies.count(r) > 1}
    if dupes:
        warn("identical example replies repeat (they become tics): " + "; ".join(sorted(dupes))[:80])
    if EXPERT.search(text):
        warn("expertise framing does not establish capability; put actual task needs outside SOUL")
    if ACT_AS.search(text):
        warn("'act as' framing invites performing a role; state who the persona is")
    # Selective emphasis is intentional. Warn on sustained shouting, not the
    # sum of a few highlighted identity/role/voice verbs across the whole file.
    for i, line in enumerate(lines, 1):
        words = re.findall(r"\b[^\W\d_]+\b", line, re.U)
        cased = [word for word in words if word.lower() != word.upper() and word.upper() not in CAPS_OK]
        if len(cased) >= 10 and sum(word.isupper() for word in cased) / len(cased) > 0.6:
            warn(f"line {i}: sustained all-caps prose; compare it with selective emphasis")
    negs = sum(1 for ln in lines if NEG.match(ln))
    if negs > 5:
        warn(f"{negs} negative bullets: prefer positive, natural descriptions")
    if any(len(EMOJI.findall(ln)) >= 6 for ln in lines):
        warn("line with 6+ emoji resembles a closed token list")
    if len(re.findall(r"`[^`\n]+`", text)) > 3 or PATH.search(text):
        warn("commands or paths in SOUL: project facts belong outside persona")
    if not re.search(r"(?im)^##\s+(?:voice|voz)\b", text):
        warn("no Voice section")
    if len(lines) > 80 or len(text) > 6000:
        warn(f"{len(lines)} lines / {len(text)} chars: long for a SOUL; trim")
    return out


def main(argv):
    if "-h" in argv or "--help" in argv:
        print(__doc__)
        return 0
    final = "--final" in argv
    as_json = "--json" in argv
    cfg_path = None
    files = []
    it = iter(argv)
    for a in it:
        if a == "--config":
            cfg_path = next(it, None)
        elif a not in ("--final", "--json"):
            files.append(a)
    if not files:
        print(__doc__)
        return 2
    cfg = load_config(cfg_path)
    failed, report = False, []
    for file in files:
        f = Path(file)
        res = [("ERROR", "file not found")] if not f.is_file() else check(f, final, cfg)
        failed |= any(level == "ERROR" for level, _ in res)
        report.append({"file": str(f), "ok": not any(l == "ERROR" for l, _ in res),
                       "errors": [m for l, m in res if l == "ERROR"],
                       "warnings": [m for l, m in res if l == "WARN"]})
    if as_json:
        print(json.dumps(report, ensure_ascii=False, indent=1))
    else:
        for r in report:
            print(f"== {r['file']}")
            if not r["errors"] and not r["warnings"]:
                print("  ok")
            for m in r["errors"]:
                print(f"  ERROR: {m}")
            for m in r["warnings"]:
                print(f"  WARN: {m}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

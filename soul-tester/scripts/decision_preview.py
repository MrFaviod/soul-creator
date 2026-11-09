#!/usr/bin/env python3
"""Make a short, sample-first comparison for human SOUL choice.

No automatic winner, personality score or causal claim. Detailed results remain
in report.md/results.json. Both test runners call these pure functions.
"""
import re


def clip(value, limit=195):
    """One readable excerpt, with explicit truncation and no reasoning traces."""
    value = re.sub(r"\s+", " ", str(value or "")).strip()
    if len(value) <= limit:
        return value or "(vacío)"
    # Showing just an opener can hide the exact closing-question tic that
    # the user wants to compare. Preserve the start AND the ending, explicitly
    # marking the omitted middle; never paraphrase or rearrange words.
    head_len = max(50, int(limit * .64))
    tail_len = max(35, limit - head_len - 5)
    head = value[:head_len].rsplit(" ", 1)[0].rstrip() or value[:head_len]
    tail = value[-tail_len:].split(" ", 1)[-1].lstrip() or value[-tail_len:]
    return head + " […] " + tail


def _labels(lang):
    if lang == "es":
        return dict(title="Elegí la voz que más te convenza", note="Muestras reales de una corrida por opción, no puntuaciones ni un ganador automático.",
                    ask="Pedido", candidate="Candidato", model="Modelo", no="Sin respuesta comparable",
                    more="Las respuestas completas, otras corridas y fallos están en `report.md` y `results.json`.",
                    decide="Elegí por naturalidad, personalidad, ajuste a la situación y utilidad; también podés pedir otra prueba o no elegir ninguno.",
                    partial="Hay pruebas incompletas: no interpretes la ausencia de respuesta como un fallo de personalidad.",
                    caveat="Las respuestas multiturno tienen historias distintas a partir de la primera respuesta; compáralas como muestras, no como condiciones idénticas turno a turno.")
    return dict(title="Choose the voice that fits best", note="Actual excerpts from one run per option, not personality scores or an automatic winner.",
                ask="Prompt", candidate="Candidate", model="Model", no="No comparable reply",
                more="Full replies, repetitions and errors are in `report.md` and `results.json`.",
                decide="Choose based on naturalness, personality, fit to the situation and usefulness; you can ask for another test or choose none.",
                partial="Some calls are incomplete: a missing reply does not mean a persona failure.",
                caveat="Multi-turn candidates develop different histories after the first response; treat these as samples, not identical turn-by-turn conditions.")


def _quote(text):
    # Plain blockquote, not a fabricated paraphrase.
    return "> " + text.replace("\n", " ")


def single_preview(souls, models, prompt, results, lang="es", limit=195):
    L = _labels(lang)
    out = [f"# {L['title']}", "", L["note"], ""]
    complete = True
    for model in models:
        out += [f"## {L['model']}: `{model}`", "", f"**{L['ask']}:** {clip(prompt, 115)}", ""]
        for soul in souls:
            samples = [r for r in results if r.get("model") == model and r.get("soul") == soul["label"]]
            chosen = next((r for r in samples if r.get("run") == 1), samples[0] if samples else None)
            name = soul["label"]
            out += [f"**{L['candidate']} `{name}`**"]
            if chosen and chosen.get("ok"):
                out.append(_quote(clip(chosen.get("content"), limit)))
            else:
                out.append(f"> *{L['no']}*" )
                complete = False
            out.append("")
    if not complete:
        out += [L["partial"], ""]
    out += [L["decide"], "", L["more"], ""]
    return "\n".join(out)


def multi_preview(souls, models, scenarios, conversations, lang="es", max_scenarios=2, limit=195):
    L = _labels(lang)
    out = [f"# {L['title']}", "", L["note"], ""]
    complete = True
    for model in models:
        out += [f"## {L['model']}: `{model}`", ""]
        for sc in scenarios[:max_scenarios]:
            sid = sc["id"]
            # A single *fixed* turn for all candidates in this scenario, not
            # whichever turn flatters each variant the most.
            turns = sc["turns"]
            index = next((i for i, t in enumerate(turns) if t.get("probe") or t.get("attack")), 0)
            turn = turns[index]
            prompt = turn.get(lang) or turn.get("en") or turn.get("es") or ""
            out += [f"### {sc.get('what', sid)}", "", f"**{L['ask']}:** {clip(prompt, 110)}", ""]
            for soul in souls:
                label = soul["label"]
                c = next((x for x in conversations if x.get("model") == model and x.get("soul") == label
                          and x.get("sid") == sid and x.get("run") == 1), None)
                r = c["res"][index] if c and index < len(c["res"]) else None
                out += [f"**{L['candidate']} `{label}`**"]
                if r and r.get("ok"):
                    out.append(_quote(clip(r.get("content"), limit)))
                else:
                    out.append(f"> *{L['no']}*" )
                    complete = False
                out.append("")
    if len(scenarios) > max_scenarios:
        out += [("Mostrando %d de %d escenarios; los demás están en el informe completo." if lang == "es" else "Showing %d of %d scenarios; the rest are in the full report.") % (max_scenarios, len(scenarios)), ""]
    if not complete:
        out += [L["partial"], ""]
    out += [L["caveat"], "", L["decide"], "", L["more"], ""]
    return "\n".join(out)


def terminal_preview(text, max_chars=5200):
    """Output stays digestible on terminals; full summary remains in choice-guide.md."""
    if len(text) <= max_chars:
        return text
    # Truncate at a paragraph boundary, never fabricate a summarization.
    cut = text[:max_chars].rfind("\n\n")
    return text[:cut if cut > max_chars // 2 else max_chars] + "\n\n[… más ejemplos en choice-guide.md / more examples in choice-guide.md]"

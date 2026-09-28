#!/usr/bin/env python3
"""Motor único del harness. Solo biblioteca estándar (Python 3.8+).

Toda la lógica vive aquí; hooks de git, hook de Claude Code, plugin de OpenCode,
Actions y scripts son envoltorios delgados. Datos: harness.json en la raíz.

Uso:
  harness.py riesgo [base]              bajo|medio|alto (detalle en stderr)
  harness.py cambio id|issue|propuesta|riesgo|nivel|roja
  harness.py nivel [base]               nivel efectivo y requisitos (JSON)
  harness.py ruta <skill>               a qué herramienta/agente/modelo va una skill
  harness.py skills [--check]           skills instaladas en el repo y cuáles están sin mapear
  harness.py analizar-skill <skill>     hechos de una skill (sin LLM) para clasificarla
  harness.py clasificar <skill> <clase> --motivo "..."   escribe la clase en harness.json (solo arquitecto)
  harness.py proceso --base B --body-file F   verificación del PR (lo usa la Action)
  harness.py guard-claude               hook PreToolUse de Claude Code (JSON por stdin)
  harness.py guard-opencode             guardia del plugin de OpenCode (JSON por stdin)
  harness.py hook pre-commit|commit-msg <archivo>|pre-push
  harness.py sync [--check]             regenera adaptadores desde harness.json
  harness.py estado                     regenera docs/ESTADO.md
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

NIVELES_RIESGO = ["bajo", "medio", "alto"]
EDIT_TOOLS_CLAUDE = {"Edit", "Write", "MultiEdit", "NotebookEdit"}
EDIT_TOOLS_OPENCODE = {"edit", "write", "patch", "multiedit"}
GENERADO = "GENERADO por scripts/harness.py sync — no editar a mano; edita harness.json"


# ----------------------------------------------------------------------------- utilidades

def git(*args, cwd=None):
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else ""


def raiz(cwd=None):
    top = git("rev-parse", "--show-toplevel", cwd=cwd)
    return Path(top) if top else Path(cwd or os.getcwd())


def cargar(root):
    p = Path(root) / "harness.json"
    if not p.exists():
        sys.stderr.write(f"harness.json no encontrado en {root}\n")
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def lista(cfg, ruta):
    d = cfg
    for k in ruta.split("."):
        d = d.get(k, {}) if isinstance(d, dict) else {}
    return d if isinstance(d, list) else []


def coincide_regex(rel, patrones):
    return any(re.search(p, rel) for p in patrones)


def coincide_prefijo(rel, prefijos):
    return any(rel == p.rstrip("/") or rel.startswith(p) for p in prefijos)


def max_riesgo(*niveles):
    v = [n for n in niveles if n in NIVELES_RIESGO]
    return max(v, key=NIVELES_RIESGO.index) if v else "bajo"


def override():
    return os.environ.get("HARNESS_OVERRIDE") == "1"


# ----------------------------------------------------------------------------- change de la rama

RAMA_RE = re.compile(r"^(feat|fix)/(?:(\d+)-)?([a-z0-9][a-z0-9-]*)$")


def rama(root):
    return os.environ.get("HARNESS_BRANCH") or git("branch", "--show-current", cwd=root)


def partes_rama(nombre):
    m = RAMA_RE.match(nombre or "")
    return (m.group(1), m.group(2), m.group(3)) if m else (None, None, None)


def propuesta(root, change_id):
    if not change_id:
        return None
    activo = Path(root) / "openspec/changes" / change_id / "proposal.md"
    if activo.exists():
        return activo
    arch = Path(root) / "openspec/changes/archive"
    if arch.exists():
        cands = sorted(d for d in arch.iterdir() if d.is_dir() and d.name.endswith("-" + change_id))
        if cands and (cands[-1] / "proposal.md").exists():
            return cands[-1] / "proposal.md"
    return None


def bloque_harness(texto):
    datos = {}
    for clave, patron in {
        "issue": r"Issue:\s*#?(\d+)",
        "riesgo": r"Riesgo:\s*(bajo|medio|alto)",
        "nivel": r"Nivel:\s*([0-3])",
        "roja": r"OpenCode-zona-roja:\s*(autorizado|no)",
    }.items():
        ms = re.findall(r"(?im)^[-*\s]*" + patron, texto)
        if ms:
            datos[clave] = ms[-1].lower()
    return datos


def info_cambio(root):
    tipo, issue, cid = partes_rama(rama(root))
    prop = propuesta(root, cid)
    bloque = bloque_harness(prop.read_text(encoding="utf-8")) if prop else {}
    return {"tipo": tipo, "issue": issue, "id": cid, "propuesta": str(prop) if prop else None, **{f"declarado_{k}": v for k, v in bloque.items()}}


# ----------------------------------------------------------------------------- riesgo y nivel

def diff(root, base):
    archivos = [f for f in git("diff", "--name-only", f"{base}...HEAD", cwd=root).splitlines() if f]
    lineas = 0
    for ln in git("diff", "--numstat", f"{base}...HEAD", cwd=root).splitlines():
        a, b, *_ = ln.split("\t") + ["", ""]
        lineas += (int(a) if a.isdigit() else 0) + (int(b) if b.isdigit() else 0)
    return archivos, lineas


def calcular_riesgo(root, base="main"):
    cfg = cargar(root)
    u = cfg.get("umbrales", {})
    archivos, lineas = diff(root, base)
    alto, bajo = lista(cfg, "zonas.alto"), lista(cfg, "zonas.bajo")
    sensibles = [f for f in archivos if coincide_regex(f, alto)]
    if not archivos:
        calc, det = "bajo", "sin cambios"
    elif sensibles:
        calc, det = "alto", "toca rutas sensibles: " + ", ".join(sensibles)
    elif len(archivos) > u.get("archivos", 5) or lineas > u.get("lineas", 300):
        calc, det = "medio", f"{len(archivos)} archivos, {lineas} líneas"
    elif any(not coincide_regex(f, bajo) for f in archivos):
        calc, det = "medio", f"cambia código de producción ({len(archivos)} archivos, {lineas} líneas)"
    else:
        calc, det = "bajo", f"solo docs/tests/config ({len(archivos)} archivos)"
    declarado = info_cambio(root).get("declarado_riesgo")
    final = max_riesgo(calc, declarado)
    if declarado and final != calc:
        det += f" · sube a {final} por el Riesgo: declarado en el proposal"
    return {"riesgo": final, "calculado": calc, "declarado": declarado, "detalle": det, "archivos": len(archivos), "lineas": lineas}


def calcular_nivel(root, base="main"):
    cfg = cargar(root)
    r = calcular_riesgo(root, base)
    c = info_cambio(root)
    trivial = cfg.get("umbrales", {}).get("trivial_lineas", 20)
    if c["propuesta"]:
        declarado = int(c.get("declarado_nivel") or 2)
        minimo = {"bajo": 1, "medio": 1, "alto": 3}[r["riesgo"]]
        nivel = max(declarado, minimo)
    else:
        nivel = 0
    req = {
        "change": nivel >= 1,
        "issue": nivel >= 2,
        "revision_1": nivel >= 1,
        "revision_2": nivel >= 1 and r["riesgo"] in ("medio", "alto"),
        "revision_3": r["riesgo"] == "alto",
        "ok_final": nivel >= 1,
        "nivel0_permitido": r["riesgo"] == "bajo" and r["lineas"] <= trivial,
    }
    return {"nivel": nivel, "riesgo": r, "cambio": c, "requisitos": req}


# ----------------------------------------------------------------------------- proceso (PR)

def verificar_proceso(root, base, body):
    errores = []
    nombre = rama(root)
    tipo, issue, cid = partes_rama(nombre)
    if not (tipo or re.match(r"^(chore|docs)/", nombre or "")):
        return [f"Rama '{nombre}' fuera de convención: feat/<id>, feat/<issue>-<id>, fix/<slug>, fix/<issue>-<id>, chore/..., docs/..."]
    n = calcular_nivel(root, base)
    req, r = n["requisitos"], n["riesgo"]
    marcado = lambda etiqueta: re.search(r"- \[x\][^\n]*" + re.escape(etiqueta), body or "", re.I) is not None
    if tipo == "feat" and not n["cambio"]["propuesta"]:
        errores.append(f"Falta openspec/changes/{cid}/proposal.md (o su archivo en archive/). Ábrelo con /cambio.")
    if n["nivel"] == 0 and tipo in ("fix", None) and not req["nivel0_permitido"] and not re.match(r"^(chore|docs)/", nombre):
        errores.append(f"Sin change solo se permiten cambios triviales (riesgo bajo y ≤ {cargar(root).get('umbrales', {}).get('trivial_lineas', 20)} líneas); salió riesgo {r['riesgo']} con {r['lineas']} líneas. Abre el change con /cambio.")
    if req["issue"]:
        num = issue or n["cambio"].get("declarado_issue")
        if not num:
            errores.append(f"Nivel {n['nivel']}: el change necesita issue (rama feat/<n>-<id> o 'Issue: #n' en ## Harness).")
        elif not re.search(rf"#{num}\b", body or ""):
            errores.append(f"El PR debe enlazar el issue (#{num}).")
    if req["revision_1"] and not marcado("Revisión 1"):
        errores.append("Falta marcar Revisión 1 (@revisor-gratis).")
    if req["revision_2"] and not marcado("Revisión 2"):
        errores.append(f"Riesgo {r['riesgo']}: falta Revisión 2 (@revisor-fuerte).")
    if req["revision_3"] and not marcado("Revisión 3"):
        errores.append("Riesgo alto: falta Revisión 3 (/codex:review, Luna) + tu lectura.")
    if req["ok_final"] and not marcado("OK final"):
        errores.append("Falta el OK final de Claude Code (/juzgar-pr).")
    return errores


# ----------------------------------------------------------------------------- rutas por skill

def ruta_skill(cfg, skill):
    clase = cfg.get("skills", {}).get(skill)
    if not clase:
        return {"skill": skill, "clase": "sin-mapear", "origen": "no está en harness.json", "herramienta": None, "agente": None,
                "modelo": None, "sugerencia": sugerencia_prefijo(cfg, skill),
                "que": f"Skill nueva sin clasificar: se bloquea en ambas herramientas. En Claude Code corre /clasificar-skill {skill}."}
    origen = "harness.json"
    info = dict(cfg.get("clases", {}).get(clase, {}))
    modelo = None
    if info.get("agente"):
        modelo = cfg.get("agentes", {}).get(info["agente"])
    elif info.get("modelo", "").startswith("claude."):
        modelo = cfg.get("claude", {}).get(info["modelo"].split(".", 1)[1])
    return {"skill": skill, "clase": clase, "origen": origen, "herramienta": info.get("herramienta"), "agente": info.get("agente"), "modelo": modelo, "que": info.get("que", "")}


def sugerencia_prefijo(cfg, skill):
    for pref, c in sorted(cfg.get("skills_por_prefijo", {}).items(), key=lambda kv: -len(kv[0])):
        if skill.startswith(pref):
            return c
    return None


def puede_correr_en(rt, herramienta):
    """None si puede; si no, el motivo."""
    if rt["clase"] == "sin-mapear":
        return "sin-mapear"
    if rt["clase"] == "prohibido":
        return "prohibido"
    if rt["herramienta"] in ("cualquiera", herramienta):
        return None
    return "otra-herramienta"


def texto_ruta(rt):
    if rt["clase"] == "prohibido":
        return f"⛔ {rt['skill']}: prohibida. {rt['que']}"
    if rt["clase"] == "sin-mapear":
        sug = f" (sugerencia por prefijo: {rt['sugerencia']})" if rt.get("sugerencia") else ""
        return f"⛔ {rt['skill']}: sin mapear{sug}. {rt['que']}"
    if rt["herramienta"] == "cualquiera":
        return f"{rt['skill']} → clase libre → Claude Code u OpenCode\n  {rt['que']}"
    donde = "Claude Code (scripts/arq)" if rt["herramienta"] == "claude" else f"OpenCode (scripts/ejec) · agente {rt['agente']}"
    return f"{rt['skill']} → clase {rt['clase']} ({rt['origen']}) → {donde} · modelo: {rt['modelo']}\n  {rt['que']}"


def nombre_skill(args):
    for k in ("skill", "name", "command", "skill_name"):
        v = args.get(k) if isinstance(args, dict) else None
        if isinstance(v, str) and v.strip():
            return v.strip().lstrip("/").split()[0].split(":")[-1] if k == "command" else v.strip()
    return None


# ----------------------------------------------------------------------------- inventario, análisis y clasificación de skills

DIRS_SKILLS = [".claude/skills", ".agents/skills", ".opencode/skills", ".cursor/skills"]

SENALES = {
    "escribe_codigo": r"\b(implement|write code|writes? (the )?code|edit(s|ing)? (files|code)|apply (the )?changes?|refactor|fix(es)? (the )?bug|produc(e|es) (a )?diff)\b|implementa|escribe código",
    "git": r"\bgit (commit|push|checkout|branch)|\bcreate (a )?(branch|commit|pull request|PR)\b|gh pr",
    "revisa": r"\b(review|adversarial|critique|audit|lens(es)?|edge[- ]case)\b|revisi[oó]n",
    "lee_mucho": r"\b(research|recon|scan|investigat|explore the (repo|codebase)|read (the )?(entire|whole))\b|investiga",
    "decide_contrato": r"\b(architecture|PRD|spec(ification)?|decision record|ADR|scope)\b|arquitectura",
    "redacta": r"\b(brief|brainstorm|elicit|draft|story|stories|epic|persona|ux)\b",
    "tests": r"\b(test(s|ing)?|e2e|playwright|coverage)\b",
}


def skills_instaladas(root):
    vistas = {}
    for d in DIRS_SKILLS:
        base = Path(root) / d
        if base.is_dir():
            for s in sorted(base.iterdir()):
                if (s / "SKILL.md").exists():
                    vistas.setdefault(s.name, []).append(str((s / "SKILL.md").relative_to(root)))
    return vistas


def estado_skills(root):
    cfg = cargar(root)
    inst = skills_instaladas(root)
    mapeadas = cfg.get("skills", {})
    return {"instaladas": inst, "sin_mapear": sorted(s for s in inst if s not in mapeadas),
            "mapeadas_no_instaladas": sorted(s for s in mapeadas if s not in inst)}


def analizar_skill(root, skill):
    cfg = cargar(root)
    inst = skills_instaladas(root).get(skill, [])
    if not inst:
        return {"skill": skill, "encontrada": False, "buscada_en": DIRS_SKILLS}
    principal = Path(root) / inst[0]
    texto = principal.read_text(encoding="utf-8", errors="replace")
    refs = sorted(set(re.findall(r"[\w{}./-]+\.(?:md|py|csv|yaml|toml)", texto)))
    extra = ""
    for r in refs:
        p = (principal.parent / r) if not r.startswith("{") else None
        if p and p.exists() and p.stat().st_size < 200_000:
            extra += "\n" + p.read_text(encoding="utf-8", errors="replace")
    todo = texto + extra
    fm = re.search(r"(?s)^---\n(.*?)\n---", texto)
    desc = re.search(r"(?m)^description:\s*(.+)$", fm.group(1)).group(1).strip("'\" ") if fm and re.search(r"(?m)^description:", fm.group(1)) else ""
    senales = {k: len(re.findall(v, todo, re.I)) for k, v in SENALES.items()}
    return {"skill": skill, "encontrada": True, "archivos": inst, "descripcion": desc,
            "tamano_bytes": len(todo.encode()), "tokens_aprox": len(todo) // 4, "referencias": refs,
            "usa_render_bmad": "render_skill.py" in texto, "senales": senales,
            "sugerencia_prefijo": sugerencia_prefijo(cfg, skill), "clases_validas": sorted(k for k in cfg.get("clases", {}) if not k.startswith("_"))}


def clasificar(root, skill, clase, motivo):
    p = Path(root) / "harness.json"
    cfg = json.loads(p.read_text(encoding="utf-8"))
    if clase not in cfg.get("clases", {}):
        raise SystemExit(f"clase '{clase}' no existe; válidas: {', '.join(k for k in cfg['clases'] if not k.startswith('_'))}")
    if not motivo:
        raise SystemExit("--motivo es obligatorio: deja la evidencia de por qué esa clase")
    cfg.setdefault("skills", {})[skill] = clase
    from datetime import date
    cfg.setdefault("skills_motivos", {})[skill] = f"{date.today().isoformat()} · {clase} · {motivo}"
    p.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return cfg["skills_motivos"][skill]


# ----------------------------------------------------------------------------- guardias

def raiz_git_de(path):
    d = Path(path).parent
    while d != d.parent:
        if (d / ".git").exists():
            return d
        d = d.parent
    return None


def objetivos_bash(cmd):
    objs = []
    objs += re.findall(r"(?<![0-9&<])>{1,2}\s*([^\s;&|<>]+)", cmd)
    objs += re.findall(r"\btee\s+(?:-a\s+)?([^\s;&|]+)", cmd)
    objs += re.findall(r"\b(?:sed|perl)\s+-[a-zA-Z]*i[^\s]*\s+(?:'[^']*'|\"[^\"]*\"|\S+)\s+([^\s;&|]+)", cmd)
    for m in re.finditer(r"\b(?:cp|mv|install)\s+(?:-\S+\s+)*(?:\S+\s+)+?(\S+)\s*(?:$|[;&|])", cmd):
        objs.append(m.group(1))
    return [o.strip("'\"") for o in objs if not o.startswith("&")]


def guard_claude(data, root=None):
    """Devuelve (codigo, mensaje). 2 = bloquear."""
    if override():
        return 0, ""
    root = Path(root or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
    tool, ti = data.get("tool_name", ""), data.get("tool_input", {}) or {}

    def permitido(p):
        ap = Path(p) if os.path.isabs(p) else (root / p)
        ap = Path(os.path.abspath(ap))
        if str(ap).startswith("/dev/"):
            return True, str(ap)
        base = raiz_git_de(ap)
        if base is None:
            return True, str(ap)
        cfg = cargar(base) or cargar(root)
        rel = os.path.relpath(ap, base)
        return coincide_prefijo(rel, lista(cfg, "permisos.arquitecto_puede")), rel

    def bloqueo(objetivo):
        return 2, (f"⛔ Harness — rol ARQUITECTO: Claude Code no implementa código de la aplicación.\n"
                   f"Bloqueado: {tool} sobre `{objetivo}`.\n\nCómo hacerlo bien:\n"
                   f"  1. Cambio normal → /cambio y ejecútalo en OpenCode: `scripts/ejec` → /ejecutar-cambio <id>.\n"
                   f"     Si estás en una skill bmad-*: BMAD no ejecuta; entrega el dossier y nombra /cambio o /opsx:update <id>.\n"
                   f"  2. Arreglo < 20 líneas en /juzgar-pr, o zona roja asignada a Claude → el humano relanza con HARNESS_OVERRIDE=1 scripts/arq\n\n"
                   f"Explícale esto al usuario tal cual. No intentes editar el archivo por otra vía (bash, python, git apply).")

    if tool in EDIT_TOOLS_CLAUDE:
        p = ti.get("file_path") or ti.get("notebook_path") or ""
        if p:
            ok, rel = permitido(p)
            if not ok:
                return bloqueo(rel)
        return 0, ""
    if tool == "Bash":
        cmd = ti.get("command", "") or ""
        if re.search(r"\bgit\s+apply\b|\bpatch\s+-p\d", cmd):
            return bloqueo("git apply / patch")
        for o in objetivos_bash(cmd):
            ok, rel = permitido(o)
            if not ok:
                return bloqueo(rel)
        return 0, ""
    if tool == "Skill":
        skill = nombre_skill(ti)
        if not skill:
            return 0, ""
        rt = ruta_skill(cargar(root), skill)
        motivo = puede_correr_en(rt, "claude")
        if motivo == "sin-mapear":
            return 2, (f"⛔ Harness — lista blanca: la skill `{skill}` no está clasificada en harness.json, así que está bloqueada en ambas herramientas.\n"
                       f"Cómo seguir: corre /clasificar-skill {skill} (analiza qué hace, propone clase y modelo con evidencia, y espera tu confirmación).\n"
                       f"No la ejecutes ni leas su workflow para hacer la tarea por otra vía.")
        if motivo:
            return 2, (f"⛔ Harness — enrutamiento de skills: `{skill}` no se corre en Claude Code.\n{texto_ruta(rt)}\n"
                       f"Explícale esto al usuario y dile exactamente dónde correrla. Tabla completa: docs/harness/RUTAS.md")
    return 0, ""


def guard_opencode(tool, args, root=None):
    """Devuelve {'block': bool, 'msg': str}."""
    if override():
        return {"block": False, "msg": ""}
    root = Path(root or os.getcwd())
    cfg = cargar(root)
    t = (tool or "").lower()

    def bloqueo(motivo, como):
        return {"block": True, "msg": f"⛔ Harness — rol EJECUTOR: {motivo}\nCómo hacerlo bien: {como}\nExplícale esto al usuario tal cual y no intentes hacerlo por otra vía."}

    if t in EDIT_TOOLS_OPENCODE:
        p = args.get("filePath") or args.get("path") or args.get("file")
        if not p:
            return {"block": False, "msg": ""}
        rel = os.path.relpath(p if os.path.isabs(p) else root / p, root)
        if coincide_regex(rel, lista(cfg, "permisos.ejecutor_no_puede")):
            return bloqueo(f"`{rel}` es un artefacto del arquitecto (proposal/design/specs, specs publicadas, BMAD, reglas, CI o harness.json).",
                           "solo editas código, openspec/changes/<id>/tasks.md y _bmad-output/digests/. Escribe el hueco en HANDOFF.md y pide /opsx:update <id> en Claude Code.")
        if coincide_regex(rel, lista(cfg, "zonas.alto")) and info_cambio(root).get("declarado_roja") != "autorizado":
            return bloqueo(f"`{rel}` está en zona roja y el proposal de esta rama no autoriza a OpenCode.",
                           "Claude Code debe poner 'OpenCode-zona-roja: autorizado' en ## Harness del proposal (con pasos cerrados), o implementarlo él.")
    elif t == "bash":
        c = str(args.get("command", ""))
        if re.search(r"\bopenspec\s+archive\b", c):
            return bloqueo("archivar publica verdad en openspec/specs/: es decisión del arquitecto.", "deja el PR listo; el usuario corre /juzgar-pr <n> en Claude Code.")
        if re.search(r"\bgh\s+pr\s+merge\b", c):
            return bloqueo("mergear PRs es decisión del arquitecto.", "deja el PR abierto; el usuario corre /juzgar-pr <n> en Claude Code.")
        if re.search(r"\bgit\s+push\b[^;&|]*\b(main|master)\b", c):
            return bloqueo("no se hace push a main.", "haz push de tu rama y marca el PR listo con gh pr ready.")
    elif t == "skill":
        skill = nombre_skill(args)
        if skill:
            rt = ruta_skill(cfg, skill)
            motivo = puede_correr_en(rt, "opencode")
            if motivo == "sin-mapear":
                return bloqueo(f"la skill `{skill}` no está clasificada en harness.json.", f"pide al usuario que en Claude Code corra /clasificar-skill {skill}; OpenCode no puede clasificarla.")
            if motivo:
                return bloqueo(f"la skill `{skill}` no se corre en OpenCode.", texto_ruta(rt) + " · Tabla: docs/harness/RUTAS.md")
    return {"block": False, "msg": ""}


# ----------------------------------------------------------------------------- git hooks

def hook_pre_commit(root):
    rol = os.environ.get("HARNESS_ROL", "humano")
    if override() or rol == "humano":
        return 0
    cfg = cargar(root)
    staged = [f for f in git("diff", "--cached", "--name-only", cwd=root).splitlines() if f]
    actual = git("branch", "--show-current", cwd=root)
    def rechazo(motivo, como):
        sys.stderr.write(f"\n⛔ Harness ({rol}): {motivo}\n   Cómo hacerlo bien: {como}\n   Override consciente: HARNESS_OVERRIDE=1 (queda registrado en el commit)\n\n")
        return 1
    if rol == "arquitecto":
        for f in staged:
            if not coincide_prefijo(f, lista(cfg, "permisos.arquitecto_puede")):
                return rechazo(f"Claude (arquitecto) intenta commitear código de la app: {f}", "abre el change con /cambio y ejecútalo en OpenCode (scripts/ejec → /ejecutar-cambio <id>).")
    elif rol == "ejecutor":
        if actual in ("main", "master"):
            return rechazo(f"OpenCode no commitea en {actual}.", "trabaja en la rama del change (feat/<id> o feat/<n>-<id>).")
        autorizado = info_cambio(root).get("declarado_roja") == "autorizado"
        for f in staged:
            if coincide_regex(f, lista(cfg, "permisos.ejecutor_no_puede")):
                return rechazo(f"OpenCode (ejecutor) intenta commitear un artefacto del arquitecto: {f}", "solo código, tasks.md del change y _bmad-output/digests/; deja la propuesta en HANDOFF.md para /opsx:update.")
            if coincide_regex(f, lista(cfg, "zonas.alto")) and not autorizado:
                return rechazo(f"zona roja sin autorización en el proposal: {f}", "Claude debe poner 'OpenCode-zona-roja: autorizado' en ## Harness del proposal, o implementarlo él.")
    return 0


def hook_commit_msg(ruta_msg):
    if override():
        p = Path(ruta_msg)
        t = p.read_text(encoding="utf-8")
        if "Harness-Override:" not in t:
            p.write_text(t.rstrip("\n") + f"\n\nHarness-Override: yes (rol: {os.environ.get('HARNESS_ROL', 'humano')})\n", encoding="utf-8")
    return 0


def hook_pre_push(stdin_text):
    rol = os.environ.get("HARNESS_ROL", "humano")
    if override() or rol == "humano":
        return 0
    for ln in stdin_text.splitlines():
        partes = ln.split()
        if len(partes) >= 3 and partes[2] in ("refs/heads/main", "refs/heads/master"):
            sys.stderr.write(f"\n⛔ Harness ({rol}): los agentes no hacen push a {partes[2].split('/')[-1]}.\n   Cómo hacerlo bien: push de tu rama + PR; el merge lo decide /juzgar-pr.\n\n")
            return 1
    return 0


# ----------------------------------------------------------------------------- sync (adaptadores generados)

def generar_rutas(cfg):
    L = [f"# Rutas del harness\n", f"<!-- {GENERADO} -->\n",
         "Cada skill de BMAD y OpenSpec pertenece a una clase; la clase decide herramienta y modelo. "
         "Las guardias bloquean correr una skill en la herramienta equivocada. Consulta rápida: `python3 scripts/harness.py ruta <skill>`.\n",
         "## Clases\n", "| Clase | Herramienta | Agente / modelo | Qué |", "|---|---|---|---|"]
    for nombre, c in cfg.get("clases", {}).items():
        if nombre.startswith("_"):
            continue
        if c.get("agente"):
            am = f"`{c['agente']}` · `{cfg.get('agentes', {}).get(c['agente'], '?')}`"
        elif c.get("modelo", "").startswith("claude."):
            am = cfg.get("claude", {}).get(c["modelo"].split(".", 1)[1], "?")
        else:
            am = "—"
        L.append(f"| {nombre} | {c.get('herramienta') or '— (bloqueada)'} | {am} | {c.get('que', '')} |")
    L += ["", "## Skills", "| Skill | Clase |", "|---|---|"]
    for s, c in sorted(cfg.get("skills", {}).items(), key=lambda kv: (kv[1], kv[0])):
        L.append(f"| `{s}` | {c} |")
    L += ["", "**Skills no listadas: bloqueadas en ambas herramientas** hasta clasificarlas con `/clasificar-skill <nombre>` en Claude Code.", "",
          "## Niveles de ceremonia", "| Nivel | Qué lleva |", "|---|---|"]
    for n, d in sorted(cfg.get("niveles", {}).items()):
        L.append(f"| {n} | {d} |")
    L += ["", "Revisiones por riesgo: bajo → Revisión 1 · medio → + Revisión 2 · alto → + Revisión 3 (Luna) y lectura humana; el riesgo alto sube el nivel a 3.", "",
          "## Zonas", "**Alto (rojo):**", *[f"- `{p}`" for p in lista(cfg, "zonas.alto")], "", "**Bajo (sin código de producción):**", *[f"- `{p}`" for p in lista(cfg, "zonas.bajo")], "",
          "## Modelos por agente de OpenCode", "| Agente | Modelo |", "|---|---|",
          *[f"| `{a}` | `{m}` |" for a, m in cfg.get("agentes", {}).items() if not a.startswith("_")], ""]
    return "\n".join(L)


def sync(root, check=False):
    root = Path(root)
    cfg = cargar(root)
    salidas = {}
    rutas = generar_rutas(cfg)
    sm = estado_skills(root)["sin_mapear"]
    if sm:
        rutas += "\n## ⛔ Instaladas y sin mapear (bloqueadas)\n" + "\n".join(f"- `{s}` → `/clasificar-skill {s}`" for s in sm) + "\n"
    salidas[root / "docs/harness/RUTAS.md"] = rutas
    agentes = {k: v for k, v in cfg.get("agentes", {}).items() if not k.startswith("_")}
    for agente, modelo in agentes.items():
        p = root / ".opencode/agents" / f"{agente}.md"
        if p.exists():
            t = p.read_text(encoding="utf-8")
            salidas[p] = re.sub(r"(?m)^model:.*$", f"model: {modelo}", t, count=1)
    oj = root / "opencode.json"
    if oj.exists():
        d = json.loads(oj.read_text(encoding="utf-8"))
        if agentes.get("build"):
            d["model"] = agentes["build"]
        if agentes.get("explorador"):
            d["small_model"] = agentes["explorador"]
        omni = sorted({m.split("/", 1)[1] for m in agentes.values() if m.startswith("omniroute/")})
        prov = d.setdefault("provider", {}).setdefault("omniroute", {})
        prov["models"] = {m: prov.get("models", {}).get(m, {"name": m}) for m in omni}
        salidas[oj] = json.dumps(d, ensure_ascii=False, indent=2) + "\n"
    if (root / ".cursor").exists():
        salidas[root / ".cursor/rules/harness.mdc"] = ("---\ndescription: Harness de copilotos (reglas en AGENTS.md)\nalwaysApply: true\n---\n"
                                                      f"<!-- {GENERADO} -->\nLas reglas del repo y del método están en `AGENTS.md` y `.claude/rules/workflow-routing.md`. "
                                                      "Rutas por skill y modelos: `docs/harness/RUTAS.md`. No dupliques reglas aquí.\n")
    cambiados = []
    for p, contenido in salidas.items():
        actual = p.read_text(encoding="utf-8") if p.exists() else None
        if actual != contenido:
            cambiados.append(str(p.relative_to(root)))
            if not check:
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(contenido, encoding="utf-8")
    return cambiados


# ----------------------------------------------------------------------------- estado (generado)

def gh_json(args, root):
    try:
        r = subprocess.run(["gh", *args], cwd=root, capture_output=True, text=True, timeout=30)
        return json.loads(r.stdout) if r.returncode == 0 and r.stdout.strip() else None
    except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError):
        return None


def estado(root):
    root = Path(root)
    ch = root / "openspec/changes"
    activos = sorted(d.name for d in ch.iterdir() if d.is_dir() and d.name != "archive") if ch.exists() else []
    arch = sorted((d.name for d in (ch / "archive").iterdir() if d.is_dir()), reverse=True) if (ch / "archive").exists() else []
    specs = sorted(d.name for d in (root / "openspec/specs").iterdir() if d.is_dir()) if (root / "openspec/specs").exists() else []
    L = ["# Estado del proyecto", "", f"<!-- GENERADO por scripts/harness.py estado — no editar; la fuente son openspec/ y los issues de GitHub -->", ""]
    L += [f"## Changes activos ({len(activos)})", *([f"- `{a}`" for a in activos] or ["- ninguno"]), ""]
    L += [f"## Últimos archivados ({len(arch)} en total)", *([f"- `{a}`" for a in arch[:15]] or ["- ninguno"]), ""]
    L += [f"## Capacidades publicadas ({len(specs)})", ", ".join(f"`{s}`" for s in specs) or "ninguna", ""]
    for etiqueta, titulo in (("verificacion-diferida", "Verificaciones diferidas"), ("deuda", "Deudas abiertas")):
        issues = gh_json(["issue", "list", "--label", etiqueta, "--state", "open", "--json", "number,title,url", "--limit", "100"], root)
        L.append(f"## {titulo}")
        if issues is None:
            L.append(f"- (gh no disponible: consulta `gh issue list --label {etiqueta}`)")
        else:
            L += [f"- [#{i['number']}]({i['url']}) {i['title']}" for i in issues] or ["- ninguna"]
        L.append("")
    L += ["Decisiones vigentes del usuario: `docs/DECISIONES.md` (append-only).", ""]
    p = root / "docs/ESTADO.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(L), encoding="utf-8")
    return str(p)


# ----------------------------------------------------------------------------- CLI

def main(argv):
    if not argv:
        print(__doc__)
        return 2
    cmd, args = argv[0], argv[1:]
    root = raiz()
    if cmd == "riesgo":
        r = calcular_riesgo(root, args[0] if args else "main")
        sys.stderr.write(f"{r['riesgo']}: {r['detalle']}\n")
        print(r["riesgo"])
        return 0
    if cmd == "cambio":
        c = info_cambio(root)
        q = args[0] if args else "id"
        if q == "roja":
            return 0 if c.get("declarado_roja") == "autorizado" else 1
        v = {"id": c["id"], "issue": c["issue"] or c.get("declarado_issue"), "propuesta": c["propuesta"], "riesgo": c.get("declarado_riesgo"), "nivel": c.get("declarado_nivel")}.get(q)
        if v:
            print(v)
            return 0
        return 1
    if cmd == "nivel":
        print(json.dumps(calcular_nivel(root, args[0] if args else "main"), ensure_ascii=False, indent=2))
        return 0
    if cmd == "ruta":
        if not args:
            print("uso: harness.py ruta <skill>")
            return 2
        print(texto_ruta(ruta_skill(cargar(root), args[0])))
        return 0
    if cmd == "skills":
        e = estado_skills(root)
        print(f"instaladas: {len(e['instaladas'])} · sin mapear: {len(e['sin_mapear'])} · mapeadas y no instaladas: {len(e['mapeadas_no_instaladas'])}")
        for s in e["sin_mapear"]:
            print(f"⛔ sin mapear: {s}  →  en Claude Code: /clasificar-skill {s}")
        if "--check" in args:
            return 1 if e["sin_mapear"] else 0
        return 0
    if cmd == "analizar-skill":
        if not args:
            print("uso: harness.py analizar-skill <skill>")
            return 2
        print(json.dumps(analizar_skill(root, args[0]), ensure_ascii=False, indent=2))
        return 0
    if cmd == "clasificar":
        if len(args) < 2:
            print('uso: harness.py clasificar <skill> <clase> --motivo "..."')
            return 2
        if os.environ.get("HARNESS_ROL") == "ejecutor":
            sys.stderr.write("⛔ Solo el arquitecto (Claude Code) clasifica skills.\n")
            return 1
        motivo = args[args.index("--motivo") + 1] if "--motivo" in args else ""
        print("clasificada:", args[0], "·", clasificar(root, args[0], args[1], motivo))
        print("\n".join(sync(root)) or "adaptadores al día")
        return 0
    if cmd == "proceso":
        base = args[args.index("--base") + 1] if "--base" in args else "main"
        body = Path(args[args.index("--body-file") + 1]).read_text(encoding="utf-8") if "--body-file" in args else ""
        errores = verificar_proceso(root, base, body)
        n = calcular_nivel(root, base)
        print(f"nivel={n['nivel']} riesgo={n['riesgo']['riesgo']} ({n['riesgo']['detalle']})")
        for e in errores:
            print(f"⛔ {e}")
        return 1 if errores else 0
    if cmd == "guard-claude":
        codigo, msg = guard_claude(json.load(sys.stdin))
        if msg:
            sys.stderr.write(msg + "\n")
        return codigo
    if cmd == "guard-opencode":
        d = json.load(sys.stdin)
        print(json.dumps(guard_opencode(d.get("tool", ""), d.get("args", {}) or {}, d.get("root") or root), ensure_ascii=False))
        return 0
    if cmd == "hook":
        h = args[0] if args else ""
        if h == "pre-commit":
            return hook_pre_commit(root)
        if h == "commit-msg":
            return hook_commit_msg(args[1])
        if h == "pre-push":
            return hook_pre_push(sys.stdin.read())
        return 2
    if cmd == "sync":
        cambiados = sync(root, check="--check" in args)
        if "--check" in args:
            if cambiados:
                print("Adaptadores desactualizados respecto a harness.json:\n  " + "\n  ".join(cambiados) + "\nCorre: python3 scripts/harness.py sync")
                return 1
            print("adaptadores al día")
            return 0
        print("regenerados:\n  " + "\n  ".join(cambiados) if cambiados else "nada que regenerar")
        return 0
    if cmd == "estado":
        print("escrito", estado(root))
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except BrokenPipeError:  # p. ej. `harness.py ruta x | head -1`
        sys.exit(0)

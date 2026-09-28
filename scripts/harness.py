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
  harness.py revision registrar|listar  evidencia de revisión atada al commit (reemplaza las casillas del PR)
  harness.py presupuesto                consumo del change frente al presupuesto de su nivel
  harness.py telemetria registrar|resumen   métricas por change en .harness/telemetria.jsonl
  harness.py versiones [--check]        versiones fijadas (.harness/versiones.json) vs instaladas
  harness.py fijar-acciones [--aplicar] fija las GitHub Actions a su SHA (usa gh)
  harness.py secretos-listar            archivos secretos del repo (los enmascara el contenedor)
  harness.py doctor [--tests]           diagnóstico del harness (config, control, secretos, versiones)

Variables: HARNESS_CONFIG (ruta de harness.json; el gate de CI usa la de la rama base),
HARNESS_ROL (arquitecto|ejecutor|humano), HARNESS_OVERRIDE=1 (salto consciente, queda registrado).
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


class ConfigError(Exception):
    """harness.json ausente o inválido: los guardias de agentes fallan CERRADOS."""


def ruta_config(root):
    return Path(os.environ.get("HARNESS_CONFIG") or (Path(root) / "harness.json"))


def cargar(root, estricto=False):
    p = ruta_config(root)
    if not p.exists():
        if estricto:
            raise ConfigError(f"no existe {p}")
        sys.stderr.write(f"harness.json no encontrado en {root}\n")
        return {}
    try:
        cfg = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ConfigError(f"{p} no es JSON válido: {e}")
    if estricto:
        for clave in ("zonas", "permisos", "secretos", "control_plane", "skills", "clases"):
            if clave not in cfg:
                raise ConfigError(f"{p} no tiene la sección '{clave}'")
    return cfg


_CONFIABLE = {}


def ref_confiable(root):
    """origin/main si existe; si no, HEAD. Los guardias usan esta config: editar harness.json sin mergear no amplía permisos."""
    for ref in ("origin/main", "HEAD"):
        if subprocess.run(["git", "cat-file", "-e", f"{ref}:harness.json"], cwd=root, capture_output=True).returncode == 0:
            return ref
    return None


def cargar_confiable(root):
    if os.environ.get("HARNESS_CONFIG"):
        return cargar(root, estricto=True)
    root = str(root)
    if root in _CONFIABLE:
        return _CONFIABLE[root]
    ref = ref_confiable(root)
    if ref is None:
        cfg = cargar(root, estricto=True)
    else:
        texto = subprocess.run(["git", "show", f"{ref}:harness.json"], cwd=root, capture_output=True, text=True).stdout
        try:
            cfg = json.loads(texto)
        except json.JSONDecodeError as e:
            raise ConfigError(f"{ref}:harness.json no es JSON válido: {e}")
        for clave in ("zonas", "permisos", "secretos", "control_plane", "skills", "clases"):
            if clave not in cfg:
                raise ConfigError(f"{ref}:harness.json no tiene la sección '{clave}'")
        # si el árbol de trabajo tiene harness.json roto, también se falla cerrado (señal de manipulación o error)
        cargar(root, estricto=True)
    _CONFIABLE[root] = cfg
    return cfg


def lista(cfg, ruta):
    d = cfg
    for k in ruta.split("."):
        d = d.get(k, {}) if isinstance(d, dict) else {}
    return d if isinstance(d, list) else []


def coincide_regex(rel, patrones):
    return any(re.search(p, rel) for p in patrones)


def coincide_prefijo(rel, prefijos):
    return any(rel == p.rstrip("/") or rel.startswith(p) for p in prefijos)


def es_secreto(cfg, ruta):
    r = str(ruta).replace("\\", "/")
    if coincide_regex(r, lista(cfg, "secretos.excepto")):
        return False
    return coincide_regex(r, lista(cfg, "secretos.rutas"))


def secretos_en_comando(cfg, cmd):
    """Motivos por los que un comando de shell expone secretos (heurística; ver docs/SEGURIDAD.md)."""
    motivos = [f"patrón {p}" for p in lista(cfg, "secretos.comandos") if re.search(p, cmd)]
    for tok in re.findall(r"[^\s'\"|;&<>()`=]+", cmd):
        t = tok.lstrip("@")
        if es_secreto(cfg, t):
            motivos.append(f"ruta {t}")
    return motivos


def es_control(cfg, rel):
    return coincide_regex(rel, lista(cfg, "control_plane.rutas"))


def secretos_en_texto(cfg, texto):
    return [p for p in lista(cfg, "secretos.contenido") if re.search(p, texto)]


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
    """--no-renames: un renombre aparece como borrado + alta, así mover un archivo fuera de una zona roja no la esconde."""
    archivos = [f for f in git("diff", "--no-renames", "--name-only", f"{base}...HEAD", cwd=root).splitlines() if f]
    lineas = 0
    for ln in git("diff", "--no-renames", "--numstat", f"{base}...HEAD", cwd=root).splitlines():
        a, b, *_ = ln.split("\t") + ["", ""]
        if a == "-" and b == "-":  # binario: numstat no cuenta líneas; se trata como un cambio mediano
            lineas += 100
            continue
        lineas += (int(a) if a.isdigit() else 0) + (int(b) if b.isdigit() else 0)
    return archivos, lineas


def calcular_riesgo(root, base="main"):
    cfg = cargar(root)
    u = cfg.get("umbrales", {})
    archivos, lineas = diff(root, base)
    alto, bajo = lista(cfg, "zonas.alto"), lista(cfg, "zonas.bajo")
    sensibles = [f for f in archivos if coincide_regex(f, alto)]
    control = [f for f in archivos if es_control(cfg, f)]
    if not archivos:
        calc, det = "bajo", "sin cambios"
    elif control:
        calc, det = "alto", "toca el plano de control: " + ", ".join(control)
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
    duro = len(archivos) > u.get("max_archivos_duro", 40) or lineas > u.get("max_lineas_duro", 1500)
    return {"riesgo": final, "calculado": calc, "declarado": declarado, "detalle": det, "archivos": len(archivos), "lineas": lineas,
            "control": control, "excede_duro": duro, "lista_archivos": archivos}


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


# ----------------------------------------------------------------------------- evidencia de revisión

DIR_REVISIONES = ".harness/revisiones"


def slug_rama(nombre):
    return re.sub(r"[^A-Za-z0-9._-]+", "_", nombre or "sin-rama")


def dir_revisiones(root, nombre_rama=None):
    return Path(root) / DIR_REVISIONES / slug_rama(nombre_rama or rama(root))


def registrar_revision(root, revisor, veredicto, modelo="", hallazgos="", tokens=None, costo=None):
    """Escribe un registro atado al commit HEAD (el revisado). No lo commitea: lo hace quien lo pide."""
    from datetime import datetime, timezone
    import hashlib
    veredicto = veredicto.upper()
    if veredicto not in ("APROBAR", "CORREGIR"):
        raise SystemExit("veredicto debe ser APROBAR o CORREGIR")
    if not revisor:
        raise SystemExit("--revisor es obligatorio")
    sha = git("rev-parse", "HEAD", cwd=root)
    if not sha:
        raise SystemExit("no hay commit HEAD que revisar")
    if veredicto == "APROBAR" and revisor != "arquitecto" and not hallazgos.strip():
        raise SystemExit("una aprobación de un revisor LLM necesita --hallazgos con su salida (aunque sea 'sin hallazgos críticos')")
    ahora = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    reg = {"schema": "harness.revision/v1", "rama": rama(root), "change": info_cambio(root).get("id"),
           "commit_sha": sha, "revisor": revisor, "rol": os.environ.get("HARNESS_ROL", "humano"), "modelo": modelo,
           "veredicto": veredicto, "hallazgos_sha256": hashlib.sha256(hallazgos.encode()).hexdigest(),
           "hallazgos": hallazgos[:20000], "tokens": tokens, "costo_usd": costo, "creado": ahora}
    d = dir_revisiones(root)
    d.mkdir(parents=True, exist_ok=True)
    f = d / f"{ahora}-{revisor}-{sha[:7]}.json"
    f.write_text(json.dumps(reg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return f


def revisiones(root, nombre_rama=None):
    d = dir_revisiones(root, nombre_rama)
    out = []
    if d.exists():
        for f in sorted(d.glob("*.json")):
            try:
                out.append(json.loads(f.read_text(encoding="utf-8")))
            except json.JSONDecodeError:
                out.append({"invalido": str(f)})
    return out


def vigente(root, cfg, reg):
    """Un registro vale si su commit es ancestro de HEAD y después solo cambió evidencia/estado (no código)."""
    sha = reg.get("commit_sha", "")
    if not re.fullmatch(r"[0-9a-f]{40}", sha or ""):
        return False, "commit_sha inválido"
    if subprocess.run(["git", "merge-base", "--is-ancestor", sha, "HEAD"], cwd=root, capture_output=True).returncode != 0:
        return False, f"{sha[:7]} no es ancestro de HEAD"
    despues = [f for f in git("diff", "--no-renames", "--name-only", f"{sha}..HEAD", cwd=root).splitlines() if f]
    otros = [f for f in despues if not coincide_regex(f, lista(cfg, "revisiones.cambios_posteriores_permitidos"))]
    if otros:
        return False, f"hubo cambios después de la revisión de {sha[:7]}: {', '.join(otros[:5])}"
    return True, ""


def verificar_revisiones(root, cfg, requeridos):
    """requeridos: lista de slots ('1','2','3','final'). Devuelve errores."""
    regs = revisiones(root)
    errores = []
    slots = cfg.get("revisiones", {}).get("slots", {})
    for slot in requeridos:
        nombres = slots.get(slot, [])
        candidatos = [r for r in regs if r.get("revisor") in nombres and r.get("rama") == rama(root)]
        aprobados = [r for r in candidatos if r.get("veredicto") == "APROBAR"]
        ok = [(r, vigente(root, cfg, r)) for r in aprobados]
        if any(v[0] for _, v in ok):
            continue
        etiqueta = {"1": "Revisión 1 (@revisor-gratis)", "2": "Revisión 2 (@revisor-fuerte)", "3": "Revisión 3 (Luna, /codex:review)", "final": "OK final del arquitecto (/juzgar-pr)"}.get(slot, slot)
        if not aprobados:
            errores.append(f"Falta evidencia de {etiqueta}: `python3 scripts/harness.py revision registrar --revisor {nombres[0] if nombres else '?'} ...` sobre el commit revisado.")
        else:
            errores.append(f"La evidencia de {etiqueta} está vencida: " + "; ".join(v[1] for _, v in ok if not v[0]))
    return errores


# ----------------------------------------------------------------------------- aprobación humana

def aprobacion_humana(root, cfg, pr, head_sha):
    """True/False si se pudo verificar; None si no hay forma de verificarlo (el gate falla cerrado)."""
    aprobadores = set(lista(cfg, "github.aprobadores_humanos"))
    if not aprobadores or not pr or not head_sha:
        return None
    fuente = os.environ.get("HARNESS_REVIEWS_JSON")
    if fuente:
        reviews = json.loads(Path(fuente).read_text(encoding="utf-8"))
    else:
        reviews = gh_json(["api", f"repos/{{owner}}/{{repo}}/pulls/{pr}/reviews", "--paginate"], root)
    if reviews is None:
        return None
    return any(r.get("state") == "APPROVED" and (r.get("user") or {}).get("login") in aprobadores
               and r.get("commit_id") == head_sha for r in reviews)


# ----------------------------------------------------------------------------- presupuesto y telemetría

def consumo(root, cfg, base="main"):
    from datetime import datetime, timezone
    regs = [r for r in revisiones(root) if "invalido" not in r]
    llm = set(cfg.get("revisiones", {}).get("llm", []))
    primero = git("log", "--reverse", "--format=%ct", f"{base}..HEAD", cwd=root).splitlines()
    dias = (datetime.now(timezone.utc).timestamp() - int(primero[0])) / 86400 if primero else 0.0
    return {"vueltas": sum(1 for r in regs if r.get("veredicto") == "CORREGIR"),
            "revisiones_llm": sum(1 for r in regs if r.get("revisor") in llm),
            "costo_usd": round(sum(float(r.get("costo_usd") or 0) for r in regs), 4),
            "tokens": sum(int(r.get("tokens") or 0) for r in regs), "dias": round(dias, 2),
            "modelos": sorted({r.get("modelo") for r in regs if r.get("modelo")})}


def verificar_presupuesto(cfg, nivel, uso):
    lim = cfg.get("presupuesto", {}).get(str(nivel), {})
    excesos = []
    for clave, limite in (("vueltas", "vueltas_max"), ("revisiones_llm", "revisiones_llm_max"), ("dias", "dias_max"), ("costo_usd", "costo_usd_max")):
        if limite in lim and uso.get(clave, 0) > lim[limite]:
            excesos.append(f"{clave} {uso[clave]} > {lim[limite]}")
    return excesos


def registrar_telemetria(root, cfg, base="main", estado_final="mergeado"):
    from datetime import datetime, timezone
    n = calcular_nivel(root, base)
    uso = consumo(root, cfg, base)
    regs = revisiones(root)
    reg = {"schema": "harness.telemetria/v1", "change_id": n["cambio"].get("id"), "rama": rama(root),
           "nivel": n["nivel"], "riesgo": n["riesgo"]["riesgo"], "archivos": n["riesgo"]["archivos"], "lineas": n["riesgo"]["lineas"],
           "control_plane": bool(n["riesgo"]["control"]), **uso,
           "revisores": sorted({r.get("revisor") for r in regs if r.get("revisor")}),
           "hallazgos_corregir": [r.get("revisor") for r in regs if r.get("veredicto") == "CORREGIR"],
           "estado_final": estado_final, "registrado": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    p = Path(root) / ".harness/telemetria.jsonl"
    with p.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(reg, ensure_ascii=False) + "\n")
    return reg


def resumen_telemetria(root):
    p = Path(root) / ".harness/telemetria.jsonl"
    filas = [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()] if p.exists() else []
    por_nivel = {}
    for f in filas:
        d = por_nivel.setdefault(f.get("nivel"), {"changes": 0, "vueltas": 0, "costo_usd": 0.0, "dias": 0.0})
        d["changes"] += 1; d["vueltas"] += f.get("vueltas", 0); d["costo_usd"] += f.get("costo_usd", 0); d["dias"] += f.get("dias", 0)
    for d in por_nivel.values():
        c = d["changes"] or 1
        d["vueltas_prom"] = round(d.pop("vueltas") / c, 2); d["dias_prom"] = round(d.pop("dias") / c, 2); d["costo_usd"] = round(d["costo_usd"], 2)
    modelos = {}
    for f in filas:
        for m in f.get("modelos", []):
            modelos.setdefault(m, {"changes": 0, "con_correcciones": 0})
            modelos[m]["changes"] += 1
            modelos[m]["con_correcciones"] += 1 if f.get("vueltas") else 0
    return {"total_changes": len(filas), "por_nivel": por_nivel, "por_modelo": modelos}


# ----------------------------------------------------------------------------- proceso (PR)

def verificar_proceso(root, base, body, pr=None, head_sha=None):
    errores = []
    nombre = rama(root)
    if (nombre or "").startswith("dependabot/"):
        cfg = cargar(root, estricto=True)
        r = calcular_riesgo(root, base)
        # solo versiones: si toca el plano de control (workflows) igual necesita tu aprobación verificable
        if r["control"] and aprobacion_humana(root, cfg, pr, head_sha) is not True:
            return ["PR de Dependabot que toca el plano de control: requiere tu review APPROVED sobre el commit HEAD (luego re-ejecuta este check)."]
        return []
    tipo, issue, cid = partes_rama(nombre)
    if not (tipo or re.match(r"^(chore|docs)/", nombre or "")):
        return [f"Rama '{nombre}' fuera de convención: feat/<id>, feat/<issue>-<id>, fix/<slug>, fix/<issue>-<id>, chore/..., docs/..."]
    cfg = cargar(root, estricto=True)
    n = calcular_nivel(root, base)
    req, r = n["requisitos"], n["riesgo"]
    if tipo == "feat" and not n["cambio"]["propuesta"]:
        errores.append(f"Falta openspec/changes/{cid}/proposal.md (o su archivo en archive/). Ábrelo con /cambio.")
    if n["nivel"] == 0 and tipo in ("fix", None) and not req["nivel0_permitido"] and not re.match(r"^(chore|docs)/", nombre):
        errores.append(f"Sin change solo se permiten cambios triviales (riesgo bajo y ≤ {cfg.get('umbrales', {}).get('trivial_lineas', 20)} líneas); salió riesgo {r['riesgo']} con {r['lineas']} líneas. Abre el change con /cambio.")
    if req["issue"]:
        num = issue or n["cambio"].get("declarado_issue")
        if not num:
            errores.append(f"Nivel {n['nivel']}: el change necesita issue (rama feat/<n>-<id> o 'Issue: #n' en ## Harness).")
        elif not re.search(rf"#{num}\b", body or ""):
            errores.append(f"El PR debe enlazar el issue (#{num}).")
    slots = [s for s, k in (("1", "revision_1"), ("2", "revision_2"), ("3", "revision_3"), ("final", "ok_final")) if req[k]]
    errores += verificar_revisiones(root, cfg, slots)
    # aprobación humana verificable: plano de control, riesgo alto, techo duro o presupuesto agotado
    motivos = []
    if r["control"]:
        motivos.append("toca el plano de control (" + ", ".join(r["control"][:4]) + ")")
    if r["riesgo"] == "alto":
        motivos.append("riesgo alto")
    if r["excede_duro"]:
        motivos.append(f"supera el techo duro ({r['archivos']} archivos, {r['lineas']} líneas)")
    excesos = verificar_presupuesto(cfg, n["nivel"], consumo(root, cfg, base)) if n["nivel"] >= 1 else []
    if excesos:
        motivos.append("presupuesto agotado: " + ", ".join(excesos))
    if motivos:
        ap = aprobacion_humana(root, cfg, pr, head_sha)
        if ap is not True:
            por_que = "no se pudo verificar (sin PR/SHA, sin aprobadores o sin acceso a la API)" if ap is None else "no hay review APPROVED de un aprobador sobre el commit HEAD"
            errores.append("Requiere aprobación humana — " + "; ".join(motivos) + f". {por_que}. Aprueba el PR en GitHub con la cuenta humana y re-ejecuta este check.")
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
    fallback = cfg.get("fallbacks", {}).get(info.get("agente") or "", [])
    if info.get("agente"):
        modelo = cfg.get("agentes", {}).get(info["agente"])
    elif info.get("modelo", "").startswith("claude."):
        modelo = cfg.get("claude", {}).get(info["modelo"].split(".", 1)[1])
    return {"skill": skill, "clase": clase, "origen": origen, "herramienta": info.get("herramienta"), "agente": info.get("agente"), "modelo": modelo,
            "fallback": fallback, "que": info.get("que", "")}


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
    donde = "Claude Code (scripts/arq)" if rt["herramienta"] == "claude" else f"OpenCode (scripts/ejec-contenedor) · agente {rt['agente']}"
    fb = f"\n  si no responde: {', '.join(rt['fallback'])}" if rt.get("fallback") else ""
    return f"{rt['skill']} → clase {rt['clase']} ({rt['origen']}) → {donde} · modelo: {rt['modelo']}{fb}\n  {rt['que']}"


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


READ_TOOLS_CLAUDE = {"Read", "Grep", "Glob", "NotebookRead", "LS"}


def mensaje_secreto(quien, objetivo):
    return (f"⛔ Harness — secretos: {quien} no puede leer ni imprimir credenciales. Bloqueado: `{objetivo}`.\n"
            f"Si la tarea necesita un valor, pídele al usuario el NOMBRE de la variable, nunca su contenido. "
            f"No intentes leerlo por otra vía.")


def guard_claude(data, root=None):
    """Devuelve (codigo, mensaje). 2 = bloquear. Cualquier excepción la convierte en 2 el envoltorio (fail-closed)."""
    if override():
        return 0, ""
    root = Path(root or os.environ.get("CLAUDE_PROJECT_DIR") or git("rev-parse", "--show-toplevel") or os.getcwd())
    cfg = cargar_confiable(root)
    tool, ti = data.get("tool_name", ""), data.get("tool_input", {}) or {}

    def relativa(p):
        ap = Path(p) if os.path.isabs(p) else (root / p)
        ap = Path(os.path.abspath(os.path.expanduser(str(ap))))
        base = raiz_git_de(ap)
        return ap, base, (os.path.relpath(ap, base) if base else str(ap))

    def permitido(p):
        ap, base, rel = relativa(p)
        if str(ap).startswith("/dev/"):
            return True, str(ap), ""
        if base is None:
            return True, str(ap), ""
        c = cargar_confiable(base) if (Path(base) / "harness.json").exists() else cfg
        if es_control(c, rel) and not coincide_regex(rel, lista(c, "control_plane.arquitecto_puede")):
            return False, rel, "control"
        return coincide_prefijo(rel, lista(c, "permisos.arquitecto_puede")), rel, "codigo"

    def bloqueo(objetivo, motivo="codigo"):
        if motivo == "control":
            return 2, (f"⛔ Harness — plano de control: `{objetivo}` controla a los agentes (guardias, hooks, workflows, permisos).\n"
                       f"Ningún agente lo edita. Si hay que cambiarlo, lo hace el humano con HARNESS_OVERRIDE=1 y el PR exige su aprobación en GitHub.\n"
                       f"Explícale esto al usuario y propón el cambio en texto; no intentes editarlo por otra vía.")
        return 2, (f"⛔ Harness — rol ARQUITECTO: Claude Code no implementa código de la aplicación.\n"
                   f"Bloqueado: {tool} sobre `{objetivo}`.\n\nCómo hacerlo bien:\n"
                   f"  1. Cambio normal → /cambio y ejecútalo en OpenCode: `scripts/ejec-contenedor` → /ejecutar-cambio <id>.\n"
                   f"     Si estás en una skill bmad-*: BMAD no ejecuta; entrega el dossier y nombra /cambio o /opsx:update <id>.\n"
                   f"  2. Arreglo < 20 líneas en /juzgar-pr, o zona roja asignada a Claude → el humano relanza con HARNESS_OVERRIDE=1 scripts/arq\n\n"
                   f"Explícale esto al usuario tal cual. No intentes editar el archivo por otra vía (bash, python, git apply).")

    if tool in READ_TOOLS_CLAUDE:
        for k in ("file_path", "notebook_path", "path"):
            v = ti.get(k)
            if isinstance(v, str) and v and es_secreto(cfg, relativa(v)[2]):
                return 2, mensaje_secreto("Claude", v)
        for k in ("pattern", "glob"):
            v = ti.get(k)
            if tool == "Glob" and isinstance(v, str) and coincide_regex(v, lista(cfg, "secretos.globs")):
                return 2, mensaje_secreto("Claude", v)
            if k == "glob" and isinstance(v, str) and coincide_regex(v, lista(cfg, "secretos.globs")):
                return 2, mensaje_secreto("Claude", v)
        return 0, ""
    if tool in EDIT_TOOLS_CLAUDE:
        p = ti.get("file_path") or ti.get("notebook_path") or ""
        if p:
            if es_secreto(cfg, relativa(p)[2]):
                return 2, mensaje_secreto("Claude", p)
            ok, rel, motivo = permitido(p)
            if not ok:
                return bloqueo(rel, motivo)
        return 0, ""
    if tool == "Bash":
        cmd = ti.get("command", "") or ""
        sec = secretos_en_comando(cfg, cmd)
        if sec:
            return 2, mensaje_secreto("Claude", "; ".join(sec[:3]))
        if re.search(r"\bgit\s+apply\b|\bpatch\s+-p\d", cmd):
            return bloqueo("git apply / patch")
        for o in objetivos_bash(cmd):
            ok, rel, motivo = permitido(o)
            if not ok:
                return bloqueo(rel, motivo)
        return 0, ""
    if tool == "Skill":
        skill = nombre_skill(ti)
        if not skill:
            return 0, ""
        rt = ruta_skill(cfg, skill)
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
    cfg = cargar_confiable(root)
    t = (tool or "").lower()

    def bloqueo(motivo, como):
        return {"block": True, "msg": f"⛔ Harness — rol EJECUTOR: {motivo}\nCómo hacerlo bien: {como}\nExplícale esto al usuario tal cual y no intentes hacerlo por otra vía."}

    def rel_de(p):
        return os.path.relpath(os.path.expanduser(p) if os.path.isabs(os.path.expanduser(p)) else root / p, root)

    if t in ("read", "grep", "glob", "list", "ls"):
        for k in ("filePath", "path", "file"):
            v = args.get(k)
            if isinstance(v, str) and v and es_secreto(cfg, rel_de(v)):
                return {"block": True, "msg": mensaje_secreto("OpenCode", v)}
        for k in ("pattern", "include", "glob"):
            v = args.get(k)
            if isinstance(v, str) and (t == "glob" or k != "pattern") and coincide_regex(v, lista(cfg, "secretos.globs")):
                return {"block": True, "msg": mensaje_secreto("OpenCode", v)}
        return {"block": False, "msg": ""}
    if t in EDIT_TOOLS_OPENCODE:
        p = args.get("filePath") or args.get("path") or args.get("file")
        if not p:
            return {"block": False, "msg": ""}
        rel = rel_de(p)
        if es_secreto(cfg, rel):
            return {"block": True, "msg": mensaje_secreto("OpenCode", rel)}
        if es_control(cfg, rel):
            return bloqueo(f"`{rel}` es del plano de control (guardias, hooks, workflows, permisos).", "no lo edita ningún agente; propón el cambio en HANDOFF.md.")
        if coincide_regex(rel, lista(cfg, "permisos.ejecutor_no_puede")):
            return bloqueo(f"`{rel}` es un artefacto del arquitecto (proposal/design/specs, specs publicadas, BMAD, reglas, CI o harness.json).",
                           "solo editas código, openspec/changes/<id>/tasks.md y _bmad-output/digests/. Escribe el hueco en HANDOFF.md y pide /opsx:update <id> en Claude Code.")
        if coincide_regex(rel, lista(cfg, "zonas.alto")) and info_cambio(root).get("declarado_roja") != "autorizado":
            return bloqueo(f"`{rel}` está en zona roja y el proposal de esta rama no autoriza a OpenCode.",
                           "Claude Code debe poner 'OpenCode-zona-roja: autorizado' en ## Harness del proposal (con pasos cerrados), o implementarlo él.")
    elif t == "bash":
        c = str(args.get("command", ""))
        sec = secretos_en_comando(cfg, c)
        if sec:
            return {"block": True, "msg": mensaje_secreto("OpenCode", "; ".join(sec[:3]))}
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

def rol_actual():
    rol = os.environ.get("HARNESS_ROL")
    if rol:
        return rol
    if os.environ.get("CLAUDECODE") == "1":  # Claude Code lo define en sus shells: sin scripts/arq sigue siendo el arquitecto
        return "arquitecto"
    return "humano"


def escanear_secretos_staged(root, cfg):
    hallazgos = []
    for f in [f for f in git("diff", "--cached", "--no-renames", "--name-only", "--diff-filter=ACMR", cwd=root).splitlines() if f]:
        if es_secreto(cfg, f):
            hallazgos.append(f"{f}: archivo de credenciales")
    agregado = "\n".join(l[1:] for l in git("diff", "--cached", "--no-renames", "-U0", cwd=root).splitlines() if l.startswith("+") and not l.startswith("+++"))
    for pat in secretos_en_texto(cfg, agregado):
        hallazgos.append(f"contenido que parece un secreto ({pat})")
    return hallazgos


def hook_pre_commit(root):
    rol = rol_actual()
    def rechazo(motivo, como):
        sys.stderr.write(f"\n⛔ Harness ({rol}): {motivo}\n   Cómo hacerlo bien: {como}\n   Override consciente: HARNESS_OVERRIDE=1 (queda registrado en el commit)\n\n")
        return 1
    if override():
        return 0
    try:
        cfg = cargar_confiable(root) if rol != "humano" else cargar(root)
    except ConfigError as e:
        return rechazo(f"configuración del harness inválida ({e}); se bloquea por seguridad.", "restaura harness.json desde main.")
    sec = escanear_secretos_staged(root, cfg) if cfg else []
    if sec:
        return rechazo("el commit incluye secretos: " + "; ".join(sec[:5]), "quítalos del staging (git restore --staged <archivo>), rota el secreto si ya salió, y usa variables de entorno.")
    if rol == "humano":
        return 0
    staged = [f for f in git("diff", "--cached", "--no-renames", "--name-only", cwd=root).splitlines() if f]
    actual = git("branch", "--show-current", cwd=root)
    if rol == "arquitecto":
        for f in staged:
            if es_control(cfg, f) and not coincide_regex(f, lista(cfg, "control_plane.arquitecto_puede")):
                return rechazo(f"Claude intenta commitear el plano de control: {f}", "los archivos de control solo los cambia el humano (HARNESS_OVERRIDE=1) y el PR exige su aprobación.")
            if not coincide_prefijo(f, lista(cfg, "permisos.arquitecto_puede")):
                return rechazo(f"Claude (arquitecto) intenta commitear código de la app: {f}", "abre el change con /cambio y ejecútalo en OpenCode (scripts/ejec-contenedor → /ejecutar-cambio <id>).")
    elif rol == "ejecutor":
        if actual in ("main", "master"):
            return rechazo(f"OpenCode no commitea en {actual}.", "trabaja en la rama del change (feat/<id> o feat/<n>-<id>).")
        autorizado = info_cambio(root).get("declarado_roja") == "autorizado"
        for f in staged:
            if es_control(cfg, f) or coincide_regex(f, lista(cfg, "permisos.ejecutor_no_puede")):
                return rechazo(f"OpenCode (ejecutor) intenta commitear un artefacto del arquitecto o del plano de control: {f}", "solo código, tasks.md del change, digests y evidencia de revisión; deja la propuesta en HANDOFF.md.")
            if coincide_regex(f, lista(cfg, "zonas.alto")) and not autorizado:
                return rechazo(f"zona roja sin autorización en el proposal: {f}", "Claude debe poner 'OpenCode-zona-roja: autorizado' en ## Harness del proposal, o implementarlo él.")
    return 0


def hook_commit_msg(ruta_msg):
    if override():
        p = Path(ruta_msg)
        t = p.read_text(encoding="utf-8")
        if "Harness-Override:" not in t:
            p.write_text(t.rstrip("\n") + f"\n\nHarness-Override: yes (rol: {rol_actual()})\n", encoding="utf-8")
    return 0


def hook_pre_push(stdin_text):
    rol = rol_actual()
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


# ----------------------------------------------------------------------------- versiones y supply chain

def cargar_versiones(root):
    p = Path(root) / ".harness/versiones.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


CLIS = {"opencode-ai": ["opencode", "--version"], "@openai/codex": ["codex", "--version"], "omniroute": ["omniroute", "--version"]}


def versiones_instaladas():
    out = {}
    for paquete, cmd in CLIS.items():
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            m = re.search(r"\d+\.\d+\.\d+", r.stdout + r.stderr)
            out[paquete] = m.group(0) if m else None
        except (FileNotFoundError, subprocess.TimeoutExpired):
            out[paquete] = None
    return out


USES_RE = re.compile(r"(?m)^(\s*-?\s*uses:\s*)([A-Za-z0-9_.-]+/[A-Za-z0-9_./-]+)@([^\s#]+)(\s*#.*)?$")


def acciones_sin_fijar(texto):
    return [(m.group(2), m.group(3)) for m in USES_RE.finditer(texto) if not re.fullmatch(r"[0-9a-f]{40}", m.group(3))]


def fijar_acciones_texto(texto, resolver):
    """Reemplaza owner/repo@tag por owner/repo@<sha> # tag. resolver(repo, ref) -> sha o None."""
    def sub(m):
        repo, ref = m.group(2), m.group(3)
        if re.fullmatch(r"[0-9a-f]{40}", ref):
            return m.group(0)
        sha = resolver(repo, ref)
        return f"{m.group(1)}{repo}@{sha} # {ref}" if sha else m.group(0)
    return USES_RE.sub(sub, texto)


def resolver_gh(root):
    def r(repo, ref):
        base = "/".join(repo.split("/")[:2])
        d = gh_json(["api", f"repos/{base}/commits/{ref}"], root)
        return d.get("sha") if isinstance(d, dict) else None
    return r


def listar_secretos(root, cfg):
    salto = {".git", "node_modules", ".venv", "venv", "dist", "build", "__pycache__"}
    out = []
    for d, dirs, files in os.walk(root):
        dirs[:] = [x for x in dirs if x not in salto]
        for f in files:
            rel = os.path.relpath(os.path.join(d, f), root)
            if es_secreto(cfg, rel):
                out.append(os.path.join(d, f))
    return sorted(out)


def doctor(root, con_tests=False):
    """Lista de (nivel, mensaje) con nivel en ok|aviso|error."""
    R = []
    ok = lambda m: R.append(("ok", m)); av = lambda m: R.append(("aviso", m)); er = lambda m: R.append(("error", m))
    try:
        cfg = cargar(root, estricto=True)
        ok(f"harness.json válido (versión {cfg.get('version')})")
    except ConfigError as e:
        er(f"harness.json: {e}")
        return R
    if not lista(cfg, "github.aprobadores_humanos"):
        er("github.aprobadores_humanos vacío: los cambios de riesgo alto y del plano de control no se podrán aprobar")
    for n in ("0", "1", "2", "3"):
        lim = cfg.get("presupuesto", {}).get(n)
        if not isinstance(lim, dict) or any(not isinstance(v, (int, float)) or v < 0 for k, v in lim.items() if not k.startswith("_")):
            er(f"presupuesto del nivel {n} ausente o inválido")
    placeholders = [a for a, m in cfg.get("agentes", {}).items() if isinstance(m, str) and "REEMPLAZA" in m]
    (av if placeholders else ok)(f"modelos sin ID real en harness.json → agentes: {', '.join(placeholders)}" if placeholders else "IDs de modelo configurados")
    (ok if sync(root, check=True) == [] else av)("adaptadores al día con harness.json" if sync(root, check=True) == [] else "adaptadores desactualizados: python3 scripts/harness.py sync")
    sm = estado_skills(root)["sin_mapear"]
    (er if sm else ok)(f"skills sin clasificar (bloqueadas): {', '.join(sm)}" if sm else "todas las skills instaladas están clasificadas")
    # secretos versionados
    versionados = [f for f in git("ls-files", cwd=root).splitlines() if es_secreto(cfg, f)]
    (er if versionados else ok)(f"secretos versionados en git: {', '.join(versionados)} (sácalos y rótalos)" if versionados else "sin archivos de credenciales versionados")
    for f in listar_secretos(root, cfg):
        rel = os.path.relpath(f, root)
        if subprocess.run(["git", "check-ignore", "-q", rel], cwd=root).returncode != 0 and rel not in versionados:
            er(f"{rel} no está en .gitignore")
    # guardias conectados y fail-closed
    st = Path(root) / ".claude/settings.json"
    txt = st.read_text(encoding="utf-8") if st.exists() else ""
    (ok if "guardia_claude.py" in txt and "exit 2" in txt else er)("hook de Claude conectado y fail-closed" if "guardia_claude.py" in txt and "exit 2" in txt else "hook de Claude ausente o sin '|| exit 2' (un fallo del guardia dejaría pasar la acción)")
    (ok if "Read|Grep|Glob" in txt or ("Read" in txt and "Grep" in txt) else er)("hook de Claude cubre lecturas (Read/Grep/Glob)" if "Read" in txt and "Grep" in txt else "hook de Claude no cubre lecturas: puede leer secretos")
    pl = Path(root) / ".opencode/plugins/guardia.ts"
    (ok if pl.exists() and "fail-closed" in pl.read_text(encoding="utf-8") else er)("plugin de OpenCode presente y fail-closed" if pl.exists() and "fail-closed" in pl.read_text(encoding="utf-8") else "plugin de OpenCode ausente o fail-open")
    (ok if git("config", "core.hooksPath", cwd=root) == ".githooks" else er)("git hooks activos" if git("config", "core.hooksPath", cwd=root) == ".githooks" else "git hooks inactivos: git config core.hooksPath .githooks")
    no_ejec = [f for f in ("scripts/harness.py", "scripts/arq", "scripts/ejec", "scripts/ejec-contenedor", ".githooks/pre-commit") if (Path(root) / f).exists() and not os.access(Path(root) / f, os.X_OK)]
    (er if no_ejec else ok)(f"no ejecutables: {', '.join(no_ejec)}" if no_ejec else "scripts y hooks ejecutables")
    # plano de control modificado respecto a origin/main
    if git("rev-parse", "--verify", "-q", "origin/main", cwd=root):
        mod = [f for f in git("diff", "--name-only", "origin/main", cwd=root).splitlines() if f and es_control(cfg, f)]
        (av if mod else ok)(f"plano de control modificado respecto a origin/main: {', '.join(mod)} (el PR exigirá tu aprobación)" if mod else "plano de control igual a origin/main")
    # versiones
    ver = cargar_versiones(root)
    if not ver:
        er("falta .harness/versiones.json (versiones fijadas)")
    else:
        inst = versiones_instaladas()
        for paq, v in inst.items():
            fijada = ver.get("npm", {}).get(paq)
            if v and fijada and v != fijada:
                av(f"{paq}: instalada {v}, fijada {fijada} (actualiza con intención: docs/SEGURIDAD.md → upgrades)")
        if not ver.get("imagen_base_digest"):
            av("imagen del contenedor sin digest fijado (.harness/versiones.json → imagen_base_digest)")
    latest = []
    for f in [".harness/contenedor/Dockerfile", "scripts/instalar-frameworks.sh", ".github/workflows/proceso.yml"]:
        pth = Path(root) / f
        if pth.exists() and re.search(r"@latest|=latest\b|:latest\b", pth.read_text(encoding="utf-8")):
            latest.append(f)
    (er if latest else ok)(f"dependencias sin fijar ('latest') en: {', '.join(latest)}" if latest else "sin 'latest' en instalación, contenedor ni gate")
    wf = Path(root) / ".github/workflows"
    sin_sha = sorted({f"{r}@{t}" for y in (wf.glob("*.yml") if wf.exists() else []) for r, t in acciones_sin_fijar(y.read_text(encoding="utf-8"))})
    (av if sin_sha else ok)(f"acciones de GitHub fijadas por etiqueta, no por SHA: {', '.join(sin_sha)} → python3 scripts/harness.py fijar-acciones --aplicar" if sin_sha else "acciones de GitHub fijadas por SHA")
    ci = Path(root) / ".github/workflows/ci.yml"
    if ci.exists() and "STACK pendiente" in ci.read_text(encoding="utf-8"):
        av("ci.yml sin los gates del stack (/init-harness)")
    if con_tests:
        r = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "scripts", "-p", "test_*.py"], cwd=root, capture_output=True, text=True,
                           env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
        (ok if r.returncode == 0 else er)("selftest del harness en verde" if r.returncode == 0 else "selftest del harness FALLA:\n" + r.stderr[-1500:])
    return R


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
        opt = lambda k: args[args.index(k) + 1] if k in args else None
        base = opt("--base") or "main"
        body = Path(opt("--body-file")).read_text(encoding="utf-8") if opt("--body-file") else ""
        try:
            errores = verificar_proceso(root, base, body, pr=opt("--pr"), head_sha=opt("--head-sha"))
        except ConfigError as e:
            print(f"⛔ configuración del harness inválida: {e}")
            return 1
        n = calcular_nivel(root, base)
        print(f"nivel={n['nivel']} riesgo={n['riesgo']['riesgo']} ({n['riesgo']['detalle']})")
        for e in errores:
            print(f"⛔ {e}")
        return 1 if errores else 0
    if cmd == "guard-claude":
        try:
            codigo, msg = guard_claude(json.load(sys.stdin))
        except Exception as e:  # fail-closed: un guardia roto no deja pasar nada
            codigo, msg = 2, f"⛔ Harness: el guardia falló ({e.__class__.__name__}: {e}); por seguridad se bloquea. Revisa harness.json o corre scripts/doctor.sh."
        if msg:
            sys.stderr.write(msg + "\n")
        return codigo
    if cmd == "guard-opencode":
        try:
            d = json.load(sys.stdin)
            res = guard_opencode(d.get("tool", ""), d.get("args", {}) or {}, d.get("root") or root)
        except Exception as e:  # fail-closed
            res = {"block": True, "msg": f"⛔ Harness: el guardia falló ({e.__class__.__name__}: {e}); por seguridad se bloquea. Corre scripts/doctor.sh."}
        print(json.dumps(res, ensure_ascii=False))
        return 0
    if cmd == "revision":
        sub = args[0] if args else ""
        opt = lambda k: args[args.index(k) + 1] if k in args else None
        if sub == "registrar":
            hall = opt("--hallazgos")
            texto = sys.stdin.read() if hall == "-" else (Path(hall).read_text(encoding="utf-8") if hall else "")
            f = registrar_revision(root, opt("--revisor"), opt("--veredicto") or "", opt("--modelo") or "", texto,
                                   int(opt("--tokens")) if opt("--tokens") else None, float(opt("--costo")) if opt("--costo") else None)
            print(f"registrada: {os.path.relpath(f, root)}  (haz commit de este archivo)")
            return 0
        if sub == "listar":
            cfg = cargar(root)
            for r in revisiones(root):
                v = vigente(root, cfg, r) if "invalido" not in r else (False, "JSON inválido")
                print(f"{r.get('creado','?')}  {r.get('revisor','?'):15} {r.get('veredicto','?'):9} {str(r.get('commit_sha',''))[:7]}  {r.get('modelo','')}  {'vigente' if v[0] else 'NO vigente: ' + v[1]}")
            return 0
        print("uso: harness.py revision registrar --revisor <nombre> --veredicto APROBAR|CORREGIR --modelo <id> --hallazgos <archivo|-> [--tokens N --costo USD] | listar")
        return 2
    if cmd == "presupuesto":
        cfg = cargar(root, estricto=True)
        n = calcular_nivel(root, args[0] if args else "main")
        uso = consumo(root, cfg, args[0] if args else "main")
        print(json.dumps({"nivel": n["nivel"], "limites": cfg.get("presupuesto", {}).get(str(n["nivel"]), {}), "uso": uso,
                          "excesos": verificar_presupuesto(cfg, n["nivel"], uso)}, ensure_ascii=False, indent=2))
        return 0
    if cmd == "telemetria":
        cfg = cargar(root, estricto=True)
        if args and args[0] == "registrar":
            print(json.dumps(registrar_telemetria(root, cfg, args[1] if len(args) > 1 else "main"), ensure_ascii=False))
            return 0
        print(json.dumps(resumen_telemetria(root), ensure_ascii=False, indent=2))
        return 0
    if cmd == "versiones":
        ver, inst = cargar_versiones(root), versiones_instaladas()
        dif = 0
        for paq, v in ver.get("npm", {}).items():
            i = inst.get(paq)
            marca = "=" if i == v else ("?" if i is None else "≠")
            dif += marca == "≠"
            print(f"{marca} {paq:32} fijada {v:10} instalada {i or '-'}")
        return 1 if ("--check" in args and dif) else 0
    if cmd == "fijar-acciones":
        wf = Path(root) / ".github/workflows"
        cambios = 0
        for y in sorted(wf.glob("*.yml")):
            t = y.read_text(encoding="utf-8")
            pend = acciones_sin_fijar(t)
            if not pend:
                continue
            print(f"{y.name}: " + ", ".join(f"{r}@{v}" for r, v in pend))
            if "--aplicar" in args:
                nuevo = fijar_acciones_texto(t, resolver_gh(root))
                if nuevo != t:
                    y.write_text(nuevo, encoding="utf-8"); cambios += 1
        print(f"workflows actualizados: {cambios}" if "--aplicar" in args else "(dry-run; usa --aplicar)")
        return 0
    if cmd == "secretos-listar":
        for f in listar_secretos(root, cargar(root, estricto=True)):
            print(f)
        return 0
    if cmd == "doctor":
        res = doctor(root, con_tests="--tests" in args)
        icono = {"ok": "\033[32m✓\033[0m", "aviso": "\033[33m!\033[0m", "error": "\033[31m✗\033[0m"}
        for nivel, m in res:
            print(f"  {icono[nivel]} {m}")
        return 1 if any(n == "error" for n, _ in res) else 0
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

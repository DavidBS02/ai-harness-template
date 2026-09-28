#!/usr/bin/env python3
"""Hook PreToolUse de Claude Code: Claude es arquitecto, no implementa código de la app.
Exit 2 bloquea la herramienta; el mensaje de stderr lo recibe Claude, que debe explicárselo al usuario."""
import json, os, re, sys

if os.environ.get("HARNESS_OVERRIDE") == "1":
    sys.exit(0)

data = json.load(sys.stdin)
tool = data.get("tool_name", "")
ti = data.get("tool_input", {}) or {}
root = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()

def cargar(ruta):
    try:
        return [l.strip() for l in open(ruta, encoding="utf-8") if l.strip() and not l.strip().startswith("#")]
    except FileNotFoundError:
        return []

def raiz_git(path):
    d = os.path.dirname(path)
    while d and d != os.path.dirname(d):
        if os.path.exists(os.path.join(d, ".git")):
            return d
        d = os.path.dirname(d)
    return None

def permitido(p):
    ap = p if os.path.isabs(p) else os.path.abspath(os.path.join(root, p))
    if ap.startswith("/dev/"):
        return True, ap
    base = raiz_git(ap)
    if base is None:
        return True, ap  # fuera de cualquier repo
    permitidos = cargar(os.path.join(base, ".harness/permisos-arquitecto.txt")) or cargar(os.path.join(root, ".harness/permisos-arquitecto.txt"))
    rel = os.path.relpath(ap, base)
    return any(rel == a.rstrip("/") or rel.startswith(a) for a in permitidos), rel

def bloquear(objetivo):
    sys.stderr.write(f"""⛔ Harness — rol ARQUITECTO: Claude Code no implementa código de la aplicación.
Bloqueado: {tool} sobre `{objetivo}`.

Cómo hacerlo bien:
  1. Feature o cambio normal → abre el change con /cambio y ejecútalo en OpenCode: `scripts/ejec` → /ejecutar-cambio <id>.
     Si estás en una skill bmad-*: BMAD no ejecuta; entrega el dossier y nombra /cambio o /opsx:update <id>.
  2. Arreglo < 20 líneas dentro de /juzgar-pr, o zona roja que docs/harness/DELEGACION.md asigna a Claude →
     el humano debe relanzar Claude con: HARNESS_OVERRIDE=1 scripts/arq

Explícale esto al usuario tal cual. No intentes editar el archivo por otra vía (bash, python, git apply).
""")
    sys.exit(2)

if tool in ("Edit", "Write", "MultiEdit", "NotebookEdit"):
    p = ti.get("file_path") or ti.get("notebook_path") or ""
    if p:
        ok, rel = permitido(p)
        if not ok:
            bloquear(rel)
    sys.exit(0)

if tool == "Bash":
    cmd = ti.get("command", "") or ""
    objetivos = []
    objetivos += re.findall(r"(?<![0-9&<])>{1,2}\s*([^\s;&|<>]+)", cmd)            # > archivo, >> archivo
    objetivos += re.findall(r"\btee\s+(?:-a\s+)?([^\s;&|]+)", cmd)                  # tee archivo
    objetivos += re.findall(r"\b(?:sed|perl)\s+-[a-zA-Z]*i[^\s]*\s+(?:'[^']*'|\"[^\"]*\"|\S+)\s+([^\s;&|]+)", cmd)
    for m in re.finditer(r"\b(?:cp|mv|install)\s+(?:-\S+\s+)*(?:\S+\s+)+?(\S+)\s*(?:$|[;&|])", cmd):
        objetivos.append(m.group(1))
    if re.search(r"\bgit\s+apply\b|\bpatch\s+-p\d", cmd):
        bloquear("git apply / patch")
    for o in objetivos:
        o = o.strip("'\"")
        if o.startswith("&") or o in ("/dev/null",):
            continue
        ok, rel = permitido(o)
        if not ok:
            bloquear(rel)
sys.exit(0)

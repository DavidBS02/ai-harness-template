// Guardia de rol para OpenCode (ejecutor). Verifica los nombres de herramienta con tu versión de OpenCode.
// Bloquea: editar artefactos del arquitecto, tocar zona roja sin autorización en el spec, mergear PRs, push a main.
import { existsSync, readFileSync, readdirSync } from "fs"
import { join, relative, isAbsolute } from "path"
import { execSync } from "child_process"

export const Guardia = async ({ directory }: { directory: string }) => {
  const root = directory
  const leer = (f: string) =>
    existsSync(join(root, f))
      ? readFileSync(join(root, f), "utf8").split("\n").map((s) => s.trim()).filter((s) => s && !s.startsWith("#"))
      : []
  const protegidas = leer(".harness/protegidas-ejecutor.txt")
  const alto = leer(".harness/rutas-alto.txt").map((r) => new RegExp(r))
  const rel = (p: string) => relative(root, isAbsolute(p) ? p : join(root, p))

  const specAutorizaZonaRoja = () => {
    try {
      const rama = execSync("git branch --show-current", { cwd: root }).toString().trim()
      const m = rama.match(/^(?:feat|fix)\/(\d+)-/)
      if (!m) return false
      const dir = join(root, "docs/specs")
      const f = readdirSync(dir).find((x) => x.startsWith(m[1] + "-"))
      return !!f && /OpenCode-zona-roja:\s*autorizado/i.test(readFileSync(join(dir, f), "utf8"))
    } catch {
      return false
    }
  }

  const bloquear = (motivo: string, como: string) => {
    throw new Error(
      `⛔ Harness — rol EJECUTOR: ${motivo}\nCómo hacerlo bien: ${como}\n` +
        `Explícale esto al usuario tal cual y no intentes hacerlo por otra vía.`,
    )
  }

  return {
    "tool.execute.before": async (input: any, output: any) => {
      if (process.env.HARNESS_OVERRIDE === "1") return
      const t = String(input.tool || "").toLowerCase()
      const a = output?.args ?? {}

      if (["edit", "write", "patch", "multiedit"].includes(t)) {
        const p = a.filePath ?? a.path ?? a.file
        if (!p) return
        const r = rel(String(p))
        if (protegidas.some((x) => r === x.replace(/\/$/, "") || r.startsWith(x)))
          bloquear(
            `\`${r}\` es un artefacto del arquitecto (spec, mapa, reglas, CI).`,
            `escribe la duda o el cambio propuesto en HANDOFF.md y pide al usuario que lo resuelva en Claude Code (/spec o /descubrir).`,
          )
        if (alto.some((re) => re.test(r)) && !specAutorizaZonaRoja())
          bloquear(
            `\`${r}\` está en zona roja y el spec de esta rama no autoriza a OpenCode a tocarla.`,
            `pide al usuario que Claude Code añada la línea "OpenCode-zona-roja: autorizado" al spec (con pasos cerrados), o que Claude lo implemente.`,
          )
      }

      if (t === "bash") {
        const c = String(a.command ?? "")
        if (/\bgh\s+pr\s+merge\b/.test(c))
          bloquear(`mergear PRs es decisión del arquitecto.`, `deja el PR abierto; el usuario corre /juzgar-pr <n> en Claude Code.`)
        if (/\bgit\s+push\b[^;&|]*\b(main|master)\b/.test(c))
          bloquear(`no se hace push a main.`, `haz push de tu rama feat/<issue>-<slug> y abre el PR con gh pr create.`)
        if (/\b(git\s+commit|git\s+add)\b/.test(c) && /\b(docs\/specs|\.harness|AGENTS\.md|CLAUDE\.md)\b/.test(c))
          bloquear(`no commiteas artefactos del arquitecto.`, `quita esos archivos del commit.`)
      }
    },
  }
}

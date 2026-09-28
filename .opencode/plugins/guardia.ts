// Guardia de rol para OpenCode (ejecutor). Verifica los nombres de herramienta con tu versión de OpenCode.
// Bloquea: editar artefactos del arquitecto (proposal/design/specs de OpenSpec, openspec/specs, config, BMAD, reglas, CI),
// tocar zona roja sin "OpenCode-zona-roja: autorizado" en el proposal, archivar, mergear PRs y push a main.
import { existsSync, readFileSync, readdirSync } from "fs"
import { join, relative, isAbsolute } from "path"
import { execSync } from "child_process"

export const Guardia = async ({ directory }: { directory: string }) => {
  const root = directory
  const leer = (f: string) =>
    existsSync(join(root, f))
      ? readFileSync(join(root, f), "utf8").split("\n").map((s) => s.trim()).filter((s) => s && !s.startsWith("#"))
      : []
  const protegidas = leer(".harness/protegidas-ejecutor.txt").map((r) => new RegExp(r))
  const alto = leer(".harness/rutas-alto.txt").map((r) => new RegExp(r))
  const rel = (p: string) => relative(root, isAbsolute(p) ? p : join(root, p))

  const proposalDeLaRama = (): string | null => {
    try {
      const rama = execSync("git branch --show-current", { cwd: root }).toString().trim()
      const m = rama.match(/^(?:feat|fix)\/(?:\d+-)?([a-z0-9][a-z0-9-]*)$/)
      if (!m) return null
      const activo = join(root, "openspec/changes", m[1], "proposal.md")
      if (existsSync(activo)) return activo
      const arch = join(root, "openspec/changes/archive")
      const d = existsSync(arch) ? readdirSync(arch).filter((x) => x.endsWith("-" + m[1])).sort().pop() : undefined
      return d && existsSync(join(arch, d, "proposal.md")) ? join(arch, d, "proposal.md") : null
    } catch {
      return null
    }
  }
  const autorizaZonaRoja = () => {
    const p = proposalDeLaRama()
    return !!p && /OpenCode-zona-roja:\s*autorizado/i.test(readFileSync(p, "utf8"))
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
        if (protegidas.some((re) => re.test(r)))
          bloquear(
            `\`${r}\` es un artefacto del arquitecto (proposal/design/specs de OpenSpec, specs publicadas, BMAD, reglas o CI).`,
            `solo editas código y openspec/changes/<id>/tasks.md. Escribe el hueco en HANDOFF.md y pide al usuario /opsx:update <id> en Claude Code.`,
          )
        if (alto.some((re) => re.test(r)) && !autorizaZonaRoja())
          bloquear(
            `\`${r}\` está en zona roja y el proposal de esta rama no autoriza a OpenCode.`,
            `pide al usuario que Claude Code ponga "OpenCode-zona-roja: autorizado" en ## Harness del proposal (con pasos cerrados), o que Claude lo implemente.`,
          )
      }

      if (t === "bash") {
        const c = String(a.command ?? "")
        if (/\bopenspec\s+archive\b/.test(c))
          bloquear(`archivar un change publica verdad en openspec/specs/: es decisión del arquitecto.`, `deja el PR listo; el usuario corre /juzgar-pr <n> en Claude Code.`)
        if (/\bgh\s+pr\s+merge\b/.test(c))
          bloquear(`mergear PRs es decisión del arquitecto.`, `deja el PR abierto; el usuario corre /juzgar-pr <n> en Claude Code.`)
        if (/\bgit\s+push\b[^;&|]*\b(main|master)\b/.test(c))
          bloquear(`no se hace push a main.`, `haz push de tu rama feat/<issue>-<id> y marca el PR listo con gh pr ready.`)
      }
    },
  }
}

// Guardia de rol de OpenCode (ejecutor). Delgada: la lógica está en scripts/harness.py (guard_opencode),
// probada en scripts/test_harness.py. Política fail-closed: si el motor no responde, se BLOQUEA la herramienta.
// Límite conocido (docs/SEGURIDAD.md): OpenCode no pasa por este hook las llamadas de subagentes (issue anomalyco/opencode#5894);
// para ellos quedan los permisos del agente, el contenedor y los git hooks.
import { execFileSync } from "child_process"
import { join } from "path"

export const Guardia = async ({ directory }: { directory: string }) => ({
  "tool.execute.before": async (input: any, output: any) => {
    if (process.env.HARNESS_OVERRIDE === "1") return
    let r: { block: boolean; msg: string }
    try {
      const out = execFileSync("python3", [join(directory, "scripts/harness.py"), "guard-opencode"], {
        cwd: directory,
        input: JSON.stringify({ tool: input?.tool ?? "", args: output?.args ?? {}, root: directory }),
        encoding: "utf8",
        timeout: 5000,
      })
      r = JSON.parse(out)
    } catch (e: any) {
      throw new Error(
        `⛔ Harness: el guardia no respondió (${e?.message ?? e}); por seguridad se bloquea ${input?.tool}. ` +
          `Corre scripts/doctor.sh. Salto consciente: HARNESS_OVERRIDE=1 (queda registrado).`,
      )
    }
    if (r.block) throw new Error(r.msg)
  },
})

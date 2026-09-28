// Guardia de rol de OpenCode (ejecutor). Delgada a propósito: toda la lógica está en scripts/harness.py
// (guard_opencode) y se prueba con scripts/test_harness.py. Verifica los nombres de herramienta con tu versión de OpenCode.
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
      // Si el motor falla, no dejamos pasar en silencio: los git hooks siguen protegiendo al commitear.
      console.error("[harness] guardia no disponible:", e?.message ?? e)
      return
    }
    if (r.block) throw new Error(r.msg)
  },
})

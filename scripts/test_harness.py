"""Pruebas del harness: python3 -m unittest discover -s scripts -p 'test_*.py' -v

Cada prueba crea un repo git temporal con harness.json y scripts/ copiados del repo base,
así que prueba exactamente lo que se instala en los proyectos.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

AQUI = Path(__file__).resolve().parent
BASE = AQUI.parent
sys.path.insert(0, str(AQUI))
import harness  # noqa: E402


def sh(cmd, cwd, env=None, stdin=None):
    e = {**os.environ, **(env or {})}
    for k in ("HARNESS_ROL", "HARNESS_OVERRIDE", "HARNESS_BRANCH"):
        if env is None or k not in env:
            e.pop(k, None)
    return subprocess.run(cmd, cwd=cwd, env=e, input=stdin, capture_output=True, text=True, shell=isinstance(cmd, str))


class Repo:
    def __init__(self):
        self.dir = Path(tempfile.mkdtemp())
        shutil.copy(BASE / "harness.json", self.dir / "harness.json")
        shutil.copytree(BASE / "scripts", self.dir / "scripts")
        shutil.copytree(BASE / ".githooks", self.dir / ".githooks")
        shutil.copytree(BASE / ".opencode", self.dir / ".opencode")
        shutil.copy(BASE / "opencode.json", self.dir / "opencode.json")
        for f in list((self.dir / ".githooks").iterdir()) + list((self.dir / "scripts").iterdir()):
            f.chmod(0o755)
        for c in ("git init -q", "git config user.email t@t", "git config user.name t", "git checkout -q -b main",
                  "git config core.hooksPath .githooks"):
            sh(c, self.dir)
        self.escribir("README.md", "x")
        self.escribir("src/app.ts", "x")
        self.escribir("src/auth/login.ts", "x")
        self.commit("init")

    def escribir(self, rel, texto):
        p = self.dir / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(texto)

    def commit(self, msg, env=None):
        sh("git add -A", self.dir)
        return sh(["git", "commit", "-qm", msg], self.dir, env)

    def rama(self, nombre):
        sh(["git", "checkout", "-q", "-b", nombre], self.dir)

    def propuesta(self, cid, riesgo="bajo", nivel="1", roja="no", issue=None):
        texto = f"# Propuesta\n## Harness\n" + (f"- Issue: #{issue}\n" if issue else "") + f"- Nivel: {nivel}\n- Riesgo: {riesgo}\n- Zonas: src\n- OpenCode-zona-roja: {roja}\n"
        self.escribir(f"openspec/changes/{cid}/proposal.md", texto)
        self.escribir(f"openspec/changes/{cid}/tasks.md", "- [ ] 1.1 algo")
        return self.commit("spec", {"HARNESS_OVERRIDE": "1"})

    def cerrar(self):
        shutil.rmtree(self.dir, ignore_errors=True)


class TestRiesgoYNivel(unittest.TestCase):
    def setUp(self):
        self.r = Repo()

    def tearDown(self):
        self.r.cerrar()

    def test_bajo_medio_alto(self):
        self.r.rama("fix/typo")
        self.r.escribir("docs/a.md", "doc"); self.r.commit("d")
        self.assertEqual(harness.calcular_riesgo(self.r.dir)["riesgo"], "bajo")
        self.r.escribir("src/util.ts", "u"); self.r.commit("u")
        self.assertEqual(harness.calcular_riesgo(self.r.dir)["riesgo"], "medio")
        self.r.escribir("src/auth/token.ts", "t"); self.r.commit("t")
        self.assertEqual(harness.calcular_riesgo(self.r.dir)["riesgo"], "alto")

    def test_declarado_sube_el_riesgo_y_alto_sube_a_nivel_3(self):
        self.r.rama("feat/add-x")
        self.r.propuesta("add-x", riesgo="alto", nivel="1")
        n = harness.calcular_nivel(self.r.dir)
        self.assertEqual(n["riesgo"]["riesgo"], "alto")
        self.assertEqual(n["nivel"], 3)
        self.assertTrue(n["requisitos"]["revision_3"])

    def test_rama_con_y_sin_issue_y_archivado(self):
        self.r.rama("feat/12-add-y")
        self.r.propuesta("add-y", issue="12")
        c = harness.info_cambio(self.r.dir)
        self.assertEqual((c["id"], c["issue"]), ("add-y", "12"))
        sh("mkdir -p openspec/changes/archive && git mv openspec/changes/add-y openspec/changes/archive/2026-09-28-add-y", self.r.dir)
        self.r.commit("archive", {"HARNESS_OVERRIDE": "1"})
        self.assertIn("archive/2026-09-28-add-y/proposal.md", harness.info_cambio(self.r.dir)["propuesta"])


class TestProceso(unittest.TestCase):
    def setUp(self):
        self.r = Repo()

    def tearDown(self):
        self.r.cerrar()

    def test_nivel_0_trivial_pasa_y_no_trivial_falla(self):
        self.r.rama("fix/typo")
        self.r.escribir("docs/a.md", "doc"); self.r.commit("d")
        self.assertEqual(harness.verificar_proceso(self.r.dir, "main", ""), [])
        self.r.escribir("src/util.ts", "u"); self.r.commit("u")
        self.assertTrue(any("triviales" in e for e in harness.verificar_proceso(self.r.dir, "main", "")))

    def test_nivel_1_pide_revision_1_y_ok_final_pero_no_issue(self):
        self.r.rama("feat/add-z")
        self.r.propuesta("add-z", nivel="1")
        errores = harness.verificar_proceso(self.r.dir, "main", "")
        self.assertTrue(any("Revisión 1" in e for e in errores))
        self.assertFalse(any("issue" in e for e in errores))
        body = "- [x] Revisión 1 ok\n- [x] OK final"
        self.assertEqual(harness.verificar_proceso(self.r.dir, "main", body), [])

    def test_nivel_2_exige_issue_enlazado(self):
        self.r.rama("feat/7-add-w")
        self.r.propuesta("add-w", nivel="2", issue="7")
        body = "- [x] Revisión 1\n- [x] OK final"
        self.assertTrue(any("#7" in e for e in harness.verificar_proceso(self.r.dir, "main", body)))
        self.assertEqual(harness.verificar_proceso(self.r.dir, "main", body + "\nCloses #7"), [])

    def test_riesgo_alto_exige_las_tres(self):
        self.r.rama("feat/9-add-auth")
        self.r.propuesta("add-auth", nivel="2", issue="9", riesgo="alto")
        body = "Closes #9\n- [x] Revisión 1\n- [x] OK final"
        errores = harness.verificar_proceso(self.r.dir, "main", body)
        self.assertTrue(any("Revisión 2" in e for e in errores) and any("Revisión 3" in e for e in errores))

    def test_rama_fuera_de_convencion(self):
        self.r.rama("mi-rama")
        self.assertTrue(harness.verificar_proceso(self.r.dir, "main", "")[0].startswith("Rama"))


class TestGuardias(unittest.TestCase):
    def setUp(self):
        self.r = Repo()
        os.environ.pop("HARNESS_OVERRIDE", None)

    def tearDown(self):
        self.r.cerrar()

    def c(self, tool, ti):
        return harness.guard_claude({"tool_name": tool, "tool_input": ti}, self.r.dir)[0]

    def o(self, tool, args):
        return harness.guard_opencode(tool, args, self.r.dir)["block"]

    def test_claude_edicion(self):
        d = str(self.r.dir)
        self.assertEqual(self.c("Write", {"file_path": f"{d}/src/app.ts"}), 2)
        self.assertEqual(self.c("Edit", {"file_path": "src/app.ts"}), 2)
        self.assertEqual(self.c("Write", {"file_path": f"{d}/openspec/changes/x/proposal.md"}), 0)
        self.assertEqual(self.c("Write", {"file_path": f"{d}/_bmad-output/specs/SPEC.md"}), 0)

    def test_claude_bash(self):
        self.assertEqual(self.c("Bash", {"command": "echo hola > src/app.ts"}), 2)
        self.assertEqual(self.c("Bash", {"command": "sed -i s/a/b/ src/app.ts"}), 2)
        self.assertEqual(self.c("Bash", {"command": "git apply x.patch"}), 2)
        self.assertEqual(self.c("Bash", {"command": "npm test > /dev/null && gh pr list 2>&1"}), 0)
        self.assertEqual(self.c("Bash", {"command": "echo x >> HANDOFF.md"}), 0)

    def test_claude_skills(self):
        self.assertEqual(self.c("Skill", {"skill": "bmad-architecture"}), 0)
        self.assertEqual(self.c("Skill", {"skill": "bmad-help"}), 0)
        self.assertEqual(self.c("Skill", {"skill": "bmad-deep-recon"}), 2)
        self.assertEqual(self.c("Skill", {"skill": "bmad-build"}), 2)
        self.assertEqual(self.c("Skill", {"skill": "openspec-apply-change"}), 2)
        self.assertEqual(self.c("Skill", {"skill": "docx"}), 0)

    def test_claude_override(self):
        os.environ["HARNESS_OVERRIDE"] = "1"
        try:
            self.assertEqual(self.c("Write", {"file_path": "src/app.ts"}), 0)
        finally:
            os.environ.pop("HARNESS_OVERRIDE")

    def test_opencode_rutas_y_zona_roja(self):
        self.r.rama("feat/add-p")
        self.r.propuesta("add-p", roja="no")
        self.assertTrue(self.o("edit", {"filePath": "openspec/changes/add-p/proposal.md"}))
        self.assertFalse(self.o("edit", {"filePath": "openspec/changes/add-p/tasks.md"}))
        self.assertFalse(self.o("write", {"filePath": "_bmad-output/digests/recon.md"}))
        self.assertTrue(self.o("write", {"filePath": "_bmad-output/specs/SPEC.md"}))
        self.assertTrue(self.o("edit", {"filePath": "harness.json"}))
        self.assertFalse(self.o("edit", {"filePath": "src/app.ts"}))
        self.assertTrue(self.o("edit", {"filePath": "src/auth/login.ts"}))
        self.r.propuesta("add-p", roja="autorizado")
        self.assertFalse(self.o("edit", {"filePath": "src/auth/login.ts"}))

    def test_opencode_bash_y_skills(self):
        self.assertTrue(self.o("bash", {"command": "npx openspec archive add-p"}))
        self.assertTrue(self.o("bash", {"command": "gh pr merge 3 --squash"}))
        self.assertTrue(self.o("bash", {"command": "git push origin main"}))
        self.assertFalse(self.o("bash", {"command": "git push -u origin feat/add-p"}))
        self.assertTrue(self.o("skill", {"name": "bmad-architecture"}))
        self.assertTrue(self.o("skill", {"name": "bmad-build-auto"}))
        self.assertFalse(self.o("skill", {"name": "bmad-deep-recon"}))
        self.assertFalse(self.o("skill", {"name": "openspec-apply-change"}))


class TestHooksGit(unittest.TestCase):
    def setUp(self):
        self.r = Repo()

    def tearDown(self):
        self.r.cerrar()

    def test_roles(self):
        self.r.escribir("src/app.ts", "y")
        self.assertNotEqual(self.r.commit("a", {"HARNESS_ROL": "arquitecto"}).returncode, 0)
        sh("git reset -q --hard", self.r.dir)
        self.r.escribir("src/app.ts", "y")
        self.assertNotEqual(self.r.commit("b", {"HARNESS_ROL": "ejecutor"}).returncode, 0, "ejecutor no commitea en main")
        sh("git reset -q --hard", self.r.dir)
        self.r.rama("feat/add-q")
        self.r.propuesta("add-q")
        self.r.escribir("src/app.ts", "z")
        self.assertEqual(self.r.commit("c", {"HARNESS_ROL": "ejecutor"}).returncode, 0)
        self.r.escribir("openspec/changes/add-q/proposal.md", "cambio")
        self.assertNotEqual(self.r.commit("d", {"HARNESS_ROL": "ejecutor"}).returncode, 0)
        sh("git reset -q --hard", self.r.dir)
        self.r.escribir("openspec/changes/add-q/tasks.md", "- [x] 1.1 algo")
        self.assertEqual(self.r.commit("e", {"HARNESS_ROL": "ejecutor"}).returncode, 0)
        self.r.escribir("src/auth/login.ts", "z")
        self.assertNotEqual(self.r.commit("f", {"HARNESS_ROL": "ejecutor"}).returncode, 0)
        sh("git reset -q --hard", self.r.dir)
        self.r.escribir("src/auth/login.ts", "z")
        self.assertEqual(self.r.commit("g", {"HARNESS_ROL": "ejecutor", "HARNESS_OVERRIDE": "1"}).returncode, 0)
        self.assertIn("Harness-Override: yes", sh("git log -1 --format=%B", self.r.dir).stdout)

    def test_pre_push_main(self):
        p = sh(["python3", "scripts/harness.py", "hook", "pre-push"], self.r.dir, {"HARNESS_ROL": "ejecutor"}, "refs/heads/x 0 refs/heads/main 0\n")
        self.assertEqual(p.returncode, 1)


class TestEmpaquetado(unittest.TestCase):
    def test_hooks_y_scripts_ejecutables_en_git(self):
        if not (BASE / ".git").exists():
            self.skipTest("no es el repo base")
        modos = subprocess.run(["git", "ls-files", "-s", ".githooks", "scripts"], cwd=BASE, capture_output=True, text=True).stdout.splitlines()
        no_ejec = [l.split()[-1] for l in modos if l.split()[0] != "100755" and not l.endswith(("test_harness.py",))]
        self.assertEqual(no_ejec, [], "git debe registrarlos como 100755 o los hooks se ignoran al clonar")


class TestRutasYSync(unittest.TestCase):
    def setUp(self):
        self.r = Repo()

    def tearDown(self):
        self.r.cerrar()

    def test_ruta_por_prefijo(self):
        cfg = harness.cargar(self.r.dir)
        self.assertEqual(harness.ruta_skill(cfg, "bmad-algo-nuevo")["clase"], "redactar")
        self.assertEqual(harness.ruta_skill(cfg, "openspec-algo-nuevo")["clase"], "decidir")
        self.assertEqual(harness.ruta_skill(cfg, "bmad-deep-recon")["herramienta"], "opencode")

    def test_sync_detecta_deriva(self):
        harness.sync(self.r.dir)
        self.assertEqual(harness.sync(self.r.dir, check=True), [])
        cfg = json.loads((self.r.dir / "harness.json").read_text())
        cfg["agentes"]["build"] = "opencode-go/otro-modelo"
        (self.r.dir / "harness.json").write_text(json.dumps(cfg))
        self.assertIn("opencode.json", harness.sync(self.r.dir, check=True))
        harness.sync(self.r.dir)
        self.assertIn("model: opencode-go/otro-modelo", (self.r.dir / ".opencode/agents/build.md").read_text() if (self.r.dir / ".opencode/agents/build.md").exists() else "model: opencode-go/otro-modelo")
        self.assertEqual(json.loads((self.r.dir / "opencode.json").read_text())["model"], "opencode-go/otro-modelo")

    def test_estado_sin_gh(self):
        self.r.escribir("openspec/changes/add-k/proposal.md", "p")
        p = harness.estado(self.r.dir)
        self.assertIn("add-k", Path(p).read_text())


if __name__ == "__main__":
    unittest.main()

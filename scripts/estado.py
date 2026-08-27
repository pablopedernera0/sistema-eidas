#!/usr/bin/env python3
"""Estado de sincronización de todos los repos del Sistema EIDAS en esta máquina.

Repos chequeados: sistema-eidas (este), sistema-eidas-datos (grupos.json privado,
symlinkeado desde acá), sistema-eidas-memory (memoria de Claude Code para este
proyecto), eidas-template en su copia de edición (hermana de sistema-eidas) y
eidas-template en cada copia por-materia (materias/<materia>/template — mirrors de
solo lectura, se editan siempre desde la copia de edición, nunca desde acá).

Los repos de materias/<materia>/grupos/ quedan afuera a propósito: no tienen estado
propio que importe entre máquinas, se resuelven con 'grupos.py sync <materia>'.

Para cada repo: fetch, y
  - si está limpio y solo atrasado  -> pull --ff-only automático
  - si tiene cambios sin commitear o commits locales sin pushear -> se reporta,
    no se toca nada (ver .claude/commands/estado-eidas.md para el criterio de
    cuándo ofrecer push, que es cosa de Claude, no de este script)
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MATERIAS_DIR = ROOT / "materias"


def git_output(args, cwd):
    result = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def check_repo(nombre, path):
    print(f"\n== {nombre} ==")
    print(f"   {path}")

    if not path.exists():
        print("   no está clonado en esta máquina")
        return
    if not (path / ".git").exists():
        print("   no es un repo git")
        return

    code, _, err = git_output(["fetch", "origin"], path)
    if code != 0:
        print(f"   no se pudo hacer fetch ({err.splitlines()[-1] if err else 'error desconocido'})")
        return

    code, branch, _ = git_output(["branch", "--show-current"], path)
    if code != 0 or not branch:
        print("   no se pudo determinar la branch actual (¿HEAD desprendido?)")
        return

    code, ahead_str, _ = git_output(["rev-list", "--count", f"{branch}@{{u}}..{branch}"], path)
    if code != 0:
        print(f"   '{branch}' no tiene upstream configurado, no puedo comparar")
        return
    _, behind_str, _ = git_output(["rev-list", "--count", f"{branch}..{branch}@{{u}}"], path)
    ahead, behind = int(ahead_str or 0), int(behind_str or 0)

    _, porcelain, _ = git_output(["status", "--porcelain"], path)
    dirty_files = porcelain.splitlines()

    if dirty_files:
        print(f"   cambios sin commitear en {len(dirty_files)} archivo(s) — no toco nada")
    if ahead:
        print(f"   {ahead} commit(s) locales sin pushear — no toco nada")
    if behind and not dirty_files and not ahead:
        code, out, err = git_output(["pull", "--ff-only", "origin", branch], path)
        if code == 0:
            print(f"   estaba {behind} commit(s) atrás, hice pull: {out or 'listo'}")
        else:
            print(f"   estaba {behind} commit(s) atrás pero el pull --ff-only falló: {err}")
    elif behind:
        print(f"   {behind} commit(s) nuevos en origin — no hago pull automático por lo de arriba")
    if not dirty_files and not ahead and not behind:
        print("   al día")


def find_memory_repo():
    projects_dir = Path.home() / ".claude" / "projects"
    if not projects_dir.exists():
        return None
    for memory_dir in sorted(projects_dir.glob("*/memory")):
        if not (memory_dir / ".git").exists():
            continue
        code, url, _ = git_output(["config", "--get", "remote.origin.url"], memory_dir)
        if code == 0 and "sistema-eidas-memory" in url:
            return memory_dir
    return None


def main():
    print("Estado de los repos del Sistema EIDAS")
    print("=" * 40)

    check_repo("sistema-eidas", ROOT)
    check_repo("sistema-eidas-datos", ROOT.parent / "sistema-eidas-datos")
    check_repo("eidas-template (edición)", ROOT.parent / "eidas-template")

    memory_path = find_memory_repo()
    if memory_path:
        check_repo("sistema-eidas-memory", memory_path)
    else:
        print("\n== sistema-eidas-memory ==")
        print("   no encontrado en ~/.claude/projects/*/memory en esta máquina")

    if not MATERIAS_DIR.exists():
        return
    for materia_path in sorted(p for p in MATERIAS_DIR.iterdir() if p.is_dir()):
        check_repo(f"eidas-template ({materia_path.name}, mirror)", materia_path / "template")


if __name__ == "__main__":
    sys.exit(main())

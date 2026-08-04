#!/usr/bin/env python3
"""Gestión de repos de grupos del Sistema EIDAS. Ver guia-de-uso.md."""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "grupos.json"
GRUPOS_DIR = ROOT / "grupos"


def load_config():
    with open(CONFIG_PATH) as f:
        return {g["id"]: g for g in json.load(f)["grupos"]}


def run(cmd, cwd=None, check=True):
    print(f"$ {' '.join(cmd)}" + (f"  (en {cwd})" if cwd else ""))
    result = subprocess.run(cmd, cwd=cwd)
    if check and result.returncode != 0:
        raise SystemExit(f"Falló: {' '.join(cmd)}")
    return result


def sync():
    GRUPOS_DIR.mkdir(exist_ok=True)
    for grupo_id, g in load_config().items():
        path = GRUPOS_DIR / grupo_id
        if path.exists():
            print(f"\n== {grupo_id}: ya clonado, actualizando main ==")
            run(["git", "checkout", "main"], cwd=path)
            run(["git", "pull", "origin", "main"], cwd=path)
        else:
            print(f"\n== {grupo_id}: clonando ==")
            run(["git", "clone", g["repo"], str(path)])


def publicar(grupo_id, skip_confirm=False):
    config = load_config()
    if grupo_id not in config:
        raise SystemExit(f"'{grupo_id}' no está en {CONFIG_PATH.name}")

    path = GRUPOS_DIR / grupo_id
    if not path.exists():
        raise SystemExit(f"{path} no existe todavía — corré 'sync' primero")

    branches = subprocess.run(
        ["git", "branch", "--list", "feedback"], cwd=path, capture_output=True, text=True
    ).stdout
    if "feedback" not in branches:
        raise SystemExit(f"{grupo_id} no tiene branch 'feedback' — no hay nada para publicar")

    if not skip_confirm:
        resp = input(
            f"¿Confirmás publicar la devolución de '{grupo_id}' "
            f"(merge feedback → main, y push)? [s/N] "
        )
        if resp.strip().lower() != "s":
            print("Cancelado.")
            return

    run(["git", "checkout", "main"], cwd=path)
    run(["git", "pull", "origin", "main"], cwd=path)
    pre_merge_sha = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=path, capture_output=True, text=True
    ).stdout.strip()
    run(["git", "merge", "feedback", "--no-edit"], cwd=path)
    marcar_publicado(path, pre_merge_sha)
    run(["git", "push", "origin", "main"], cwd=path)
    print(f"\n{grupo_id}: devolución publicada.")


def marcar_publicado(path, pre_merge_sha):
    """Tilda '- [ ] Publicado al grupo' en los archivos de feedback que trajo el merge."""
    changed = subprocess.run(
        ["git", "diff", "--name-only", pre_merge_sha, "HEAD", "--", "feedback/"],
        cwd=path, capture_output=True, text=True
    ).stdout.split()

    updated = []
    for rel_path in changed:
        file_path = path / rel_path
        if not file_path.exists():
            continue
        text = file_path.read_text()
        marked = text.replace("- [ ] Publicado al grupo", "- [x] Publicado al grupo")
        if marked != text:
            file_path.write_text(marked)
            updated.append(rel_path)

    if updated:
        run(["git", "add", *updated], cwd=path)
        run(["git", "commit", "-m", "Marcar devolución como publicada"], cwd=path)


def main():
    if len(sys.argv) < 2:
        print("Uso:\n  grupos.py sync\n  grupos.py publicar <grupo-id> [--yes]")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "sync":
        sync()
    elif cmd == "publicar":
        if len(sys.argv) < 3:
            raise SystemExit("Uso: grupos.py publicar <grupo-id> [--yes]")
        grupo_id = sys.argv[2]
        skip_confirm = "--yes" in sys.argv[3:]
        publicar(grupo_id, skip_confirm)
    else:
        raise SystemExit(f"Comando desconocido: {cmd}")


if __name__ == "__main__":
    main()

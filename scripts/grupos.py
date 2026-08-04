#!/usr/bin/env python3
"""Gestión de repos de grupos del Sistema EIDAS, por materia. Ver guia-de-uso.md."""

import json
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MATERIAS_DIR = ROOT / "materias"
N8N_WEBHOOK_URL = "http://localhost:5678/webhook/evaluar-grupo"
FECHA_RE = re.compile(r"feedback/(\d{4}-\d{2}-\d{2})\.md$")


def materia_dir(materia):
    path = MATERIAS_DIR / materia
    if not path.exists():
        raise SystemExit(
            f"No existe {path}. Materias disponibles: "
            + ", ".join(p.name for p in MATERIAS_DIR.iterdir() if p.is_dir())
        )
    return path


def load_config(materia):
    config_path = materia_dir(materia) / "grupos.json"
    with open(config_path) as f:
        return {g["id"]: g for g in json.load(f)["grupos"]}, config_path


def run(cmd, cwd=None, check=True):
    print(f"$ {' '.join(cmd)}" + (f"  (en {cwd})" if cwd else ""))
    result = subprocess.run(cmd, cwd=cwd)
    if check and result.returncode != 0:
        raise SystemExit(f"Falló: {' '.join(cmd)}")
    return result


def sync(materia):
    grupos_dir = materia_dir(materia) / "grupos"
    grupos_dir.mkdir(exist_ok=True)
    config, _ = load_config(materia)
    for grupo_id, g in config.items():
        path = grupos_dir / grupo_id
        if path.exists():
            print(f"\n== {grupo_id}: ya clonado, actualizando main ==")
            run(["git", "checkout", "main"], cwd=path)
            run(["git", "pull", "origin", "main"], cwd=path)
        else:
            print(f"\n== {grupo_id}: clonando ==")
            run(["git", "clone", g["repo"], str(path)])


def publicar(materia, grupo_id, skip_confirm=False):
    config, config_path = load_config(materia)
    if grupo_id not in config:
        raise SystemExit(f"'{grupo_id}' no está en {config_path}")

    path = materia_dir(materia) / "grupos" / grupo_id
    if not path.exists():
        raise SystemExit(f"{path} no existe todavía — corré 'sync {materia}' primero")

    branches = subprocess.run(
        ["git", "branch", "--list", "feedback"], cwd=path, capture_output=True, text=True
    ).stdout
    if "feedback" not in branches:
        raise SystemExit(f"{grupo_id} no tiene branch 'feedback' — no hay nada para publicar")

    if not skip_confirm:
        resp = input(
            f"¿Confirmás publicar la devolución de '{materia}/{grupo_id}' "
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
    fechas = marcar_publicado(path, pre_merge_sha)
    run(["git", "push", "origin", "main"], cwd=path)
    print(f"\n{materia}/{grupo_id}: devolución publicada.")

    if not fechas:
        print(
            "Aviso: no se detectó ningún feedback/AAAA-MM-DD.md en el merge — no se "
            "disparó la notificación. Si hace falta, corré 'notificar' a mano."
        )
    for fecha in fechas:
        notificar(materia, grupo_id, fecha)


def marcar_publicado(path, pre_merge_sha):
    """Tilda '- [ ] Publicado al grupo' en los archivos que trajo el merge y devuelve
    la lista de fechas (AAAA-MM-DD) detectadas en sus nombres."""
    changed = subprocess.run(
        ["git", "diff", "--name-only", pre_merge_sha, "HEAD", "--", "feedback/"],
        cwd=path, capture_output=True, text=True
    ).stdout.split()

    updated = []
    fechas = []
    for rel_path in changed:
        m = FECHA_RE.search(rel_path)
        if m:
            fechas.append(m.group(1))

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

    return fechas


def notificar(materia, grupo_id, fecha):
    """Dispara el workflow de N8N (webhook local) para subir a Drive y avisar por Gmail."""
    payload = json.dumps({"materia": materia, "grupo_id": grupo_id, "fecha": fecha}).encode()
    req = urllib.request.Request(
        N8N_WEBHOOK_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    print(f"$ POST {N8N_WEBHOOK_URL}  (materia={materia}, grupo_id={grupo_id}, fecha={fecha})")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = resp.read().decode()
            print(f"N8N respondió {resp.status}: {body[:300]}")
    except (urllib.error.URLError, TimeoutError) as e:
        print(
            f"AVISO: no se pudo notificar a N8N ({e}). ¿Está corriendo "
            f"'docker compose up -d' en infra/n8n/? Podés reintentar con:\n"
            f"  python3 scripts/grupos.py notificar {materia} {grupo_id} {fecha}"
        )


def main():
    uso = (
        "Uso:\n"
        "  grupos.py sync <materia>\n"
        "  grupos.py publicar <materia> <grupo-id> [--yes]\n"
        "  grupos.py notificar <materia> <grupo-id> <AAAA-MM-DD>\n\n"
        "<materia> es el nombre de carpeta en materias/, ej: af-diseno-sistemas-web-31"
    )
    if len(sys.argv) < 2:
        print(uso)
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "sync":
        if len(sys.argv) < 3:
            raise SystemExit("Uso: grupos.py sync <materia>")
        sync(sys.argv[2])
    elif cmd == "publicar":
        if len(sys.argv) < 4:
            raise SystemExit("Uso: grupos.py publicar <materia> <grupo-id> [--yes]")
        materia, grupo_id = sys.argv[2], sys.argv[3]
        skip_confirm = "--yes" in sys.argv[4:]
        publicar(materia, grupo_id, skip_confirm)
    elif cmd == "notificar":
        if len(sys.argv) < 5:
            raise SystemExit("Uso: grupos.py notificar <materia> <grupo-id> <AAAA-MM-DD>")
        notificar(sys.argv[2], sys.argv[3], sys.argv[4])
    else:
        raise SystemExit(f"Comando desconocido: {cmd}\n\n{uso}")


if __name__ == "__main__":
    main()

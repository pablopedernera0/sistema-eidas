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
DATOS_DIR = ROOT.parent / "sistema-eidas-datos"
N8N_WEBHOOK_URL = "http://localhost:5678/webhook/evaluar-grupo"
FECHA_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})\.md$")
CONFIANZA_RE = re.compile(r"^\*\*Confianza Claude:\*\*.*\n", re.MULTILINE)
PREGUNTA_DOCENTE_RE = re.compile(r"## Pregunta para el docente\n\n.*?\n\n(?=## )", re.DOTALL)


def limpiar_confidencial(text):
    """Saca las líneas 'Confianza Claude' y la sección entera 'Pregunta para el
    docente' — son para uso interno del docente durante la revisión, nunca deberían
    llegarle al grupo. No-op si el docente ya las sacó a mano."""
    text = CONFIANZA_RE.sub("", text)
    text = PREGUNTA_DOCENTE_RE.sub("", text)
    return text


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
            actual = subprocess.run(
                ["git", "branch", "--show-current"], cwd=path, capture_output=True, text=True
            ).stdout.strip()
            if actual and actual != "main":
                print(
                    f"\n== {grupo_id}: está parado en la branch '{actual}', no en 'main' "
                    f"(no debería pasar en el flujo normal) — no lo toco, revisalo a mano =="
                )
                continue
            print(f"\n== {grupo_id}: ya clonado, actualizando main ==")
            run(["git", "checkout", "main"], cwd=path)
            run(["git", "pull", "origin", "main"], cwd=path)
        else:
            print(f"\n== {grupo_id}: clonando ==")
            run(["git", "clone", g["repo"], str(path)])


def borradores_dir(materia, grupo_id):
    """Carpeta en sistema-eidas-datos (repo privado, sincronizado entre máquinas del
    docente) donde vive el borrador de devolución de un grupo hasta que se publica. No
    vive en el repo del grupo ni en una branch local — eso es lo que hacía que una
    devolución en curso quedara atada a una sola máquina."""
    return DATOS_DIR / materia / "borradores" / grupo_id


def publicar(materia, grupo_id, skip_confirm=False):
    config, config_path = load_config(materia)
    if grupo_id not in config:
        raise SystemExit(f"'{grupo_id}' no está en {config_path}")

    path = materia_dir(materia) / "grupos" / grupo_id
    if not path.exists():
        raise SystemExit(f"{path} no existe todavía — corré 'sync {materia}' primero")

    bdir = borradores_dir(materia, grupo_id)
    if not bdir.exists():
        raise SystemExit(f"{bdir} no existe — generá un borrador con /evaluar-grupo primero")

    pendientes = sorted(
        f for f in bdir.glob("*.md")
        if FECHA_RE.match(f.name) and "- [x] Publicado al grupo" not in f.read_text()
    )
    if not pendientes:
        raise SystemExit(f"No hay ningún borrador sin publicar en {bdir}")

    sucio = subprocess.run(
        ["git", "status", "--porcelain"], cwd=path, capture_output=True, text=True
    ).stdout
    if sucio.strip():
        raise SystemExit(
            f"{grupo_id} tiene cambios sin commitear en su propio repo clonado — no "
            f"debería pasar (ya nada se edita ahí hasta publicar), revisalo a mano antes "
            f"de publicar."
        )

    fechas_str = ", ".join(f.stem for f in pendientes)
    if not skip_confirm:
        resp = input(
            f"¿Confirmás publicar la devolución de '{materia}/{grupo_id}' "
            f"({fechas_str}) y pushear al repo del grupo? [s/N] "
        )
        if resp.strip().lower() != "s":
            print("Cancelado.")
            return

    run(["git", "checkout", "main"], cwd=path)
    run(["git", "pull", "origin", "main"], cwd=path)

    fechas = []
    feedback_dir = path / "feedback"
    feedback_dir.mkdir(exist_ok=True)
    for f in pendientes:
        fecha = f.stem
        original = f.read_text()
        text = limpiar_confidencial(original)
        if text != original:
            print(f"Aviso: saqué restos de 'Confianza Claude' y/o 'Pregunta para el docente' de {fecha}.md.")
        marcado = text.replace("- [ ] Publicado al grupo", "- [x] Publicado al grupo")
        (feedback_dir / f"{fecha}.md").write_text(marcado)
        f.write_text(marcado)  # también en el borrador — para no volver a publicarlo de nuevo
        fechas.append(fecha)
        run(["git", "add", f"feedback/{fecha}.md"], cwd=path)

    run(["git", "commit", "-m", f"Devolución {fechas_str}"], cwd=path)
    run(["git", "push", "origin", "main"], cwd=path)
    print(f"\n{materia}/{grupo_id}: devolución publicada ({fechas_str}).")

    # La devolución ya está pusheada al repo del grupo — lo de acá es bookkeeping en el
    # repo privado (marcar el borrador como publicado). Si algo de esto falla, avisamos
    # pero no abortamos: no tiene sentido dejar de notificar al grupo por un problema en
    # un repo aparte que ya cumplió su función.
    rel_bdir = bdir.relative_to(DATOS_DIR)
    run(["git", "pull", "--ff-only"], cwd=DATOS_DIR, check=False)
    dsucio = subprocess.run(
        ["git", "status", "--porcelain", "--", str(rel_bdir)],
        cwd=DATOS_DIR, capture_output=True, text=True
    ).stdout
    if dsucio.strip():
        run(["git", "add", str(rel_bdir)], cwd=DATOS_DIR, check=False)
        run(
            ["git", "commit", "-m", f"Marcar publicada la devolución de {materia}/{grupo_id} ({fechas_str})"],
            cwd=DATOS_DIR, check=False,
        )
        if not run(["git", "push"], cwd=DATOS_DIR, check=False).returncode == 0:
            print(
                f"Aviso: no pude pushear en sistema-eidas-datos el marcado de "
                f"'publicado' del borrador — quedó commiteado local. Corré 'git push' ahí "
                f"a mano cuando puedas, para que otra máquina no lo vuelva a publicar."
            )

    for fecha in fechas:
        notificar(materia, grupo_id, fecha)


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

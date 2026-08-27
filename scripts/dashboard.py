#!/usr/bin/env python3
"""Servidor local (solo 127.0.0.1, nunca expuesto a la red) que muestra el estado de
evaluación de cada grupo de cada materia. Recalcula todo en cada request leyendo
grupos.json y el estado git local de cada repo de grupo (branch 'feedback', que nunca
se pushea) — no llama a GitHub ni a N8N, no escribe nada. La página se refresca sola
cada REFRESH_SECONDS. Arrancalo con /dashboard, o a mano:
  python3 scripts/dashboard.py [--no-abrir]
Ver bitacora-implementacion.md y CLAUDE.md para el pipeline completo."""

import json
import re
import socket
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path

try:
    from flask import Flask, Response
except ImportError:
    raise SystemExit("Falta flask instalado — corré: pip install flask")

ROOT = Path(__file__).resolve().parent.parent
MATERIAS_DIR = ROOT / "materias"
PORT = 8420
REFRESH_SECONDS = 10

FECHA_RE = re.compile(r"feedback/(\d{4}-\d{2}-\d{2})\.md$")

ESTADO_LABELS = {
    "no-clonado": ("No clonado", "#9ca3af"),
    "sin-evaluar": ("Sin evaluar", "#9ca3af"),
    "borrador": ("Borrador generado", "#d97706"),
    "revisado": ("Revisado, sin publicar", "#2563eb"),
    "publicado": ("Publicado", "#16a34a"),
}

app = Flask(__name__)


def git(args, cwd):
    result = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    return result.stdout.strip() if result.returncode == 0 else ""


def estado_grupo(repo_path):
    if not repo_path.exists():
        return {"estado": "no-clonado", "detalle": None, "ultima_actividad": None}

    ultima_actividad = git(["log", "-1", "--format=%ad", "--date=short", "main"], repo_path) or None

    if "feedback" not in git(["branch", "--list", "feedback"], repo_path):
        return {"estado": "sin-evaluar", "detalle": None, "ultima_actividad": ultima_actividad}

    archivos = git(
        ["ls-tree", "-r", "--name-only", "feedback", "--", "feedback/"], repo_path
    ).splitlines()
    fechas = sorted(m.group(1) for a in archivos if (m := FECHA_RE.search(a)))
    if not fechas:
        return {"estado": "borrador", "detalle": "sin archivo detectable", "ultima_actividad": ultima_actividad}

    ultima_fecha = fechas[-1]
    contenido = git(["show", f"feedback:feedback/{ultima_fecha}.md"], repo_path)

    if re.search(r"- \[x\] Publicado al grupo", contenido):
        estado = "publicado"
    elif re.search(r"- \[x\] Revisado y aprobado", contenido):
        estado = "revisado"
    else:
        estado = "borrador"

    return {"estado": estado, "detalle": ultima_fecha, "ultima_actividad": ultima_actividad}


def recolectar():
    materias = []
    for materia_path in sorted(p for p in MATERIAS_DIR.iterdir() if p.is_dir()):
        config_path = materia_path / "grupos.json"
        if not config_path.exists():
            continue
        with open(config_path) as f:
            grupos_config = json.load(f)["grupos"]

        grupos = []
        for g in grupos_config:
            repo_path = materia_path / "grupos" / g["id"]
            info = estado_grupo(repo_path)
            grupos.append({"id": g["id"], "email": g.get("email", ""), **info})

        materias.append({"nombre": materia_path.name, "grupos": grupos})
    return materias


def render_fila(g):
    label, color = ESTADO_LABELS[g["estado"]]
    detalle = f" — {g['detalle']}" if g["detalle"] else ""
    actividad = g["ultima_actividad"] or "—"
    return f"""
    <tr>
      <td>{g['id']}</td>
      <td>{g['email']}</td>
      <td>{actividad}</td>
      <td><span class="badge" style="background:{color}">{label}{detalle}</span></td>
    </tr>"""


def render_materia(m):
    conteo = {}
    for g in m["grupos"]:
        conteo[g["estado"]] = conteo.get(g["estado"], 0) + 1
    resumen = " · ".join(
        f"{n} {ESTADO_LABELS[estado][0].lower()}" for estado, n in conteo.items()
    )

    filas = "".join(render_fila(g) for g in m["grupos"])
    return f"""
    <section>
      <h2>{m['nombre']}</h2>
      <p class="resumen">{len(m['grupos'])} grupos — {resumen}</p>
      <table>
        <thead>
          <tr><th>Grupo</th><th>Email</th><th>Última actividad (main)</th><th>Estado evaluación</th></tr>
        </thead>
        <tbody>{filas}
        </tbody>
      </table>
    </section>"""


def render_html(materias):
    secciones = "".join(render_materia(m) for m in materias)
    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta http-equiv="refresh" content="{REFRESH_SECONDS}">
<title>Dashboard EIDAS</title>
<style>
  body {{ font-family: system-ui, sans-serif; max-width: 900px; margin: 2rem auto; padding: 0 1rem; color: #1f2937; }}
  h1 {{ margin-bottom: 0.25rem; }}
  .subtitulo {{ color: #6b7280; margin-top: 0; }}
  section {{ margin-bottom: 2.5rem; }}
  h2 {{ border-bottom: 2px solid #e5e7eb; padding-bottom: 0.25rem; }}
  .resumen {{ color: #6b7280; }}
  table {{ width: 100%; border-collapse: collapse; margin-top: 0.5rem; }}
  th, td {{ text-align: left; padding: 0.5rem 0.75rem; border-bottom: 1px solid #e5e7eb; }}
  th {{ color: #6b7280; font-weight: 600; font-size: 0.85rem; text-transform: uppercase; }}
  .badge {{ color: white; padding: 0.15rem 0.6rem; border-radius: 999px; font-size: 0.85rem; white-space: nowrap; }}
  footer {{ color: #9ca3af; font-size: 0.85rem; margin-top: 3rem; }}
</style>
</head>
<body>
  <h1>Dashboard EIDAS</h1>
  <p class="subtitulo">
    Estado local de evaluación por materia y grupo. Se refresca solo cada {REFRESH_SECONDS}s.
    Solo lectura — no toca git ni N8N.
  </p>
  {secciones}
  <footer>scripts/dashboard.py — http://127.0.0.1:{PORT} — corriendo local, nunca expuesto a la red.</footer>
</body>
</html>"""


@app.route("/")
def index():
    return Response(render_html(recolectar()), mimetype="text/html")


def ya_corriendo():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.3)
        return s.connect_ex(("127.0.0.1", PORT)) == 0


def abrir_navegador_demorado(url, espera=0.6):
    def _abrir():
        time.sleep(espera)
        webbrowser.open(url)
    threading.Thread(target=_abrir, daemon=True).start()


def main():
    url = f"http://127.0.0.1:{PORT}"
    abrir = "--no-abrir" not in sys.argv

    if ya_corriendo():
        print(f"Ya está corriendo en {url}")
        if abrir:
            webbrowser.open(url)
        return

    print(f"Dashboard EIDAS en {url} (refresca solo cada {REFRESH_SECONDS}s). Ctrl+C para parar.")
    if abrir:
        abrir_navegador_demorado(url)
    app.run(host="127.0.0.1", port=PORT, debug=False)


if __name__ == "__main__":
    main()

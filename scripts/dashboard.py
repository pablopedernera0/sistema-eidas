#!/usr/bin/env python3
"""Servidor local (solo 127.0.0.1, nunca expuesto a la red) que muestra el estado de
evaluación de cada grupo de cada materia. Recalcula todo en cada request leyendo
grupos.json y los borradores de sistema-eidas-datos/<materia>/borradores/<grupo-id>/
(repo hermano de sistema-eidas) — no llama a GitHub ni a N8N. La página de grupos se
refresca sola cada REFRESH_SECONDS y es de solo lectura. La pestaña /cronograma es la
única que escribe: edita y guarda el cronograma*.md de una materia directo al archivo
en disco — nunca hace commit ni push, eso lo sigue haciendo el docente a mano. Arrancalo
con /dashboard, o a mano:
  python3 scripts/dashboard.py [--no-abrir]
Ver bitacora-implementacion.md y CLAUDE.md para el pipeline completo."""

import html
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
    from flask import Flask, Response, redirect, request
except ImportError:
    raise SystemExit("Falta flask instalado — corré: pip install flask")

try:
    import markdown as mdlib
except ImportError:
    raise SystemExit("Falta el paquete markdown instalado — corré: pip install markdown")

ROOT = Path(__file__).resolve().parent.parent
MATERIAS_DIR = ROOT / "materias"
DATOS_DIR = ROOT.parent / "sistema-eidas-datos"
PORT = 8420
REFRESH_SECONDS = 10

FECHA_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})\.md$")
CRONOGRAMA_GLOB = "cronograma*.md"

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


def estado_grupo(repo_path, borrador_dir):
    if not repo_path.exists():
        return {"estado": "no-clonado", "detalle": None, "ultima_actividad": None}

    ultima_actividad = git(["log", "-1", "--format=%ad", "--date=short", "main"], repo_path) or None

    if not borrador_dir.exists():
        return {"estado": "sin-evaluar", "detalle": None, "ultima_actividad": ultima_actividad}

    fechas = sorted(m.group(1) for f in borrador_dir.iterdir() if (m := FECHA_RE.match(f.name)))
    if not fechas:
        return {"estado": "sin-evaluar", "detalle": None, "ultima_actividad": ultima_actividad}

    ultima_fecha = fechas[-1]
    contenido = (borrador_dir / f"{ultima_fecha}.md").read_text()

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

        borradores_dir = DATOS_DIR / materia_path.name / "borradores"

        grupos = []
        for g in grupos_config:
            repo_path = materia_path / "grupos" / g["id"]
            info = estado_grupo(repo_path, borradores_dir / g["id"])
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


BASE_CSS = """
  body { font-family: system-ui, sans-serif; max-width: 900px; margin: 2rem auto; padding: 0 1rem; color: #1f2937; }
  h1 { margin-bottom: 0.25rem; }
  .subtitulo { color: #6b7280; margin-top: 0; }
  nav { margin: 1rem 0 2rem; border-bottom: 2px solid #e5e7eb; padding-bottom: 0.75rem; }
  nav a { margin-right: 1.25rem; text-decoration: none; color: #6b7280; font-weight: 600; }
  nav a.activo { color: #1f2937; }
  section { margin-bottom: 2.5rem; }
  h2 { border-bottom: 2px solid #e5e7eb; padding-bottom: 0.25rem; }
  .resumen { color: #6b7280; }
  table { width: 100%; border-collapse: collapse; margin-top: 0.5rem; }
  th, td { text-align: left; padding: 0.5rem 0.75rem; border-bottom: 1px solid #e5e7eb; }
  th { color: #6b7280; font-weight: 600; font-size: 0.85rem; text-transform: uppercase; }
  .badge { color: white; padding: 0.15rem 0.6rem; border-radius: 999px; font-size: 0.85rem; white-space: nowrap; }
  footer { color: #9ca3af; font-size: 0.85rem; margin-top: 3rem; }
  .tabs-materia { margin-bottom: 1rem; }
  .tabs-materia a { margin-right: 1rem; padding: 0.25rem 0.75rem; border-radius: 999px; background: #f3f4f6; color: #374151; text-decoration: none; font-size: 0.9rem; }
  .tabs-materia a.activo { background: #1f2937; color: white; }
  .acciones { margin-bottom: 1rem; }
  .acciones a, .acciones button { font-size: 0.9rem; padding: 0.4rem 0.9rem; border-radius: 6px; border: 1px solid #d1d5db; background: white; color: #1f2937; text-decoration: none; cursor: pointer; }
  .acciones button.guardar { background: #16a34a; color: white; border-color: #16a34a; }
  .aviso-guardado { background: #dcfce7; color: #166534; padding: 0.5rem 0.9rem; border-radius: 6px; margin-bottom: 1rem; display: inline-block; }
  textarea { width: 100%; min-height: 70vh; font-family: ui-monospace, monospace; font-size: 0.85rem; padding: 0.75rem; box-sizing: border-box; }
  .cronograma-render table { font-size: 0.9rem; }
  .cronograma-render { line-height: 1.5; }
"""


def render_nav(activo):
    items = [("/", "Grupos"), ("/cronograma", "Cronograma")]
    enlaces = "".join(
        f'<a href="{href}" class="{"activo" if href == activo else ""}">{label}</a>'
        for href, label in items
    )
    return f"<nav>{enlaces}</nav>"


def render_html(materias):
    secciones = "".join(render_materia(m) for m in materias)
    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta http-equiv="refresh" content="{REFRESH_SECONDS}">
<title>Dashboard EIDAS</title>
<style>{BASE_CSS}</style>
</head>
<body>
  <h1>Dashboard EIDAS</h1>
  {render_nav("/")}
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


def listar_cronogramas():
    materias = []
    for materia_path in sorted(p for p in MATERIAS_DIR.iterdir() if p.is_dir()):
        archivos = sorted(materia_path.glob(CRONOGRAMA_GLOB))
        if archivos:
            materias.append((materia_path.name, archivos[0]))
    return materias


def render_cronograma_page(materia_actual, archivo, editar, guardado):
    disponibles = listar_cronogramas()
    if not disponibles:
        cuerpo = "<p>No hay ningún archivo <code>cronograma*.md</code> en ninguna materia todavía.</p>"
    else:
        tabs = "".join(
            f'<a href="/cronograma/{nombre}" class="{"activo" if nombre == materia_actual else ""}">{nombre}</a>'
            for nombre, _ in disponibles
        )
        aviso = '<p class="aviso-guardado">Guardado.</p>' if guardado else ""
        contenido = archivo.read_text()

        if editar:
            acciones = (
                f'<a href="/cronograma/{materia_actual}">Cancelar</a> '
                f'<button class="guardar" type="submit" form="form-cronograma">Guardar</button>'
            )
            cuerpo_editor = (
                f'<form id="form-cronograma" method="post" action="/cronograma/{materia_actual}">'
                f'<textarea name="contenido">{html.escape(contenido)}</textarea>'
                f"</form>"
            )
        else:
            acciones = f'<a href="/cronograma/{materia_actual}?editar=1">Editar</a>'
            cuerpo_editor = (
                f'<div class="cronograma-render">'
                f'{mdlib.markdown(contenido, extensions=["tables"])}'
                f"</div>"
            )

        cuerpo = f"""
        <div class="tabs-materia">{tabs}</div>
        {aviso}
        <div class="acciones">{acciones}</div>
        {cuerpo_editor}
        """

    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>Cronograma EIDAS — {materia_actual or ""}</title>
<style>{BASE_CSS}</style>
</head>
<body>
  <h1>Cronograma</h1>
  {render_nav("/cronograma")}
  <p class="subtitulo">
    Visualiza y edita el archivo <code>cronograma*.md</code> de cada materia. Guardar
    escribe directo al archivo — no hace commit ni push, eso queda para vos a mano.
  </p>
  {cuerpo}
  <footer>scripts/dashboard.py — http://127.0.0.1:{PORT} — corriendo local, nunca expuesto a la red.</footer>
</body>
</html>"""


@app.route("/cronograma")
def cronograma_index():
    disponibles = listar_cronogramas()
    if not disponibles:
        return Response(render_cronograma_page(None, None, False, False), mimetype="text/html")
    return redirect(f"/cronograma/{disponibles[0][0]}")


@app.route("/cronograma/<materia>", methods=["GET", "POST"])
def cronograma_materia(materia):
    disponibles = dict(listar_cronogramas())
    archivo = disponibles.get(materia)
    if archivo is None:
        return Response(f"No encontré cronograma para la materia '{materia}'.", status=404)

    if request.method == "POST":
        archivo.write_text(request.form["contenido"])
        return redirect(f"/cronograma/{materia}?guardado=1")

    editar = request.args.get("editar") == "1"
    guardado = request.args.get("guardado") == "1"
    return Response(render_cronograma_page(materia, archivo, editar, guardado), mimetype="text/html")


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

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
import mimetypes
import posixpath
import re
import socket
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from datetime import datetime
from pathlib import Path

import grupos as grupos_py

try:
    from flask import Flask, Response, abort, redirect, request
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
            grupos.append({"id": g["id"], "email": g.get("email", ""), "materia": materia_path.name, **info})

        materias.append({"nombre": materia_path.name, "grupos": grupos})
    return materias


def render_fila(g):
    label, color = ESTADO_LABELS[g["estado"]]
    detalle = f" — {g['detalle']}" if g["detalle"] else ""
    actividad = g["ultima_actividad"] or "—"
    return f"""
    <tr>
      <td><a href="/recorrer/{g['materia']}/grupo/{urllib.parse.quote(g['id'])}">{g['id']}</a></td>
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
    items = [("/", "Grupos"), ("/recorrer", "Recorrer"), ("/notas", "Notas"), ("/cronograma", "Cronograma")]
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


# ---------------------------------------------------------------------------
# Recorrer: navegador de los repos clonados de los grupos, de solo lectura.
# Dos formas: por grupo (todos los archivos de un grupo, en el orden del template) y
# por sección (el mismo archivo en todos los grupos, uno detrás del otro). Lee los
# clones locales de materias/<materia>/grupos/ — correr /sync antes para tenerlos al día.
# ---------------------------------------------------------------------------

PLANTUML_URL = "http://127.0.0.1:8090/svg"

# Orden de la rúbrica de Diseño de Sistemas Web; lo que el template tenga y no esté acá
# va al final, así una materia con otro template igual funciona.
ORDEN_SECCIONES = [
    "README.md", "integrantes.md", "docs/stakeholders.md", "docs/requisitos.md",
    "docs/historias-de-usuario.md", "docs/casos-de-uso.md", "diagramas/casos-de-uso.puml",
    "DoR.md", "slicing.md", "docs/er-modelo.md", "diagramas/er.puml", "docs/diseño-ui.md",
    "diagramas/wireframes/",
]

RUIDO_RE = re.compile(
    r"(^|/)(\.gitkeep|\.gitignore|\.markdownlint\.json|\.DS_Store)$"
    r"|^\.github/|^feedback/|^RECURSOS\.md$|(^|/)(node_modules|__pycache__|\.venv|venv)/"
)
IMAGEN_EXT = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp"}
PUML_EXT = {".puml", ".plantuml", ".pu", ".iuml"}
PALABRAS_GENERICAS = {"docs", "diagramas", "puml", "modelo"}


def q(path):
    return urllib.parse.quote(path)


def grupos_de(materia):
    config = MATERIAS_DIR / materia / "grupos.json"
    if not config.exists():
        return []
    with open(config) as f:
        return json.load(f)["grupos"]


def materias_con_grupos():
    return [p.name for p in sorted(MATERIAS_DIR.iterdir()) if (p / "grupos.json").exists()]


def ls_files(repo):
    result = subprocess.run(["git", "-C", str(repo), "ls-files", "-z"], capture_output=True, text=True)
    return [p for p in result.stdout.split("\0") if p and not RUIDO_RE.search(p)]


def secciones_de(materia):
    template = MATERIAS_DIR / materia / "template"
    archivos = ls_files(template) if template.exists() else []
    secciones = [
        s for s in ORDEN_SECCIONES
        if (s.endswith("/") and (template / s).is_dir()) or s in archivos
    ]
    resto = [a for a in archivos if not any(pertenece(a, s) for s in secciones)]
    return secciones + sorted(resto)


def pertenece(path, seccion):
    """El archivo corresponde a esa sección del template, aunque cambie mayúsculas o carpeta."""
    if seccion.endswith("/"):
        return path.lower().startswith(seccion.lower())
    if path.lower() == seccion.lower():
        return True
    nombre = Path(seccion).name.lower()
    return nombre != "readme.md" and Path(path).name.lower() == nombre


def orden_archivos(archivos, secciones):
    def clave(path):
        for i, s in enumerate(secciones):
            if pertenece(path, s):
                return (i, path)
        return (len(secciones), path)
    return sorted(archivos, key=clave)


def candidatos(archivos, seccion, secciones):
    """Archivos del grupo fuera del template cuyo nombre se parece a la sección."""
    tokens = {
        t for t in re.split(r"[^a-z0-9ñ]+", Path(seccion.rstrip("/")).stem.lower())
        if len(t) >= 3 and t not in PALABRAS_GENERICAS
    }
    return [
        a for a in archivos
        if not any(pertenece(a, s) for s in secciones) and any(t in a.lower() for t in tokens)
    ]


def ultimos_cambios(repo):
    """{archivo: fecha ISO del último commit en main que lo tocó}, con un solo git log."""
    salida = git(["-c", "core.quotepath=false", "log", "main", "--format=@@%cI", "--name-only"], repo)
    cambios, fecha = {}, None
    for linea in salida.splitlines():
        if linea.startswith("@@"):
            fecha = linea[2:]
        elif linea and fecha:
            cambios.setdefault(linea, fecha)
    return cambios


def ultimo_borrador(materia, gid):
    """Fecha del último borrador y cuándo se creó (primer commit en sistema-eidas-datos)."""
    carpeta = DATOS_DIR / materia / "borradores" / gid
    if not carpeta.exists():
        return None
    fechas = sorted(m.group(1) for f in carpeta.iterdir() if (m := FECHA_RE.match(f.name)))
    if not fechas:
        return None
    rel = f"{materia}/borradores/{gid}/{fechas[-1]}.md"
    creado = git(["log", "--diff-filter=A", "--format=%cI", "--", rel], DATOS_DIR).splitlines()
    return {"fecha": fechas[-1], "desde": creado[-1] if creado else f"{fechas[-1]}T00:00:00-03:00"}


def cambio_desde(fecha_archivo, borrador):
    if not fecha_archivo or not borrador:
        return False
    return datetime.fromisoformat(fecha_archivo) > datetime.fromisoformat(borrador["desde"])


def fecha_corta(iso):
    return datetime.fromisoformat(iso).strftime("%d/%m %H:%M") if iso else "—"


def repo_web(repo_url):
    return (repo_url[:-4] if repo_url.endswith(".git") else repo_url).rstrip("/")


def url_github(repo_url, path, carpeta=False):
    return f"{repo_web(repo_url)}/{'tree' if carpeta else 'blob'}/main/{q(path)}"


def repo_de(materia, gid):
    grupo = next((g for g in grupos_de(materia) if g["id"] == gid), None)
    if grupo is None:
        abort(404)
    return grupo, MATERIAS_DIR / materia / "grupos" / gid


def archivo_seguro(materia, gid, path):
    _, repo = repo_de(materia, gid)
    base = repo.resolve()
    full = (base / path).resolve()
    if not full.is_relative_to(base) or not full.is_file():
        abort(404)
    return full


def plantuml_prendido():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.2)
        return s.connect_ex(("127.0.0.1", 8090)) == 0


def visor_pdf(src):
    """Lo dibuja PDF.js (ver VISOR_PDF_JS) página por página; si no carga, queda el iframe."""
    return (
        f'<div class="pdf-visor" data-src="{src}">'
        f'<div class="pdf-barra"><span class="pdf-info">Cargando PDF…</span>'
        f'<button type="button" data-zoom="-1">−</button><button type="button" data-zoom="1">+</button>'
        f'<a href="{src}" target="_blank">abrir en otra pestaña ↗</a></div>'
        f'<div class="pdf-paginas"></div></div>'
    )


SEPARADOR_TABLA_RE = re.compile(r"^\s*\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)*\|?\s*$")


def avisos_markdown(texto):
    """Errores de forma que GitHub tampoco muestra bien: se renderiza igual que GitHub y se avisa."""
    avisos = []
    lineas = texto.splitlines()
    en_codigo = False
    for n, linea in enumerate(lineas):
        if linea.lstrip().startswith("```"):
            en_codigo = not en_codigo
        if en_codigo or not re.match(r"^\s*\|.*\|\s*$", linea):
            continue
        anterior = lineas[n - 1] if n > 0 else ""
        siguiente = lineas[n + 1] if n + 1 < len(lineas) else ""
        # Primera fila de un bloque de tabla sin la fila |---| debajo
        if not re.match(r"^\s*\|", anterior) and not SEPARADOR_TABLA_RE.match(siguiente):
            avisos.append(
                f"Línea {n + 1}: tabla sin la fila separadora (<code>|---|---|</code>) debajo del "
                "encabezado. GitHub tampoco la muestra como tabla."
            )
    return "".join(f'<p class="aviso">{a}</p>' for a in avisos)


def render_archivo(materia, gid, path, repo_url, cambios, borrador):
    full = archivo_seguro(materia, gid, path)
    ext = full.suffix.lower()
    raw = f"/raw/{materia}/{gid}/{q(path)}"
    nuevo = cambio_desde(cambios.get(path), borrador)
    marca = ' <span class="nuevo">cambió después del borrador</span>' if nuevo else ""
    cabecera = (
        f'<div class="archivo-cab"><code>{html.escape(path)}</code>'
        f'<span class="meta">último cambio {fecha_corta(cambios.get(path))}{marca}</span>'
        f'<a href="{url_github(repo_url, path)}" target="_blank">GitHub ↗</a></div>'
    )

    if ext == ".md":
        texto = full.read_text(errors="replace")
        # Las rutas relativas (imágenes) se resuelven contra la carpeta del archivo
        carpeta = q(str(Path(path).parent)) if Path(path).parent != Path(".") else ""
        base = f"/raw/{materia}/{gid}/{carpeta}/" if carpeta else f"/raw/{materia}/{gid}/"
        cuerpo = mdlib.markdown(texto, extensions=["tables", "fenced_code", "sane_lists"])
        cuerpo = re.sub(
            r'(<img[^>]*\ssrc=")(?!https?:|/|data:)([^"]+)"',
            lambda m: f'{m.group(1)}{base}{m.group(2)}"', cuerpo,
        )
        # Links a un PDF del repo: se puede desplegar el visor ahí mismo
        def pdf_inline(m):
            destino = posixpath.normpath(posixpath.join(str(Path(path).parent), urllib.parse.unquote(m.group(2))))
            src = f"/raw/{materia}/{gid}/{q(destino)}"
            return (f'{m.group(0)} <details class="pdf-inline"><summary>ver acá</summary>'
                    f'{visor_pdf(src)}</details>')
        cuerpo = re.sub(r'(<a href=")(?!https?:|/|#)([^"]+\.pdf)">.*?</a>', pdf_inline, cuerpo, flags=re.I)
        contenido = avisos_markdown(texto) + f'<div class="md">{cuerpo}</div>'
    elif ext in PUML_EXT:
        aviso = "" if plantuml_prendido() else (
            '<p class="aviso">PlantUML local apagado: <code>cd infra/plantuml &amp;&amp; '
            "docker compose up -d</code> y recargá.</p>"
        )
        fuente = html.escape(full.read_text(errors="replace"))
        contenido = (
            f'{aviso}<img class="diagrama" src="/puml/{materia}/{gid}/{q(path)}">'
            f"<details><summary>Fuente</summary><pre>{fuente}</pre></details>"
        )
    elif ext in IMAGEN_EXT:
        contenido = f'<img class="diagrama" src="{raw}">'
    elif ext == ".pdf":
        contenido = visor_pdf(raw)
    else:
        datos = full.read_bytes()
        if b"\0" in datos[:4096]:
            contenido = f'<p>Archivo binario. <a href="{raw}">Descargar</a></p>'
        else:
            contenido = f"<pre>{html.escape(datos.decode(errors='replace'))}</pre>"
    return f'<article class="archivo">{cabecera}{contenido}</article>'


RECORRER_CSS = """
  body.ancho { max-width: 1500px; }
  .layout { display: grid; grid-template-columns: 270px 1fr; gap: 1.5rem; align-items: start; }
  .lateral { position: sticky; top: 1rem; max-height: 92vh; overflow-y: auto; font-size: 0.85rem; }
  .lateral a { display: block; padding: 0.2rem 0.4rem; border-radius: 4px; color: #374151; text-decoration: none; word-break: break-all; }
  .lateral a.activo { background: #1f2937; color: white; }
  .lateral a.falta { color: #9ca3af; }
  .lateral .grupo-sep { margin-top: 0.6rem; color: #9ca3af; font-size: 0.75rem; text-transform: uppercase; }
  .punto { display: inline-block; width: 7px; height: 7px; border-radius: 50%; background: #d97706; margin-left: 4px; vertical-align: middle; }
  .botones { display: flex; flex-wrap: wrap; gap: 0.5rem; margin: 0.75rem 0 1rem; align-items: center; }
  .botones a { font-size: 0.9rem; padding: 0.35rem 0.8rem; border-radius: 6px; border: 1px solid #d1d5db; color: #1f2937; text-decoration: none; background: white; }
  .botones a.principal { background: #1f2937; color: white; border-color: #1f2937; }
  .botones .atajos { color: #9ca3af; font-size: 0.8rem; margin-left: auto; }
  .cab { display: flex; flex-wrap: wrap; gap: 0.5rem 1.5rem; align-items: baseline; }
  .cab h2 { border: none; margin: 0; }
  .cab .meta, .archivo-cab .meta { color: #6b7280; font-size: 0.85rem; }
  .archivo { border: 1px solid #e5e7eb; border-radius: 8px; padding: 1rem 1.25rem; margin-bottom: 1.5rem; overflow-x: auto; }
  .archivo-cab { display: flex; flex-wrap: wrap; gap: 0.4rem 1rem; align-items: baseline; border-bottom: 1px solid #e5e7eb; padding-bottom: 0.5rem; margin-bottom: 0.75rem; }
  .nuevo { background: #fef3c7; color: #92400e; padding: 0.05rem 0.45rem; border-radius: 999px; font-size: 0.8rem; }
  .md { line-height: 1.55; }
  .md img, img.diagrama { max-width: 100%; }
  .md table { font-size: 0.9rem; }
  .md pre, .archivo pre { background: #f3f4f6; padding: 0.75rem; overflow-x: auto; font-size: 0.85rem; }
  iframe.pdf { width: 100%; height: 85vh; border: none; }
  .pdf-visor { background: #e5e7eb; border-radius: 6px; padding: 0.5rem; margin: 0.5rem 0; }
  .pdf-barra { display: flex; gap: 0.5rem; align-items: center; font-size: 0.85rem; color: #4b5563; margin-bottom: 0.5rem; }
  .pdf-barra button { width: 2rem; border: 1px solid #d1d5db; background: white; border-radius: 4px; cursor: pointer; }
  .pdf-barra a { margin-left: auto; }
  .pdf-paginas { max-height: 85vh; overflow: auto; text-align: center; }
  .pdf-paginas canvas { display: block; margin: 0 auto 0.5rem; box-shadow: 0 1px 3px rgba(0,0,0,.25); background: white; }
  details.pdf-inline { display: inline; }
  details.pdf-inline[open] { display: block; }
  details.pdf-inline summary { display: inline; cursor: pointer; color: #2563eb; font-size: 0.85rem; }
  .aviso { background: #fef3c7; color: #92400e; padding: 0.5rem 0.9rem; border-radius: 6px; }
  .falta-box { color: #6b7280; }
  .form-sync { display: inline; }
  .form-sync button { font-size: 0.85rem; padding: 0.3rem 0.75rem; border-radius: 6px; border: 1px solid #d1d5db; background: white; cursor: pointer; }
  .form-sync button:disabled { color: #9ca3af; cursor: wait; }
  .banner-sync { padding: 0.5rem 0.9rem; border-radius: 6px; font-size: 0.9rem; }
  .columnas { display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; }
  .columnas a { display: block; padding: 0.25rem 0; }
"""

ATAJOS_JS = """
<script>
document.addEventListener('keydown', e => {
  if (e.target.closest('input, textarea') || e.ctrlKey || e.metaKey || e.altKey) return;
  const a = document.querySelector(`[data-key="${(e.shiftKey ? 'S' : '') + e.key}"]`);
  if (a) { e.preventDefault(); location.href = a.href; }
});
</script>"""


PDFJS = "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174"

# Cada .pdf-visor se carga recién cuando se ve (los PDF de wireframes pueden ser muchos)
VISOR_PDF_JS = f"""
<script src="{PDFJS}/pdf.min.js"></script>
<script>
(() => {{
  const visores = document.querySelectorAll('.pdf-visor');
  if (!visores.length) return;
  if (!window.pdfjsLib) {{
    visores.forEach(v => {{
      v.querySelector('.pdf-paginas').innerHTML = `<iframe class="pdf" src="${{v.dataset.src}}"></iframe>`;
      v.querySelector('.pdf-info').textContent = 'Visor del navegador (sin conexión a cdnjs)';
    }});
    return;
  }}
  pdfjsLib.GlobalWorkerOptions.workerSrc = '{PDFJS}/pdf.worker.min.js';

  async function dibujar(v) {{
    const cont = v.querySelector('.pdf-paginas');
    const ancho = (cont.clientWidth || 800) - 20;
    cont.innerHTML = '';
    for (let n = 1; n <= v.pdf.numPages; n++) {{
      const pagina = await v.pdf.getPage(n);
      const base = pagina.getViewport({{ scale: 1 }});
      const escala = (ancho / base.width) * v.zoom;
      const vista = pagina.getViewport({{ scale: escala * devicePixelRatio }});
      const canvas = document.createElement('canvas');
      canvas.width = vista.width;
      canvas.height = vista.height;
      canvas.style.width = (vista.width / devicePixelRatio) + 'px';
      cont.appendChild(canvas);
      await pagina.render({{ canvasContext: canvas.getContext('2d'), viewport: vista }}).promise;
    }}
  }}

  async function cargar(v) {{
    v.zoom = 1;
    try {{
      v.pdf = await pdfjsLib.getDocument(v.dataset.src).promise;
      const n = v.pdf.numPages;
      v.querySelector('.pdf-info').textContent = n + (n === 1 ? ' página' : ' páginas');
      await dibujar(v);
    }} catch (e) {{
      v.querySelector('.pdf-info').textContent = 'No se pudo leer con PDF.js: se muestra con el visor del navegador';
      v.querySelector('.pdf-paginas').innerHTML = `<iframe class="pdf" src="${{v.dataset.src}}"></iframe>`;
    }}
  }}

  const obs = new IntersectionObserver(entradas => entradas.forEach(e => {{
    if (e.isIntersecting) {{ obs.unobserve(e.target); cargar(e.target); }}
  }}), {{ rootMargin: '300px' }});
  visores.forEach(v => {{
    obs.observe(v);
    v.querySelectorAll('[data-zoom]').forEach(b => b.addEventListener('click', () => {{
      if (!v.pdf) return;
      v.zoom = Math.min(3, Math.max(0.4, v.zoom * (b.dataset.zoom === '1' ? 1.25 : 0.8)));
      dibujar(v);
    }}));
  }});
}})();
</script>"""


def pagina_recorrer(titulo, cuerpo):
    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>{html.escape(titulo)} — Recorrer EIDAS</title>
<style>{BASE_CSS}{RECORRER_CSS}</style>
</head>
<body class="ancho">
  <h1>Recorrer repos</h1>
  {render_nav("/recorrer")}
  {cuerpo}
  {ATAJOS_JS}
  {VISOR_PDF_JS}
</body>
</html>"""


def boton(href, texto, key=None, principal=False):
    if not href:
        return ""
    atributos = f' data-key="{key}"' if key else ""
    clase = ' class="principal"' if principal else ""
    return f'<a href="{href}"{atributos}{clase}>{texto}</a>'


def tabs_materias(actual):
    return '<div class="tabs-materia">' + "".join(
        f'<a href="/recorrer/{m}" class="{"activo" if m == actual else ""}">{m}</a>'
        for m in materias_con_grupos()
    ) + "</div>"


@app.route("/recorrer")
def recorrer_index():
    materias = materias_con_grupos()
    if not materias:
        abort(404)
    return redirect(f"/recorrer/{materias[0]}")


@app.route("/recorrer/<materia>")
def recorrer_materia(materia):
    grupos = grupos_de(materia)
    if not grupos:
        abort(404)
    secciones = secciones_de(materia)
    por_grupo = "".join(
        f'<a href="/recorrer/{materia}/grupo/{q(g["id"])}">{html.escape(g["id"])}</a>' for g in grupos
    )
    por_seccion = "".join(
        f'<a href="/recorrer/{materia}/seccion/{i}"><code>{html.escape(s)}</code></a>'
        for i, s in enumerate(secciones)
    )
    cuerpo = f"""
    {tabs_materias(materia)}
    <p class="subtitulo">Lee los clones locales. "↻ actualizar" hace lo mismo que <code>/sync</code>: pull de
    <code>main</code>, sin tocar un clon que esté en otra branch o con cambios sin commitear.
    Un punto naranja marca los archivos que cambiaron después del último borrador del grupo.</p>
    <div class="botones">{form_actualizar(f"/actualizar/{materia}", "↻ actualizar todos los grupos")}</div>
    {banner_sync()}
    <div class="columnas">
      <div><h2>Por grupo</h2><p class="resumen">Todos los archivos de un grupo, en el orden del template.</p>{por_grupo}</div>
      <div><h2>Por sección</h2><p class="resumen">El mismo archivo en todos los grupos, uno detrás del otro.</p>{por_seccion}</div>
    </div>"""
    return Response(pagina_recorrer(materia, cuerpo), mimetype="text/html")


def info_borrador(borrador):
    if not borrador:
        return "sin borradores"
    return f"último borrador {borrador['fecha']} (creado {fecha_corta(borrador['desde'])})"


@app.route("/recorrer/<materia>/grupo/<gid>")
def recorrer_grupo(materia, gid):
    grupo, repo = repo_de(materia, gid)
    grupos = grupos_de(materia)
    ids = [g["id"] for g in grupos]
    i = ids.index(gid)
    secciones = secciones_de(materia)
    if not repo.exists():
        cuerpo = (f"{tabs_materias(materia)}{banner_sync()}<p>El grupo <b>{html.escape(gid)}</b> no está clonado.</p>"
                  + form_actualizar(f"/actualizar/{materia}/{q(gid)}", "↻ clonar"))
        return Response(pagina_recorrer(gid, cuerpo), mimetype="text/html")

    archivos = orden_archivos(ls_files(repo), secciones)
    cambios = ultimos_cambios(repo)
    borrador = ultimo_borrador(materia, gid)
    actual = request.args.get("f") or (archivos[0] if archivos else None)
    if actual not in archivos:
        actual = archivos[0] if archivos else None
    j = archivos.index(actual) if actual else 0

    def href_archivo(path):
        return f"/recorrer/{materia}/grupo/{q(gid)}?f={q(path)}"

    def href_grupo(otro):
        # Al cambiar de grupo, intentar quedarse en el mismo archivo
        return f"/recorrer/{materia}/grupo/{q(otro)}" + (f"?f={q(actual)}" if actual else "")

    lateral, seccion_previa = "", None
    for path in archivos:
        sec = next((s for s in secciones if pertenece(path, s)), None)
        if sec is None and seccion_previa != "otros":
            lateral += '<div class="grupo-sep">fuera del template</div>'
            seccion_previa = "otros"
        punto = '<span class="punto" title="cambió después del borrador"></span>' if cambio_desde(cambios.get(path), borrador) else ""
        lateral += f'<a href="{href_archivo(path)}" class="{"activo" if path == actual else ""}">{html.escape(path)}{punto}</a>'

    botones = "".join([
        boton(href_archivo(archivos[j - 1]) if actual and j > 0 else None, "← archivo", "ArrowLeft"),
        boton(href_archivo(archivos[j + 1]) if actual and j + 1 < len(archivos) else None, "archivo →", "ArrowRight", True),
        boton(href_grupo(ids[i - 1]) if i > 0 else None, "⇐ grupo", "SArrowLeft"),
        boton(href_grupo(ids[i + 1]) if i + 1 < len(ids) else None, "grupo ⇒", "SArrowRight"),
        '<span class="atajos">← → archivo · Shift + ← → grupo</span>',
    ])
    contenido = render_archivo(materia, gid, actual, grupo["repo"], cambios, borrador) if actual else "<p>El repo no tiene archivos.</p>"
    cuerpo = f"""
    {tabs_materias(materia)}
    <div class="cab"><h2>{html.escape(gid)}</h2>
      <span class="meta">grupo {i + 1} de {len(ids)} · archivo {j + 1} de {len(archivos)} · {info_borrador(borrador)}</span>
      <a href="{repo_web(grupo['repo'])}" target="_blank">repo ↗</a>
      {form_actualizar(f"/actualizar/{materia}/{q(gid)}", "↻ actualizar")}</div>
    {banner_sync()}
    <div class="botones">{botones}</div>
    <div class="layout"><nav class="lateral">{lateral}</nav><main>{contenido}</main></div>"""
    return Response(pagina_recorrer(f"{gid} — {actual}", cuerpo), mimetype="text/html")


@app.route("/recorrer/<materia>/seccion/<int:n>")
def recorrer_seccion(materia, n):
    grupos = grupos_de(materia)
    secciones = secciones_de(materia)
    if not grupos or not 0 <= n < len(secciones):
        abort(404)
    seccion = secciones[n]
    ids = [g["id"] for g in grupos]
    gid = request.args.get("g") if request.args.get("g") in ids else ids[0]
    i = ids.index(gid)
    grupo = grupos[i]
    repo = MATERIAS_DIR / materia / "grupos" / gid

    def href(sec, otro):
        return f"/recorrer/{materia}/seccion/{sec}?g={q(otro)}"

    # Lateral: qué grupos tienen la sección y si cambió desde su último borrador
    lateral = ""
    for otro in ids:
        repo_otro = MATERIAS_DIR / materia / "grupos" / otro
        tiene = repo_otro.exists() and any(pertenece(a, seccion) for a in ls_files(repo_otro))
        punto = ""
        if tiene:
            cambios_otro = ultimos_cambios(repo_otro)
            borrador_otro = ultimo_borrador(materia, otro)
            if any(cambio_desde(f, borrador_otro) for a, f in cambios_otro.items() if pertenece(a, seccion)):
                punto = '<span class="punto" title="cambió después del borrador"></span>'
        clase = "activo" if otro == gid else ("" if tiene else "falta")
        lateral += f'<a href="{href(n, otro)}" class="{clase}">{html.escape(otro)}{punto}</a>'

    if not repo.exists():
        contenido = f"<p>No está clonado. Corré <code>/sync {materia}</code>.</p>"
    else:
        archivos = orden_archivos(ls_files(repo), secciones)
        cambios = ultimos_cambios(repo)
        borrador = ultimo_borrador(materia, gid)
        propios = [a for a in archivos if pertenece(a, seccion)]
        if propios:
            contenido = "".join(render_archivo(materia, gid, a, grupo["repo"], cambios, borrador) for a in propios)
        else:
            # Contenido pertinente fuera de la ruta del template: se muestra igual
            parecidos = candidatos(archivos, seccion, secciones)
            contenido = f'<div class="falta-box"><p>Este grupo no tiene <code>{html.escape(seccion)}</code>.'
            if parecidos:
                contenido += " Se muestra lo que tiene fuera del template con un nombre parecido:</p></div>"
                contenido += "".join(render_archivo(materia, gid, a, grupo["repo"], cambios, borrador) for a in parecidos[:3])
            else:
                contenido += "</p></div>"

    # Al terminar los grupos, "grupo ⇒" sigue con la próxima sección
    siguiente = href(n, ids[i + 1]) if i + 1 < len(ids) else (href(n + 1, ids[0]) if n + 1 < len(secciones) else None)
    anterior = href(n, ids[i - 1]) if i > 0 else (href(n - 1, ids[-1]) if n > 0 else None)
    botones = "".join([
        boton(anterior, "← grupo", "ArrowLeft"),
        boton(siguiente, "grupo →", "ArrowRight", True),
        boton(href(n - 1, gid) if n > 0 else None, "⇐ sección", "SArrowLeft"),
        boton(href(n + 1, gid) if n + 1 < len(secciones) else None, "sección ⇒", "SArrowRight"),
        '<span class="atajos">← → grupo · Shift + ← → sección</span>',
    ])
    opciones = "".join(
        f'<option value="{k}"{" selected" if k == n else ""}>{html.escape(s)}</option>' for k, s in enumerate(secciones)
    )
    selector = (
        f'<select onchange="location.href=\'/recorrer/{materia}/seccion/\'+this.value+\'?g={q(gid)}\'">{opciones}</select>'
    )
    cuerpo = f"""
    {tabs_materias(materia)}
    <div class="cab"><h2><code>{html.escape(seccion)}</code></h2> {selector}
      <span class="meta">sección {n + 1} de {len(secciones)} · <b>{html.escape(gid)}</b> (grupo {i + 1} de {len(ids)})</span>
      {form_actualizar(f"/actualizar/{materia}/{q(gid)}", f"↻ actualizar {html.escape(gid)}")}</div>
    {banner_sync()}
    <div class="botones">{botones}</div>
    <div class="layout"><nav class="lateral">{lateral}</nav><main>{contenido}</main></div>"""
    return Response(pagina_recorrer(f"{seccion} — {gid}", cuerpo), mimetype="text/html")


def volver_aca():
    """La URL actual sin el resultado del último actualizar, para volver después del POST."""
    args = {k: v for k, v in request.args.items() if k not in ("sync", "sync_msg")}
    return request.path + (f"?{urllib.parse.urlencode(args)}" if args else "")


def form_actualizar(accion, texto):
    # POST y no link: que no se dispare solo navegando con las flechas
    return (
        f'<form method="post" action="{accion}" class="form-sync" '
        """onsubmit="const b=this.querySelector('button');b.disabled=true;b.textContent='actualizando…'">"""
        f'<input type="hidden" name="volver" value="{html.escape(volver_aca())}">'
        f'<button type="submit">{texto}</button></form>'
    )


SYNC_COLORES = {"ok": ("#dcfce7", "#166534"), "aviso": ("#fef3c7", "#92400e"), "error": ("#fee2e2", "#991b1b")}


def banner_sync():
    nivel = request.args.get("sync")
    if nivel not in SYNC_COLORES:
        return ""
    fondo, color = SYNC_COLORES[nivel]
    lineas = html.escape(request.args.get("sync_msg", "")).replace("\n", "<br>")
    return f'<p class="banner-sync" style="background:{fondo};color:{color}">{lineas}</p>'


def redirigir_con(resultados):
    """resultados: [(grupo_id, estado, detalle)] → vuelve a la página con el resumen."""
    if any(e == "error" for _, e, _ in resultados):
        nivel = "error"
    elif any(e == "salteado" for _, e, _ in resultados):
        nivel = "aviso"
    else:
        nivel = "ok"
    msg = "\n".join(f"{gid}: {detalle}" for gid, _, detalle in resultados)
    volver = request.form.get("volver", "/recorrer")
    if not volver.startswith("/recorrer"):
        volver = "/recorrer"
    sep = "&" if "?" in volver else "?"
    return redirect(volver + sep + urllib.parse.urlencode({"sync": nivel, "sync_msg": msg}))


@app.route("/actualizar/<materia>/<gid>", methods=["POST"])
def actualizar_grupo(materia, gid):
    grupo, _ = repo_de(materia, gid)
    estado, detalle = grupos_py.sync_grupo(materia, gid, grupo["repo"])
    return redirigir_con([(gid, estado, detalle)])


@app.route("/actualizar/<materia>", methods=["POST"])
def actualizar_materia(materia):
    grupos = grupos_de(materia)
    if not grupos:
        abort(404)
    (MATERIAS_DIR / materia / "grupos").mkdir(exist_ok=True)
    return redirigir_con([(g["id"], *grupos_py.sync_grupo(materia, g["id"], g["repo"])) for g in grupos])


@app.route("/raw/<materia>/<gid>/<path:path>")
def recorrer_raw(materia, gid, path):
    full = archivo_seguro(materia, gid, path)
    tipo = mimetypes.guess_type(full.name)[0] or "application/octet-stream"
    if tipo.startswith("text/") or full.suffix.lower() in {".md", ".puml"}:
        tipo = "text/plain; charset=utf-8"
    return Response(full.read_bytes(), mimetype=tipo)


@app.route("/puml/<materia>/<gid>/<path:path>")
def recorrer_puml(materia, gid, path):
    full = archivo_seguro(materia, gid, path)
    pedido = urllib.request.Request(
        PLANTUML_URL, data=full.read_bytes(), method="POST",
        headers={"Content-Type": "text/plain; charset=utf-8"},
    )
    try:
        with urllib.request.urlopen(pedido, timeout=20) as r:
            return Response(r.read(), mimetype="image/svg+xml")
    except urllib.error.HTTPError as e:
        # Con errores de sintaxis PlantUML igual devuelve un SVG con el error dibujado
        return Response(e.read(), mimetype="image/svg+xml")
    except (urllib.error.URLError, TimeoutError):
        svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="520" height="40">'
               '<text x="8" y="25" font-family="sans-serif" font-size="14">PlantUML local apagado '
               '(infra/plantuml: docker compose up -d)</text></svg>')
        return Response(svg, mimetype="image/svg+xml")


# ---------------------------------------------------------------------------
# Notas: cuestionario individual (Classroom + Forms) + repo grupal, por alumno.
# Muestra el CSV que deja scripts/notas.py; el botón lo vuelve a traer por API (solo lectura).
# ---------------------------------------------------------------------------

ESTADO_NOTA_COLORES = {
    "corregido y devuelto en Classroom": "#16a34a",
    "corregido, falta devolver en Classroom": "#2563eb",
    "corregido en Forms, falta importar a Classroom": "#2563eb",
    "falta corregir": "#d97706",
    "no respondió": "#9ca3af",
}


def materias_con_notas():
    return [m for m in materias_con_grupos() if (DATOS_DIR / m / "classroom.json").exists()]


def pagina_notas(materia, cuerpo):
    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>Notas — {html.escape(materia or "")}</title>
<style>{BASE_CSS}{RECORRER_CSS}
  table.notas td, table.notas th {{ padding: 0.35rem 0.5rem; font-size: 0.85rem; }}
  table.notas td.num {{ text-align: right; font-variant-numeric: tabular-nums; }}
  .chips {{ display: flex; flex-wrap: wrap; gap: 0.5rem; margin: 0.5rem 0 1rem; }}
  .chips a {{ text-decoration: none; }}
</style>
</head>
<body class="ancho">
  <h1>Notas</h1>
  {render_nav("/notas")}
  {cuerpo}
</body>
</html>"""


@app.route("/notas")
def notas_index():
    materias = materias_con_notas()
    if not materias:
        return Response(pagina_notas(None, "<p>Ninguna materia tiene <code>classroom.json</code> en sistema-eidas-datos.</p>"), mimetype="text/html")
    return redirect(f"/notas/{materias[0]}")


@app.route("/notas/<materia>")
def notas_materia(materia):
    import notas as notas_py  # perezoso: si faltan las librerías de Google, el resto del dashboard anda igual
    if materia not in materias_con_notas():
        abort(404)
    tabs = '<div class="tabs-materia">' + "".join(
        f'<a href="/notas/{m}" class="{"activo" if m == materia else ""}">{m}</a>' for m in materias_con_notas()
    ) + "</div>"
    filas = notas_py.leer(materia)
    cfg = notas_py.config(materia)
    path = notas_py.csv_path(materia)
    boton = form_actualizar(f"/notas/{materia}/actualizar", "↻ traer de Classroom y Forms")
    if filas is None:
        cuerpo = f"{tabs}{banner_sync()}<p>Todavía no hay tabla para esta materia.</p>{boton}"
        return Response(pagina_notas(materia, cuerpo), mimetype="text/html")

    filtro = request.args.get("estado")
    conteo = {}
    for f in filas:
        conteo[f["Estado del cuestionario"]] = conteo.get(f["Estado del cuestionario"], 0) + 1
    chips = '<div class="chips">' + f'<a href="/notas/{materia}"><span class="badge" style="background:#1f2937">todos: {len(filas)}</span></a>' + "".join(
        f'<a href="/notas/{materia}?estado={urllib.parse.quote(e)}"><span class="badge" style="background:{ESTADO_NOTA_COLORES.get(e, "#6b7280")}">{html.escape(e)}: {n}</span></a>'
        for e, n in conteo.items()
    ) + "</div>"

    def celda(v, num=False):
        return f'<td class="num">{html.escape(v)}</td>' if num else f"<td>{html.escape(v)}</td>"

    cuerpo_tabla = ""
    for f in filas:
        if filtro and f["Estado del cuestionario"] != filtro:
            continue
        grupo = f["Grupo"]
        enlace = f'<a href="/recorrer/{materia}/grupo/{q(grupo)}">{html.escape(grupo)}</a>' if grupo else '<span class="falta-box">sin grupo</span>'
        color = ESTADO_NOTA_COLORES.get(f["Estado del cuestionario"], "#6b7280")
        cuerpo_tabla += (
            "<tr>" + celda(f["Alumno"]) + f"<td>{enlace}</td>"
            + celda(f["Cuestionario (/100)"], True) + celda(f["Cuestionario (/30)"], True)
            + celda(f["Repo grupal (/70)"], True) + celda(f["Repo: devolución"])
            + f'<td class="num"><b>{html.escape(f["Total (/100)"])}</b></td>'
            + f'<td><span class="badge" style="background:{color}">{html.escape(f["Estado del cuestionario"])}</span></td></tr>'
        )
    actualizado = datetime.fromtimestamp(path.stat().st_mtime).strftime("%d/%m %H:%M")
    cuerpo = f"""
    {tabs}
    <p class="subtitulo">Cuestionario <b>{html.escape(cfg.get("nombre_cuestionario", ""))}</b> (Classroom + Forms, /30) más
    la última devolución del repo (/70). Tabla del {actualizado}, en
    <code>sistema-eidas-datos/{materia}/{path.name}</code>. Solo lectura: el botón vuelve a leer Classroom y Forms.</p>
    <div class="botones">{boton}</div>
    {banner_sync()}
    {chips}
    <table class="notas">
      <thead><tr><th>Alumno</th><th>Grupo</th><th>Cuest. /100</th><th>Cuest. /30</th><th>Repo /70</th><th>Devolución</th><th>Total</th><th>Estado</th></tr></thead>
      <tbody>{cuerpo_tabla}</tbody>
    </table>"""
    return Response(pagina_notas(materia, cuerpo), mimetype="text/html")


@app.route("/notas/<materia>/actualizar", methods=["POST"])
def notas_actualizar(materia):
    import notas as notas_py
    if materia not in materias_con_notas():
        abort(404)
    volver = f"/notas/{materia}"
    try:
        filas = notas_py.notas_cierre(materia)
        notas_py.guardar(materia, filas)
        nivel, msg = "ok", f"Tabla actualizada desde Classroom y Forms: {len(filas)} alumnos."
    except Exception as e:  # token vencido, sin red, API caída: que se vea en la página
        nivel, msg = "error", f"No se pudo leer Classroom/Forms: {e}"
    return redirect(volver + "?" + urllib.parse.urlencode({"sync": nivel, "sync_msg": msg}))


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

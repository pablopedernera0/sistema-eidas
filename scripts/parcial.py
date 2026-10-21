#!/usr/bin/env python3
"""Corrección del parcial B (cuestionario impreso por grupo) desde el celular.

A diferencia de dashboard.py, este SÍ escucha en la red (0.0.0.0) para que el docente entre
desde el celular a la IP de la notebook; por eso pide un PIN y no expone nada más que esto.

Flujo: elegir comisión → grupo → estudiante, sacar foto de las 2 carillas, el motor (`claude`
de la terminal) lee las marcas y propone el puntaje de la abierta en segundo plano; el
docente revisa al lado de la foto, corrige si hace falta y confirma. Queda una vista para
mostrarle al estudiante y una tabla/CSV por comisión.

  python3 scripts/parcial.py [--puerto 8421]      (PIN: variable PARCIAL_PIN o uno al azar)

Bancos y clave: sistema-eidas-datos/cuestionarios/parcial-b-2c-2026/ (se usa su generar.py
para que las letras sean las mismas que las impresas). Fotos y resultados quedan en
respuestas/<com>/<grupo>/<estudiante>/ dentro de esa carpeta.
"""
import csv
import hashlib
import html
import importlib.util
import io
import json
import os
import random
import re
import secrets
import subprocess
import sys
import threading
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

from flask import Flask, Response, abort, redirect, request, send_file

ROOT = Path(__file__).resolve().parent.parent
MATERIAS_DIR = ROOT / "materias"
PARCIAL_DIR = ROOT.parent / "sistema-eidas-datos" / "cuestionarios" / "parcial-b-2c-2026"
RESP_DIR = PARCIAL_DIR / "respuestas"
COMISIONES = {"c31": "af-diseno-sistemas-web-31", "c32": "af-diseno-sistemas-web-32"}
ETIQUETAS = {"c31": "3.° 1.ª", "c32": "3.° 2.ª"}
PIN = os.environ.get("PARCIAL_PIN") or f"{random.randint(0, 9999):04d}"
COOKIE = "parcial_pin"
LETRAS = "abcdefgh"

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 60 * 1024 * 1024
motor = ThreadPoolExecutor(max_workers=3)
candado = threading.Lock()

_spec = importlib.util.spec_from_file_location("generar_parcial", PARCIAL_DIR / "generar.py")
generar = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(generar)


# ---------- datos ----------

def normalizar(texto):
    return "".join(c for c in unicodedata.normalize("NFD", texto.lower()) if unicodedata.category(c) != "Mn")


def slug(texto):
    return re.sub(r"[^a-z0-9]+", "-", normalizar(texto)).strip("-")


def banco(com, gid):
    """(meta, preguntas) con las opciones en el mismo orden que el PDF impreso."""
    ruta = PARCIAL_DIR / "bancos" / f"{com}-{gid}.md"
    if not ruta.exists():
        abort(404)
    meta, preguntas = generar.leer_banco(ruta)
    generar.mezclar(meta, preguntas)
    return meta, preguntas


def grupos(com):
    return [r.name[len(com) + 1:-3] for r in sorted(PARCIAL_DIR.glob(f"bancos/{com}-*.md"), key=lambda r: r.name.lower())]


def leer_integrantes_md(texto):
    """['Apellido, Nombre'] desde integrantes.md. Solo cuentan las tablas cuyo encabezado tiene
    columnas Nombre + Apellido (la del template) o una columna Integrante ('Apellido, Nombre');
    el resto de las tablas del archivo se ignora. Si no hay ninguna, se usa una lista
    '- Nombre Apellido'."""
    nombres, viñetas = [], []
    columnas = None  # (i_nombre, i_apellido) o (i_integrante, None) de la tabla actual
    for linea in texto.splitlines():
        linea = linea.strip()
        if not linea.startswith("|"):
            columnas = None
            m = re.fullmatch(r"[-*]\s+([^\W\d_][\w.'\s-]*)", linea)
            if m and 2 <= len(m.group(1).split()) <= 4:
                partes = m.group(1).split()
                viñetas.append(f"{partes[-1]}, {' '.join(partes[:-1])}")
            continue
        celdas = [c.strip().strip("*").strip() for c in linea.strip("|").split("|")]
        if set("".join(celdas)) <= set("-: "):
            continue
        if columnas is None:
            enc = [normalizar(c) for c in celdas]
            if "nombre" in enc and "apellido" in enc:
                columnas = (enc.index("nombre"), enc.index("apellido"))
            elif "integrante" in enc:
                columnas = (enc.index("integrante"), None)
            else:
                columnas = False  # tabla que no es de integrantes
            continue
        if not columnas or len(celdas) <= max(i for i in columnas if i is not None):
            continue
        i, j = columnas
        nombre = celdas[i] if j is None else f"{celdas[j]}, {celdas[i]}"
        if nombre.strip(", "):
            nombres.append(nombre)
    return nombres or viñetas


def integrantes(com, gid):
    """[(slug, 'Apellido, Nombre')] desde integrantes.md, más los cargados a mano."""
    ruta = MATERIAS_DIR / COMISIONES[com] / "grupos" / gid / "integrantes.md"
    lista = []
    if ruta.exists():
        for nombre in leer_integrantes_md(ruta.read_text()):
            lista.append((slug(nombre), nombre))
    vistos = {s for s, _ in lista}
    carpeta = RESP_DIR / com / gid
    if carpeta.exists():
        for d in sorted(carpeta.iterdir()):
            est = leer_estado(com, gid, d.name)
            if d.name not in vistos and est.get("nombre"):
                lista.append((d.name, est["nombre"]))
    return sorted(lista, key=lambda x: normalizar(x[1]))


def carpeta(com, gid, sid):
    if com not in COMISIONES or not re.fullmatch(r"[a-z0-9-]+", sid) or gid not in grupos(com):
        abort(404)
    return RESP_DIR / com / gid / sid


def leer_estado(com, gid, sid):
    ruta = RESP_DIR / com / gid / sid / "estado.json"
    return json.loads(ruta.read_text()) if ruta.exists() else {}


def guardar_estado(com, gid, sid, cambios):
    with candado:
        d = RESP_DIR / com / gid / sid
        d.mkdir(parents=True, exist_ok=True)
        est = leer_estado(com, gid, sid)
        est.update(cambios)
        (d / "estado.json").write_text(json.dumps(est, ensure_ascii=False, indent=1))
        return est


def correcta(p):
    if p["tipo"] == "vf":
        return "V" if p["opciones"][0][1] else "F"
    return ",".join(LETRAS[i] for i, (_, c) in enumerate(p["opciones"]) if c)


def normal_resp(p, r):
    r = (r or "").strip()
    if p["tipo"] == "vf":
        r = r[:1].upper()
        return r if r in ("V", "F") else "?"
    letras = sorted(set(re.findall(r"[a-h]", r.lower())))
    if not letras:
        return "?"
    return ",".join(letras)


def puntuar(preguntas, respuestas, abierta_pts):
    total, detalle = 0, []
    for p in preguntas:
        if p["tipo"] == "abierta":
            pts = max(0, min(p["pts"], int(abierta_pts or 0)))
            detalle.append((p, None, None, pts))
        else:
            r = normal_resp(p, respuestas.get(str(p["n"])))
            ok = r == correcta(p)
            pts = p["pts"] if ok else 0
            detalle.append((p, r, ok, pts))
        total += pts
    return total, detalle


# ---------- motor ----------

ESQUEMA = {
    "type": "object",
    "properties": {
        "respuestas": {"type": "object", "additionalProperties": {"type": "string"},
                       "description": "pregunta (1..9) -> 'V'/'F', una letra, o letras separadas por coma; '?' si no se lee"},
        "dudosas": {"type": "array", "items": {"type": "integer"}},
        "abierta_transcripcion": {"type": "string"},
        "abierta_puntaje": {"type": "integer", "minimum": 0, "maximum": 3},
        "abierta_comentario": {"type": "string"},
        "nombre_escrito": {"type": "string"},
        "observaciones": {"type": "string"},
    },
    "required": ["respuestas", "dudosas", "abierta_transcripcion", "abierta_puntaje", "abierta_comentario"],
}


def prompt_motor(meta, preguntas, fotos):
    partes = []
    for p in preguntas:
        if p["tipo"] == "abierta":
            partes.append(f"{p['n']}. (ABIERTA) {p['texto']}\n   Criterio del docente: {p['se_espera']}")
        elif p["tipo"] == "vf":
            partes.append(f"{p['n']}. (V/F, círculos) {p['texto']}")
        else:
            como = "una sola, círculos" if p["tipo"] == "una" else "varias, cuadrados"
            ops = "\n".join(f"   {LETRAS[i]}) {t}" for i, (t, _) in enumerate(p["opciones"]))
            partes.append(f"{p['n']}. ({como}) {p['texto']}\n{ops}")
    lista = "\n".join(f"- {f}" for f in fotos)
    return f"""Corregís un cuestionario impreso que un estudiante completó a mano. Leé con Read estas fotos (carillas del examen):
{lista}

Grupo: {meta['grupo']}. Estas son las preguntas tal como están impresas (mismas letras):

{chr(10).join(partes)}

Para cada pregunta 1 a 9 informá SOLO lo que el estudiante marcó (no lo que sería correcto): "V" o "F"; una letra; o varias letras separadas por coma.
- Vale cualquier marca clara (cruz, tilde, círculo relleno o rodeado). Si tachó una y aclaró otra, vale la aclarada.
- Si no marcó nada, o no se puede leer con seguridad, poné "?" y agregá el número a "dudosas". Si dudás entre dos lecturas, poné la más probable y agregala a "dudosas".
Pregunta 10: transcribí lo que escribió, puntuala de 0 a 3 con el criterio del docente y escribí un comentario de 1 o 2 oraciones para el estudiante, en voseo rioplatense: qué estuvo bien y qué le faltó. Si está en blanco, 0 y decilo.
"nombre_escrito": el nombre que figura en la hoja, si se lee. "observaciones": algo raro de la foto (borrosa, falta una carilla, es de otro grupo), o vacío."""


def preparar_foto(origen, destino):
    from PIL import Image, ImageOps
    img = ImageOps.exif_transpose(Image.open(origen)).convert("RGB")
    img.thumbnail((2200, 2200))
    img.save(destino, "JPEG", quality=85)


def correr_motor(com, gid, sid):
    meta, preguntas = banco(com, gid)
    d = carpeta(com, gid, sid)
    fotos = [str(f) for f in sorted(d.glob("foto-*.jpg"))]
    try:
        r = subprocess.run(
            ["claude", "-p", prompt_motor(meta, preguntas, fotos), "--output-format", "json",
             "--json-schema", json.dumps(ESQUEMA), "--allowedTools", "Read", "--add-dir", str(d),
             "--no-session-persistence"],
            capture_output=True, text=True, timeout=300, cwd=d)
        salida = json.loads(r.stdout)
        det = salida.get("structured_output")
        if salida.get("is_error") or not det:
            raise RuntimeError(salida.get("result") or r.stderr[-500:])
    except Exception as ex:  # noqa: BLE001 — cualquier falla queda visible en la pantalla
        guardar_estado(com, gid, sid, {"estado": "error", "error": str(ex)[:800]})
        return
    respuestas = {str(p["n"]): normal_resp(p, det["respuestas"].get(str(p["n"])))
                  for p in preguntas if p["tipo"] != "abierta"}
    guardar_estado(com, gid, sid, {
        "estado": "revisar", "deteccion": det, "respuestas": respuestas,
        "abierta_pts": det.get("abierta_puntaje", 0), "abierta_comentario": det.get("abierta_comentario", ""),
        "costo_usd": salida.get("total_cost_usd"), "error": "",
    })


# ---------- páginas ----------

CSS = """
:root { --bg:#f6f5f2; --card:#fff; --tx:#1b1b1b; --mut:#666; --bd:#ddd; --ok:#1d7a3a; --mal:#b3261e; --duda:#a86400; --acc:#24527a; }
@media (prefers-color-scheme: dark) { :root { --bg:#151515; --card:#202020; --tx:#eee; --mut:#aaa; --bd:#3a3a3a; --ok:#5cc47a; --mal:#ff8a80; --duda:#f0b44c; --acc:#8cb8e0; } }
* { box-sizing:border-box; }
body { margin:0; padding:12px 16px 40px; background:var(--bg); color:var(--tx); font:16px/1.4 system-ui, sans-serif; max-width:760px; margin-inline:auto; }
a { color:var(--acc); }
h1 { font-size:1.25rem; margin:4px 0 12px; } h2 { font-size:1.05rem; margin:18px 0 8px; }
.card { background:var(--card); border:1px solid var(--bd); border-radius:10px; padding:12px; margin:8px 0; }
.fila { display:flex; justify-content:space-between; align-items:center; gap:8px; padding:10px 12px; background:var(--card);
        border:1px solid var(--bd); border-radius:10px; margin:6px 0; text-decoration:none; color:var(--tx); }
.mut { color:var(--mut); font-size:.88rem; }
.chip { font-size:.8rem; padding:2px 8px; border-radius:99px; border:1px solid var(--bd); white-space:nowrap; }
.chip.revisar { border-color:var(--duda); color:var(--duda); } .chip.confirmado { border-color:var(--ok); color:var(--ok); }
.chip.error { border-color:var(--mal); color:var(--mal); }
button, .btn { font:inherit; padding:12px 16px; border-radius:10px; border:1px solid var(--acc); background:var(--acc); color:#fff;
               width:100%; margin-top:10px; text-align:center; display:block; text-decoration:none; }
.btn.sec { background:transparent; color:var(--acc); }
input[type=file], input[type=text], input[type=number], textarea, select { font:inherit; width:100%; padding:10px; border-radius:8px;
               border:1px solid var(--bd); background:var(--card); color:var(--tx); }
label { display:block; margin:10px 0 4px; font-weight:600; }
.fotos { display:flex; gap:8px; overflow-x:auto; } .fotos img { height:180px; border-radius:6px; border:1px solid var(--bd); }
.preg { border-left:4px solid var(--bd); padding:6px 10px; margin:8px 0; background:var(--card); border-radius:6px; }
.preg.ok { border-color:var(--ok); } .preg.mal { border-color:var(--mal); } .preg.duda { border-color:var(--duda); }
.preg .enun { font-size:.92rem; }
.res { display:flex; gap:8px; align-items:center; margin-top:6px; flex-wrap:wrap; }
.res input { width:90px; }
.nota { font-size:2rem; font-weight:700; }
table { border-collapse:collapse; width:100%; font-size:.85rem; } td, th { border-bottom:1px solid var(--bd); padding:6px 4px; text-align:left; }
code { font-family:ui-monospace, monospace; font-size:.9em; }
.err { color:var(--mal); white-space:pre-wrap; font-size:.85rem; }
"""


def pagina(titulo, cuerpo, refrescar=False):
    meta = '<meta http-equiv="refresh" content="5">' if refrescar else ""
    return (f'<!doctype html><html lang="es"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width, initial-scale=1">{meta}'
            f'<title>{html.escape(titulo)}</title><style>{CSS}</style></head><body>{cuerpo}</body></html>')


def e(t):
    """Escapa y muestra `código` en monoespaciada (igual que el PDF impreso)."""
    return generar.e(str(t))


def ok_pin():
    return request.cookies.get(COOKIE) == hashlib.sha256(PIN.encode()).hexdigest()


@app.before_request
def exigir_pin():
    if request.endpoint not in ("login",) and not ok_pin():
        return redirect(f"/login?sig={request.path}")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if secrets.compare_digest(request.form.get("pin", ""), PIN):
            resp = redirect(request.args.get("sig") or "/")
            resp.set_cookie(COOKIE, hashlib.sha256(PIN.encode()).hexdigest(), max_age=14 * 86400, samesite="Strict")
            return resp
        error = '<p class="err">PIN incorrecto.</p>'
    else:
        error = ""
    return pagina("Parcial — ingreso", f"""<h1>Parcial B — corrección</h1>{error}
<form method="post"><label>PIN</label><input type="text" name="pin" inputmode="numeric" autofocus>
<button>Entrar</button></form>""")


def chip(est):
    estado = est.get("estado")
    if not estado:
        return '<span class="chip">sin foto</span>'
    if estado == "confirmado":
        return f'<span class="chip confirmado">{est.get("nota", "")}/30</span>'
    texto = {"corrigiendo": "corrigiendo…", "revisar": "para revisar", "error": "error"}[estado]
    return f'<span class="chip {estado}">{texto}</span>'


@app.route("/")
def inicio():
    filas = ""
    for com in COMISIONES:
        hechos = total = 0
        for gid in grupos(com):
            for sid, _ in integrantes(com, gid):
                total += 1
                hechos += leer_estado(com, gid, sid).get("estado") == "confirmado"
        filas += f'<a class="fila" href="/{com}"><span>{ETIQUETAS[com]}</span><span class="mut">{hechos}/{total} confirmados</span></a>'
    return pagina("Parcial B", f"<h1>Parcial B — Diseño de Sistemas Web</h1>{filas}")


@app.route("/<com>")
def comision(com):
    if com not in COMISIONES:
        abort(404)
    cuerpo = f'<p><a href="/">← inicio</a></p><h1>{ETIQUETAS[com]}</h1>'
    pendientes = 0
    for gid in grupos(com):
        cuerpo += f"<h2>{e(gid)}</h2>"
        for sid, nombre in integrantes(com, gid):
            est = leer_estado(com, gid, sid)
            pendientes += est.get("estado") == "corrigiendo"
            cuerpo += f'<a class="fila" href="/{com}/{gid}/{sid}"><span>{e(nombre)}</span>{chip(est)}</a>'
        cuerpo += (f'<form method="post" action="/{com}/{gid}/nuevo" class="res"><input type="text" name="nombre" '
                   f'placeholder="Otro estudiante (Apellido, Nombre)" style="flex:1;width:auto">'
                   f'<button style="width:auto;margin:0">+</button></form>')
    cuerpo += f'<a class="btn sec" href="/{com}/tabla">Tabla de notas</a>'
    return pagina(ETIQUETAS[com], cuerpo, refrescar=pendientes > 0)


@app.route("/<com>/<gid>/nuevo", methods=["POST"])
def nuevo(com, gid):
    nombre = request.form.get("nombre", "").strip()
    if not nombre:
        return redirect(f"/{com}")
    sid = slug(nombre)
    carpeta(com, gid, sid)
    guardar_estado(com, gid, sid, {"nombre": nombre})
    return redirect(f"/{com}/{gid}/{sid}")


def nombre_de(com, gid, sid):
    return dict(integrantes(com, gid)).get(sid) or leer_estado(com, gid, sid).get("nombre") or sid


@app.route("/<com>/<gid>/<sid>", methods=["GET"])
def estudiante(com, gid, sid):
    d = carpeta(com, gid, sid)
    est = leer_estado(com, gid, sid)
    nombre = nombre_de(com, gid, sid)
    volver = f'<p><a href="/{com}">← {ETIQUETAS[com]}</a></p><h1>{e(nombre)}</h1><p class="mut">{e(gid)}</p>'
    fotos = sorted(d.glob("foto-*.jpg")) if d.exists() else []
    galeria = ('<div class="fotos">' + "".join(
        f'<a href="/foto/{com}/{gid}/{sid}/{f.name}"><img src="/foto/{com}/{gid}/{sid}/{f.name}"></a>' for f in fotos)
        + "</div>") if fotos else ""
    subir = f"""<form method="post" action="/{com}/{gid}/{sid}/fotos" enctype="multipart/form-data" class="card">
<label>Carilla 1</label><input type="file" name="foto1" accept="image/*" capture="environment" required>
<label>Carilla 2</label><input type="file" name="foto2" accept="image/*" capture="environment">
<button>{'Reemplazar fotos y corregir de nuevo' if fotos else 'Subir y corregir'}</button></form>"""
    estado = est.get("estado")
    if estado == "corrigiendo":
        return pagina(nombre, volver + galeria + '<div class="card">Corrigiendo… (se actualiza solo)</div>', refrescar=True)
    if estado == "error":
        return pagina(nombre, volver + galeria + f'<div class="card"><b>Falló la lectura</b><p class="err">{e(est.get("error", ""))}</p>'
                      f'<form method="post" action="/{com}/{gid}/{sid}/reintentar"><button>Reintentar</button></form></div>' + subir)
    if estado in ("revisar", "confirmado"):
        return pagina(nombre, volver + galeria + revision(com, gid, sid, est) + f"<details><summary>Cambiar fotos</summary>{subir}</details>")
    return pagina(nombre, volver + subir)


def revision(com, gid, sid, est):
    _, preguntas = banco(com, gid)
    det = est.get("deteccion", {})
    dudosas = set(det.get("dudosas", []))
    total, detalle = puntuar(preguntas, est.get("respuestas", {}), est.get("abierta_pts", 0))
    bloques = ""
    for p, r, ok, pts in detalle:
        if p["tipo"] == "abierta":
            bloques += f"""<div class="preg"><div class="enun"><b>{p['n']}.</b> {e(p['texto'])}</div>
<p class="mut"><i>Escribió:</i> {e(det.get('abierta_transcripcion', ''))}</p>
<p class="mut"><i>Se espera:</i> {e(p['se_espera'])}</p>
<div class="res"><span>Puntaje</span><input type="number" name="abierta_pts" min="0" max="{p['pts']}" value="{pts}"></div>
<label>Comentario para el estudiante</label><textarea name="abierta_comentario" rows="3">{e(est.get('abierta_comentario', ''))}</textarea></div>"""
            continue
        clase = "duda" if (p["n"] in dudosas or r == "?") else ("ok" if ok else "mal")
        marca = "✓" if ok else "✗"
        bloques += f"""<div class="preg {clase}"><div class="enun"><b>{p['n']}.</b> {e(p['texto'][:140])}{'…' if len(p['texto']) > 140 else ''}</div>
<div class="res"><span>Marcó</span><input type="text" name="r{p['n']}" value="{e(r)}" autocapitalize="off">
<span>{marca} correcta: <b>{correcta(p)}</b></span>{' <span class="chip revisar">dudosa</span>' if clase == 'duda' else ''}</div></div>"""
    obs = det.get("observaciones") or ""
    escrito = det.get("nombre_escrito") or ""
    avisos = ""
    if obs:
        avisos += f'<p class="err">{e(obs)}</p>'
    if escrito:
        avisos += f'<p class="mut">Nombre en la hoja: {e(escrito)}</p>'
    confirmado = est.get("estado") == "confirmado"
    return f"""<div class="card"><span class="nota">{total}/30</span> {chip(est)}{avisos}</div>
<form method="post" action="/{com}/{gid}/{sid}/confirmar">{bloques}
<button>{'Guardar cambios' if confirmado else 'Confirmar nota'}</button></form>
<a class="btn sec" href="/{com}/{gid}/{sid}/alumno">Vista para el estudiante</a>"""


@app.route("/foto/<com>/<gid>/<sid>/<nombre>")
def foto(com, gid, sid, nombre):
    if not re.fullmatch(r"foto-\d\.jpg", nombre):
        abort(404)
    ruta = carpeta(com, gid, sid) / nombre
    if not ruta.exists():
        abort(404)
    return send_file(ruta, mimetype="image/jpeg")


@app.route("/<com>/<gid>/<sid>/fotos", methods=["POST"])
def subir_fotos(com, gid, sid):
    d = carpeta(com, gid, sid)
    archivos = [request.files.get(k) for k in ("foto1", "foto2")]
    archivos = [a for a in archivos if a and a.filename]
    if not archivos:
        return redirect(f"/{com}/{gid}/{sid}")
    d.mkdir(parents=True, exist_ok=True)
    for viejo in d.glob("foto-*.jpg"):
        viejo.unlink()
    for i, a in enumerate(archivos, 1):
        preparar_foto(io.BytesIO(a.read()), d / f"foto-{i}.jpg")
    guardar_estado(com, gid, sid, {"estado": "corrigiendo", "nombre": nombre_de(com, gid, sid),
                                   "subido": datetime.now().isoformat(timespec="seconds"), "error": ""})
    motor.submit(correr_motor, com, gid, sid)
    return redirect(f"/{com}")


@app.route("/<com>/<gid>/<sid>/reintentar", methods=["POST"])
def reintentar(com, gid, sid):
    carpeta(com, gid, sid)
    guardar_estado(com, gid, sid, {"estado": "corrigiendo", "error": ""})
    motor.submit(correr_motor, com, gid, sid)
    return redirect(f"/{com}/{gid}/{sid}")


@app.route("/<com>/<gid>/<sid>/confirmar", methods=["POST"])
def confirmar(com, gid, sid):
    carpeta(com, gid, sid)
    _, preguntas = banco(com, gid)
    respuestas = {str(p["n"]): normal_resp(p, request.form.get(f"r{p['n']}"))
                  for p in preguntas if p["tipo"] != "abierta"}
    try:
        pts = int(request.form.get("abierta_pts") or 0)
    except ValueError:
        pts = 0
    total, _ = puntuar(preguntas, respuestas, pts)
    guardar_estado(com, gid, sid, {
        "estado": "confirmado", "respuestas": respuestas, "abierta_pts": pts,
        "abierta_comentario": request.form.get("abierta_comentario", "").strip(), "nota": total,
        "confirmado": datetime.now().isoformat(timespec="seconds"),
    })
    return redirect(f"/{com}/{gid}/{sid}/alumno")


@app.route("/<com>/<gid>/<sid>/alumno")
def vista_alumno(com, gid, sid):
    carpeta(com, gid, sid)
    est = leer_estado(com, gid, sid)
    if est.get("estado") not in ("revisar", "confirmado"):
        return redirect(f"/{com}/{gid}/{sid}")
    _, preguntas = banco(com, gid)
    total, detalle = puntuar(preguntas, est.get("respuestas", {}), est.get("abierta_pts", 0))
    bloques = ""
    for p, r, ok, pts in detalle:
        if p["tipo"] == "abierta":
            bloques += (f'<div class="preg"><div class="enun"><b>{p["n"]}.</b> {e(p["texto"])}</div>'
                        f'<p><b>{pts}/{p["pts"]}</b> — {e(est.get("abierta_comentario", ""))}</p></div>')
            continue
        if p["tipo"] == "vf":
            def txt(x):
                return {"V": "Verdadero", "F": "Falso"}.get(x, "sin respuesta")
        else:
            def txt(x):
                if x == "?":
                    return "sin respuesta"
                return "; ".join(f"{l}) {p['opciones'][LETRAS.index(l)][0].rstrip('.')}" for l in x.split(",") if l in LETRAS[:len(p["opciones"])])
        cuerpo = f'<p class="mut">Tu respuesta: {e(txt(r))}</p>'
        if not ok:
            cuerpo += f'<p>Correcta: <b>{e(txt(correcta(p)))}</b></p><p class="mut">{e(p["por_que"])}</p>'
        bloques += (f'<div class="preg {"ok" if ok else "mal"}"><div class="enun"><b>{p["n"]}.</b> {e(p["texto"])} '
                    f'<b>{"✓" if ok else "✗"}</b></div>{cuerpo}</div>')
    aviso = "" if est.get("estado") == "confirmado" else '<p class="err">Todavía sin confirmar por el docente.</p>'
    return pagina("Tu resultado", f"""<h1>{e(nombre_de(com, gid, sid))}</h1><p class="mut">Cuestionario individual · {e(gid)}</p>
<div class="card"><span class="nota">{total}/30</span>{aviso}</div>{bloques}
<a class="btn sec" href="/{com}/{gid}/{sid}">← volver a la revisión</a>""")


def filas_tabla(com):
    filas = []
    for gid in grupos(com):
        _, preguntas = banco(com, gid)
        for sid, nombre in integrantes(com, gid):
            est = leer_estado(com, gid, sid)
            nota = ""
            if est.get("estado") in ("revisar", "confirmado"):
                nota, _ = puntuar(preguntas, est.get("respuestas", {}), est.get("abierta_pts", 0))
            filas.append({"grupo": gid, "estudiante": nombre, "estado": est.get("estado", "sin foto"), "nota": nota,
                          "abierta": est.get("abierta_pts", "") if est.get("estado") else ""})
    return filas


@app.route("/<com>/tabla")
def tabla(com):
    if com not in COMISIONES:
        abort(404)
    filas = filas_tabla(com)
    cuerpo = "".join(f"<tr><td>{e(f['estudiante'])}<br><span class='mut'>{e(f['grupo'])}</span></td>"
                     f"<td>{e(f['estado'])}</td><td><b>{e(f['nota'])}</b></td></tr>" for f in filas)
    return pagina("Tabla", f"""<p><a href="/{com}">← {ETIQUETAS[com]}</a></p><h1>Notas {ETIQUETAS[com]}</h1>
<table><tr><th>Estudiante</th><th>Estado</th><th>/30</th></tr>{cuerpo}</table>
<a class="btn sec" href="/{com}/tabla.csv">Descargar CSV</a>""")


@app.route("/<com>/tabla.csv")
def tabla_csv(com):
    if com not in COMISIONES:
        abort(404)
    out = io.StringIO()
    w = csv.DictWriter(out, fieldnames=["grupo", "estudiante", "estado", "nota", "abierta"])
    w.writeheader()
    w.writerows(filas_tabla(com))
    return Response(out.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": f"attachment; filename=parcial-b-{com}.csv"})


def ips_locales():
    """IPs de las placas reales (wifi, cable, tailscale), sin docker ni VMware."""
    salida = subprocess.run(["ip", "-4", "-o", "addr"], capture_output=True, text=True).stdout
    ips = []
    for linea in salida.splitlines():
        partes = linea.split()
        if not partes[1].startswith(("lo", "docker", "br-", "vmnet", "veth")):
            ips.append((partes[1], partes[3].split("/")[0]))
    return ips


def main():
    puerto = int(sys.argv[sys.argv.index("--puerto") + 1]) if "--puerto" in sys.argv else 8421
    print(f"\nParcial B — PIN: {PIN}")
    for placa, ip in ips_locales():
        print(f"  http://{ip}:{puerto}   ({placa})")
    print()
    app.run(host="0.0.0.0", port=puerto, debug=False, threaded=True)


if __name__ == "__main__":
    main()

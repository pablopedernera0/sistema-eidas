#!/usr/bin/env python3
"""Corrección del parcial B (cuestionario impreso por grupo) desde el celular.

A diferencia de dashboard.py, este SÍ escucha en la red (0.0.0.0) para que el docente entre
desde el celular a la IP de la notebook; por eso pide un PIN y no expone nada más que esto.

Flujo: elegir comisión → grupo → estudiante, sacar foto de las carillas (hasta 6), el motor (`claude`
de la terminal) lee las marcas y propone el puntaje de la abierta en segundo plano; el
docente revisa al lado de la foto, corrige si hace falta y confirma. Queda una vista para
mostrarle al estudiante y una tabla/CSV por comisión.

  python3 scripts/parcial.py [--parcial iti] [--puerto 8421]      (PIN: variable PARCIAL_PIN o uno al azar)

Bancos y clave: sistema-eidas-datos/cuestionarios/parcial-b-2c-2026/ (se usa su generar.py
para que las letras sean las mismas que las impresas). Fotos y resultados quedan en
respuestas/<com>/<grupo>/<estudiante>/ dentro de esa carpeta.

Con --parcial iti corrige el parcial de Infraestructura de Redes II (cuestionarios/parcial-iti21-2c-2026/):
un solo banco en dos versiones (A/B, mismas preguntas con otro orden de opciones). Hay un único
"grupo" con la lista del curso (cierre-2c-2026.csv de ITI); la versión se elige al subir las fotos y
queda en el estado de cada estudiante. La abierta admite medio punto.
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
import shutil
import subprocess
import sys
import threading
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path

from flask import Flask, Response, abort, redirect, request, send_file

ROOT = Path(__file__).resolve().parent.parent
MATERIAS_DIR = ROOT / "materias"
DATOS_DIR = ROOT.parent / "sistema-eidas-datos"
ITI = "--parcial" in sys.argv and sys.argv[sys.argv.index("--parcial") + 1] == "iti"
if ITI:
    PARCIAL_DIR = DATOS_DIR / "cuestionarios" / "parcial-iti21-2c-2026"
    COMISIONES = {"iti": "iti-infra-redes-21"}
    ETIQUETAS = {"iti": "ITI-21"}
    TITULO, MATERIA, TOTAL, IMPRESO = "Parcial ITI-21", "Infraestructura de Redes II", 10, "Versión"
    ROSTER_ITI = DATOS_DIR / "iti-infra-redes-21" / "cierre-2c-2026.csv"
    GRUPO_ITI = "iti21"
else:
    PARCIAL_DIR = DATOS_DIR / "cuestionarios" / "parcial-b-2c-2026"
    COMISIONES = {"c31": "af-diseno-sistemas-web-31", "c32": "af-diseno-sistemas-web-32"}
    ETIQUETAS = {"c31": "3.° 1.ª", "c32": "3.° 2.ª"}
    TITULO, MATERIA, TOTAL, IMPRESO = "Parcial B", "Diseño de Sistemas Web", 30, "Grupo"
RESP_DIR = PARCIAL_DIR / "respuestas"
PIN = os.environ.get("PARCIAL_PIN") or f"{random.randint(0, 9999):04d}"
COOKIE = "parcial_pin"
LETRAS = "abcdefgh"
MAX_CARILLAS = 6  # el nombre foto-N.jpg asume un solo dígito
MODELO = os.environ.get("PARCIAL_MODELO", "sonnet")  # sonnet gasta bastante menos cuota que opus y alcanza para leer marcas

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


def banco(com, gid, sid=None):
    """(meta, preguntas) con las opciones en el mismo orden que el PDF impreso.
    En ITI depende de la versión (A/B) que tiene cargada el estudiante."""
    if ITI:
        return generar.version(version_de(com, gid, sid))
    ruta = PARCIAL_DIR / "bancos" / f"{com}-{gid}.md"
    if not ruta.exists():
        abort(404)
    meta, preguntas = generar.leer_banco(ruta)
    generar.mezclar(meta, preguntas)
    return meta, preguntas


def version_de(com, gid, sid):
    v = leer_estado(com, gid, sid).get("version") if sid else None
    return v if v in generar.VERSIONES else "A"


def grupos(com):
    if ITI:
        return [GRUPO_ITI]
    return [r.name[len(com) + 1:-3] for r in sorted(PARCIAL_DIR.glob(f"bancos/{com}-*.md"), key=lambda r: r.name.lower())]


def num(x):
    """Puntaje como número (admite medio punto); 1.0 → 1 para mostrarlo sin decimales."""
    try:
        x = round(float(str(x).replace(",", ".")) * 2) / 2
    except ValueError:
        return 0
    return int(x) if x == int(x) else x


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
    """[(slug, 'Apellido, Nombre')] desde integrantes.md (en ITI, la lista del curso), más los cargados a mano."""
    lista = []
    if ITI:
        with open(ROSTER_ITI, newline="", encoding="utf-8") as f:
            for fila in csv.DictReader(f):
                nombre = fila["Alumno"].strip().title()
                if nombre:
                    lista.append((slug(nombre), nombre))
    else:
        ruta = MATERIAS_DIR / COMISIONES[com] / "grupos" / gid / "integrantes.md"
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


def apellido_en(nombre, escrito):
    """True si alguna palabra del apellido ('Apellido, Nombre') aparece, con tolerancia a la letra
    manuscrita, en el nombre escrito en la hoja."""
    palabras = re.findall(r"[a-z]+", normalizar(escrito))
    apellido = [a for a in re.findall(r"[a-z]+", normalizar(nombre.split(",")[0])) if len(a) >= 3]
    return any(SequenceMatcher(None, a, w).ratio() >= 0.8 for a in apellido for w in palabras)


def sospecha(com, gid, nombre, est):
    """(aviso, [(gid, sid, nombre)] candidatos) si las fotos parecen de otro estudiante o grupo; ('', []) si no."""
    det = est.get("deteccion") or {}
    escrito, impreso = det.get("nombre_escrito") or "", det.get("grupo_impreso") or ""
    avisos = []
    if ITI:
        impreso = ""  # la versión distinta se avisa aparte (version_impresa), no es otro estudiante
    if impreso and slug(impreso) != slug(gid):
        avisos.append(f"La hoja es del grupo «{impreso}», no de {gid}.")
    if escrito and not apellido_en(nombre, escrito):
        avisos.append(f"En la hoja dice «{escrito}», no {nombre}.")
    if not avisos:
        return "", []
    candidatos = [(g, s, n) for g in grupos(com) for s, n in integrantes(com, g)
                  if escrito and apellido_en(n, escrito) and (not impreso or slug(impreso) == slug(g))]
    return " ".join(avisos), candidatos


def version_impresa(est):
    """En ITI, la versión que dice la hoja si es A o B y no coincide con la cargada; '' si no."""
    v = re.sub(r"[^AB]", "", ((est.get("deteccion") or {}).get("grupo_impreso") or "").upper()[-1:])
    return v if ITI and v and v != (est.get("version") or "A") else ""


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


def puntuar(preguntas, respuestas, abierta_pts, manual=None):
    """manual: {n: pts} puestos a mano por el docente (crédito parcial); pisan el todo-o-nada."""
    total, detalle, manual = 0, [], manual or {}
    for p in preguntas:
        if p["tipo"] == "abierta":
            pts = max(0, min(p["pts"], num(abierta_pts or 0)))
            detalle.append((p, None, None, pts))
        else:
            r = normal_resp(p, respuestas.get(str(p["n"])))
            ok = r == correcta(p)
            pts = p["pts"] if ok else 0
            if str(p["n"]) in manual:
                pts = max(0, min(p["pts"], num(manual[str(p["n"])])))
            detalle.append((p, r, ok, pts))
        total += pts
    return num(total), detalle


# ---------- motor ----------

ESQUEMA = {
    "type": "object",
    "properties": {
        "respuestas": {"type": "object", "additionalProperties": {"type": "string"},
                       "description": "pregunta (1..9) -> 'V'/'F', una letra, o letras separadas por coma; '?' si no se lee"},
        "dudosas": {"type": "array", "items": {"type": "integer"}},
        "abierta_transcripcion": {"type": "string"},
        "abierta_puntaje": {"type": "number", "minimum": 0},
        "abierta_comentario": {"type": "string"},
        "nombre_escrito": {"type": "string"},
        "grupo_impreso": {"type": "string", "description": f"lo que dice '{IMPRESO}:' en el encabezado impreso"},
        "observaciones": {"type": "string"},
    },
    "required": ["respuestas", "dudosas", "abierta_transcripcion", "abierta_puntaje", "abierta_comentario"],
}


PROMPT_VERSION = "v2-sin-opciones"  # v1 (hasta el Parcial B 2c-2026): mandaba el texto completo de cada opción
COSTOS = PARCIAL_DIR / "costos.jsonl"  # una línea por corrida del motor, reintentos incluidos (el estado guarda solo la última)


def recorte(texto, largo=70):
    return texto if len(texto) <= largo else texto[:largo].rsplit(" ", 1)[0] + "…"


def prompt_motor(meta, preguntas, fotos):
    partes = []
    for p in preguntas:
        if p["tipo"] == "abierta":
            partes.append(f"{p['n']}. (ABIERTA) {p['texto']}\n   Criterio del docente: {p['se_espera']}")
        elif p["tipo"] == "vf":
            partes.append(f"{p['n']}. (V/F, círculos) {recorte(p['texto'])}")
        else:  # solo hace falta leer la marca: el inicio del enunciado para ubicarla y las letras, no el texto de cada opción
            como = "una sola, círculos" if p["tipo"] == "una" else "varias, cuadrados"
            partes.append(f"{p['n']}. ({como}, opciones a–{LETRAS[len(p['opciones']) - 1]}) {recorte(p['texto'])}")
    lista = "\n".join(f"- {f}" for f in fotos)
    abierta = next(p for p in preguntas if p["tipo"] == "abierta")
    escala = f"de 0 a {abierta['pts']}" + (" (podés usar medio punto: 0,5)" if ITI else "")
    cual = f"Versión {meta['version']}" if ITI else f"Grupo: {meta['grupo']}"
    return f"""Corregís un cuestionario impreso que un estudiante completó a mano. Leé con Read estas fotos (carillas del examen):
{lista}

{cual}. Estas son las preguntas tal como están impresas (mismas letras):

{chr(10).join(partes)}

Para cada pregunta 1 a 9 informá SOLO lo que el estudiante marcó (no lo que sería correcto): "V" o "F"; una letra; o varias letras separadas por coma.
- Vale cualquier marca clara (cruz, tilde, círculo relleno o rodeado). Si tachó una y aclaró otra, vale la aclarada.
- Si no marcó nada, o no se puede leer con seguridad, poné "?" y agregá el número a "dudosas". Si dudás entre dos lecturas, poné la más probable y agregala a "dudosas".
Pregunta 10: transcribí lo que escribió, puntuala {escala} con el criterio del docente y escribí un comentario de 1 o 2 oraciones para el estudiante, en voseo rioplatense: qué estuvo bien y qué le faltó. Si está en blanco, 0 y decilo.
"nombre_escrito": el nombre que figura en la hoja, si se lee. "grupo_impreso": lo que dice "{IMPRESO}:" en el encabezado impreso de la hoja. "observaciones": algo raro de la foto (borrosa, falta una carilla, es de otro {IMPRESO.lower()}), o vacío."""


def preparar_foto(origen, destino):
    from PIL import Image, ImageOps
    img = ImageOps.exif_transpose(Image.open(origen)).convert("RGB")
    img.thumbnail((1600, 1600))  # menos píxeles = menos tokens por foto
    img.save(destino, "JPEG", quality=85)


def correr_motor(com, gid, sid):
    meta, preguntas = banco(com, gid, sid)
    d = carpeta(com, gid, sid)
    fotos = [str(f) for f in sorted(d.glob("foto-*.jpg"))]
    try:
        r = subprocess.run(
            ["claude", "-p", prompt_motor(meta, preguntas, fotos), "--output-format", "json", "--model", MODELO,
             "--json-schema", json.dumps(ESQUEMA), "--allowedTools", "Read", "--add-dir", str(d),
             "--no-session-persistence"],
            capture_output=True, text=True, timeout=300, cwd=d)
        salida = json.loads(r.stdout)
        anotar_costo(com, gid, sid, len(fotos), salida)
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
        "abierta_pts": num(det.get("abierta_puntaje", 0)), "abierta_comentario": det.get("abierta_comentario", ""),
        "costo_usd": salida.get("total_cost_usd"), "error": "",
        "motor": {"prompt": PROMPT_VERSION, "modelo": MODELO, "usage": salida.get("usage"), "duracion_ms": salida.get("duration_ms")},
    })


def anotar_costo(com, gid, sid, fotos, salida):
    linea = {"fecha": datetime.now().isoformat(timespec="seconds"), "com": com, "grupo": gid, "estudiante": sid,
             "prompt": PROMPT_VERSION, "modelo": MODELO, "fotos": fotos, "costo_usd": salida.get("total_cost_usd"),
             "usage": salida.get("usage"), "duracion_ms": salida.get("duration_ms"), "error": bool(salida.get("is_error"))}
    with candado, COSTOS.open("a") as f:
        f.write(json.dumps(linea, ensure_ascii=False) + "\n")


# ---------- páginas ----------

CSS = """
:root { --bg:#f6f5f2; --card:#fff; --tx:#1b1b1b; --mut:#666; --bd:#ddd; --ok:#1d7a3a; --mal:#b3261e; --duda:#a86400; --acc:#24527a; }
@media (prefers-color-scheme: dark) { :root { --bg:#151515; --card:#202020; --tx:#eee; --mut:#aaa; --bd:#3a3a3a; --ok:#5cc47a; --mal:#ff8a80; --duda:#f0b44c; --acc:#8cb8e0; } }
* { box-sizing:border-box; }
body { margin:0; padding:12px 16px 40px; background:var(--bg); color:var(--tx); font:16px/1.4 system-ui, sans-serif; max-width:760px; margin-inline:auto;
       overflow-wrap:anywhere; }
.fila > span:first-child { min-width:0; }
[hidden] { display:none !important; }
.nav { display:flex; gap:6px; margin:8px 0; }
.nav-btn { flex:1; text-align:center; padding:10px 6px; border:1px solid var(--acc); border-radius:10px; color:var(--acc);
           text-decoration:none; font-size:.9rem; }
.nav-btn.pend { background:var(--acc); color:#fff; } .nav-btn.off { opacity:.35; border-color:var(--bd); color:var(--mut); background:none; }
.spin { display:inline-block; width:1em; height:1em; margin-right:8px; vertical-align:-2px; border:2px solid currentColor;
        border-right-color:transparent; border-radius:50%; animation:girar .7s linear infinite; }
@keyframes girar { to { transform:rotate(360deg); } }
button:disabled { opacity:.75; }
.buscar { position:sticky; top:0; z-index:1; background:var(--bg); padding:8px 0; }
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
input[type=file], input[type=text], input[type=search], input[type=number], textarea, select { font:inherit; width:100%; padding:10px; border-radius:8px;
               border:1px solid var(--bd); background:var(--card); color:var(--tx); }
label { display:block; margin:10px 0 4px; font-weight:600; }
.fotos { display:flex; gap:8px; overflow-x:auto; } .fotos img { height:180px; border-radius:6px; border:1px solid var(--bd); }
.preg { border-left:4px solid var(--bd); padding:6px 10px; margin:8px 0; background:var(--card); border-radius:6px; }
.preg.ok { border-color:var(--ok); } .preg.mal { border-color:var(--mal); } .preg.duda, .preg.parcial { border-color:var(--duda); }
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
            f'<title>{html.escape(titulo)}</title><style>{CSS}</style></head><body>{cuerpo}{CARGANDO}</body></html>')


# Al mandar un formulario: botón deshabilitado (evita doble envío) con spinner hasta que cargue la página siguiente.
CARGANDO = """<script>
document.addEventListener("submit", ev => {
  const b = ev.target.querySelector("button:not([type=button])");
  if (!b || ev.defaultPrevented) return;
  b.disabled = true;
  b.innerHTML = '<span class="spin"></span>' + (b.dataset.cargando || "Guardando…");
});
window.addEventListener("pageshow", ev => {  // volver atrás desde el celular: que el botón no quede trabado
  if (ev.persisted) location.reload();
});
</script>"""


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
    return pagina("Parcial — ingreso", f"""<h1>{TITULO} — corrección</h1>{error}
<form method="post"><label>PIN</label><input type="text" name="pin" inputmode="numeric" autofocus>
<button>Entrar</button></form>""")


def chip(est, nota=None, otro=False):
    estado = est.get("estado")
    if not estado:
        return '<span class="chip">sin foto</span>'
    if otro:
        return '<span class="chip error">¿fotos de otro?</span>'
    if estado == "confirmado":
        return f'<span class="chip confirmado">{est.get("nota", "")}/{TOTAL}</span>'
    if estado == "revisar" and nota is not None:
        return f'<span class="chip revisar">{nota}/{TOTAL} · revisar</span>'
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
    return pagina(TITULO, f"<h1>{TITULO} — {MATERIA}</h1>{filas}")


@app.route("/<com>")
def comision(com):
    if com not in COMISIONES:
        abort(404)
    cuerpo = (f'<p><a href="/">← inicio</a></p><h1>{ETIQUETAS[com]}</h1>'
              f'<div class="buscar"><input type="search" id="buscar" placeholder="Buscar apellido…" autocomplete="off"></div>')
    pendientes = 0
    for gid in grupos(com):
        cuerpo += f'<section class="grupo"><h2>{e(gid)}</h2>'
        for sid, nombre in integrantes(com, gid):
            est = leer_estado(com, gid, sid)
            pendientes += est.get("estado") == "corrigiendo"
            nota = otro = None
            if est.get("estado") in ("revisar", "confirmado"):
                _, preguntas = banco(com, gid, sid)
                nota, _ = puntuar(preguntas, est.get("respuestas", {}), est.get("abierta_pts", 0), est.get("pts_manual"))
                otro = bool(sospecha(com, gid, nombre, est)[0])
            cuerpo += f'<a class="fila" href="/{com}/{gid}/{sid}"><span>{e(nombre)}</span>{chip(est, nota, otro)}</a>'
        cuerpo += (f'<form method="post" action="/{com}/{gid}/nuevo" class="res"><input type="text" name="nombre" '
                   f'placeholder="Otro estudiante (Apellido, Nombre)" style="flex:1;width:auto">'
                   f'<button style="width:auto;margin:0">+</button></form></section>')
    cuerpo += f'<p id="nada" class="mut" hidden>Nadie con ese apellido.</p><a class="btn sec" href="/{com}/tabla">Tabla de notas</a>'
    return pagina(ETIQUETAS[com], cuerpo + BUSCADOR.replace("CLAVE", com), refrescar=pendientes > 0)


# Filtra las filas por texto sin tildes; el texto queda en sessionStorage para sobrevivir al refresco automático.
BUSCADOR = """<script>
(() => {
  const q = document.getElementById("buscar"), clave = "buscar-CLAVE";
  const norm = t => t.normalize("NFD").replace(/[\\u0300-\\u036f]/g, "").toLowerCase();
  function filtrar() {
    const t = norm(q.value.trim());
    let hay = false;
    try { sessionStorage.setItem(clave, q.value); } catch (_) {}
    for (const g of document.querySelectorAll(".grupo")) {
      let visibles = 0;
      for (const f of g.querySelectorAll(".fila")) {
        const ok = !t || norm(f.firstElementChild.textContent).includes(t);
        f.hidden = !ok; visibles += ok;
      }
      g.hidden = t && !visibles;
      g.querySelector("form").hidden = !!t;
      hay ||= visibles > 0;
    }
    document.getElementById("nada").hidden = !t || hay;
  }
  try { q.value = sessionStorage.getItem(clave) || ""; } catch (_) {}
  q.addEventListener("input", filtrar);
  filtrar();
})();
</script>"""


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
    elegir_version = ""
    if ITI:
        actual = est.get("version")
        elegir_version = '<label>Versión (arriba a la derecha de la hoja)</label><div class="res">' + "".join(
            f'<label style="margin:0;font-weight:400"><input type="radio" name="version" value="{v}" required'
            f'{" checked" if v == actual else ""}> {v}</label>' for v in generar.VERSIONES) + "</div>"
    carillas = "".join(
        f'<div class="carilla"{" hidden" if i > 2 else ""}><label>Carilla {i}</label><input type="file" name="foto{i}" '
        f'accept="image/*" capture="environment"{" required" if i == 1 else ""}></div>' for i in range(1, MAX_CARILLAS + 1))
    subir = f"""<form method="post" action="/{com}/{gid}/{sid}/fotos" enctype="multipart/form-data" class="card">{elegir_version}
{carillas}
<button type="button" class="btn sec" onclick="const c = this.form.querySelector('.carilla[hidden]'); if (c) c.hidden = false;
  if (!this.form.querySelector('.carilla[hidden]')) this.hidden = true;">+ Otra carilla</button>
<button data-cargando="Subiendo fotos…">{'Reemplazar fotos y corregir de nuevo' if fotos else 'Subir y corregir'}</button></form>"""
    estado = est.get("estado")
    nav = navegacion(com, gid, sid)
    if estado == "corrigiendo":
        return pagina(nombre, nav + volver + galeria + '<div class="card">Corrigiendo… (se actualiza solo)</div>' + nav, refrescar=True)
    if estado == "error":
        return pagina(nombre, nav + volver + galeria + f'<div class="card"><b>Falló la lectura</b><p class="err">{e(est.get("error", ""))}</p>'
                      f'<form method="post" action="/{com}/{gid}/{sid}/reintentar"><button>Reintentar</button></form></div>' + subir + nav)
    if estado in ("revisar", "confirmado"):
        return pagina(nombre, nav + volver + galeria + revision(com, gid, sid, est)
                      + f"<details><summary>Cambiar fotos</summary>{subir}</details>" + nav)
    return pagina(nombre, nav + volver + subir + nav)


def navegacion(com, gid, sid):
    """Anterior / siguiente en el orden de la lista de la comisión, y el próximo que falta revisar."""
    orden = [(g, s) for g in grupos(com) for s, _ in integrantes(com, g)]
    i = orden.index((gid, sid)) if (gid, sid) in orden else -1
    pendiente = next((x for x in orden[i + 1:] + orden[:max(i, 0)]
                      if leer_estado(com, *x).get("estado") == "revisar"), None)

    def link(x, texto, extra=""):
        if not x:
            return f'<span class="nav-btn off{extra}">{texto}</span>'
        return f'<a class="nav-btn{extra}" href="/{com}/{x[0]}/{x[1]}">{texto}</a>'
    return (f'<nav class="nav">{link(orden[i - 1] if i > 0 else None, "← Anterior")}'
            f'{link(pendiente, "Próximo para revisar", " pend")}'
            f'{link(orden[i + 1] if 0 <= i < len(orden) - 1 else None, "Siguiente →")}</nav>' + AVISO_SALIDA)


# Si hay cambios sin guardar en la revisión, pregunta antes de irse con la navegación.
AVISO_SALIDA = """<script>
document.currentScript.previousElementSibling.addEventListener("click", ev => {
  const pend = document.getElementById("sin-guardar");
  if (ev.target.closest("a") && pend && !pend.hidden && !confirm("Hay cambios sin guardar. ¿Salir igual?")) ev.preventDefault();
});
</script>"""


def revision(com, gid, sid, est):
    _, preguntas = banco(com, gid, sid)
    det = est.get("deteccion", {})
    dudosas = set(det.get("dudosas", []))
    total, detalle = puntuar(preguntas, est.get("respuestas", {}), est.get("abierta_pts", 0), est.get("pts_manual"))
    bloques = ""
    for p, r, ok, pts in detalle:
        if p["tipo"] == "abierta":
            bloques += f"""<div class="preg"><div class="enun"><b>{p['n']}.</b> {e(p['texto'])}</div>
<p class="mut"><i>Escribió:</i> {e(det.get('abierta_transcripcion', ''))}</p>
<p class="mut"><i>Se espera:</i> {e(p['se_espera'])}</p>
<div class="res"><span>Puntaje</span><input type="number" name="abierta_pts" min="0" max="{p['pts']}" step="0.5" value="{pts}" data-pts="{p['pts']}"></div>
<label>Comentario para el estudiante</label><textarea name="abierta_comentario" rows="3">{e(est.get('abierta_comentario', ''))}</textarea></div>"""
            continue
        clase = "duda" if (p["n"] in dudosas or r == "?") else ("ok" if pts == p["pts"] else "parcial" if pts else "mal")
        comentario = est.get("comentarios", {}).get(str(p["n"]), "")
        marca = "✓" if ok else "✗"
        bloques += f"""<div class="preg {clase}" data-tipo="{p['tipo']}" data-correcta="{correcta(p)}" data-pts="{p['pts']}"><div class="enun"><b>{p['n']}.</b> {e(p['texto'][:140])}{'…' if len(p['texto']) > 140 else ''}</div>
<div class="res"><span>Marcó</span><input type="text" name="r{p['n']}" value="{e(r)}" autocapitalize="off">
<span><span class="marca">{marca}</span> correcta: <b>{correcta(p)}</b></span>
<span>Puntaje <input type="number" name="p{p['n']}" class="pts" min="0" max="{p['pts']}" step="0.5" value="{pts}" style="width:64px">/{p['pts']}</span>{' <span class="chip revisar">dudosa</span>' if clase == 'duda' else ''}</div>
<details{' open' if comentario else ''}><summary class="mut">Comentario</summary>
<textarea name="c{p['n']}" rows="2" placeholder="Opcional, lo ve el estudiante">{e(comentario)}</textarea></details></div>"""
    obs = det.get("observaciones") or ""
    escrito = det.get("nombre_escrito") or ""
    avisos = ""
    if obs:
        avisos += f'<p class="err">{e(obs)}</p>'
    if escrito:
        avisos += f'<p class="mut">Nombre en la hoja: {e(escrito)}</p>'
    aviso, candidatos = sospecha(com, gid, nombre_de(com, gid, sid), est)
    if aviso:
        opciones = "".join(f'<option value="{g}/{s}">{e(n)} — {e(g)}</option>'
                           for g in grupos(com) for s, n in integrantes(com, g) if (g, s) != (gid, sid))
        for g, s, _ in candidatos[:1]:
            opciones = opciones.replace(f'value="{g}/{s}"', f'value="{g}/{s}" selected', 1)
        if not candidatos:
            opciones = '<option value="">— elegir —</option>' + opciones
        avisos = (f'<div class="card" style="border-color:var(--mal)"><b class="err">⚠ ¿Fotos de otro estudiante?</b>'
                  f'<p class="err">{e(aviso)}</p><form method="post" action="/{com}/{gid}/{sid}/mover">'
                  f'<label>Mover estas fotos a</label><select name="destino">{opciones}</select>'
                  f'<button>Mover</button></form>'
                  f'<form method="post" action="/{com}/{gid}/{sid}/descartar"><button class="btn sec">'
                  f'Descartar (duplicado de algo ya cargado)</button></form></div>') + avisos
    if ITI:
        otra = version_impresa(est)
        if otra:
            avisos = (f'<div class="card" style="border-color:var(--mal)"><b class="err">⚠ La hoja dice versión {otra}, '
                      f'cargada como {est.get("version") or "A"}.</b>'
                      f'<form method="post" action="/{com}/{gid}/{sid}/version"><input type="hidden" name="version" value="{otra}">'
                      f'<button>Corregir con la clave de la versión {otra}</button></form></div>') + avisos
        avisos += f'<p class="mut">Versión {version_de(com, gid, sid)}</p>'
    confirmado = est.get("estado") == "confirmado"
    return f"""<div class="card"><span class="nota"><span id="total">{total}</span>/{TOTAL}</span> {chip(est)}
<span id="sin-guardar" class="chip revisar" hidden>sin guardar</span>{avisos}</div>
<form method="post" action="/{com}/{gid}/{sid}/confirmar">{bloques}
<button>{'Guardar cambios' if confirmado else 'Confirmar nota'}</button></form>
<a class="btn sec" href="/{com}/{gid}/{sid}/alumno">Vista para el estudiante</a>{RECALCULO}"""


# Recalcula el total mientras se corrige; misma normalización que normal_resp() y puntuar().
RECALCULO = """<script>
(() => {
  const form = document.querySelector("form[action$='/confirmar']");
  function normal(tipo, r) {
    r = (r || "").trim();
    if (tipo === "vf") { r = r.slice(0, 1).toUpperCase(); return r === "V" || r === "F" ? r : "?"; }
    const letras = [...new Set(r.toLowerCase().match(/[a-h]/g) || [])].sort();
    return letras.length ? letras.join(",") : "?";
  }
  function recalcular(cambio) {
    let total = 0;
    for (const p of form.querySelectorAll(".preg[data-correcta]")) {
      const ok = normal(p.dataset.tipo, p.querySelector("input[type=text]").value) === p.dataset.correcta;
      const caja = p.querySelector("input.pts");
      if (cambio === p.querySelector("input[type=text]")) caja.value = ok ? p.dataset.pts : 0;  // nueva respuesta: vuelve al automático
      const pts = Math.max(0, Math.min(+p.dataset.pts, parseFloat(caja.value) || 0));
      p.classList.remove("ok", "mal", "duda", "parcial");
      p.classList.add(pts == p.dataset.pts ? "ok" : pts ? "parcial" : "mal");
      p.querySelector(".marca").textContent = ok ? "✓" : "✗";
      total += pts;
    }
    const abierta = form.querySelector("input[name=abierta_pts]");
    if (abierta) total += Math.max(0, Math.min(+abierta.dataset.pts, parseFloat(abierta.value) || 0));
    document.getElementById("total").textContent = total;
    document.getElementById("sin-guardar").hidden = false;
  }
  form.addEventListener("input", e => { if (e.target.matches("input")) recalcular(e.target); else document.getElementById("sin-guardar").hidden = false; });
})();
</script>"""


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
    archivos = [request.files.get(k) for k in (f"foto{i}" for i in range(1, MAX_CARILLAS + 1))]
    archivos = [a for a in archivos if a and a.filename]
    if not archivos:
        return redirect(f"/{com}/{gid}/{sid}")
    d.mkdir(parents=True, exist_ok=True)
    for viejo in d.glob("foto-*.jpg"):
        viejo.unlink()
    for i, a in enumerate(archivos, 1):
        preparar_foto(io.BytesIO(a.read()), d / f"foto-{i}.jpg")
    cambios = {"estado": "corrigiendo", "nombre": nombre_de(com, gid, sid),
               "subido": datetime.now().isoformat(timespec="seconds"), "error": ""}
    if ITI and request.form.get("version") in generar.VERSIONES:
        cambios["version"] = request.form["version"]
    guardar_estado(com, gid, sid, cambios)
    motor.submit(correr_motor, com, gid, sid)
    return redirect(f"/{com}")


@app.route("/<com>/<gid>/<sid>/mover", methods=["POST"])
def mover(com, gid, sid):
    """Pasa fotos y lectura a otro estudiante. Si cambia el grupo, cambia el banco: se vuelve a leer."""
    origen = carpeta(com, gid, sid)
    g2, _, s2 = request.form.get("destino", "").partition("/")
    if not s2:
        return redirect(f"/{com}/{gid}/{sid}")
    destino = carpeta(com, g2, s2)
    nombre = nombre_de(com, g2, s2)
    fotos_destino = sorted(destino.glob("foto-*.jpg"))
    if fotos_destino and not request.form.get("reemplazar"):
        def galeria(g, s_, fotos):
            return '<div class="fotos">' + "".join(f'<a href="/foto/{com}/{g}/{s_}/{f.name}"><img src="/foto/{com}/{g}/{s_}/{f.name}"></a>'
                                                   for f in fotos) + "</div>"
        est_d = leer_estado(com, g2, s2)
        return pagina("¿Reemplazar?", f"""<h1>{e(nombre)} ya tiene fotos</h1>
<p class="mut">Cargadas {e(est_d.get('subido', ''))} · {chip(est_d)}</p>{galeria(g2, s2, fotos_destino)}
<h2>Las que querés mover (de {e(nombre_de(com, gid, sid))})</h2>{galeria(gid, sid, sorted(origen.glob('foto-*.jpg')))}
<p>Si las reemplazás, las fotos y la corrección que ya tenía {e(nombre)} van a <code>_duplicados/</code> (no se borran).
Si son el mismo examen, mejor descartá estas.</p>
<form method="post"><input type="hidden" name="destino" value="{g2}/{s2}"><input type="hidden" name="reemplazar" value="1">
<button>Reemplazar las de {e(nombre)}</button></form>
<form method="post" action="/{com}/{gid}/{sid}/descartar"><button class="btn sec">Descartar estas (duplicado)</button></form>
<a class="btn sec" href="/{com}/{gid}/{sid}">← volver</a>""")
    if fotos_destino:
        apartar(com, g2, s2)
    est = leer_estado(com, gid, sid)
    destino.mkdir(parents=True, exist_ok=True)
    for f in origen.glob("foto-*.jpg"):
        shutil.move(f, destino / f.name)
    (origen / "estado.json").unlink(missing_ok=True)
    if not any(origen.iterdir()):
        origen.rmdir()
    with candado:
        (destino / "estado.json").unlink(missing_ok=True)
    guardar_estado(com, g2, s2, {**est, "nombre": nombre, "movido_de": f"{gid}/{sid}"})
    if g2 != gid:
        guardar_estado(com, g2, s2, {"estado": "corrigiendo", "error": ""})
        motor.submit(correr_motor, com, g2, s2)
    return redirect(f"/{com}/{g2}/{s2}")


@app.route("/<com>/<gid>/<sid>/descartar", methods=["POST"])
def descartar(com, gid, sid):
    """Aparta fotos y lectura en respuestas/<com>/_duplicados/ (no se borran); el estudiante queda sin foto."""
    apartar(com, gid, sid)
    return redirect(f"/{com}")


def apartar(com, gid, sid):
    origen = carpeta(com, gid, sid)
    if origen.exists():
        destino = RESP_DIR / com / "_duplicados" / f"{gid}-{sid}-{datetime.now():%Y%m%d-%H%M%S}"
        destino.parent.mkdir(parents=True, exist_ok=True)
        with candado:
            shutil.move(origen, destino)


@app.route("/<com>/<gid>/<sid>/version", methods=["POST"])
def cambiar_version(com, gid, sid):
    """ITI: corrige con la clave de la otra versión. Las letras marcadas no cambian, así que no hace falta releer."""
    carpeta(com, gid, sid)
    if ITI and request.form.get("version") in generar.VERSIONES:
        guardar_estado(com, gid, sid, {"version": request.form["version"]})
    return redirect(f"/{com}/{gid}/{sid}")


@app.route("/<com>/<gid>/<sid>/reintentar", methods=["POST"])
def reintentar(com, gid, sid):
    carpeta(com, gid, sid)
    guardar_estado(com, gid, sid, {"estado": "corrigiendo", "error": ""})
    motor.submit(correr_motor, com, gid, sid)
    return redirect(f"/{com}/{gid}/{sid}")


@app.route("/<com>/<gid>/<sid>/confirmar", methods=["POST"])
def confirmar(com, gid, sid):
    carpeta(com, gid, sid)
    _, preguntas = banco(com, gid, sid)
    respuestas = {str(p["n"]): normal_resp(p, request.form.get(f"r{p['n']}"))
                  for p in preguntas if p["tipo"] != "abierta"}
    pts = num(request.form.get("abierta_pts") or 0)
    manual = {}
    for p in preguntas:
        valor = request.form.get(f"p{p['n']}", "").strip()
        if p["tipo"] != "abierta" and re.fullmatch(r"\d+([.,]\d+)?", valor):
            auto = p["pts"] if respuestas[str(p["n"])] == correcta(p) else 0
            if num(valor) != auto:
                manual[str(p["n"])] = max(0, min(p["pts"], num(valor)))
    total, _ = puntuar(preguntas, respuestas, pts, manual)
    guardar_estado(com, gid, sid, {
        "estado": "confirmado", "respuestas": respuestas, "abierta_pts": pts, "pts_manual": manual,
        "comentarios": {str(p["n"]): request.form[f"c{p['n']}"].strip() for p in preguntas
                        if request.form.get(f"c{p['n']}", "").strip()},
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
    _, preguntas = banco(com, gid, sid)
    total, detalle = puntuar(preguntas, est.get("respuestas", {}), est.get("abierta_pts", 0), est.get("pts_manual"))
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
        if pts and not ok:
            cuerpo += f'<p><b>Parcialmente correcta: {pts}/{p["pts"]}</b></p>'
        if est.get("comentarios", {}).get(str(p["n"])):
            cuerpo += f'<p><i>Comentario del profe:</i> {e(est["comentarios"][str(p["n"])])}</p>'
        clase, marca = ("ok", "✓") if pts == p["pts"] else ("parcial", "◐") if pts else ("mal", "✗")
        bloques += (f'<div class="preg {clase}"><div class="enun"><b>{p["n"]}.</b> {e(p["texto"])} '
                    f'<b>{marca}</b></div>{cuerpo}</div>')
    aviso = "" if est.get("estado") == "confirmado" else '<p class="err">Todavía sin confirmar por el docente.</p>'
    sub = f"{TITULO} · versión {version_de(com, gid, sid)}" if ITI else f"Cuestionario individual · {gid}"
    return pagina("Tu resultado", f"""<h1>{e(nombre_de(com, gid, sid))}</h1><p class="mut">{e(sub)}</p>
<div class="card"><span class="nota">{total}/{TOTAL}</span>{aviso}</div>{bloques}
<a class="btn" href="/{com}/{gid}/{sid}/registro.pdf">PDF del examen (para el mail)</a>
<a class="btn sec" href="/{com}/{gid}/{sid}">← volver a la revisión</a>{navegacion(com, gid, sid)}""")


REGISTROS = PARCIAL_DIR / "salida" / "registros"

CSS_REGISTRO = """
@page { size:A4; margin:16mm 15mm; }
body { font:10.5pt/1.4 system-ui, sans-serif; color:#111; margin:0; }
h1 { font-size:15pt; margin:0 0 2mm; } .mut { color:#555; font-size:9pt; }
.cab { border-bottom:1.5px solid #111; padding-bottom:3mm; margin-bottom:4mm; display:flex; justify-content:space-between; align-items:end; }
.nota { font-size:20pt; font-weight:700; white-space:nowrap; }
.preg { break-inside:avoid; border-left:3px solid #bbb; padding:1mm 0 1mm 3mm; margin:0 0 4mm; }
.preg.ok { border-color:#1d7a3a; } .preg.mal { border-color:#b3261e; } .preg.parcial { border-color:#a86400; }
.enun { font-weight:600; display:flex; justify-content:space-between; gap:4mm; } .pts { font-weight:700; white-space:nowrap; }
ul { list-style:none; padding:0; margin:1.5mm 0; } li { padding:.6mm 0 .6mm 6mm; position:relative; }
li .m { position:absolute; left:0; } li.marcada { font-weight:600; }
.tag { font-size:8.5pt; border:1px solid #999; border-radius:3px; padding:0 4px; margin-left:4px; font-weight:400; }
.tag.ok { border-color:#1d7a3a; color:#1d7a3a; } .tag.tuya { border-color:#24527a; color:#24527a; }
.expl { font-size:9.5pt; color:#333; margin:1mm 0; } .com { font-size:9.5pt; background:#f3f1ea; padding:1.5mm 2.5mm; margin:1mm 0; }
.trans { font-style:italic; background:#f6f6f6; padding:1.5mm 2.5mm; }
.anexo { break-before:page; } .anexo img { width:100%; max-height:250mm; object-fit:contain; display:block; margin:0 auto 4mm; break-inside:avoid; }
code { font-family:ui-monospace, monospace; font-size:.9em; }
"""


def registro_html(com, gid, sid, carpeta_fotos):
    """HTML imprimible con todo el examen corregido + las fotos de las carillas (registro para el estudiante)."""
    est = leer_estado(com, gid, sid)
    meta, preguntas = banco(com, gid, sid)
    total, detalle = puntuar(preguntas, est.get("respuestas", {}), est.get("abierta_pts", 0), est.get("pts_manual"))
    comentarios = est.get("comentarios", {})
    det = est.get("deteccion", {})
    bloques = ""
    for p, r, ok, pts in detalle:
        clase = "ok" if pts == p["pts"] else "parcial" if pts else "mal"
        cab = f'<div class="enun"><span>{p["n"]}. {e(p["texto"])}</span><span class="pts">{pts}/{p["pts"]}</span></div>'
        if p["tipo"] == "abierta":
            cuerpo = (f'<p class="mut">Lo que escribiste (transcripción de la hoja):</p>'
                      f'<p class="trans">{e(det.get("abierta_transcripcion") or "—")}</p>'
                      f'<p class="expl"><b>Qué se esperaba:</b> {e(p["se_espera"])}</p>')
            if est.get("abierta_comentario"):
                cuerpo += f'<p class="com"><b>Comentario del profe:</b> {e(est["abierta_comentario"])}</p>'
            bloques += f'<div class="preg {clase}">{cab}{cuerpo}</div>'
            continue
        marcadas = set(r.split(",")) if r and r != "?" else set()
        buenas = set(correcta(p).split(","))
        items = ""
        for i, (texto, _) in enumerate(p["opciones"]):
            clave = ("V" if i == 0 else "F") if p["tipo"] == "vf" else LETRAS[i]
            rotulo = texto if p["tipo"] == "vf" else f"{LETRAS[i]}) {e(texto)}"
            tuya, buena = clave in marcadas, clave in buenas
            marca = "☒" if tuya else "☐"
            tags = (' <span class="tag tuya">tu respuesta</span>' if tuya else "") + (' <span class="tag ok">correcta</span>' if buena else "")
            items += f'<li class="{"marcada" if tuya else ""}"><span class="m">{marca}</span>{rotulo}{tags}</li>'
        cuerpo = f"<ul>{items}</ul>" + ("" if marcadas else '<p class="expl">Sin respuesta.</p>')
        if pts < p["pts"]:
            cuerpo += f'<p class="expl"><b>Por qué:</b> {e(p["por_que"])}</p>'
        if comentarios.get(str(p["n"])):
            cuerpo += f'<p class="com"><b>Comentario del profe:</b> {e(comentarios[str(p["n"])])}</p>'
        bloques += f'<div class="preg {clase}">{cab}{cuerpo}</div>'
    fotos = "".join(f'<img src="{f.as_uri()}">' for f in sorted(carpeta_fotos.glob("foto-*.jpg")))
    estado = "" if est.get("estado") == "confirmado" else '<div class="mut">(borrador: todavía sin confirmar)</div>'
    return f"""<!doctype html><html lang="es"><head><meta charset="utf-8"><style>{CSS_REGISTRO}</style></head><body>
<div class="cab"><div><div class="mut">{TITULO} · {MATERIA} · {ETIQUETAS[com]} · Cuestionario individual</div>
<h1>{e(nombre_de(com, gid, sid))}</h1><div class="mut">{e(f"Versión {meta['version']}" if ITI else f"Grupo: {meta.get('sistema') or gid} ({gid})")}</div></div>
<div><div class="nota">{total}/{TOTAL}</div>{estado}</div></div>
{bloques}{f'<div class="anexo"><div class="mut">Anexo: tu examen escrito</div>{fotos}</div>' if fotos else ''}
</body></html>"""


@app.route("/<com>/<gid>/<sid>/registro.pdf")
def registro_pdf(com, gid, sid):
    d = carpeta(com, gid, sid)
    if leer_estado(com, gid, sid).get("estado") not in ("revisar", "confirmado"):
        abort(404)
    destino = REGISTROS / com / gid
    destino.mkdir(parents=True, exist_ok=True)
    tmp = destino / f".{sid}"
    tmp.mkdir(exist_ok=True)
    from PIL import Image
    for f in d.glob("foto-*.jpg"):  # fotos achicadas para que el PDF entre cómodo en un mail
        img = Image.open(f)
        img.thumbnail((1400, 1400))
        img.save(tmp / f.name, "JPEG", quality=70)
    html_tmp = tmp / "registro.html"
    html_tmp.write_text(registro_html(com, gid, sid, tmp))
    pdf = destino / f"{sid}.pdf"
    subprocess.run(["google-chrome", "--headless", "--disable-gpu", "--no-pdf-header-footer",
                    f"--print-to-pdf={pdf}", html_tmp.as_uri()], check=True, capture_output=True, timeout=120)
    shutil.rmtree(tmp)
    return send_file(pdf, mimetype="application/pdf", download_name=f"{slug(TITULO)}-{gid}-{sid}.pdf")


def filas_tabla(com):
    filas = []
    for gid in grupos(com):
        for sid, nombre in integrantes(com, gid):
            est = leer_estado(com, gid, sid)
            nota = ""
            if est.get("estado") in ("revisar", "confirmado"):
                _, preguntas = banco(com, gid, sid)
                nota, _ = puntuar(preguntas, est.get("respuestas", {}), est.get("abierta_pts", 0), est.get("pts_manual"))
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
<table><tr><th>Estudiante</th><th>Estado</th><th>/{TOTAL}</th></tr>{cuerpo}</table>
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
                    headers={"Content-Disposition": f"attachment; filename={slug(TITULO)}-{com}.csv"})


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
    print(f"\n{TITULO} — PIN: {PIN}")
    for placa, ip in ips_locales():
        print(f"  http://{ip}:{puerto}   ({placa})")
    print()
    app.run(host="0.0.0.0", port=puerto, debug=False, threaded=True)


if __name__ == "__main__":
    main()

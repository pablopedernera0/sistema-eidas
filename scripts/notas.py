#!/usr/bin/env python3
"""Tabla de notas de cierre de una materia: cuestionario individual (Classroom + Forms, /30)
más repo grupal (última devolución, /70), alumno por alumno. Solo lee Classroom y Forms.

La materia necesita sistema-eidas-datos/<materia>/classroom.json:
  {"curso": "<id>", "tarea_cuestionario": "<id>", "form_cuestionario": "<id>",
   "nombre_cuestionario": "..."}
(ids con `classroom.py cursos` / `tareas <curso>`). Escribe
sistema-eidas-datos/<materia>/notas-cierre-2c-2026.csv. Lo usa también el dashboard (/notas).

Uso: notas.py <materia>        (con /usr/bin/python3, ver dashboard.md)
"""
import csv
import json
import re
import sys
import unicodedata
from pathlib import Path

import classroom

ROOT = Path(__file__).resolve().parent.parent
MATERIAS_DIR = ROOT / "materias"
DATOS_DIR = ROOT.parent / "sistema-eidas-datos"
FECHA_RE = re.compile(r"^\d{4}-\d{2}-\d{2}\.md$")
SUBTOTAL_RE = re.compile(r"Subtotal repo\*{0,2}\s*\|\s*\*{0,2}(\d+)")
# En el Form, 10 o menos es solo la parte que se corrige sola: la respuesta no se corrigió
MINIMO_CORREGIDO = 10
CAMPOS = [
    "Alumno", "Mail", "Grupo", "Cuestionario (/100)", "Cuestionario (/30)",
    "Repo grupal (/70)", "Repo: devolución", "Total (/100)", "Estado del cuestionario",
]


def config(materia):
    path = DATOS_DIR / materia / "classroom.json"
    return json.loads(path.read_text()) if path.exists() else None


def csv_path(materia):
    return DATOS_DIR / materia / "notas-cierre-2c-2026.csv"


def normalizar(texto):
    return "".join(c for c in unicodedata.normalize("NFD", texto.lower()) if unicodedata.category(c) != "Mn")


def grupos_y_repo(materia):
    """{grupo: (texto normalizado de integrantes.md, dígitos de DNI, (nota repo, devolución, publicada))}"""
    grupos = json.loads((MATERIAS_DIR / materia / "grupos.json").read_text())["grupos"]
    datos = {}
    for g in grupos:
        integrantes = MATERIAS_DIR / materia / "grupos" / g["id"] / "integrantes.md"
        texto = integrantes.read_text() if integrantes.exists() else ""
        # El DNI a veces está con puntos (44.783.419)
        dnis = set(re.findall(r"\b\d{7,8}\b", texto.replace(".", "")))
        carpeta = DATOS_DIR / materia / "borradores" / g["id"]
        repo = (None, "", False)
        if carpeta.exists():
            fechas = sorted(f for f in carpeta.iterdir() if FECHA_RE.match(f.name))
            if fechas:
                t = fechas[-1].read_text()
                m = SUBTOTAL_RE.search(t)
                repo = (int(m.group(1)) if m else None, fechas[-1].stem, "- [x] Publicado al grupo" in t)
        datos[g["id"]] = (normalizar(texto), dnis, repo)
    return datos


def grupo_de(nombre, email, grupos):
    """Por DNI (el mail es <DNI>@...) y, si no, por apellido + otro nombre en integrantes.md."""
    dni = email.split("@")[0]
    por_dni = [g for g, (_, dnis, _) in grupos.items() if dni in dnis]
    if len(por_dni) == 1:
        return por_dni[0]
    palabras = [w for w in normalizar(nombre).split() if len(w) > 3]
    if not palabras:
        return ""

    def esta(w, texto):
        return re.search(rf"\b{re.escape(w)}\b", texto)

    candidatos = [g for g, (t, _, _) in grupos.items()
                  if esta(palabras[0], t) and any(esta(w, t) for w in palabras[1:])]
    if not candidatos:
        candidatos = [g for g, (t, _, _) in grupos.items() if esta(palabras[0], t)]
    return candidatos[0] if len(candidatos) == 1 else ""


def notas_cierre(materia):
    cfg = config(materia)
    if cfg is None:
        raise SystemExit(f"Falta {DATOS_DIR / materia / 'classroom.json'}")
    cr = classroom.servicio()
    curso = cfg["curso"]
    respuestas, _, _ = classroom.respuestas_form(cfg["form_cuestionario"])
    form = {email: puntaje for email, puntaje, _ in respuestas}
    alumnos = {
        a["userId"]: (a["profile"]["name"]["fullName"], a["profile"].get("emailAddress", ""))
        for a in classroom.todas(lambda **kw: cr.courses().students().list(courseId=curso, **kw), "students")
    }
    entregas = {
        s["userId"]: s
        for s in classroom.todas(
            lambda **kw: cr.courses().courseWork().studentSubmissions().list(
                courseId=curso, courseWorkId=cfg["tarea_cuestionario"], **kw),
            "studentSubmissions",
        )
    }
    grupos = grupos_y_repo(materia)

    filas = []
    for uid, (nombre, email) in sorted(alumnos.items(), key=lambda x: x[1][0]):
        s = entregas.get(uid, {})
        respondio = s.get("state") in ("RETURNED", "TURNED_IN") or email in form
        nota_classroom = s.get("assignedGrade", s.get("draftGrade")) if respondio else None
        nota_form = form.get(email)
        if nota_form is not None and nota_form <= MINIMO_CORREGIDO:
            nota_form = None
        nota = nota_classroom if nota_classroom is not None else nota_form

        if not respondio:
            estado = "no respondió"
        elif nota is None:
            estado = "falta corregir"
        elif s.get("state") == "RETURNED":
            estado = "corregido y devuelto en Classroom"
        elif nota_classroom is not None:
            estado = "corregido, falta devolver en Classroom"
        else:
            estado = "corregido en Forms, falta importar a Classroom"

        grupo = grupo_de(nombre, email, grupos)
        repo, devolucion, publicada = grupos[grupo][2] if grupo else (None, "", False)
        sobre_30 = round(nota * 0.3, 1) if nota is not None else None
        total = round(sobre_30 + repo, 1) if sobre_30 is not None and repo is not None else None
        filas.append({
            "Alumno": nombre, "Mail": email, "Grupo": grupo,
            "Cuestionario (/100)": "" if nota is None else nota,
            "Cuestionario (/30)": "" if sobre_30 is None else sobre_30,
            "Repo grupal (/70)": "" if repo is None else repo,
            "Repo: devolución": f"{devolucion}{'' if publicada else ' (sin publicar)'}" if devolucion else "",
            "Total (/100)": "" if total is None else total,
            "Estado del cuestionario": estado,
        })
    return filas


def guardar(materia, filas):
    with open(csv_path(materia), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS)
        w.writeheader()
        w.writerows(filas)


def leer(materia):
    path = csv_path(materia)
    if not path.exists():
        return None
    with open(path) as f:
        return list(csv.DictReader(f))


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    materia = sys.argv[1]
    filas = notas_cierre(materia)
    guardar(materia, filas)
    estados = {}
    for f in filas:
        estados[f["Estado del cuestionario"]] = estados.get(f["Estado del cuestionario"], 0) + 1
    print(f"{len(filas)} alumnos → {csv_path(materia)}")
    for e, n in estados.items():
        print(f"  {n:3}  {e}")


if __name__ == "__main__":
    main()

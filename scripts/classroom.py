#!/usr/bin/env python3
"""Lectura de Google Classroom por API — SOLO LECTURA (prueba del 15/10/2026).

Usa scopes .readonly: no puede crear, calificar ni devolver nada aunque se lo pida.
El cliente OAuth (tipo "App de escritorio", proyecto sistema-eidas de Google Cloud) vive en
sistema-eidas-datos/classroom/oauth-client.json (repo privado, viaja entre máquinas). El token
de la cuenta docente queda solo en esta máquina, en ~/.config/sistema-eidas/classroom-token.json:
la primera vez abre el navegador para autorizar (loguearse con la cuenta del terciario).

Uso (con /usr/bin/python3, ver dashboard.md):
  classroom.py cursos                       lista los cursos donde sos docente
  classroom.py tareas <curso-id>            tareas del curso, con fecha de entrega
  classroom.py entregas <curso-id> [filtro] estado de entrega y nota por alumno, de cada tarea
                                            (filtro: parte del título de la tarea)
  classroom.py form <form-id>               respuestas de un Form (cuestionario) con su puntaje
"""
import os
import sys
import warnings
from pathlib import Path

# Google devuelve classroom.student-submissions.students.readonly (nombre viejo, equivalente) en
# vez de coursework.students.readonly, y oauthlib lo toma como error si no se relaja el chequeo
os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "1"
warnings.filterwarnings("ignore", category=FutureWarning)

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

ROOT = Path(__file__).resolve().parent.parent
CLIENTE = ROOT.parent / "sistema-eidas-datos" / "classroom" / "oauth-client.json"
# El nombre cambia cuando cambian los SCOPES, así se vuelve a autorizar solo
TOKEN = Path.home() / ".config" / "sistema-eidas" / "classroom-token-v2.json"
SCOPES = [
    "https://www.googleapis.com/auth/classroom.courses.readonly",
    "https://www.googleapis.com/auth/classroom.rosters.readonly",
    "https://www.googleapis.com/auth/classroom.profile.emails",
    "https://www.googleapis.com/auth/classroom.coursework.students.readonly",
    "https://www.googleapis.com/auth/forms.body.readonly",
    "https://www.googleapis.com/auth/forms.responses.readonly",
]

ESTADOS = {
    "NEW": "sin abrir",
    "CREATED": "sin entregar",
    "TURNED_IN": "entregada",
    "RETURNED": "devuelta",
    "RECLAIMED_BY_STUDENT": "retirada por el alumno",
}


def credenciales():
    creds = Credentials.from_authorized_user_file(TOKEN, SCOPES) if TOKEN.exists() else None
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    elif not creds or not creds.valid:
        if not CLIENTE.exists():
            raise SystemExit(f"Falta el cliente OAuth en {CLIENTE}")
        flow = InstalledAppFlow.from_client_secrets_file(CLIENTE, SCOPES)
        creds = flow.run_local_server(port=0, login_hint="pedernera.pablo@terciariourquiza.edu.ar")
    TOKEN.parent.mkdir(parents=True, exist_ok=True)
    TOKEN.write_text(creds.to_json())
    TOKEN.chmod(0o600)
    return creds


def servicio():
    return build("classroom", "v1", credentials=credenciales(), cache_discovery=False)


def servicio_forms():
    return build("forms", "v1", credentials=credenciales(), cache_discovery=False)


def respuestas_form(form_id):
    """[(email, puntaje total, fecha)] de un Form en modo cuestionario, más el puntaje máximo."""
    fs = servicio_forms()
    form = fs.forms().get(formId=form_id).execute()
    maximo = sum(
        i["questionItem"]["question"].get("grading", {}).get("pointValue", 0)
        for i in form.get("items", []) if "questionItem" in i
    )
    resps = todas(lambda **kw: fs.forms().responses().list(formId=form_id, **kw), "responses")
    return [(r.get("respondentEmail", "?"), r.get("totalScore"), r.get("lastSubmittedTime", "")[:10])
            for r in resps], maximo, form["info"]["title"]


def form(form_id):
    filas, maximo, titulo = respuestas_form(form_id)
    print(f"## {titulo}  ({len(filas)} respuestas, puntaje máximo {maximo})")
    for email, puntaje, cuando in sorted(filas):
        print(f"  {email:45} {'—' if puntaje is None else puntaje:>6}  {cuando}")


def todas(pedido, clave):
    """Recorre todas las páginas de un list() de la API."""
    items, token = [], None
    while True:
        r = pedido(pageToken=token).execute()
        items += r.get(clave, [])
        token = r.get("nextPageToken")
        if not token:
            return items


def cursos(cr):
    for c in todas(lambda **kw: cr.courses().list(teacherId="me", **kw), "courses"):
        print(f"{c['id']}  [{c['courseState']}]  {c['name']}" + (f" — {c['section']}" if c.get("section") else ""))


def fecha(t):
    d = t.get("dueDate")
    return f"{d['day']:02d}/{d['month']:02d}/{d['year']}" if d else "sin fecha"


def tareas(cr, curso):
    for t in todas(lambda **kw: cr.courses().courseWork().list(courseId=curso, **kw), "courseWork"):
        puntos = t.get("maxPoints", "—")
        print(f"{t['id']}  vence {fecha(t)}  /{puntos}  {t['title']}")


def entregas(cr, curso, filtro=None):
    alumnos = {
        a["userId"]: a["profile"]["name"]["fullName"]
        for a in todas(lambda **kw: cr.courses().students().list(courseId=curso, **kw), "students")
    }
    for t in todas(lambda **kw: cr.courses().courseWork().list(courseId=curso, **kw), "courseWork"):
        if filtro and filtro.lower() not in t["title"].lower():
            continue
        subs = todas(
            lambda **kw: cr.courses().courseWork().studentSubmissions().list(
                courseId=curso, courseWorkId=t["id"], **kw),
            "studentSubmissions",
        )
        print(f"\n## {t['title']}  (vence {fecha(t)}, /{t.get('maxPoints', '—')})")
        for s in sorted(subs, key=lambda s: alumnos.get(s["userId"], "")):
            nota = s.get("assignedGrade", s.get("draftGrade"))
            borrador = " (borrador)" if "assignedGrade" not in s and "draftGrade" in s else ""
            tarde = " · tarde" if s.get("late") else ""
            print(f"  {alumnos.get(s['userId'], s['userId'])[:35]:35}  "
                  f"{ESTADOS.get(s['state'], s['state']):22}  "
                  f"{'—' if nota is None else nota}{borrador}{tarde}")


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in {"cursos", "tareas", "entregas", "form"}:
        raise SystemExit(__doc__)
    if sys.argv[1] == "form":
        if len(sys.argv) < 3:
            raise SystemExit(__doc__)
        return form(sys.argv[2])
    cr = servicio()
    if sys.argv[1] == "cursos":
        cursos(cr)
    elif len(sys.argv) < 3:
        raise SystemExit(__doc__)
    elif sys.argv[1] == "tareas":
        tareas(cr, sys.argv[2])
    else:
        entregas(cr, sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)


if __name__ == "__main__":
    main()

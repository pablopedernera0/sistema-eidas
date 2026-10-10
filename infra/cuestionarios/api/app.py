#!/usr/bin/env python3
"""API del stack de cuestionarios: única dueña de la base SQLite.

Los alumnos responden en github.io (caso-bicirio/v2/?cuestionario=<id>) y mandan sus
respuestas por mail. N8N baja esos mails de Gmail y se los pasa a esta API, que saca
la línea `DATOS: {...}` de cada uno, corrige con la clave del JSON publicado y guarda.
El CSV que N8N sube a Drive sale de acá. Solo biblioteca estándar.

Endpoints (todos bajo /api):
  GET  /cuestionarios                     lista, con cantidad de respuestas y última corrida
  POST /cuestionarios {"id": ...}         agrega un cuestionario a controlar
  GET  /cuestionarios/<id>                detalle, con el id del CSV en Drive
  POST /cuestionarios/<id>/ingesta        mails de una corrida de N8N (ver ingesta())
  GET  /cuestionarios/<id>/respuestas     respuestas corregidas, para el dashboard
  GET  /cuestionarios/<id>/corridas       historial de corridas
  GET  /cuestionarios/<id>/csv            planilla para Drive
  POST /cuestionarios/<id>/drive {"file_id": ...}   N8N guarda el CSV que creó
"""
import csv
import io
import json
import os
import re
import sqlite3
import sys
import urllib.request
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

DB = os.environ.get('DB', '/datos/cuestionarios.db')
SITIO = os.environ.get('SITIO', 'https://pablopedernera0.github.io/caso-bicirio/v2/cuestionarios')
ID_RE = re.compile(r'^[a-z0-9-]+$')
DATOS_RE = re.compile(r'DATOS:\s*(\{.*)')


def ahora():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def conectar():
    con = sqlite3.connect(DB, timeout=10)
    con.row_factory = sqlite3.Row
    con.execute('PRAGMA foreign_keys = ON')
    return con


def crear_tablas():
    os.makedirs(os.path.dirname(DB), exist_ok=True)
    with conectar() as con:
        con.executescript('''
            CREATE TABLE IF NOT EXISTS cuestionarios (
                id TEXT PRIMARY KEY,
                titulo TEXT NOT NULL,
                clave TEXT NOT NULL,          -- JSON publicado, con las correctas
                drive_file_id TEXT,
                agregado TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS corridas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cuestionario TEXT NOT NULL REFERENCES cuestionarios(id),
                fecha TEXT NOT NULL,
                mails INTEGER NOT NULL,
                nuevas INTEGER NOT NULL,
                repetidas INTEGER NOT NULL,
                problemas TEXT NOT NULL       -- JSON: [{de, asunto, motivo}]
            );
            CREATE TABLE IF NOT EXISTS respuestas (
                cuestionario TEXT NOT NULL REFERENCES cuestionarios(id),
                nombre TEXT NOT NULL,
                comision TEXT NOT NULL,
                fin TEXT NOT NULL,            -- hora en que el alumno tocó Finalizar
                r TEXT NOT NULL,              -- JSON {num: letra}
                puntos INTEGER NOT NULL,
                remitente TEXT,
                message_id TEXT,
                corrida INTEGER REFERENCES corridas(id),
                recibido TEXT NOT NULL,
                PRIMARY KEY (cuestionario, nombre, fin)
            );
        ''')


def bajar_json(qid):
    with urllib.request.urlopen(f'{SITIO}/{qid}.json', timeout=20) as r:
        return json.loads(r.read().decode('utf-8'))


def leer_clave(con, qid, refrescar=False):
    """Clave del cuestionario. Al procesar se vuelve a bajar por si se corrigió alguna
    pregunta; si github.io no responde, sirve la última guardada."""
    fila = con.execute('SELECT clave FROM cuestionarios WHERE id = ?', (qid,)).fetchone()
    if refrescar:
        try:
            q = bajar_json(qid)
            con.execute('UPDATE cuestionarios SET clave = ?, titulo = ? WHERE id = ?',
                        (json.dumps(q, ensure_ascii=False), q.get('titulo', qid), qid))
            return q
        except Exception as e:
            print(f'No pude bajar {qid}.json, uso la clave guardada: {e}', file=sys.stderr)
    return json.loads(fila['clave'])


def puntaje(q, r):
    return sum(p['puntos'] for p in q['preguntas'] if r.get(str(p['num'])) in p['correctas'])


def extraer_datos(texto):
    """Todas las líneas DATOS de un texto. Si el correo partió la línea en varias, las
    junta hasta que el JSON cierre (el cuestionario escribe los espacios como \\u0020
    justamente para que no se parta, pero un .txt viejo sí tiene espacios)."""
    salida, lineas = [], texto.replace('\r\n', '\n').split('\n')
    for i, linea in enumerate(lineas):
        m = DATOS_RE.search(linea)
        if not m and linea.strip() == 'DATOS:' and lineas[i + 1:i + 2] and lineas[i + 1].lstrip().startswith('{'):
            # Algunos clientes de correo cortan justo después de "DATOS:" y el JSON queda abajo.
            m = DATOS_RE.search('DATOS: ' + lineas.pop(i + 1).strip())
        if not m:
            continue
        # Los correos parten en un espacio, así que se vuelve a juntar con un espacio.
        crudo, datos = m.group(1).strip(), None
        for siguiente in [None] + lineas[i + 1:i + 8]:
            if siguiente is not None:
                crudo += ' ' + siguiente.strip()
            try:
                datos = json.loads(crudo)
                break
            except json.JSONDecodeError:
                pass
        salida.append(datos)
    return salida


def ingesta(con, qid, cuerpo):
    """cuerpo = {"mensajes": [{"id", "de", "asunto", "texto", "adjuntos": [texto, ...]}]}
    Devuelve el resumen y en `procesados` los mails que N8N tiene que etiquetar como
    `procesado`: solo los que trajeron respuestas de este cuestionario y ningún problema.
    Los demás quedan sin etiqueta y vuelven a aparecer en cada corrida hasta que el
    docente los resuelva a mano (un mail de otro cuestionario lo levanta ese otro)."""
    q = leer_clave(con, qid, refrescar=True)
    mensajes = [m for m in cuerpo.get('mensajes', []) if m.get('id')]
    cur = con.execute('INSERT INTO corridas (cuestionario, fecha, mails, nuevas, repetidas, problemas) '
                      'VALUES (?, ?, ?, 0, 0, ?)', (qid, ahora(), len(mensajes), '[]'))
    corrida = cur.lastrowid
    nuevas = repetidas = 0
    problemas, procesados = [], []
    for m in mensajes:
        antes = len(problemas)
        textos = [m.get('texto') or ''] + list(m.get('adjuntos') or [])
        hallados = [d for t in textos for d in extraer_datos(t)]
        if not hallados:
            problemas.append(dict(de=m.get('de', ''), asunto=m.get('asunto', ''), motivo='no tiene la línea DATOS'))
            continue
        for d in hallados:
            if d is None:
                problemas.append(dict(de=m.get('de', ''), asunto=m.get('asunto', ''), motivo='la línea DATOS está cortada'))
                continue
            if d.get('id') != qid:
                problemas.append(dict(de=m.get('de', ''), asunto=m.get('asunto', ''), motivo=f'es de otro cuestionario ({d.get("id")})'))
                continue
            nombre, fin = (d.get('nombre') or '').strip(), d.get('fin') or ''
            if not nombre or not fin:
                problemas.append(dict(de=m.get('de', ''), asunto=m.get('asunto', ''), motivo='falta el nombre o la hora de finalización'))
                continue
            r = {str(k): v for k, v in (d.get('r') or {}).items()}
            cur = con.execute(
                'INSERT OR IGNORE INTO respuestas (cuestionario, nombre, comision, fin, r, puntos, remitente, message_id, corrida, recibido) '
                'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                (qid, nombre, d.get('comision') or '', fin, json.dumps(r), puntaje(q, r),
                 m.get('de', ''), m['id'], corrida, ahora()))
            if cur.rowcount:
                nuevas += 1
            else:
                repetidas += 1
        if len(problemas) == antes:
            procesados.append(m['id'])
    con.execute('UPDATE corridas SET nuevas = ?, repetidas = ?, problemas = ? WHERE id = ?',
                (nuevas, repetidas, json.dumps(problemas, ensure_ascii=False), corrida))
    return dict(corrida=corrida, mails=len(mensajes), nuevas=nuevas, repetidas=repetidas,
                problemas=problemas, procesados=procesados)


def respuestas(con, qid):
    q = leer_clave(con, qid)
    filas = con.execute('SELECT * FROM respuestas WHERE cuestionario = ? ORDER BY comision, nombre', (qid,)).fetchall()
    salida = []
    for f in filas:
        r = json.loads(f['r'])
        marcas = []
        for p in q['preguntas']:
            dada = r.get(str(p['num']), '')
            marcas.append('ok' if dada in p['correctas'] else (dada or '-'))
        salida.append(dict(nombre=f['nombre'], comision=f['comision'], fin=f['fin'], puntos=f['puntos'],
                           total=q['total'], remitente=f['remitente'], recibido=f['recibido'], marcas=marcas))
    return q, salida


def planilla(con, qid):
    """Mismas columnas que el CSV del corrector de la página, más el remitente."""
    q, filas = respuestas(con, qid)
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(['nombre', 'comision', 'finalizado', f'puntaje/{q["total"]}']
               + [f'P{p["num"]}' for p in q['preguntas']] + ['remitente'])
    for f in filas:
        w.writerow([f['nombre'], f['comision'], f['fin'], f['puntos']] + f['marcas'] + [f['remitente']])
    return '﻿' + buf.getvalue()


def resumen(con, fila):
    n = con.execute('SELECT COUNT(*) FROM respuestas WHERE cuestionario = ?', (fila['id'],)).fetchone()[0]
    ult = con.execute('SELECT fecha, mails, nuevas FROM corridas WHERE cuestionario = ? ORDER BY id DESC LIMIT 1',
                      (fila['id'],)).fetchone()
    return dict(id=fila['id'], titulo=fila['titulo'], agregado=fila['agregado'], drive_file_id=fila['drive_file_id'],
                respuestas=n, ultima_corrida=dict(ult) if ult else None)


class Handler(BaseHTTPRequestHandler):
    def responder(self, codigo, cuerpo, tipo='application/json; charset=utf-8'):
        datos = cuerpo.encode('utf-8') if isinstance(cuerpo, str) else json.dumps(cuerpo, ensure_ascii=False).encode('utf-8')
        self.send_response(codigo)
        self.send_header('Content-Type', tipo)
        self.send_header('Content-Length', str(len(datos)))
        self.end_headers()
        self.wfile.write(datos)

    def error(self, codigo, msg):
        self.responder(codigo, {'error': msg})

    def leer_cuerpo(self):
        n = int(self.headers.get('Content-Length') or 0)
        return json.loads(self.rfile.read(n) or b'{}')

    def ruta(self):
        partes = [p for p in self.path.split('?')[0].split('/') if p]
        if partes[:2] != ['api', 'cuestionarios']:
            return None
        return partes[2:]

    def existe(self, con, qid):
        return con.execute('SELECT * FROM cuestionarios WHERE id = ?', (qid,)).fetchone()

    def do_GET(self):
        p = self.ruta()
        if p is None:
            return self.error(404, 'no existe')
        with conectar() as con:
            if not p:
                filas = con.execute('SELECT * FROM cuestionarios ORDER BY agregado DESC').fetchall()
                return self.responder(200, [resumen(con, f) for f in filas])
            fila = self.existe(con, p[0])
            if not fila:
                return self.error(404, f'No se controla el cuestionario {p[0]}')
            if len(p) == 1:
                return self.responder(200, resumen(con, fila))
            if p[1:] == ['respuestas']:
                q, filas = respuestas(con, p[0])
                return self.responder(200, dict(preguntas=[x['num'] for x in q['preguntas']], total=q['total'], respuestas=filas))
            if p[1:] == ['corridas']:
                filas = con.execute('SELECT * FROM corridas WHERE cuestionario = ? ORDER BY id DESC', (p[0],)).fetchall()
                return self.responder(200, [dict(f, problemas=json.loads(f['problemas'])) for f in filas])
            if p[1:] == ['csv']:
                return self.responder(200, planilla(con, p[0]), 'text/csv; charset=utf-8')
        self.error(404, 'no existe')

    def do_POST(self):
        p = self.ruta()
        if p is None:
            return self.error(404, 'no existe')
        try:
            cuerpo = self.leer_cuerpo()
        except json.JSONDecodeError:
            return self.error(400, 'El cuerpo no es JSON')
        with conectar() as con:
            if not p:
                qid = str(cuerpo.get('id', '')).strip()
                if not ID_RE.match(qid):
                    return self.error(400, 'El id va en minúsculas, números y guiones (como en el link ?cuestionario=)')
                if self.existe(con, qid):
                    return self.error(409, f'{qid} ya está en la lista')
                try:
                    q = bajar_json(qid)
                except Exception as e:
                    return self.error(404, f'No encontré {qid}.json en github.io ({e})')
                con.execute('INSERT INTO cuestionarios (id, titulo, clave, agregado) VALUES (?, ?, ?, ?)',
                            (qid, q.get('titulo', qid), json.dumps(q, ensure_ascii=False), ahora()))
                return self.responder(201, resumen(con, self.existe(con, qid)))
            if not self.existe(con, p[0]):
                return self.error(404, f'No se controla el cuestionario {p[0]}')
            if p[1:] == ['ingesta']:
                return self.responder(200, ingesta(con, p[0], cuerpo))
            if p[1:] == ['drive']:
                con.execute('UPDATE cuestionarios SET drive_file_id = ? WHERE id = ?', (cuerpo.get('file_id'), p[0]))
                return self.responder(200, {'ok': True})
        self.error(404, 'no existe')

    def log_message(self, fmt, *args):
        sys.stderr.write(f'{self.command} {self.path} -> {args[1] if len(args) > 1 else ""}\n')


if __name__ == '__main__':
    crear_tablas()
    puerto = int(os.environ.get('PORT', '8000'))
    print(f'API de cuestionarios en :{puerto}, base {DB}', file=sys.stderr)
    ThreadingHTTPServer(('0.0.0.0', puerto), Handler).serve_forever()

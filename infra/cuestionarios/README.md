# Cuestionarios por mail

Junta las respuestas de los cuestionarios de `caso-bicirio/v2/?cuestionario=<id>` que
los estudiantes mandan por mail, las corrige y deja una planilla por cuestionario en Drive.

```
estudiante ──mail──▶ Gmail ◀── N8N ──▶ api (SQLite) ──▶ CSV ──▶ Drive
                                 ▲
         dashboard (nginx) ──────┘  botón "Procesar mails"
```

- El cuestionario tiene que tener `envio_mail:` en su banco (`sistema-eidas-datos/cuestionarios/<id>.md`).
  Al finalizar, la página arma el mail: asunto `[<id>] Nombre – comisión` y en el cuerpo
  la línea `DATOS: {...}`. También se leen los `.txt` adjuntos del formato viejo.
- **N8N** busca `subject:"[<id>]" -label:procesado` (Gmail ignora los corchetes, así que también trae
  asuntos parecidos: la API descarta lo que es de otro cuestionario), le pasa los mails a la API,
  etiqueta como `procesado` los que salieron bien y sube o actualiza `<id>-respuestas.csv` en la raíz del Drive.
- **api** (`api/app.py`, solo biblioteca estándar) es la única que toca la base `datos/cuestionarios.db`:
  cuestionarios a controlar, respuestas (sin repetidos: nombre + hora de finalización) y corridas.
  Corrige con la clave del JSON publicado en github.io, que vuelve a bajar en cada corrida.
- Un mail con problemas (sin `DATOS`, cortado, de otro cuestionario) **no** se etiqueta: aparece
  en la corrida del dashboard cada vez hasta que lo resolvés a mano en Gmail.

## Uso

```bash
infra/cuestionarios/levantar.sh     # N8N + flujo + api + dashboard
```

Dashboard en http://localhost:8430: agregar el id del cuestionario (el del link), **Procesar mails**,
**Ver respuestas**, bajar el CSV o abrirlo en Drive.

`datos/` tiene nombres y notas de estudiantes: no está en git y vive solo en la máquina donde se
procesa. Si se pierde, se reconstruye sacando la etiqueta `procesado` en Gmail y procesando de nuevo.

## Archivos

| Archivo | Qué es |
|---|---|
| `docker-compose.yml` | `api` (python:3.12-slim) y `nginx`, colgados de la red de `infra/n8n` |
| `nginx.conf` | `/` dashboard, `/api/` la API, `/procesar` el webhook de N8N |
| `workflows/procesar-cuestionario.json` | flujo de N8N; usa las credenciales "Gmail account" y "Google Drive account" |
| `levantar.sh` | levanta todo e importa/publica el flujo si falta |

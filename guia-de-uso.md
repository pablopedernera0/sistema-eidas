# Guía de uso — Sistema EIDAS

> Cómo operar el sistema hoy, con el estado real de cada pieza (qué está automatizado
> y qué todavía requiere pasos manuales). El sistema es multi-materia: casi todos los
> comandos toman `<materia>` como primer argumento — es el nombre de carpeta dentro de
> `materias/` (ej: `af-diseno-sistemas-web-31`). Ver `CLAUDE.md` para el diseño completo y
> `materias/<materia>/rubrica.md` / `marco-teorico-fundamentacion.md` para el fundamento de
> cada decisión. Versión de un vistazo de esta guía (comandos y advertencias, sin el
> detalle completo): [cheat sheet del docente](https://pablopedernera0.github.io/eidas-cheatsheet/).

---

## Mapa: qué uso para qué

Desde octubre de 2026 EIDAS dejó de ser solo "repos + devoluciones": también lee Classroom y
Forms, tiene cuestionarios propios en github.io y un dashboard que junta todo. Si no sabés
por dónde arrancar, buscá lo que querés hacer acá:

| Quiero... | Voy a... | Detalle |
|---|---|---|
| Ver en qué estado está cada grupo (evaluado, aprobado, publicado) | Dashboard → **Grupos** (`/dashboard`, http://127.0.0.1:8420) | sección 6 |
| Leer los repos de los grupos sin abrir GitHub | Dashboard → **Recorrer**: por grupo o por sección | sección 6 |
| Traer los últimos cambios de los grupos | Botón **↻ actualizar** en Recorrer, o `/sync <materia>` | sección 2 |
| Evaluar un grupo y publicarle la devolución | `/evaluar-grupo` → revisar el borrador → `/publicar` | sección 3 |
| Ver las notas por alumno (cuestionario + repo, o tareas de Classroom) | Dashboard → **Notas** (botón **↻ traer de Classroom y Forms**) | sección 4 |
| Consultar Classroom sin abrirlo (cursos, tareas, entregas, respuestas de un Form) | `scripts/classroom.py` | sección 4 |
| Armar un cuestionario o simulacro para que practiquen | banco en `sistema-eidas-datos/cuestionarios/` + `scripts/cuestionario.py generar` | sección 5 |
| Juntar las respuestas que los alumnos mandan por mail | colector `infra/cuestionarios/` (http://localhost:8430) | sección 5 |
| Saber si esta máquina está al día | `/estado-eidas` | — |
| Preparar una máquina nueva (la notebook) | checklist | sección 7 |

**Dónde vive cada cosa, en una línea:** el código en `sistema-eidas` (público); todo lo que
tiene datos de alumnos o la clave de algo en `sistema-eidas-datos` (privado: borradores,
`grupos.json`, notas, bancos de cuestionarios, secretos de N8N y de Classroom); lo que ven
los alumnos en `pablopedernera0.github.io` (cuestionarios publicados) y en el repo de cada
grupo (devoluciones). Las notas y comentarios de Classroom/Forms siguen viviendo en Google.

---

## Comandos, de un vistazo

Hay dos familias de comandos que no hay que confundir: los que corrés en la terminal
(`python3 scripts/grupos.py ...`) y los que corrés dentro de Claude Code (`/comando`, sin
`python3`). Ninguno de los `grupos.py` tiene un modo "dry-run" — el chequeo de solo lectura
es un comando de Claude Code aparte, no un flag.

`sync` es el único de los tres subcomandos de `grupos.py` que además tiene un wrapper de
Claude Code (`/sync`) — así no hace falta abrir una terminal aparte solo para traer los
repos al día antes de chequear o evaluar. `publicar` y `notificar` **no** tienen wrapper,
a propósito: `publicar` pide una confirmación antes de un push que hace visible la
devolución y dispara un mail — envolverlo significaría pasarle `--yes` para que no quede
esperando input, y ese prompt es el último freno antes de algo que no se puede deshacer.

| Quiero... | Comando | Tipo | ¿Escribe algo? |
|---|---|---|---|
| Traer/actualizar los repos de los grupos | `python3 scripts/grupos.py sync <materia>` o `/sync <materia>` | Python o Claude Code (mismo resultado) | Clona/actualiza repos en `materias/<materia>/grupos/` |
| Ver si un grupo está listo para evaluar, sin generar nada todavía (el "dry-run") | `/chequear-grupo <materia> <grupo-id>` | Claude Code | Actualiza `main` con `git pull`, pero no genera devolución — solo reporta en el chat |
| Ver cómo trabajó el grupo a lo largo del tiempo (iteración, no aporte) | `/resumen-commits <materia> <grupo-id>` | Claude Code | No — solo reporta en el chat, no entra en la devolución |
| Generar el borrador de devolución | `/evaluar-grupo <materia> <grupo-id>` | Claude Code | Sí — commitea y pushea en `sistema-eidas-datos` (repo privado, no el del grupo) |
| Publicar la devolución y notificar al grupo | `python3 scripts/grupos.py publicar <materia> <grupo-id>` | Python | Sí — commit directo a `main` del repo del grupo y `git push` |
| Reintentar solo la notificación (si publicar no la disparó) | `python3 scripts/grupos.py notificar <materia> <grupo-id> <fecha>` | Python | No sobre el repo — dispara el webhook de N8N |
| Ver si esta máquina tiene todo al día (`sistema-eidas`, `sistema-eidas-datos`, `sistema-eidas-memory`, `eidas-template`) | `/estado-eidas` (sin argumentos) | Claude Code | Pullea solo lo que esté limpio y atrasado; lo demás solo lo reporta |
| Abrir el dashboard (Grupos, Recorrer, Notas, Cronograma) | `/dashboard` | Claude Code | No, salvo los botones de actualizar (pull de los clones y regenerar la tabla de notas) |
| Leer Classroom: cursos, tareas, entregas, respuestas de un Form | `classroom.py cursos` / `tareas <curso>` / `entregas <curso> [filtro]` / `form <form-id>` | Python | No: solo lectura (permisos `.readonly`) |
| Regenerar la tabla de notas de una materia | `notas.py <materia>` (o el botón en Notas) | Python | Sí: el CSV de notas en `sistema-eidas-datos/<materia>/` (no hace commit) |
| Publicar un cuestionario en github.io | `cuestionario.py generar <banco.md> --sitio <…/caso-bicirio/v2/cuestionarios>` | Python | Sí: el JSON en el repo de github.io (el commit es aparte) |
| Corregir respuestas de un cuestionario (.txt) | `cuestionario.py corregir <banco.md> <archivos…>` | Python | No |

**Ojo con el Python:** en la PC, la terminal tiene activado el venv de `santafe-gov-tools`,
que no tiene Flask ni las librerías de Google. Los scripts de EIDAS se corren con
`/usr/bin/python3` (así está en `/dashboard`).

Detalle de cada uno en las secciones 3 a 6.

---

## 0. Piezas del sistema y dónde viven

| Pieza | Dónde está | Estado |
|---|---|---|
| Template de cada materia | `materias/<materia>/template/` (mirror de solo lectura); se edita desde la copia hermana `.../terciario-urquiza/eidas-template/`, nunca desde acá | Activo — ver `CLAUDE.md` para la lista de materias y sus templates |
| Rúbrica de cada materia | `materias/<materia>/rubrica.md` | Completa para `af-diseno-sistemas-web-31` y `-32` (incluye la sección "Proceso: evolución sobre la entrega intermedia") |
| Cronograma de cada materia (opcional) | `materias/<materia>/cronograma-2c-2026.md` | Solo `af-diseno-sistemas-web-31` y `-32` lo tienen — si existe, `/chequear-grupo` y `/evaluar-grupo` lo usan para saber qué secciones de la rúbrica ya corresponden según la fecha |
| Marco teórico | `marco-teorico-fundamentacion.md`, `marco-teorico-resumen.md` (compartido, materia-agnóstico) | Completo (pendiente confirmar 2 citas) |
| Repos clonados de cada grupo | `materias/<materia>/grupos/grupo-XX-nombre/` (local, se puebla en el cuatrimestre) | — |
| Borradores de devolución | `sistema-eidas-datos/<materia>/borradores/grupo-XX/AAAA-MM-DD.md` (repo privado, sincronizado entre máquinas — no vive en `sistema-eidas` ni en el repo del grupo, ver `CLAUDE.md`) | — |
| Automatización N8N | `infra/n8n/` (Docker local, compartido entre materias) | Activo — se dispara solo desde `scripts/grupos.py publicar` (webhook local), no desplegado en Linode |
| Dashboard | `scripts/dashboard.py`, http://127.0.0.1:8420 (solo local) | Activo — pestañas Grupos, Recorrer, Notas y Cronograma |
| Lectura de Classroom y Forms | `scripts/classroom.py` (API, solo lectura) + cliente OAuth en `sistema-eidas-datos/classroom/oauth-client.json` + token por máquina en `~/.config/sistema-eidas/` | Activo desde 15/10/2026 |
| Config de Classroom por materia | `sistema-eidas-datos/<materia>/classroom.json` (curso, tareas, Form del cuestionario) | 31, 32 e ITI-21 |
| Tablas de notas | `sistema-eidas-datos/<materia>/notas-cierre-2c-2026.csv` (AF) y `iti-infra-redes-21/notas-classroom-2c-2026.csv` (ITI, la genera la API) | Se regeneran con `notas.py` o el botón del dashboard |
| CSV docente de ITI | `sistema-eidas-datos/iti-infra-redes-21/cierre-2c-2026.csv` — **lo completás vos** (Trabajo 7, nota de proceso, observaciones); el dashboard lo lee, nunca lo escribe | — |
| Cuestionarios propios | bancos en `sistema-eidas-datos/cuestionarios/<id>.md`, motor en github.io `caso-bicirio/v2/`, generador `scripts/cuestionario.py` | Activo — ver `sistema-eidas-datos/cuestionarios/README.md` |
| Colector de respuestas por mail | `infra/cuestionarios/` (N8N + API, http://localhost:8430); la base vive solo en la máquina donde se procesa | Activo — se levanta con `infra/cuestionarios/levantar.sh` |
| PlantUML local | `infra/plantuml/` (http://localhost:8090) — lo usa Recorrer para dibujar los `.puml` | Se levanta a demanda: `docker compose up -d` |

---

## 1. Al inicio del cuatrimestre — dar de alta una materia nueva (si hace falta)

Si la materia todavía no existe en `materias/`:

1. Creá `materias/<slug>/` (convención de nombre: `<carrera>-<materia>-<comisión>`, ej.
   `af-redes-comunicaciones-31`).
2. Escribí `materias/<slug>/rubrica.md` con los criterios de esa materia.
3. Armá `materias/<slug>/template/` como un repo git propio, pusheado a GitHub y marcado
   como *template repository* (mismo proceso que se usó para `eidas-template`).
4. Creá `materias/<slug>/grupos.json` con `{"grupos": []}`.

No hace falta tocar `scripts/grupos.py`, `.claude/commands/evaluar-grupo.md` ni N8N — ya
saben operar sobre cualquier materia que exista en `materias/`.

## 2. Al inicio del cuatrimestre — dar de alta un grupo

1. Cada grupo entra al repo template de su materia (`materias/<materia>/template/`, el link está en `CLAUDE.md`) y usa el botón **"Use this template"** para crear su propio repo (pueden elegirlo público o privado).
2. El grupo completa `integrantes.md` y va documentando en `docs/` a medida que avanza.
3. **El grupo te agrega como colaborador con permiso de escritura** en su repo (Settings → Collaborators). Es imprescindible: sin esto, el paso de publicar la devolución (`git push`) va a fallar.
4. Agregás el grupo a `materias/<materia>/grupos.json` (el campo `email` es el
   destinatario de la notificación — puede ser el de un representante del grupo, o varios
   separados por coma):
   ```json
   { "id": "grupo-01-nombre", "repo": "https://github.com/<usuario-del-grupo>/<repo>.git", "email": "grupo01@ejemplo.com" }
   ```
5. Corrés el script para clonarlo (o `/sync <materia>` si ya estás en una sesión de
   Claude Code — es el mismo comando, sin cambiar de terminal):
   ```
   python3 scripts/grupos.py sync <materia>
   ```
   Este mismo comando, corrido de nuevo más adelante, clona los grupos nuevos que hayas
   agregado a `grupos.json` de esa materia y hace `git pull` de los que ya estaban clonados
   — es el comando de "traeme todo al día" para toda la lista de grupos de esa materia.

---

## 3. Durante el cuatrimestre — evaluar una entrega

Este es el pipeline tal como funciona **hoy** (pasos manuales incluidos, sin disimular).
El borrador de la devolución vive como archivo normal en `sistema-eidas-datos` (repo
privado, hermano de `sistema-eidas/`) — nunca se pushea al repo del grupo hasta que la
aprobás, así que el grupo no tiene forma de verla antes de tiempo, y de paso podés
retomarla desde cualquiera de tus máquinas.

1. **Traer los cambios de todos los grupos de la materia** (opcional si solo vas a mirar
   uno puntual — ver paso 2). Terminal o Claude Code, es lo mismo:
   ```
   python3 scripts/grupos.py sync <materia>
   ```
   o `/sync <materia>` sin salir de la sesión.
2. **Chequear si conviene evaluar todavía:** `/chequear-grupo <materia> grupo-01-nombre`
   (definido en `.claude/commands/chequear-grupo.md`) clona el repo si hace falta y hace
   `git pull` de ese grupo puntual — no hace falta correr `sync` antes solo para chequear
   uno — y no genera ninguna devolución: no escribe nada, solo te da un veredicto
   (`LISTO PARA EVALUAR` / `ESPERAR` / `PEDIR ACTUALIZACIÓN`) contrastando lo que subió el
   grupo contra `rubrica.md`. De paso muestra el total de commits y cuántos archivos se
   retocaron más de una vez, como dato liviano — sin que eso pese en el veredicto. Sirve
   para no generar (y dejar commiteado en `sistema-eidas-datos`) un borrador de
   devolución completa de un grupo que todavía no tiene nada evaluable — más simple que
   generarla igual y después tener que rehacerla cuando el grupo actualice.

   Si la materia tiene `materias/<materia>/cronograma-2c-2026.md`, el chequeo solo mira las
   secciones que ya corresponden según la fecha de hoy — lo que todavía no se dio en clase
   no cuenta como "Ausente", se reporta aparte. Si la materia no tiene ese archivo, chequea
   todas las secciones de la rúbrica como si fuera la entrega final.
3. **(Opcional) Ver el detalle de cómo trabajaron en el tiempo:**
   `/resumen-commits <materia> grupo-01-nombre` (definido en
   `.claude/commands/resumen-commits.md`) recorre todo el historial de `main` y arma, por
   archivo, la línea de tiempo de cuándo se tocó y si fue en un solo bloque o revisado más
   adelante, más un desglose por autor. Es informativo, no entra en la devolución ni pesa
   en la nota por sí solo — sirve como insumo para tu criterio (por ejemplo, para preparar
   una charla o defensa oral con el grupo). El desglose por autor viene con la advertencia
   de que "quién commiteó" no es lo mismo que "quién hizo" — no lo uses solo para juzgar
   aporte individual. La versión a nivel de repo (sin autor) de este mismo análisis sí
   entra en la devolución si la rúbrica de la materia tiene la sección "Proceso" (ver
   punto 4).
4. **Generar el borrador con Claude Code:** abrís Claude Code en `sistema-eidas/` y corrés
   `/evaluar-grupo <materia> grupo-01-nombre`. Ese comando (definido en
   `.claude/commands/evaluar-grupo.md`) **no toca el repo clonado del grupo** — aplica
   `materias/<materia>/rubrica.md` y escribe el borrador en
   `sistema-eidas-datos/<materia>/borradores/grupo-01-nombre/AAAA-MM-DD.md` con el formato
   definido en `CLAUDE.md`, y lo commitea y pushea ahí mismo (repo privado del docente, no
   el del grupo). Es el único lugar donde vive el borrador hasta que se publica — nada de
   branches locales ni copias aparte (así funcionaba hasta 2026-09: una branch `feedback`
   100% local dentro del repo del grupo, que quedaba atada a la máquina donde se generó).

   Las rúbricas de `af-diseno-sistemas-web-31` y `-32` tienen una sección "Proceso:
   evolución sobre la entrega intermedia" (5 pts) — para esa sección, `/evaluar-grupo` busca
   la devolución intermedia anterior de ese grupo en `feedback/` (si existe) y el patrón de
   iteración del historial de commits (a nivel de repo, sin desglose por autor). Si otra
   materia no tiene esta sección en su `rubrica.md`, `/evaluar-grupo` simplemente no la
   evalúa — no hace falta que todas las materias la usen.

   Igual que `/chequear-grupo`, si todavía quedan secciones sin darse en clase según
   `cronograma-2c-2026.md`, el comando genera una **devolución parcial**: solo puntúa lo
   que ya corresponde, marca el resto como "no corresponde todavía" (sin tratarlo como
   Ausente) y no arma la tabla de "Total sobre 100" — esa se arma recién en la entrega
   final, cuando ya todo esté en alcance. "Proceso" nunca se puntúa en una parcial. Formato
   completo de la variante en `CLAUDE.md`, sección "Variante: devolución parcial".
5. **Revisión docente (obligatoria):** abrís
   `sistema-eidas-datos/<materia>/borradores/grupo-01-nombre/AAAA-MM-DD.md` directamente
   (desde cualquier máquina), ajustás puntajes y texto, agregás el contexto que Claude no
   puede ver (proceso grupal, presentación oral, etc. — acá es donde entraría lo que viste
   con `/resumen-commits` si querés mencionarlo, no como puntaje sino como observación), y
   respondés la "Pregunta para el docente" que Claude dejó planteada. Si editás a mano
   (sin Claude Code), acordate de commitear y pushear en `sistema-eidas-datos` — si no, el
   cambio se queda solo en esa máquina.
6. **Publicar y notificar — un solo comando, recién acá se vuelve visible para el grupo:**
   ```
   python3 scripts/grupos.py publicar <materia> grupo-01-nombre
   ```
   Te pide confirmación antes de pushear (podés saltearla con `--yes` si ya estás seguro).
   Revisá el borrador en `sistema-eidas-datos` **antes** de correr esto — el script no te
   muestra el contenido, asume que ya lo revisaste vos. Publica todos los borradores
   pendientes de ese grupo que encuentre (normalmente uno, puede ser más de uno si quedaron
   varias fechas sin publicar).

   Este único comando hace todo el resto solo: tilda "Publicado al grupo" en el archivo, lo
   escribe en `feedback/AAAA-MM-DD.md` del repo del grupo, commitea y pushea directo a
   `main` (no hay branch de por medio, así que no hace falta merge), y **dispara
   automáticamente la notificación en N8N** (vía un webhook local — requiere que N8N esté
   corriendo: `infra/n8n/setup.sh` lo levanta y lo deja configurado solo). N8N busca el
   email y el repo del grupo en `materias/<materia>/grupos.json`, arma el link directo al
   archivo recién publicado en el repo del grupo (`.../blob/main/feedback/AAAA-MM-DD.md`,
   nada se sube a Drive) y manda el mail con ese link — sin que tengas que abrir el
   navegador ni tipear nada de nuevo.

   Requisito para que esto funcione: el grupo tiene que tener los campos `"email"` y
   `"repo"` cargados en su entrada de `grupos.json` (ver sección 2).

   **En una máquina nueva:** no hace falta configurar N8N a mano — corré
   `sistema-eidas/infra/n8n/setup.sh` una vez. Crea los symlinks a los secretos (que viven
   en `sistema-eidas-datos/n8n/`, ver el `README.md` de ese repo), levanta el contenedor, e
   importa el workflow y las credenciales por CLI (el workflow ya no usa la de Drive, pero
   no hace falta sacarla del import — no molesta si queda sin usar). Único paso manual que
   queda: prender el toggle "Active" del workflow "Evaluacion EIDAS" en `localhost:5678` —
   esta versión de N8N no soporta activarlo por CLI fuera de modo queue. El script es
   idempotente, corrélo de nuevo sin miedo si no estás seguro de en qué quedó una máquina.

   Si la notificación falla (por ejemplo, N8N no estaba corriendo), el push ya se hizo —
   no se pierde nada — y el script te va a decir cómo reintentar:
   ```
   python3 scripts/grupos.py notificar <materia> grupo-01-nombre AAAA-MM-DD
   ```

---

## 4. Notas por alumno: Classroom, Forms y la pestaña Notas

El cuestionario individual (30 pts en AF) se toma con Google Forms y se asigna desde
Classroom. La nota se combina con el repo grupal (70) según la `rubrica.md`.

**De dónde sale cada nota.** `scripts/classroom.py` lee Classroom y Forms por API, **solo
lectura**. La primera vez en cada máquina abre el navegador para autorizar con la cuenta del
terciario. `scripts/notas.py <materia>` cruza todo y deja un CSV por materia; la pestaña
**Notas** del dashboard lo muestra con filtros y tiene el botón **↻ traer de Classroom y Forms**.

- **AF (31 y 32): cuestionario + repo.** Por alumno: nota del cuestionario (/100 y /30), grupo
  (por el DNI del mail, o por apellido en `integrantes.md`), nota del repo (/70, de la última
  devolución, aclarando si no está publicada) y total. La nota del cuestionario se toma de
  Classroom si está ahí, o del Form si se corrigió en Forms; en el Form, 10 puntos o menos es
  solo la parte autocorregida y cuenta como "falta corregir". Estados: *no respondió*, *falta
  corregir*, *corregido en Forms, falta importar a Classroom*, *corregido, falta devolver en
  Classroom*, *corregido y devuelto*.
- **ITI (sin repo grupal): por tareas.** Una columna por tarea de Classroom (las que lista
  `classroom.json`), más las columnas del CSV docente que completás vos (Trabajo 7, nota de
  proceso, observaciones), promedio con 0 en lo no entregado y avisos (*entregada, falta
  calificar*, *no está en Classroom*).

**Lo que la API no puede hacer** (límites de Google, no nuestros):
- **Calificar ni devolver** tareas creadas a mano en Classroom: solo las que crea nuestra app.
  Por eso la carga de notas sigue siendo en Classroom (o "Importar calificaciones" desde un Form).
- **Comentarios privados:** no existen en la API. La devolución en texto va por el repo o el mail.
- **Rúbricas:** piden licencia Education Plus.

Para sumar una materia: crear `sistema-eidas-datos/<materia>/classroom.json` (ids con
`classroom.py cursos` y `tareas <curso>`; ver ejemplos de la 31 y de ITI-21).

---

## 5. Cuestionarios propios y simulacros (github.io)

Para práctica y simulacros con corrección y explicación por pregunta. El detalle completo está
en `sistema-eidas-datos/cuestionarios/README.md`; el circuito corto:

1. Banco en `sistema-eidas-datos/cuestionarios/<id>.md`: preguntas con `- [x]` en la correcta y
   `> Por qué:`. El V/F se arma como opción múltiple de 2.
2. `cuestionario.py generar <banco> --sitio …/pablopedernera0.github.io/caso-bicirio/v2/cuestionarios`
   (si las correctas quedan amontonadas en una letra, cambiar la `semilla`). Crear
   `casos/<caso>/caso.md` con la consigna. Commit y push de github.io.
3. Link para los alumnos: `https://pablopedernera0.github.io/caso-bicirio/v2/?cuestionario=<id>`.
   La corrección se ve recién con el **código del día** (en `&modo=docente`, con la clave
   maestra). **Cambia a las 0 h**: el de hoy no sirve para quien lo haga mañana.
4. Si el banco tiene `envio_mail:`, las respuestas llegan por mail y las junta el colector
   (`infra/cuestionarios/levantar.sh`, http://localhost:8430). Su base vive **solo en la
   máquina donde se procesó**: no proceses en una máquina con la base vacía, porque pisa la
   planilla de Drive con lo poco que tenga. Los mails ya procesados quedan con la etiqueta
   `procesado` en Gmail.

Mails de aviso de Classroom: "Enviado con retraso" se puede ignorar (está en Notas y en
`classroom.py entregas`). **"Se agregó un comentario privado" y "Se entregó nuevamente" no**:
los comentarios privados no se pueden leer por API, y una reentrega suele ser un alumno que
corrigió lo que le pediste y espera otra revisión (caso Sanfilippo, Medición de servidores, 05/10).

---

## 6. El dashboard

`/dashboard` lo levanta en http://127.0.0.1:8420, solo local. Pestañas:

- **Grupos:** estado de evaluación de cada grupo de cada materia (sin evaluar, borrador,
  revisado, publicado). El nombre del grupo lleva a Recorrer.
- **Recorrer:** navegador de los clones locales. **Por grupo**: todos sus archivos en el orden
  del template (← → archivo, Shift+← → grupo). **Por sección**: el mismo archivo en todos los
  grupos (← → grupo, Shift+← → sección); si un grupo lo tiene en otra ruta, lo muestra igual.
  Punto naranja = cambió después del último borrador. Dibuja `.puml` (con PlantUML local
  prendido) y PDF, y avisa las tablas Markdown rotas. **↻ actualizar** hace pull de un grupo o
  de toda la materia, como `/sync`.
- **Notas:** ver sección 4.
- **Cronograma:** ver y editar `cronograma*.md` de cada materia (guarda en disco, sin commit).

En ITI-21, los "grupos" son los repos del Trabajo 7 (`t7-…` en su `grupos.json`): se recorren
igual, y desde Notas el link "recorrer" de cada alumno lleva a su repo.

---

## 7. Máquina nueva (o la notebook después de mucho tiempo)

1. `/estado-eidas` para traer `sistema-eidas`, `sistema-eidas-datos`, la memoria y los templates.
2. Python del sistema con lo necesario:
   `/usr/bin/python3 -m pip install --user flask markdown google-api-python-client google-auth-oauthlib`.
3. N8N: `infra/n8n/setup.sh` (ver sección 3, paso 6).
4. Symlinks de `grupos.json`: cada `materias/<materia>/grupos.json` apunta a
   `sistema-eidas-datos/<materia>/grupos.json`. Están en `.gitignore`, así que en una máquina
   nueva hay que crearlos, ej.:
   `ln -s ../../../sistema-eidas-datos/iti-infra-redes-21/grupos.json materias/iti-infra-redes-21/grupos.json`.
5. Classroom: el cliente OAuth está en `sistema-eidas-datos/classroom/oauth-client.json`
   **solo si lo commiteaste a mano** (el modo automático de Claude Code no commitea
   credenciales). Si no está, bajalo de nuevo desde la consola de Google Cloud (proyecto
   `sistema-eidas` → Credenciales → "EIDAS Classroom lectura"). Después, `classroom.py cursos`
   abre el navegador una vez para autorizar.
6. `/sync <materia>` para clonar los repos de los grupos, y `docker compose up -d` en
   `infra/plantuml/` si vas a recorrer diagramas.

---

## 8. Pendientes para completar la automatización

- **Apps Script en Google Forms** — evaluado y descartado (ver `CLAUDE.md`, sección de
  pendientes): el cuestionario ya se autocalifica y es individual, no vale la pena meterlo
  en el repo grupal.
- **Rúbrica y template de las materias de Redes** (ej. `af-redes-comunicaciones-31`,
  `iti-infraestructura-redes-21`) — contenido nuevo, no reutilizable de Diseño de Sistemas
  Web, va a llevar más tiempo armarlo.

**Decisión ya tomada — no son pendientes:**
- *El disparo sigue controlado por vos, aunque ya no requiere un click aparte en N8N.*
  `scripts/grupos.py publicar` es lo único que dispara la notificación — no hay ningún
  webhook de GitHub ni nada escuchando push events por su cuenta. Publicar y notificar
  pasaron a ser un solo paso porque en la práctica siempre se hacían juntos; la decisión de
  "cuándo" sigue siendo 100% tuya.
- *N8N se queda en local, no se despliega en el Linode.* El webhook que dispara la
  notificación es una llamada `localhost:5678` desde el propio script — nunca sale a
  internet, así que no hace falta que N8N sea accesible desde afuera. El Linode solo
  entraría en juego si en el futuro se necesita que un servicio externo (GitHub, Apps
  Script) le llegue a N8N desde afuera de esta máquina.
- *N8N es una sola instancia compartida entre todas las materias*, no una por materia —
  el `materia` viaja como dato en cada llamada (webhook, `grupos.json` a leer, carpeta de
  Drive), no como infraestructura separada.

---

*Sistema EIDAS — Terciario Urquiza — Rosario, 2026*

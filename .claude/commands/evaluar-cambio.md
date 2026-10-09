Evaluá la actividad "El cliente cambió de idea": cada grupo recibe un pedido de cambio de su
comitente y rastrea su impacto en los documentos. Es formativa, no se puntúa con la rúbrica.

**La entrega es una issue** titulada "Cambios <fecha>" en el repo del grupo, con qué cambiaría
en cada archivo. La consigna original pedía una branch, con la issue como plan B, pero el
09/10 se decidió que todos los grupos fueran por la issue. Si un grupo igual creó la branch,
se lee también (ver paso 1), pero no se pide ni se marca nada por no tenerla.

`$ARGUMENTS`: `<materia> <grupo-id> [<actividad>]` o `<materia> --control [<actividad>]`.
`<actividad>` es por defecto `cambios-20261009`, y es también el nombre de la branch. Si
faltan argumentos, pedíselos al usuario.

Todo vive en `sistema-eidas-datos/<materia>/<actividad>/` (repo privado, hermano de
`sistema-eidas/`):
- `pedidos.md`: frontmatter (`branch`, `hoy` = fecha del control obligatorio,
  `presentacion`) y una sección `## <grupo-id>` por grupo, con `### Pedido` (lo que vieron
  los estudiantes) e `### Impacto esperado` (la clave: lo mínimo que un cambio bien rastreado
  debería tocar, más una "Señal de alerta").
- `devoluciones/<grupo-id>.md`: lo que escribe este comando.

Para leer el repo del grupo, usá siempre `git -C <repo>`, nunca `cd`. **No hagas checkout
de la branch** en el clon del grupo: `scripts/grupos.py sync` espera encontrarlo en `main`.
Todo se lee desde `origin/<branch>`.

## 1. Traer la issue (y la branch, si existe)

La URL del repo sale de `materias/<materia>/grupos.json` (sacale el `https://github.com/` del
principio y el `.git` del final, si lo tiene). Con ella:

```
gh issue list -R <owner>/<repo> --state all --search "Cambios" --json number,title,author,createdAt
gh issue view <n> -R <owner>/<repo> --json title,body,author,createdAt,updatedAt,comments
```

El rastreo puede estar en el cuerpo o repartido en comentarios: leé los dos. Si no hay issue,
el grupo no entregó.

Además, fijate si existe la branch (un `fetch` de una branch que no existe falla entero). El
repo clonado es `materias/<materia>/grupos/<grupo-id>/`; si no está, alcanza con la issue:

```
git -C <repo> ls-remote --heads origin <branch>
git -C <repo> fetch origin main          # siempre
git -C <repo> fetch origin <branch>      # solo si ls-remote la encontró
```

## 2. Control del día (`--control`, o como primer paso de la evaluación)

Para cada grupo de `grupos.json` (con `--control`) o solo para `<grupo-id>`:
- La issue: si existe, cuándo se creó y quién, y qué archivos nombra el cuerpo y los
  comentarios con un cambio concreto para cada uno (un título sin cuerpo no nombra nada).
- Si hay branch:
  - Archivos de la branch respecto de main: `git -C <repo> diff --name-status origin/main...origin/<branch>`.
  - Commits de la branch con fecha y autor:
    `git -C <repo> log --format='%h|%ad|%an|%s' --date=format-local:'%Y-%m-%d %H:%M' origin/main..origin/<branch>`
    (corré git con `TZ=America/Argentina/Buenos_Aires`).
  - Archivos tocados por commits del día `hoy`:
    `git -C <repo> log --since='<hoy> 00:00' --until='<hoy> 23:59' --name-only --format= origin/main..origin/<branch>`, sin repetidos.
  - Si `main` recibió un merge de la branch, avisalo: el pedido era no mezclarla.

**Cumple el control** si la issue existe y nombra al menos 2 archivos distintos con lo que
cambiaría en cada uno, o si hay branch y los commits del día `hoy` tocan al menos 2 archivos.
Una issue vacía o que no nombra archivos: "issue sin detalle", no cumple todavía.

Con `--control`, el resultado es una tabla por grupo (issue sí/no con número, archivos que
nombra, autor, branch sí/no, cumple/no cumple/issue sin detalle) y nada más: no escribas
archivos.

## 3. Evaluar el cambio (sin `--control`)

1. Leé la sección `## <grupo-id>` de `pedidos.md`.
2. Leé la issue entera (cuerpo y comentarios) y, para cada archivo que nombra, su versión
   actual en `main` (`git -C <repo> show origin/main:<ruta>`, después de
   `git -C <repo> fetch origin main`), para ver si el cambio propuesto encaja con lo que ya
   está: que los IDs que citan existan, que no dupliquen un RF que ya había. Si hay branch,
   leé también su diff (`git -C <repo> diff origin/main...origin/<branch>`).
3. Compará contra el **Impacto esperado**, área por área (stakeholders, requisitos, HU, casos
   de uso, ER, UI, y lo que liste el pedido de ese grupo): **Cubierto**, **Parcial**,
   **Falta** o **Resuelto distinto** (si lo resolvieron de otra forma razonable y justificada,
   está bien: el impacto esperado no es la única respuesta). Siempre con evidencia: archivo e
   ID (RF-xx, HU-xx, entidad). En la issue no se espera el texto final de cada artefacto,
   pero sí que diga qué se agrega o cambia y dónde: "agregar RF de seña" sin decir cuál es
   el requisito cuenta como **Parcial**.
4. Mirá la coherencia entre artefactos: cada RF nuevo, ¿tiene su HU o CU y su lugar en el ER?
   Mirá los bordes (los criterios de aceptación, ¿cubren lo que no es el camino feliz?) y
   si apareció la "Señal de alerta" del pedido.
5. Anotá lo que tocaron fuera del pedido y si borraron algo de lo que ya estaba sin
   reemplazarlo.

## 4. Escribir la devolución

En `sistema-eidas-datos/<materia>/<actividad>/devoluciones/<grupo-id>.md` (creá la carpeta si
no existe; si el archivo ya existe, reemplazalo: es la foto del estado actual de la issue):

```
# Cambio <actividad> — <grupo-id>

**Control del <hoy>:** cumple / no cumple / issue sin detalle — N archivos, autor: …
**Estado de la issue al <fecha de hoy>:** #N, M comentarios, última actualización el …

## Qué rastrearon bien
## Qué se les escapó
(por área, con lo que falta y por qué importa)
## Bordes y coherencia
## Para la revisión del <presentacion>
(2 o 3 cosas concretas que tienen que quedar en la issue para esa fecha)

**Confianza Claude:** Alta / Media / Baja
**Pregunta para el docente:** …
```

Escribí para el grupo, en segunda persona del plural y en tono de colegas. Sin puntaje.

Commiteá y pusheá solo ese archivo en `sistema-eidas-datos`:

```
git -C ../sistema-eidas-datos add <materia>/<actividad>/devoluciones/<grupo-id>.md
git -C ../sistema-eidas-datos commit -m "Devolución <actividad> para <grupo-id>"
git -C ../sistema-eidas-datos push
```

## 5. Reportar

Un resumen corto: cumple o no el control, las áreas cubiertas y las que faltan, y la ruta
del archivo. Esta devolución **no** se publica con `grupos.py publicar` (ese circuito es el de
la rúbrica). Es para que el docente la use en la revisión del miércoles o la comparta
como quiera.

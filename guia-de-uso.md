# Guía de uso — Sistema EIDAS

> Cómo operar el sistema hoy, con el estado real de cada pieza (qué está automatizado
> y qué todavía requiere pasos manuales). El sistema es multi-materia: casi todos los
> comandos toman `<materia>` como primer argumento — es el nombre de carpeta dentro de
> `materias/` (ej: `af-diseno-sistemas-web-31`). Ver `CLAUDE.md` para el diseño completo y
> `materias/<materia>/rubrica.md` / `marco-teorico-fundamentacion.md` para el fundamento de
> cada decisión.

---

## 0. Piezas del sistema y dónde viven

| Pieza | Dónde está | Estado |
|---|---|---|
| Template de cada materia | `materias/<materia>/template/`, repo propio en GitHub | Activo — ver `CLAUDE.md` para la lista de materias y sus templates |
| Rúbrica de cada materia | `materias/<materia>/rubrica.md` | Completa para `af-diseno-sistemas-web-31` |
| Marco teórico | `marco-teorico-fundamentacion.md`, `marco-teorico-resumen.md` (compartido, materia-agnóstico) | Completo (pendiente confirmar 2 citas) |
| Repos clonados de cada grupo | `materias/<materia>/grupos/grupo-XX-nombre/` (local, se puebla en el cuatrimestre) | — |
| Borradores de devolución | `materias/<materia>/feedback/grupo-XX.md` (local, generados por Claude) | — |
| Automatización N8N | `infra/n8n/` (Docker local, compartido entre materias) | Activo — se dispara solo desde `scripts/grupos.py publicar` (webhook local), no desplegado en Linode |

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
5. Corrés el script para clonarlo:
   ```
   python3 scripts/grupos.py sync <materia>
   ```
   Este mismo comando, corrido de nuevo más adelante, clona los grupos nuevos que hayas
   agregado a `grupos.json` de esa materia y hace `git pull` de los que ya estaban clonados
   — es el comando de "traeme todo al día" para toda la lista de grupos de esa materia.

---

## 3. Durante el cuatrimestre — evaluar una entrega

Este es el pipeline tal como funciona **hoy** (pasos manuales incluidos, sin disimular).
La devolución vive como una **branch local** (`feedback`) dentro del propio repo clonado
del grupo — nunca se pushea hasta que la aprobás, así que el grupo no tiene forma de verla
antes de tiempo.

1. **Traer los cambios del grupo:**
   ```
   python3 scripts/grupos.py sync <materia>
   ```
   (o `cd materias/<materia>/grupos/grupo-01-nombre && git pull` si solo querés actualizar ese grupo puntual)
2. **(Opcional) Chequear si conviene evaluar todavía:** `/chequear-grupo <materia> grupo-01-nombre`
   (definido en `.claude/commands/chequear-grupo.md`) es de solo lectura — no crea la branch
   `feedback` ni escribe nada — y te da un veredicto (`LISTO PARA EVALUAR` / `ESPERAR` /
   `PEDIR ACTUALIZACIÓN`) contrastando lo que subió el grupo contra `rubrica.md`. Sirve para
   no generar (y dejar commiteada en la branch local) una devolución completa de un grupo
   que todavía no tiene nada evaluable — más simple que generarla igual y después tener que
   rehacerla cuando el grupo actualice.
3. **Generar el borrador con Claude Code:** abrís Claude Code en `sistema-eidas/` y corrés
   `/evaluar-grupo <materia> grupo-01-nombre`. Ese comando (definido en
   `.claude/commands/evaluar-grupo.md`) crea (o actualiza) la branch local `feedback` dentro
   de `materias/<materia>/grupos/grupo-01-nombre/`, aplica `materias/<materia>/rubrica.md`,
   y commitea ahí `feedback/AAAA-MM-DD.md` con el formato definido en `CLAUDE.md`. De paso,
   deja una copia de trabajo en
   `materias/<materia>/feedback/grupo-01-nombre_AAAA-MM-DD.md` (esta sí es tuya,
   no se pushea a ningún lado, es solo para que tengas todas las devoluciones de esa materia juntas).
4. **Revisión docente (obligatoria):** revisás el diff de la branch `feedback` contra `main`
   (`git diff main..feedback` dentro del repo del grupo), ajustás puntajes y texto directamente
   en el archivo, agregás el contexto que Claude no puede ver (proceso grupal, presentación
   oral, etc.), y respondés la "Pregunta para el docente" que Claude dejó planteada.
5. **Publicar y notificar — un solo comando, recién acá se vuelve visible para el grupo:**
   ```
   python3 scripts/grupos.py publicar <materia> grupo-01-nombre
   ```
   Te pide confirmación antes de hacer el merge y el push (podés saltearla con `--yes` si
   ya estás seguro). Revisá la branch `feedback` con `git diff main..feedback` **antes** de
   correr esto — el script no te muestra el diff, asume que ya lo revisaste vos.

   Este único comando hace todo el resto solo: mergea `feedback` → `main`, tilda "Publicado
   al grupo" en el archivo, pushea, y **dispara automáticamente la notificación en N8N**
   (vía un webhook local — requiere que `docker compose up -d` esté corriendo en
   `infra/n8n/`). N8N busca el email del grupo en `materias/<materia>/grupos.json`, lee el
   archivo recién publicado, lo sube a "Devoluciones EIDAS" en Drive con la materia en el
   nombre del archivo, y manda el mail con el link — sin que tengas que abrir el navegador
   ni tipear nada de nuevo.

   Requisito para que esto funcione: el grupo tiene que tener un campo `"email"` cargado en
   su entrada de `grupos.json` (ver sección 2).

   Si la notificación falla (por ejemplo, N8N no estaba corriendo), el push ya se hizo —
   no se pierde nada — y el script te va a decir cómo reintentar:
   ```
   python3 scripts/grupos.py notificar <materia> grupo-01-nombre AAAA-MM-DD
   ```

---

## 4. Cuestionario individual

Vía Google Classroom/Forms — activo, sin cambios pendientes de este lado. La nota se combina con el puntaje del repo grupal según la `rubrica.md` de cada materia (típicamente 70 repo + 30 cuestionario = 100, pero puede variar por materia).

---

## 5. Pendientes para completar la automatización

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

# Guía de uso — Sistema EIDAS

> Cómo operar el sistema hoy, con el estado real de cada pieza (qué está automatizado
> y qué todavía requiere pasos manuales). Ver `CLAUDE.md` para el diseño completo y
> `rubrica.md` / `marco-teorico-fundamentacion.md` para el fundamento de cada decisión.

---

## 0. Piezas del sistema y dónde viven

| Pieza | Dónde está | Estado |
|---|---|---|
| Template para los grupos | https://github.com/pablopedernera0/eidas-template | Activo — repo público, template repository |
| Rúbrica de evaluación | `rubrica.md` | Completa |
| Marco teórico | `marco-teorico-fundamentacion.md`, `marco-teorico-resumen.md` | Completo (pendiente confirmar 2 citas) |
| Repos clonados de cada grupo | `grupos/grupo-XX-nombre/` (local, se puebla en el cuatrimestre) | — |
| Borradores de devolución | `feedback/grupo-XX.md` (local, generados por Claude) | — |
| Automatización N8N | `infra/n8n/` (Docker local) | Activo — se dispara solo desde `scripts/grupos.py publicar` (webhook local), no desplegado en Linode |

---

## 1. Al inicio del cuatrimestre — dar de alta un grupo

1. Cada grupo entra a https://github.com/pablopedernera0/eidas-template y usa el botón **"Use this template"** para crear su propio repo (pueden elegirlo público o privado).
2. El grupo completa `integrantes.md` y va documentando en `docs/` a medida que avanza.
3. **El grupo te agrega como colaborador con permiso de escritura** en su repo (Settings → Collaborators). Es imprescindible: sin esto, el paso de publicar la devolución (`git push`) va a fallar.
4. Agregás el grupo a `grupos.json`, en la raíz de `sistema-eidas/` (el campo `email` es el
   destinatario de la notificación — puede ser el de un representante del grupo, o varios
   separados por coma):
   ```json
   { "id": "grupo-01-nombre", "repo": "https://github.com/<usuario-del-grupo>/<repo>.git", "email": "grupo01@ejemplo.com" }
   ```
5. Corrés el script para clonarlo:
   ```
   python3 scripts/grupos.py sync
   ```
   Este mismo comando, corrido de nuevo más adelante, clona los grupos nuevos que hayas
   agregado a `grupos.json` y hace `git pull` de los que ya estaban clonados — es el comando
   de "traeme todo al día" para toda la lista de grupos de una sola vez.

---

## 2. Durante el cuatrimestre — evaluar una entrega

Este es el pipeline tal como funciona **hoy** (pasos manuales incluidos, sin disimular).
La devolución vive como una **branch local** (`feedback`) dentro del propio repo clonado
del grupo — nunca se pushea hasta que la aprobás, así que el grupo no tiene forma de verla
antes de tiempo.

1. **Traer los cambios del grupo:**
   ```
   python3 scripts/grupos.py sync
   ```
   (o `cd grupos/grupo-01-nombre && git pull` si solo querés actualizar ese grupo puntual)
2. **Generar el borrador con Claude Code:** abrís Claude Code en `sistema-eidas/` y corrés
   `/evaluar-grupo grupo-01-nombre`. Ese comando (definido en
   `.claude/commands/evaluar-grupo.md`) crea (o actualiza) la branch local `feedback` dentro
   de `grupos/grupo-01-nombre/`, aplica `rubrica.md`, y commitea ahí
   `feedback/AAAA-MM-DD.md` con el formato definido en `CLAUDE.md`. De paso, deja una copia
   de trabajo en `sistema-eidas/feedback/grupo-01-nombre_AAAA-MM-DD.md` (esta sí es tuya,
   no se pushea a ningún lado, es solo para que tengas todas las devoluciones juntas).
3. **Revisión docente (obligatoria):** revisás el diff de la branch `feedback` contra `main`
   (`git diff main feedback` dentro del repo del grupo), ajustás puntajes y texto directamente
   en el archivo, agregás el contexto que Claude no puede ver (proceso grupal, presentación
   oral, etc.), y respondés la "Pregunta para el docente" que Claude dejó planteada.
4. **Publicar y notificar — un solo comando, recién acá se vuelve visible para el grupo:**
   ```
   python3 scripts/grupos.py publicar grupo-01-nombre
   ```
   Te pide confirmación antes de hacer el merge y el push (podés saltearla con `--yes` si
   ya estás seguro). Revisá la branch `feedback` con `git diff main..feedback` **antes** de
   correr esto — el script no te muestra el diff, asume que ya lo revisaste vos.

   Este único comando hace todo el resto solo: mergea `feedback` → `main`, tilda "Publicado
   al grupo" en el archivo, pushea, y **dispara automáticamente la notificación en N8N**
   (vía un webhook local — requiere que `docker compose up -d` esté corriendo en
   `infra/n8n/`). N8N busca el email del grupo en `grupos.json`, lee el archivo recién
   publicado, lo sube a "Devoluciones EIDAS" en Drive, y manda el mail con el link — sin que
   tengas que abrir el navegador ni tipear nada de nuevo.

   Requisito para que esto funcione: el grupo tiene que tener un campo `"email"` cargado en
   su entrada de `grupos.json` (ver sección 1).

   Si la notificación falla (por ejemplo, N8N no estaba corriendo), el push ya se hizo —
   no se pierde nada — y el script te va a decir cómo reintentar:
   ```
   python3 scripts/grupos.py notificar grupo-01-nombre AAAA-MM-DD
   ```

---

## 3. Cuestionario individual

Vía Google Classroom/Forms — activo, sin cambios pendientes de este lado. La nota se combina con el puntaje del repo grupal según `rubrica.md` (70 repo + 30 cuestionario = 100).

---

## 4. Pendientes para completar la automatización

- **Apps Script en Google Forms** — evaluado y descartado (ver `CLAUDE.md`, sección de
  pendientes): el cuestionario ya se autocalifica y es individual, no vale la pena meterlo
  en el repo grupal.

Con esto, no queda ningún pendiente de automatización sin resolver o decidir explícitamente.

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

---

*Sistema EIDAS — Terciario Urquiza — Rosario, 2026*

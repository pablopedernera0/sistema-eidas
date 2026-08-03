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
| Automatización N8N | `infra/n8n/` (Docker local) | Probado con datos de prueba, no conectado a devoluciones reales, no desplegado en Linode |

---

## 1. Al inicio del cuatrimestre — dar de alta un grupo

1. Cada grupo entra a https://github.com/pablopedernera0/eidas-template y usa el botón **"Use this template"** para crear su propio repo (pueden elegirlo público o privado).
2. El grupo completa `integrantes.md` y va documentando en `docs/` a medida que avanza.
3. **El grupo te agrega como colaborador con permiso de escritura** en su repo (Settings → Collaborators). Es imprescindible: sin esto, el paso de publicar la devolución (`git push`) va a fallar.
4. Agregás el grupo a `grupos.json`, en la raíz de `sistema-eidas/`:
   ```json
   { "id": "grupo-01-nombre", "repo": "https://github.com/<usuario-del-grupo>/<repo>.git" }
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
2. **Generar el borrador con Claude Code:** abrís Claude Code en `sistema-eidas/` y le pedís
   que, dentro de `grupos/grupo-01-nombre/`, cree (o actualice) una branch local `feedback`,
   lea el repo del grupo, aplique `rubrica.md`, y commitee ahí
   `feedback/AAAA-MM-DD.md` con el formato definido en `CLAUDE.md`. De paso, deja una copia
   de trabajo en `sistema-eidas/feedback/grupo-01-nombre_AAAA-MM-DD.md` (esta sí es tuya,
   no se pushea a ningún lado, es solo para que tengas todas las devoluciones juntas).
3. **Revisión docente (obligatoria):** revisás el diff de la branch `feedback` contra `main`
   (`git diff main feedback` dentro del repo del grupo), ajustás puntajes y texto directamente
   en el archivo, agregás el contexto que Claude no puede ver (proceso grupal, presentación
   oral, etc.), y respondés la "Pregunta para el docente" que Claude dejó planteada.
4. **Publicar — recién acá se vuelve visible para el grupo:**
   ```
   python3 scripts/grupos.py publicar grupo-01-nombre
   ```
   Te pide confirmación antes de hacer el merge y el push (podés saltearla con `--yes` si
   ya estás seguro). Revisá la branch `feedback` con `git diff main feedback` **antes** de
   correr esto — el script no te muestra el diff, asume que ya lo revisaste vos.
5. **Notificar al grupo — hoy esto es manual:**
   - Abrís N8N local (`docker compose up -d` en `infra/n8n/`, luego http://localhost:5678).
   - Abrís el workflow **"Evaluacion EIDAS"**.
   - En el nodo **"Edit Fields"**, reemplazás los valores de prueba (`nombre_grupo`, `contenido`, `email_destino`) por los datos reales de esta devolución.
   - Ejecutás el workflow manualmente ("Test workflow"). Esto sube el archivo a la carpeta **"Devoluciones EIDAS"** en Drive y manda el mail de aviso.

   *(El nodo "Edit Fields" todavía no lee `feedback/AAAA-MM-DD.md` automáticamente — hay que
   pegar los datos a mano por ahora. Ver "Pendientes" más abajo.)*

---

## 3. Cuestionario individual

Vía Google Classroom/Forms — activo, sin cambios pendientes de este lado. La nota se combina con el puntaje del repo grupal según `rubrica.md` (70 repo + 30 cuestionario = 100).

---

## 4. Pendientes para completar la automatización

En orden de lo que más impacto tiene:

1. **Conectar el workflow a los archivos reales:** que el nodo "Edit Fields" lea `grupos/grupo-XX/feedback/AAAA-MM-DD.md` en vez de tener datos de prueba hardcodeados.
2. **Apps Script en Google Forms** para copiar las respuestas del cuestionario individual al repo o a algún lugar donde el pipeline las pueda leer.

**Decisión ya tomada — no son pendientes:**
- *El trigger es manual, y así se queda.* Vos pusheás `main` cuando aprobás, y después disparás N8N a mano. Encaja con la idea de que el docente controla cuándo se publica una devolución, sin necesitar webhooks.
- *N8N se queda en local, no se despliega en el Linode.* Como el disparo es manual y vos operás todo desde tu PC, no hay necesidad de que N8N sea accesible desde internet. El Linode solo entraría en juego si en el futuro se necesita que un servicio externo llame a N8N (webhook real, Apps Script empujando en vez de N8N consultando).

---

*Sistema EIDAS — Terciario Urquiza — Rosario, 2026*

# Sistema EIDAS
## Evaluación Integrada con Devolución Asistida y Supervisada

### Contexto institucional

- **Institución:** Terciario Urquiza — Rosario, Santa Fe, Argentina
- **Docente:** Pedernera Pablo (Profe Pablo)
- **Cuatrimestre:** 2.° 2026

**Antes de arrancar, leer también** `~/trabajos/pablo/terciario-urquiza/contexto-docente/CONTEXTO.md`
(repo privado `pablopedernera0/contexto-docente`) — contexto que cruza este repo con
`la-cajonera`, `sistema-eidas-datos`, `hilo-conductor-redes-ataques` y
`pablopedernera0.github.io` (cuentas de GitHub, incidente Killercoda, hábito de dos
máquinas). La memoria de Claude Code es por proyecto; ese repo es el complemento manual
para lo que es transversal a varios.

Este sistema es **multi-materia**: cada materia/comisión vive en su propia carpeta bajo
`materias/`, con su propia rúbrica y su propio repo template. La infraestructura (N8N,
scripts, el dispositivo pedagógico en sí) es compartida entre todas.

**Materias activas:**

| Carpeta en `materias/` | Carrera | Materia | Comisión | Template |
|---|---|---|---|---|
| `af-diseno-sistemas-web-31` | Analista Funcional de Sistemas | Diseño de Sistemas Web | 31 | https://github.com/pablopedernera0/eidas-template |
| `af-diseno-sistemas-web-32` | Analista Funcional de Sistemas | Diseño de Sistemas Web | 32 | https://github.com/pablopedernera0/eidas-template (mismo template, compartido entre comisiones) |

---

### Qué es el Sistema EIDAS

EIDAS es un dispositivo de evaluación con fundamento pedagógico que combina:

1. **Trabajo grupal** documentado en GitHub con estructura fija
2. **Cuestionario individual** via Google Classroom/Forms
3. **Evaluación asistida por IA** (Claude) como primer lector
4. **Supervisión docente** obligatoria antes de publicar cualquier devolución
5. **Automatización** via N8N para notificación a los grupos

El docente supervisa y aprueba toda devolución antes de que los estudiantes la vean. Claude actúa como primer lector sistemático, no como evaluador final. Ver `marco-teorico-fundamentacion.md` para el fundamento pedagógico completo — es materia-agnóstico, aplica igual a todas las materias que usen el sistema.

---

### Estructura del proyecto en disco

```
sistema-eidas/
├── CLAUDE.md                           ← este archivo (genérico, sin detalle de una materia)
├── guia-de-uso.md                      ← guía operativa paso a paso
├── guia-docente-clase-git.md           ← plan de clase práctica de git (solo docente)
├── guia-prueba-circuito-completo.md    ← runbook para probar el sistema de punta a punta
├── .claude/commands/evaluar-grupo.md   ← comando /evaluar-grupo <materia> <grupo-id>
├── marco-teorico*.md                   ← fundamento pedagógico (compartido, materia-agnóstico)
├── infra/n8n/                          ← docker-compose de N8N (local, compartido entre materias)
│   └── setup.sh                        ← setup en una máquina nueva, ver nota abajo
├── scripts/grupos.py                   ← sync/publicar/notificar, todos toman <materia> como argumento
└── materias/
    └── af-diseno-sistemas-web-31/      ← una carpeta por materia/comisión
        ├── rubrica.md                  ← rúbrica de ESTA materia
        ├── template/                   ← mirror de solo lectura de eidas-template (ver nota debajo)
        ├── grupos.json                 ← id + url de repo + email de cada grupo de ESTA materia
        └── grupos/                     ← repos clonados de los grupos de esta materia
            └── grupo-01-xxxxx/
                └── feedback/
                    └── AAAA-MM-DD.md   ← devolución ya publicada (visible para el grupo);
                                           no existe hasta que se publica — antes de eso el
                                           borrador vive en sistema-eidas-datos, ver Pipeline
```

El borrador de una devolución **no vive en `sistema-eidas`** — vive en
`sistema-eidas-datos/<materia>/borradores/<grupo-id>/AAAA-MM-DD.md` (repo privado, ver su
`README.md`), justo para que sea portable entre las máquinas del docente. Ver Pipeline abajo.

Para dar de alta una materia nueva: crear `materias/<slug>/` con su propia `rubrica.md` y
`template/` (clon de su repo template en GitHub — propio de la materia, o compartido si
reutiliza uno existente como `eidas-template`), y un `grupos.json` con `{"grupos": []}`. El
resto (scripts, comando, N8N) ya sabe operar sobre cualquier materia sin cambios.

**Convención para editar un template compartido entre materias:** cuando el mismo repo
template se usa en más de una materia (como `eidas-template`, hoy en 31 y 32), no se edita
desde ninguna de las copias en `materias/*/template/` — esas son mirrors de solo lectura,
`/estado-eidas` las pullea solas cuando están limpias. Se clona una copia aparte, hermana de
`sistema-eidas/` (ej. `.../terciario-urquiza/eidas-template/`), y ahí se edita, commitea y
pushea. Mismo patrón que `sistema-eidas-datos` y `sistema-eidas-memory`: los repos que no son
de una sola materia viven al lado de `sistema-eidas/`, no anidados adentro de una.

---

### Pipeline de evaluación

```
Grupo sube trabajo al repo GitHub (repo generado desde el template de SU materia)
        ↓
Profe corre: python3 scripts/grupos.py sync <materia>  (o /sync <materia> en Claude Code)
— clona los grupos nuevos de materias/<materia>/grupos.json, actualiza los que ya estaban —
        ↓
(Opcional) Abre Claude Code y corre: /chequear-grupo <materia> <grupo-id>
— clona el repo si hace falta y actualiza main con git pull para ese grupo puntual (no
hace falta correr sync antes solo para chequear uno); no escribe nada; da un veredicto
LISTO PARA EVALUAR / ESPERAR / PEDIR ACTUALIZACIÓN, para no generar una devolución
completa de un grupo que todavía no tiene nada evaluable —
        ↓
Abre Claude Code en sistema-eidas/ y corre: /evaluar-grupo <materia> <grupo-id>
— NO toca el repo del grupo (se queda en main, sin tocar, hasta publicar). Aplica
materias/<materia>/rubrica.md y escribe el borrador en
sistema-eidas-datos/<materia>/borradores/<grupo-id>/AAAA-MM-DD.md — commitea y pushea ahí
(repo privado del docente, no el del grupo, así que esto no lo ve nadie más). Es el único
lugar donde vive el borrador — no hay copia ni symlink —
        ↓
Profe edita el archivo de devolución directamente en sistema-eidas-datos, desde la máquina
que le quede cómoda — ajusta puntajes y texto, agrega contexto que Claude no puede ver. Si
lo edita a mano (sin Claude Code de por medio), tiene que commitear y pushear él mismo en
sistema-eidas-datos antes de seguir en otra máquina, o el cambio no viaja —
        ↓
Profe corre: python3 scripts/grupos.py publicar <materia> <grupo-id>
— busca en sistema-eidas-datos/<materia>/borradores/<grupo-id>/ los AAAA-MM-DD.md que
todavía no digan "[x] Publicado al grupo"; corta con error si no hay ninguno, o si el repo
del grupo tiene cambios sin commitear (no debería pasar — ya nada se edita ahí hasta acá).
Saca, como red de seguridad, cualquier "Confianza Claude" o "Pregunta para el docente" que
haya quedado sin sacar, tilda "Publicado al grupo", escribe cada archivo en
materias/<materia>/grupos/<grupo-id>/feedback/ del repo clonado, commitea y pushea directo
a main (no hace falta merge, no hay branch de por medio) —
— ACÁ es cuando la devolución se vuelve visible para el grupo, al pushear main —
— de paso, marca el mismo cambio en el borrador de sistema-eidas-datos y lo pushea ahí
también (bookkeeping, para que otra máquina no lo vuelva a publicar; si esto último falla,
no aborta — la devolución ya se publicó, lo importante ya pasó) —
        ↓
El mismo comando dispara automáticamente el workflow de N8N (webhook local,
no sale de esta máquina) para notificar por Gmail con un link directo al
archivo ya pusheado al repo del grupo (`.../blob/main/feedback/AAAA-MM-DD.md`,
nada se sube a Drive), con la materia incluida en el asunto del mail
```

---

### Formato del archivo de feedback

Cada archivo de devolución sigue esta estructura genérica. Las secciones de "Devolución por
sección" y las filas de la tabla de puntuación **salen de la `rubrica.md` de la materia
correspondiente** — no hay una lista fija de secciones a nivel sistema, cada materia define
las suyas:

```markdown
# Devolución — [Nombre del grupo / caso de estudio]
## Materia: [Nombre de la materia] — Comisión [XX] | Fecha: XX/XX/2026

## Puntuación

| Sección | Puntaje obtenido | Puntaje máximo | Nivel |
|---------|-----------------|---------------|-------|
| [una fila por cada sección de la rúbrica de la materia] | | | |
| Subtotal repo | | [según rúbrica] | |
| Cuestionario individual | | [según rúbrica] | |
| **Total** | | **100** | |

## Devolución por sección

### [Nombre de sección, según rúbrica]
**Confianza Claude:** Alta / Media / Baja
[observaciones]

[... una sub-sección por cada sección de la rúbrica ...]

## Pregunta para el docente
[Una pregunta específica sobre este grupo que solo el docente puede responder
— contexto del proceso grupal, presentación oral, dificultades conocidas, etc.]

## Estado
- [ ] Borrador generado por Claude
- [ ] Revisado y aprobado por Profe Pablo
- [ ] Publicado al grupo
```

`/evaluar-grupo` tilda la primera casilla al generar el borrador. La segunda la tildás vos a
mano durante la revisión. La tercera **no la toques manualmente** — `scripts/grupos.py
publicar` la tilda solo, como parte del mismo commit que hace el push, así el archivo queda
consistente con la realidad sin pasos extra.

#### Variante: devolución parcial (entrega intermedia)

Cuando la materia tiene `materias/<materia>/cronograma-2c-2026.md` y todavía quedan
secciones de la rúbrica sin darse en clase, `/evaluar-grupo` genera una devolución
**parcial** en vez de la final — evalúa solo lo que ya corresponde según el cronograma, sin
tratar lo que no se dio todavía como "Ausente". La tabla de puntuación queda así:

```markdown
## Puntuación (devolución parcial — entrega intermedia, no es la nota final del repo)

| Sección | Puntaje obtenido | Puntaje máximo | Nivel |
|---------|-----------------|---------------|-------|
| [sección en alcance] | | [según rúbrica] | |
| [sección fuera de alcance] | — | — | No corresponde todavía (ver cronograma) |
| **Subtotal evaluado** | | [suma solo de lo en alcance] | |
```

No hay fila de "Total" sobre 100 en una devolución parcial — esa tabla se arma recién en la
devolución final, cuando ya todo está en alcance. "Devolución por sección" solo lleva
sub-secciones de lo evaluado; de lo que no corresponde todavía no hace falta escribir nada.

---

### Convención al escribir un comando nuevo (`.claude/commands/*.md`)

Si un comando necesita hacer operaciones de `git` sobre el repo clonado de un grupo
(`materias/<materia>/grupos/<grupo-id>/`) **y** en algún otro paso lee un archivo a nivel de
`sistema-eidas/` (`rubrica.md`, `cronograma-2c-2026.md`, `grupos.json`, etc.), usá siempre
`git -C materias/<materia>/grupos/<grupo-id> <comando>` — nunca "entrá a esa carpeta y
corré git ...". Un `cd` real dentro de las instrucciones deja los pasos siguientes
dependiendo de que el modelo se acuerde de volver a la raíz antes de leer una ruta relativa
a `sistema-eidas/`; `-C` corre el comando ahí sin mover el directorio de trabajo real, así
que ningún paso posterior puede romperse por esto. Bug real, detectado el 2026-08-26
probando `/chequear-grupo` en vivo — ya corregido en `chequear-grupo.md`, `evaluar-grupo.md`
y `resumen-commits.md`.

---

### Bug real: devolución sin publicar que "desaparecía" al correr `sync`

Detectado el 2026-09-02 trabajando desde la notebook con una devolución en curso sin
publicar todavía. Dos problemas relacionados:

1. **`grupos.py sync`** hacía `git checkout main` sin condición alguna para **todos** los
   grupos ya clonados, incluido uno con una devolución sin publicar parada en la branch
   `feedback`. Eso sacaba `feedback/AAAA-MM-DD.md` del working tree (esa branch todavía no
   existe en `main`), dejando visible solo la copia de trabajo del docente en
   `materias/<materia>/feedback/`. **Corregido:** `sync` ahora detecta si un grupo está
   parado en `feedback` y, en ese caso, no lo toca — solo hace `git fetch origin main` (sin
   tocar el working tree) y avisa por consola.
2. Aunque el problema de arriba no hubiera pasado, la copia de trabajo era un **archivo
   independiente**, escrito una sola vez por `/evaluar-grupo` y vuelto a escribir por
   `publicar` — cualquier edición del docente hecha directamente sobre esa copia, entre
   medio, se perdía en silencio, porque `publicar` solo lee
   `grupos/<grupo-id>/feedback/AAAA-MM-DD.md`, nunca la copia. **Corregido:** la copia de
   trabajo pasó a ser un **symlink** a ese mismo archivo (`evaluar-grupo.md` paso 5,
   `marcar_publicado` en `grupos.py` como red de seguridad) — ya no hay dos archivos, así
   que no hay forma de editar el que no corresponde.

Mismo día, causa raíz de fondo: **N8N era la única pieza de infraestructura que no viajaba
entre máquinas.** `infra/n8n/.env` y `google-oauth-client.json` están en `.gitignore` (son
secretos), y el workflow/credenciales importados viven en el volumen Docker `n8n_data`, que
tampoco es portable — en una máquina nueva había que copiar archivos a mano y reconfigurar
todo por la UI. **Corregido:** mismo patrón que `grupos.json` — los secretos ahora viven en
`sistema-eidas-datos/n8n/` (repo privado, ver su `README.md`) y `infra/n8n/.env` /
`google-oauth-client.json` son symlinks a ahí. `infra/n8n/setup.sh` automatiza todo lo
demás: crea los symlinks si faltan, levanta el contenedor, e importa el workflow y las
credenciales de Gmail/Drive por CLI (`n8n import:workflow` / `import:credentials`), leyendo
`sistema-eidas-datos/n8n/credentials.json` — un export **desencriptado** de esas
credenciales (decisión explícita del docente, ver advertencia en ese README sobre qué hacer
si el repo se filtra). Único paso manual que queda: activar el workflow desde la UI — esta
versión de N8N no soporta hacerlo por CLI fuera de modo queue. Probado de punta a punta
simulando una máquina nueva (instancia con volumen Docker vacío, mismo puerto, mismos IDs de
credencial/workflow tras importar) antes de darlo por terminado.

**Actualización, más tarde el mismo día — rediseño de fondo, no solo el bug de arriba:**
Pablo notó la limitación real detrás de los dos síntomas de la sección anterior: **por
diseño, una devolución en curso no podía continuarse en otra máquina**, porque la branch
`feedback` era 100% local al repo clonado del grupo (a propósito, para que el grupo no la
viera) — el symlink de más arriba resolvía la pérdida silenciosa de ediciones, pero no la
portabilidad entre máquinas. Se sacó la branch `feedback` del medio por completo: el
borrador ahora vive como archivo normal en `sistema-eidas-datos/<materia>/borradores/`
(mismo repo privado que ya sincroniza `grupos.json` y los secretos de N8N), y `publicar`
lee de ahí en vez de mergear una branch. Esto también volvió obsoleto el symlink del punto
2 de arriba — ya no hay dos rutas para el mismo archivo, hay una sola, y está en un repo
que sí viaja entre máquinas. Ver "Pipeline de evaluación" arriba para el flujo final.

---

### Pendientes del sistema

- [x] Crear `docs/diseño-ui.md` en el template
- [x] Crear carpeta `diagramas/wireframes/` en el template
- [x] Subir template a GitHub y configurarlo como template repository (https://github.com/pablopedernera0/eidas-template)
- [x] Prerrequisitos + cheatsheet de git + recursos para estudiantes (`RECURSOS.md` en cada template) y plan de clase práctica para el docente (`guia-docente-clase-git.md`)
- [~] Apps Script en Google Forms → repo — **decisión: no se hace.** El cuestionario ya se autocalifica en Forms, y como es individual (no grupal), meterlo en el repo del grupo expondría la nota de cada estudiante al resto del equipo.
- [~] Levantar N8N en el Linode — **decisión: no es necesario por ahora.** Todo el pipeline es local; N8N puede seguir corriendo en la PC del docente indefinidamente. El Linode solo pasaría a ser necesario si un servicio externo necesitara llegarle a N8N desde internet.
- [x] Armar lógica del flow N8N en local: genera archivo → sube a "Devoluciones EIDAS" en Drive → notifica por Gmail (workflow `Evaluacion EIDAS`, exportado a `infra/n8n/workflows/evaluacion-eidas.json`)
- [x] **2026-09-03: sacado el paso de Drive.** El mail ya no linkea a una copia subida a Drive — linkea directo al archivo que `/publicar` ya pusheó al repo del grupo (`grupos.json` ya tenía el campo `repo`, alcanzó con derivar la URL del blob en el nodo "Buscar datos del grupo"). Se sacaron los nodos "Leer devolución" y "Upload file" del workflow. La credencial de Drive queda sin uso (no hace falta sacarla del import). **Pendiente: reimportar el workflow actualizado en N8N** — `infra/n8n/setup.sh` NO lo hace solo (si detecta que "Evaluacion EIDAS" ya existe, no lo toca, justamente para no desactivarlo). Hace falta reimportarlo a mano: `docker compose exec n8n n8n import:workflow --input=/home/node/data/infra/n8n/workflows/evaluacion-eidas.json` desde `infra/n8n/`, y después volver a prender el toggle "Active" en `localhost:5678` (queda inactivo tras cualquier reimport). El cambio en el JSON del repo todavía no corrió en la instancia real.
- [x] Workflow de N8N conectado a los archivos reales, con disparo automático vía Webhook (workflow activado/publicado) — `scripts/grupos.py publicar` lo llama solo al final, sin volver a tipear nada. Fallback manual: `scripts/grupos.py notificar <materia> <grupo-id> <fecha>`. Requiere `N8N_RESTRICT_FILE_ACCESS_TO` seteado en `docker-compose.yml` y el bind mount del proyecto en `/home/node/data`.
- [x] Escribir marco teórico del Sistema EIDAS (`marco-teorico-fundamentacion.md` y `marco-teorico-resumen.md`) — pendiente confirmar datos de edición de Achilli/Ander-Egg y ampliar referencia al seminario de Placci sobre IA
- [x] Soporte multi-materia (2026-08-04): reestructurado a `materias/<carrera>-<materia>-<comisión>/` — cada una con su propia `rubrica.md`, `template/` (repo GitHub propio) y `grupos.json`. `scripts/grupos.py`, `/evaluar-grupo` y el workflow de N8N ahora toman la materia como parámetro. Migrada la materia existente a `af-diseno-sistemas-web-31`.
- [ ] Armar `rubrica.md` y `template/` para las materias de Redes (ej: `af-redes-comunicaciones-31`, `iti-infraestructura-redes-21`) — pendiente, va a llevar más tiempo por ser contenido nuevo, no reutilizable de Diseño de Sistemas Web.
- [ ] **⚠️ URGENTE — migrar 14 devoluciones sin publicar que quedaron en branches `feedback`
  locales en la notebook** (rediseño del borrador movido a `sistema-eidas-datos/borradores/`,
  ver más arriba): 6 de `af-diseno-sistemas-web-31` (`easy-core-computacion`,
  `ecommerce-mundo-sport`, `GLPI`, `pos-carrefour`, `sistema-turnos`, `aberturas-los-pampas`
  — ya editadas a mano el 2026-09-02, con "Devolución docente" escrita, ver
  `bitacora-implementacion.md`) y 8 de `af-diseno-sistemas-web-32` (generadas 26/08, sin
  revisar todavía). El código nuevo de `/publicar` y `/evaluar-grupo` ya no sabe leer esa
  branch — nada se perdió (los commits siguen ahí, en la branch `feedback` de cada repo
  clonado en la notebook), pero quedaron invisibles para la herramienta hasta que alguien
  copie ese contenido a `sistema-eidas-datos/<materia>/borradores/<grupo-id>/AAAA-MM-DD.md`
  a mano (o publique esas 14 con el código viejo antes de actualizar la notebook). Pablo lo
  sabe y decidió resolverlo él mismo la próxima vez que use la notebook (2026-09-02) — no
  hacer nada automático acá sin que él lo pida explícitamente.

---

### Infraestructura

| Componente | Tecnología | Estado |
|------------|------------|--------|
| Repos de grupos | GitHub (template repository, uno por materia) | Activo |
| Cuestionarios | Google Classroom + Forms | Activo |
| Conexión Forms → repo | — | Descartado — no aporta valor suficiente (ver pendientes) |
| Automatización | N8N en Docker (`infra/n8n/`), corre local en la PC del docente, compartido entre materias; setup en máquina nueva con `infra/n8n/setup.sh` (secretos en `sistema-eidas-datos/n8n/`) | Activo — se dispara solo desde `scripts/grupos.py publicar` |
| Servidor | Linode propio de Profe Pablo | Disponible, no se usa por ahora |
| Evaluación asistida | Claude Code (local) | Activo |

---

### Marco teórico (en construcción)

- **Placci, Norma** — *La evaluación de la práctica como eje del proceso formativo* (Homo Sapiens, 2025). Evaluar prácticas exige formas más difíciles de diseñar que no admiten respuestas modelo ni reproducción.
- **Álvarez Méndez, Juan Manuel** — Evaluar para conocer vs. examinar para excluir.
- **Perrenoud, Philippe** — Las dos lógicas de la evaluación.
- **Cruce con IA** — en carreras técnicas, la IA resuelve evaluaciones que miden reproducción; las evaluaciones que miden comprensión real requieren producción, decisión y justificación — exactamente lo que EIDAS busca verificar.

---

*Sistema EIDAS — Terciario Urquiza — Rosario, 2026*

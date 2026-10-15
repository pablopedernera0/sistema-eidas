Arrancá (o reabrí) el dashboard local de estado de evaluación del Sistema EIDAS.

Este comando no toma argumentos.

Es un wrapper fino sobre `scripts/dashboard.py`: un servidor Flask que corre solo en
`127.0.0.1:8420` (nunca expuesto a la red, igual que N8N) y recalcula el estado de cada
grupo, de todas las materias, en cada request — leyendo `grupos.json` y los borradores de
`sistema-eidas-datos/<materia>/borradores/`. No escribe nada, no toca N8N, no hace push. La
página de grupos se refresca sola cada 10s.

La pestaña **Recorrer** (`/recorrer`) es un navegador de solo lectura de los clones locales
de los grupos, con dos formas: **por grupo** (todos sus archivos en el orden del template) y
**por sección** (el mismo archivo en todos los grupos, uno detrás del otro; si un grupo lo
tiene en otra ruta, muestra el archivo de nombre parecido). Flechas ← → y Shift + ← → para
moverse. Marca los archivos que cambiaron después del último borrador. Los `.puml` se
renderizan con el PlantUML local de `infra/plantuml/` (`docker compose up -d`, puerto 8090).
Tiene botones "↻ actualizar" (un grupo) y "↻ actualizar todos los grupos" (la materia): hacen
lo mismo que `/sync` (`sync_grupo` de `grupos.py`, pull de `main`; no tocan un clon parado en
otra branch o con cambios sin commitear). Es la única acción del navegador, y no escribe nada
en los repos de los grupos ni pushea.

La pestaña **Notas** (`/notas`) muestra, por alumno, el cuestionario individual (Classroom +
Forms, /30) más la última devolución del repo (/70), con filtro por estado. Lee el CSV que deja
`scripts/notas.py <materia>`; el botón "↻ traer de Classroom y Forms" lo vuelve a generar por API
(solo lectura). Requiere `sistema-eidas-datos/<materia>/classroom.json` y el token de
`scripts/classroom.py` autorizado en esa máquina.

Pasos:
1. Corré, detached en background (así sigue corriendo aunque termine esta sesión de
   Claude Code):
   `nohup /usr/bin/python3 scripts/dashboard.py > dashboard.log 2>&1 & disown`
2. Esperá ~1 segundo y mirá `dashboard.log` para saber si arrancó de cero o ya estaba
   corriendo — el script mismo detecta si el puerto 8420 ya está ocupado y no lo duplica,
   solo abre el navegador de nuevo.
3. Confirmale al usuario la URL (`http://127.0.0.1:8420`) y que el script va a intentar
   abrirla solo en el navegador. Si no hay entorno gráfico disponible acá, decile la URL
   igual para que la abra a mano.
4. Solo si pregunta cómo pararlo: se mata con `pkill -f scripts/dashboard.py` (no hay un
   comando de stop todavía).

**No es el lugar para acciones que modifiquen algo** (publicar, notificar, etc.; el único botón de acción es el "actualizar" de Recorrer, equivalente a `/sync`) — esas
siguen siendo solo terminal, a propósito (ver `sync.md`). Si el dashboard suma botones de
acción más adelante, van a necesitar su propia revisión de riesgo antes de agregarse acá.

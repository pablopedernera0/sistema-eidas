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
Lee los clones tal como están: correr `/sync <materia>` antes.

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

**No es el lugar para acciones que modifiquen algo** (publicar, notificar, etc.) — esas
siguen siendo solo terminal, a propósito (ver `sync.md`). Si el dashboard suma botones de
acción más adelante, van a necesitar su propia revisión de riesgo antes de agregarse acá.

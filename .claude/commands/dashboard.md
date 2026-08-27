Arrancá (o reabrí) el dashboard local de estado de evaluación del Sistema EIDAS.

Este comando no toma argumentos.

Es un wrapper fino sobre `scripts/dashboard.py`: un servidor Flask que corre solo en
`127.0.0.1:8420` (nunca expuesto a la red, igual que N8N) y recalcula el estado de cada
grupo, de todas las materias, en cada request — leyendo `grupos.json` y la branch local
`feedback` de cada repo de grupo (que nunca se pushea). No escribe nada, no toca N8N, no
hace push. La página se refresca sola cada 10s.

Pasos:
1. Corré, detached en background (así sigue corriendo aunque termine esta sesión de
   Claude Code):
   `nohup python3 scripts/dashboard.py > dashboard.log 2>&1 & disown`
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

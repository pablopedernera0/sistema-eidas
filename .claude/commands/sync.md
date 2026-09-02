Traé al día los repos de los grupos de una materia del Sistema EIDAS.

`$ARGUMENTS` trae un valor: `<materia>`. Si `$ARGUMENTS` no lo trae, pedíselo al usuario
antes de seguir — es el nombre de carpeta dentro de `materias/` (ej:
`af-diseno-sistemas-web-31`).

Este comando es un wrapper fino: solo corre
`python3 scripts/grupos.py sync <materia>` y reporta la salida tal cual — no interpreta
nada, no escribe nada por su cuenta. Clona los grupos nuevos de
`materias/<materia>/grupos.json` que todavía no estén en `materias/<materia>/grupos/`, y
hace `git checkout main` + `git pull origin main` de los que ya estaban clonados (si algún
repo de grupo está parado en una branch que no es `main` — no debería pasar en el flujo
normal — lo deja intacto y avisa en vez de tocarlo).

Después de correrlo, resumí en una línea qué grupos se clonaron por primera vez (si
alguno) y cuáles ya estaban — no hace falta repetir la salida completa del script si fue
larga.

**No es el lugar para `publicar` ni `notificar`.** `publicar` tiene su propio comando,
`/publicar` (`.claude/commands/publicar.md`) — ahí el freno de confirmación se mueve al
chat en vez de perderse, así que no hace falta duplicarlo acá. `notificar` (el reintento
manual de la notificación de N8N si algo falló) sigue siendo solo de terminal
(`python3 scripts/grupos.py notificar <materia> <grupo-id> <AAAA-MM-DD>`) — es un comando
de bajo riesgo (no pushea nada, solo reintenta un webhook), no justifica su propio wrapper
todavía.

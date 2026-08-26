Traé al día los repos de los grupos de una materia del Sistema EIDAS.

`$ARGUMENTS` trae un valor: `<materia>`. Si `$ARGUMENTS` no lo trae, pedíselo al usuario
antes de seguir — es el nombre de carpeta dentro de `materias/` (ej:
`af-diseno-sistemas-web-31`).

Este comando es un wrapper fino: solo corre
`python3 scripts/grupos.py sync <materia>` y reporta la salida tal cual — no interpreta
nada, no escribe nada por su cuenta, no toca ninguna branch `feedback`. Clona los grupos
nuevos de `materias/<materia>/grupos.json` que todavía no estén en
`materias/<materia>/grupos/`, y hace `git checkout main` + `git pull origin main` de los
que ya estaban clonados.

Después de correrlo, resumí en una línea qué grupos se clonaron por primera vez (si
alguno) y cuáles ya estaban — no hace falta repetir la salida completa del script si fue
larga.

**No es el lugar para `publicar` ni `notificar`.** Esos dos siguen siendo solo comandos de
terminal (`python3 scripts/grupos.py publicar/notificar ...`), a propósito: `publicar`
tiene un prompt de confirmación antes de un push que hace visible la devolución para el
grupo y dispara un mail — ese es el último freno antes de algo que no se puede deshacer
del todo, y envolverlo acá significaría pasarle `--yes` para que no quede esperando input,
que es sacarte ese freno. Si el usuario pide un `/publicar` o `/notificar`, avisale esto
antes de crearlo.

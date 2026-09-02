Chequeá si un grupo del Sistema EIDAS está en condiciones de ser evaluado, sin generar
ninguna devolución todavía. Es el paso previo a `/evaluar-grupo` — sirve para decidir si
conviene evaluar ahora o esperar/pedirle al grupo que actualice, sin dejar rastro de una
evaluación (buena o mala) en ningún lado.

`$ARGUMENTS` trae dos valores separados por espacio: `<materia> <grupo-id>`. Si
`$ARGUMENTS` no trae ambos valores, pedíselos al usuario antes de seguir.

Este comando **no genera ninguna devolución**: no escribe ni commitea ningún archivo, ni
en `materias/<materia>/grupos/<grupo-id>/` ni en `sistema-eidas-datos`. Sí actualiza `main`
con lo último del remoto (paso 2) — eso no cuenta como "generar" nada, es la misma
actualización que hace `sync`.

Seguí estos pasos, en orden:

1. **Asegurar que el repo está clonado.** Si `materias/<materia>/grupos/<grupo-id>/` no
   existe todavía, corré `python3 scripts/grupos.py sync <materia>` (clona todos los grupos
   nuevos de esa materia, no solo este) y seguí desde el paso 2.

2. **Actualizar y traer lo último.** Usá `git -C materias/<materia>/grupos/<grupo-id>
   checkout main` y `git -C materias/<materia>/grupos/<grupo-id> pull origin main` — `-C`
   corre el comando ahí sin hacer `cd`, así no dependés de en qué carpeta haya quedado
   parada la terminal por un paso anterior.
   Fijate cuándo fue el último commit con
   `git -C materias/<materia>/grupos/<grupo-id> log -1 --format="%ad %s" --date=relative`.

3. **Determinar el alcance según el cronograma.** Todas las rutas de este paso son
   relativas a la raíz de `sistema-eidas/` (no a la carpeta del grupo del paso 2 — `git -C`
   no te movió de ahí, así que no hace falta ni corregir nada). Si existe
   `materias/<materia>/cronograma-2c-2026.md`, buscá su tabla (columna "Sección de la
   rúbrica" o equivalente) y usá la fecha de hoy (`date +%d/%m/%Y`) para ubicar hasta qué
   fila del cronograma ya se dio clase. Las secciones de `rubrica.md` que aparecen en esa
   fila o en filas anteriores están **en alcance** — son las que corresponde chequear hoy.
   Las que aparecen solo en filas con fecha futura están **fuera de alcance todavía** — no
   se espera que el grupo tenga nada ahí, así que no cuentan como "Ausente". La sección
   "Proceso: evolución sobre la entrega intermedia" (si la rúbrica la tiene) queda siempre
   fuera de alcance acá — solo se evalúa en la entrega final, con `/evaluar-grupo`.

   Si `materias/<materia>/cronograma-2c-2026.md` no existe para esta materia, todas las
   secciones de `rubrica.md` quedan en alcance (comportamiento de antes, sin cambios).

4. **Contar commits (contexto liviano, no pesa en el veredicto).** Corré
   `git -C materias/<materia>/grupos/<grupo-id> log --oneline main | wc -l` para el total,
   y por cada archivo/carpeta relevante de la rúbrica (README, `integrantes.md`, cada
   archivo de `docs/`, `diagramas/`) corré
   `git -C materias/<materia>/grupos/<grupo-id> log --oneline -- <path> | wc -l` (el
   `<path>` es relativo a esa carpeta, ej. `docs/requisitos.md`) para ver si tiene un solo
   commit (apareció de una) o varios (se retocó más de una vez). Esto es solo un dato de
   contexto para vos — la cantidad de commits no dice nada sobre si el trabajo está bien,
   así que no lo uses para decidir el veredicto del paso 6. Si querés el detalle fino de
   qué se revisó y en qué orden, para eso está `/resumen-commits <materia> <grupo-id>`
   (comando aparte).

5. **Leer el contenido actual** (`materias/<materia>/grupos/<grupo-id>/README.md`,
   `integrantes.md`, `docs/`, `diagramas/`) y contrastarlo, sección por sección, contra las
   secciones **en alcance** del paso 3 (no las que todavía no corresponden) — no para
   puntuar, sino para clasificar cada una en una de tres categorías:
   - **Evaluable:** hay contenido real y específico de este grupo para juzgar.
   - **Insuficiente:** existe el archivo/sección pero es un placeholder, está vacío, o es
     genérico (copiado del template sin adaptar).
   - **Ausente:** no existe nada de esa sección todavía, y ya correspondía tenerla según
     el cronograma.

6. **Dar un veredicto único**, uno de estos tres, con la razón concreta — basado solo en
   las secciones en alcance, nunca en las que todavía no corresponden:
   - `LISTO PARA EVALUAR` — la mayoría de las secciones en alcance son evaluables; los
     huecos que queden se pueden señalar como observaciones normales de una devolución.
   - `ESPERAR` — hay avance real pero todavía temprano (ej. el grupo viene subiendo commits
     seguido y es capaz de que actualice pronto); recomendable esperar antes que evaluar
     una foto parcial.
   - `PEDIR ACTUALIZACIÓN` — hay secciones en alcance en "Ausente" o "Insuficiente" sin
     señales de que vayan a completarse solas (ej. sin commits hace mucho, o el placeholder
     del template intacto); conviene contactar al grupo antes de evaluar.

7. **Reportar en el chat** (nada de esto va a archivo):
   - El veredicto del punto 6.
   - Una lista corta de qué está evaluable vs. insuficiente/ausente, sección por sección,
     **solo de lo que está en alcance**.
   - Aparte, y sin que pese en el veredicto, una línea con las secciones que todavía no
     corresponden según el cronograma (paso 3) — para que quede claro que no son un hueco,
     sino algo que todavía no se dio.
   - El total de commits del punto 4, y cuántos de los archivos relevantes tienen un solo
     commit vs. varios — una línea, sin interpretarlo más que eso.
   - Si el veredicto es `PEDIR ACTUALIZACIÓN` o `ESPERAR`, un mensaje breve sugerido para
     mandarle al grupo (usando el email de `materias/<materia>/grupos.json`, aunque el envío
     en sí lo hace el docente a mano — este comando no manda nada).
   - Si el veredicto es `LISTO PARA EVALUAR`, recordá que el siguiente paso es
     `/evaluar-grupo <materia> <grupo-id>`.

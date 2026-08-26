Chequeá si un grupo del Sistema EIDAS está en condiciones de ser evaluado, sin generar
ninguna devolución todavía. Es el paso previo a `/evaluar-grupo` — sirve para decidir si
conviene evaluar ahora o esperar/pedirle al grupo que actualice, sin dejar rastro de una
evaluación (buena o mala) en la branch local `feedback`.

`$ARGUMENTS` trae dos valores separados por espacio: `<materia> <grupo-id>`. Si
`$ARGUMENTS` no trae ambos valores, pedíselos al usuario antes de seguir.

Este comando **no genera ninguna devolución**: no crea ni cambia a la branch `feedback`, ni
escribe ni commitea ningún archivo, ni en `materias/<materia>/grupos/<grupo-id>/` ni en
`materias/<materia>/feedback/`. Sí actualiza `main` con lo último del remoto (paso 2) —
eso no cuenta como "generar" nada, es la misma actualización que hace `sync`.

Seguí estos pasos, en orden:

1. **Asegurar que el repo está clonado.** Si `materias/<materia>/grupos/<grupo-id>/` no
   existe todavía, corré `python3 scripts/grupos.py sync <materia>` (clona todos los grupos
   nuevos de esa materia, no solo este) y seguí desde el paso 2.

2. **Actualizar y traer lo último.** Dentro de `materias/<materia>/grupos/<grupo-id>/`,
   corré `git checkout main` y `git pull origin main` (no toques la branch `feedback`
   aunque exista), y fijate cuándo fue el último commit
   (`git log -1 --format="%ad %s" --date=relative`).

3. **Contar commits (contexto liviano, no pesa en el veredicto).** Corré
   `git log --oneline main | wc -l` para el total, y por cada archivo/carpeta relevante de
   la rúbrica (README, `integrantes.md`, cada archivo de `docs/`, `diagramas/`) corré
   `git log --oneline -- <path> | wc -l` para ver si tiene un solo commit (apareció de una)
   o varios (se retocó más de una vez). Esto es solo un dato de contexto para vos — la
   cantidad de commits no dice nada sobre si el trabajo está bien, así que no lo uses para
   decidir el veredicto del paso 5. Si querés el detalle fino de qué se revisó y en qué
   orden, para eso está `/resumen-commits <materia> <grupo-id>` (comando aparte).

4. **Leer el contenido actual** (README, `integrantes.md`, `docs/`, `diagramas/`) y
   contrastarlo, sección por sección, contra `materias/<materia>/rubrica.md` — no para
   puntuar, sino para clasificar cada sección de la rúbrica en una de tres categorías:
   - **Evaluable:** hay contenido real y específico de este grupo para juzgar.
   - **Insuficiente:** existe el archivo/sección pero es un placeholder, está vacío, o es
     genérico (copiado del template sin adaptar).
   - **Ausente:** no existe nada de esa sección todavía.

5. **Dar un veredicto único**, uno de estos tres, con la razón concreta:
   - `LISTO PARA EVALUAR` — la mayoría de las secciones son evaluables; los huecos que
     queden se pueden señalar como observaciones normales de una devolución.
   - `ESPERAR` — hay avance real pero todavía temprano (ej. el grupo viene subiendo commits
     seguido y es capaz de que actualice pronto); recomendable esperar antes que evaluar
     una foto parcial.
   - `PEDIR ACTUALIZACIÓN` — hay secciones clave en "Ausente" o "Insuficiente" sin señales
     de que vayan a completarse solas (ej. sin commits hace mucho, o el placeholder del
     template intacto); conviene contactar al grupo antes de evaluar.

6. **Reportar en el chat** (nada de esto va a archivo):
   - El veredicto del punto 5.
   - Una lista corta de qué está evaluable vs. insuficiente/ausente, sección por sección de
     la rúbrica.
   - El total de commits del punto 3, y cuántos de los archivos relevantes tienen un solo
     commit vs. varios — una línea, sin interpretarlo más que eso.
   - Si el veredicto es `PEDIR ACTUALIZACIÓN` o `ESPERAR`, un mensaje breve sugerido para
     mandarle al grupo (usando el email de `materias/<materia>/grupos.json`, aunque el envío
     en sí lo hace el docente a mano — este comando no manda nada).
   - Si el veredicto es `LISTO PARA EVALUAR`, recordá que el siguiente paso es
     `/evaluar-grupo <materia> <grupo-id>`.

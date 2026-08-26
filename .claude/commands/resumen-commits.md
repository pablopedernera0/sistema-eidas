Analizá el historial de commits de un grupo del Sistema EIDAS para ver **cómo trabajaron a
lo largo del tiempo**, no qué tienen hoy. Es un comando informativo, aparte de
`/chequear-grupo` y `/evaluar-grupo`: no decide si el grupo está listo, no genera
devolución, y **no se guarda en ningún archivo ni entra en la branch `feedback`**. Sirve
como insumo para tu criterio — por ejemplo, para preparar preguntas de una defensa oral, o
como el "contexto que Claude no puede ver" que agregás a mano al revisar una devolución.

`$ARGUMENTS` trae dos valores separados por espacio: `<materia> <grupo-id>`. Si
`$ARGUMENTS` no trae ambos valores, pedíselos al usuario antes de seguir.

**Lo que este comando NO es:** no es detección de uso de IA, no es una forma de calcular
"aporte" real de cada integrante, y el resultado no debería pesar en la nota salvo que
`materias/<materia>/rubrica.md` declare explícitamente un criterio de proceso/trazabilidad
— si no está en la rúbrica, esto es solo para tu ojo, no para justificar un puntaje.

Seguí estos pasos, en orden:

1. **Asegurar que el repo está clonado y actualizado.** Si
   `materias/<materia>/grupos/<grupo-id>/` no existe, corré
   `python3 scripts/grupos.py sync <materia>` primero. Si ya existe, usá
   `git -C materias/<materia>/grupos/<grupo-id> checkout main` y
   `git -C materias/<materia>/grupos/<grupo-id> pull origin main` (no toques `feedback`
   aunque exista) — `-C` evita el `cd`, así no hay que acordarse de volver a ningún lado.

2. **Traer el historial completo de `main`** con fecha, autor y archivos tocados:
   ```
   git -C materias/<materia>/grupos/<grupo-id> log --format='--- %h|%ad|%an|%s' --date=short --name-only main
   ```
   Usá esto como fuente de todo lo que sigue — no inventes commits que no aparezcan acá.

3. **Armar la línea de tiempo por archivo**, para cada archivo/carpeta relevante de la
   rúbrica (README, `integrantes.md`, cada archivo de `docs/`, `diagramas/`): listá, en
   orden cronológico, cada commit que lo tocó (fecha, autor, mensaje). Clasificá cada
   archivo en una de estas categorías:
   - **Bloque único:** apareció completo en un solo commit y nunca se volvió a tocar.
   - **Revisado:** tiene más de un commit separados en el tiempo (no todos el mismo día) —
     señal de que volvieron sobre el contenido, no necesariamente de que "mejoraron" nada,
     eso lo juzgás vos mirando el contenido real con `/chequear-grupo` o `/evaluar-grupo`.
   - **Fragmentado el mismo día:** varios commits pero todos concentrados en una sola
     sesión — no es lo mismo que "revisado a lo largo del tiempo", acláralo así.

4. **Desglose por autor** (con la advertencia de abajo, que tenés que incluir siempre que
   muestres esta sección): para cada persona que aparece en `%an`, cuántos commits hizo y
   qué archivos/carpetas tocó. Mostralo como tabla simple, sin calcular porcentajes de
   "aporte" ni ranking entre integrantes.

   **Advertencia fija a incluir en el reporte, siempre:** "Este desglose muestra quién
   *commiteó* cada cambio, no quién lo *hizo* — es común que una sola persona del grupo
   pushee el trabajo de los demás. No uses esto solo para inferir aporte individual; para
   eso sirve mejor una charla corta con el grupo."

5. **Reportar en el chat** (nada de esto va a archivo):
   - Resumen de 2-3 líneas: total de commits, rango de fechas (primer commit → último), y
     cuántos archivos relevantes quedaron en cada categoría del punto 3.
   - La línea de tiempo del punto 3, agrupada por archivo.
   - La tabla y advertencia del punto 4.
   - Si casi todo quedó en "Bloque único" y en una sola sesión, decilo explícitamente como
     una observación neutral ("el repo no muestra iteración visible en el historial") — sin
     concluir que copiaron o usaron IA, solo que el proceso no dejó rastro en git.

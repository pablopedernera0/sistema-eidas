Generá el borrador de devolución para un grupo del Sistema EIDAS.

`$ARGUMENTS` trae dos valores separados por espacio: `<materia> <grupo-id>`. Ejemplo:
`af-diseno-sistemas-web-31 grupo-01-nombre`. La `materia` es el nombre de carpeta dentro de
`materias/` (ej: `af-diseno-sistemas-web-31`), y `grupo-id` es el `id` tal como figura en
`materias/<materia>/grupos.json`. Si `$ARGUMENTS` no trae ambos valores, pedíselos al
usuario antes de seguir.

Seguí estos pasos, en orden:

1. **Verificar que el repo está clonado.** Si `materias/<materia>/grupos/<grupo-id>/` no
   existe, avisá que hay que correr `python3 scripts/grupos.py sync <materia>` primero, y
   no sigas.

2. **Preparar la branch local.** Dentro de `materias/<materia>/grupos/<grupo-id>/`:
   - Si la branch `feedback` no existe todavía, creala desde `main` (`git checkout -b feedback`).
   - Si ya existe, hacé `git checkout feedback` (no la recrees, no perdés lo que ya estaba
     ahí a menos que la vayas a reemplazar a propósito).
   - Esta branch es **local únicamente** — no la pushees en ningún paso de este comando.

3. **Leer y evaluar.** Revisá el contenido de `materias/<materia>/grupos/<grupo-id>/`
   (README, integrantes.md, `docs/`, `diagramas/`) y aplicá los criterios de
   `materias/<materia>/rubrica.md` — esa es la rúbrica de esta materia específica, no
   asumas la de otra. Prestá atención a los criterios transversales que pide `CLAUDE.md`:
   coherencia entre artefactos, profundidad de las justificaciones, y manejo de excepciones
   (no solo el camino feliz).

4. **Escribir el archivo de devolución**, siguiendo el formato genérico de la sección
   "Formato del archivo de feedback" de `CLAUDE.md` (una fila de puntuación y una
   sub-sección "Devolución por sección" por cada sección de `rubrica.md` de esta materia —
   los nombres de sección salen de la rúbrica, no están hardcodeados), en dos lugares:
   - `materias/<materia>/grupos/<grupo-id>/feedback/AAAA-MM-DD.md` (fecha de hoy) — este es
     el que se pushea cuando el docente lo apruebe.
   - `materias/<materia>/feedback/<grupo-id>_AAAA-MM-DD.md` — copia de trabajo del docente,
     no se pushea a ningún repo de grupo.

   Completá honestamente el nivel de "Confianza Claude" (Alta/Media/Baja) en cada sección,
   y dejá una "Pregunta para el docente" real y específica de este grupo — no una genérica.

5. **Commitear en la branch `feedback`** (dentro de
   `materias/<materia>/grupos/<grupo-id>/`) el archivo del punto 4 que vive en ese repo.
   Mensaje de commit sugerido: `Devolución AAAA-MM-DD`. No commitees ni pushees nada en
   `main`. No pushees la branch `feedback`.

6. **Reportar al final:** un resumen breve de la puntuación por sección y el puntaje total
   sobre el máximo del repo grupal (según `rubrica.md` de la materia), y recordale al
   docente que antes de publicar tiene que revisar el diff con `git diff main..feedback`
   dentro de `materias/<materia>/grupos/<grupo-id>/`, y que la publicación (que también
   dispara la notificación) se hace con
   `python3 scripts/grupos.py publicar <materia> <grupo-id>`.

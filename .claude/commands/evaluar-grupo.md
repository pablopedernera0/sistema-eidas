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

2. **Preparar la branch local.** Usá `git -C materias/<materia>/grupos/<grupo-id> ...` para
   todo esto (no hagas `cd` — así no arrastrás el directorio de trabajo a los pasos
   siguientes, que necesitan rutas relativas a la raíz de `sistema-eidas/`):
   - Si la branch `feedback` no existe todavía, creala desde `main`
     (`git -C materias/<materia>/grupos/<grupo-id> checkout -b feedback`).
   - Si ya existe, hacé `git -C materias/<materia>/grupos/<grupo-id> checkout feedback`
     (no la recrees, no perdés lo que ya estaba ahí a menos que la vayas a reemplazar a
     propósito).
   - Esta branch es **local únicamente** — no la pushees en ningún paso de este comando.

3. **Determinar el alcance según el cronograma.** Todas las rutas de este paso son
   relativas a la raíz de `sistema-eidas/` — el paso 2 no te movió de ahí. Si existe
   `materias/<materia>/cronograma-2c-2026.md`, buscá su tabla ("Sección de la rúbrica" o
   columna equivalente) y usá la fecha de hoy (`date +%d/%m/%Y`) para ubicar hasta qué fila
   ya se dio clase. Las secciones de `rubrica.md` de esa fila o anteriores están **en
   alcance**; las de filas con fecha futura están **fuera de alcance todavía** — esta va a
   ser una devolución **parcial**, no la final. Si todas las secciones de la rúbrica ya
   están en alcance (o la materia no tiene `cronograma-2c-2026.md`), es una devolución
   **final**: evaluás todo como siempre, sin nada de esto.

   "Proceso: evolución sobre la entrega intermedia" (si la rúbrica la tiene) solo entra en
   alcance en una devolución final — nunca la puntúes en una parcial, todavía no hay nada
   que comparar.

4. **Leer y evaluar.** Revisá el contenido de `materias/<materia>/grupos/<grupo-id>/`
   (README, integrantes.md, `docs/`, `diagramas/`) y aplicá los criterios de
   `materias/<materia>/rubrica.md` — esa es la rúbrica de esta materia específica, no
   asumas la de otra — **solo para las secciones en alcance del paso 3**. Prestá atención a
   los criterios transversales que pide `CLAUDE.md`: coherencia entre artefactos,
   profundidad de las justificaciones, y manejo de excepciones (no solo el camino feliz).

   Si la rúbrica de esta materia incluye la sección "Proceso: evolución sobre la entrega
   intermedia", juntá además lo que hace falta para esa sección (no la puntúes todavía sin
   esto):
   - Buscá en `materias/<materia>/grupos/<grupo-id>/feedback/` si hay algún
     `AAAA-MM-DD.md` de fecha anterior a hoy (la devolución de una entrega intermedia). Si
     existe, leela y anotá qué observaciones señalaba.
   - Corré
     `git -C materias/<materia>/grupos/<grupo-id> log --format='--- %h|%ad|%s' --date=short --name-only main`
     y clasificá, para README/`integrantes.md`/cada archivo de `docs/`/`diagramas/`, si se
     tocó en más de una fecha distinta (revisado en el tiempo) o solo apareció en un bloque
     cerca de la fecha de esta evaluación. **No hagas el desglose por autor acá** — esa
     parte es de `/resumen-commits`, no de esta sección de la rúbrica.
   - Si no hay devolución intermedia previa para este grupo, basá el nivel de esta sección
     solo en el patrón del historial — no lo trates como "Insuficiente" automáticamente,
     puede ser una causa ajena al grupo (ver criterio transversal de la rúbrica).

5. **Escribir el archivo de devolución**, siguiendo el formato genérico de la sección
   "Formato del archivo de feedback" de `CLAUDE.md` (una fila de puntuación y una
   sub-sección "Devolución por sección" por cada sección **en alcance** de `rubrica.md` de
   esta materia — los nombres de sección salen de la rúbrica, no están hardcodeados), en
   dos lugares:
   - `materias/<materia>/grupos/<grupo-id>/feedback/AAAA-MM-DD.md` (fecha de hoy) — este es
     el que se pushea cuando el docente lo apruebe.
   - `materias/<materia>/feedback/<grupo-id>_AAAA-MM-DD.md` — copia de trabajo del docente,
     no se pushea a ningún repo de grupo.

   Si el paso 3 determinó que esto es una **devolución parcial**, seguí la variante de
   formato "Devolución parcial (entrega intermedia)" de `CLAUDE.md`: en la tabla de
   puntuación, las secciones fuera de alcance van con puntaje "—" y la aclaración "no
   corresponde todavía (ver cronograma)" en vez de un puntaje o nivel — no las cuentes en
   ningún subtotal ni las trates como Ausente. El subtotal y el total de esta devolución
   son solo sobre lo evaluado, dejando explícito que no es la nota final del repo grupal.

   Completá honestamente el nivel de "Confianza Claude" (Alta/Media/Baja) en cada sección
   evaluada, y dejá una "Pregunta para el docente" real y específica de este grupo — no una
   genérica.

6. **Commitear en la branch `feedback`** el archivo del punto 5 que vive en
   `materias/<materia>/grupos/<grupo-id>/feedback/`, usando
   `git -C materias/<materia>/grupos/<grupo-id> add feedback/AAAA-MM-DD.md` y
   `git -C materias/<materia>/grupos/<grupo-id> commit -m "..."`. Mensaje de commit
   sugerido: `Devolución AAAA-MM-DD` (o `Devolución parcial AAAA-MM-DD` si corresponde). No
   commitees ni pushees nada en `main`. No pushees la branch `feedback`.

7. **Reportar al final:** un resumen breve de la puntuación por sección evaluada y el
   puntaje obtenido sobre el máximo de lo evaluado (aclarando si es parcial o final), y
   recordale al docente que antes de publicar tiene que revisar el diff con
   `git -C materias/<materia>/grupos/<grupo-id> diff main..feedback`, y que la publicación
   (que también dispara la notificación) se hace con
   `python3 scripts/grupos.py publicar <materia> <grupo-id>`.

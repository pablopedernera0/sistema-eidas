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

2. **No toques el repo del grupo todavía.** El borrador de esta devolución no vive ahí — va
   a `sistema-eidas-datos/<materia>/borradores/<grupo-id>/` (repo privado del docente,
   hermano de `sistema-eidas/`, ya sincronizado entre sus máquinas). El repo clonado del
   grupo se queda en `main`, sin tocar, hasta que se publique.

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
   esta materia — los nombres de sección salen de la rúbrica, no están hardcodeados), en:
   - `sistema-eidas-datos/<materia>/borradores/<grupo-id>/AAAA-MM-DD.md` (fecha de hoy;
     creá los directorios que hagan falta con `mkdir -p`). Este es el **único** lugar donde
     vive el borrador — no hay copia aparte ni symlink. El docente lo edita ahí
     directamente, en cualquiera de sus máquinas, hasta publicarlo.

   Si el paso 3 determinó que esto es una **devolución parcial**, seguí la variante de
   formato "Devolución parcial (entrega intermedia)" de `CLAUDE.md`: en la tabla de
   puntuación, las secciones fuera de alcance van con puntaje "—" y la aclaración "no
   corresponde todavía (ver cronograma)" en vez de un puntaje o nivel — no las cuentes en
   ningún subtotal ni las trates como Ausente. El subtotal y el total de esta devolución
   son solo sobre lo evaluado, dejando explícito que no es la nota final del repo grupal.

   Completá honestamente el nivel de "Confianza Claude" (Alta/Media/Baja) en cada sección
   evaluada, y dejá una "Pregunta para el docente" real y específica de este grupo — no una
   genérica.

6. **Commitear y pushear en `sistema-eidas-datos`** el archivo del punto 5 — **no** en
   `sistema-eidas` ni en el repo del grupo:
   ```
   git -C ../sistema-eidas-datos add <materia>/borradores/<grupo-id>/AAAA-MM-DD.md
   git -C ../sistema-eidas-datos commit -m "Devolución AAAA-MM-DD para <grupo-id>"
   git -C ../sistema-eidas-datos push
   ```
   (mensaje `Devolución parcial AAAA-MM-DD para <grupo-id>` si corresponde). Pushealo — es
   un repo privado del docente, no el del grupo, así que esto es lo que hace que el
   borrador esté disponible para seguir editándolo desde otra máquina.

7. **Reportar al final:** un resumen breve de la puntuación por sección evaluada y el
   puntaje obtenido sobre el máximo de lo evaluado (aclarando si es parcial o final), y
   recordale al docente que:
   - Puede seguir editando el archivo directamente en
     `sistema-eidas-datos/<materia>/borradores/<grupo-id>/AAAA-MM-DD.md` — si lo edita a
     mano (sin pasar por acá), tiene que commitear y pushear en `sistema-eidas-datos` él
     mismo antes de cambiar de máquina, o el cambio no viaja.
   - La publicación (que lee ese archivo, lo pushea al repo del grupo, y dispara la
     notificación) se hace con `python3 scripts/grupos.py publicar <materia> <grupo-id>`.

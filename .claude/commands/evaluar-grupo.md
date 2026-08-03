Generá el borrador de devolución para el grupo `$ARGUMENTS` del Sistema EIDAS.

Grupo objetivo: `$ARGUMENTS` (este es el `id` tal como figura en `grupos.json`).

Seguí estos pasos, en orden:

1. **Verificar que el repo está clonado.** Si `grupos/$ARGUMENTS/` no existe, avisá que hay
   que correr `python3 scripts/grupos.py sync` primero, y no sigas.

2. **Preparar la branch local.** Dentro de `grupos/$ARGUMENTS/`:
   - Si la branch `feedback` no existe todavía, creala desde `main` (`git checkout -b feedback`).
   - Si ya existe, hacé `git checkout feedback` (no la recrees, no perdés lo que ya estaba
     ahí a menos que la vayas a reemplazar a propósito).
   - Esta branch es **local únicamente** — no la pushees en ningún paso de este comando.

3. **Leer y evaluar.** Revisá el contenido de `grupos/$ARGUMENTS/` (README, integrantes.md,
   `docs/`, `diagramas/`) y aplicá los criterios de `rubrica.md` (raíz de `sistema-eidas/`).
   Prestá atención a los criterios transversales que pide `CLAUDE.md`: coherencia entre
   artefactos, profundidad de las justificaciones, y manejo de excepciones (no solo el
   camino feliz).

4. **Escribir el archivo de devolución**, siguiendo exactamente el formato de la sección
   "Formato del archivo de feedback" de `CLAUDE.md`, en dos lugares:
   - `grupos/$ARGUMENTS/feedback/AAAA-MM-DD.md` (fecha de hoy) — este es el que se pushea
     cuando el docente lo apruebe.
   - `sistema-eidas/feedback/$ARGUMENTS_AAAA-MM-DD.md` — copia de trabajo del docente, no
     se pushea a ningún repo de grupo.

   Completá honestamente el nivel de "Confianza Claude" (Alta/Media/Baja) en cada sección,
   y dejá una "Pregunta para el docente" real y específica de este grupo — no una genérica.

5. **Commitear en la branch `feedback`** (dentro de `grupos/$ARGUMENTS/`) el archivo del
   punto 4 que vive en ese repo. Mensaje de commit sugerido: `Devolución AAAA-MM-DD`.
   No commitees ni pushees nada en `main`. No pushees la branch `feedback`.

6. **Reportar al final:** un resumen breve de la puntuación por sección y el puntaje total
   sobre 70, y recordale al docente que antes de publicar tiene que revisar el diff con
   `git diff main feedback` dentro de `grupos/$ARGUMENTS/`, y que la publicación se hace
   con `python3 scripts/grupos.py publicar $ARGUMENTS`.

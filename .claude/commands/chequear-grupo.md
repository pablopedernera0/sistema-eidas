Chequeá si un grupo del Sistema EIDAS está en condiciones de ser evaluado, sin generar
ninguna devolución todavía. Es el paso previo a `/evaluar-grupo` — sirve para decidir si
conviene evaluar ahora o esperar/pedirle al grupo que actualice, sin dejar rastro de una
evaluación (buena o mala) en la branch local `feedback`.

`$ARGUMENTS` trae dos valores separados por espacio: `<materia> <grupo-id>`. Si
`$ARGUMENTS` no trae ambos valores, pedíselos al usuario antes de seguir.

Este comando es **de solo lectura**: en ningún paso creás ni cambiás de branch, ni escribís
ni commiteás ningún archivo, ni en `materias/<materia>/grupos/<grupo-id>/` ni en
`materias/<materia>/feedback/`.

Seguí estos pasos, en orden:

1. **Verificar que el repo está clonado.** Si `materias/<materia>/grupos/<grupo-id>/` no
   existe, avisá que hay que correr `python3 scripts/grupos.py sync <materia>` primero, y
   no sigas.

2. **Traer lo último sin generar nada.** Dentro de `materias/<materia>/grupos/<grupo-id>/`,
   quedate en `main` (no toques la branch `feedback` aunque exista) y fijate cuándo fue el
   último commit (`git log -1 --format="%ad %s" --date=relative`).

3. **Leer el contenido actual** (README, `integrantes.md`, `docs/`, `diagramas/`) y
   contrastarlo, sección por sección, contra `materias/<materia>/rubrica.md` — no para
   puntuar, sino para clasificar cada sección de la rúbrica en una de tres categorías:
   - **Evaluable:** hay contenido real y específico de este grupo para juzgar.
   - **Insuficiente:** existe el archivo/sección pero es un placeholder, está vacío, o es
     genérico (copiado del template sin adaptar).
   - **Ausente:** no existe nada de esa sección todavía.

4. **Dar un veredicto único**, uno de estos tres, con la razón concreta:
   - `LISTO PARA EVALUAR` — la mayoría de las secciones son evaluables; los huecos que
     queden se pueden señalar como observaciones normales de una devolución.
   - `ESPERAR` — hay avance real pero todavía temprano (ej. el grupo viene subiendo commits
     seguido y es capaz de que actualice pronto); recomendable esperar antes que evaluar
     una foto parcial.
   - `PEDIR ACTUALIZACIÓN` — hay secciones clave en "Ausente" o "Insuficiente" sin señales
     de que vayan a completarse solas (ej. sin commits hace mucho, o el placeholder del
     template intacto); conviene contactar al grupo antes de evaluar.

5. **Reportar en el chat** (nada de esto va a archivo):
   - El veredicto del punto 4.
   - Una lista corta de qué está evaluable vs. insuficiente/ausente, sección por sección de
     la rúbrica.
   - Si el veredicto es `PEDIR ACTUALIZACIÓN` o `ESPERAR`, un mensaje breve sugerido para
     mandarle al grupo (usando el email de `materias/<materia>/grupos.json`, aunque el envío
     en sí lo hace el docente a mano — este comando no manda nada).
   - Si el veredicto es `LISTO PARA EVALUAR`, recordá que el siguiente paso es
     `/evaluar-grupo <materia> <grupo-id>`.

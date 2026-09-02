Publicá la devolución de un grupo del Sistema EIDAS — pushea el borrador de
`sistema-eidas-datos` al repo del grupo (`main`) y dispara la notificación automática.

`$ARGUMENTS` trae dos valores separados por espacio: `<materia> <grupo-id>`. Ejemplo:
`af-diseno-sistemas-web-31 GLPI`. Si `$ARGUMENTS` no trae ambos valores, pedíselos al
usuario antes de seguir.

**Esto pushea a `main` (visible para el grupo) y dispara un mail — es la acción menos
reversible de todo el sistema.** `scripts/grupos.py publicar` normalmente frena con un
prompt de confirmación por terminal antes de eso, pero corrido desde acá (vía Bash, sin
terminal interactiva) ese prompt no tiene con quién hablar. Este comando mueve el freno al
chat en vez de sacarlo — no se te ocurra saltear el paso 3.

Seguí estos pasos, en orden:

1. **Verificar que hay algo para publicar.** Si `materias/<materia>/grupos/<grupo-id>/` no
   existe, avisá que hay que correr `/sync <materia>` primero, y no sigas. Buscá en
   `../sistema-eidas-datos/<materia>/borradores/<grupo-id>/` algún `AAAA-MM-DD.md` que
   **no** diga `- [x] Publicado al grupo`. Si no hay ninguno, avisá que no hay devolución
   pendiente (`/evaluar-grupo <materia> <grupo-id>` para generar una) y no sigas.

2. **Mostrar el borrador para revisión.** Mostrale el contenido completo de cada
   `AAAA-MM-DD.md` pendiente al usuario — no lo resumas de más, es lo último que va a ver
   antes de que se vuelva visible para el grupo. Fijate en particular si:
   - El checkbox `- [x] Revisado y aprobado por Profe Pablo` está tildado. Si no lo está,
     avisá y preguntá si de verdad quiere publicar así.
   - Quedó algún resto de `**Confianza Claude:**` o `## Pregunta para el docente` sin sacar
     — `scripts/grupos.py publicar` los saca solo como red de seguridad, pero mejor que el
     usuario lo sepa de antemano en vez de enterarse después del push.

3. **Pedir confirmación explícita en el chat**, mostrando materia y grupo-id, antes de
   seguir. No asumas un "dale" genérico de mensajes anteriores en la conversación — cada
   grupo necesita su propia confirmación puntual. Si el usuario no confirma, no sigas.

4. **Recién ahí, correr:**
   `python3 scripts/grupos.py publicar <materia> <grupo-id> --yes`
   Dejá que la salida se muestre tal cual — incluye los avisos de commit automático, el
   resultado del push y de la notificación a N8N.

5. **Reportar al final:** confirmá si el push y la notificación salieron bien (o qué avisos
   dio el script si algo falló, como N8N no corriendo), y recordale al usuario que puede
   reintentar la notificación sola con
   `python3 scripts/grupos.py notificar <materia> <grupo-id> <AAAA-MM-DD>` si hizo falta.

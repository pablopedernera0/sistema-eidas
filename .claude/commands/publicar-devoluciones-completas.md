Publicá en lote todas las devoluciones listas de una materia del Sistema EIDAS — variante de
`/publicar` (`.claude/commands/publicar.md`) que recorre todos los grupos en vez de pedirte
el grupo-id uno por uno.

`$ARGUMENTS` trae un valor: `<materia>`. Si `$ARGUMENTS` no lo trae, pedíselo al usuario
antes de seguir.

**Mismo freno que `/publicar`, no lo saltees.** Este comando no publica más rápido saltando
confirmaciones — solo te ahorra tener que volver a escribir `/publicar <materia> <grupo-id>`
por cada uno. Cada grupo sigue necesitando su propio diff y su propia confirmación puntual en
el chat.

Seguí estos pasos, en orden:

1. **Armar la lista de candidatos.** Leé `materias/<materia>/grupos.json` para tener todos
   los `grupo-id` de la materia. Para cada uno cuyo repo exista en
   `materias/<materia>/grupos/<grupo-id>/`, fijate si tiene branch `feedback`
   (`git -C ... branch --list feedback`). Descartá sin mostrar diff a los que no la tengan
   (no hay nada generado todavía).

2. **Filtrar por aprobado.** Para cada grupo con branch `feedback`, leé el archivo
   `feedback/AAAA-MM-DD.md` más reciente de esa branch (working tree, no solo lo commiteado
   — el docente puede tener ediciones sin commitear) y fijate si
   `- [x] Revisado y aprobado por Profe Pablo` está tildado. Separá en dos listas: **listos**
   (tildado) y **no listos** (sin tildar, o sin ningún archivo de feedback legible).

3. **Reportar el plan antes de tocar nada:** mostrale al usuario la lista de listos (van a
   pasar por publicación) y la de no listos (se van a saltear, con el motivo — por ejemplo
   "sin tildar 'Revisado y aprobado'"). Esperá confirmación de que la lista está bien antes
   de arrancar el lote — si el usuario quiere sacar o agregar alguno, ajustá la lista.

4. **Por cada grupo de la lista de listos, en orden, repetí el proceso completo de
   `/publicar`:** mostrale el diff (`git -C materias/<materia>/grupos/<grupo-id> diff
   main..feedback` más los cambios sin commitear si los hay), pedile confirmación puntual
   para ESE grupo, y si confirma corré
   `python3 scripts/grupos.py publicar <materia> <grupo-id> --yes`. Si no confirma para un
   grupo puntual, saltealo (no aborta el lote entero) y seguí con el siguiente.

5. **Reportar al final:** una lista de qué se publicó, qué se saltó por falta de
   confirmación, y qué se excluyó desde el paso 2 por no estar aprobado — para que quede
   claro qué falta todavía sin tener que volver a correr el comando para averiguarlo.

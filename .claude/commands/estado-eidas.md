Chequeá el estado de sincronización de todos los repos del Sistema EIDAS en esta máquina.

No toma argumentos. Corré `python3 scripts/estado.py` y reportá la salida.

El script chequea, por cada repo (`sistema-eidas`, `sistema-eidas-datos`, `sistema-eidas-memory`
y `eidas-template` una vez por cada materia en `materias/`): fetch, y

- si está limpio y solo atrasado respecto de `origin` → hace `git pull --ff-only` solo,
  sin preguntar (es 100% seguro);
- si tiene cambios sin commitear o commits locales sin pushear → **no toca nada**, solo lo
  reporta.

Los repos de `materias/<materia>/grupos/` (los de los estudiantes) quedan afuera a
propósito — esos se resuelven con `/sync <materia>`, no tienen estado propio que importe
entre máquinas.

Después de correrlo:

1. Resumí en pocas líneas qué se pulleó (si algo) y qué quedó pendiente de subir, repo por
   repo — no repitas la salida completa si fue larga.
2. **Si `sistema-eidas-memory` quedó con cambios sin commitear o commits sin pushear**,
   ofrecé al usuario commitear y pushear vos mismo ahora, con su confirmación explícita en
   el momento (nunca en silencio). Es memoria propia tuya, generada por vos, de bajo riesgo.
3. **Para `sistema-eidas`, `sistema-eidas-datos` y `eidas-template`, nunca hagas push por tu
   cuenta**, ni lo ofrezcas como "lo hago ya" — son repos que ven estudiantes u otras
   personas. Si quedaron con cambios sin subir, solo señalalo; el push queda en manos del
   usuario, a mano, cuando quiera.

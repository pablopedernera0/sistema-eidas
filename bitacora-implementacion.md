# Bitácora de implementación — Sistema EIDAS

> Registro de cada corrida real del sistema en el aula: qué pasó, cómo lo recibieron los
> estudiantes, qué funcionó y qué hubo que ajustar. Es insumo para una eventual presentación a
> Placci y a otros colegas — separado del fundamento pedagógico, que vive en
> `marco-teorico-fundamentacion.md`. Acá se registra la experiencia, no la teoría.

---

## Qué registrar en cada entrada

No hace falta llenar las cinco categorías todas las veces — mejor una nota corta hecha que una
completa que nunca se escribe. Como guía:

- **Contexto:** fecha, materia/comisión, qué entrega/etapa del cronograma.
- **Proceso:** cuántos grupos se evaluaron, cuánto de la devolución de Claude quedó tal cual vs.
  cuánto hubo que corregir/ajustar a mano antes de publicar, cualquier fricción del pipeline.
- **Recepción:** cómo reaccionaron los estudiantes — reacciones textuales si las hay, clima
  general de la clase.
- **Nivel observado:** calidad de los repos entregados, en términos generales (no notas
  individuales de grupos).
- **A revisar:** cualquier ajuste que se te ocurra para la próxima corrida (rúbrica, plantilla,
  proceso).

---

## 2026-08-26 — Primera corrida real con estudiantes

**Contexto:** Primera vez que el sistema corrió con entregas reales de estudiantes (no prueba de
circuito). Ambas comisiones (31 y 32) de Diseño de Sistemas Web.

**Proceso:** En ambas comisiones se corrió `/chequear-grupo` (pre-chequeo) sobre los grupos. En
la comisión 32 se corrió además `/evaluar-grupo` para todos sus grupos, generando el borrador de
devolución de cada uno. Ninguna devolución fue publicada todavía (`scripts/grupos.py publicar`) —
quedan en revisión, sin pasar aún por el ajuste manual del docente ni por N8N.

**Recepción:** Muy buena. Los estudiantes aceptaron el dispositivo de forma excelente, clima
motivador en la clase.

**Nivel observado:** Muy buen nivel general en los repos entregados.

**A revisar:** —

---

## 2026-08-27/28 — Primeras devoluciones parciales generadas (comisión 31)

**Contexto:** Entrega intermedia (Requisitos + DoR/Slicing en curso, según cronograma). Comisión
31 de Diseño de Sistemas Web.

**Proceso:** Se corrió `/evaluar-grupo` sobre los 5 grupos de la 31
(`easy-core-computacion`, `ecommerce-mundo-sport`, `GLPI`, `pos-carrefour`, `sistema-turnos`),
generando en cada uno una devolución **parcial** en branch local `feedback` (variante de
entrega intermedia, sin fila de Total sobre 100). Ninguna fue publicada todavía —quedan
pendientes de revisión y ajuste manual antes de correr `scripts/grupos.py publicar`. La
comisión 32 ya tenía sus 8 devoluciones generadas desde el 2026-08-26, tampoco publicadas
todavía — la revisión de ambas comisiones queda para la próxima sesión.

**Recepción:** —

**Nivel observado:** —

**A revisar:** —

---

## 2026-09-02 — Primera revisión y ajuste manual antes de publicar (comisión 31)

**Contexto:** Devolución parcial (Requisitos + Stakeholders en alcance según cronograma).
Comisión 31 de Diseño de Sistemas Web. Revisión de las 5 devoluciones generadas el 28/08
(`easy-core-computacion`, `ecommerce-mundo-sport`, `GLPI`, `pos-carrefour`, `sistema-turnos`)
más una nueva generada hoy (`aberturas-los-pampas`), previo a la primera corrida real de
`scripts/grupos.py publicar`.

**Proceso:** Primer dato real sobre cuánto sobrevive el borrador de Claude al ajuste manual
(pendiente desde la entrada del 27/28-08). En las 6 devoluciones, el texto evaluativo por
sección (Requisitos, Stakeholders) quedó intacto tal como lo escribió Claude — el ajuste
manual sistemático fue otro: sacar la línea "Confianza Claude" y reemplazar "Pregunta para
el docente" por una sub-sección "Devolución docente". Esa nota fue idéntica en 4 de las 6
(GLPI, pos-carrefour, sistema-turnos, ecommerce-mundo-sport — sobre la relación entre
Requisitos, RNF y Diseño UI), y personalizada en las otras 2 (easy-core-computacion,
aberturas-los-pampas). Se agregó un chequeo automático a `publicar` (saca "Confianza Claude"
y "Pregunta para el docente" si quedan sin sacar) como red de seguridad, no reemplaza la
revisión manual.

Caso particular: `aberturas-los-pampas` no tenía ningún commit de este cuatrimestre — todo
el repo era el trabajo del 1er cuatrimestre (un PDF fechado junio 2026, sin el template
actual). Se decidió evaluar igual el contenido del PDF (Requisitos y Stakeholders, buen
nivel) y usar la devolución como aviso formal para que el grupo migre al template y retome
el proceso, en vez de esperar sin evaluar.

**Recepción:** — (pendiente, todavía no se publicó esta tanda)

**Nivel observado:** Bueno en las 6, con un caso atípico: el contenido de
`aberturas-los-pampas` es de buen nivel pero corresponde a trabajo ya hecho el cuatrimestre
anterior, nunca migrado al proceso de este.

**A revisar:** Confirmar en la próxima tanda si reusar la misma nota de "Devolución docente"
en varios grupos sigue siendo la práctica, o si conviene personalizarla más ahora que el
volumen de grupos aprobados a la vez creció.

---

<!-- Nueva entrada: copiar el bloque de arriba con fecha y completar -->

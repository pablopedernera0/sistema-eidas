# Guía docente — Clase práctica de Git y GitHub

> Material solo para el docente. No se comparte con los estudiantes — lo que ellos
> reciben es `template/RECURSOS.md`, que además les compartís por Classroom.

---

## Objetivo de la clase

Que cada estudiante termine la clase habiendo clonado el repo de su propio grupo, hecho
al menos un commit real, y verificado que aparece en GitHub. La meta no es que dominen
git — es que pierdan el miedo y salgan con el flujo mínimo internalizado: `pull → editar
→ add → commit → push`.

## Duración sugerida

90 minutos. Se puede comprimir a 45 si el grupo ya tiene experiencia previa con git.

## Requisitos previos de la clase

- Que cada grupo ya haya generado su repo desde el template (**"Use this template"**)
  antes de la clase — pedirlo como tarea previa, para no perder tiempo de clase en eso.
- Que cada estudiante tenga git instalado y cuenta de GitHub creada (avisar con
  antelación, verificar al inicio de la clase).
- Repartir `template/RECURSOS.md` antes o al comienzo de la clase.

## Estructura sugerida

### 1. Por qué git (10 min)

Breve, sin teoría exhaustiva: por qué versionar, por qué GitHub como evidencia del
proceso —no solo del resultado final—, por qué la profesión lo usa. Conectar con el
marco teórico de EIDAS (`marco-teorico-fundamentacion.md`, sección 7): el repo es
evidencia de producción real, no un trabajo entregado en un Word.

### 2. Clonar y explorar (15 min)

- Cada estudiante clona el repo de **su propio grupo** (no el template — el repo que su
  grupo ya generó).
- Recorren juntos la estructura: `docs/`, `diagramas/`, `cuestionario/`.
- Ejercicio: cada uno completa una línea de `integrantes.md` y hace su primer
  commit + push.

### 3. El ciclo pull → editar → add → commit → push (30 min)

- Demostración en vivo con un archivo de ejemplo.
- Ejercicio en grupos: cada integrante edita una sección distinta de
  `docs/requisitos.md` (para forzar que trabajen en paralelo) y sube sus cambios.
- **Importante:** provocar un conflicto real a propósito — hacer que dos integrantes
  editen la misma línea del mismo archivo sin avisarse, y resolverlo juntos en vivo. Es
  mejor que vean un conflicto por primera vez en clase, con ayuda, que solos a las 11pm
  antes de una entrega.

### 4. Conflictos: qué son y cómo se resuelven (15 min)

- Mostrar las marcas `<<<<<<<`, `=======`, `>>>>>>>`.
- Resolver juntos el conflicto generado en el paso anterior.
- Regla de oro: `git pull` siempre antes de empezar a trabajar, para minimizar
  conflictos.

### 5. Cierre y verificación (10 min)

- Cada grupo verifica en GitHub (desde el navegador) que los commits de todos los
  integrantes aparecen en el historial.
- Recordatorio: agregar al profesor como colaborador si no lo hicieron ya (lo van a
  necesitar para que la devolución se pueda publicar más adelante — ver
  `guia-de-uso.md`).

## Señales de alerta durante la clase

- Grupos donde solo un integrante hace commits — vale la pena revisar el historial de
  contribuciones más adelante en el cuatrimestre; puede ser indicio de reparto desigual
  del trabajo, relevante para matizar la devolución individual.
- Estudiantes que editan directamente desde la interfaz web de GitHub en vez de clonar —
  funciona para cambios chicos, pero no incorpora el flujo real. Redirigirlos a hacerlo
  por línea de comandos, especialmente en esta primera clase.

---

*Sistema EIDAS — Terciario Urquiza — Rosario, 2026*

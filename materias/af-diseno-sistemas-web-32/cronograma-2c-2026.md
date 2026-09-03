# Cronograma — Diseño de Sistemas Web (AF 3°2°), 2do cuatrimestre 2026

Cruce entre el Sistema EIDAS (rúbrica + template ya definidos en esta carpeta) y el programa oficial de la materia. **La estructura la define la rúbrica de EIDAS** (`rubrica.md`).

## Punto de partida real (corregido)

La teoría de RF/RNF, Stakeholders, Historias de Usuario y Casos de Uso ya se dio en el 1er cuatrimestre (confirmado en la planilla: "Repaso Identificación de Stakeholders", "Ejercicio Análisis rápido de requisitos", etc., abril-mayo 2026). La presentación de Diseño de Interfaces que armaste (usabilidad, accesibilidad, coherencia visual, diseño de formularios) también está dada. Los grupos ya hicieron una presentación de avances a fin del 1er cuatrimestre, con nivel dispar — algunos dejaron los casos de uso solo como títulos, sin desarrollar.

**Esto cambia el rol del 2do cuatrimestre por completo: no es una serie de clases nuevas, es el proceso de volcar y completar lo ya presentado dentro de la estructura de EIDAS.** Casi no hace falta contenido nuevo, salvo lo estrictamente necesario para operar el sistema (git, estructura del repo, PlantUML) — eso es lo único que realmente arranca de cero.

## Hallazgo importante: el examen ya existe

El "examen escrito de 10 preguntas sobre el proceso" que pediste ya es el **Cuestionario individual** de `rubrica.md` (30 pts, Google Forms, autocalificado). La presentación final grupal es la Parte A del parcial; el Cuestionario individual ya es la Parte B. No hace falta crear nada nuevo, salvo confirmar que el Form tenga 10 preguntas.

## Patrón de modalidad (comisión 3°2°)

Martes y miércoles alternan modalidad opuesta cada semana. Asumo virtual = con computadora, presencial = sin computadora (pizarrón/proyector) — no confirmado explícitamente para esta comisión.

## Punto de partida

- **Martes 04/08** — Presentación del Sistema EIDAS (ya dado)
- **Miércoles 05/08** — sin clase (confirmado)
- **Martes 11/08** — Demo en vivo de clonación del template (ya en la planilla)
- A partir de acá, temario vacío en la planilla.

## Cronograma propuesto

**Virtual = trabajo en grupo, volcando y ampliando lo que ya presentaron.**
**Presencial = revisión en vivo con proyector de lo volcado (feedback puntual, no clase nueva), más lo mínimo indispensable de EIDAS como herramienta.**

| Fecha         | Modalidad | Sección de la rúbrica | Actividad |
|---------------|---|---|---|
| Mié 12/08     | Virtual | Onboarding EIDAS | Alta del repo desde el template, agregar al profesor como colaborador, primer commit con lo que cada grupo ya tiene (aunque sea solo títulos) — arranca el volcado |
| Mar 25/08     | Virtual | Stakeholders + Requisitos | Trabajo en grupo: volcar stakeholders y requisitos ya presentados a `docs/stakeholders.md` y `docs/requisitos.md`, completando lo que falte |
| Mié 02/09     | Presencial | DoR + Slicing | **Actualizado 19/08:** la revisión de Stakeholders + Requisitos se corre porque la entrega viene retrasada (a los grupos les está costando entrar en la dinámica de GitHub). En su lugar, taller de Definition of Ready y Slicing vertical (`DoR.md` / `slicing.md` del template) — ver presentación en `pablopedernera0.github.io/dor-slicing/`. |
| Mar 01/09     | Presencial | Historias de usuario | Revisión en vivo de HU volcadas — repaso breve de INVEST solo si hace falta |
| Mar 08/09     | Presencial | Requisitos + HU + Casos de uso | Cierre de Requisitos y HU (lo pendiente desde que el taller de DoR/Slicing corrió esta revisión) + arranque del diagrama general de Casos de Uso |
| Mié 09/09     | Virtual | Casos de uso (20 pts) | Trabajo en grupo: expandir a diagrama general completo + arrancar CUs desarrollados |
| Mar 15/09     | Virtual | Casos de uso (20 pts) | Trabajo en grupo: cierre de CUs desarrollados (precondiciones, postcondiciones, secuencia, excepciones) |
| Mié 16/09     | Presencial | Requisitos + HU + Casos de uso | **Entrega de plantillas completas — entrega intermedia** (confirmado por Pablo el 02/09: el taller de DoR/Slicing ya se dio, la entrega completa de Requisitos+HU+CU se pide esta semana). Revisión en vivo de lo entregado, feedback puntual por grupo |
| Mar 22/09     | Presencial | Diseño UI | Revisión en vivo de wireframes contra los criterios ya vistos en la presentación de interfaces (agrupación, jerarquía, accesibilidad) |
| Mié 23/09     | Virtual | Modelo ER (10 pts) | Trabajo en grupo: diagrama entidad-relación |
| Mar 29/09     | Virtual | Diseño UI (10 pts) | Trabajo en grupo: wireframes |
| Mié 30/09     | Presencial | — | Consulta general y repaso, sin contenido nuevo |
| Mar 06/10     | Presencial | — | **Taller "Qué pide el mercado"** (presencial, con proyector) — ver sección dedicada abajo. El repaso del Cuestionario individual pasa a ofrecerse de forma asincrónica, sin sesión presencial dedicada |
| Mié 07/10     | Virtual | README (5 pts) | Últimos ajustes: README, `integrantes.md`, estructura del repo completa |
| **Mar 13/10** | Virtual | — | **Presentación final grupal = Parcial, Parte A** (última semana de clases) |
| Mié 14/10     | Presencial | — | Cierre del cuatrimestre + repaso general para el Cuestionario individual |

**Entrega sugerida del repo:** antes del martes 13/10 (ej. domingo 11/10 o lunes 12/10).

**Resuelto 2026-09-02:** la revisión de Stakeholders + Requisitos que se había corrido por el
taller de DoR/Slicing quedó absorbida en la fila de Mar 08/09 ("cierre de Requisitos y HU").
Pablo confirmó que el taller de DoR/Slicing ya se dio y que la entrega completa de
Requisitos + HU + Casos de uso ("plantillas completas") se pide en la semana del 16-18/09 —
la fila de Mié 16/09 pasó a ser esa entrega intermedia, y la vieja revisión de Modelo ER que
estaba ahí se sacó (Modelo ER pasa directo a la sesión de trabajo en grupo del Mié 23/09, sin
revisión en vivo previa dedicada).

## Parcial (fecha exacta a confirmar)

- **Parte A — Presentación virtual (grupal):** la del martes 13/10, o una instancia equivalente dentro del período de parciales.
- **Parte B — Cuestionario individual (30 pts, Google Forms):** ya existe en `rubrica.md`, no es un examen nuevo. Sugerencia: rendirlo presencial por consistencia institucional, a confirmar.

## Taller "Qué pide el mercado" (martes 06/10, cierre)

Sesión presencial con proyector, fuera de la rúbrica de EIDAS — conecta el cierre del
cuatrimestre con la búsqueda laboral real. Mismo taller en las dos comisiones (ver también
`materias/af-diseno-sistemas-web-31/cronograma-2c-2026.md`, ahí va el viernes 16/10).

**Material a entregar a los estudiantes antes de la clase** (ninguno existe todavía, hay
que crearlos):
- Guía de LinkedIn — tips, recomendaciones y recursos para armar un perfil efectivo,
  publicada en `pablopedernera0.github.io`.
- Lista de instrucciones sobre qué puestos buscar.
- Cuestionario tipo guía de estudio, para completar antes de venir a clase.

## Riesgo a tener presente

El nivel de avance real varía por grupo ("algunos solo dejaron planteados los títulos de los casos de uso"). Las fechas de "revisión en vivo" están pensadas para calibrar sobre la marcha cuánto tiempo de clase necesita cada sección — si un grupo viene muy atrasado en Casos de Uso, probablemente haga falta correr tiempo de Modelo ER o Diseño UI hacia la semana de consulta del Mié 30/09, el único colchón que queda sin contenido fijo (el Mar 06/10 pasó a ser el taller "Qué pide el mercado", ver arriba).

## Nota sobre alcance

La rúbrica de EIDAS hoy cubre Requisitos, HU, Casos de Uso, Modelo ER, Diseño UI, Stakeholders y README — el contenido de los TP1 a TP3 del programa oficial, aproximadamente. Los TP4 en adelante (prototipo con testeo, capacitación, manual de usuario, implementación, usabilidad, IA) no están en este cronograma — avisame si también tienen que salir este cuatrimestre.

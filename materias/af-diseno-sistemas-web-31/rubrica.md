# Rúbrica de Evaluación — Sistema EIDAS
## Diseño de Sistemas Web — Analista Funcional de Sistemas — Comisión 31
### Terciario Urquiza — Rosario | 2.° Cuatrimestre 2026
### Docente: Pedernera Pablo

---

## Distribución de puntaje

| Componente | Puntaje |
|------------|---------|
| Repo grupal | 70 pts |
| Cuestionario individual | 30 pts |
| **Total parcial** | **100 pts** |

---

## Repo grupal (70 puntos)

| Sección | Puntaje máximo |
|---------|---------------|
| Requisitos funcionales y no funcionales | 10 |
| Historias de usuario (INVEST) | 10 |
| Casos de uso | 15 |
| Definition of Ready (DoR) | 8 |
| Slicing vertical | 8 |
| Modelo Entidad-Relación | 7 |
| Diseño UI | 7 |
| Stakeholders | 3 |
| README e integrantes | 2 |
| **Total** | **70** |

---

## 1. Requisitos funcionales y no funcionales (10 puntos)

| Nivel | Puntaje | Descripción |
|-------|---------|-------------|
| **Muy bueno** | 9–10 | Los requisitos están agrupados por módulo con IDs claros. Los RF describen comportamiento observable del sistema, no intenciones genéricas. Los RNF especifican valores medibles (tiempos, porcentajes, dimensiones). Hay coherencia entre los RF y el contexto del caso de estudio. |
| **Bueno** | 7–8 | Los requisitos están presentes y agrupados. La mayoría son observables y medibles, pero alguno es vago o genérico. La coherencia con el caso de estudio es mayormente correcta. |
| **Regular** | 4–6 | Los requisitos están incompletos o mezclados sin distinción clara entre funcionales y no funcionales. Predominan enunciados genéricos ("el sistema debe ser rápido") sin valores concretos. |
| **Insuficiente** | 0–3 | Faltan requisitos relevantes para el caso de estudio, o los presentes no describen comportamiento del sistema sino características deseables sin especificación. |

**Criterios transversales a observar:**
- *Coherencia:* ¿los RF se corresponden con el problema real del caso de estudio?
- *Profundidad:* ¿los RNF tienen valores concretos o son enunciados vacíos?

---

## 2. Historias de usuario (10 puntos)

| Nivel | Puntaje | Descripción |
|-------|---------|-------------|
| **Muy bueno** | 9–10 | Al menos una HU por módulo relevante. Formato clásico completo (Como / quiero / para). Criterios de aceptación verificables y específicos. Validación INVEST con observaciones reales que justifican cada criterio, no monosílabos. |
| **Bueno** | 7–8 | Las HU están presentes y con formato correcto. Los criterios de aceptación son mayormente verificables. La validación INVEST está completa pero algunas observaciones son superficiales. |
| **Regular** | 4–6 | Las HU están incompletas o les falta algún componente del formato. Los criterios de aceptación son vagos o no verificables. La validación INVEST está presente pero sin justificación real. |
| **Insuficiente** | 0–3 | Faltan HU de módulos relevantes, o las presentes no siguen el formato, o los criterios de aceptación son inexistentes o no verificables. |

**Criterios transversales a observar:**
- *Coherencia:* ¿las HU se corresponden con los RF identificados?
- *Profundidad:* ¿las observaciones INVEST demuestran que pensaron el criterio, o son respuestas automáticas?

---

## 3. Casos de uso (15 puntos)

| Nivel | Puntaje | Descripción |
|-------|---------|-------------|
| **Muy bueno** | 13–15 | Diagrama general coherente con actores bien identificados y relaciones UML correctas (include/extend justificadas). Al menos tres CU desarrollados con precondiciones, postcondiciones, secuencia normal y excepciones reales. Las excepciones modelan situaciones concretas del caso de estudio, no situaciones genéricas. Los campos de rendimiento y frecuencia tienen valores estimados. |
| **Bueno** | 10–12 | El diagrama es mayormente correcto. Los CU están desarrollados con todos los campos pero alguna excepción es genérica o falta una situación relevante. Los valores de rendimiento y frecuencia están presentes. |
| **Regular** | 6–9 | El diagrama tiene errores de relaciones o actores mal identificados. Los CU están incompletos — faltan excepciones o postcondiciones. Se modeló solo el camino feliz. |
| **Insuficiente** | 0–5 | Falta el diagrama general o los CU desarrollados. Las excepciones están ausentes o son triviales. No hay coherencia entre el diagrama y los CU desarrollados. |

**Criterios transversales a observar:**
- *Coherencia:* ¿el diagrama general es consistente con los CU desarrollados y con los RF?
- *Profundidad:* ¿las secuencias normales modelan el flujo real del negocio o son genéricas?
- *Manejo de excepciones:* ¿pensaron qué pasa cuando algo falla, o solo modelaron el camino feliz?

---

## 4. Definition of Ready — DoR (8 puntos)

Evalúa el archivo `DoR.md`: la checklist de criterios de entrada del equipo y su aplicación honesta a tres historias propias del primer semestre.

| Nivel | Puntaje | Descripción |
|-------|---------|-------------|
| **Muy bueno** | 7–8 | Checklist de 6 a 10 ítems, todos formulados como condición verificable (se responden sí/no sin discutir), no como deseo. Cubre como mínimo: criterios de aceptación, flujos alternativos o excepciones, dependencias y algún requerimiento no funcional. Cada ítem tiene justificación específica (qué problema evita), no genérica. La autoevaluación de las tres historias es honesta: detecta faltas reales, no declara que las tres pasan sin observaciones. |
| **Bueno** | 5–6 | Checklist completa y mayormente verificable, con algún ítem formulado como deseo en vez de condición. Cubre la mayor parte de las áreas mínimas exigidas, puede faltar una (por ejemplo dependencias o RNF). La autoevaluación es correcta pero alguna observación es superficial. |
| **Regular** | 3–4 | Checklist incompleta o con ítems no verificables ("la historia está bien definida", "es clara"). Falta más de un área mínima de cobertura. La autoevaluación declara que las tres historias pasan sin detectar ninguna falta real, o las justificaciones son intercambiables entre ítems. |
| **Insuficiente** | 0–2 | No hay checklist, o los ítems son deseos sin forma de verificarse sí/no. No se aplicó a tres historias propias reales, o la aplicación es simulada. Archivo ausente o no versionado. |

**Criterios transversales a observar:**
- *Honestidad:* ¿el grupo reconoce fallas reales en su propio trabajo, o todo "pasa" convenientemente?
- *Verificabilidad:* ¿cada ítem se puede responder sí/no sin discutir, o requiere interpretación?

---

## 5. Slicing vertical (8 puntos)

Evalúa el archivo `slicing.md`: la fragmentación de la épica en historias verticales (Parte A) y el análisis de caminos alternativos sobre una de ellas (Parte B). La Parte C (defensa en plenario) no se documenta en el archivo.

| Nivel | Puntaje | Descripción |
|-------|---------|-------------|
| **Muy bueno** | 7–8 | Entre 5 y 8 historias, todas genuinamente verticales (cada una, sola, entrega algo usable de punta a punta — no son capas técnicas disfrazadas de historia). Formato Como/Quiero/Para completo con dos criterios de aceptación específicos por historia. Las cinco preguntas de la Parte B están respondidas con decisiones concretas del sistema, no genéricas, y con la atribución de quién decide cada caso (analista, negocio o técnica) justificada. |
| **Bueno** | 5–6 | Historias mayormente verticales, alguna se acerca a ser una capa horizontal sin que se note con claridad. Formato correcto pero algún criterio de aceptación es vago. Las cinco preguntas de la Parte B están respondidas, pero una o dos respuestas son genéricas o no distinguen bien quién decide. |
| **Regular** | 3–4 | Menos de cinco historias, o alguna claramente horizontal (por ejemplo "diseñar la pantalla de envío") sin que el grupo lo detecte. Criterios de aceptación ausentes o triviales. La Parte B está incompleta o no llega a las tres preguntas más importantes (falla parcial entre el débito y el crédito, doble clic, corte de conexión). |
| **Insuficiente** | 0–2 | La épica no se fragmentó realmente, o el corte no tiene relación con historias verticales. Falta la Parte B. |

**Criterios transversales a observar:**
- *Verticalidad real:* ¿cada historia sola entrega algo usable, o es una tarea técnica disfrazada de historia de usuario?
- *Profundidad en excepciones:* ¿pensaron los casos de falla parcial, duplicación de la acción o corte de conexión con una decisión concreta, o los dejaron sin resolver?

---

## 6. Modelo Entidad-Relación (7 puntos)

| Nivel | Puntaje | Descripción |
|-------|---------|-------------|
| **Muy bueno** | 6–7 | Diagrama completo con entidades, atributos tipados, PK y FK identificadas, y cardinalidades correctas. Las decisiones de diseño están justificadas — explican el por qué, no solo el qué. Los atributos reflejan los requisitos del sistema (ej: marcas temporales si hay métricas). |
| **Bueno** | 4–5 | El diagrama es mayormente correcto. Hay al menos una decisión de diseño justificada. Algún atributo relevante puede estar ausente o alguna cardinalidad es imprecisa. |
| **Regular** | 2–3 | El diagrama tiene entidades pero faltan atributos relevantes, cardinalidades incorrectas o FK no identificadas. Las decisiones de diseño están enunciadas pero no justificadas. |
| **Insuficiente** | 0–1 | El diagrama está incompleto o no refleja el caso de estudio. Faltan entidades relevantes o las relaciones son incorrectas. No hay decisiones de diseño. |

**Criterios transversales a observar:**
- *Coherencia:* ¿el modelo ER soporta los casos de uso y los requisitos identificados?
- *Profundidad:* ¿las decisiones de diseño demuestran que pensaron alternativas?

---

## 7. Diseño UI (7 puntos)

| Nivel | Puntaje | Descripción |
|-------|---------|-------------|
| **Muy bueno** | 6–7 | Al menos un wireframe por pantalla o módulo relevante. Los patrones de diseño elegidos (Card, Modal, Step-by-step, etc.) están justificados en función del caso de estudio y los usuarios del sistema. Las decisiones de formularios consideran cantidad de campos, flujo y usabilidad. Hay al menos una consideración de accesibilidad concreta. |
| **Bueno** | 4–5 | Los wireframes están presentes y los patrones identificados son adecuados. La justificación es mayormente correcta pero alguna decisión no está argumentada. |
| **Regular** | 2–3 | Los wireframes son escasos o muy esquemáticos. Los patrones están mencionados pero no justificados en función del caso de estudio concreto. |
| **Insuficiente** | 0–1 | No hay wireframes o son irreconocibles. Los patrones están ausentes o son genéricos sin relación con el sistema analizado. |

**Criterios transversales a observar:**
- *Coherencia:* ¿las decisiones de UI son consistentes con los requisitos no funcionales (accesibilidad, dispositivos)?
- *Profundidad:* ¿los patrones elegidos responden al usuario real del sistema o son elecciones arbitrarias?

---

## 8. Stakeholders (3 puntos)

| Nivel | Puntaje | Descripción |
|-------|---------|-------------|
| **Completo** | 3 | Todos los stakeholders relevantes están identificados, incluyendo sistemas externos si aplica. Cada uno tiene justificación real de por qué es clave — no es una descripción genérica. El nivel de impacto está argumentado. |
| **Parcial** | 1–2 | Los stakeholders principales están identificados. Puede faltar alguno secundario, o la justificación es genérica, o el nivel de impacto no está argumentado. |
| **Insuficiente** | 0 | Faltan stakeholders clave o las justificaciones no tienen relación con el caso de estudio. |

---

## 9. README e integrantes (2 puntos)

| Nivel | Puntaje | Descripción |
|-------|---------|-------------|
| **Completo** | 2 | README completo con descripción del proyecto, caso de estudio y tabla de entregas actualizada. `integrantes.md` completo con todos los integrantes. Estructura del repo respeta el template, incluidos `DoR.md` y `slicing.md` en la raíz. |
| **Parcial** | 1 | README mayormente completo, con algún campo sin completar o tabla de entregas desactualizada. |
| **Insuficiente** | 0 | README vacío o sin modificar desde el template, o falta `integrantes.md`. |

---

## Cuestionario individual (30 puntos)

El cuestionario evalúa comprensión individual del proceso de análisis y la teoría detrás del trabajo grupal.
La puntuación se calcula automáticamente según las respuestas correctas.

| Rango | Nivel |
|-------|-------|
| 25–30 pts | Muy bueno |
| 18–24 pts | Bueno |
| 12–17 pts | Regular |
| 0–11 pts | Insuficiente |

---

## Tabla de puntuación final

| Componente | Puntaje obtenido | Puntaje máximo |
|------------|-----------------|---------------|
| Requisitos | | 10 |
| Historias de usuario | | 10 |
| Casos de uso | | 15 |
| Definition of Ready (DoR) | | 8 |
| Slicing vertical | | 8 |
| Modelo ER | | 7 |
| Diseño UI | | 7 |
| Stakeholders | | 3 |
| README e integrantes | | 2 |
| **Subtotal repo** | | **70** |
| Cuestionario individual | | 30 |
| **Total** | | **100** |

---

## Nota de aprobación

| Condición | Detalle |
|-----------|---------|
| Aprobación directa | 60 puntos o más sobre 100 |
| Recuperatorio | Entre 40 y 59 puntos |
| Insuficiente | Menos de 40 puntos |

---

*Sistema EIDAS — Evaluación Integrada con Devolución Asistida y Supervisada*
*Terciario Urquiza — Diseño de Sistemas Web — 2.° Cuatrimestre 2026*

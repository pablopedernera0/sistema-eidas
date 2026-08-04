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
| Requisitos funcionales y no funcionales | 15 |
| Historias de usuario (INVEST) | 15 |
| Casos de uso | 20 |
| Modelo Entidad-Relación | 10 |
| Diseño UI | 10 |
| Stakeholders | 5 |
| README e integrantes | 5 |
| **Total** | **70** |

---

## 1. Requisitos funcionales y no funcionales (15 puntos)

| Nivel | Puntaje | Descripción |
|-------|---------|-------------|
| **Muy bueno** | 13–15 | Los requisitos están agrupados por módulo con IDs claros. Los RF describen comportamiento observable del sistema, no intenciones genéricas. Los RNF especifican valores medibles (tiempos, porcentajes, dimensiones). Hay coherencia entre los RF y el contexto del caso de estudio. |
| **Bueno** | 10–12 | Los requisitos están presentes y agrupados. La mayoría son observables y medibles, pero alguno es vago o genérico. La coherencia con el caso de estudio es mayormente correcta. |
| **Regular** | 6–9 | Los requisitos están incompletos o mezclados sin distinción clara entre funcionales y no funcionales. Predominan enunciados genéricos ("el sistema debe ser rápido") sin valores concretos. |
| **Insuficiente** | 0–5 | Faltan requisitos relevantes para el caso de estudio, o los presentes no describen comportamiento del sistema sino características deseables sin especificación. |

**Criterios transversales a observar:**
- *Coherencia:* ¿los RF se corresponden con el problema real del caso de estudio?
- *Profundidad:* ¿los RNF tienen valores concretos o son enunciados vacíos?

---

## 2. Historias de usuario (15 puntos)

| Nivel | Puntaje | Descripción |
|-------|---------|-------------|
| **Muy bueno** | 13–15 | Al menos una HU por módulo relevante. Formato clásico completo (Como / quiero / para). Criterios de aceptación verificables y específicos. Validación INVEST con observaciones reales que justifican cada criterio, no monosílabos. |
| **Bueno** | 10–12 | Las HU están presentes y con formato correcto. Los criterios de aceptación son mayormente verificables. La validación INVEST está completa pero algunas observaciones son superficiales. |
| **Regular** | 6–9 | Las HU están incompletas o les falta algún componente del formato. Los criterios de aceptación son vagos o no verificables. La validación INVEST está presente pero sin justificación real. |
| **Insuficiente** | 0–5 | Faltan HU de módulos relevantes, o las presentes no siguen el formato, o los criterios de aceptación son inexistentes o no verificables. |

**Criterios transversales a observar:**
- *Coherencia:* ¿las HU se corresponden con los RF identificados?
- *Profundidad:* ¿las observaciones INVEST demuestran que pensaron el criterio, o son respuestas automáticas?

---

## 3. Casos de uso (20 puntos)

| Nivel | Puntaje | Descripción |
|-------|---------|-------------|
| **Muy bueno** | 17–20 | Diagrama general coherente con actores bien identificados y relaciones UML correctas (include/extend justificadas). Al menos tres CU desarrollados con precondiciones, postcondiciones, secuencia normal y excepciones reales. Las excepciones modelan situaciones concretas del caso de estudio, no situaciones genéricas. Los campos de rendimiento y frecuencia tienen valores estimados. |
| **Bueno** | 13–16 | El diagrama es mayormente correcto. Los CU están desarrollados con todos los campos pero alguna excepción es genérica o falta una situación relevante. Los valores de rendimiento y frecuencia están presentes. |
| **Regular** | 8–12 | El diagrama tiene errores de relaciones o actores mal identificados. Los CU están incompletos — faltan excepciones o postcondiciones. Se modeló solo el camino feliz. |
| **Insuficiente** | 0–7 | Falta el diagrama general o los CU desarrollados. Las excepciones están ausentes o son triviales. No hay coherencia entre el diagrama y los CU desarrollados. |

**Criterios transversales a observar:**
- *Coherencia:* ¿el diagrama general es consistente con los CU desarrollados y con los RF?
- *Profundidad:* ¿las secuencias normales modelan el flujo real del negocio o son genéricas?
- *Manejo de excepciones:* ¿pensaron qué pasa cuando algo falla, o solo modelaron el camino feliz?

---

## 4. Modelo Entidad-Relación (10 puntos)

| Nivel | Puntaje | Descripción |
|-------|---------|-------------|
| **Muy bueno** | 9–10 | Diagrama completo con entidades, atributos tipados, PK y FK identificadas, y cardinalidades correctas. Las decisiones de diseño están justificadas — explican el por qué, no solo el qué. Los atributos reflejan los requisitos del sistema (ej: marcas temporales si hay métricas). |
| **Bueno** | 7–8 | El diagrama es mayormente correcto. Hay al menos una decisión de diseño justificada. Algún atributo relevante puede estar ausente o alguna cardinalidad es imprecisa. |
| **Regular** | 4–6 | El diagrama tiene entidades pero faltan atributos relevantes, cardinalidades incorrectas o FK no identificadas. Las decisiones de diseño están enunciadas pero no justificadas. |
| **Insuficiente** | 0–3 | El diagrama está incompleto o no refleja el caso de estudio. Faltan entidades relevantes o las relaciones son incorrectas. No hay decisiones de diseño. |

**Criterios transversales a observar:**
- *Coherencia:* ¿el modelo ER soporta los casos de uso y los requisitos identificados?
- *Profundidad:* ¿las decisiones de diseño demuestran que pensaron alternativas?

---

## 5. Diseño UI (10 puntos)

| Nivel | Puntaje | Descripción |
|-------|---------|-------------|
| **Muy bueno** | 9–10 | Al menos un wireframe por pantalla o módulo relevante. Los patrones de diseño elegidos (Card, Modal, Step-by-step, etc.) están justificados en función del caso de estudio y los usuarios del sistema. Las decisiones de formularios consideran cantidad de campos, flujo y usabilidad. Hay al menos una consideración de accesibilidad concreta. |
| **Bueno** | 7–8 | Los wireframes están presentes y los patrones identificados son adecuados. La justificación es mayormente correcta pero alguna decisión no está argumentada. |
| **Regular** | 4–6 | Los wireframes son escasos o muy esquemáticos. Los patrones están mencionados pero no justificados en función del caso de estudio concreto. |
| **Insuficiente** | 0–3 | No hay wireframes o son irreconocibles. Los patrones están ausentes o son genéricos sin relación con el sistema analizado. |

**Criterios transversales a observar:**
- *Coherencia:* ¿las decisiones de UI son consistentes con los requisitos no funcionales (accesibilidad, dispositivos)?
- *Profundidad:* ¿los patrones elegidos responden al usuario real del sistema o son elecciones arbitrarias?

---

## 6. Stakeholders (5 puntos)

| Nivel | Puntaje | Descripción |
|-------|---------|-------------|
| **Muy bueno** | 5 | Todos los stakeholders relevantes están identificados, incluyendo sistemas externos si aplica. Cada uno tiene justificación real de por qué es clave — no es una descripción genérica. El nivel de impacto está argumentado. |
| **Bueno** | 4 | Los stakeholders principales están identificados con justificación mayormente correcta. Puede faltar alguno secundario o el nivel de impacto no está argumentado. |
| **Regular** | 2–3 | Los stakeholders están listados pero las justificaciones son genéricas o intercambiables entre sí. Falta algún stakeholder relevante. |
| **Insuficiente** | 0–1 | Faltan stakeholders clave o las justificaciones no tienen relación con el caso de estudio. |

---

## 7. README e integrantes (5 puntos)

| Nivel | Puntaje | Descripción |
|-------|---------|-------------|
| **Muy bueno** | 5 | README completo con descripción del proyecto, caso de estudio y tabla de entregas actualizada. `integrantes.md` completo con todos los integrantes. Estructura del repo respeta el template. |
| **Bueno** | 4 | README mayormente completo. Algún campo sin completar o tabla de entregas desactualizada. |
| **Regular** | 2–3 | README con información mínima. Falta la tabla de entregas o `integrantes.md` incompleto. |
| **Insuficiente** | 0–1 | README vacío o sin modificar desde el template. Falta `integrantes.md`. |

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
| Requisitos | | 15 |
| Historias de usuario | | 15 |
| Casos de uso | | 20 |
| Modelo ER | | 10 |
| Diseño UI | | 10 |
| Stakeholders | | 5 |
| README e integrantes | | 5 |
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

# Sistema EIDAS

**Evaluación Integrada con Devolución Asistida y Supervisada**

Dispositivo de evaluación para carreras técnicas que combina trabajo grupal en GitHub,
un cuestionario individual, un primer lector automatizado con IA y la aprobación docente
obligatoria antes de que cualquier devolución llegue a los estudiantes. Nace en el
Terciario Urquiza (Rosario, Argentina) para las materias de la carrera de Analista
Funcional de Sistemas, pensado desde el inicio para ser multi-materia: cada materia vive
en su propia carpeta, con su propia rúbrica y su propio repo template, sobre la misma
infraestructura compartida.

## Por qué existe

En carreras técnicas, buena parte de lo que una IA puede resolver por sí sola es
exactamente lo que las evaluaciones tradicionales miden: reproducción de una respuesta
modelo. EIDAS parte de la idea contraria — evaluar para conocer, no para excluir — y
arma un dispositivo donde lo que se mide es producción, decisión y justificación de un
grupo real, documentadas en su propio repositorio. La IA participa como primer lector
sistemático de ese trabajo, nunca como evaluador final: toda devolución queda revisada,
ajustada y aprobada por el docente antes de publicarse.

El fundamento pedagógico completo, con las referencias teóricas, está en
[`marco-teorico-fundamentacion.md`](marco-teorico-fundamentacion.md) (versión resumida en
[`marco-teorico-resumen.md`](marco-teorico-resumen.md)).

## Cómo funciona, en breve

1. Cada grupo trabaja en un repo de GitHub generado desde el template de su materia.
2. El docente sincroniza los repos de los grupos y corre un comando de Claude Code que
   genera un borrador de devolución en una rama local (`feedback`) — nunca visible para
   el grupo en ese punto.
3. El docente revisa ese borrador, ajusta puntajes y agrega contexto que la IA no puede
   ver (proceso grupal, presentación oral, etc.).
4. Al aprobarlo, un script mergea la devolución a `main`, la pushea — recién ahí se
   vuelve visible para el grupo — y dispara una automatización (N8N) que sube el archivo
   a Drive y notifica por Gmail.

El diseño completo (estructura de carpetas, formato de la devolución, cómo dar de alta
una materia nueva) está en [`CLAUDE.md`](CLAUDE.md); los pasos operativos día a día, en
[`guia-de-uso.md`](guia-de-uso.md).

## Estado actual

Activo en dos comisiones de Diseño de Sistemas Web (Analista Funcional de Sistemas),
2.° cuatrimestre 2026. La infraestructura (scripts, automatización, el dispositivo en sí)
es genérica; sumar una materia nueva implica agregar su rúbrica y su template, sin tocar
el resto del sistema.

## Créditos

Pedernera Pablo — Terciario Urquiza, Rosario.

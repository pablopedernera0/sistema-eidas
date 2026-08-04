# Sistema EIDAS
## Evaluación Integrada con Devolución Asistida y Supervisada

### Contexto institucional

- **Institución:** Terciario Urquiza — Rosario, Santa Fe, Argentina
- **Carrera:** Analista Funcional de Sistemas
- **Materia:** Diseño de Sistemas Web (3.er año)
- **Docente:** Pedernera Pablo (Profe Pablo)
- **Cuatrimestre:** 2.° 2026

---

### Qué es el Sistema EIDAS

EIDAS es un dispositivo de evaluación con fundamento pedagógico que combina:

1. **Trabajo grupal** documentado en GitHub con estructura fija
2. **Cuestionario individual** via Google Classroom/Forms
3. **Evaluación asistida por IA** (Claude) como primer lector
4. **Supervisión docente** obligatoria antes de publicar cualquier devolución
5. **Automatización** via N8N para notificación a los grupos

El docente supervisa y aprueba toda devolución antes de que los estudiantes la vean. Claude actúa como primer lector sistemático, no como evaluador final.

---

### Estructura del proyecto en disco

```
sistema-eidas/
├── CLAUDE.md                  ← este archivo
├── template/                  ← repo template a subir a GitHub
│   ├── README.md
│   ├── integrantes.md
│   ├── RECURSOS.md            ← para estudiantes: prerrequisitos, cheatsheet de git, recursos
│   ├── docs/
│   │   ├── requisitos.md
│   │   ├── historias-de-usuario.md
│   │   ├── casos-de-uso.md
│   │   ├── er-modelo.md
│   │   ├── stakeholders.md
│   │   └── diseño-ui.md
│   ├── diagramas/
│   │   ├── casos-de-uso.puml
│   │   ├── er.puml
│   │   └── wireframes/
│   └── cuestionario/
│       └── .gitkeep
├── rubrica.md                 ← rúbrica de evaluación
├── guia-de-uso.md                      ← guía operativa paso a paso (estado real: qué es manual, qué está automatizado)
├── guia-docente-clase-git.md           ← plan de clase práctica de git (solo docente, no se sube al template)
├── guia-prueba-circuito-completo.md    ← runbook para probar el sistema de punta a punta (solo docente)
├── .claude/
│   └── commands/
│       └── evaluar-grupo.md            ← comando /evaluar-grupo <id>: automatiza el paso de Claude Code
├── marco-teorico.md                    ← notas y bibliografía fuente
├── marco-teorico-fundamentacion.md     ← fundamentación teórica completa
├── marco-teorico-resumen.md            ← resumen de 2 hojas
├── infra/
│   └── n8n/                   ← docker-compose de N8N (local; base para el Linode)
├── grupos.json                ← config: id + url de repo + email de cada grupo
├── scripts/
│   └── grupos.py               ← sync (clonar/pull), publicar (merge→push+notifica N8N solo), notificar (reintento manual)
├── grupos/                    ← repos clonados de cada grupo (se puebla en el cuatrimestre)
│   ├── grupo-01-xxxxx/
│   │   └── feedback/          ← dentro del propio repo del grupo, se puebla vía branch local "feedback"
│   │       └── AAAA-MM-DD.md  ← devolución ya aprobada y pusheada (visible para el grupo)
│   └── grupo-02-xxxxx/
└── feedback/                  ← TU copia de trabajo, todos los grupos juntos (no se pushea a ningún repo de grupo)
    ├── grupo-01-xxxxx_AAAA-MM-DD.md
    └── grupo-02-xxxxx_AAAA-MM-DD.md
```

---

### Rúbrica resumida (ver rubrica.md para detalle completo)

| Sección | Puntos |
|---------|--------|
| Requisitos funcionales y no funcionales | 15 |
| Historias de usuario (INVEST) | 15 |
| Casos de uso | 20 |
| Modelo Entidad-Relación | 10 |
| Diseño UI | 10 |
| Stakeholders | 5 |
| README e integrantes | 5 |
| **Subtotal repo grupal** | **70** |
| Cuestionario individual | 30 |
| **Total** | **100** |

**Aprobación:** 60 puntos o más.

**Criterios transversales de calidad** (aplican a todas las secciones):
- **Coherencia** — ¿los artefactos son consistentes entre sí y con el caso de estudio?
- **Profundidad** — ¿justifican las decisiones o solo las enuncian?
- **Manejo de excepciones** — ¿modelaron solo el camino feliz, o pensaron los casos de falla?

---

### Pipeline de evaluación

```
Grupo sube trabajo al repo GitHub
        ↓
Profe hace git pull sobre grupos/grupo-XX/ (repo del grupo, local)
        ↓
Abre Claude Code en sistema-eidas/
        ↓
Claude, dentro de grupos/grupo-XX/, crea (o actualiza) la branch local "feedback",
aplica la rúbrica y commitea grupos/grupo-XX/feedback/AAAA-MM-DD.md
— esta branch es 100% local, nunca se pushea, el grupo no puede verla —
también deja una copia de trabajo en sistema-eidas/feedback/grupo-XX_AAAA-MM-DD.md
        ↓
Profe revisa la branch "feedback" (diff local), ajusta puntajes y texto,
agrega contexto que Claude no puede ver
        ↓
Profe corre: python3 scripts/grupos.py publicar grupo-XX
— hace merge feedback → main (local), tilda "Publicado al grupo", y git push origin main —
— ACÁ es cuando la devolución se vuelve visible para el grupo, al pushear main —
        ↓
El mismo comando dispara automáticamente el workflow de N8N (webhook local,
no sale de esta máquina) para subir el archivo a Drive y notificar por Gmail
```

---

### Formato del archivo de feedback

Cada archivo de devolución sigue esta estructura, tanto la copia de trabajo en
`sistema-eidas/feedback/grupo-XX_AAAA-MM-DD.md` como la que termina pusheada en
`grupos/grupo-XX/feedback/AAAA-MM-DD.md`:

```markdown
# Devolución — [Nombre del grupo / caso de estudio]
## Materia: Diseño de Sistemas Web | Fecha: XX/XX/2026

## Puntuación

| Sección | Puntaje obtenido | Puntaje máximo | Nivel |
|---------|-----------------|---------------|-------|
| Requisitos | | 15 | |
| Historias de usuario | | 15 | |
| Casos de uso | | 20 | |
| Modelo ER | | 10 | |
| Diseño UI | | 10 | |
| Stakeholders | | 5 | |
| README e integrantes | | 5 | |
| Subtotal repo | | 70 | |
| Cuestionario individual | | 30 | |
| **Total** | | **100** | |

## Devolución por sección

### Requisitos
**Confianza Claude:** Alta / Media / Baja
[observaciones]

### Historias de usuario
**Confianza Claude:** Alta / Media / Baja
[observaciones]

### Casos de uso
**Confianza Claude:** Alta / Media / Baja
[observaciones]

### Modelo ER
**Confianza Claude:** Alta / Media / Baja
[observaciones]

### Diseño UI
**Confianza Claude:** Alta / Media / Baja
[observaciones]

### Stakeholders
**Confianza Claude:** Alta / Media / Baja
[observaciones]

### README e integrantes
**Confianza Claude:** Alta / Media / Baja
[observaciones]

## Pregunta para el docente
[Una pregunta específica sobre este grupo que solo el docente puede responder
— contexto del proceso grupal, presentación oral, dificultades conocidas, etc.]

## Estado
- [ ] Borrador generado por Claude
- [ ] Revisado y aprobado por Profe Pablo
- [ ] Publicado al grupo
```

`/evaluar-grupo` tilda la primera casilla al generar el borrador. La segunda la tildás vos a
mano durante la revisión. La tercera **no la toques manualmente** — `scripts/grupos.py
publicar` la tilda solo, como parte del mismo commit que hace el push, así el archivo queda
consistente con la realidad sin pasos extra.

---

### Pendientes del sistema

- [x] Crear `docs/diseño-ui.md` en el template
- [x] Crear carpeta `diagramas/wireframes/` en el template
- [x] Subir template a GitHub y configurarlo como template repository (https://github.com/pablopedernera0/eidas-template)
- [x] Prerrequisitos + cheatsheet de git + recursos para estudiantes (`template/RECURSOS.md`, publicado en `eidas-template`) y plan de clase práctica para el docente (`guia-docente-clase-git.md`)
- [~] Apps Script en Google Forms → repo — **decisión: no se hace.** El cuestionario ya se autocalifica en Forms, y como es individual (no grupal), meterlo en el repo del grupo expondría la nota de cada estudiante al resto del equipo. Buscar el puntaje a mano una vez por estudiante al cerrar la nota final no justifica automatizarlo.
- [~] Levantar N8N en el Linode — **decisión: no es necesario por ahora.** Todo el pipeline es local y el disparo de notificación es manual, así que N8N puede seguir corriendo en la PC del docente indefinidamente. El Linode solo pasaría a ser necesario si en el futuro se necesita que un servicio externo (webhook de GitHub, Apps Script) le llegue a N8N desde internet — evaluar entonces, no antes.
- [x] Armar lógica del flow N8N en local: genera archivo → sube a "Devoluciones EIDAS" en Drive → notifica por Gmail (workflow `Evaluacion EIDAS`, probado end-to-end con Manual Trigger; exportado a `infra/n8n/workflows/evaluacion-eidas.json`)
- [x] Workflow de N8N conectado a los archivos reales: lee `grupos/grupo-XX/feedback/AAAA-MM-DD.md` y busca el email en `grupos.json` automáticamente. Requiere `N8N_RESTRICT_FILE_ACCESS_TO` seteado en `docker-compose.yml` (N8N por defecto solo deja leer `~/.n8n-files`) y el bind mount del proyecto en `/home/node/data`.
- [x] Disparo de N8N automatizado: el trigger pasó de Manual Trigger a un nodo **Webhook** (workflow activado/publicado), y `scripts/grupos.py publicar` lo llama solo al final (POST a `http://localhost:5678/webhook/evaluar-grupo` con `grupo_id`+`fecha`, detectados automáticamente del merge — no hay que volver a tipearlos). Ya no hace falta abrir la UI de N8N para el uso normal. Fallback manual: `scripts/grupos.py notificar <grupo-id> <fecha>`.
- [x] Escribir marco teórico del Sistema EIDAS (`marco-teorico-fundamentacion.md` y `marco-teorico-resumen.md`) — pendiente confirmar datos de edición de Achilli/Ander-Egg y ampliar referencia al seminario de Placci sobre IA

---

### Infraestructura

| Componente | Tecnología | Estado |
|------------|------------|--------|
| Repos de grupos | GitHub (template repository) | Activo |
| Cuestionarios | Google Classroom + Forms | Activo |
| Conexión Forms → repo | — | Descartado — no aporta valor suficiente (ver pendientes) |
| Automatización | N8N en Docker (`infra/n8n/`), corre local en la PC del docente | Activo — conectado a archivos reales, se dispara solo desde `scripts/grupos.py publicar` |
| Servidor | Linode propio de Profe Pablo | Disponible, no se usa por ahora (ver pendientes — N8N se queda local) |
| Evaluación asistida | Claude Code (local) | Activo |

---

### Marco teórico (en construcción)

- **Placci, Norma** — *La evaluación de la práctica como eje del proceso formativo* (Homo Sapiens, 2025). Evaluar prácticas exige formas más difíciles de diseñar que no admiten respuestas modelo ni reproducción.
- **Álvarez Méndez, Juan Manuel** — Evaluar para conocer vs. examinar para excluir.
- **Perrenoud, Philippe** — Las dos lógicas de la evaluación.
- **Cruce con IA** — en carreras técnicas, la IA resuelve evaluaciones que miden reproducción; las evaluaciones que miden comprensión real requieren producción, decisión y justificación — exactamente lo que EIDAS busca verificar.

---

*Sistema EIDAS — Terciario Urquiza — Rosario, 2026*

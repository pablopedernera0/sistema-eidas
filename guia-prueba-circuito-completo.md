# Guía de prueba — circuito completo del Sistema EIDAS

> Runbook para probar el sistema de punta a punta con una cuenta de estudiante de prueba.
> Solo para el docente — no se sube al template. Pensada para reusarse cada vez que se
> quiera validar el circuito completo, no solo para la primera prueba.

---

## 0. Qué se prueba

Todo el camino: un grupo crea su repo desde el template → sube trabajo → vos generás la
devolución con Claude → la revisás → la publicás → el grupo la recibe por Drive + Gmail.

## 1. Preparar la cuenta de estudiante de prueba

1. Logueate en GitHub con la cuenta de prueba (no la de `pablopedernera0`).
2. Entrá a https://github.com/pablopedernera0/eidas-template → **"Use this template" →
   "Create a new repository"**. Nombre sugerido: `eidas-prueba-circuito`.
3. Cloná ese repo con la cuenta de prueba y completá algo mínimo para simular trabajo real:
   - `integrantes.md` con un nombre de prueba.
   - Alguna línea en `docs/requisitos.md` (para que Claude tenga algo real que evaluar).
   - `git add . && git commit -m "..." && git push`.
4. En GitHub, andá a **Settings → Collaborators** del repo de prueba y agregá a tu cuenta
   real (`pablopedernera0`) con permiso de escritura. **Este paso es el que más fácil se
   olvida** — sin él, el `push` de la devolución va a fallar más adelante.

## 2. Volver a tu cuenta de docente

Todo lo que sigue es con tu cuenta real y en tu terminal, dentro de `sistema-eidas/`.

1. Agregá el grupo de prueba a `grupos.json`:
   ```json
   { "id": "grupo-prueba", "repo": "https://github.com/<cuenta-de-prueba>/eidas-prueba-circuito.git", "email": "<tu email real, para poder verificar>" }
   ```
2. Cloná el repo:
   ```
   python3 scripts/grupos.py sync
   ```
   Verificá que aparezca `grupos/grupo-prueba/` con lo que subiste en el paso 1.

## 3. Generar la devolución con Claude Code

1. Abrí Claude Code en `sistema-eidas/` y pedile explícitamente:
   - Que trabaje dentro de `grupos/grupo-prueba/`.
   - Que cree la branch local `feedback` (si no existe).
   - Que aplique `rubrica.md` sobre lo que hay en el repo de prueba.
   - Que commitee el archivo en `grupos/grupo-prueba/feedback/AAAA-MM-DD.md` (fecha de hoy),
     siguiendo el formato de `CLAUDE.md`.
   - Que deje también la copia de trabajo en `sistema-eidas/feedback/grupo-prueba_AAAA-MM-DD.md`.
2. Verificá que la branch `feedback` es local y no se pusheó sola:
   ```
   cd grupos/grupo-prueba && git branch -a
   ```
   No debería aparecer `feedback` en el listado de `origin/*`.

## 4. Revisar y publicar

1. Revisá el contenido:
   ```
   git diff main feedback
   ```
2. Ajustá lo que haga falta directamente en el archivo (esto simula tu revisión real).
3. Publicá:
   ```
   cd ../..    # volver a sistema-eidas/
   python3 scripts/grupos.py publicar grupo-prueba
   ```
4. **Verificación cruzada:** volvé a loguearte como la cuenta de estudiante de prueba (o
   mirá el repo sin sesión, si es público) y confirmá que el archivo de devolución
   apareció en `feedback/AAAA-MM-DD.md` del repo de prueba, en la rama `main`.

## 5. Notificar por N8N

1. `cd infra/n8n && docker compose up -d` (si no estaba corriendo).
2. Entrá a http://localhost:5678, abrí el workflow **"Evaluacion EIDAS"**.
3. En **"Datos de la devolución"**: `grupo_id = grupo-prueba`, `fecha = AAAA-MM-DD` (la de hoy).
4. **Test workflow**.
5. Verificá:
   - Que apareció el archivo `grupo-prueba_AAAA-MM-DD.md` en la carpeta **"Devoluciones
     EIDAS"** de Drive.
   - Que llegó el mail al email que pusiste en `grupos.json` para este grupo, con el link
     correcto al archivo.

## 6. Limpieza — dejar todo como estaba

No te olvides de este paso, para no dejar basura de prueba en el sistema real:

1. Sacá la entrada `grupo-prueba` de `grupos.json`.
2. `rm -rf grupos/grupo-prueba` y `rm sistema-eidas/feedback/grupo-prueba_*.md`.
3. Borrá el archivo de prueba subido a Drive (carpeta "Devoluciones EIDAS").
4. Opcional: borrá el repo `eidas-prueba-circuito` desde la cuenta de estudiante de prueba
   (Settings → General → Delete this repository), si no lo vas a reusar en la próxima prueba.

---

## Problemas conocidos (por si algo falla)

Cosas que ya nos mordieron una vez armando esto — si algo se rompe, empezar por acá:

- **`git push` falla al publicar:** casi siempre es que te olvidaste de agregarte como
  colaborador con permiso de escritura en el repo del grupo (paso 1.4).
- **N8N tira error de DNS (`EAI_AGAIN`) al conectar con Google:** el contenedor no heredó
  las variables de proxy del host. Revisar que `HTTP_PROXY`/`HTTPS_PROXY` estén seteadas en
  el shell antes de `docker compose up`, y que `infra/n8n/docker-compose.yml` las pase al
  contenedor (ya está resuelto en el compose actual, pero si se reinstala desde cero puede
  volver a pasar).
- **N8N tira "Access to the file is not allowed":** falta `N8N_RESTRICT_FILE_ACCESS_TO` en
  el `docker-compose.yml`, o el path no coincide con `/home/node/data/...`. Ya está
  configurado en el compose actual — si aparece este error, algo se rompió en esa config.
- **El mail llega con datos vacíos o `undefined`:** algún nodo de N8N está usando `$json`
  en vez de `$('Nombre del nodo').item.json` para referenciar un campo que viene de dos
  pasos atrás (Google Drive y "Extract from File" pisan el `$json` con su propia salida).

---

*Sistema EIDAS — Terciario Urquiza — Rosario, 2026*

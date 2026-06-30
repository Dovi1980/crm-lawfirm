# 📋 Estado y Bitácora del Proyecto — CRM Lex Studio

Bitácora viva del proyecto. Debe actualizarse al final de cada sesión de trabajo significativa.

---

## 📅 Información de control

- **Última actualización:** 2026-06-26
- **Rama Git activa:** `main` (último commit `6ba4b71`)
- **Versión funcional:** v2.0.1a (adjuntos por caso + lectura multimodal por IA)
- **Tests:** 39/39 ✅ (sqlite-in-memory para unit; Postgres real en CI)
- **Build frontend:** ~404 KB / 114 KB gzip
- **Proveedor IA en uso:** Gemini (`gemini-2.5-flash` por defecto, `gemini-2.5-pro` para redacción pesada)
- **Despliegue local:** Docker Compose (Postgres, FastAPI, React/Vite, Nginx) — dev y prod separados

---

## 🏗️ Arquitectura actual

```mermaid
graph TD
    Client[Navegador] -->|Puerto 80| Nginx[Nginx Proxy]
    Nginx -->|/api/*| FastAPI[Backend FastAPI]
    Nginx -->|/*| Frontend[SPA React]
    FastAPI -->|asyncpg| PostgreSQL[(PostgreSQL 15)]
    FastAPI -->|BaseAIProvider| Provider{AI Provider Factory}
    Provider -->|AI_PROVIDER=anthropic| Anthropic[Anthropic Claude]
    Provider -->|AI_PROVIDER=openai| OpenAI[OpenAI / Azure]
    Provider -->|AI_PROVIDER=gemini| Gemini[Google Gemini]
```

### Decisión arquitectónica clave: capa de IA universal

Toda la app consume una interfaz abstracta `BaseAIProvider`. El switch entre proveedores es una variable de entorno — no hay código atado a Anthropic, OpenAI o Gemini en ningún lado fuera de `app/services/ai/<provider>.py`. Esto deja al cliente final libre de:

- Usar su suscripción existente con cualquier proveedor
- Cambiar de proveedor sin tocar la app
- Negociar precio con quien quiera

---

## ✅ Fases completadas

### Fase 1 — Hardening (seguridad y operación)
- Refresh token en **cookie HttpOnly** con rotación (XSS-resistente)
- Single-flight refresh en el cliente (evita N llamadas paralelas a `/refresh`)
- `alembic.ini` sin credenciales hardcodeadas
- Build de producción multi-stage (SPA estática en image de Nginx)
- `docker-compose.prod.yml` separado (sin source volumes, sin Node container)
- Scripts `setup.sh` y `setup.ps1` (un comando: docker → migrar → seed)
- Suite de tests: auth + RBAC + inmutabilidad (verifica rutas de FastAPI, no solo runtime)

### Fase 2 — IA conversacional
- Capa abstracta `BaseAIProvider` + adaptadores Anthropic / OpenAI / Gemini
- Factory que lee `AI_PROVIDER` y cachea la instancia (`lru_cache`)
- `ai_service.py` arma dossiers del caso (metadata + 30 interacciones + tasks abiertas)
- 3 endpoints SSE:
  - `POST /api/ai/cases/{id}/summary` (sync, resumen de 8 viñetas)
  - `POST /api/ai/cases/{id}/chat` (chat con contexto del caso)
  - `POST /api/ai/assistant` (asistente flotante global, sin contexto)
- Hook `useAIStream` consume SSE con `fetch` + `ReadableStream` (no se puede usar EventSource por auth header)
- UI: `ChatPanel` reutilizable, `FloatingAssistant` global, `CaseAIPanel` en el detalle de caso

### Fase 3 — Redacción asistida, export y templates dinámicos
- Modelo `Document` (append-only, `is_archived` para soft delete) + migración
- 4 templates de sistema en código: `carta_documento`, `intimacion_cobro`, `escrito_presentacion`, `convenio_honorarios`
- Wizard de 3 pasos en UI: picker → variables → streaming preview → guardar
- Export **DOCX** (python-docx) y **PDF** (reportlab) — puro Python, sin LibreOffice/Cairo en el image
- Parser de Markdown propio para alimentar ambos renderers (headings, listas, **bold**, *italic*)
- Modelo `CustomTemplate` con variables como JSON; built-in tiene precedencia sobre custom en caso de colisión
- CRUD `/api/templates/` admin-only (`RoleChecker`) + catálogo lectura libre (`GET /api/templates/catalog` con flag `is_builtin`)
- Página admin `/templates` con cards built-in (badge "Sistema") vs custom (editables)
- Modal con form: clave, nombre, descripción, instrucción para el modelo, editor dinámico de variables

### v2.0.1a — Documentación escaneada + lectura multimodal por IA
- Capa de IA ahora **multimodal**: `AIAttachment` (mime_type, data, filename) + campo `attachments` en `AIMessage`. Gemini envía `inline_data` base64; Anthropic/OpenAI rechazan adjuntos con `ProviderError` claro (multimodal pendiente en esos adaptadores).
- Modelo `Attachment` (binario en volumen Docker `attachments_data`, metadata en DB) + migración `c3d4e5f6a7b8`.
- `services/attachment_storage.py`: guarda con nombre UUID, protección anti path-traversal.
- Endpoints `/api/cases/{id}/attachments/`: upload (valida MIME + tamaño 15 MB), list, download, delete (assistant no puede).
- Análisis IA: `POST /api/ai/cases/{id}/attachments/{aid}/analyze` (SSE) — lee el documento con Gemini multimodal y devuelve resumen + texto listo para cargar como gestión.
- UI `CaseAttachmentsSection`: subida, listado, panel de análisis en streaming, "Cargar como gestión" que pre-llena y guarda una interacción.
- **Fix Gemini 2.5**: los modelos "piensan" por defecto y esos tokens salían del presupuesto de salida → el texto se cortaba. Solución: presupuesto de salida separado del thinking + thinking deshabilitado en modelos `flash` + reintento automático en 503/429.
- `seed_demo.py`: datos de demostración (2 abogados, 5 clientes, 5 expedientes con gestiones, 2 tareas).

### Fix de CI (2026-06-26)
- `test_immutability.py` fallaba en CI porque FastAPI ≥0.138 / Starlette ≥1.3 dejaron de aplanar los routers incluidos en `app.routes` (ahora son objetos opacos `_IncludedRouter`). Como `requirements.txt` usa `>=`, CI instala siempre lo último y rompió el helper que recorría `app.routes`. Reescrito para leer el schema OpenAPI (`app.openapi()`), estable entre versiones.

---

## 🧪 Cobertura de tests

| Archivo | Foco | Tests |
| :--- | :--- | :--- |
| `test_main.py` | Health check | 1 |
| `test_auth.py` | Login OK/KO, cookie HttpOnly, rotación de token, logout revoca, endpoint protegido sin token | 7 |
| `test_rbac.py` | Lawyer ve solo sus casos, no puede ver ajenos por ID, admin ve todos, assistant no borra | 5 |
| `test_immutability.py` | No existen rutas PUT/PATCH/DELETE en `/interactions` (verifica tabla de rutas + runtime) | 6 |
| `test_export.py` | Parser de markdown distingue bloques, DOCX produce ZIP válido, PDF produce magic bytes | 4 |
| `test_templates.py` | Admin CRUD, lawyer no puede crear, no se puede shadowizar built-in, duplicados rechazados, catalog list | 8 |
| `test_attachments.py` | Upload + validación de tipo, RBAC, descarga, assistant no borra, shape multimodal de Gemini, thinking budget, rechazo de adjuntos en providers text-only | 8 |
| **Total** | | **39** |

> El helper de `test_immutability.py` lee el schema OpenAPI (`app.openapi()`), no `app.routes`, para ser estable ante cambios de FastAPI (ver Fix de CI arriba).

---

## 🔑 Decisiones de diseño que conviene recordar

1. **Documents append-only.** Cada `guardar` es una fila nueva — nunca se sobrescribe. Soft delete con `is_archived`, igual que interactions.
2. **Built-in templates inmutables.** Viven en código (`document_templates.py`) y siempre ganan sobre custom. El admin extiende, no shadowiza.
3. **Refresh token NUNCA en localStorage.** Cookie HttpOnly, `Path=/api/auth`, `SameSite=lax`. El cliente nunca tiene acceso JS al refresh.
4. **Auth = bearer en header + cookie en refresh.** El access token corto sí va en `Authorization`; el refresh en cookie. Mejor del XSS y mejor UX que doble cookie.
5. **SSE con `fetch`, no `EventSource`.** EventSource no permite Authorization header. Se parsea el stream a mano (~30 líneas en `useAIStream`).
6. **Multi-proveedor desde el día 1.** No hay `import anthropic` fuera de `anthropic_provider.py`. Aplicar el mismo patrón si se agrega Mistral/Cohere/Bedrock.
7. **Export sin deps de sistema.** Se descartó WeasyPrint (necesita Cairo/Pango); python-docx + reportlab son puro Python y mantienen el image chico.
8. **Adjuntos: binario en disco, metadata en DB.** El archivo va al volumen Docker con nombre UUID; la DB solo guarda el mapeo. Lectura/borrado siempre vía `os.path.basename` (anti path-traversal).
9. **Multimodal solo en Gemini (hoy).** La lectura de PDF/imagen funciona con Gemini; Anthropic/OpenAI devuelven `ProviderError` claro si reciben adjuntos. Agregarlo en esos adaptadores es localizado (~30 LOC c/u).
10. **Gemini 2.5 "piensa" y consume `maxOutputTokens`.** Siempre dar al texto su presupuesto ADEMÁS del de thinking, y desactivar thinking en modelos `flash` (`thinkingBudget: 0`); Pro no permite desactivarlo. Si no, el texto se corta a mitad.
11. **Tests de rutas: usar `app.openapi()`, no `app.routes`.** FastAPI ≥0.138 no aplana los routers incluidos; el schema OpenAPI es la fuente estable.

---

## 🛣️ Próximos pasos sugeridos (no comprometidos)

**Siguiente planificado — v2.0.1b:** que la IA cree el expediente **pre-llenado** a partir de un documento escaneado cuando el caso todavía no existe (la IA propone los campos; el abogado revisa y confirma — nunca creación silenciosa).

| Idea | Costo aprox | Cuándo conviene |
| :--- | :--- | :--- |
| Audit log de quién leyó qué documento | medio | Cuando el cliente lo pida por compliance |
| Pinear versiones / `requirements.lock` | bajo | Para builds reproducibles (CI ya rompió una vez por `>=`) |
| Versión multi-tenant (mismo deploy, varios estudios) | alto | Solo si el negocio crece a SaaS |
| Plantillas DOCX cargadas por el usuario (no Markdown) | medio | Si se piden "membrete del estudio" en exports |
| Adapter Mistral / Bedrock | bajo | Cuando un cliente lo pida (~70 LOC + tests) |
| OAuth con Google Workspace | medio | Si el estudio ya usa Google |
| Búsqueda full-text en documentos generados | medio | Cuando el catálogo crezca a >100 docs/caso |

---

## ⚠️ Cosas que NO conviene tocar sin pensarlo dos veces

- Las rutas `/interactions` (la inmutabilidad es un requisito legal — los tests fallan si se agrega PUT/DELETE)
- El scope del cookie de refresh (`Path=/api/auth`) — moverlo a `/` rompe el modelo de seguridad
- Mover `document_templates.py` a DB sin mantener la precedencia built-in > custom — admins podrían bloquear features de sistema
- `BaseAIProvider.complete()` y `.stream()` — son la frontera con cada SDK; cambios de firma rompen los 3 adapters

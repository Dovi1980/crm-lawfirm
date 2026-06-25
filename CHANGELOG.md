# Changelog

Todas las versiones notables del proyecto se documentan acá. Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y [Versionamiento Semántico](https://semver.org/lang/es/).

---

## [Unreleased]

Sin cambios pendientes.

---

## [0.3.0] — 2026-06-24 — Redacción asistida, export y templates dinámicos

### Added

- **Modelo `Document`** persistido por caso, append-only con soft delete (`is_archived`).
- **4 templates de sistema** de redacción asistida: `carta_documento`, `intimacion_cobro`, `escrito_presentacion`, `convenio_honorarios`.
- **Endpoint streaming** `POST /api/ai/cases/{id}/document/generate` que combina dossier del expediente + template + variables del usuario.
- **CRUD persistente** de documentos por caso (`/api/cases/{id}/documents/`) con RBAC heredado del scoping de casos.
- **Exportación a DOCX** (`python-docx`) y **PDF** (`reportlab`) mediante `GET /api/cases/{id}/documents/{doc_id}/export?format=docx|pdf`.
- Parser propio de Markdown (`document_export.py`) que alimenta ambos renderers — soporta headings, listas, `**bold**` e `*italic*`.
- **Modelo `CustomTemplate`** con variables como JSON, para que el admin extienda el catálogo desde la UI.
- **CRUD admin de templates** en `/api/templates/` (POST/PUT/DELETE solo admin vía `RoleChecker`).
- **Endpoint catálogo** `GET /api/templates/catalog` con flag `is_builtin` para distinguir origen.
- **Servicio merge** (`template_service.py`): built-in siempre gana en colisión de claves; admin no puede shadowizar templates de sistema.
- **Página admin `/templates`** con cards de built-in (badge "Sistema", solo lectura) y custom (CRUD completo) + modal con editor dinámico de variables.
- **UI exportación**: botones de descarga DOCX/PDF en cada documento y en el viewer modal.
- 8 tests de templates CRUD + RBAC + 4 tests del exportador (verifican magic bytes ZIP/PDF).

### Changed

- Router IA ahora consume `template_service.list_all_templates()` y `get_template_resolved()` (versiones async que mergean built-in + DB).
- Sidebar incluye nueva entrada **"Templates de IA"** visible solo para admin.

### Database

- Migración `a1b2c3d4e5f6_add_documents_table.py`.
- Migración `b2c3d4e5f6a7_add_custom_templates.py` (JSON column con compat Postgres JSONB / SQLite JSON).

---

## [0.2.0] — 2026-06-23 — Capa de IA universal + chat con contexto

### Added

- **Interfaz abstracta `BaseAIProvider`** en `backend/app/services/ai/base.py` con `complete()` y `stream()` async.
- **Tres adaptadores**:
  - `AnthropicProvider` usando el SDK oficial de Anthropic
  - `OpenAIProvider` (compatible con Azure OpenAI vía `OPENAI_BASE_URL`)
  - `GeminiProvider` vía HTTPS raw con `httpx` (sin SDK extra para no engordar el image)
- **Factory** `get_ai_provider()` con `lru_cache(1)` que lee `AI_PROVIDER` del env.
- **Servicio de dominio** `ai_service.py` que arma dossiers del caso (metadata + 30 últimas interacciones + tasks abiertas).
- **3 endpoints** bajo `/api/ai/`:
  - `POST /cases/{id}/summary` — resumen ejecutivo sync, 8 viñetas
  - `POST /cases/{id}/chat` — chat con contexto del caso (SSE streaming)
  - `POST /assistant` — asistente global sin contexto (SSE streaming)
- **Hook `useAIStream`** que consume SSE con `fetch` + `ReadableStream` (no `EventSource` por restricción de auth header).
- **Componentes**:
  - `ChatPanel.jsx` reutilizable (history + streaming bubble + abort + error display)
  - `FloatingAssistant.jsx` (burbuja global en `Layout`)
  - `CaseAIPanel.jsx` (botones "Resumir caso" y "Hablar sobre el caso" en el detalle de caso)
- Variables de entorno nuevas: `AI_ENABLED`, `AI_PROVIDER`, `AI_MODEL_DEFAULT`, `AI_MODEL_DEEP`, `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `OPENAI_BASE_URL`, `GEMINI_API_KEY`.

### Notes

- El `system prompt` incluye guardrails para contexto jurídico argentino: no inventa citas legales, no inventa jurisprudencia, marca sugerencias como tales.

---

## [0.1.0] — 2026-06-23 — Seguridad y operación

### Added

- **Cookie HttpOnly para el refresh token** con `Path=/api/auth`, `SameSite=lax`, `Secure` configurable (`COOKIE_SECURE`).
- **Rotación de refresh token** atómica: cada `POST /api/auth/refresh` invalida el anterior.
- **Single-flight refresh** en el cliente (`axiosClient.js`): N llamadas 401 paralelas disparan una sola llamada a `/refresh` y comparten su promesa.
- **Build de producción** vía `nginx/Dockerfile.prod` multi-stage que compila la SPA y la sirve estática.
- **`docker-compose.prod.yml`** separado del dev: sin source mounts, sin Node container, `--workers 2`, CSP estricta sin `unsafe-inline`.
- **Scripts de setup** `setup.sh` (bash/WSL) y `setup.ps1` (PowerShell): copian `.env.example`, levantan docker, esperan a Postgres, corren migraciones y siembran admin.
- **Suite de tests inicial**:
  - `test_auth.py` — 7 tests del flujo de auth (cookie, rotación, lockout implícito)
  - `test_rbac.py` — 5 tests de scoping por rol en casos
  - `test_immutability.py` — 6 tests que verifican la **tabla de rutas** de FastAPI (no solo runtime) para garantizar que no existen PUT/DELETE en `/interactions`
- `conftest.py` con sqlite-in-memory y `dependency_overrides` para `get_db` — no requiere Docker para correr tests.
- `pytest.ini` con `asyncio_mode = auto`.

### Changed

- `axiosClient.js`: `withCredentials: true`, refresh leído de cookie, sin `refresh_token` en localStorage.
- `AuthContext.jsx`: `login()` ya no guarda refresh token; `logout()` no lo envía manualmente.
- Schema `TokenResponse`: removido `refresh_token` del body.
- `alembic.ini`: removidas credenciales hardcodeadas (el `env.py` ya usaba `settings.DATABASE_URL`).

### Security

- Refresh token resistente a XSS — JavaScript no puede leer la cookie.
- Cierre de la sesión revoca el token en DB **y** borra la cookie del browser.

---

## [pre-0.1] — Estado inicial

MVP funcional de gestión de clientes / expedientes / interacciones / tareas con RBAC (admin / lawyer / assistant), inmutabilidad del historial, lockout por intentos fallidos, dashboard con KPIs y CI básico.

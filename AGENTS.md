# AGENTS.md — Guía de contexto para agentes de IA

Este archivo orienta a agentes de código (Claude Code, Cursor, Aider, OpenAI Codex, GitHub Copilot Workspace, etc.) que trabajen sobre este repositorio. **Léelo entero antes del primer cambio.** Las decisiones de diseño y los invariantes están acá; no los descubras volviendo a leer todo el código.

Este documento complementa al `README.md` (orientado a humanos), al `PROJECT_STATUS.md` (bitácora) y al `CHANGELOG.md` (historial por fases).

---

## 1. Qué es este repo

CRM web full-stack para estudios jurídicos chicos / medianos (2-20 letrados), en español rioplatense. Cada estudio corre su propia instancia Docker — no hay multitenancy. Funciones:

- Gestión de **clientes**, **expedientes** (con auto-numeración `EXP-AAAA-NNNN`), **interacciones** append-only, **tareas**.
- **RBAC de 3 roles**: `admin`, `lawyer`, `assistant`.
- **IA integrada** con capa universal (Anthropic / OpenAI / Gemini intercambiables vía variable de entorno) que cubre: resumen de caso, chat con contexto del expediente, asistente flotante global, **redacción asistida de documentos** con templates de sistema + templates personalizables desde la UI por admin.
- **Exportación DOCX y PDF** de los documentos generados, sin dependencias de sistema.

Estado funcional: **v0.3** (fases 1-3 completas). 31 tests verdes. Ver `CHANGELOG.md`.

---

## 2. Stack y versiones

| Capa | Tecnología | Notas |
| :--- | :--- | :--- |
| Lenguaje backend | Python 3.11 (3.10 en CI) | `from __future__ import annotations` en módulos nuevos |
| Framework backend | FastAPI async + SQLAlchemy 2.0 + asyncpg | Pydantic v2 |
| DB | PostgreSQL 15 en prod / SQLite in-memory en tests | Migraciones con Alembic |
| Frontend | React 18 + Vite + TailwindCSS 3 + TanStack Query v5 + React Router 6 | JS, no TS |
| Estilos | Tailwind con tokens `legal-gold`, `legal-navy-deep`, `legal-cream` | utilities `.premium-input`, `.premium-btn-primary`, `.premium-btn-secondary`, `.premium-card`, `.timeline-pill` |
| Iconos | `lucide-react` | |
| SDKs IA | `anthropic`, `openai`, `httpx` (Gemini via raw HTTPS) | |
| Export | `python-docx`, `reportlab` | Puro Python. No reemplazar por WeasyPrint sin discutir antes. |
| Tests | pytest + pytest-asyncio + httpx + aiosqlite | `asyncio_mode = auto` |
| Proxy | Nginx | dev: reverse proxy a Vite; prod: SPA estática + reverse proxy |

---

## 3. Comandos canónicos

Trabajá desde la raíz del repo salvo que se indique lo contrario.

### Setup inicial

```bash
cp .env.example .env                  # Linux/Mac/WSL
# Copy-Item .env.example .env          # PowerShell
./setup.sh dev                        # ./setup.ps1 -Mode dev en PowerShell
```

Levanta los 4 contenedores, espera a Postgres, corre migraciones y siembra el admin.

### Tests del backend (sin Docker)

```bash
cd backend
# Una vez:
python -m venv .venv && .venv/bin/activate    # (.venv\Scripts\activate en Windows)
pip install -r requirements-dev.txt

# Cada corrida:
pytest                                # 31 tests, ~13s; usa sqlite in-memory
pytest tests/test_auth.py -v          # un archivo concreto
pytest -k "rbac"                      # filtrar por nombre
```

El `conftest.py` setea `DATABASE_URL=sqlite+aiosqlite:///:memory:` con `os.environ.setdefault` **antes** de importar la app. Si agregás un test que importa `app.X` arriba del archivo, va a heredar esa config automáticamente.

### Build del frontend

```bash
cd frontend
npm install                # solo la primera vez
npm run dev                # Vite con HMR en :3000 (lo levanta el docker-compose en dev)
npm run build              # output en dist/
```

El build debe terminar **sin warnings ni errors**. Si los hay, son nuevos — arreglalos antes de cerrar la tarea.

### Migraciones de DB

```bash
docker compose exec backend alembic upgrade head        # aplicar
docker compose exec backend alembic revision --autogenerate -m "descripción"
docker compose exec backend alembic downgrade -1        # rollback (raramente)
```

**Las migraciones generadas con `--autogenerate` SIEMPRE hay que revisarlas a mano** antes de commitear. Alembic no detecta todos los cambios (renombres, defaults custom).

### Linting / formato

El proyecto **no tiene linter configurado todavía**. Si lo agregás, propónelo en un commit separado. El estilo actual es:

- Python: 4 espacios, líneas de hasta ~100 columnas, comillas dobles, type hints en firmas públicas, `from __future__ import annotations` en módulos nuevos. Sin docstring obligatorio en cada función pero sí en las que tienen lógica no obvia.
- JS/JSX: comillas simples para strings, 2 espacios, sin punto y coma final, funciones flecha para componentes.

---

## 4. Mapa de arquitectura

```
┌──── Browser ────┐
│  React SPA      │
│  ↕ cookie HttpOnly (refresh) + Authorization: Bearer (access)
└─────────────────┘
        │ HTTP
        ▼
┌──── Nginx ────────────────────────────┐
│  /            → SPA estática (prod) o frontend:3000 (dev)
│  /api/*       → backend:8000
└───────────────────────────────────────┘
        │
        ▼
┌──── FastAPI (uvicorn) ─────────────────┐
│  routers/       auth, users, clients, cases,
│                 interactions, tasks, ai,
│                 documents, templates
│  middleware/    get_current_user, RoleChecker
│  services/      auth, email, ai_service, template_service,
│                 document_export, document_templates,
│                 ai/  ← provider factory + adapters
│  models/        SQLAlchemy 2.0 ORM
│  schemas/       Pydantic v2 (req/res)
└────────────────────────────────────────┘
        │ asyncpg
        ▼
   PostgreSQL 15
        │
        └── (en tests) sqlite-in-memory vía dependency_overrides
```

### Donde vive cada cosa

| Si tu cambio toca... | Archivo principal |
| :--- | :--- |
| Login, refresh, logout, lockout | `backend/app/routers/auth.py` + `services/auth_service.py` |
| Validación de token / RBAC | `backend/app/middleware/security.py` (`get_current_user`, `RoleChecker`) |
| Scoping de un recurso por rol | El propio router del recurso (ej. `cases.py`'s `get_scoped_case`) |
| Capa de IA — agregar proveedor | `backend/app/services/ai/<nombre>_provider.py` + ajuste de `factory.py` |
| System prompt o dossier del caso | `backend/app/services/ai_service.py` |
| Catálogo de templates de sistema | `backend/app/services/document_templates.py` |
| Templates persistidos (admin) | `backend/app/routers/templates.py` + `models/custom_template.py` |
| Render DOCX/PDF | `backend/app/services/document_export.py` |
| SPA shell / asistente flotante | `frontend/src/components/Layout.jsx` + `components/ai/FloatingAssistant.jsx` |
| Streaming SSE en cliente | `frontend/src/hooks/useAIStream.js` |
| Wizard de redacción | `frontend/src/components/ai/DocumentDraftModal.jsx` |
| Cookie HttpOnly y auth en cliente | `frontend/src/api/axiosClient.js` + `context/AuthContext.jsx` |

---

## 5. Invariantes — **no romper sin discusión explícita**

Estas reglas están enforced por tests, por compliance legal o por seguridad. Romperlas en silencio es la principal forma en que un agente de IA puede causar daño en este repo.

1. **Las interacciones son append-only.** No agregar rutas `PUT`, `PATCH` o `DELETE` en `routers/interactions.py`. `tests/test_immutability.py` lee la tabla de rutas de FastAPI y falla si las detecta. Esto es un requisito legal del estudio jurídico, no preferencia técnica.

2. **El refresh token vive en cookie HttpOnly con `Path=/api/auth`.** No moverlo a localStorage, no expandir el scope del cookie. El cliente nunca debe tener acceso JavaScript al refresh.

3. **Built-in templates ganan sobre custom.** Si admin crea un template con la misma `key` que uno de sistema, el backend devuelve 409 (`POST /api/templates/`) y el merge en `template_service.py` ignora el custom. No invertir la precedencia.

4. **`BaseAIProvider` es la frontera con los SDK.** No hacer `import anthropic` ni `import openai` fuera de `services/ai/<provider>_provider.py`. La firma de `complete()` y `stream()` no se cambia sin actualizar los 3 adapters al mismo tiempo.

5. **El refresh token rota en cada uso.** El viejo se invalida en DB. Si modificás `routers/auth.py:refresh_tokens()`, mantenelo así.

6. **No commitear `.env` ni secrets.** Solo `.env.example`. El `.gitignore` lo cubre, pero si tu cambio toca esos archivos verificá doble.

7. **RBAC de Lawyer en `cases`**: el helper `get_scoped_case()` en `routers/cases.py` filtra por `assigned_lawyer_id == current_user.id` para lawyers. Cualquier ruta que sirva datos de un caso a un lawyer **debe** pasar por ese helper. Los endpoints de IA reutilizan `get_scoped_case` por eso mismo.

8. **`Assistant` no borra**. Para cada operación destructiva nueva, agregar el check `if current_user.role == UserRole.ASSISTANT: raise 403`. Documentos: el archive (soft delete) ya hace ese check; replicar el patrón.

---

## 6. Capa de IA multi-proveedor (el corazón del diseño)

El switch entre Anthropic / OpenAI / Gemini es **una variable de entorno**, no un fork de código. Esto es deliberado: cada estudio jurídico cliente puede usar el proveedor con el que ya tiene contrato.

```
backend/app/services/ai/
├── base.py                  # BaseAIProvider (abstract): complete(), stream()
├── anthropic_provider.py    # usa anthropic SDK; default claude-sonnet-4-6
├── openai_provider.py       # usa openai SDK; compatible con Azure OpenAI vía OPENAI_BASE_URL
├── gemini_provider.py       # HTTPS raw con httpx (sin SDK de Google)
└── factory.py               # lee AI_PROVIDER, cachea con @lru_cache(1)
```

### Reglas para agregar un proveedor nuevo

1. Implementar `BaseAIProvider` en `services/ai/<nuevo>_provider.py`.
2. Agregar la rama en `factory.py`.
3. Documentar variables de entorno en `.env.example` y `config.py`.
4. **No hacer falta tocar nada de `ai_service.py`, routers ni frontend** — si lo necesitás, algo del diseño se rompió.

### Reglas para tocar `ai_service.py`

- `_load_case_context()` arma el dossier del caso. Cualquier campo nuevo del modelo `Case` que sea relevante para la IA hay que agregarlo ahí.
- Los system prompts viven en constantes al inicio (`_BASE_SYSTEM_PROMPT`). Mantener los guardrails: no inventar citas legales, no inventar jurisprudencia, marcar sugerencias.
- Si agregás un endpoint IA nuevo, seguí el patrón `async def stream_X(...) -> AsyncIterator[str]` y el wrapper SSE del router.

### Streaming SSE — convención del wire format

```
data: {"text": "..."}\n\n     ← chunk de texto
event: error\ndata: {...}\n\n ← error
data: [DONE]\n\n              ← terminator (siempre se manda en el finally)
```

El cliente espera esto en `frontend/src/hooks/useAIStream.js`. Cualquier formato distinto rompe el frontend en silencio (sigue al modo "loading" indefinidamente).

---

## 7. Patrones de test

```
backend/tests/
├── conftest.py          # fixtures: db_engine, db_session, client, admin_user, lawyer_user, ...
├── test_main.py         # health check
├── test_auth.py         # auth flow + cookie + rotación
├── test_rbac.py         # scoping por rol en cases
├── test_immutability.py # verifica tabla de rutas de FastAPI
├── test_export.py       # parser markdown + magic bytes DOCX/PDF
└── test_templates.py    # CRUD admin + merge built-in/custom
```

Patrones que conviene seguir:

- Para tests de RBAC: usar las fixtures `admin_user` / `lawyer_user` / `other_lawyer_user` / `assistant_user`, llamar `login()` y `auth_headers()`.
- Para tests que necesitan datos seed (clientes, casos): crear fixtures locales en el archivo de test (ver `test_rbac.py:seed_client`).
- Para tests que verifican que algo **no existe**: leer la tabla de rutas de FastAPI (`app.routes`) — no asumir 404/405 en runtime. Ver `test_immutability.py:_interaction_routes_by_method`.
- **Sin mocks de la API de IA todavía**. Tests de funciones que llaman al provider no están escritos. Cuando se agreguen, usar inyección de dependencia para reemplazar `get_ai_provider()` por un fake, no monkeypatch.

---

## 8. Convenciones de UI

- **Todas las strings visibles al usuario en español** (rioplatense, voseo). Identificadores en código en inglés.
- **Avisos legales**: cualquier output de IA visible al usuario debe llevar un disclaimer del tipo *"Borrador generado por IA. Validá antes de firmar o presentar."* Los componentes existentes ya lo hacen, replicar el patrón.
- **Roles en UI**: usar el hook `useAuth()` que expone `isAdmin`, `isLawyer`, `isAssistant`. No comparar `user.role === 'admin'` a mano salvo en `ProtectedRoute` y `Sidebar`.
- **Llamadas a la API**: usar `axiosClient` (no `axios` directo) — tiene el interceptor de refresh y `withCredentials: true`.
- **Streaming**: usar el hook `useAIStream` reutilizable, no reimplementar el parseo SSE.
- **TanStack Query**: queries por recurso identificadas en `queryKey`. Después de mutaciones que afectan al caso o sus relaciones, invalidar las queries: `queryClient.invalidateQueries({ queryKey: ['caseDocuments', caseId] })`.

---

## 9. Gotchas conocidos

- **DateTime con timezone en SQLite**: SQLAlchemy lo emula como TEXT. Funciona pero no esperes precisión de microsegundos en tests.
- **bcrypt cost ≥ 12** hace que los tests de auth tarden ~200ms cada uno. Esto es deliberado (es la latencia real). No bajar el cost para acelerar tests.
- **Vite dev server con polling**: `vite.config.js` tiene `usePolling: true` porque sin eso el HMR no detecta cambios dentro del contenedor Docker en Windows.
- **CSP en dev vs prod**: dev permite `'unsafe-inline'` `'unsafe-eval'` para Vite. Prod las prohíbe (la SPA está pre-compilada). Si agregás algo que dependa de inline scripts/styles, va a romper en prod.
- **Migraciones con SQLite en tests**: las migraciones de Alembic **no se corren en tests**. El `conftest.py` usa `Base.metadata.create_all` directamente. Si rompés esa relación (ej. agregando una migración con DDL custom), los tests no la van a aplicar.
- **`nginx/Dockerfile.prod` contexto de build**: el `context` en `docker-compose.prod.yml` es `.` (raíz), no `./nginx`. Esto es así para que pueda copiar `frontend/` al build stage. Si lo cambiás, va a romper.
- **El frontend no tiene tipos**. No agregar TypeScript a medias — o el front entero o ninguno. Si lo discutís con el dueño del proyecto y deciden migrar, hacelo en un PR aparte completo.
- **SECRET_KEY de tests**: el `conftest.py` setea un valor fijo (`test_secret_key_for_pytest_runs_only_not_real`). No usar ese valor en ningún otro lado.

---

## 10. Convención de commits

El historial está limpio y descriptivo. Cuando hagas un cambio:

- Mensajes en español, conciso, formato libre (no se usa Conventional Commits estricto pero los prefijos `feat:`, `fix:`, `chore:`, `docs:`, `refactor:`, `test:` son bienvenidos).
- Un commit por unidad lógica de cambio. Si tu PR toca 3 cosas independientes, idealmente 3 commits.
- **No commitear sin que pasen los tests** (`pytest -q` desde `backend/`) y sin que el build del frontend pase (`npm run build` desde `frontend/`).

---

## 11. Antes de cerrar una tarea

Checklist mental:

1. ¿Pasa `pytest`? Tirá los 31+ tests, no solo los que tocaste.
2. ¿Pasa `npm run build`? Sin warnings nuevos.
3. ¿Toqué algún invariante de la sección 5? Si sí, justificarlo en el commit o revertir.
4. ¿Agregué dependencias? Actualizar `requirements.txt` o `package.json`. Verificar que el image sigue compilando.
5. ¿Cambié variables de entorno? Actualizar `.env.example` y la sección correspondiente del `README.md`.
6. ¿Agregué un endpoint, modelo o tabla? Actualizar `CHANGELOG.md` (sección `[Unreleased]`).
7. ¿Cambié algo que afecta al setup? Tirar `setup.sh dev` desde cero contra un `.env` fresco para validar.

---

## 12. Glosario rápido (español ↔ inglés del dominio)

| UI / docs (es) | Código (en) |
| :--- | :--- |
| Expediente | `Case`, `case` |
| Cliente | `Client`, `client` |
| Gestión / Interacción | `Interaction` |
| Tarea | `Task` |
| Abogado | `lawyer` (rol) |
| Asistente | `assistant` (rol) |
| Administrador | `admin` (rol) |
| Honorarios pactados | `agreed_fees` |
| Carta documento | `carta_documento` (template key) |
| Intimación de cobro | `intimacion_cobro` |
| Escrito de presentación | `escrito_presentacion` |
| Convenio de honorarios | `convenio_honorarios` |

---

## 13. Referencias

- **`README.md`** — para humanos: pitch, features, setup
- **`PROJECT_STATUS.md`** — bitácora del estado actual y decisiones de diseño con su justificación
- **`CHANGELOG.md`** — diff entre versiones; updaeálo en `[Unreleased]` mientras trabajás
- **`DEMO_GUIDE.md`** — walkthrough end-to-end para mostrar el producto
- **`.env.example`** — todas las variables de entorno con comentarios contextuales
- **`/api/docs`** — OpenAPI interactivo (con Docker corriendo) — `http://localhost/api/docs`

---

*Última revisión de este archivo: 2026-06-24 (v0.3).* Si la realidad del repo se aleja de lo descrito acá, actualizá esta guía en el mismo commit que el cambio.

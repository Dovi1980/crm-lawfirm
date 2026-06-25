# CRM Lex Studio — Sistema de Gestión para Estudios Jurídicos

**Lex Studio** es una plataforma web full-stack, segura y dockerizada para estudios jurídicos pequeños y medianos (2 – 20 letrados). Incluye **redacción asistida por IA** (multi‑proveedor: Anthropic, OpenAI o Gemini) con templates personalizables, chat con contexto del expediente, resúmenes automáticos y exportación a Word/PDF — todo bajo la misma arquitectura RBAC con inmutabilidad del historial.

> Cada despliegue es una instancia aislada por estudio (un Docker compose por cliente, sin datos compartidos).

---

## ✨ Características principales

### Gestión jurídica
- Clientes, expedientes (con auto‑numeración `EXP-AAAA-NNNN`), historial **append-only** de gestiones, tareas con vencimientos
- Tres roles con aislamiento estricto:
  - **Admin** — acceso total, gestión de personal y catálogo de templates de IA
  - **Lawyer (Abogado)** — solo ve sus expedientes y tareas asignadas
  - **Assistant** — lee todo el estudio, no puede borrar
- Dashboard con KPIs (clientes activos, expedientes abiertos, tareas vencidas, urgentes)

### IA integrada (universal, no atada a un proveedor)
- **Asistente flotante** disponible en toda la app para dudas generales
- **Chat con contexto del expediente** — el modelo conoce datos del caso + últimas 30 gestiones
- **Resumen ejecutivo del caso** con un click
- **Redacción asistida de documentos** con templates de sistema (carta documento, intimación de cobro, escrito de presentación, convenio de honorarios) **+ templates personalizables por admin desde la UI**
- **Exportación a DOCX y PDF** sin dependencias de sistema (puro Python)
- Streaming en vivo (SSE) — el usuario ve el documento mientras se redacta

### Seguridad
- **Refresh token en cookie HttpOnly** (resistente a XSS), con rotación automática + scope `Path=/api/auth`
- JWT access tokens (60 min) + bcrypt cost ≥ 12 para contraseñas
- **Rate limiting** (5 logins / 15 min por IP) + lockout (15 min tras 10 intentos fallidos)
- Cabeceras HTTP de seguridad estrictas (CSP sin `unsafe-inline` en prod, HSTS, X-Frame-Options)
- **Inmutabilidad** del historial: no existen rutas PUT/DELETE en `/interactions` ni se sobrescriben documentos generados

---

## 🛠️ Stack Tecnológico

| Capa | Tecnología |
| :--- | :--- |
| **Backend** | Python 3.11, FastAPI (async), SQLAlchemy 2.0 + asyncpg |
| **Base de datos** | PostgreSQL 15 con migraciones Alembic |
| **Frontend** | React 18 + Vite, TailwindCSS 3, TanStack Query v5, React Router 6 |
| **IA (intercambiable)** | Anthropic Claude / OpenAI / Google Gemini |
| **Export documentos** | `python-docx` (DOCX) + `reportlab` (PDF) — sin LibreOffice/Cairo |
| **Proxy / Web** | Nginx (dev: reverse proxy a Vite, prod: SPA estática + reverse proxy) |
| **Contenedores** | Docker + Docker Compose (compose separado para dev y prod) |
| **CI** | GitHub Actions (pytest + npm build) |

---

## 🚀 Guía de Arranque Rápido

### Setup en un comando

Linux / WSL / macOS:
```bash
cp .env.example .env
./setup.sh dev          # o "prod" para el build de producción
```

Windows / PowerShell:
```powershell
Copy-Item .env.example .env
.\setup.ps1 -Mode dev   # o "prod"
```

El script:
1. Crea `.env` desde el ejemplo si no existe
2. Levanta los contenedores con `docker compose up -d --build`
3. Espera a Postgres
4. Aplica las migraciones (`alembic upgrade head`)
5. Crea el usuario administrador inicial (`seed_admin.py`)

### Si preferís hacerlo a mano

```bash
cp .env.example .env
# Editar .env (SECRET_KEY, FIRST_ADMIN_PASSWORD, AI_PROVIDER, API key del proveedor)
docker compose up --build -d
docker compose exec backend alembic upgrade head
docker compose exec backend python seed_admin.py
```

Después abrir 👉 **[http://localhost](http://localhost)** y entrar con las credenciales de `.env`.

### Modo desarrollo vs producción

| Modo | Compose file | Frontend | Cuándo usarlo |
| :--- | :--- | :--- | :--- |
| **Dev** | `docker-compose.yml` | Vite con hot reload en su propio contenedor | Trabajo diario, cambios en frontend |
| **Prod** | `docker-compose.prod.yml` | SPA estática horneada dentro del nginx image, CSP estricta | Demo, despliegue a cliente, staging |

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

---

## ⚙️ Variables de entorno clave

Ver `.env.example` para la lista completa. Las más relevantes:

```env
# --- Seguridad ---
SECRET_KEY=                      # rotar SIEMPRE antes de prod
COOKIE_SECURE=False              # poner en True cuando esté detrás de HTTPS
COOKIE_SAMESITE=lax

# --- IA (cambiar de proveedor sin tocar código) ---
AI_ENABLED=True
AI_PROVIDER=anthropic            # anthropic | openai | gemini
AI_MODEL_DEFAULT=claude-sonnet-4-6
AI_MODEL_DEEP=                   # opcional para redacción larga, ej. claude-opus-4-8

# Solo se necesita la API key del proveedor elegido
ANTHROPIC_API_KEY=
OPENAI_API_KEY=
OPENAI_BASE_URL=                 # vacío para OpenAI; setear para Azure OpenAI / self-hosted
GEMINI_API_KEY=

# --- Admin inicial ---
FIRST_ADMIN_EMAIL=admin@estudio.com
FIRST_ADMIN_PASSWORD=CambiarEstoEnProd!
```

---

## 🧪 Tests

31 tests cubriendo: auth + cookie HttpOnly + rotación, RBAC en casos y documentos, inmutabilidad de interacciones, exportación DOCX/PDF, CRUD de templates personalizados con `is_builtin` flag.

```bash
cd backend
pip install -r requirements-dev.txt
pytest                   # usa sqlite-in-memory automáticamente
```

Las variables de entorno por defecto del `conftest.py` apuntan a SQLite, así que no se necesita Postgres corriendo para tests unitarios. La CI sí levanta Postgres real para validar contra el dialecto productivo.

---

## 📂 Estructura del repositorio

```
crm-lawfirm/
├── docker-compose.yml             # Stack de desarrollo (Vite + hot reload)
├── docker-compose.prod.yml        # Stack de producción (SPA estática)
├── setup.sh / setup.ps1           # Setup en un comando (bash y PowerShell)
├── .env.example                   # Plantilla de configuración
├── nginx/
│   ├── nginx.conf                 # Reverse proxy dev
│   ├── nginx.prod.conf            # SPA + reverse proxy prod, CSP estricta
│   └── Dockerfile.prod            # Multi-stage: build SPA → nginx slim
│
├── backend/
│   ├── Dockerfile                 # Imagen Python para FastAPI
│   ├── requirements.txt           # Runtime (FastAPI, SQLAlchemy, anthropic, openai, docx, reportlab)
│   ├── requirements-dev.txt       # pytest, httpx, aiosqlite, cov
│   ├── pytest.ini                 # asyncio_mode = auto
│   ├── alembic/                   # Migraciones (initial + documents + custom_templates)
│   ├── seed_admin.py              # Bootstrap del primer admin
│   ├── app/
│   │   ├── main.py                # Registro de routers + Dashboard stats
│   │   ├── config.py              # Pydantic Settings (cookies, IA, SMTP)
│   │   ├── database.py            # Engine asíncrono
│   │   ├── models/                # User, Client, Case, Interaction, Task, Token, Document, CustomTemplate
│   │   ├── schemas/               # Pydantic v2
│   │   ├── routers/               # auth, users, clients, cases, interactions, tasks, ai, documents, templates
│   │   ├── middleware/
│   │   │   └── security.py        # get_current_user + RoleChecker
│   │   └── services/
│   │       ├── auth_service.py
│   │       ├── email_service.py
│   │       ├── document_export.py        # Markdown → DOCX/PDF (puro Python)
│   │       ├── document_templates.py     # Templates de sistema (carta doc, intimación, etc.)
│   │       ├── template_service.py       # Merge built-in + custom (con precedencia)
│   │       ├── ai_service.py             # Orquestación: resumen, chat, redacción
│   │       └── ai/                       # Capa de proveedores
│   │           ├── base.py               # BaseAIProvider (interfaz)
│   │           ├── anthropic_provider.py
│   │           ├── openai_provider.py
│   │           ├── gemini_provider.py    # vía HTTPS raw, sin SDK extra
│   │           └── factory.py            # lee AI_PROVIDER
│   └── tests/                     # conftest + auth + rbac + immutability + export + templates
│
└── frontend/
    ├── Dockerfile                 # Vite dev server
    ├── package.json
    ├── tailwind.config.js
    └── src/
        ├── api/axiosClient.js     # withCredentials, single-flight refresh
        ├── context/AuthContext.jsx
        ├── hooks/
        │   ├── useAuth.js
        │   └── useAIStream.js     # Consumidor SSE reutilizable
        ├── components/
        │   ├── Layout.jsx         # Sidebar + Navbar + FloatingAssistant
        │   ├── Sidebar.jsx
        │   ├── ProtectedRoute.jsx
        │   ├── forms/             # CaseForm, ClientForm, InteractionForm, TaskForm, UserForm
        │   └── ai/
        │       ├── ChatPanel.jsx
        │       ├── FloatingAssistant.jsx     # Burbuja global en todas las rutas
        │       ├── CaseAIPanel.jsx           # Resumen + chat con contexto
        │       ├── DocumentDraftModal.jsx    # Wizard 3 pasos (template→variables→stream)
        │       └── CaseDocumentsSection.jsx  # Listado + descarga DOCX/PDF
        └── pages/
            ├── LoginPage.jsx
            ├── DashboardPage.jsx
            ├── ClientsPage.jsx, ClientDetailPage.jsx
            ├── CasesPage.jsx, CaseDetailPage.jsx
            ├── TasksPage.jsx
            ├── UsersPage.jsx       # Admin: personal
            └── TemplatesPage.jsx   # Admin: catálogo de templates (built-in + custom)
```

---

## 🔌 Endpoints relevantes

| Recurso | Endpoint | Notas |
| :--- | :--- | :--- |
| Login (cookie + access token) | `POST /api/auth/login` | refresh token en cookie HttpOnly |
| Refresh con rotación | `POST /api/auth/refresh` | el cookie viejo se invalida |
| Logout | `POST /api/auth/logout` | revoca el token y borra el cookie |
| CRUD casos / clientes / tareas | `/api/cases`, `/api/clients`, `/api/tasks` | RBAC por rol |
| Append-only historial | `GET / POST /api/interactions` | no existe PUT/DELETE (verificado en tests) |
| Resumen IA del caso | `POST /api/ai/cases/{id}/summary` | sync, 8 viñetas |
| Chat IA con contexto | `POST /api/ai/cases/{id}/chat` | SSE streaming |
| Asistente global | `POST /api/ai/assistant` | SSE streaming |
| Catálogo de templates | `GET /api/ai/templates` | built-in + custom |
| Generar borrador | `POST /api/ai/cases/{id}/document/generate` | SSE streaming |
| Documentos guardados | `GET /api/cases/{id}/documents/` | persistidos por caso |
| Exportar DOCX o PDF | `GET /api/cases/{id}/documents/{doc_id}/export?format=docx\|pdf` | descarga directa |
| Templates admin | `GET /api/templates/catalog` (todos), `POST/PUT/DELETE /api/templates/` (solo admin) | gestión del catálogo |

Documentación OpenAPI interactiva: **[http://localhost/api/docs](http://localhost/api/docs)**

---

## 🧠 Cambiar de proveedor de IA

¿El cliente / estudio ya paga una suscripción con OpenAI? Editar `.env` y reiniciar:

```env
AI_PROVIDER=openai
AI_MODEL_DEFAULT=gpt-4o-mini      # o el modelo de su contrato
OPENAI_API_KEY=sk-...
```

Para Azure OpenAI: además setear `OPENAI_BASE_URL=https://<resource>.openai.azure.com/`.
Para Gemini: `AI_PROVIDER=gemini`, `AI_MODEL_DEFAULT=gemini-1.5-flash`, `GEMINI_API_KEY=...`.

Toda la aplicación consume una interfaz abstracta (`BaseAIProvider`); agregar otro proveedor (Mistral, Cohere, Bedrock, etc.) son ~70 líneas en `backend/app/services/ai/`.

---

## 📧 Email en desarrollo

Si `SMTP_HOST` está vacío en `.env`, los emails de recuperación de contraseña se imprimen en los logs del backend en lugar de enviarse. Verlos en vivo:

```bash
docker compose logs -f backend
```

---

## 🧪 CI / CD

Pipeline en `.github/workflows/ci.yml` que en cada push a `main` o pull request:

1. **Backend**: levanta Postgres 15 real, instala deps, corre `pytest` con cobertura
2. **Frontend**: instala con `npm ci` y corre `npm run build` para detectar errores de import / sintaxis

---

## 📜 Documentación adicional

- **`PROJECT_STATUS.md`** — bitácora del estado del proyecto, decisiones y próximos pasos
- **`CHANGELOG.md`** — historial de cambios versionado por fases
- **OpenAPI** en `/api/docs` — referencia interactiva de cada endpoint
- **`.env.example`** — todas las variables comentadas en su contexto

---

## ⚠️ Antes de poner en producción

1. **Rotar `SECRET_KEY`** (generar uno nuevo, 64+ chars)
2. **Cambiar `FIRST_ADMIN_PASSWORD`** y rotar tras el primer login
3. **`COOKIE_SECURE=True`** y desplegar detrás de HTTPS
4. **Setear `AI_PROVIDER` y la API key** del proveedor elegido — sin esto, los endpoints `/api/ai/*` devuelven 503
5. Cambiar contraseña de Postgres (`POSTGRES_PASSWORD`)
6. Usar `docker-compose.prod.yml` (frontend estático, CSP sin `unsafe-inline`, sin source mounts)
7. Considerar correr `seed_admin.py` con un email real y borrar el admin de prueba

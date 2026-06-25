# 🎬 Guía de demo — CRM Lex Studio

Walkthrough paso a paso para probar la aplicación de punta a punta en local. Sirve para validar los roles, el aislamiento de datos, los controles de seguridad y todas las funciones de IA.

> Reemplaza al antiguo `testeo.txt`. La guía está actualizada al estado de v0.3 (fases 1, 2 y 3 cerradas).

---

## Paso 1 — Preparar el entorno

Desde la raíz del repositorio:

```powershell
# PowerShell
Copy-Item .env.example .env
.\setup.ps1 -Mode dev
```

```bash
# bash / WSL / macOS
cp .env.example .env
./setup.sh dev
```

El script de setup levanta los 4 contenedores (Postgres, FastAPI, frontend Vite, Nginx), corre las migraciones y siembra el admin inicial.

**Para activar la IA**, antes de iniciar editá `.env` y completá según el proveedor de tu cliente:

```env
AI_PROVIDER=anthropic
AI_MODEL_DEFAULT=claude-sonnet-4-6
ANTHROPIC_API_KEY=sk-ant-...
```

> Si dejás `AI_ENABLED=False` o sin API key, la app sigue funcionando — los endpoints `/api/ai/*` solo devolverán 503.

---

## Paso 2 — Acceso de administrador y creación de personal

1. Abrí **http://localhost** e iniciá sesión con las credenciales de `.env` (por defecto `admin@estudio.com` / `AdminLawFirm2026!`).
2. En el sidebar entrá a **"Abogados & Personal"**.
3. Registrá dos miembros del estudio con **"Agregar Personal"**:

   | Rol | Email | Contraseña |
   | :--- | :--- | :--- |
   | Abogado (lawyer) | `pedro@estudio.com` | `PedroLawyer2026!` |
   | Asistente (assistant) | `ana@estudio.com` | `AnaAssistant2026!` |

---

## Paso 3 — Crear clientes y expedientes

1. En **"Clientes"** → "Nuevo Cliente":
   - **Juan Pérez** (CUIT `20-35492843-2`).
2. En **"Expedientes"** → "Nuevo Expediente":
   - **Caso 1**: *Divorcio Contencioso – Pérez c/ Gómez* → cliente: Pérez, materia: Familia, abogado asignado: **Admin** (vos).
   - **Caso 2**: *Cobro de Pesos – Pérez c/ Constructora* → cliente: Pérez, materia: Comercial, abogado asignado: **Pedro Letrado**.

---

## Paso 4 — Verificar el aislamiento de datos (rol Abogado)

1. Cerrá sesión e ingresá como **Pedro** (`pedro@estudio.com` / `PedroLawyer2026!`).
2. En **"Expedientes"** Pedro **solo ve "Cobro de Pesos"**, el caso de divorcio queda oculto (RBAC del backend, no del frontend).
3. Creá una **tarea urgente** asignada a Pedro con vencimiento hoy → aparece en el dashboard de Pedro pero **no** en el del admin para el otro expediente.

---

## Paso 5 — Verificar restricciones del Asistente (Ana)

1. Cerrá sesión e ingresá como **Ana** (`ana@estudio.com` / `AnaAssistant2026!`).
2. **Lectura global**: Ana ve los dos expedientes (los asistentes necesitan visibilidad total).
3. **Sin botón de borrado**: la UI esconde el botón, y si se llama al endpoint directo con su token el backend devuelve `403 Forbidden`.

---

## Paso 6 — Inmutabilidad del historial

1. Como Pedro, abrí *Cobro de Pesos* y registrá una nueva **gestión**: tipo Audiencia, 45 minutos, detalle "Audiencia de mediación inicial".
2. La gestión se suma al timeline cronológicamente.
3. **Validación**: no existe botón de editar/eliminar para esa interacción. Tampoco existen los endpoints `PUT /api/interactions/{id}` ni `DELETE /api/interactions/{id}` — los tests del repo lo verifican leyendo la tabla de rutas de FastAPI.

---

## Paso 7 — Asistente IA flotante

Visible en todas las rutas (esquina inferior derecha, burbuja con destellos):

1. Hacé click → se abre un panel de chat conectado a `/api/ai/assistant`.
2. Probá una consulta general: *"redactame un mail formal de seguimiento a un cliente que no responde hace 10 días"*.
3. La respuesta aparece **en streaming** (palabra por palabra).

> Es el mismo modelo que el resto, sin contexto del expediente. Útil para tareas generales del estudio.

---

## Paso 8 — Resumen y chat con contexto del caso

Dentro del expediente *Cobro de Pesos*, debajo de la cabecera vas a ver el **"Asistente IA del expediente"**:

1. **Resumir caso** → llama a `POST /api/ai/cases/{id}/summary`. Devuelve un resumen ejecutivo de hasta 8 viñetas usando todas las interacciones registradas + tareas abiertas como contexto.
2. **Hablar sobre el caso** → abre un panel deslizante con chat conectado a `POST /api/ai/cases/{id}/chat` con SSE. El modelo conoce los datos del expediente, así que se le puede preguntar *"¿cuál es la siguiente gestión pendiente?"* o *"¿qué argumentos esgrimimos hasta ahora?"* y va a responder en base al historial real.

---

## Paso 9 — Redacción asistida + export a Word/PDF

En la misma vista del expediente, debajo del asistente IA está la sección **"Documentos redactados"**:

1. Click **"Nueva redacción"** → modal con 3 pasos.
2. **Paso 1**: elegí un template (por ejemplo *Carta documento*).
3. **Paso 2**: completá las variables (destinatario, motivo, exigencia, apercibimiento).
4. **Paso 3**: la IA empieza a redactar **en streaming**. Cuando termina mostrás *"Guardar documento"*.
5. El documento queda persistido en la sección. Desde ahí:
   - **Ver** (icono ojo) — abrís el contenido completo.
   - **Descargar Word** (icono `.docx`) — descarga inmediata, mantiene headings y negritas.
   - **Descargar PDF** (icono `.pdf`) — A4 con márgenes de 2.5 cm, listo para presentar.
   - **Archivar** (icono basurero) — soft delete, queda registrado pero oculto.

---

## Paso 10 — Crear templates personalizados (solo admin)

Como administrador, en el sidebar:

1. **"Templates de IA"** → catálogo de templates.
2. Los del sistema están marcados con candado "Sistema" — solo lectura.
3. **"Nuevo template"** → modal con:
   - Clave única (`demanda_laboral`), nombre visible, descripción.
   - **Instrucción para la IA** (textarea grande) — *"Redactá una demanda laboral por despido. Estructura: SUMA, hechos, derecho, petitorio…"*.
   - **Variables del template** — botón "Agregar variable" para cada campo que querés que el abogado complete (clave, etiqueta, tipo: texto/textarea/monto/fecha, obligatorio).
4. Guardás → el template ya aparece en el picker que ven los abogados cuando entran a un expediente.

> Built-in nunca puede ser sobrescrito por un custom con la misma clave (el backend devuelve 409).

---

## Paso 11 — Cambiar de proveedor de IA

Para validar la portabilidad multi-proveedor:

1. Detené la app: `docker compose down`.
2. Editá `.env`:
   ```env
   AI_PROVIDER=openai
   AI_MODEL_DEFAULT=gpt-4o-mini
   OPENAI_API_KEY=sk-...
   ```
3. Volvé a levantar: `docker compose up -d`.
4. Recargá el navegador y repetí el Paso 9: la app responde igual, ahora con GPT.

> Esto demuestra que el cliente puede usar la suscripción que ya tiene. La misma operación funciona con Gemini (`AI_PROVIDER=gemini`, `GEMINI_API_KEY=...`).

---

## Validación rápida del backend (opcional)

Sin levantar Docker:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate    # Windows
# source .venv/bin/activate    # Linux/Mac
pip install -r requirements-dev.txt
pytest -q
```

Salida esperada: **31 passed**.

---

## Tabla resumen de los flujos visibles

| Quién | Qué ve | Qué no puede |
| :--- | :--- | :--- |
| **Admin** | Todos los expedientes, todo el personal, **catálogo de templates** | — |
| **Lawyer** | Solo sus expedientes / tareas, asistente IA, redacción de documentos | Ver casos de otros abogados |
| **Assistant** | Todos los expedientes (lectura), asistente IA | Eliminar nada |

Si alguno de estos pasos falla, primero `docker compose logs -f backend` y `docker compose logs -f frontend` para ver qué se queja.

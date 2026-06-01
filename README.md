# CRM Lex Studio — Sistema de Gestión para Estudios Jurídicos

**Lex Studio** es una plataforma web Full-Stack, segura y dockerizada, diseñada específicamente para optimizar la gestión operativa de estudios de abogados pequeños y medianos (2 a 20 letrados). 

Este MVP (Mínimo Producto Viable) incluye una arquitectura robusta y modular lista para producción, garantizando la inmutabilidad de los registros, aislamiento de datos por rol y total protección de la información de sus clientes.

---

## 🛠️ Stack Tecnológico

| Capa | Tecnología | Descripción |
| :--- | :--- | :--- |
| **Backend** | Python 3.11, **FastAPI** | REST API asíncrona, robusta y veloz. |
| **BBDD** | **PostgreSQL 15** | Base de datos relacional robusta. |
| **Migraciones**| **Alembic** | Control y versionamiento de base de datos. |
| **Frontend** | **React 18** (Vite) | Interfaz fluida, moderna e interactiva SPA. |
| **Estilos** | **Tailwind CSS 3** | Diseño premium con paleta legal navy & gold. |
| **Query State**| **TanStack React Query v5** | Gestión y caché asíncrona en el frontend. |
| **Proxy / Web** | **Nginx** | Reverse proxy con estrictas cabeceras de seguridad. |
| **Contenedores**| **Docker & Docker Compose**| Despliegue unificado con un solo comando. |
| **CI / CD**     | **GitHub Actions**          | Pipeline automatizado de pruebas y compilación. |

---

## 🔒 Características Clave de Seguridad

* **Inmutabilidad del Historial (Interacciones)**: Requisito legal obligatorio. No existen endpoints para editar o eliminar las interacciones registradas.
* **Seguridad de Contraseñas**: Encriptación hash robusta mediante `bcrypt` (cost factor $\ge 12$).
* **Sesiones Seguras (JWT)**: Autenticación por Tokens de Acceso de corta duración (60 min) y Tokens de Refresco persistidos en BBDD como hash SHA-256 con rotación automática (Token Rotation).
* **Cabeceras de Seguridad HTTP**: Nginx implementa cabeceras estrictas (`CSP`, `HSTS`, `X-Frame-Options`, `X-Content-Type-Options`).
* **Rate Limiting & Lockout**: El endpoint de login limita a un máximo de 5 intentos por IP cada 15 minutos, y bloquea temporalmente la cuenta de correo tras 10 intentos fallidos consecutivos.
* **Aislamiento por Roles**:
  * **Admin**: Acceso absoluto y administración de abogados y personal.
  * **Lawyer (Abogado)**: Solo visualiza, crea e interactúa con expedientes y tareas que tiene **directamente asignados**.
  * **Assistant (Asistente)**: Visualiza la totalidad de los datos del estudio (Dashboard global), pero está estrictamente bloqueado (`403 Forbidden`) para eliminar cualquier recurso.

---

## 🚀 Guía de Arranque Rápido

Siga estos pasos sencillos para levantar el sistema localmente en segundos:

### 1. Clonar y Configurar el Entorno
Copie el archivo de ejemplo de variables de entorno y personalice los valores (especialmente contraseñas y claves JWT):

```bash
cd crm-lawfirm
cp .env.example .env
```

### 2. Iniciar la Orquestación Docker
Compile y ejecute los contenedores en segundo plano:

```bash
docker compose up --build -d
```
*Este comando descarga PostgreSQL, compila el backend FastAPI, procesa la SPA de React y monta el servidor Nginx en el puerto 80.*

### 3. Correr las Migraciones de Base de Datos
Ejecute Alembic dentro del contenedor del backend para crear el esquema de tablas en PostgreSQL:

```bash
docker compose exec backend alembic upgrade head
```

### 4. Crear el Usuario Administrador Inicial
Corra el script de siembra para generar el primer usuario usando las credenciales declaradas en su archivo `.env` (`FIRST_ADMIN_EMAIL` y `FIRST_ADMIN_PASSWORD`):

```bash
docker compose exec backend python seed_admin.py
```

### 5. ¡Listo para Usar!
Abra su navegador e ingrese a:
👉 **[http://localhost](http://localhost)**

---

## 📂 Estructura de Directorios

```
crm-lawfirm/
├── docker-compose.yml          # Orquestador multi-contenedor
├── .env.example                # Plantilla de variables de entorno
├── nginx/
│   └── nginx.conf              # Proxy Nginx con seguridad HTTP
├── backend/
│   ├── Dockerfile              # Construcción multi-stage de Python
│   ├── requirements.txt        # Dependencias de paquetes backend
│   ├── alembic.ini             # Configuración de migraciones
│   ├── alembic/                # Historial de versiones SQL
│   ├── seed_admin.py           # Script CLI de siembra inicial
│   └── app/
│       ├── main.py             # Registro de rutas y Dashboard stats
│       ├── config.py           # Validación Pydantic Settings
│       ├── database.py         # Configuración del motor asíncrono
│       ├── models/             # Esquemas de tablas de base de datos
│       ├── schemas/            # Validación de datos de entrada/salida
│       ├── routers/            # Controladores REST API por entidad
│       ├── services/           # Lógica de encriptación y correos
│       └── middleware/         # Validadores de autenticación y rol
└── frontend/
    ├── Dockerfile              # Servidor de desarrollo node
    ├── package.json            # Librerías y compilador Vite
    ├── tailwind.config.js      # Paleta de colores Premium navy/gold
    └── src/
        ├── main.jsx            # Punto de montaje de React
        ├── App.jsx             # Ruteador principal y query clients
        ├── api/
        │   └── axiosClient.js  # Cliente HTTP con auto-refresco 401
        ├── context/
        │   └── AuthContext.jsx # Proveedor de sesión y login/logout
        ├── hooks/
        │   └── useAuth.js      # Hook ágil para usar contexto
        ├── components/         # Reutilizables premium (Tablas, Modales)
        └── pages/              # Vistas completas de flujos procesales
```

---

## 📧 Recuperación de Contraseñas en Desarrollo
Si el servidor SMTP se deja vacío en su archivo `.env` para pruebas locales, el sistema cuenta con un fallback de desarrollo inteligente: los enlaces de recuperación de contraseña con tokens firmados se imprimen directamente en la consola de logs del backend. 

Para visualizarlos en tiempo real, simplemente ejecute:
```bash
docker compose logs -f backend
```

---

## 🧪 Integración Continua (CI) y Pruebas Automatizadas

El proyecto cuenta con una canalización de **Integración Continua (CI)** totalmente automatizada configurada con **GitHub Actions** en `.github/workflows/ci.yml`.

### Flujo de Trabajo en la Nube
Cada vez que realizas un `push` o abres un `pull request` en la rama `main`, GitHub Actions ejecuta automáticamente:
1.  **Backend (Python 3.10)**: Levanta una base de datos PostgreSQL 15 temporal y aislada, instala las dependencias de desarrollo (`requirements-dev.txt`) y ejecuta la suite de pruebas unitarias (`pytest`) con reportes de cobertura de código.
2.  **Frontend (React/Vite)**: Instala las dependencias y compila la aplicación (`npm run build`) para asegurar que no haya errores de tipo ni de importación en la vista de producción.

### Ejecutar Pruebas Locales (Backend)
Si quieres correr los tests automatizados localmente en tu entorno de desarrollo, sigue estos pasos:
1. Asegúrate de tener un entorno virtual de Python activo e instala las dependencias de desarrollo:
   ```bash
   cd backend
   pip install -r requirements-dev.txt
   ```
2. Ejecuta los tests indicando variables ficticias para evitar fallos de configuración de entorno:
   ```bash
   DATABASE_URL=sqlite+aiosqlite:///:memory: SECRET_KEY=testkey PYTHONPATH=. pytest
   ```

### ⚙️ Rate Limiting en Desarrollo
Por defecto, el endpoint de inicio de sesión tiene un límite de intentos estricto de seguridad. En desarrollo local o pruebas de integración, este límite puede provocar bloqueos temporales (error `429 Too Many Requests`). 

Puedes desactivar fácilmente el limitador local agregando `ENABLE_RATE_LIMITER=False` en tu archivo `.env`. En producción, esta variable se mantendrá en `True` de forma automática para proteger el sistema.

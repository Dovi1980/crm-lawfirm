#!/usr/bin/env bash
# One-command setup for Lex Studio CRM.
# Usage: ./setup.sh [dev|prod]   (default: dev)
set -euo pipefail

MODE="${1:-dev}"

if [[ "$MODE" != "dev" && "$MODE" != "prod" ]]; then
  echo "Modo desconocido: $MODE  (usar dev o prod)"
  exit 1
fi

COMPOSE_FILE="docker-compose.yml"
[[ "$MODE" == "prod" ]] && COMPOSE_FILE="docker-compose.prod.yml"

echo "==> Lex Studio CRM setup ($MODE)"

# 1. .env
if [[ ! -f .env ]]; then
  if [[ -f .env.example ]]; then
    cp .env.example .env
    echo "    .env creado desde .env.example."
    echo "    EDITAR LAS CREDENCIALES ANTES DE PRODUCCIÓN:"
    echo "      - SECRET_KEY"
    echo "      - POSTGRES_PASSWORD"
    echo "      - FIRST_ADMIN_PASSWORD"
    echo "      - COOKIE_SECURE=True (en prod con HTTPS)"
  else
    echo "    ERROR: no existe .env ni .env.example"
    exit 1
  fi
fi

# 2. Docker
if ! command -v docker >/dev/null 2>&1; then
  echo "    ERROR: docker no está instalado"
  exit 1
fi

DC="docker compose"
if ! $DC version >/dev/null 2>&1; then
  DC="docker-compose"
fi

echo "==> Construyendo y levantando servicios ($COMPOSE_FILE)..."
$DC -f "$COMPOSE_FILE" up -d --build

# 3. Esperar a Postgres
echo "==> Esperando a que Postgres acepte conexiones..."
for i in {1..30}; do
  if $DC -f "$COMPOSE_FILE" exec -T db pg_isready -U "${POSTGRES_USER:-postgres}" >/dev/null 2>&1; then
    echo "    Postgres OK"
    break
  fi
  sleep 2
done

# 4. Migraciones
echo "==> Aplicando migraciones (alembic upgrade head)..."
$DC -f "$COMPOSE_FILE" exec -T backend alembic upgrade head

# 5. Seed admin
echo "==> Seeding usuario administrador..."
$DC -f "$COMPOSE_FILE" exec -T backend python seed_admin.py

# 6. URLs
echo ""
echo "============================================="
echo "  Lex Studio CRM listo."
if [[ "$MODE" == "dev" ]]; then
  echo "  Frontend (Vite dev): http://localhost:5173"
  echo "  Nginx (reverse proxy): http://localhost"
else
  echo "  App: http://localhost"
fi
echo "  API docs:  http://localhost/api/docs"
echo "  Admin:     ver FIRST_ADMIN_EMAIL en .env"
echo "============================================="

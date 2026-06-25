# One-command setup for Lex Studio CRM.
# Usage:   .\setup.ps1 [-Mode dev|prod]     (default: dev)
param(
    [ValidateSet("dev", "prod")]
    [string]$Mode = "dev"
)

$ErrorActionPreference = "Stop"

$ComposeFile = if ($Mode -eq "prod") { "docker-compose.prod.yml" } else { "docker-compose.yml" }

Write-Host "==> Lex Studio CRM setup ($Mode)" -ForegroundColor Cyan

# 1. .env
if (-not (Test-Path ".env")) {
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Host "    .env creado desde .env.example." -ForegroundColor Yellow
        Write-Host "    EDITAR LAS CREDENCIALES ANTES DE PRODUCCIÓN:" -ForegroundColor Yellow
        Write-Host "      - SECRET_KEY"
        Write-Host "      - POSTGRES_PASSWORD"
        Write-Host "      - FIRST_ADMIN_PASSWORD"
        Write-Host "      - COOKIE_SECURE=True (en prod con HTTPS)"
    } else {
        Write-Host "    ERROR: no existe .env ni .env.example" -ForegroundColor Red
        exit 1
    }
}

# 2. Docker
$dockerExists = Get-Command docker -ErrorAction SilentlyContinue
if (-not $dockerExists) {
    Write-Host "    ERROR: docker no está instalado o no está en el PATH" -ForegroundColor Red
    exit 1
}

# Detect compose v2 vs v1
$DC = "docker compose"
try {
    & docker compose version | Out-Null
} catch {
    $DC = "docker-compose"
}

Write-Host "==> Construyendo y levantando servicios ($ComposeFile)..." -ForegroundColor Cyan
Invoke-Expression "$DC -f $ComposeFile up -d --build"

# 3. Esperar a Postgres
Write-Host "==> Esperando a que Postgres acepte conexiones..." -ForegroundColor Cyan
for ($i = 1; $i -le 30; $i++) {
    try {
        $output = Invoke-Expression "$DC -f $ComposeFile exec -T db pg_isready -U postgres" 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "    Postgres OK" -ForegroundColor Green
            break
        }
    } catch {}
    Start-Sleep -Seconds 2
}

# 4. Migraciones
Write-Host "==> Aplicando migraciones (alembic upgrade head)..." -ForegroundColor Cyan
Invoke-Expression "$DC -f $ComposeFile exec -T backend alembic upgrade head"

# 5. Seed admin
Write-Host "==> Seeding usuario administrador..." -ForegroundColor Cyan
Invoke-Expression "$DC -f $ComposeFile exec -T backend python seed_admin.py"

# 6. URLs
Write-Host ""
Write-Host "=============================================" -ForegroundColor Green
Write-Host "  Lex Studio CRM listo." -ForegroundColor Green
if ($Mode -eq "dev") {
    Write-Host "  Frontend (Vite dev): http://localhost:5173"
    Write-Host "  Nginx (reverse proxy): http://localhost"
} else {
    Write-Host "  App: http://localhost"
}
Write-Host "  API docs:  http://localhost/api/docs"
Write-Host "  Admin:     ver FIRST_ADMIN_EMAIL en .env"
Write-Host "=============================================" -ForegroundColor Green

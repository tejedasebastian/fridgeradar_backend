# FridgeRadar - Backend

API REST en **FastAPI + SQLAlchemy 2 + PostgreSQL**, con migraciones Alembic y un scheduler en background para alertas de caducidad.

- App: `app/main.py` (puerto `8000` por defecto)
- Documentacion interactiva: <http://localhost:8000/docs>
- Healthcheck: <http://localhost:8000/api/health>

## Estado del proyecto

Este repositorio es un **fork huerfano**: el upstream original ya no existe (la URL devuelve 404), asi que no hay remoto de sincronizacion ni un lugar canonico para reportar issues. El desarrollo continua aqui de forma independiente.

- Alcance actual: MVP funcional para uso local / demo. No hay entorno de produccion ni deploy automatizado.
- El CI valida instalacion de dependencias y `pytest` contra PostgreSQL 16.
- La app **no arranca sin `DATABASE_URL` ni `JWT_SECRET`**; no hay credenciales por defecto.

## Requisitos

- Python 3.11+ (el CI usa 3.12)
- PostgreSQL 14+ (el CI usa 16) con una base para desarrollo y otra para tests
- No hace falta Docker para desarrollo local, pero el CI levanta `postgres:16` como service container

## Setup

```powershell
# 1. Crear las bases (solo la primera vez)
psql -U postgres -c "CREATE DATABASE fridge_inventory;"
psql -U postgres -c "CREATE DATABASE fridge_inventory_test;"

# 2. Entorno virtual + dependencias
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt

# 3. Variables de entorno
Copy-Item .env.example .env
# Editar .env: DATABASE_URL, JWT_SECRET y (opcional) GEMINI_API_KEY
```

Equivalentes en bash:

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Variables de entorno

| Variable | Obligatoria | Descripcion |
|---|---|---|
| `DATABASE_URL` | si | DSN de PostgreSQL, p. ej. `postgresql+psycopg://USER:PASSWORD@localhost:5432/fridge_inventory`. Sin default. |
| `JWT_SECRET` | si | Secreto aleatorio de >= 32 caracteres para firmar JWT. Sin default. |
| `TEST_DATABASE_URL` | no | DSN de la base de tests. Si falta, `pytest` usa `DATABASE_URL`. |
| `CORS_ORIGINS` | no | Origenes permitidos, separados por coma. Default: `http://localhost:3000,http://localhost:3001,http://127.0.0.1:3000,http://127.0.0.1:3001`. |
| `ENVIRONMENT` | no | `local` / `staging` / `production` (solo informativo). |
| `GEMINI_API_KEY` | no | Habilita el chat IA en `/api/ai/chat`. Sin ella, ese endpoint responde 501 y el resto funciona. |
| `RATE_LIMIT_ENABLED` | no | `true` / `false` (los tests lo fuerzan a `false`). |
| `ENABLE_SCHEDULER` | no | `true` / `false`. Enciende el escaneo periodico de caducidades. |
| `SCAN_INTERVAL_MINUTES` | no | Cada cuantos minutos corre el scan (default `60`). |

Genera un secreto con:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

`.env` esta en `.gitignore`. Nunca commitees valores reales; `.env.example` solo contiene placeholders vacios.

### CORS

`CORS_ORIGINS` acepta una lista separada por coma. En produccion configura solo los origenes reales del frontend:

```env
CORS_ORIGINS=https://app.example.com
```

Si se usa `*`, el middleware desactiva `allow_credentials` (combinacion invalida segun la spec de CORS).

## Esquema y datos de prueba

Recomendado: `reset_db.py` (esquema + seed consistente para inventario, alertas y recetas):

```powershell
python scripts/reset_db.py
```

> **Advertencia:** el script borra y recrea todas las tablas. No lo ejecutes contra una base con datos que quieras conservar ni en produccion.

Crea usuarios de demo **ficticios** con password `demo1234`:

- `demo@example.com`
- `alice@example.com`
- `bob@example.com`

> Los correos, nombres y contrasenas son placeholders inventados para desarrollo. No corresponden a personas reales.

Alternativa solo-esquema con Alembic:

```powershell
alembic upgrade head
```

Verificacion rapida:

```powershell
python scripts/verify_db.py    # debe terminar con "Overall: PASS"
```

## Levantar el servidor

```powershell
uvicorn app.main:app --reload --port 8000
```

Al arrancar, `app.workers.scheduler` levanta APScheduler y escanea el inventario cada `SCAN_INTERVAL_MINUTES` para generar alertas. Para apagarlo en dev: `ENABLE_SCHEDULER=false`.

## Tests y CI

```powershell
$env:DATABASE_URL="postgresql+psycopg://USER:PASSWORD@localhost:5432/fridge_inventory_test"
$env:JWT_SECRET="un-secreto-solo-para-tests-de-32-o-mas-caracteres"
pytest -q
```

`tests/conftest.py`:

- Lee `TEST_DATABASE_URL`; si no existe, usa `DATABASE_URL`.
- Crea la base de tests si no existe (conectando a la base `postgres`).
- Fuerza `RATE_LIMIT_ENABLED=false`, `ENABLE_SCHEDULER=false` y `GEMINI_API_KEY=""`.
- Exige un `JWT_SECRET` valido (usa uno de test si el entorno no lo define).

El workflow [`.github/workflows/ci.yml`](.github/workflows/ci.yml) corre en cada push y pull request a `main` con un service container `postgres:16`, instala `requirements.txt` y ejecuta `pytest`.

## Estructura

```
fridgeradar_backend/
??? app/
?   ??? main.py            # FastAPI app + CORS + lifespan (scheduler)
?   ??? core/              # config, db, security, rate-limit, dependencies
?   ??? models/            # SQLAlchemy
?   ??? schemas/           # Pydantic
?   ??? repositories/      # acceso a datos
?   ??? services/          # logica de negocio
?   ??? routers/           # endpoints (auth, household, inventory, ...)
?   ??? workers/           # APScheduler (alertas de caducidad)
??? alembic/               # migraciones
??? scripts/               # reset_db, verify_db, inspect_db
??? tests/                 # pytest
??? requirements.txt
??? alembic.ini
??? .env.example
```

## Endpoints principales

Prefijo comun: `/api`. Algunos routers:

- `auth` - login, refresh, logout, registro
- `household`, `invitation` - hogares compartidos
- `refrigerator`, `zone` - frigorificos y zonas
- `inventory` - items
- `expiry`, `alert` - caducidades y alertas
- `shopping` - lista de la compra
- `recipes` - recetas
- `activity` - bitacora
- `ai` - chat con Gemini (requiere `GEMINI_API_KEY`)

La lista exacta y los schemas viven en Swagger: <http://localhost:8000/docs>.

## Scripts de mantenimiento

- `scripts/reset_db.py`: borra y siembra la base de desarrollo (destructivo).
- `scripts/verify_db.py`: comprueba integridad y datos esperados.
- `scripts/inspect_db.py`: inspeccion de solo lectura.
- `scripts/migrate_legacy_DO_NOT_RUN.py`: obsoleto, se conserva solo como referencia historica.

No hay scripts que reasignen contrasenas masivamente. Si necesitas rotar una password, hazlo por usuario desde la API o con una herramienta externa.

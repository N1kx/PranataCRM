# Pranata CRM

A modular-monolith CRM built with FastAPI (backend) and Nuxt 4 (frontend) in a single repository.

## Repository Layout

```text
pranata-crm/
├── backend/       ← FastAPI + SQLAlchemy async
│   ├── app/       ← Application source
│   ├── alembic/   ← Database migrations
│   ├── tests/     ← Unit tests
│   ├── Dockerfile
│   ├── entrypoint.sh
│   ├── requirements.txt
│   └── run.py     ← Windows-compatible server entrypoint
├── design/        ← Architectural decision records (ADR-001, ADR-002, ...)
├── docker-compose.yml
├── nginx/         ← Reverse proxy config for the `gateway` service
│   └── nginx.conf
├── postman/       ← Postman collection + environment for exercising the API
└── frontend/      ← Nuxt 4 + Nuxt UI + Pinia + i18n
    ├── app/       ← Pages, components, composables, stores, layouts
    ├── i18n/      ← Locale files (id / en)
    ├── public/    ← Static assets (favicon, robots.txt)
    └── Dockerfile
```

## Backend Stack

| Area       | Choice                                                    |
| ---------- | --------------------------------------------------------- |
| Framework  | FastAPI + Uvicorn                                         |
| ORM        | SQLAlchemy async + asyncpg                                |
| Migrations | Alembic (auto-run on startup)                             |
| Database   | PostgreSQL 15 + pgvector                                  |
| Cache      | Redis 7                                                   |
| Queue      | RabbitMQ 3.13                                             |
| Worker     | Celery + Celery Beat                                      |
| Auth       | JWT (PyJWT) + httpOnly cookie + refresh token rotation    |
| Password   | passlib + bcrypt                                          |
| Email      | Resend / SMTP                                             |
| AI         | LiteLLM (Ollama dev / Groq prod / OpenRouter fallback)    |

## Frontend Stack

| Area       | Choice                                  |
| ---------- | --------------------------------------- |
| Framework  | Nuxt 4 (Vue 3, SSR + SPA for `/app/**`) |
| UI         | Nuxt UI + Tailwind CSS                  |
| State      | Pinia                                   |
| i18n       | @nuxtjs/i18n (Indonesia / English)      |
| Validation | Zod                                     |
| Auth       | httpOnly cookies (no token in JS)       |

---

## Running with Docker (Recommended)

`docker-compose.yml` spins up the full stack: PostgreSQL, Redis, RabbitMQ, the API, the
frontend, and an **nginx gateway** that puts both behind a single origin. Database migrations
run automatically on API startup via `entrypoint.sh`.

### 1. Start everything

```bash
docker compose up -d --build
```

### 2. Verify all services are healthy

```bash
docker compose ps
```

Expected output:

```text
NAME               STATUS
pranata_api        Up (healthy)
pranata_db         Up (healthy)
pranata_gateway    Up
pranata_redis      Up (healthy)
pranata_rabbitmq   Up (healthy)
pranata_web        Up
```

### 3. Health check

```bash
curl http://localhost:8230/health
```

```json
{ "status": "ok", "redis": true, "db": true }
```

> The API is exposed directly on port **8230** (mapped from container port 8000) for
> debugging. Normal usage goes through the gateway instead (see below).

### 4. Open the app

```text
http://localhost:8080
```

The **gateway** (nginx) is the single entrypoint: `/` proxies to the frontend, `/api/v1/`
proxies to the API — same origin, so the browser never makes a cross-origin request between
them. (`/api/v1/` specifically, not the broader `/api/` — Nuxt's own server reserves `/api/`
for internal routes such as icon serving.) The `web` service is still built with the production `.output` bundle
(`docker compose up --build` is required after a frontend code change); only the **API**
container is wired for live editing (see below). Direct access to `pranata_web` on
**:3000** and `pranata_api` on **:8230** remains available for debugging either service in
isolation.

### 5. Editing backend code

The `api` service bind-mounts `./backend` into the container and runs `uvicorn --reload`, so
changes to backend source apply immediately — no rebuild needed. Only changes to
`requirements.txt` require `docker compose up -d --build api`.

### 6. Stop

```bash
docker compose down
```

---

## Running Locally on Windows (Dev)

Infra (DB, Redis, RabbitMQ) runs in Docker; the FastAPI app runs directly on Windows.

### 1. Start infra only

```bash
docker compose up -d db redis rabbitmq
```

### 2. Create virtualenv and install dependencies

```powershell
cd backend
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 3. Set environment variables

```powershell
$env:DATABASE_URL   = "postgresql+asyncpg://postgres:postgres@localhost:5432/pranata_crm"
$env:REDIS_URL      = "redis://127.0.0.1:6379/0"
$env:RABBITMQ_URL   = "amqp://guest:guest@localhost:5672//"
$env:JWT_SECRET_KEY = "dev-secret-change-in-production"
$env:APP_ENV        = "development"
```

### 4. Run migrations

```powershell
.venv\Scripts\python.exe -m alembic upgrade head
```

### 5. Start the API

```powershell
.venv\Scripts\python.exe run.py
```

API available at <http://localhost:8000>

---

## Running the Frontend

The frontend is a Nuxt 4 app. For day-to-day development run it locally (fast HMR);
use Docker only for demos / sharing with others.

### Option A — Local dev (recommended)

Make sure the backend + infra are already running (see sections above).

```bash
cd frontend
npm install      # first time only
npm run dev
```

App available at <http://localhost:3000> (Nuxt picks the next free port if 3000 is taken).

- Login: <http://localhost:3000/login>
- Register: <http://localhost:3000/register>

The dev server talks to the backend at `http://localhost:8230/api/v1`. Override with an
`.env` file in `frontend/` if needed:

```dotenv
NUXT_PUBLIC_API_BASE=http://localhost:8230/api/v1
NUXT_PUBLIC_APP_ENV=development
```

> In development the workspace tenant is resolved from the **workspace address** field
> on the login form (sent as the `X-Tenant-Slug` header). In production it comes from the
> subdomain (`acme.pranata.app`).

### Option B — Full stack via Docker (demo)

`docker-compose.yml` includes a `web` service that builds and serves the frontend, plus a
`gateway` (nginx) service in front of it. See [Running with Docker](#running-with-docker-recommended)
above — the short version:

```bash
docker compose up --build
```

This brings up everything (db, redis, rabbitmq, api, web, gateway). Open
<http://localhost:8080> (the gateway — same origin as the API, so no CORS setup is needed).

To point the build at a remote backend instead of the bundled `api` service (e.g. a demo
server), pass an absolute API base at build time and skip the gateway:

```bash
docker compose build --build-arg NUXT_PUBLIC_API_BASE=http://your-server:8230/api/v1 web
docker compose up web
```

### Language

The UI ships in **Indonesia** and **English**. Switch via the language dropdown in the
top-right corner of the auth pages. The choice is persisted in a cookie.

---

## API Reference

The full API — Auth, Users, Contacts, and Companies — is documented as a Postman collection
(see below) rather than in this file, so request/response shapes never drift out of sync with
the code. A couple of conventions apply across every endpoint:

- Base URL: `/api/v1`.
- All error responses follow the same shape:
  `{ "error": { "code": "ERROR_CODE", "message": "...", "detail": null } }`.
- Everything except `/auth/register-tenant` and `/auth/login` requires the `access_token`
  httpOnly cookie set by `/auth/login`, and is scoped to the caller's tenant — a record
  belonging to another tenant looks like `404`, never `403`.

## Testing the API with Postman

A ready-to-import Postman collection lives in [`postman/`](postman/):

- `PranataCRM.postman_collection.json` — every endpoint, organized into
  Auth / Users / Contacts / Companies / Cleanup & Extras folders.
- `PranataCRM.postman_environment.json` — the `PranataCRM Local` environment.

Auth cookies, the dev-mode `X-Tenant-Slug` header, and IDs produced along the way
(`tenant_id`, `user_id`, `contact_id`, `company_id`) are captured and re-injected automatically
by the collection's scripts — no manual copy-pasting of tokens or headers. See
[`postman/README.md`](postman/README.md) for the full run order and how to run it headlessly
via Newman.

---

## Architecture

The backend follows a **modular monolith** pattern:

```text
router → use_case (implements Protocol) → service (internal) → repository → model
```

- **`router.py`** — HTTP adapter only. Calls its own module's `use_case`, never a `service` or
  `repository` directly, and contains no business logic.
- **`use_case.py`** — the module's sole entry point from the outside world (its own router, or
  another module). It's the only class that implements that module's `*ContractProtocol` from
  `shared/contracts/`. If it needs another module's capability, it depends on that module's
  Protocol (injected via constructor), never the concrete class.
- **`service.py`** — internal domain logic. Never imported or called from outside its own module,
  and knows nothing about other modules.
- Contracts (`typing.Protocol`) are defined per-module in `shared/contracts/`, but only for the
  capabilities another module actually consumes (e.g. `CompanyContractProtocol.company_exists`,
  used by `contacts` to validate `company_id`) — not speculatively for every module.
- All use_case wiring (concrete class → Protocol) happens in `app/container.py`, via FastAPI
  `Depends()` provider functions — routers never construct a service/repository themselves.
- No foreign keys in the DB — soft UUID references, manual indexes.
- UUID v7 (time-ordered) generated in the application layer.
- Row Level Security (RLS) enabled on all tenant-scoped tables.

See [design/](design/) for the full set of architectural decision records (ADRs), including
[ADR-007](design/ADR-007-modular-monolith-usecase-contract.md) for the rationale behind this
layering.

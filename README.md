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
├── docker-compose.yml
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

`docker-compose.yml` spins up the full stack: PostgreSQL, Redis, RabbitMQ, and the API.
Database migrations run automatically on API startup via `entrypoint.sh`.

### 1. Start everything

```bash
docker compose up -d
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
pranata_redis      Up (healthy)
pranata_rabbitmq   Up (healthy)
```

### 3. Health check

```bash
curl http://localhost:8230/health
```

```json
{ "status": "ok", "redis": true, "db": true }
```

> The API is exposed on port **8230** (mapped from container port 8000).

### 4. Stop

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

`docker-compose.yml` includes a `web` service that builds and serves the frontend.

```bash
docker compose up --build
```

This brings up everything (db, redis, rabbitmq, api, web). Open <http://localhost:3000>.

To point the build at a remote backend (e.g. demo server), pass the API base at build time:

```bash
docker compose build --build-arg NUXT_PUBLIC_API_BASE=http://your-server:8230/api/v1 web
docker compose up
```

### Language

The UI ships in **Indonesia** and **English**. Switch via the language dropdown in the
top-right corner of the auth pages. The choice is persisted in a cookie.

---

## Auth API Endpoints

Base URL: `/api/v1`

All error responses follow this shape:

```json
{ "error": { "code": "ERROR_CODE", "message": "Human-readable message.", "detail": null } }
```

---

### POST /auth/register-tenant

Create a new tenant (organization) and its owner account. No authentication required.

Request body:

```json
{
  "full_name": "Niko Winoko",
  "email": "niko@nxcorp.co",
  "password": "secret123",
  "organization_name": "nxcorp",
  "slug": "nxcorp",
  "industry": "Technology",
  "team_size": "1-10"
}
```

Validation rules:

- `email` — valid email, normalized to lowercase
- `password` — min 8 chars, must contain at least one letter and one digit
- `slug` — lowercase, `[a-z0-9-]` only, 3–63 chars, not reserved (`www`, `api`, `app`, `admin`, `mail`, `pranata`, `static`, `assets`)

Response `201`:

```json
{
  "tenant_id": "019ef67e-272d-7084-aec7-0eb4ce43719d",
  "slug": "nxcorp",
  "user": {
    "id": "019ef67e-27e0-7174-bccb-d12bd921528e",
    "email": "niko@nxcorp.co",
    "full_name": "Niko Winoko",
    "suite_role": "tenant_owner"
  }
}
```

Error codes:

| Code              | HTTP | Meaning                 |
| ----------------- | ---- | ----------------------- |
| `AUTH_SLUG_TAKEN` | 409  | Slug already registered |

---

### POST /auth/login

Authenticate a user. Tenant is resolved from the `X-Tenant-Slug` header (development) or subdomain (production).
Sets `access_token` and `refresh_token` as **httpOnly cookies**.

Request body:

```json
{ "email": "niko@nxcorp.co", "password": "secret123" }
```

Request header:

```text
X-Tenant-Slug: nxcorp
```

Response `200`:

```json
{
  "id": "019ef67e-27e0-7174-bccb-d12bd921528e",
  "email": "niko@nxcorp.co",
  "full_name": "Niko Winoko",
  "suite_role": "tenant_owner"
}
```

Error codes:

| Code                       | HTTP | Meaning                                                                 |
| -------------------------- | ---- | ----------------------------------------------------------------------- |
| `AUTH_TENANT_NOT_FOUND`    | 404  | Subdomain / slug not found                                              |
| `AUTH_INVALID_CREDENTIALS` | 401  | Wrong email or password (same message for both — anti user-enumeration) |

---

### POST /auth/logout

Revoke the refresh token and clear auth cookies. Idempotent — safe to call without an active session.

Response `200`:

```json
{ "message": "Signed out successfully." }
```

---

### POST /auth/accept-invite

Accept an invitation sent by a tenant admin. Creates the user account and assigns the role specified in the invite.

Request body:

```json
{
  "token": "<invite-jwt>",
  "full_name": "New Member",
  "password": "secret123"
}
```

Response `201`:

```json
{
  "id": "...",
  "email": "invitee@nxcorp.co",
  "full_name": "New Member",
  "suite_role": "member"
}
```

Error codes:

| Code                  | HTTP | Meaning                                 |
| --------------------- | ---- | --------------------------------------- |
| `AUTH_INVITE_INVALID` | 400  | Token invalid, expired, or already used |
| `AUTH_EMAIL_EXISTS`   | 409  | Email already registered in this tenant |
| `AUTH_SEAT_LIMIT`     | 409  | No seats available                      |

---

### POST /users

Create a user account directly (no invite flow). Requires `tenant_owner` or `tenant_admin` role.

Request body:

```json
{
  "full_name": "Member One",
  "email": "member1@nxcorp.co",
  "password": "secret123",
  "role_id": "<uuid-of-crm-role>"
}
```

Response `201`: same shape as the user object in the login response above.

Error codes:

| Code                     | HTTP | Meaning                      |
| ------------------------ | ---- | ---------------------------- |
| `AUTH_PERMISSION_DENIED` | 403  | Caller is not owner or admin |
| `AUTH_EMAIL_EXISTS`      | 409  | Email already in this tenant |
| `AUTH_SEAT_LIMIT`        | 409  | No seats available           |

---

### POST /users/invite

Send an invitation email to a new user. Requires `tenant_owner` or `tenant_admin` role.

Request body:

```json
{
  "email": "invitee@nxcorp.co",
  "full_name": "Invited User",
  "role_id": "<uuid-of-crm-role>"
}
```

Response `200`:

```json
{ "message": "Invitation sent successfully." }
```

---

## Architecture

The backend follows a **modular monolith** pattern:

```text
router → use_case (implements Protocol) → service (internal) → repository → model
```

- Modules only communicate via `shared/contracts/` — never by direct import.
- All dependency wiring lives in `container.py`.
- No foreign keys in the DB — soft UUID references, manual indexes.
- UUID v7 (time-ordered) generated in the application layer.
- Row Level Security (RLS) enabled on all tenant-scoped tables.

See [issue.md](issue.md) for full architectural decisions (ADRs).

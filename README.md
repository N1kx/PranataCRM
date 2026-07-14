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
├── nginx/         ← Reverse proxy config for the `gateway` service
│   └── nginx.conf
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

### GET /auth/me

Return the currently authenticated user's profile, resolved from the `access_token` cookie.
Used by the frontend to restore the session after a page refresh.

Response `200`:

```json
{
  "id": "019ef67e-27e0-7174-bccb-d12bd921528e",
  "email": "niko@nxcorp.co",
  "full_name": "Niko Winoko",
  "suite_role": "tenant_owner",
  "tenant_id": "019ef67e-272d-7084-aec7-0eb4ce43719d",
  "is_active": true,
  "created_at": "2026-01-01T12:00:00Z"
}
```

Error codes:

| Code                     | HTTP | Meaning                              |
| ------------------------ | ---- | ------------------------------------ |
| `AUTH_NOT_AUTHENTICATED` | 401  | Missing, invalid, or expired session |

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

## Contacts API Endpoints

Base URL: `/api/v1`. All endpoints require authentication (`access_token` cookie) and are
scoped to the caller's tenant — a contact belonging to another tenant looks like `404`, never
`403`, so tenant existence is never leaked.

### POST /contacts

Create a contact. Only `first_name` is required.

Request body:

```json
{
  "first_name": "Ada",
  "last_name": "Lovelace",
  "email": "ada@example.com",
  "status": "lead"
}
```

Response `201`: the created contact (see field list under `GET /contacts/{id}` below).

Validation error (`422`) examples:

- `first_name` empty or over 100 characters
- `status` not one of `lead, qualified, customer, churned`
- `lifecycle_stage` not one of `subscriber, lead, mql, sql, opportunity, customer, evangelist`
- `preferred_contact_method` not one of `email, phone, sms, whatsapp`
- `owner_id` / `company_id` not a valid UUID

### GET /contacts

List the caller's tenant's contacts, paginated.

Query params: `page` (default `1`), `page_size` (default `20`, capped at `100`).

Response `200`:

```json
{
  "items": [ { "id": "...", "first_name": "Ada", "...": "..." } ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

### GET /contacts/{contact_id}

Get a single contact. Response `200` fields: `id`, `tenant_id`, `owner_id`, `company_id`,
`first_name`, `last_name`, `email`, `secondary_email`, `phone`, `mobile_phone`, `job_title`,
`department`, `status`, `lifecycle_stage`, `lead_source`, `linkedin_url`, `twitter_handle`,
`address_line1`, `city`, `state`, `postal_code`, `country`, `timezone`,
`preferred_contact_method`, `preferred_language`, `do_not_contact`, `description`, `tags`,
`custom_fields`, `created_at`, `updated_at`.

### PATCH /contacts/{contact_id}

Partial update — send only the fields you want to change.

### DELETE /contacts/{contact_id}

Response `200`:

```json
{ "message": "Contact deleted successfully." }
```

### Error codes (all Contacts endpoints)

| Code                     | HTTP | Meaning                                        |
| ------------------------ | ---- | ---------------------------------------------- |
| `AUTH_NOT_AUTHENTICATED` | 401  | Missing, invalid, or expired session           |
| `CONTACT_NOT_FOUND`      | 404  | No contact with that id in the caller's tenant |

---

## Testing the API with Postman

A ready-to-import Postman collection lives in [`postman/`](postman/):

- `PranataCRM.postman_collection.json` — every endpoint above, organized into
  Auth / Users / Contacts / Cleanup & Extras folders.
- `PranataCRM.postman_environment.json` — the `PranataCRM Local` environment.

Auth cookies, the dev-mode `X-Tenant-Slug` header, and IDs produced along the way
(`tenant_id`, `user_id`, `contact_id`) are captured and re-injected automatically by the
collection's scripts — no manual copy-pasting of tokens or headers. See
[`postman/README.md`](postman/README.md) for the full run order and how to run it headlessly
via Newman.

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

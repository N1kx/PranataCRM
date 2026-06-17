# Pranata CRM

A modular-monolith CRM built with FastAPI (backend) and Nuxt 3 (frontend) in a single repository.

## Repository Layout

```
pranata-crm/
├── backend/   ← FastAPI + SQLAlchemy async
└── frontend/  ← Nuxt 3 + Tailwind + Pinia (coming soon)
```

## Backend Stack

| Area | Choice |
|---|---|
| Framework | FastAPI + Uvicorn |
| ORM | SQLAlchemy async + asyncpg |
| Migrations | Alembic |
| Database | PostgreSQL 15 + pgvector |
| Cache | Redis |
| Queue | RabbitMQ |
| Worker | Celery + Celery Beat |
| Auth | JWT + httpOnly cookie + refresh rotation |
| Email | Resend / SMTP |
| AI | LiteLLM (Ollama dev / Groq prod / OpenRouter fallback) |

## Quick Start (Backend)

### 1. Start infrastructure

```bash
docker-compose up -d
```

This starts PostgreSQL, Redis, and RabbitMQ.

### 2. Create and activate virtual environment

```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -e ".[dev]"
```

### 4. Configure environment

```bash
cp .env.example .env
# Edit .env with your values
```

### 5. Run the API

```bash
uvicorn app.main:app --reload
```

API is available at http://localhost:8000  
Interactive docs at http://localhost:8000/docs  
Health check at http://localhost:8000/health

### 6. Run Celery worker

```bash
celery -A app.worker.celery_app worker --loglevel=info
```

### 7. Run Celery Beat (scheduled tasks)

```bash
celery -A app.worker.celery_app beat --loglevel=info
```

## Architecture

The backend follows a **modular monolith** pattern with layered architecture per module:

```
router → use_case → service → repository → model
          (impl Protocol)  (internal)   (DB)
```

Cross-module communication happens **only** via contracts defined in `shared/contracts/`.  
Dependency wiring is **only** in `container.py`.

See [issue.md](issue.md) for the full architectural decisions.

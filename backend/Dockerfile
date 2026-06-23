FROM python:3.12-slim

WORKDIR /app

# Install system deps for asyncpg + bcrypt
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies directly (no editable install needed)
COPY pyproject.toml .
RUN pip install --no-cache-dir \
    "fastapi>=0.111.0" \
    "uvicorn[standard]>=0.30.0" \
    "sqlalchemy[asyncio]>=2.0.30" \
    "asyncpg>=0.29.0" \
    "alembic>=1.13.0" \
    "pgvector>=0.3.0" \
    "pydantic[email]>=2.7.0" \
    "pydantic-settings>=2.3.0" \
    "python-dotenv>=1.0.0" \
    "passlib[bcrypt]>=1.7.4" \
    "bcrypt<4" \
    "python-multipart>=0.0.9" \
    "redis[hiredis]>=5.0.0" \
    "httpx>=0.27.0" \
    "resend>=2.0.0" \
    "aiosmtplib>=3.0.0" \
    "PyJWT>=2.8.0"

COPY . .

RUN chmod +x entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]

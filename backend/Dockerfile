FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system deps for asyncpg + bcrypt
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# requirements.txt is the pinned source of truth (kept in sync with the venv
# via `pip freeze`); install from it instead of a hand-maintained list here so
# the image never drifts from what's actually used by the code.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Baked in for a working standalone image (`docker run` without compose).
# In docker-compose, a bind mount overlays this at container start so local
# edits apply immediately without a rebuild - see docker-compose.yml.
COPY . .

RUN chmod +x entrypoint.sh

EXPOSE 8000

# Invoke via `sh` explicitly (not `./entrypoint.sh`) so a bind-mounted copy of
# this file - CRLF line endings or a lost executable bit from the host - can
# never break container startup.
ENTRYPOINT ["sh", "entrypoint.sh"]

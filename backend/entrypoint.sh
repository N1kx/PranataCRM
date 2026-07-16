#!/bin/sh
set -e

echo "Running database migrations..."
python -m alembic upgrade head

# Geo reference data (issue #26: countries/states/cities) — plain SQL, not a
# Python step, so it can be reviewed/edited without touching app code. The
# script itself is idempotent (each block skips if its table already has
# rows, INSERTs also carry ON CONFLICT DO NOTHING), so running it on every
# deploy is safe and cheap after the first time.
echo "Seeding geo reference data..."
psql "$(echo "$DATABASE_URL" | sed 's/^postgresql+asyncpg:/postgresql:/')" \
  -v ON_ERROR_STOP=1 -f db/seed/geo_reference_data.sql

echo "Starting API server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 "$@"

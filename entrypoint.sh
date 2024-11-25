#!/bin/sh
set -e

echo "Starting entrypoint script..."

cd /app

# Initialize migrations if they don't exist
if [ ! -d "/app/migrations" ] || [ ! -f "/app/migrations/alembic.ini" ]; then
    echo "Initializing migrations..."
    flask db init || sudo flask db init
fi

echo "Running database migrations..."
flask db upgrade || sudo flask db upgrade

if [ "$INIT_DB" = "true" ]; then
    echo "Initializing database with admin user..."
    flask init-db || sudo flask init-db
fi

echo "Ensuring admin user exists..."
flask ensure-admin || sudo flask ensure-admin

echo "Entrypoint script completed. Starting application..."

# Execute the main command (likely gunicorn)
exec "$@"

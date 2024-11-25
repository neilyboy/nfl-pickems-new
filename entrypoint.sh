#!/bin/sh
set -e

echo "Starting entrypoint script..."

# Change to app directory and create migrations directory
cd /app
mkdir -p /app/migrations/versions

# Initialize migrations if they don't exist
if [ ! -f /app/migrations/alembic.ini ]; then
    echo "Initializing database migrations..."
    FLASK_APP=/app/app flask db init
fi

echo "Running database migrations..."
FLASK_APP=/app/app flask db upgrade

if [ "$INIT_DB" = "true" ]; then
    echo "Initializing database with admin user..."
    FLASK_APP=/app/app flask init-db
fi

echo "Ensuring admin user exists..."
FLASK_APP=/app/app flask ensure-admin

echo "Entrypoint script completed. Starting application..."

# Execute the main command (likely gunicorn)
exec "$@"

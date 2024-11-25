#!/bin/sh
set -e

echo "Starting entrypoint script..."

cd /app

# Initialize migrations if they don't exist
if [ ! -d "/app/migrations" ] || [ ! -f "/app/migrations/alembic.ini" ]; then
    echo "Initializing migrations..."
    # Try to init migrations
    flask db init || sudo -u root flask db init
fi

echo "Running database migrations..."
flask db upgrade || sudo -u root flask db upgrade

if [ "$INIT_DB" = "true" ]; then
    echo "Initializing database with admin user..."
    flask init-db || sudo -u root flask init-db
fi

echo "Ensuring admin user exists..."
flask ensure-admin || sudo -u root flask ensure-admin

echo "Entrypoint script completed. Starting application..."

# Execute the main command (likely gunicorn)
exec "$@"

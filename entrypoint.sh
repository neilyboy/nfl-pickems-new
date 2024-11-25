#!/bin/sh
set -e

echo "Starting entrypoint script..."

cd /app

# Initialize migrations if they don't exist
if [ ! -d "/app/migrations" ] || [ ! -f "/app/migrations/alembic.ini" ]; then
    echo "Initializing migrations..."
    # Try to init migrations
    if ! flask db init; then
        echo "Failed to initialize migrations, trying as root..."
        # If it fails, try as root
        su -c "flask db init" root
    fi
fi

echo "Running database migrations..."
flask db upgrade

if [ "$INIT_DB" = "true" ]; then
    echo "Initializing database with admin user..."
    flask init-db
fi

echo "Ensuring admin user exists..."
flask ensure-admin

echo "Entrypoint script completed. Starting application..."

# Execute the main command (likely gunicorn)
exec "$@"

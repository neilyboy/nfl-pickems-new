#!/bin/sh
set -e

echo "Starting entrypoint script..."

cd /app

# Initialize migrations if they don't exist
if [ ! -d "/app/migrations" ] || [ ! -f "/app/migrations/alembic.ini" ]; then
    echo "Initializing migrations..."
    # Try to init migrations
    if ! sudo -u "$USER" flask db init; then
        echo "Failed to initialize migrations, trying as root..."
        sudo flask db init
    fi
fi

echo "Running database migrations..."
sudo -u "$USER" flask db upgrade

if [ "$INIT_DB" = "true" ]; then
    echo "Initializing database with admin user..."
    sudo -u "$USER" flask init-db
fi

echo "Ensuring admin user exists..."
sudo -u "$USER" flask ensure-admin

echo "Entrypoint script completed. Starting application..."

# Execute the main command (likely gunicorn)
exec "$@"

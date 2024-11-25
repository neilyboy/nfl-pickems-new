#!/bin/sh
set -e

echo "Starting entrypoint script..."

# Create instance directory if it doesn't exist
mkdir -p /app/instance

# Create migrations directory if it doesn't exist
mkdir -p /app/migrations/versions

# Initialize database if it doesn't exist
if [ ! -f /app/instance/app.db ]; then
    echo "Creating new database..."
    touch /app/instance/app.db
    export INIT_DB=true
fi

# Initialize migrations if they don't exist
if [ ! -f /app/migrations/alembic.ini ]; then
    echo "Initializing database migrations..."
    flask db init
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

#!/bin/sh
set -e

echo "Starting entrypoint script..."

# Create necessary directories
mkdir -p /app/instance /app/migrations
echo "Created necessary directories"

# Initialize database if it doesn't exist
if [ ! -f /app/instance/app.db ]; then
    echo "Creating new database..."
    touch /app/instance/app.db
    export INIT_DB=true
fi

# Initialize migrations if they don't exist
if [ ! -f /app/migrations/alembic.ini ]; then
    echo "Initializing database migrations..."
    cd /app && flask db init
fi

# Run database migrations
echo "Running database migrations..."
cd /app && flask db upgrade

# Initialize database if needed
if [ "$INIT_DB" = "true" ]; then
    echo "Initializing database with admin user..."
    cd /app && flask init-db
fi

# Ensure admin user exists
echo "Ensuring admin user exists..."
cd /app && flask ensure-admin

echo "Entrypoint script completed. Starting application..."

# Start the application
exec "$@"

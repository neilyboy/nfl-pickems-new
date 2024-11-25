#!/bin/sh
set -e

echo "Starting entrypoint script..."

cd /app

# Initialize database directory if it doesn't exist
mkdir -p /app/instance

echo "Setting up database and migrations..."

# Initialize migrations if they don't exist
if [ ! -d "/app/migrations" ] || [ -z "$(ls -A /app/migrations)" ]; then
    echo "Initializing migrations directory..."
    flask db init
fi

# Create and apply migrations
echo "Running database migrations..."
flask db migrate -m "Auto-migration" || echo "Migration creation failed (this is normal if no changes), continuing..."
flask db upgrade || echo "Migration upgrade failed, continuing..."

# Initialize database with admin user if needed
if [ "$INIT_DB" = "true" ]; then
    echo "Initializing database with admin user..."
    flask init-db
fi

echo "Ensuring admin user exists..."
flask ensure-admin

echo "Entrypoint script completed. Starting application..."

# Execute the main command (likely gunicorn)
exec "$@"

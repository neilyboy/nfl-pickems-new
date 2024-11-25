#!/bin/sh
set -e

echo "Starting entrypoint script..."

cd /app

echo "Setting up database..."

# Database should already exist from Dockerfile
# Just initialize if needed
if [ "$INIT_DB" = "true" ]; then
    echo "Initializing database with admin user..."
    flask init-db
fi

echo "Ensuring admin user exists..."
flask ensure-admin || echo "Admin user check failed, continuing..."

echo "Entrypoint script completed. Starting application..."

# Execute the main command (likely gunicorn)
exec "$@"

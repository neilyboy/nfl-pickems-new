#!/bin/sh
set -e

echo "Starting entrypoint script..."

cd /app

# Initialize database directory if it doesn't exist
mkdir -p /app/instance

# Create database tables first
echo "Creating database tables..."
flask db stamp head
flask db migrate
flask db upgrade

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

#!/bin/sh
set -e

echo "Starting entrypoint script..."

# Get host user UID/GID from environment, default to 1000
USER_ID=${DOCKER_UID:-1000}
GROUP_ID=${DOCKER_GID:-1000}

echo "Setting up permissions with UID: $USER_ID, GID: $GROUP_ID"

# Create necessary directories with proper permissions
mkdir -p /app/instance /app/migrations
chown -R $USER_ID:$GROUP_ID /app/instance /app/migrations

# Initialize database if it doesn't exist
if [ ! -f /app/instance/app.db ]; then
    echo "Creating new database..."
    touch /app/instance/app.db
    chown $USER_ID:$GROUP_ID /app/instance/app.db
    export INIT_DB=true
fi

# Switch to the non-root user for all Flask commands
echo "Switching to non-root user for Flask commands..."

if [ ! -f /app/migrations/alembic.ini ]; then
    echo "Initializing database migrations..."
    gosu $USER_ID:$GROUP_ID flask db init
fi

echo "Running database migrations..."
gosu $USER_ID:$GROUP_ID flask db upgrade

if [ "$INIT_DB" = "true" ]; then
    echo "Initializing database with admin user..."
    gosu $USER_ID:$GROUP_ID flask init-db
fi

echo "Ensuring admin user exists..."
gosu $USER_ID:$GROUP_ID flask ensure-admin

echo "Entrypoint script completed. Starting application..."

# Execute the main command (likely gunicorn)
exec "$@"

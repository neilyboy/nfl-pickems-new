#!/bin/sh
set -e

# Create necessary directories with proper permissions
mkdir -p /app/instance /app/migrations
chown -R $(id -u):$(id -g) /app/instance /app/migrations
chmod -R 777 /app/instance /app/migrations

# Initialize database if it doesn't exist
if [ ! -f /app/instance/app.db ]; then
    touch /app/instance/app.db
    chmod 666 /app/instance/app.db
fi

# Initialize migrations if they don't exist
if [ ! -f /app/migrations/alembic.ini ]; then
    cd /app && flask db init
    chown -R $(id -u):$(id -g) /app/migrations
fi

# Run migrations
cd /app
flask db migrate -m "Initial migration" || true
flask db upgrade || true

# Create admin user if it doesn't exist
python create_admin.py || true

# Execute the main command
exec "$@"

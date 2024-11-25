#!/bin/sh
set -e

# Initialize database if it doesn't exist
if [ ! -f /app/instance/app.db ]; then
    touch /app/instance/app.db
fi

# Initialize migrations if they don't exist
if [ ! -f /app/migrations/alembic.ini ]; then
    cd /app && flask db init
fi

# Run migrations
cd /app && flask db upgrade

# Ensure admin user exists
cd /app && flask ensure-admin

# Start the application
exec "$@"

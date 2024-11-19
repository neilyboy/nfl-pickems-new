#!/bin/sh

# Create instance directory if it doesn't exist
mkdir -p /app/instance
chmod 777 /app/instance

# Initialize database if it doesn't exist
if [ ! -f /app/instance/app.db ]; then
    touch /app/instance/app.db
    chmod 666 /app/instance/app.db
fi

# Initialize migrations if they don't exist
if [ ! -d /app/migrations ]; then
    flask db init
fi

# Run migrations
flask db migrate -m "Initial migration" || true
flask db upgrade || true

# Execute the main command
exec "$@"

#!/bin/bash
set -e

echo "Starting entrypoint script..."

cd /app

# Initialize database
init_database() {
    echo "Initializing database..."
    
    # Create database file if it doesn't exist
    if [ ! -f "/app/instance/app.db" ]; then
        echo "Creating new database file..."
        touch "/app/instance/app.db"
        chmod 666 "/app/instance/app.db"
    fi
    
    # Initialize migrations if they don't exist
    if [ ! -d "/app/migrations" ] || [ -z "$(ls -A /app/migrations)" ]; then
        echo "Initializing migrations..."
        flask db init
    fi
    
    # Run migrations
    echo "Running database migrations..."
    flask db stamp head || echo "Migration stamp head failed (this is normal for first run)"
    flask db migrate || echo "No new migrations to generate"
    flask db upgrade || echo "No migrations to apply"
    
    # Initialize database with admin user if needed
    if [ "$INIT_DB" = "true" ]; then
        echo "Initializing database with admin user..."
        flask init-db || echo "Database initialization failed"
    fi
}

# Main execution
init_database

echo "Entrypoint script completed. Starting application..."

# Execute the main command (likely gunicorn)
exec "$@"

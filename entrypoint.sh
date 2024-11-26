#!/bin/bash
set -e

echo "Starting entrypoint script..."

cd /app

# Set correct permissions for instance directory
echo "Setting up instance directory permissions..."
mkdir -p /app/instance
chown -R ${HOST_UID:-1000}:${HOST_GID:-1000} /app/instance
chmod 755 /app/instance

# Function to wait for database to be accessible
wait_for_db() {
    local retries=5
    local wait_time=1
    local counter=0
    echo "Waiting for database directory to be accessible..."
    
    while [ $counter -lt $retries ]; do
        if [ -w "/app/instance" ]; then
            echo "Database directory is accessible!"
            return 0
        fi
        echo "Waiting for database directory... (${counter}/${retries})"
        sleep $wait_time
        counter=$((counter + 1))
    done
    
    echo "Failed to access database directory after $retries attempts"
    return 1
}

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

# Ensure admin user exists
ensure_admin() {
    echo "Ensuring admin user exists..."
    flask ensure-admin || echo "Admin user check failed"
}

# Main execution
echo "Checking database directory permissions..."
if wait_for_db; then
    init_database
    ensure_admin
    echo "Database setup completed successfully"
else
    echo "Failed to access database directory - check permissions"
    exit 1
fi

echo "Entrypoint script completed. Starting application..."

# Execute the main command (likely gunicorn)
exec "$@"

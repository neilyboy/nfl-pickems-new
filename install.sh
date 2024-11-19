#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print status messages
print_status() {
    echo -e "${GREEN}[+]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[x]${NC} $1"
}

# Check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first:"
        echo "https://docs.docker.com/get-docker/"
        exit 1
    fi

    if ! command -v docker compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first:"
        echo "https://docs.docker.com/compose/install/"
        exit 1
    fi
}

# Function to generate a secure random key
generate_secret_key() {
    python3 -c 'import secrets; print(secrets.token_hex(32))'
}

# Function to check if a port is in use
check_port() {
    local port=$1
    if command -v nc &> /dev/null; then
        nc -z localhost $port &> /dev/null
        return $?
    elif command -v lsof &> /dev/null; then
        lsof -i :$port &> /dev/null
        return $?
    else
        # Fallback to netstat
        netstat -tuln 2>/dev/null | grep -q ":$port "
        return $?
    fi
}

# Function to find next available port
find_available_port() {
    local port=$1
    while check_port $port; do
        port=$((port + 1))
    done
    echo $port
}

# Main installation process
main() {
    print_status "NFL Pick'em Game Installation"
    echo "----------------------------"

    # Check for Docker
    print_status "Checking prerequisites..."
    check_docker

    # Create necessary directories
    print_status "Creating required directories..."
    mkdir -p instance migrations
    chmod 777 instance migrations

    # Set up environment file
    if [ ! -f .env ]; then
        print_status "Setting up environment file..."
        cp .env.example .env
        
        # Generate a secure secret key
        SECRET_KEY=$(generate_secret_key)
        sed -i.bak "s/generate-a-secure-secret-key-here/$SECRET_KEY/" .env
        rm -f .env.bak

        # Check ports and update if needed
        NGINX_PORT=8080
        APP_PORT=8000

        if check_port $NGINX_PORT; then
            NEW_NGINX_PORT=$(find_available_port $NGINX_PORT)
            print_warning "Port $NGINX_PORT is in use, using port $NEW_NGINX_PORT instead"
            NGINX_PORT=$NEW_NGINX_PORT
        fi

        if check_port $APP_PORT; then
            NEW_APP_PORT=$(find_available_port $APP_PORT)
            print_warning "Port $APP_PORT is in use, using port $NEW_APP_PORT instead"
            APP_PORT=$NEW_APP_PORT
        fi

        # Update ports in .env
        sed -i.bak "s/^NGINX_PORT=.*/NGINX_PORT=$NGINX_PORT/" .env
        sed -i.bak "s/^APP_PORT=.*/APP_PORT=$APP_PORT/" .env
        rm -f .env.bak

        print_warning "Please edit .env file with your preferred settings:"
        echo "  - Set ADMIN_USERNAME and ADMIN_PASSWORD"
        echo "  - Adjust TIMEZONE if needed (current: US/Eastern)"
        echo "  - Ports have been automatically configured to:"
        echo "    NGINX_PORT=$NGINX_PORT"
        echo "    APP_PORT=$APP_PORT"
        
        read -p "Press Enter to continue after editing .env (or Ctrl+C to cancel)..."
    else
        print_warning ".env file already exists, skipping creation..."
    fi

    # Start the application
    print_status "Starting NFL Pick'em..."
    docker compose down 2>/dev/null  # Clean up any existing containers
    docker compose up -d --build

    # Wait for the application to start
    print_status "Waiting for the application to start..."
    sleep 5

    # Check if the application is running
    if docker compose ps | grep -q "Up"; then
        print_status "NFL Pick'em is now running!"
        
        # Get the port from .env file or use default
        NGINX_PORT=$(grep NGINX_PORT .env 2>/dev/null | cut -d= -f2)
        NGINX_PORT=${NGINX_PORT:-8080}  # Default to 8080 if not found
        
        echo -e "\n${GREEN}Access URLs:${NC}"
        echo "Local: http://localhost:${NGINX_PORT}"
        
        # Try to get public IP
        PUBLIC_IP=$(curl -s ifconfig.me 2>/dev/null)
        if [ ! -z "$PUBLIC_IP" ]; then
            echo "Public: http://${PUBLIC_IP}:${NGINX_PORT}"
        fi
        
        echo -e "\n${GREEN}Useful Commands:${NC}"
        echo "View logs: docker compose logs -f"
        echo "Stop application: docker compose down"
        echo "Restart application: docker compose restart"
        echo "Backup database: docker compose exec web flask db-backup"
    else
        print_error "Installation failed! Check the logs with: docker compose logs"
        exit 1
    fi
}

# Run the installation
main

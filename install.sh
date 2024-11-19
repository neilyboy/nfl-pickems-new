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

        print_warning "Please edit .env file with your preferred settings:"
        echo "  - Set ADMIN_USERNAME and ADMIN_PASSWORD"
        echo "  - Adjust TIMEZONE if needed"
        echo "  - Change ports if needed"
        
        read -p "Press Enter to continue after editing .env..."
    else
        print_warning ".env file already exists, skipping creation..."
    fi

    # Start the application
    print_status "Starting NFL Pick'em..."
    docker compose up -d --build

    # Wait for the application to start
    print_status "Waiting for the application to start..."
    sleep 5

    # Check if the application is running
    if docker compose ps | grep -q "Up"; then
        print_status "NFL Pick'em is now running!"
        
        # Get the port from .env file or use default
        NGINX_PORT=$(grep NGINX_PORT .env 2>/dev/null | cut -d= -f2)
        NGINX_PORT=${NGINX_PORT:-80}  # Default to 80 if not found
        
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

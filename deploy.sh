#!/bin/bash

# Exit on error
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "Please run as root (sudo ./deploy.sh)"
    exit 1
fi

# Check if running on Ubuntu
if ! grep -q "Ubuntu" /etc/os-release; then
    print_warning "This script is designed for Ubuntu. Your mileage may vary on other distributions."
fi

# Install required packages if not present
print_status "Checking and installing required packages..."
apt update
apt install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    software-properties-common \
    git

# Install Docker if not present
if ! command -v docker &> /dev/null; then
    print_status "Installing Docker..."
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add -
    add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
    apt update
    apt install -y docker-ce docker-ce-cli containerd.io
fi

# Install Docker Compose if not present
if ! command -v docker-compose &> /dev/null; then
    print_status "Installing Docker Compose..."
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

# Create directories if they don't exist
print_status "Creating required directories..."
mkdir -p instance backups
chmod 777 instance backups

# Check if .env exists
if [ ! -f .env ]; then
    print_warning ".env file not found. Creating from .env.example..."
    if [ -f .env.example ]; then
        cp .env.example .env
        print_status "Please edit .env with your production settings"
        print_warning "Press Enter when ready to continue..."
        read
    else
        print_error ".env.example not found. Please create .env file manually."
        exit 1
    fi
fi

# Stop any running containers
print_status "Stopping any running containers..."
docker-compose down

# Pull latest changes
print_status "Pulling latest changes..."
git pull origin main

# Build and start containers
print_status "Building and starting containers..."
docker-compose up -d --build

# Wait for web container to be ready
print_status "Waiting for web container to be ready..."
sleep 10

# Run database migrations
print_status "Running database migrations..."
if ! docker-compose exec -T web flask db upgrade; then
    print_error "Database migration failed!"
    exit 1
fi

# Create admin user if it doesn't exist
print_status "Checking admin user..."
if ! docker-compose exec -T web python create_admin.py; then
    print_error "Admin user creation failed!"
    exit 1
fi

# Install SSL certificate if domain is configured
if grep -q "server_name" nginx.conf && ! grep -q "localhost" nginx.conf; then
    DOMAIN=$(grep "server_name" nginx.conf | awk '{print $2}' | sed 's/;//')
    if [ "$DOMAIN" != "localhost" ]; then
        print_status "Installing SSL certificate for $DOMAIN..."
        apt install -y certbot python3-certbot-nginx
        certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos --email "admin@$DOMAIN" --redirect
    fi
fi

# Check if containers are running
if docker-compose ps | grep -q "Up"; then
    print_status "Deployment successful!"
    echo -e "\n${GREEN}Application Status:${NC}"
    docker-compose ps
    
    # Get the public IP
    PUBLIC_IP=$(curl -s ifconfig.me)
    echo -e "\n${GREEN}Access URLs:${NC}"
    echo "Local: http://localhost"
    echo "Public: http://$PUBLIC_IP"
    
    if [ "$DOMAIN" != "localhost" ] && [ ! -z "$DOMAIN" ]; then
        echo "Domain: https://$DOMAIN"
    fi
    
    echo -e "\n${YELLOW}Useful Commands:${NC}"
    echo "View logs: docker-compose logs -f"
    echo "Restart app: docker-compose restart"
    echo "Stop app: docker-compose down"
else
    print_error "Deployment failed! Check logs with: docker-compose logs"
    exit 1
fi

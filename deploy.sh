#!/bin/bash

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

# Check if running on Ubuntu
if ! grep -q "Ubuntu" /etc/os-release; then
    print_warning "This script is designed for Ubuntu. Your mileage may vary on other distributions."
fi

# Install system dependencies if needed
install_dependencies() {
    print_status "Installing system dependencies..."
    sudo apt update
    sudo apt install -y \
        apt-transport-https \
        ca-certificates \
        curl \
        software-properties-common \
        git \
        lsof \
        python3-pip

    # Install Docker if not present
    if ! command -v docker &> /dev/null; then
        print_status "Installing Docker..."
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
        sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
        sudo apt update
        sudo apt install -y docker-ce docker-ce-cli containerd.io
        
        # Add current user to docker group
        sudo usermod -aG docker $USER
        print_warning "You may need to log out and back in for docker group changes to take effect"
    fi

    # Install Docker Compose if not present
    if ! command -v docker-compose &> /dev/null; then
        print_status "Installing Docker Compose..."
        sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        sudo chmod +x /usr/local/bin/docker-compose
    fi

    # Install Python dependencies for setup script
    pip3 install pytz
}

read -p "Do you need to install/update system dependencies? (y/n): " install_deps
if [[ "$install_deps" =~ ^[Yy]$ ]]; then
    install_dependencies
fi

# Run setup script if .env doesn't exist or user wants to reconfigure
if [ ! -f .env ] || [[ "$1" == "--reconfigure" ]]; then
    print_status "Running setup script..."
    python3 setup.py
fi

# Stop any running containers
print_status "Stopping any running containers..."
docker compose down -v || true

# Configure git to use HTTPS instead of SSH
git config --global url."https://github.com/".insteadOf git@github.com:

# Check if we're in a git repository
if [ ! -d .git ]; then
    print_status "Initializing fresh clone..."
    cd ..
    rm -rf nfl-pickems
    git clone https://github.com/neilyboy/nfl-pickems.git
    cd nfl-pickems
    # Copy back the .env file if it exists
    if [ -f ../.env ]; then
        cp ../.env .
    fi
else
    # Pull latest changes
    print_status "Pulling latest changes..."
    # Stash any local changes
    git stash || true
    git pull origin main || {
        print_error "Failed to pull latest changes. Please ensure you have the correct repository URL."
        exit 1
    }
    # Pop stashed changes
    git stash pop || true
fi

# Create required directories
print_status "Creating required directories..."
mkdir -p instance migrations
chmod -R 777 instance migrations

# Build and start containers
print_status "Building and starting containers..."
docker compose up -d --build

# Print status and instructions
if docker compose ps | grep -q "Up"; then
    print_status "Deployment successful!"
    echo -e "\n${GREEN}Application Status:${NC}"
    docker compose ps
    
    # Get the public IP
    PUBLIC_IP=$(curl -s ifconfig.me)
    
    # Get ports from .env file
    NGINX_PORT=$(grep NGINX_PORT .env | cut -d= -f2)
    NGINX_PORT=${NGINX_PORT:-8080}  # Default to 8080 if not found
    
    echo -e "\n${GREEN}Access URLs:${NC}"
    echo "Local: http://localhost:${NGINX_PORT}"
    echo "Public: http://${PUBLIC_IP}:${NGINX_PORT}"
    
    echo -e "\n${YELLOW}Useful Commands:${NC}"
    echo "View logs: docker compose logs -f"
    echo "Restart app: docker compose restart"
    echo "Stop app: docker compose down"
    echo "Reconfigure: ./deploy.sh --reconfigure"
else
    print_error "Deployment failed! Check logs with: docker compose logs"
    exit 1
fi

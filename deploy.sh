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

# Function to check if a port is available
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
        return 1
    else
        return 0
    fi
}

# Function to get valid port
get_valid_port() {
    local default_port=$1
    local port_type=$2
    local port

    while true; do
        read -p "Enter $port_type port (default: $default_port): " port
        port=${port:-$default_port}

        if ! [[ "$port" =~ ^[0-9]+$ ]]; then
            print_error "Please enter a valid port number"
            continue
        fi

        if [ "$port" -lt 1024 ] && [ "$EUID" -ne 0 ]; then
            print_error "Ports below 1024 require root privileges"
            continue
        fi

        if ! check_port "$port"; then
            print_warning "Port $port is already in use"
            read -p "Would you like to try a different port? (y/n): " try_again
            if [[ "$try_again" =~ ^[Yy]$ ]]; then
                continue
            fi
            print_error "Please free up port $port and try again"
            exit 1
        fi

        break
    done
    echo "$port"
}

# Function to install system dependencies
install_dependencies() {
    print_status "Installing system dependencies..."
    sudo apt update
    sudo apt install -y \
        apt-transport-https \
        ca-certificates \
        curl \
        software-properties-common \
        git \
        lsof

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
}

# Check if running on Ubuntu
if ! grep -q "Ubuntu" /etc/os-release; then
    print_warning "This script is designed for Ubuntu. Your mileage may vary on other distributions."
fi

# Install dependencies if needed
read -p "Do you need to install/update system dependencies? (y/n): " install_deps
if [[ "$install_deps" =~ ^[Yy]$ ]]; then
    install_dependencies
fi

# Get port configurations
print_status "Configuring ports..."
NGINX_PORT=$(get_valid_port 8080 "nginx")
APP_PORT=$(get_valid_port 8000 "application")

# Update docker-compose.yml with new ports
print_status "Updating docker-compose configuration..."
sed -i.bak "s/- \"80:80\"/- \"$NGINX_PORT:80\"/" docker-compose.yml
sed -i.bak "s/- \"8000:8000\"/- \"$APP_PORT:8000\"/" docker-compose.yml

# Create directories if they don't exist
print_status "Creating required directories..."
mkdir -p instance backups migrations
chmod 777 instance backups migrations

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
docker-compose down || true

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
    git pull https://github.com/neilyboy/nfl-pickems.git main || {
        print_error "Failed to pull latest changes. Please ensure you have the correct repository URL."
        exit 1
    }
    # Pop stashed changes
    git stash pop || true
fi

# Build and start containers
print_status "Building and starting containers..."
docker-compose up -d --build

# Wait for web container to be ready
print_status "Waiting for web container to be ready..."
sleep 10

# Initialize database if needed
print_status "Initializing database..."
if [ ! -f migrations/alembic.ini ]; then
    print_status "First time setup: Initializing migrations..."
    docker-compose exec -T web flask db init
fi

# Run database migrations
print_status "Running database migrations..."
if ! docker-compose exec -T web flask db migrate -m "Initial migration"; then
    print_error "Database migration generation failed!"
    exit 1
fi

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
        sudo apt install -y certbot python3-certbot-nginx
        sudo certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos --email "admin@$DOMAIN" --redirect
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
    echo "Local: http://localhost:$NGINX_PORT"
    echo "Public: http://$PUBLIC_IP:$NGINX_PORT"
    
    if [ "$DOMAIN" != "localhost" ] && [ ! -z "$DOMAIN" ]; then
        echo "Domain: https://$DOMAIN"
    fi
    
    echo -e "\n${YELLOW}Useful Commands:${NC}"
    echo "View logs: docker-compose logs -f"
    echo "Restart app: docker-compose restart"
    echo "Stop app: docker-compose down"
    
    # Save port configuration
    echo -e "\n${GREEN}Port Configuration:${NC}"
    echo "Nginx port: $NGINX_PORT"
    echo "Application port: $APP_PORT"
    echo "These settings have been saved to docker-compose.yml"
else
    print_error "Deployment failed! Check logs with: docker-compose logs"
    exit 1
fi

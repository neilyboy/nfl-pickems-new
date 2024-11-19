#!/bin/bash

# Exit on error
set -e

# Check if .env exists
if [ ! -f .env ]; then
    echo "Error: .env file not found"
    echo "Please create .env file from .env.example"
    exit 1
fi

# Pull latest changes
git pull origin main

# Build and start containers
docker-compose up -d --build

# Run database migrations
docker-compose exec -T web flask db upgrade

# Create admin user if it doesn't exist
docker-compose exec -T web python create_admin.py

echo "Deployment complete!"
echo "Application is running at http://localhost"

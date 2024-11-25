# NFL Pick'em App Deployment Guide

This guide will help you deploy the NFL Pick'em application on an Ubuntu server.

## Prerequisites

1. Ubuntu Server (20.04 LTS or newer)
2. Root access or sudo privileges
3. Domain name (optional, but recommended)

## Step 1: Initial Server Setup

```bash
# Update system packages
sudo apt update
sudo apt upgrade -y

# Install required system packages
sudo apt install -y python3-pip python3-venv nginx git supervisor

# Install PostgreSQL (recommended for production)
sudo apt install -y postgresql postgresql-contrib
```

## Step 2: Create Application User and Directory

```bash
# Create application user
sudo useradd -m -s /bin/bash nflpicks

# Create application directory
sudo mkdir -p /var/www/nflpicks
sudo chown nflpicks:nflpicks /var/www/nflpicks
```

## Step 3: Clone and Set Up Application

```bash
# Switch to application user
sudo su - nflpicks

# Clone repository
cd /var/www/nflpicks
git clone https://github.com/neilyboy/nfl-pickems-new.git .

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Step 4: Configure PostgreSQL Database

```bash
# Create database and user
sudo -u postgres psql

postgres=# CREATE DATABASE nflpicks;
postgres=# CREATE USER nflpicks WITH PASSWORD 'your_secure_password';
postgres=# GRANT ALL PRIVILEGES ON DATABASE nflpicks TO nflpicks;
postgres=# \q
```

## Step 5: Configure Environment Variables

Create a .env file in /var/www/nflpicks:

```bash
# Application configuration
FLASK_APP=nfl_pickems.py
FLASK_ENV=production
SECRET_KEY=your_secure_secret_key

# Database configuration
DATABASE_URL=postgresql://nflpicks:your_secure_password@localhost/nflpicks

# ESPN API configuration (if needed)
ESPN_API_KEY=your_espn_api_key
```

## Step 6: Set Up Gunicorn Configuration

Create /etc/supervisor/conf.d/nflpicks.conf:

```ini
[program:nflpicks]
directory=/var/www/nflpicks
command=/var/www/nflpicks/venv/bin/gunicorn -w 4 -b 127.0.0.1:5001 "app:create_app()"
user=nflpicks
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stderr_logfile=/var/log/nflpicks/gunicorn.err.log
stdout_logfile=/var/log/nflpicks/gunicorn.out.log
```

Create log directory:
```bash
sudo mkdir -p /var/log/nflpicks
sudo chown -R nflpicks:nflpicks /var/log/nflpicks
```

## Step 7: Configure Nginx

Create /etc/nginx/sites-available/nflpicks:

```nginx
server {
    server_name your_domain.com;  # Replace with your domain

    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /var/www/nflpicks/app/static;
        expires 30d;
    }

    listen 80;
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/nflpicks /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default  # Remove default site
sudo nginx -t  # Test configuration
sudo systemctl restart nginx
```

## Step 8: Initialize Database and Start Services

```bash
# Initialize database
source venv/bin/activate
flask db upgrade

# Start services
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start nflpicks
```

## Step 9: Set Up SSL (Optional but Recommended)

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d your_domain.com
```

## Step 10: Final Steps

1. Create admin user:
```bash
source venv/bin/activate
flask init-db
```

2. Test the application:
   - Visit http://your_domain.com (or https:// if SSL is configured)
   - Log in with admin credentials
   - Verify all functionality works

## Maintenance

### Updating the Application

```bash
# Switch to application directory
cd /var/www/nflpicks

# Pull latest changes
git pull

# Activate virtual environment
source venv/bin/activate

# Update dependencies
pip install -r requirements.txt

# Apply database migrations
flask db upgrade

# Restart application
sudo supervisorctl restart nflpicks
```

### Viewing Logs

```bash
# Application logs
sudo tail -f /var/log/nflpicks/gunicorn.out.log
sudo tail -f /var/log/nflpicks/gunicorn.err.log

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Backup Database

```bash
# Backup
pg_dump -U nflpicks nflpicks > backup.sql

# Restore (if needed)
psql -U nflpicks nflpicks < backup.sql
```

## Troubleshooting

1. Check application status:
```bash
sudo supervisorctl status nflpicks
```

2. Check Nginx status:
```bash
sudo systemctl status nginx
```

3. Check logs for errors:
```bash
sudo tail -f /var/log/nflpicks/gunicorn.err.log
```

4. Test Nginx configuration:
```bash
sudo nginx -t
```

5. Verify database connection:
```bash
psql -U nflpicks -h localhost -d nflpicks
```

If you encounter any issues during deployment, check these logs and statuses for error messages.

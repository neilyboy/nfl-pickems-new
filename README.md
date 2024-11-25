# NFL Pick'em Game

A web application for managing NFL game predictions with friends. Users can make picks for each week's games and compete to see who has the most accurate predictions.

## Features

- Weekly game picks for all NFL games
- Real-time game score updates via ESPN API
- Standings page showing pick accuracy
  - Interactive trend visualization
  - Weekly performance tracking
  - Visual pick history
- Monday Night Football total points prediction
- Admin interface for managing users and games
  - Database backup and restore
  - Password management
  - User management
- Responsive design for mobile and desktop

## Technologies Used

- Python 3.12
- Flask 3.0.0
- SQLAlchemy 2.0.23
- Bootstrap 5.3.2
- JavaScript Libraries
  - ApexCharts (Interactive trend visualization)
  - Font Awesome (Icons)
  - Bootstrap Bundle (UI components)

## Installation on Ubuntu 24.04

### Prerequisites

1. Update system packages:
```bash
sudo apt update && sudo apt upgrade -y
```

2. Install Docker and Docker Compose:
```bash
# Install required packages
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common

# Add Docker's official GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Add Docker repository
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Add your user to docker group (optional, for running docker without sudo)
sudo usermod -aG docker $USER
newgrp docker
```

### Deployment Steps

1. Clone the repository:
```bash
git clone https://github.com/neilyboy/nfl-pickems.git
cd nfl-pickems
```

2. Set up environment variables:
```bash
cp .env.example .env
```

3. Edit the .env file with your settings:
```bash
nano .env
```

Required environment variables:
```env
FLASK_APP=app
FLASK_ENV=production
SECRET_KEY=your-secure-secret-key
ADMIN_USERNAME=your-admin-username
ADMIN_PASSWORD=your-secure-password
DATABASE_URL=sqlite:///instance/app.db
TIMEZONE=US/Eastern
NGINX_PORT=8080
APP_PORT=8000
```

4. Create required directories:
```bash
mkdir -p instance backups
chmod 777 instance backups
```

5. Build and start the application:
```bash
# Build and start containers in detached mode
docker compose up -d --build

# Check container status
docker compose ps
```

6. Access the application:
- Open your web browser and navigate to `http://your-server-ip:8080`
- Log in with the admin credentials you set in the .env file

### Maintenance Commands

1. View logs:
```bash
# View all logs
docker compose logs

# View specific service logs
docker compose logs web
docker compose logs nginx

# Follow logs in real-time
docker compose logs -f
```

2. Restart services:
```bash
docker compose restart
```

3. Stop services:
```bash
docker compose down
```

4. Update application:
```bash
# Pull latest changes
git pull

# Rebuild and restart containers
docker compose down
docker compose up -d --build
```

5. Backup database:
```bash
# Enter the web container
docker compose exec web bash

# Run backup command
flask db-backup

# Exit container
exit
```

### Troubleshooting

1. Check container status:
```bash
docker compose ps
```

2. Check container logs:
```bash
docker compose logs web
```

3. Check nginx configuration:
```bash
docker compose exec nginx nginx -t
```

4. Reset admin password:
```bash
docker compose exec web flask reset-admin-password
```

5. Check file permissions:
```bash
ls -la instance/
ls -la backups/
```

## Production Deployment

### Prerequisites
- Ubuntu/Debian server
- Docker and Docker Compose installed
- Git installed
- Root or sudo access

### Installation Steps

1. Install required packages:
```bash
# Update system
sudo apt update
sudo apt upgrade -y

# Install required packages
sudo apt install -y docker.io docker-compose git curl

# Add your user to docker group
sudo usermod -aG docker $USER

# Log out and log back in for the group change to take effect
```

2. Set up application directory:
```bash
# Create directory
sudo mkdir -p /opt/nfl-pickems
sudo chown -R $USER:$USER /opt/nfl-pickems
cd /opt/nfl-pickems

# Clone repository
git clone https://github.com/neilyboy/nfl-pickems-new.git .
```

3. Create systemd service for persistence and auto-start:
```bash
sudo nano /etc/systemd/system/nfl-pickems.service
```

Add this content to the service file:
```ini
[Unit]
Description=NFL Pickems Docker Compose Application
Requires=docker.service
After=docker.service network.target

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/nfl-pickems
ExecStartPre=/bin/sleep 10
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
```

4. Enable and start the service:
```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable nfl-pickems.service

# Start the service
sudo systemctl start nfl-pickems.service
```

5. Verify installation:
```bash
# Check service status
sudo systemctl status nfl-pickems.service

# Check running containers
docker ps

# View logs if needed
sudo journalctl -u nfl-pickems.service -f
```

### Data Persistence
The application uses Docker volumes to ensure data persistence:
- Database is stored in a Docker volume named `app-data`
- Volume persists across container restarts and system reboots
- Database location: `/app/instance/app.db` inside the volume

### Automatic Startup
- Application automatically starts on system boot
- Containers automatically restart on failure
- Service waits for Docker and network to be ready before starting

### Maintenance Commands

**View Logs:**
```bash
# Service logs
sudo journalctl -u nfl-pickems.service -f

# Container logs
docker logs nfl-pickems-web-1
docker logs nfl-pickems-nginx-1
```

**Restart Application:**
```bash
sudo systemctl restart nfl-pickems.service
```

**Stop Application:**
```bash
sudo systemctl stop nfl-pickems.service
```

**Check Volume:**
```bash
docker volume ls
docker volume inspect nfl-pickems_app-data
```

**Update Application:**
```bash
cd /opt/nfl-pickems
git pull
sudo systemctl restart nfl-pickems.service
```

### Troubleshooting

1. If the service fails to start:
   - Check logs: `sudo journalctl -u nfl-pickems.service -f`
   - Ensure Docker is running: `sudo systemctl status docker`
   - Verify permissions: `ls -l /opt/nfl-pickems`

2. If database is not persisting:
   - Check volume: `docker volume ls`
   - Inspect volume: `docker volume inspect nfl-pickems_app-data`
   - Verify docker-compose.yml has volume configuration

3. If containers keep restarting:
   - Check container logs: `docker logs nfl-pickems-web-1`
   - Verify environment variables in .env file
   - Check disk space: `df -h`

### Security Notes
- Ensure firewall allows access to port 80
- Consider setting up SSL/TLS with Let's Encrypt
- Regularly update system and Docker images
- Back up the database volume regularly

## Project Structure

```
nfl-pickems/
├── app/                    # Application code
│   ├── admin/             # Admin interface
│   ├── auth/              # Authentication
│   ├── main/              # Main routes
│   ├── models/            # Database models
│   ├── services/          # Business logic
│   ├── static/            # Static files
│   └── templates/         # HTML templates
├── instance/              # Instance-specific files
├── migrations/            # Database migrations
├── backups/              # Database backups
├── Dockerfile            # Container definition
├── docker-compose.yml    # Container orchestration
├── nginx.conf           # Nginx configuration
├── entrypoint.sh        # Container entrypoint
├── requirements.txt     # Python dependencies
└── .env                # Environment variables
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

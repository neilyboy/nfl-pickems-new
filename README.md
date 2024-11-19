# NFL Pick'em Game

A web application for managing NFL game predictions with friends. Users can make picks for each week's games and compete to see who has the most accurate predictions.

## Features

- Weekly game picks for all NFL games
- Real-time game score updates via ESPN API
- Standings page showing pick accuracy
- Monday Night Football total points prediction
- Admin interface for managing users and games
  - Database backup and restore
  - Password management
  - User management
- Responsive design for mobile and desktop

## Production Deployment on Ubuntu Server

### Prerequisites

1. Ubuntu Server 20.04 LTS or newer
2. Docker and Docker Compose installed:
```bash
# Update package list
sudo apt update

# Install required packages
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common

# Add Docker's official GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -

# Add Docker repository
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"

# Install Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

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
nano .env  # Edit with your production settings
```

Required environment variables:
```
FLASK_APP=run.py
FLASK_ENV=production
SECRET_KEY=your-secure-secret-key
DATABASE_URL=sqlite:///instance/app.db
BACKUP_DIR=/app/backups
```

3. Create required directories:
```bash
mkdir -p instance backups
chmod 777 instance backups  # Ensure Docker has write permissions
```

4. Build and start the containers:
```bash
docker-compose up -d --build
```

5. Initialize the database and create admin user:
```bash
# Initialize database
docker-compose exec web flask db upgrade

# Create initial admin user (follow prompts)
docker-compose exec web python create_admin.py
```

6. Configure your domain (optional):
```bash
# Edit nginx.conf
nano nginx.conf

# Update server_name with your domain
server {
    listen 80;
    server_name your-domain.com;  # Change this
    ...
}
```

7. Set up SSL with Let's Encrypt (recommended):
```bash
# Install certbot
sudo apt install -y certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com
```

### Maintenance

#### Backup Database
```bash
# Manual backup
docker-compose exec web flask db-backup

# Backups are stored in ./backups directory
```

#### Update Application
```bash
# Pull latest changes
git pull

# Rebuild and restart containers
docker-compose up -d --build

# Run any new migrations
docker-compose exec web flask db upgrade
```

#### View Logs
```bash
# View all logs
docker-compose logs

# View specific service logs
docker-compose logs web
docker-compose logs nginx

# Follow logs
docker-compose logs -f
```

### Troubleshooting

1. Check container status:
```bash
docker-compose ps
```

2. Check application logs:
```bash
docker-compose logs web
```

3. Restart services:
```bash
docker-compose restart
```

4. Reset everything:
```bash
docker-compose down
docker-compose up -d --build
```

### Security Notes

1. Always use strong passwords for admin account
2. Keep your system and Docker updated
3. Use SSL/TLS in production (Let's Encrypt)
4. Regularly backup your database
5. Monitor logs for suspicious activity

## Local Development Setup

1. Clone the repository:
```bash
git clone [your-repo-url]
cd nfl-pickems
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Initialize the database:
```bash
flask db upgrade
python init_db.py
```

6. Create an admin user:
```bash
python create_admin.py
```

7. Start the development server:
```bash
flask run
```

## Project Structure

- `/app` - Main application code
  - `/admin` - Admin interface routes and forms
  - `/auth` - Authentication routes
  - `/models` - Database models
  - `/services` - Business logic and external API integration
  - `/static` - Static files (CSS, images)
  - `/templates` - Jinja2 templates
  - `/utils` - Utility functions
- `/instance` - Instance-specific files (database)
- `/backups` - Database backups
- `/migrations` - Database migrations

## Backup and Restore

The application includes built-in backup and restore functionality:

1. Access the admin dashboard
2. Use the "Backup Database" button to create and download a backup
3. Use the "Restore Database" to restore from a backup file

Backups are stored in the `/backups` directory with timestamps.

## Security

- All admin routes are protected
- Passwords are hashed using Werkzeug security
- CSRF protection on all forms
- Secure session handling
- Regular database backups
- Input validation and sanitization

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License

## Support

For issues and feature requests, please create an issue on GitHub.

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

## Production Deployment

### Using Docker (Recommended)

1. Clone the repository:
```bash
git clone [your-repo-url]
cd nfl-pickems
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your production configuration
```

3. Build and start the containers:
```bash
docker-compose up -d --build
```

4. Initialize the database:
```bash
docker-compose exec web flask db upgrade
docker-compose exec web python init_db.py
docker-compose exec web python create_admin.py
```

The application will be available at:
- HTTP: http://your-domain
- Container port: 8000
- Nginx port: 80

### Manual Deployment

1. Clone and set up:
```bash
git clone [your-repo-url]
cd nfl-pickems
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your production configuration
```

3. Initialize the database:
```bash
flask db upgrade
python init_db.py
python create_admin.py
```

4. Run with gunicorn:
```bash
gunicorn --bind 0.0.0.0:8000 --workers 4 run:app
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

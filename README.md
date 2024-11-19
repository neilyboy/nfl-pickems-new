# NFL Pick'em Application

A modern, mobile-responsive web application for tracking NFL pick'em competitions. Inspired by Sleeper.com's design aesthetic.

## Features

- 📱 Mobile-first responsive design
- 📊 Real-time standings and statistics
- 🏈 Live game tracking via ESPN API
- 👤 User avatar management
- 🔐 Admin dashboard for user and pick management
- 💾 Season data backup and archival
- 🏆 Weekly and season-long statistics

## Installation

### Using Docker (Recommended)

1. Clone the repository:
```bash
git clone https://github.com/yourusername/nfl-pickems.git
cd nfl-pickems
```

2. Build and run with Docker Compose:
```bash
docker-compose up --build
```

The application will be available at `http://localhost:5000`

### Manual Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/nfl-pickems.git
cd nfl-pickems
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Initialize the database:
```bash
flask db upgrade
```

6. Run the application:
```bash
flask run
```

## Environment Variables

Create a `.env` file with the following variables:

```
FLASK_APP=app
FLASK_ENV=development
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///nfl_pickems.db
ADMIN_PASSWORD=your-admin-password
```

## Admin Access

Default admin credentials:
- Password: admin

Change the admin password through the admin settings page after first login.

## API Data

The application uses the ESPN NFL API for game data:
- Endpoint: https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard
- Data is cached locally and updates every 5 minutes
- Manual updates available through admin panel

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

Distributed under the MIT License. See `LICENSE` for more information.

# NFL Pick'em Game

A web application for managing NFL game predictions with friends. Users can make picks for each week's games and compete to see who has the most accurate predictions.

## Features

- Weekly game picks for all NFL games
- Real-time game score updates via ESPN API
- Standings page showing pick accuracy
- Monday Night Football total points prediction
- Admin interface for managing users and games
- Responsive design for mobile and desktop

## Installation

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

4. Initialize the database:
```bash
python init_db.py
```

5. Create an admin user:
```bash
python create_admin.py
```

## Running the Application

1. Start the server:
```bash
./start_server.sh
```

2. Access the application at `http://localhost:5000`

## Development

- The application uses Flask for the web framework
- SQLAlchemy for database management
- ESPN API for game data
- Bootstrap 5 for the frontend

## Project Structure

- `/app` - Main application code
  - `/admin` - Admin interface routes and forms
  - `/auth` - Authentication routes
  - `/models` - Database models
  - `/services` - Business logic and external API integration
  - `/static` - Static files (CSS, images)
  - `/templates` - Jinja2 templates
  - `/utils` - Utility functions

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License

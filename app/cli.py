from datetime import datetime, timedelta
from app.extensions import db
from app.models.game import GameCache
import json
import click
from flask.cli import with_appcontext
from app.services.game_service import GameService

@click.command('update-games')
@click.option('--week', type=int, help='Week number to update. If not specified, updates current week.')
@click.option('--force', is_flag=True, help='Force update even if cache exists')
@with_appcontext
def update_games_command(week, force):
    """Update NFL game data from ESPN"""
    games = GameService.update_week_games(week, force)
    click.echo(f"Updated {len(games)} games for week {week or 'current'}")

@click.command('init-sample-games')
@with_appcontext
def init_sample_games():
    """Initialize sample NFL games for testing."""
    # Create sample games for week 1
    sample_games = [
        {
            'id': 'sample1',
            'name': 'Kansas City Chiefs at Buffalo Bills',
            'shortName': 'KC @ BUF',
            'week': 1,
            'season_type': 2,
            'year': 2024,
            'date': (datetime.now() + timedelta(days=7)).isoformat(),
            'status': 'scheduled',
            'home_team': 'BUF',
            'away_team': 'KC',
            'home_score': 0,
            'away_score': 0,
            'home_team_name': 'Buffalo Bills',
            'away_team_name': 'Kansas City Chiefs',
            'is_mnf': False
        },
        {
            'id': 'sample2',
            'name': 'San Francisco 49ers at Dallas Cowboys',
            'shortName': 'SF @ DAL',
            'week': 1,
            'season_type': 2,
            'year': 2024,
            'date': (datetime.now() + timedelta(days=7)).isoformat(),
            'status': 'scheduled',
            'home_team': 'DAL',
            'away_team': 'SF',
            'home_score': 0,
            'away_score': 0,
            'home_team_name': 'Dallas Cowboys',
            'away_team_name': 'San Francisco 49ers',
            'is_mnf': False
        },
        {
            'id': 'sample3',
            'name': 'Green Bay Packers at Detroit Lions',
            'shortName': 'GB @ DET',
            'week': 1,
            'season_type': 2,
            'year': 2024,
            'date': (datetime.now() + timedelta(days=8)).isoformat(),
            'status': 'scheduled',
            'home_team': 'DET',
            'away_team': 'GB',
            'home_score': 0,
            'away_score': 0,
            'home_team_name': 'Detroit Lions',
            'away_team_name': 'Green Bay Packers',
            'is_mnf': True
        }
    ]
    
    # Clear existing games for week 1
    GameCache.query.filter_by(week=1, season_type=2, year=2024).delete()
    
    # Add new sample games
    for game in sample_games:
        game_cache = GameCache(
            game_id=game['id'],
            week=game['week'],
            season_type=game['season_type'],
            year=game['year'],
            start_time=datetime.fromisoformat(game['date']),
            data=json.dumps(game),
            is_mnf=game['is_mnf'],
            home_team=game['home_team'],
            away_team=game['away_team'],
            home_team_abbrev=game['home_team'],
            away_team_abbrev=game['away_team'],
            home_score=game['home_score'],
            away_score=game['away_score'],
            status=game['status']
        )
        db.session.add(game_cache)
    
    db.session.commit()
    click.echo("Sample games initialized for week 1 of 2024 season")

@click.command('ensure-admin')
@with_appcontext
def ensure_admin_command():
    """Ensure admin user exists and optionally reset password."""
    from app.models.user import User
    from app.extensions import db
    import os

    admin = User.query.filter_by(username='admin').first()
    if not admin:
        print('Admin user does not exist. Creating...')
        admin = User(username='admin', is_admin=True)
        admin.set_password('admin')
        db.session.add(admin)
        db.session.commit()
        print('Admin user created!')
    elif os.environ.get('RESET_ADMIN_PASSWORD', '').lower() == 'true':
        print('Resetting admin password...')
        admin.set_password('admin')
        db.session.commit()
        print('Admin password updated!')
    else:
        print('Admin user already exists!')

def init_cli(app):
    """Initialize CLI commands."""
    app.cli.add_command(update_games_command)
    app.cli.add_command(init_sample_games)
    app.cli.add_command(ensure_admin_command)

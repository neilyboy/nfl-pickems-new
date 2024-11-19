import requests
import json
from datetime import datetime
from app.models.game import GameCache
from app.extensions import db

ESPN_NFL_API = 'https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard'

def fetch_games():
    """Fetch game data from ESPN API."""
    try:
        response = requests.get(ESPN_NFL_API)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching ESPN data: {e}")
        return None

def parse_game_data(game_data):
    """Parse raw game data from ESPN API."""
    game_id = game_data['id']
    week = game_data['week']['number']
    
    home_team = game_data['competitions'][0]['competitors'][0]
    away_team = game_data['competitions'][0]['competitors'][1]
    
    # Ensure home team is actually home team
    if home_team['homeAway'] == 'away':
        home_team, away_team = away_team, home_team
    
    game = {
        'game_id': game_id,
        'week': week,
        'status': game_data['status']['type']['name'],
        'home_team': home_team['team']['abbreviation'],
        'away_team': away_team['team']['abbreviation'],
        'home_score': int(home_team['score']) if 'score' in home_team else None,
        'away_score': int(away_team['score']) if 'score' in away_team else None,
        'start_time': datetime.strptime(game_data['date'], '%Y-%m-%dT%H:%MZ'),
        'is_mnf': game_data['competitions'][0].get('notes', [{}])[0].get('headline', '').lower().find('monday') != -1
    }
    
    if game['status'].startswith('Final'):
        home_winner = home_team.get('winner', False)
        away_winner = away_team.get('winner', False)
        game['winning_team'] = home_team['team']['abbreviation'] if home_winner else away_team['team']['abbreviation']
    
    return game

def update_games():
    """Update game cache with latest ESPN data."""
    data = fetch_games()
    if not data:
        return
    
    for game_data in data['events']:
        parsed_game = parse_game_data(game_data)
        game_cache = GameCache.query.filter_by(game_id=parsed_game['game_id']).first()
        
        if game_cache:
            # Update existing game
            for key, value in parsed_game.items():
                setattr(game_cache, key, value)
            game_cache.last_updated = datetime.utcnow()
            game_cache.data = json.dumps(game_data)
        else:
            # Create new game cache
            game_cache = GameCache(
                data=json.dumps(game_data),
                last_updated=datetime.utcnow(),
                **parsed_game
            )
            db.session.add(game_cache)
        
    try:
        db.session.commit()
    except Exception as e:
        print(f"Error updating game cache: {e}")
        db.session.rollback()

def get_week_games(week):
    """Get all games for a specific week."""
    return GameCache.query.filter_by(week=week).all()

def get_mnf_games(week):
    """Get Monday Night Football games for a specific week."""
    return GameCache.query.filter_by(week=week, is_mnf=True).all()

def get_current_week():
    """Get the current NFL week."""
    data = fetch_games()
    if data and 'week' in data:
        return data['week']['number']
    return None

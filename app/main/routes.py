from flask import render_template, request, current_app, jsonify
from app.main import bp
from app.models.user import User
from app.models.pick import Pick, MNFPrediction
from app.models.game import GameCache
from app.utils.espn_api import get_current_week, get_week_games, get_mnf_games
from collections import defaultdict
from flask_login import login_required, current_user
from datetime import datetime
from app import db
from functools import wraps
from app.data.nfl_teams import NFL_TEAMS
import os

# Debug: Print NFL_TEAMS at module level
print("NFL_TEAMS dictionary loaded:", sorted(NFL_TEAMS.keys()))

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kws):
        if not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kws)
    return decorated_function

def get_team_abbrev(team_name):
    """Convert full team name to abbreviation"""
    # If it's already an abbreviation (2-4 letters), return it uppercase
    if 2 <= len(team_name) <= 4:
        abbrev = team_name.upper()
        # Special case for Washington which can be either WAS or WSH
        if abbrev == 'WAS':
            return 'WSH'
        if abbrev in NFL_TEAMS:
            return abbrev
    
    # Otherwise try to find it by full name
    team_name = team_name.upper()
    for abbrev, team_data in NFL_TEAMS.items():
        if team_data['name'].upper() == team_name:
            return abbrev
    
    # If we still haven't found it, try some common variations
    team_variations = {
        'LAC': ['LA CHARGERS', 'LOS ANGELES CHARGERS'],
        'LAR': ['LA RAMS', 'LOS ANGELES RAMS'],
        'WSH': ['WAS', 'WASHINGTON'],
        'SF': ['SAN FRAN', 'SAN FRANCISCO', '49ERS', 'NINERS'],
        'TB': ['TAMPA', 'TAMPA BAY', 'BUCCANEERS', 'BUCS'],
        'GB': ['GREEN BAY'],
        'NE': ['NEW ENGLAND', 'PATRIOTS', 'PATS'],
        'NO': ['NEW ORLEANS', 'SAINTS'],
        'KC': ['KANSAS CITY', 'CHIEFS']
    }
    
    for abbrev, variations in team_variations.items():
        if team_name in variations:
            return abbrev
    
    return team_name if team_name in NFL_TEAMS else None

@bp.context_processor
def inject_year():
    return {'current_year': datetime.now().year}

@bp.route('/')
@bp.route('/standings', defaults={'week': None})
@bp.route('/standings/<int:week>')
def standings(week=None):
    current_week = get_current_week()
    selected_week = week if week is not None else current_week

    # Get all users except admin
    users = User.query.filter_by(is_admin=False).all()
    
    # Get all games for the week
    games = GameCache.query.filter_by(week=selected_week).all()
    total_games = len(games)
    current_app.logger.info(f"Found {total_games} games for week {selected_week}")
    
    # Get all picks for the week
    picks = Pick.query.filter_by(week=selected_week).all()
    current_app.logger.info(f"Found {len(picks)} total picks for week {selected_week}")
    
    # Get MNF predictions for the week
    mnf_predictions = MNFPrediction.query.filter_by(week=selected_week).all()
    
    # Define team abbreviation mapping
    TEAM_ABBREV = {
        'ARIZONA': 'ari', 'CARDINALS': 'ari', 'ARI': 'ari',
        'ATLANTA': 'atl', 'FALCONS': 'atl', 'ATL': 'atl',
        'BALTIMORE': 'bal', 'RAVENS': 'bal', 'BAL': 'bal',
        'BUFFALO': 'buf', 'BILLS': 'buf', 'BUF': 'buf',
        'CAROLINA': 'car', 'PANTHERS': 'car', 'CAR': 'car',
        'CHICAGO': 'chi', 'BEARS': 'chi', 'CHI': 'chi',
        'CINCINNATI': 'cin', 'BENGALS': 'cin', 'CIN': 'cin',
        'CLEVELAND': 'cle', 'BROWNS': 'cle', 'CLE': 'cle',
        'DALLAS': 'dal', 'COWBOYS': 'dal', 'DAL': 'dal',
        'DENVER': 'den', 'BRONCOS': 'den', 'DEN': 'den',
        'DETROIT': 'det', 'LIONS': 'det', 'DET': 'det',
        'GREEN BAY': 'gb', 'PACKERS': 'gb', 'GB': 'gb',
        'HOUSTON': 'hou', 'TEXANS': 'hou', 'HOU': 'hou',
        'INDIANAPOLIS': 'ind', 'COLTS': 'ind', 'IND': 'ind',
        'JACKSONVILLE': 'jax', 'JAGUARS': 'jax', 'JAX': 'jax', 'JAC': 'jax',
        'KANSAS CITY': 'kc', 'CHIEFS': 'kc', 'KC': 'kc',
        'LA CHARGERS': 'lac', 'LOS ANGELES CHARGERS': 'lac', 'LAC': 'lac',
        'LA RAMS': 'lar', 'LOS ANGELES RAMS': 'lar', 'LAR': 'lar',
        'LAS VEGAS': 'lv', 'RAIDERS': 'lv', 'LV': 'lv',
        'MIAMI': 'mia', 'DOLPHINS': 'mia', 'MIA': 'mia',
        'MINNESOTA': 'min', 'VIKINGS': 'min', 'MIN': 'min',
        'NEW ENGLAND': 'ne', 'PATRIOTS': 'ne', 'NE': 'ne',
        'NEW ORLEANS': 'no', 'SAINTS': 'no', 'NO': 'no',
        'NY GIANTS': 'nyg', 'NEW YORK GIANTS': 'nyg', 'NYG': 'nyg',
        'NY JETS': 'nyj', 'NEW YORK JETS': 'nyj', 'NYJ': 'nyj',
        'PHILADELPHIA': 'phi', 'EAGLES': 'phi', 'PHI': 'phi',
        'PITTSBURGH': 'pit', 'STEELERS': 'pit', 'PIT': 'pit',
        'SEATTLE': 'sea', 'SEAHAWKS': 'sea', 'SEA': 'sea',
        'SAN FRANCISCO': 'sf', '49ERS': 'sf', 'SF': 'sf',
        'TAMPA BAY': 'tb', 'BUCCANEERS': 'tb', 'TB': 'tb',
        'TENNESSEE': 'ten', 'TITANS': 'ten', 'TEN': 'ten',
        'WASHINGTON': 'was', 'COMMANDERS': 'was', 'WAS': 'was', 'WSH': 'was'
    }
    
    # Calculate weekly records and prepare user data
    standings_data = []
    season_standings = []
    
    for user in users:
        weekly_record = user.get_weekly_record(selected_week)
        season_record = user.get_season_record()
        
        # Get weekly trend data
        weekly_trend = []
        for w in range(1, current_week + 1):
            week_record = user.get_weekly_record(w)
            weekly_trend.append(week_record['wins'])
        
        # Get user's picks for display
        user_picks = []
        user_picks_count = 0
        for game in games:
            pick = next((p for p in picks if p.user_id == user.id and p.game_id == game.game_id), None)
            if pick:
                team_picked = pick.team_picked.strip().upper()
                current_app.logger.info(f"Processing pick for {user.username} - Raw team: {team_picked}")
                
                # Get the team abbreviation from our mapping
                team_abbrev = TEAM_ABBREV.get(team_picked)
                if team_abbrev:
                    logo_path = f"/static/img/teams/{team_abbrev}.png"
                    current_app.logger.info(f"Found team abbreviation: {team_abbrev}, Logo path: {logo_path}")
                    
                    # Check if the logo file exists
                    logo_file = current_app.root_path + "/static/img/teams/" + team_abbrev + ".png"
                    if os.path.exists(logo_file):
                        current_app.logger.info(f"Logo file exists: {logo_file}")
                    else:
                        current_app.logger.error(f"Logo file does not exist: {logo_file}")
                    
                    pick_data = {
                        'team': team_picked,
                        'team_logo': logo_path,
                        'result': 'win' if pick.is_correct else 'loss' if pick.is_correct is not None else 'pending'
                    }
                    user_picks.append(pick_data)
                    user_picks_count += 1
                else:
                    current_app.logger.error(f"Unknown team abbreviation: {team_picked}")
        
        current_app.logger.info(f"Found {user_picks_count} picks for user {user.username}")
        
        # Calculate weekly percentage
        total_picks = weekly_record['total']
        weekly_percentage = (weekly_record['wins'] / total_picks * 100) if total_picks > 0 else 0
        
        # Calculate season percentage
        total_season_picks = season_record['total']
        season_percentage = (season_record['wins'] / total_season_picks * 100) if total_season_picks > 0 else 0
        
        user_data = {
            'username': user.username,
            'weekly_correct': weekly_record['wins'],
            'weekly_total': weekly_record['total'],
            'weekly_percentage': weekly_percentage,
            'season_correct': season_record['wins'],
            'season_total': season_record['total'],
            'season_percentage': season_percentage,
            'weekly_trend': weekly_trend,
            'picks': user_picks,
            'mnf_prediction': next((p.total_points for p in mnf_predictions if p.user_id == user.id), None)
        }
        standings_data.append(user_data)
    
    # Sort standings by weekly wins (descending) and username (ascending)
    standings_data.sort(key=lambda x: (-x['weekly_correct'], x['username']))
    season_standings = sorted(standings_data, key=lambda x: (-x['season_correct'], x['username']))
    
    return render_template('main/standings.html',
                         standings=standings_data,
                         season_standings=season_standings,
                         week=selected_week,
                         total_games=total_games)

# Removed old make_picks route as it's been replaced by picks.picks

@bp.route('/submit_picks', methods=['POST'])
@admin_required
def submit_picks():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    week = data.get('week')
    user_id = data.get('user_id')
    picks = data.get('picks', {})
    mnf_points = data.get('mnf_points')
    
    if not week or not user_id:
        return jsonify({'error': 'Week and user must be specified'}), 400
    
    try:
        # Get all games for the week
        games = GameCache.query.filter_by(week=week).all()
        
        # Delete existing picks for the week
        Pick.query.filter_by(user_id=user_id, week=week).delete()
        
        # Save new picks
        for game in games:
            team_picked = picks.get(game.game_id)
            if team_picked in [game.home_team, game.away_team]:
                pick = Pick(
                    user_id=user_id,
                    week=week,
                    game_id=game.game_id,
                    team_picked=team_picked
                )
                db.session.add(pick)
        
        # Handle MNF prediction
        if mnf_points is not None:
            MNFPrediction.query.filter_by(user_id=user_id, week=week).delete()
            try:
                mnf_points = int(mnf_points)
                if 0 <= mnf_points <= 200:  # Validate the points range
                    mnf_pred = MNFPrediction(
                        user_id=user_id,
                        week=week,
                        total_points=mnf_points
                    )
                    db.session.add(mnf_pred)
            except (ValueError, TypeError):
                pass  # Invalid points value
        
        db.session.commit()
        return jsonify({'message': 'Picks saved successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

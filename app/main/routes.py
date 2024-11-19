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

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kws):
        if not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kws)
    return decorated_function

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
    
    # Get all picks for the week
    picks = Pick.query.filter_by(week=selected_week).all()
    
    # Get MNF predictions for the week
    mnf_predictions = MNFPrediction.query.filter_by(week=selected_week).all()
    
    # Calculate weekly records and prepare user data
    standings_data = []
    for user in users:
        weekly_record = user.get_weekly_record(selected_week)
        season_record = user.get_season_record()
        
        # Get user's picks for display
        user_picks = []
        for game in games:
            pick = next((p for p in picks if p.user_id == user.id and p.game_id == game.game_id), None)
            if pick:
                pick_data = {
                    'game_id': game.game_id,
                    'away_team': game.away_team,
                    'home_team': game.home_team,
                    'team_picked': pick.team_picked,
                    'is_correct': pick.is_correct,
                    'away_team_abbrev': game.away_team_abbrev.upper(),
                    'home_team_abbrev': game.home_team_abbrev.upper(),
                    'away_team_score': game.away_score,
                    'home_team_score': game.home_score,
                    'game_status': game.status
                }
                user_picks.append(pick_data)
        
        # Get user's MNF prediction
        mnf_prediction = next((p for p in mnf_predictions if p.user_id == user.id), None)
        mnf_data = None
        if mnf_prediction:
            mnf_data = {
                'prediction': mnf_prediction.total_points,
                'points_off': mnf_prediction.points_off if mnf_prediction.points_off is not None else None
            }
        
        # Calculate weekly percentage
        total_picks = weekly_record['total']  # Finished picks
        total_possible = weekly_record['total_possible']  # Total picks made
        weekly_percentage = (weekly_record['wins'] / total_picks * 100) if total_picks > 0 else 0
        
        # Calculate season percentage
        total_season_picks = season_record['total']  # Finished picks
        total_season_possible = season_record['total_possible']  # Total picks made
        season_percentage = (season_record['wins'] / total_season_picks * 100) if total_season_picks > 0 else 0
        
        user_data = {
            'id': user.id,
            'username': user.username,
            'weekly_wins': weekly_record['wins'],  # Store raw number for sorting
            'weekly_correct': f"{weekly_record['wins']}/{weekly_record['total']}",  # For display
            'weekly_percentage': weekly_percentage,
            'season_wins': season_record['wins'],  # Store raw number for sorting
            'season_correct': f"{season_record['wins']}/{season_record['total']}",  # For display
            'season_percentage': season_percentage,
            'picks': user_picks,
            'mnf_prediction': mnf_data['prediction'] if mnf_data else None,
            'mnf_points_off': mnf_data['points_off'] if mnf_data and mnf_data['points_off'] is not None else None,
            'mnf_over': mnf_data['points_off'] < 0 if mnf_data and mnf_data['points_off'] is not None else True  # True means prediction was over
        }
        standings_data.append(user_data)
    
    # Sort standings:
    # 1. Most weekly wins
    # 2. For ties, closest MNF prediction without going over
    # 3. If still tied or no MNF prediction, keep original order
    def sort_key(x):
        wins = x['weekly_wins']
        mnf_points_off = x.get('mnf_points_off')
        mnf_over = x.get('mnf_over', True)
        
        # If prediction is over or no prediction, use infinity for sorting
        if mnf_over or mnf_points_off is None:
            mnf_points_off = float('inf')
            
        return (-wins, mnf_points_off)  # Negative wins for descending order
        
    standings_data.sort(key=sort_key)
    
    # Get weekly ranks history for season standings
    season_standings = []
    for user in users:
        season_record = user.get_season_record()
        season_percentage = (season_record['wins'] / season_record['total'] * 100) if season_record['total'] > 0 else 0
        
        # Get weekly ranks for sparkline
        weekly_ranks = []
        for w in range(1, current_week + 1):
            week_record = user.get_weekly_record(w)
            if week_record['total'] > 0:  # Only include weeks with picks
                weekly_ranks.append(week_record['wins'])
        
        user_data = {
            'id': user.id,
            'username': user.username,
            'season_wins': season_record['wins'],  # Store raw number for sorting
            'season_correct': f"{season_record['wins']}/{season_record['total']}",
            'season_percentage': season_percentage,
            'weekly_ranks': weekly_ranks
        }
        season_standings.append(user_data)
    
    # Sort season standings by total wins
    season_standings.sort(key=lambda x: (-x['season_wins']))
    
    return render_template('main/standings.html',
                         current_week=selected_week,
                         total_games=total_games,
                         standings=standings_data,
                         season_standings=season_standings,
                         season_total=sum(1 for g in GameCache.query.all() if g.status == 'STATUS_FINAL'),
                         nfl_teams={k.upper(): v for k, v in NFL_TEAMS.items()})

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

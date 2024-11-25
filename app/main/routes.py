from flask import render_template, request, current_app, jsonify
from app.main import bp
from app.models.user import User
from app.models.pick import Pick, MNFPrediction
from app.models.game import GameCache
from app.utils.espn_api import get_current_week, get_week_games, get_mnf_games
from collections import defaultdict, Counter
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
    if not team_name:
        return None
        
    team_name = team_name.upper()
    abbrev_map = {
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
        'JACKSONVILLE': 'jax', 'JAGUARS': 'jax', 'JAX': 'jax',
        'KANSAS CITY': 'kc', 'CHIEFS': 'kc', 'KC': 'kc',
        'LOS ANGELES CHARGERS': 'lac', 'CHARGERS': 'lac', 'LAC': 'lac',
        'LOS ANGELES RAMS': 'lar', 'RAMS': 'lar', 'LAR': 'lar',
        'LAS VEGAS': 'lv', 'RAIDERS': 'lv', 'LV': 'lv',
        'MIAMI': 'mia', 'DOLPHINS': 'mia', 'MIA': 'mia',
        'MINNESOTA': 'min', 'VIKINGS': 'min', 'MIN': 'min',
        'NEW ENGLAND': 'ne', 'PATRIOTS': 'ne', 'NE': 'ne',
        'NEW ORLEANS': 'no', 'SAINTS': 'no', 'NO': 'no',
        'NEW YORK GIANTS': 'nyg', 'GIANTS': 'nyg', 'NYG': 'nyg',
        'NEW YORK JETS': 'nyj', 'JETS': 'nyj', 'NYJ': 'nyj',
        'PHILADELPHIA': 'phi', 'EAGLES': 'phi', 'PHI': 'phi',
        'PITTSBURGH': 'pit', 'STEELERS': 'pit', 'PIT': 'pit',
        'SEATTLE': 'sea', 'SEAHAWKS': 'sea', 'SEA': 'sea',
        'SAN FRANCISCO': 'sf', '49ERS': 'sf', 'SF': 'sf',
        'TAMPA BAY': 'tb', 'BUCCANEERS': 'tb', 'TB': 'tb',
        'TENNESSEE': 'ten', 'TITANS': 'ten', 'TEN': 'ten',
        'WASHINGTON': 'was', 'COMMANDERS': 'was', 'WAS': 'was'
    }
    return abbrev_map.get(team_name)

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
    
    def calculate_team_stats(user_id):
        """Calculate success rate for each team picked by the user"""
        team_stats = defaultdict(lambda: {'correct': 0, 'total': 0})
        
        # Get all picks for the user
        picks = Pick.query.filter_by(user_id=user_id).all()
        
        for pick in picks:
            if pick.is_correct is not None:  # Only count decided games
                team = pick.team_picked.strip().upper()
                team_stats[team]['total'] += 1
                if pick.is_correct:
                    team_stats[team]['correct'] += 1
        
        # Calculate success rates
        team_success_rates = {}
        for team, stats in team_stats.items():
            if stats['total'] >= 3:  # Only include teams picked at least 3 times
                success_rate = (stats['correct'] / stats['total']) * 100
                team_success_rates[team] = {
                    'success_rate': success_rate,
                    'correct': stats['correct'],
                    'total': stats['total']
                }
        
        return team_success_rates

    def calculate_streaks(user_id):
        """Calculate streak information including current streak"""
        picks = Pick.query.filter_by(user_id=user_id).order_by(Pick.week.asc()).all()
        
        current_streak = 0
        longest_win_streak = 0
        longest_loss_streak = 0
        current_streak_type = None
        
        # Track the current streak separately
        current_streak_count = 0
        current_streak_is_win = None
        last_pick = None
        
        for pick in picks:
            if pick.is_correct is None:
                continue
                
            # Update historical longest streaks
            if current_streak_type is None:
                current_streak_type = pick.is_correct
                current_streak = 1
            elif pick.is_correct == current_streak_type:
                current_streak += 1
            else:
                if current_streak_type:  # Was a win streak
                    longest_win_streak = max(longest_win_streak, current_streak)
                else:  # Was a loss streak
                    longest_loss_streak = max(longest_loss_streak, current_streak)
                current_streak_type = pick.is_correct
                current_streak = 1
            
            # Update current streak
            if last_pick is None or pick.is_correct == current_streak_is_win:
                current_streak_count += 1
                current_streak_is_win = pick.is_correct
            else:
                current_streak_count = 1
                current_streak_is_win = pick.is_correct
            
            last_pick = pick
        
        # Check final historical streak
        if current_streak_type is not None:
            if current_streak_type:
                longest_win_streak = max(longest_win_streak, current_streak)
            else:
                longest_loss_streak = max(longest_loss_streak, current_streak)
        
        return {
            'longest_win_streak': longest_win_streak,
            'longest_loss_streak': longest_loss_streak,
            'current_streak': current_streak_count,
            'current_streak_type': 'win' if current_streak_is_win else 'loss' if current_streak_is_win is not None else None
        }

    def calculate_upsets(user_id):
        """Calculate upset picks (correctly picking against the majority)"""
        picks = Pick.query.filter_by(user_id=user_id).all()
        upset_picks = []
        total_correct_upsets = 0
        
        for pick in picks:
            if pick.is_correct:
                # Get all picks for this game
                game_picks = Pick.query.filter_by(game_id=pick.game_id).all()
                if not game_picks:
                    continue
                
                # Count picks for each team
                team_counts = {}
                for p in game_picks:
                    team = p.team_picked.upper()
                    team_counts[team] = team_counts.get(team, 0) + 1
                
                # Find the majority picked team
                majority_team = max(team_counts.items(), key=lambda x: x[1])[0]
                total_picks = sum(team_counts.values())
                
                # If user picked against majority (and won)
                user_pick = pick.team_picked.upper()
                if user_pick != majority_team:
                    majority_percentage = (team_counts[majority_team] / total_picks) * 100
                    # Only count as upset if at least 65% picked the other team
                    if majority_percentage >= 65:
                        total_correct_upsets += 1
                        game = GameCache.query.filter_by(game_id=pick.game_id).first()
                        upset_picks.append({
                            'week': pick.week,
                            'team': pick.team_picked,
                            'opponent': game.away_team if pick.team_picked.upper() == game.home_team.upper() else game.home_team,
                            'majority_pct': majority_percentage
                        })
        
        # Sort by how heavily favored the other team was
        upset_picks.sort(key=lambda x: x['majority_pct'], reverse=True)
        
        return {
            'total_upsets': total_correct_upsets,
            'upset_picks': upset_picks[:3]  # Top 3 biggest upsets
        }

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
                team_abbrev = get_team_abbrev(team_picked)
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
        
        # Calculate streaks and upsets
        streak_info = calculate_streaks(user.id)
        upset_info = calculate_upsets(user.id)
        team_stats = calculate_team_stats(user.id)
        
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
            'mnf_prediction': next((p.total_points for p in mnf_predictions if p.user_id == user.id), None),
            'streak_info': streak_info,
            'upset_info': upset_info,
            'team_stats': team_stats
        }
        standings_data.append(user_data)
    
    # Sort standings by weekly wins (descending) and username (ascending)
    standings_data.sort(key=lambda x: (-x['weekly_correct'], x['username']))
    season_standings = sorted(standings_data, key=lambda x: (-x['season_correct'], x['username']))
    
    return render_template('main/standings.html',
                         standings=standings_data,
                         season_standings=season_standings,
                         current_week=current_week,
                         selected_week=selected_week,
                         total_games=total_games)

@bp.route('/head_to_head')
def head_to_head():
    """Compare picks between two users"""
    user1_id = request.args.get('user1', type=int)
    user2_id = request.args.get('user2', type=int)
    
    # Get all non-admin users
    users = User.query.filter_by(is_admin=False).order_by(User.username).all()
    
    if not user1_id or not user2_id:
        return render_template('main/head_to_head.html', users=users)
    
    user1 = User.query.get_or_404(user1_id)
    user2 = User.query.get_or_404(user2_id)
    
    # Get all picks for both users
    user1_picks = Pick.query.filter_by(user_id=user1.id).all()
    user2_picks = Pick.query.filter_by(user_id=user2.id).all()
    
    # Convert picks to dictionary for easier lookup
    user1_picks_dict = {(p.week, p.game_id): p for p in user1_picks}
    user2_picks_dict = {(p.week, p.game_id): p for p in user2_picks}
    
    # Initialize stats
    stats = {
        'different_picks': 0,
        'head_to_head': {user1.id: 0, user2.id: 0},
        'total_games': 0,
        'agreement_percentage': 0
    }
    
    # Weekly breakdown
    weekly_breakdown = []
    current_week = get_current_week()
    
    for week in range(1, current_week + 1):
        week_games = []
        different_picks = 0
        
        # Get all games for the week
        games = GameCache.query.filter_by(week=week).all()
        
        for game in games:
            pick1 = user1_picks_dict.get((week, game.game_id))
            pick2 = user2_picks_dict.get((week, game.game_id))
            
            if not pick1 or not pick2:
                continue
                
            stats['total_games'] += 1
            
            # Get winner if game is finished
            winner = None
            if game.home_score is not None and game.away_score is not None:
                # Use stored team abbreviations instead of converting full names
                winner_team = game.home_team_abbrev if game.home_score > game.away_score else game.away_team_abbrev
                winner = winner_team.lower() if winner_team else None
            
            # Get and validate picks - ensure abbreviations are lowercase
            user1_abbrev = get_team_abbrev(pick1.team_picked) if pick1 and pick1.team_picked else None
            user2_abbrev = get_team_abbrev(pick2.team_picked) if pick2 and pick2.team_picked else None
            
            user1_pick = user1_abbrev.lower() if user1_abbrev else None
            user2_pick = user2_abbrev.lower() if user2_abbrev else None
            
            # Skip if either pick is missing
            if not user1_pick or not user2_pick:
                continue
            
            if user1_pick != user2_pick:
                stats['different_picks'] += 1
                different_picks += 1
                
                # If game is finished, update head-to-head record
                if winner:
                    if user1_pick == winner:
                        stats['head_to_head'][user1.id] += 1
                    else:
                        stats['head_to_head'][user2.id] += 1
            
            week_games.append({
                'user1_pick': user1_pick,
                'user2_pick': user2_pick,
                'winner': winner
            })
        
        if week_games:
            weekly_breakdown.append({
                'week': week,
                'different_picks': different_picks,
                'games': week_games
            })
    
    # Calculate agreement percentage
    if stats['total_games'] > 0:
        stats['agreement_percentage'] = ((stats['total_games'] - stats['different_picks']) / stats['total_games']) * 100
    
    return render_template('main/head_to_head.html',
                         users=users,
                         user1=user1,
                         user2=user2,
                         stats=stats,
                         weekly_breakdown=weekly_breakdown)

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

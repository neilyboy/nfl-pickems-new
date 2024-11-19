from datetime import datetime
from flask import render_template, flash, redirect, url_for, request, jsonify
from flask_login import login_required, current_user
from app.picks import bp
from app.models.game import GameCache
from app.models.pick import Pick, MNFPrediction
from app.models.user import User
from app.services.game_service import GameService
from app.extensions import db
from app.data.nfl_teams import NFL_TEAMS
import logging
logger = logging.getLogger(__name__)

@bp.route('/picks/<int:week>')
@bp.route('/picks/<int:week>/<int:user_id>')
@login_required
def picks(week, user_id=None):
    # Validate week number
    if week < 1 or week > 18:
        flash(f'Invalid week number: {week}. Please select a week between 1 and 18.', 'warning')
        return redirect(url_for('picks.picks', week=1))

    # Only admins can view other users' picks
    if user_id and not current_user.is_admin:
        flash('You do not have permission to view other users\' picks.', 'danger')
        return redirect(url_for('picks.picks', week=week))

    # Get all users for admin dropdown (exclude admin)
    all_users = User.query.filter(User.id != 1).order_by(User.username).all()
    
    # Get target user - either current user or selected user for admin
    target_user = current_user
    if current_user.is_admin and user_id:
        target_user = User.query.get_or_404(user_id)

    # Get games for the week
    games = GameService.update_week_games(week=week)
    
    if not games:
        flash(f'No games found for week {week}', 'warning')
        games = []

    # Transform game data into the format expected by the template
    transformed_games = []
    mnf_games = []
    
    logger.info(f"Processing {len(games)} games for week {week}")
    
    for game in games:
        try:
            # Handle both old and new API formats
            if isinstance(game.get('away_team'), dict):
                # New format
                away_abbrev = game['away_team']['abbreviation']
                home_abbrev = game['home_team']['abbreviation']
                away_team = game['away_team']['display_name']
                home_team = game['home_team']['display_name']
                away_score = game['away_team'].get('score', '0')
                home_score = game['home_team'].get('score', '0')
            else:
                # Old format
                away_abbrev = game['away_team']
                home_abbrev = game['home_team']
                away_team = game['away_team_name']
                home_team = game['home_team_name']
                away_score = game['away_score']
                home_score = game['home_score']
            
            # Parse game date - always convert to UTC
            game_date = datetime.fromisoformat(game['date'].replace('Z', '+00:00'))
            game_time = game_date.strftime('%I:%M %p')
            
            # Use the API's is_mnf flag if available, otherwise detect based on game time
            is_mnf = game.get('is_mnf', False)
            if not is_mnf and game_date.weekday() == 0:  # Monday is 0
                game_hour = game_date.hour
                is_mnf = game_hour >= 19 or game_hour < 4  # 7 PM to 4 AM UTC
            
            transformed_game = {
                'id': game.get('game_id', game.get('id')),
                'away_team_abbrev': away_abbrev,
                'home_team_abbrev': home_abbrev,
                'away_team': away_team,
                'home_team': home_team,
                'away_team_score': away_score,
                'home_team_score': home_score,
                'game_status': game.get('status', 'scheduled'),
                'game_time': game_time,
                'is_mnf': is_mnf
            }
            transformed_games.append(transformed_game)
            
            # If this is an MNF game, add it to the list
            if transformed_game['is_mnf']:
                mnf_games.append(transformed_game)
                logger.info(f"Found MNF game: {away_team} @ {home_team}")
                logger.info(f"Game details: status={game.get('status')}, time={game_time}, date={game_date}")
            
            # Debug logging for each game
            logger.info(f"Game {transformed_game['id']}: {away_team} @ {home_team}")
            logger.info(f"Status: {transformed_game['game_status']}, Time: {game_time}, Is MNF: {transformed_game['is_mnf']}")
            
        except (KeyError, TypeError) as e:
            logger.error(f"Error processing game data: {e}")
            logger.error(f"Raw game data: {game}")
            continue
    
    logger.info(f"Found {len(mnf_games)} MNF games for week {week}")
    
    # Get user's existing picks
    user_picks = {pick.game_id: pick.team_picked 
                 for pick in Pick.query.filter_by(user_id=target_user.id, week=week).all()}
    
    # Get MNF prediction if exists
    mnf_prediction = MNFPrediction.query.filter_by(
        user_id=target_user.id, 
        week=week
    ).first()
    
    if mnf_prediction:
        logger.info(f"Found existing MNF prediction for week {week}: {mnf_prediction.total_points} points")
    else:
        logger.info(f"No existing MNF prediction found for week {week}")
    
    # Debug: Print team abbreviations and logo URLs
    for game in transformed_games:
        print(f"Away Team: {game['away_team_abbrev']} -> Logo: {NFL_TEAMS.get(game['away_team_abbrev'].upper(), {}).get('logo', 'Not found')}")
        print(f"Home Team: {game['home_team_abbrev']} -> Logo: {NFL_TEAMS.get(game['home_team_abbrev'].upper(), {}).get('logo', 'Not found')}")
    
    return render_template('picks/picks.html',
                         week=week,
                         games=transformed_games,
                         user_picks=user_picks,
                         mnf_games=mnf_games,
                         mnf_prediction=mnf_prediction,
                         nfl_teams=NFL_TEAMS,
                         users=all_users,
                         target_user=target_user)

@bp.route('/submit-picks/<int:week>', methods=['GET', 'POST'])
@login_required
def submit_picks(week):
    # Get user_id from query parameter
    user_id = request.args.get('user_id', type=int)
    
    # Only admins can submit picks for other users
    if user_id and not current_user.is_admin:
        flash('You do not have permission to submit picks for other users.', 'danger')
        return redirect(url_for('picks.picks', week=week))

    # Get the target user
    target_user = User.query.get(user_id) if user_id else current_user

    if request.method != 'POST':
        return redirect(url_for('picks.picks', week=week, user_id=user_id))

    # Get games for the week
    games = GameService.update_week_games(week=week)
    if not games:
        flash(f'No games found for week {week}', 'warning')
        return redirect(url_for('main.index'))

    # Process each game pick
    for game in games:
        game_id = game['game_id']
        pick_key = f'pick_{game_id}'
        
        if pick_key in request.form:
            team_picked = request.form[pick_key]
            
            # Check if pick already exists
            pick = Pick.query.filter_by(
                user_id=target_user.id,
                week=week,
                game_id=game_id
            ).first()
            
            if pick:
                pick.team_picked = team_picked
            else:
                pick = Pick(
                    user_id=target_user.id,
                    week=week,
                    game_id=game_id,
                    team_picked=team_picked
                )
                db.session.add(pick)

    # Process MNF prediction if provided
    if 'mnf_total_points' in request.form and request.form['mnf_total_points']:
        total_points = int(request.form['mnf_total_points'])
        
        # Check if prediction already exists
        prediction = MNFPrediction.query.filter_by(
            user_id=target_user.id,
            week=week
        ).first()
        
        if prediction:
            prediction.total_points = total_points
        else:
            prediction = MNFPrediction(
                user_id=target_user.id,
                week=week,
                total_points=total_points
            )
            db.session.add(prediction)

    db.session.commit()
    flash('Picks submitted successfully!', 'success')
    return redirect(url_for('picks.picks', week=week, user_id=user_id))

@bp.route('/api/picks/<int:week>')
@login_required
def get_picks(week):
    """API endpoint to get user's picks for a week"""
    picks = Pick.query.filter_by(user_id=current_user.id, week=week).all()
    return jsonify({
        'picks': {pick.game_id: pick.team_picked for pick in picks}
    })

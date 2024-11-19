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

@bp.route('/picks/<int:week>', methods=['GET'])
@bp.route('/picks/<int:week>/<int:user_id>', methods=['GET'])
@login_required
def picks(week, user_id=None):
    # Only admins can view other users' picks
    if user_id and not current_user.is_admin:
        flash('You do not have permission to view other users\' picks.', 'danger')
        return redirect(url_for('picks.picks', week=week))

    # Get the target user
    target_user = User.query.get(user_id) if user_id else current_user
    
    # If admin, get all users for the dropdown
    users = User.query.all() if current_user.is_admin else None

    # Get games for the week
    games = GameService.update_week_games(week=week)
    
    if not games:
        flash(f'No games found for week {week}', 'warning')
        return redirect(url_for('main.index'))
    
    # Transform game data into the format expected by the template
    transformed_games = []
    mnf_games = []
    
    for game in games:
        # Debug: Print raw game data
        print(f"Raw game data: {game}")
        away_abbrev = game['away_team']['abbreviation']
        home_abbrev = game['home_team']['abbreviation']
        print(f"Team abbreviations - Away: {away_abbrev}, Home: {home_abbrev}")
        
        transformed_game = {
            'id': game['game_id'],
            'away_team_abbrev': away_abbrev,
            'home_team_abbrev': home_abbrev,
            'away_team': game['away_team']['display_name'],
            'home_team': game['home_team']['display_name'],
            'away_team_score': game['away_team']['score'],
            'home_team_score': game['home_team']['score'],
            'game_status': game['status'],
            'game_time': datetime.fromisoformat(game['date'].replace('Z', '+00:00')).strftime('%I:%M %p'),
            'is_mnf': game.get('is_mnf', False)
        }
        transformed_games.append(transformed_game)
        
        # If this is an MNF game, add it to the list
        if game.get('is_mnf', False):
            mnf_games.append(transformed_game)
            print(f"Added MNF game: {transformed_game}")
    
    # Debug: Print team abbreviations and logo URLs
    for game in transformed_games:
        print(f"Away Team: {game['away_team_abbrev']} -> Logo: {NFL_TEAMS.get(game['away_team_abbrev'].upper(), {}).get('logo', 'Not found')}")
        print(f"Home Team: {game['home_team_abbrev']} -> Logo: {NFL_TEAMS.get(game['home_team_abbrev'].upper(), {}).get('logo', 'Not found')}")
    
    # Get user's existing picks
    user_picks = {pick.game_id: pick.team_picked 
                 for pick in Pick.query.filter_by(user_id=target_user.id, week=week).all()}
    
    # Get MNF prediction if exists
    mnf_prediction = MNFPrediction.query.filter_by(
        user_id=target_user.id, 
        week=week
    ).first()
    
    return render_template('picks/picks.html',
                         user=target_user,
                         week=week,
                         games=transformed_games,
                         user_picks=user_picks,
                         mnf_games=mnf_games,
                         mnf_prediction=mnf_prediction,
                         nfl_teams=NFL_TEAMS,
                         users=users)

@bp.route('/submit-picks/<int:week>', methods=['POST'])
@bp.route('/submit-picks/<int:week>/<int:user_id>', methods=['POST'])
@login_required
def submit_picks(week, user_id=None):
    # Only admins can submit picks for other users
    if user_id and not current_user.is_admin:
        flash('You do not have permission to submit picks for other users.', 'danger')
        return redirect(url_for('picks.picks', week=week))

    # Get the target user
    target_user = User.query.get(user_id) if user_id else current_user

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

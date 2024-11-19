from flask import render_template, flash, redirect, url_for, request, jsonify, make_response
from flask_login import login_required, current_user
from app.admin import bp
from app.extensions import db, csrf
from app.services.game_service import GameService
from functools import wraps
import logging

logger = logging.getLogger(__name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return make_response(jsonify({'error': 'Admin access required'}), 403)
            flash('You need to be an admin to access this page.', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/')
@login_required
@admin_required
def index():
    return render_template('admin/index.html')

@bp.route('/refresh-games', methods=['GET', 'POST'])
@login_required
@admin_required
def refresh_games():
    try:
        logger.info("Starting game refresh")
        games = GameService.update_week_games(force=True)
        message = f'Successfully refreshed {len(games)} games from ESPN API!'
        logger.info(message)
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            response = make_response(jsonify({
                'success': True,
                'message': message,
                'games': len(games)
            }))
            response.headers['Content-Type'] = 'application/json'
            return response
            
        flash(message, 'success')
        return redirect(url_for('admin.index'))
        
    except Exception as e:
        error_msg = f'Error refreshing games: {str(e)}'
        logger.error(error_msg)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            response = make_response(jsonify({
                'success': False,
                'error': error_msg
            }), 500)
            response.headers['Content-Type'] = 'application/json'
            return response
        flash(error_msg, 'error')
        return redirect(url_for('admin.index'))

@bp.route('/update-picks', methods=['GET', 'POST'])
@login_required
@admin_required
def update_picks():
    try:
        logger.info("Starting pick updates")
        updated_picks = GameService.update_all_pick_results()
        message = f'Successfully updated {updated_picks} pick results!'
        logger.info(message)
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            response = make_response(jsonify({
                'success': True,
                'message': message,
                'picks': updated_picks
            }))
            response.headers['Content-Type'] = 'application/json'
            return response
            
        flash(message, 'success')
        return redirect(url_for('admin.index'))
        
    except Exception as e:
        error_msg = f'Error updating picks: {str(e)}'
        logger.error(error_msg)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            response = make_response(jsonify({
                'success': False,
                'error': error_msg
            }), 500)
            response.headers['Content-Type'] = 'application/json'
            return response
        flash(error_msg, 'error')
        return redirect(url_for('admin.index'))

from flask import render_template, jsonify, request, current_app, send_file, url_for
from app.admin import bp
from flask_login import login_required, current_user
from app.decorators import admin_required
from app.services.game_service import GameService
from app.models.user import User
from app.models.pick import Pick
from app.models.game import GameCache
from app import db
from werkzeug.security import check_password_hash, generate_password_hash
import os
import shutil
from datetime import datetime
import logging
from functools import wraps

logger = logging.getLogger(__name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'error': 'Admin access required'}), 403
            flash('You need to be an admin to access this page.', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/')
@login_required
@admin_required
def index():
    week_info = GameService.get_current_nfl_week()
    current_week = week_info['week'] if isinstance(week_info, dict) else week_info
    return render_template('admin/index.html', current_week=current_week)

@bp.route('/backup-db', methods=['POST'])
@login_required
@admin_required
def backup_db():
    try:
        # Create backups directory if it doesn't exist
        backup_dir = os.path.join(current_app.root_path, '..', 'backups')
        os.makedirs(backup_dir, exist_ok=True)

        # Create backup filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(backup_dir, f'nfl_pickems_backup_{timestamp}.db')

        # Get the path to the current database
        db_path = current_app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        if not os.path.exists(db_path):
            logger.error(f"Database file not found at {db_path}")
            return jsonify({'error': 'Database file not found'}), 404

        # Copy the database file
        shutil.copy2(db_path, backup_file)

        # Create a download URL
        download_url = url_for('admin.download_backup', filename=f'nfl_pickems_backup_{timestamp}.db')
        return jsonify({'download_url': download_url})

    except Exception as e:
        logger.error(f"Database backup failed: {str(e)}")
        return jsonify({'error': 'Failed to backup database'}), 500

@bp.route('/download-backup/<filename>')
@login_required
@admin_required
def download_backup(filename):
    try:
        backup_dir = os.path.join(current_app.root_path, '..', 'backups')
        return send_file(
            os.path.join(backup_dir, filename),
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        logger.error(f"Failed to download backup: {str(e)}")
        return jsonify({'error': 'Failed to download backup'}), 500

@bp.route('/restore-db', methods=['POST'])
@login_required
@admin_required
def restore_db():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if not file.filename.endswith('.db'):
            return jsonify({'error': 'Invalid file format. Must be a .db file'}), 400

        # Get the path to the current database
        db_path = current_app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')

        # Create a backup of the current database before restoring
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_dir = os.path.join(current_app.root_path, '..', 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        backup_file = os.path.join(backup_dir, f'pre_restore_backup_{timestamp}.db')
        shutil.copy2(db_path, backup_file)

        # Save the uploaded file as the new database
        file.save(db_path)

        return jsonify({'message': 'Database restored successfully'})

    except Exception as e:
        logger.error(f"Database restore failed: {str(e)}")
        return jsonify({'error': 'Failed to restore database'}), 500

@bp.route('/change-password', methods=['POST'])
@login_required
@admin_required
def change_password():
    try:
        data = request.get_json()
        current_password = data.get('current_password')
        new_password = data.get('new_password')

        if not current_password or not new_password:
            return jsonify({'error': 'Missing required fields'}), 400

        # Verify current password
        if not check_password_hash(current_user.password_hash, current_password):
            return jsonify({'error': 'Current password is incorrect'}), 400

        # Update password
        current_user.password_hash = generate_password_hash(new_password)
        db.session.commit()

        return jsonify({'message': 'Password changed successfully'})

    except Exception as e:
        logger.error(f"Password change failed: {str(e)}")
        return jsonify({'error': 'Failed to change password'}), 500

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
            response = jsonify({
                'success': True,
                'message': message,
                'games': len(games)
            })
            response.headers['Content-Type'] = 'application/json'
            return response
            
        flash(message, 'success')
        return redirect(url_for('admin.index'))
        
    except Exception as e:
        error_msg = f'Error refreshing games: {str(e)}'
        logger.error(error_msg)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            response = jsonify({
                'success': False,
                'error': error_msg
            }), 500
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
            response = jsonify({
                'success': True,
                'message': message,
                'picks': updated_picks
            })
            response.headers['Content-Type'] = 'application/json'
            return response
            
        flash(message, 'success')
        return redirect(url_for('admin.index'))
        
    except Exception as e:
        error_msg = f'Error updating picks: {str(e)}'
        logger.error(error_msg)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            response = jsonify({
                'success': False,
                'error': error_msg
            }), 500
            response.headers['Content-Type'] = 'application/json'
            return response
        flash(error_msg, 'error')
        return redirect(url_for('admin.index'))

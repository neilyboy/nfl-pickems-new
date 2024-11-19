from flask import render_template, flash, redirect, url_for, request
from flask_login import login_required, current_user
from app.admin import bp
from app.admin.forms import UserForm
from app.models.user import User
from app.extensions import db
from werkzeug.utils import secure_filename
from app.utils.espn_api import get_current_week
import os
from PIL import Image

@bp.route('/users')
@login_required
def users():
    if not current_user.is_admin:
        flash('You must be an admin to view this page.', 'danger')
        return redirect(url_for('admin.index'))
    users = User.query.filter(User.is_admin == False).all()
    current_week = request.args.get('week', get_current_week(), type=int)
    return render_template('admin/users.html', users=users, current_week=current_week)

@bp.route('/user/new', methods=['GET', 'POST'])
@login_required
def new_user():
    if not current_user.is_admin:
        flash('You must be an admin to create users.', 'danger')
        return redirect(url_for('admin.index'))
    
    form = UserForm()
    if form.validate_on_submit():
        user = User(username=form.username.data)
        
        # Handle avatar upload if provided
        if form.avatar.data:
            filename = secure_filename(form.avatar.data.filename)
            avatar_path = os.path.join('app', 'static', 'avatars', filename)
            
            # Ensure avatars directory exists
            os.makedirs(os.path.dirname(avatar_path), exist_ok=True)
            
            # Save and resize avatar
            image = Image.open(form.avatar.data)
            image.thumbnail((150, 150))
            image.save(avatar_path)
            
            user.avatar_path = f'/static/avatars/{filename}'
        
        db.session.add(user)
        db.session.commit()
        flash(f'User {user.username} has been created!', 'success')
        return redirect(url_for('admin.users'))
    
    return render_template('admin/user_form.html', form=form, title='New User')

@bp.route('/user/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    if not current_user.is_admin:
        flash('You must be an admin to edit users.', 'danger')
        return redirect(url_for('admin.index'))
    
    user = User.query.get_or_404(user_id)
    if user.is_admin:
        flash('Admin user cannot be edited.', 'danger')
        return redirect(url_for('admin.index'))
    
    form = UserForm(obj=user)
    if form.validate_on_submit():
        user.username = form.username.data
        
        # Handle avatar upload if provided
        if form.avatar.data:
            # Delete old avatar if it exists
            if user.avatar_path:
                old_avatar = os.path.join('app', user.avatar_path.lstrip('/'))
                if os.path.exists(old_avatar):
                    os.remove(old_avatar)
            
            filename = secure_filename(form.avatar.data.filename)
            avatar_path = os.path.join('app', 'static', 'avatars', filename)
            
            # Ensure avatars directory exists
            os.makedirs(os.path.dirname(avatar_path), exist_ok=True)
            
            # Save and resize avatar
            image = Image.open(form.avatar.data)
            image.thumbnail((150, 150))
            image.save(avatar_path)
            
            user.avatar_path = f'/static/avatars/{filename}'
        
        db.session.commit()
        flash(f'User {user.username} has been updated!', 'success')
        return redirect(url_for('admin.users'))
    
    return render_template('admin/user_form.html', form=form, user=user, title='Edit User')

@bp.route('/user/<int:user_id>/delete')
@login_required
def delete_user(user_id):
    if not current_user.is_admin:
        flash('You must be an admin to delete users.', 'danger')
        return redirect(url_for('admin.index'))
    
    user = User.query.get_or_404(user_id)
    if user.is_admin:
        flash('Admin user cannot be deleted.', 'danger')
        return redirect(url_for('admin.index'))
    
    # Delete user's avatar if it exists
    if user.avatar_path:
        avatar_path = os.path.join('app', user.avatar_path.lstrip('/'))
        if os.path.exists(avatar_path):
            os.remove(avatar_path)
    
    db.session.delete(user)
    db.session.commit()
    flash(f'User {user.username} has been deleted!', 'success')
    return redirect(url_for('admin.users'))

import os
from PIL import Image
from flask import current_app
from werkzeug.utils import secure_filename

def save_avatar(file, username):
    """Save and process user avatar"""
    if not file:
        return None
        
    # Create avatars directory if it doesn't exist
    avatar_path = os.path.join(current_app.root_path, 'static', 'avatars')
    os.makedirs(avatar_path, exist_ok=True)
    
    # Secure the filename and create full path
    filename = secure_filename(f"{username}_avatar.jpg")
    filepath = os.path.join(avatar_path, filename)
    
    # Process and save the image
    try:
        # Open and convert to RGB (handles PNG, JPEG, etc.)
        image = Image.open(file)
        image = image.convert('RGB')
        
        # Resize to standard size (e.g., 200x200)
        image.thumbnail((200, 200))
        
        # Save as JPEG
        image.save(filepath, 'JPEG', quality=85)
        
        # Return relative path for database storage
        return os.path.join('avatars', filename)
    except Exception as e:
        current_app.logger.error(f"Error saving avatar: {str(e)}")
        return None

def delete_avatar(avatar_path):
    """Delete user avatar file"""
    if not avatar_path:
        return
        
    try:
        full_path = os.path.join(current_app.root_path, 'static', avatar_path)
        if os.path.exists(full_path):
            os.remove(full_path)
    except Exception as e:
        current_app.logger.error(f"Error deleting avatar: {str(e)}")

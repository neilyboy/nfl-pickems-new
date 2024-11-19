from app import create_app
from app.extensions import db
from app.models.user import User
import os

def create_admin_user():
    app = create_app()
    with app.app_context():
        # Check if admin user already exists
        admin = User.query.filter_by(username=os.environ.get('ADMIN_USERNAME', 'admin')).first()
        if admin is None:
            admin = User(
                username=os.environ.get('ADMIN_USERNAME', 'admin'),
                is_admin=True
            )
            admin.set_password(os.environ.get('ADMIN_PASSWORD', 'admin'))
            db.session.add(admin)
            db.session.commit()
            print("Admin user created successfully!")
        else:
            print("Admin user already exists!")

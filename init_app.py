from app import create_app
from app.extensions import db
from app.models.user import User
import os

def init_app():
    app = create_app()
    with app.app_context():
        # Drop all tables first
        db.drop_all()
        print("Dropped all existing tables.")
        
        # Create all tables
        db.create_all()
        print("Database tables created successfully!")

        # Create admin user
        admin = User(
            username=os.environ.get('ADMIN_USERNAME', 'admin'),
            is_admin=True
        )
        admin.set_password(os.environ.get('ADMIN_PASSWORD', 'admin'))
        db.session.add(admin)
        db.session.commit()
        print("Admin user created successfully!")

if __name__ == '__main__':
    init_app()

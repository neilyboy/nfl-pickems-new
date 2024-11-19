from app import create_app
from app.extensions import db
from app.models.user import User
import os

def create_admin_user():
    app = create_app()
    with app.app_context():
        try:
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
                print(f"Username: {admin.username}")
                print(f"Password: {os.environ.get('ADMIN_PASSWORD', 'admin')}")
            else:
                print("Admin user already exists!")
                # Update admin password
                admin.set_password(os.environ.get('ADMIN_PASSWORD', 'admin'))
                db.session.commit()
                print("Admin password updated!")
                print(f"Username: {admin.username}")
                print(f"Password: {os.environ.get('ADMIN_PASSWORD', 'admin')}")
        except Exception as e:
            print(f"Error creating admin user: {str(e)}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    create_admin_user()

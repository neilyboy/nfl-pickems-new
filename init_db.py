from app import create_app, db
from app.models.user import User

def init_db():
    app = create_app()
    with app.app_context():
        # Create tables
        db.create_all()
        
        # Check if admin user exists
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(username='admin', is_admin=True)
            admin.set_password('admin')  # Set default password
            db.session.add(admin)
            db.session.commit()
            print("Created admin user (username: admin, password: admin)")
        else:
            print("Admin user already exists")

if __name__ == '__main__':
    init_db()

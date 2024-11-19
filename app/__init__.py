import os
from flask import Flask, redirect, url_for
from config import Config
from app.extensions import db, login, migrate, csrf
from app.scheduler import init_scheduler
from app.cli import init_cli
from app.services.game_service import GameService

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize Flask extensions
    db.init_app(app)
    login.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    
    # Initialize scheduler
    init_scheduler(app)
    
    # Initialize CLI commands
    init_cli(app)
    
    # Register blueprints
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)
    
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    from app.admin import bp as admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    from app.picks import bp as picks_bp
    app.register_blueprint(picks_bp, url_prefix='/picks')

    @app.context_processor
    def inject_current_week():
        """Inject current week into all templates."""
        current_week = GameService.get_current_nfl_week()['week']
        return dict(current_week=current_week)

    @app.route('/')
    def index():
        return redirect(url_for('main.standings'))

    @app.cli.command('init-db')
    def init_db():
        """Initialize the database."""
        db.drop_all()  # Drop existing tables
        db.create_all()
        
        # Create default admin user
        from app.models.user import User
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(username='admin', is_admin=True)
            admin.set_password('admin')
            db.session.add(admin)
            db.session.commit()
            print('Created admin user (username: admin, password: admin)')
        
        print('Database initialized.')

    @login.user_loader
    def load_user(id):
        from app.models import User
        return User.query.get(int(id))

    return app

from app import models

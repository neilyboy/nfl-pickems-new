from app.extensions import db, login
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User(UserMixin, db.Model):
    """User model for NFL Pick'em participants."""
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    password_hash = db.Column(db.String(128))  # Only used for admin
    avatar_path = db.Column(db.String(256))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)

    # Relationships
    picks = db.relationship('Pick', backref='user', lazy=True, cascade='all, delete-orphan')
    mnf_predictions = db.relationship('MNFPrediction', backref='user', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        if self.is_admin:  # Only set password for admin users
            self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if not self.is_admin:  # Non-admin users can't log in
            return False
        return check_password_hash(self.password_hash, password)

    def update_last_login(self):
        self.last_login = datetime.utcnow()
        db.session.commit()

    def get_weekly_record(self, week):
        """Get user's win-loss record for a specific week."""
        # Only count picks where is_correct is not None (game is finished)
        week_picks = [pick for pick in self.picks if pick.week == week]
        finished_picks = [pick for pick in week_picks if pick.is_correct is not None]
        wins = sum(1 for pick in finished_picks if pick.is_correct is True)
        losses = sum(1 for pick in finished_picks if pick.is_correct is False)
        total_possible = len(week_picks)  # Total picks made for the week
        return {
            'wins': wins, 
            'losses': losses, 
            'total': len(finished_picks),
            'total_possible': total_possible
        }

    def get_season_record(self):
        """Get user's overall season record."""
        # Only count picks where is_correct is not None (game is finished)
        all_picks = self.picks
        finished_picks = [pick for pick in all_picks if pick.is_correct is not None]
        wins = sum(1 for pick in finished_picks if pick.is_correct is True)
        losses = sum(1 for pick in finished_picks if pick.is_correct is False)
        total_possible = len(all_picks)  # Total picks made for the season
        return {
            'wins': wins, 
            'losses': losses, 
            'total': len(finished_picks),
            'total_possible': total_possible
        }

    def get_mnf_prediction(self, week):
        """Get user's Monday Night Football prediction for a specific week."""
        prediction = MNFPrediction.query.filter_by(user_id=self.id, week=week).first()
        return prediction

    def __repr__(self):
        return f'<User {self.username}>'

@login.user_loader
def load_user(id):
    return User.query.get(int(id))

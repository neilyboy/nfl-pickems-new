from datetime import datetime
from app.extensions import db

class Pick(db.Model):
    """Model for user's game picks."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    week = db.Column(db.Integer, nullable=False)
    game_id = db.Column(db.String(64), nullable=False)
    team_picked = db.Column(db.String(64), nullable=False)
    is_correct = db.Column(db.Boolean, default=None)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Pick Week:{self.week} Game:{self.game_id} Team:{self.team_picked}>'

class MNFPrediction(db.Model):
    """Model for Monday Night Football total points predictions."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    week = db.Column(db.Integer, nullable=False)
    total_points = db.Column(db.Integer)
    actual_total = db.Column(db.Integer)
    points_off = db.Column(db.Integer)
    is_over = db.Column(db.Boolean)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def calculate_difference(self, actual_total):
        """Calculate difference between prediction and actual total."""
        self.actual_total = actual_total
        self.points_off = abs(self.total_points - actual_total)
        self.is_over = self.total_points > actual_total

    def __repr__(self):
        return f'<MNFPrediction Week:{self.week} Points:{self.total_points}>'

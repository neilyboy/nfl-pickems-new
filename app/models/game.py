from datetime import datetime
from app.extensions import db

class GameCache(db.Model):
    """Model for caching ESPN API game data."""
    id = db.Column(db.Integer, primary_key=True)
    week = db.Column(db.Integer, nullable=False)
    season_type = db.Column(db.Integer, nullable=False, default=2)  # 1=preseason, 2=regular season, 3=postseason
    year = db.Column(db.Integer, nullable=False)
    game_id = db.Column(db.String(64), nullable=False, unique=True)
    data = db.Column(db.Text, nullable=False)
    last_updated = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(20), default='scheduled')
    winning_team = db.Column(db.String(64))
    home_team = db.Column(db.String(64), nullable=False)
    away_team = db.Column(db.String(64), nullable=False)
    home_team_abbrev = db.Column(db.String(10), nullable=False)
    away_team_abbrev = db.Column(db.String(10), nullable=False)
    home_score = db.Column(db.Integer, default=0)
    away_score = db.Column(db.Integer, default=0)
    start_time = db.Column(db.DateTime, nullable=False)
    is_mnf = db.Column(db.Boolean, default=False)
    venue_name = db.Column(db.String(128))
    venue_city = db.Column(db.String(64))
    venue_state = db.Column(db.String(2))
    spread = db.Column(db.Float)
    over_under = db.Column(db.Float)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def update_result(self, status, winning_team=None, home_score=None, away_score=None):
        """Update game result with new data."""
        self.status = status
        if winning_team:
            self.winning_team = winning_team
        if home_score is not None:
            self.home_score = home_score
        if away_score is not None:
            self.away_score = away_score
        self.last_updated = datetime.utcnow()

    def is_final(self):
        """Check if game is final."""
        if not self.status:
            return False
        status_lower = self.status.lower()
        
        # First check exact status matches
        if status_lower in {'final', 'final ot', 'status_final', 'post', 'postponed', 'canceled'}:
            return True
        
        # Then check if contains 'final'    
        if 'final' in status_lower:
            return True
            
        # Finally check if game has started and completed
        if self.start_time and datetime.utcnow() > self.start_time:
            if self.home_score is not None and self.away_score is not None:
                return not self.is_in_progress()
                
        return False

    def get_winner(self):
        """Get the winning team based on score."""
        if not self.is_final():
            return None
            
        # First check if we have a stored winner
        if self.winning_team:
            return self.winning_team
            
        # If no stored winner, determine by score
        if self.home_score is not None and self.away_score is not None:
            if self.home_score > self.away_score:
                return self.home_team
            elif self.away_score > self.home_score:
                return self.away_team
                
        return None

    def is_in_progress(self):
        """Check if game is in progress."""
        if not self.status:
            return False
            
        in_progress_statuses = {
            'in progress',
            'halftime',
            '1st quarter',
            '2nd quarter',
            '3rd quarter',
            '4th quarter',
            'overtime'
        }
        
        status_lower = self.status.lower()
        return (
            status_lower in in_progress_statuses or
            'quarter' in status_lower or
            'overtime' in status_lower
        )

    def get_total_points(self):
        """Get total points scored in the game."""
        if self.home_score is not None and self.away_score is not None:
            return self.home_score + self.away_score
        return None

    def is_mnf_game(self):
        """Check if this is a Monday Night Football game."""
        return bool(self.is_mnf)

    def __repr__(self):
        return f'<GameCache Week:{self.week} {self.away_team}@{self.home_team}>'

class Season(db.Model):
    """Model for tracking NFL seasons."""
    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    current_week = db.Column(db.Integer, nullable=False, default=1)
    season_type = db.Column(db.Integer, nullable=False, default=2)  # 1=preseason, 2=regular season, 3=postseason
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    archived_at = db.Column(db.DateTime)
    backup_path = db.Column(db.String(256))

    def archive(self, backup_path):
        """Archive the season."""
        self.is_active = False
        self.archived_at = datetime.utcnow()
        self.backup_path = backup_path

    def __repr__(self):
        return f'<Season {self.year} Week:{self.current_week}>'

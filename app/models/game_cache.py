from datetime import datetime
from sqlalchemy.dialects.sqlite import JSON
from app.extensions import db

class GameCache(db.Model):
    """Cache table for NFL game data from ESPN API"""
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.String(64), unique=True, nullable=False)
    week = db.Column(db.Integer, nullable=False)
    season_type = db.Column(db.Integer, nullable=False)  # 1=preseason, 2=regular season, 3=postseason
    year = db.Column(db.Integer, nullable=False)
    
    # Team information
    home_team = db.Column(db.String(64), nullable=False)
    home_team_abbrev = db.Column(db.String(8), nullable=False)
    away_team = db.Column(db.String(64), nullable=False)
    away_team_abbrev = db.Column(db.String(8), nullable=False)
    
    # Game details
    start_time = db.Column(db.DateTime, nullable=False)
    venue_name = db.Column(db.String(128))
    venue_city = db.Column(db.String(64))
    venue_state = db.Column(db.String(32))
    status = db.Column(db.String(32))  # scheduled, in_progress, final
    
    # Scores (null until game starts)
    home_score = db.Column(db.Integer)
    away_score = db.Column(db.Integer)
    
    # Betting information
    spread = db.Column(db.Float)  # Positive means home team is underdog
    over_under = db.Column(db.Float)
    
    # Store complete game data as JSON for flexibility
    data = db.Column(JSON)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<GameCache {self.away_team_abbrev}@{self.home_team_abbrev} Week {self.week}>'
        
    def to_dict(self):
        """Convert to dictionary format matching ESPN API response"""
        return {
            'game_id': self.game_id,
            'week': self.week,
            'season_type': self.season_type,
            'year': self.year,
            'date': self.start_time.isoformat() + 'Z',
            'status': self.status,
            'venue': {
                'name': self.venue_name,
                'city': self.venue_city,
                'state': self.venue_state
            },
            'home_team': {
                'display_name': self.home_team,
                'abbreviation': self.home_team_abbrev,
                'score': self.home_score
            },
            'away_team': {
                'display_name': self.away_team,
                'abbreviation': self.away_team_abbrev,
                'score': self.away_score
            },
            'odds': {
                'spread': self.spread,
                'over_under': self.over_under
            }
        }

from app import db

class Team(db.Model):
    __tablename__ = 'teams'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    abbreviation = db.Column(db.String(10), nullable=False, unique=True)
    conference = db.Column(db.String(10))  # AFC or NFC
    division = db.Column(db.String(10))    # North, South, East, West
    city = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    # Relationships
    home_games = db.relationship('Game', backref='home_team', foreign_keys='Game.home_team_id')
    away_games = db.relationship('Game', backref='away_team', foreign_keys='Game.away_team_id')

    def __repr__(self):
        return f'<Team {self.name} ({self.abbreviation})>'

    @property
    def full_name(self):
        return f'{self.city} {self.name}'

    @classmethod
    def get_by_abbreviation(cls, abbreviation):
        return cls.query.filter_by(abbreviation=abbreviation.upper()).first()

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'abbreviation': self.abbreviation,
            'conference': self.conference,
            'division': self.division,
            'city': self.city,
            'full_name': self.full_name
        }

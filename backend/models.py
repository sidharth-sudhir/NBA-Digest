from extensions import db

class Game(db.Model):
    gameId = db.Column(db.Integer, primary_key=True)
    homeTeamID = db.Column(db.Integer, db.ForeignKey('team.id'))  # Define ForeignKey for homeTeamID
    awayTeamID = db.Column(db.Integer, db.ForeignKey('team.id'))  # Define ForeignKey for awayTeamID
    home_team = db.relationship("Team", foreign_keys=[homeTeamID], backref="home_games")  # Define relationship for home_team
    away_team = db.relationship("Team", foreign_keys=[awayTeamID], backref="away_games")  # Define relationship for away_team
    home_team_score = db.Column(db.Integer)
    away_team_score = db.Column(db.Integer)
    game_date = db.Column(db.Date)
    game_status = db.Column(db.Integer)

class Player(db.Model):
    playerId = db.Column(db.Integer, primary_key=True)
    firstName = db.Column(db.String(100))
    lastName = db.Column(db.String(100))
    height = db.Column(db.Float)
    weight = db.Column(db.Float)

class PlayerStatistics(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('player.playerId'), nullable=False)
    game_id = db.Column(db.Integer, db.ForeignKey('game.gameId'), nullable=False)
    points = db.Column(db.Integer)
    assists = db.Column(db.Integer)
    rebounds = db.Column(db.Integer)
    fgm = db.Column(db.Integer)
    fga = db.Column(db.Integer)
    ftm = db.Column(db.Integer)
    fta = db.Column(db.Integer)
    fouls = db.Column(db.Integer)
    steals = db.Column(db.Integer)
    turnovers = db.Column(db.Integer)
    blocks = db.Column(db.Integer)
    plusMinus = db.Column(db.Integer)
    minutes = db.Column(db.String(10))

    # Define relationships with other models
    player = db.relationship('Player', backref=db.backref('player_statistics', lazy=True))
    game = db.relationship('Game', backref=db.backref('player_statistics', lazy=True))

class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    code = db.Column(db.String(10))
    logo = db.Column(db.String(1000))
    city = db.Column(db.String(100))
    nickname = db.Column(db.String(100))
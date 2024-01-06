import datetime
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
import requests
import os
from threading import Thread
from datetime import datetime

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('AWSURL')
db = SQLAlchemy(app)

class Game(db.Model):
    gameId = db.Column(db.Integer, primary_key=True)
    homeTeamID = db.Column(db.Integer, db.ForeignKey('team.id'))  # Define ForeignKey for homeTeamID
    awayTeamID = db.Column(db.Integer, db.ForeignKey('team.id'))  # Define ForeignKey for awayTeamID
    home_team = db.relationship("Team", foreign_keys=[homeTeamID], backref="home_games")  # Define relationship for home_team
    away_team = db.relationship("Team", foreign_keys=[awayTeamID], backref="away_games")  # Define relationship for away_team


class Player(db.Model):
    playerId = db.Column(db.Integer, primary_key=True)

class PlayerStatistics(db.Model):
    id = db.Column(db.Integer, primary_key=True)

class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    code = db.Column(db.String(10))
    logo = db.Column(db.String(1000))
    city = db.Column(db.String(100))
    nickname = db.Column(db.String(100))

with app.app_context():
    db.create_all()

@app.route('/populate_teams')
def populate_teams():
    with app.app_context():
        url = "https://api-nba-v1.p.rapidapi.com/teams"
        headers = {
            "X-RapidAPI-Key": os.environ.get('RAPID_API_KEY'),
            "X-RapidAPI-Host": "api-nba-v1.p.rapidapi.com"
        }

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            fetched_teams = response.json()["response"]
            try:
                for team in fetched_teams:
                    try:
                        existing_team = Team.query.filter_by(id=team['id']).first()
                        if not existing_team:
                            new_team = Team(
                                id=team['id'],
                                name=team['name'],
                                code=team["code"],
                                logo=team["logo"],
                                city=team["city"],
                                nickname=team["nickname"]
                            )
                            db.session.add(new_team)
                    except Exception as e:
                        db.session.rollback()
                        return f'Failed to store NBA Teams in Database: {str(e)}'
                db.session.commit()
                return 'Teams fetched and stored successfully'
            except Exception as e:
                db.session.rollback()
                return f'Failed to store NBA Teams in Database: {str(e)}'
        else:
            return 'Failed to fetch NBA Teams from API'

@app.route('/fetch-nba-scores')
def fetch_and_store_scores():
    url = "https://api-nba-v1.p.rapidapi.com/games?date=2024-01-06"
    headers = {
        "X-RapidAPI-Key": os.environ.get('RAPID_API_KEY'),
        "X-RapidAPI-Host": "api-nba-v1.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        fetched_scores = response.json()["response"]
        try:
            with app.app_context():
                for game in fetched_scores:
                    new_game_entry = Game(
                        gameId = game["id"],
                        homeTeamID = game["teams"]["home"]["id"],
                        awayTeamID = game["teams"]["visitors"]["id"]
                    )
                    db.session.add(new_game_entry)
                db.session.commit()
            return 'Scores fetched and stored successfully'
        except Exception as e:
            db.session.rollback()
            return 'Failed to store NBA Scores in Database'
    else:
        return 'Failed to fetch NBA scores from RAPID API'
    
@app.route('/get-nba-scores')
def get_nba_scores():
    latest_game_results = Game.query.order_by(Game.id.desc()).limit(100).all()
    if latest_game_results:
        scores = []
        for _ in latest_game_results:
            scores.append({
                'test': 'This is a test value foo!'
            })
        return jsonify(scores)
    else:
        return jsonify([])

if __name__ == '__main__':
    app.run(debug=True)

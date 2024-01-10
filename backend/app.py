import datetime
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
import requests
import os
from threading import Thread
from datetime import datetime
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
import json

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('AWSURL')
db = SQLAlchemy(app)

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

class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    code = db.Column(db.String(10))
    logo = db.Column(db.String(1000))
    city = db.Column(db.String(100))
    nickname = db.Column(db.String(100))

with app.app_context():
    db.create_all()

def populate_teams_and_players():
    with app.app_context():
        team_count = db.session.query(func.count(Team.id)).scalar()
        player_count = db.session.query(func.count(Player.playerId)).scalar()
        
        if team_count > 0 and player_count > 0:
            return 'Team and Player tables are already populated'

        # Process teams
        if not team_count:
            db.session.query(Team).delete()
            with open('teams.json', 'r') as teams_file:
                teams_data = json.load(teams_file)
                teams_to_insert = []

                for team in teams_data:
                    new_team = Team(
                        id = team['id'],
                        name = team['name'],
                        code = team["code"],
                        logo = team["logo"],
                        city = team["city"],
                        nickname = team["nickname"]
                    )
                    teams_to_insert.append(new_team)
                
                try:
                    if teams_to_insert:
                        db.session.bulk_save_objects(teams_to_insert)
                    else:
                        return 'No new teams to store'
                except IntegrityError as e:
                    db.session.rollback()
                    return f'Failed to store NBA Teams from JSON in Database: {str(e)}'

        # Process players
        if not player_count:
            db.session.query(Player).delete()
            with open('players.json', 'r') as players_file:
                players_data = json.load(players_file)
                players_to_insert = []
                added_player_ids = set()

                for team_id, team_players in players_data.items():
                    for player_data in team_players:
                        if player_data['id'] in added_player_ids:
                            continue
                        new_player = Player(
                            playerId = player_data['id'],
                            firstName = player_data['firstname'],
                            lastName = player_data['lastname'],
                            weight = player_data['weight']['kilograms'],
                            height = player_data['height']['meters']
                        )
                        players_to_insert.append(new_player)
                        added_player_ids.add(player_data['id'])
                try:
                    if players_to_insert:
                        db.session.bulk_save_objects(players_to_insert)
                    else:
                        return 'No new players to store'
                except IntegrityError as e:
                    db.session.rollback()
                    return f'Failed to store NBA Players from JSON in Database: {str(e)}'

        # Commit changes only after processing both teams and players
        db.session.commit()
        return 'Teams and Players fetched and stored successfully from JSON'


@app.route('/fetch-nba-scores')
def fetch_and_store_scores():
    url = "https://api-nba-v1.p.rapidapi.com/games?date=2024-01-08"
    headers = {
        "X-RapidAPI-Key": os.environ.get('RAPID_API_KEY'),
        "X-RapidAPI-Host": "api-nba-v1.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        fetched_scores = response.json()["response"]
        # Collect existing games to update
        existing_games = {}
        for game in fetched_scores:
            existing_game = Game.query.filter_by(gameId=game["id"]).first()
            if existing_game and existing_game.game_status != '3':
                # If the game exists and was not finished, update its details
                existing_games[game["id"]] = existing_game

        # Update existing games
        for game_id, existing_game in existing_games.items():
            # Find the corresponding fetched game by ID
            fetched_game = next((g for g in fetched_scores if g["id"] == game_id), None)
            if fetched_game:
                existing_game.home_team_score = fetched_game["scores"]["home"]["points"]
                existing_game.away_team_score = fetched_game["scores"]["visitors"]["points"]
                existing_game.game_status = fetched_game["status"]["short"]

        # Add new games to bulk save
        new_games_to_insert = [
            Game(
                gameId=game["id"],
                homeTeamID=game["teams"]["home"]["id"],
                awayTeamID=game["teams"]["visitors"]["id"],
                game_date=datetime.strptime(game["date"]["start"], "%Y-%m-%dT%H:%M:%S.%fZ"),
                home_team_score=game["scores"]["home"]["points"],
                away_team_score=game["scores"]["visitors"]["points"],
                game_status=game["status"]["short"]
            ) for game in fetched_scores if game["id"] not in existing_games
        ]

        try:
            # Bulk save new games
            if new_games_to_insert:
                db.session.bulk_save_objects(new_games_to_insert)
            db.session.commit()
            return 'Scores fetched and stored successfully'
        except IntegrityError as e:
            db.session.rollback()
            return f'Failed to store NBA Scores in Database: {str(e)}'

    else:
        return 'Failed to fetch NBA scores from RAPID API'
    
@app.route('/get-nba-scores/<date>')
def get_nba_scores(date):
    try:
        target_date = datetime.strptime(date, '%Y-%m-%d').date()
        
        games_on_date = Game.query \
            .filter(Game.game_date == target_date) \
            .options(joinedload(Game.home_team), joinedload(Game.away_team)) \
            .order_by(Game.gameId.desc()) \
            .limit(100) \
            .all()
        
        if games_on_date:
            scores = []
            for game in games_on_date:
                home_team = game.home_team
                away_team = game.away_team
                
                game_data = {
                    'HOME': home_team.name,
                    'AWAY': away_team.name,
                    'STATUS': 'Not Started' if game.game_status == 1 else ('Live' if game.game_status == 2 else 'Finished')
                }

                # Conditionally add scores if the game status is 2 or 3
                if game.game_status in [2, 3]:
                    game_data['HOME_SCORE'] = game.home_team_score
                    game_data['AWAY_SCORE'] = game.away_team_score
                
                scores.append(game_data)

            return jsonify(scores)
        else:
            return jsonify([])

    except ValueError:
        return 'Invalid date format. Please use YYYY-MM-DD.'


if __name__ == '__main__':
    populate_teams_and_players()
    app.run(debug=True)

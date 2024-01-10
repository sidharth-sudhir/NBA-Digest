from flask import jsonify, Blueprint
import requests
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload
from models import Game  # Import your Game model here
from extensions import db
from datetime import datetime
import os

app = Blueprint('app', __name__)  

@app.route('/fetch-nba-scores')
def fetch_and_store_scores():
    url = "https://api-nba-v1.p.rapidapi.com/games?date=2024-01-10"
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
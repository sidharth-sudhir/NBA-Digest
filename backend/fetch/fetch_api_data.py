import requests
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload
from models import Game  # Import your Game model here
from extensions import db
import os

def fetch_and_store_scores(date):
    target_date = datetime.strptime(date, '%Y-%m-%d').date()

    url = f"https://api-nba-v1.p.rapidapi.com/games?date={target_date}"
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
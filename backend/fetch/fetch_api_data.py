import requests
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload
from models import Game, PlayerStatistics  # Import your Game model here
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
        except IntegrityError as e:
            db.session.rollback()
            return f'Failed to store NBA Scores in Database: {str(e)}'
        
        for game in fetched_scores:
            fetch_and_store_player_stats(game["id"])
            
        return 'Scores fetched and stored successfully'


    else:
        return 'Failed to fetch NBA scores from RAPID API'


def fetch_and_store_player_stats(game_id):
    url = "https://api-nba-v1.p.rapidapi.com/players/statistics"
    headers = {
        "X-RapidAPI-Key": os.environ.get('RAPID_API_KEY'),
        "X-RapidAPI-Host": "api-nba-v1.p.rapidapi.com"
    }
    params = {"game": str(game_id)}

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        player_stats_data = response.json()["response"]
        existing_stats = {}

        for player_stat in player_stats_data:
            player_id = player_stat["player"]["id"]

            existing_stat = PlayerStatistics.query.filter_by(player_id = player_id, game_id = game_id).first()
            if existing_stat:
                existing_stats[player_id] = existing_stat
        
        for player_id, existing_stat in existing_stats.items():
            fetched_stat = next((s for s in player_stats_data if s["player"]["id"] == player_id), None)
            if fetched_stat:
                existing_stat.points = fetched_stat["points"]
                existing_stat.assists = fetched_stat["assists"]
                existing_stat.rebounds = fetched_stat["totReb"]
                existing_stat.fgm = fetched_stat["fgm"]
                existing_stat.fga = fetched_stat["fga"]
                existing_stat.ftm = fetched_stat["ftm"]
                existing_stat.fta = fetched_stat["fta"]
                existing_stat.fouls = fetched_stat["pFouls"]
                existing_stat.steals = fetched_stat["steals"]
                existing_stat.turnovers = fetched_stat["turnovers"]
                existing_stat.blocks = fetched_stat["blocks"]
                existing_stat.plusMinus = fetched_stat["plusMinus"]
                existing_stat.minutes = fetched_stat["min"]
        
        new_stats_to_insert = [
            PlayerStatistics(
                player_id = stat["player"]["id"],
                game_id = game_id,
                points = stat["points"],
                assists = stat["assists"],
                rebounds = stat["totReb"],
                fgm = stat["fgm"],
                fga = stat["fga"],
                ftm = stat["ftm"],
                fta = stat["fta"],
                fouls = stat["pFouls"],
                steals = stat["steals"],
                turnovers = stat["turnovers"],
                blocks = stat["blocks"],
                plusMinus = stat["plusMinus"],
                minutes = stat["min"]
            ) for stat in player_stats_data if stat["player"]["id"] not in existing_stats
        ]

        
        try:
            # Bulk save new games
            if new_stats_to_insert:
                db.session.bulk_save_objects(new_stats_to_insert)
            db.session.commit()
            return 'Player stats fetched and stored successfully'
        except IntegrityError as e:
            print("we are rolling back with e")
            print(e)
            db.session.rollback()
            return f'Failed to store Player Stats in Database: {str(e)}'

    else:
        return 'Failed to fetch Player stats from RAPID API'

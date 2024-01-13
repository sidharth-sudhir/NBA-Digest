from flask import jsonify
from datetime import datetime
from sqlalchemy.orm import joinedload
from models import Game, PlayerStatistics

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
                    'ID': game.gameId,
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


def get_player_stats(game_id):
    player_stats = (
        PlayerStatistics.query
        .options(joinedload(PlayerStatistics.player))  # Eager loading of player data
        .filter_by(game_id=game_id)
        .all()
    )

    if player_stats:
        stats = []
        for player_stat in player_stats:
            player_data = {
                'NAME': f"{player_stat.player.firstName} {player_stat.player.lastName}",
                'POINTS': player_stat.points,
                'REBOUNDS': player_stat.rebounds,
                'ASSISTS': player_stat.assists
            }
            stats.append(player_data)
        return jsonify(stats)
    else:
        return jsonify([])

import json
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from extensions import db
from models import Player, Team


def initialize_teams_and_players(app) -> bool:
    with app.app_context():
        team_count = db.session.query(func.count(Team.id)).scalar()
        player_count = db.session.query(func.count(Player.playerId)).scalar()
        
        if team_count > 0 and player_count > 0:
            print('Team and Player tables are already populated')
            return True

        if not team_count:
            db.session.query(Team).delete()
            with open('data/teams.json', 'r') as teams_file:
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
                        return True
                except IntegrityError as e:
                    db.session.rollback()
                    print(f'Failed to store NBA Teams from JSON in Database: {str(e)}')
                    return False

        # Process players
        if not player_count:
            db.session.query(Player).delete()
            with open('data/players.json', 'r') as players_file:
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
                        return True
                except IntegrityError as e:
                    db.session.rollback()
                    print(f'Failed to store NBA Players from JSON in Database: {str(e)}')
                    return False

        # Commit changes only after processing both teams and players
        db.session.commit()
        print('Teams and Players fetched and stored successfully from JSON')
        return True
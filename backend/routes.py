from flask import Blueprint
from fetch.fetch_api_data import fetch_and_store_scores
from fetch.fetch_db_data import get_nba_scores, get_player_stats

app = Blueprint('app', __name__)  

@app.route('/fetch-nba-scores/<date>')
def fetch_nba_scores_route(date):
    return fetch_and_store_scores(date)
    
@app.route('/get-nba-scores/<date>')
def get_nba_scores_route(date):
    return get_nba_scores(date)

@app.route('/get-box-score/<gameID>')
def get_box_score(gameID):
    return get_player_stats(gameID)
from flask import Blueprint
from fetch.fetch_api_data import fetch_and_store_scores
from fetch.fetch_db_data import get_nba_scores

app = Blueprint('app', __name__)  

@app.route('/fetch-nba-scores/<date>')
def fetch_nba_scores_route(date):
    return fetch_and_store_scores(date)
    
@app.route('/get-nba-scores/<date>')
def get_nba_scores_route(date):
    return get_nba_scores(date)
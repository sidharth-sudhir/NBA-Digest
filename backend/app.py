from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
import requests
import os
from threading import Thread

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('AWSURL')
db = SQLAlchemy(app)

class NBAScore(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.JSON)

with app.app_context():
    db.create_all()

@app.route('/fetch-nba-scores')
def fetch_and_store_scores():
    url = "https://api-nba-v1.p.rapidapi.com/games?date=2024-01-04"
    headers = {
        "X-RapidAPI-Key": os.environ.get('RAPID_API_KEY'),
        "X-RapidAPI-Host": "api-nba-v1.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        fetched_scores = response.json()
        new_nba_score = NBAScore(data=fetched_scores)
        
        try:
            with app.app_context():
                db.session.add(new_nba_score)
                db.session.commit()
            return 'Scores fetched and stored successfully'
        except Exception as e:
            db.session.rollback()  # Rollback changes on exception
            return 'Failed to fetch NBA scores'
    else:
        return 'Failed to fetch NBA scores'

@app.route('/get-nba-scores')
def get_nba_scores():
    latest_scores = NBAScore.query.order_by(NBAScore.id.desc()).first()
    if latest_scores:
        return jsonify(latest_scores.data)
    else:
        return jsonify({})  # No scores available yet

if __name__ == '__main__':
    app.run(debug=True)

from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Sample mock data
mock_scores = [
    {'id': 1, 'homeTeam': 'Warriors', 'awayTeam': 'Lakers', 'homeScore': 120, 'awayScore': 98},
    {'id': 2, 'homeTeam': 'Raptors', 'awayTeam': '76ers', 'homeScore': 115, 'awayScore': 110},
]

# Flask route to serve mock scores data
@app.route('/api/scores')
def get_scores():
    return jsonify(mock_scores)

# Start the server
if __name__ == '__main__':
    app.run(debug=True)  # For development, use debug=True

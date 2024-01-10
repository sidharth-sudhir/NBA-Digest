import datetime
import requests
import os
import json
from initialize_db import initialize_teams_and_players
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from threading import Thread
from datetime import datetime
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from extensions import db
from routes import app as routes_blueprint

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('AWSURL')
db.init_app(app)

app.register_blueprint(routes_blueprint)

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    if initialize_teams_and_players(app):
        app.run(debug = True)

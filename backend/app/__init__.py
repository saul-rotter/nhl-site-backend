"""Flask App Factory"""

import os
from flask import Flask, jsonify, url_for
from database import Database, SQLALCHEMY_DATABASE_URL
from database.models import game, team, event, player, shift
import uvicorn
from fastapi import FastAPI


# type: ignore
from flask_cors import CORS

db = Database()


def create_app(test_config=None):

    app = Flask(__name__, instance_relative_config=True)
    # configuration and database location
    app.config.from_mapping(
        SECRET_KEY="dev",
        DATABASE=SQLALCHEMY_DATABASE_URL,
    )
    CORS(app)
    db.init_app(app)

    @app.after_request
    def remove(response):
        db.remove_session()
        return response

    @app.before_request
    def start():
        db.start_session()

    from app.blueprints import init_blueprints

    init_blueprints(app)
    return app


gunicorn_app = create_app()

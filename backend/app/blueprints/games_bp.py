from database.models.team import Team
from database.models.game import Game
from app import db
from sqlalchemy import select
from sqlalchemy.orm import load_only, selectinload
from flask import Blueprint, jsonify
from app.blueprints.events import get_events_for_game
from fastapi import APIRouter

router = APIRouter(
    prefix="/games",
    tags=["games"],
    responses={404: {"description": "Not found"}},
)
games_bp = Blueprint("games", __name__)


def get_all_games():
    session = db.session()
    games = session.scalars(
        select(Game).options(
            selectinload(Game.homeTeam).load_only(Team.name),
            selectinload(Game.awayTeam).load_only(Team.name),
        )
    ).all()

    return games


def get_all_games_with_team():
    session = db.session()
    game_objs = session.scalars(
        select(Game).options(
            selectinload(Game.homeTeam).load_only(Team.name),
            selectinload(Game.awayTeam).load_only(Team.name),
        )
    ).all()
    games = []
    for game in game_objs:
        game_dict = game.to_dict()
        game_dict["homeTeamName"] = game.homeTeam.name
        game_dict["awayTeamName"] = game.awayTeam.name
        games.append(game_dict)

    return games


def load_game(game_id):
    session = db.session()
    game = session.get(
        Game,
        game_id,
        options=[
            selectinload(Game.homeTeam).load_only(Team.name),
            selectinload(Game.awayTeam).load_only(Team.name),
        ],
    )
    return game


def get_dict(game):
    game_dict = game.to_dict()
    game_dict["homeTeamName"] = game.homeTeam.name
    game_dict["awayTeamName"] = game.awayTeam.name
    return game_dict


@games_bp.route("/")
def show_games():
    games = get_all_games()
    game_list = []
    events = []
    for game in games:
        game_dict = get_dict(game)
        events = events + get_events_for_game(game)
        game_list.append(game_dict)
    return jsonify({'events': events})


@games_bp.route("/<int:id>/")
def show_game(id):
    game = load_game(id)
    game_dict = get_dict(game)
    events = get_events_for_game(game)
    return jsonify({'game': game_dict, 'events': events})

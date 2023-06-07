from database.models.team import Team
from database.models.game import Game
from app import db
from sqlalchemy import select
from sqlalchemy.orm import load_only, selectinload
from flask import Blueprint, jsonify
from app.blueprints.events import get_events_for_game
games_bp = Blueprint("games", __name__)


def get_all_games():
    session = db.session()
    games = session.scalars(
        select(Game).options(
            load_only(Game.id)
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
    game_dict['homeTeam'] = {}
    game_dict['awayTeam'] = {}
    game_dict['homeTeam']['name'] = game.homeTeam.name
    game_dict['homeTeam']['id'] = game.homeTeamId
    game_dict['homeTeam']['coach'] = game.homeCoach
    game_dict['homeTeam']['score'] = game.homeScore
    game_dict['awayTeam']['id'] = game.awayTeamId
    game_dict['awayTeam']['name'] = game.awayTeam.name
    game_dict['awayTeam']['coach'] = game.awayCoach
    game_dict['awayTeam']['score'] = game.awayScore
    return game_dict


@games_bp.route("/")
def show_games():
    games = get_all_games()
    return jsonify({'games': games})


@games_bp.route("/<int:id>/")
def show_game(id):
    game = load_game(id)
    game_dict = get_dict(game)
    events = get_events_for_game(game)
    return jsonify({'game': game_dict, 'events': events})

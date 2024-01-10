from flask import request
from flask_restx import Namespace, Resource, fields, reqparse
from database.models.team import Team
from database.models.game import Game
from app import db
from sqlalchemy import select
from sqlalchemy.orm import load_only, selectinload
from app.blueprints.events import get_events_for_game
from app.blueprints.events_ns import event_model
from app.blueprints.teams_ns import team_model
import functools
# Create a Flask-RESTX Namespace
games_ns = Namespace("games", description="Game related operations")

game_model = games_ns.model("Games", {
    "id": fields.Integer(),
    "homeTeam": fields.Nested(team_model),
    "awayTeam": fields.Nested(team_model),
    "events": fields.List(fields.Nested(event_model)),
})

@games_ns.route("/")
class GamesResource(Resource):
    @games_ns.marshal_list_with(game_model, skip_none=True)
    def get(self):
        games = get_all_games_with_team()
        if not games:
            games_ns.abort(404, "No Games Found")

        return games

@games_ns.route("/<int:id>")
class GameResource(Resource):
    @games_ns.marshal_with(game_model, skip_none=True)
    def get(self, id):
        page = request.args.get('page', None, type=int)
        limit = 25
        session = db.session()
        game = session.get(
            Game,
            id,
            options=[
                selectinload(Game.homeTeam).load_only(Team.name),
                selectinload(Game.awayTeam).load_only(Team.name),
            ],
        )

        if not game:
            games_ns.abort(404, "Game not found")

        game_dict = get_dict(game)
        events = get_events_for_game(game)
        if (not(page is None)) :
            events = events[(page * limit) : (page * limit) + limit]
        print(game_dict)
        game_dict["events"] =  events
           

        return game_dict

def get_all_games_with_team():
    session = db.session()
    game_objs = session.scalars(
        select(Game).options(
            selectinload(Game.homeTeam).load_only(Team.name),
            selectinload(Game.awayTeam).load_only(Team.name),
        )
    ).all()
    return [get_dict(game) for game in game_objs]

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
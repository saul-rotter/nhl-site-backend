from flask_restx import Api, Resource
from app.blueprints.games_ns import games_ns
from app.blueprints.teams_ns import teams_ns
from app.blueprints.players_ns import players_ns
from app.blueprints.events_ns import events_ns

api = Api(
    title="Zoo API",
    version="1.0",
    description="A simple demo API",
)

api.add_namespace(teams_ns)
api.add_namespace(players_ns)
api.add_namespace(events_ns)
api.add_namespace(games_ns)


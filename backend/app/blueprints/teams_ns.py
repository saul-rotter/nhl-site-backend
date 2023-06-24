from database.models.team import Team
from sqlalchemy import select, func
from app import db
from flask_restx import Namespace, Resource, fields
from app.blueprints.players_ns import player_model

# Create a Flask-RESTX Namespace
teams_ns = Namespace("teams", description="Team related operations")

# Define a model for the team
team_model = teams_ns.model("Team", {
    "id": fields.Integer(),
    "name": fields.String(),
    "coach": fields.String(skip_none=True),
    "score": fields.String(skip_none=True),
    "roster": fields.List(fields.Nested(player_model)),
    "city": fields.String(skip_none=True),
    "abbrev": fields.String(skip_none=True),
    "games": fields.List(fields.Raw())
})

@teams_ns.route("/")
class TeamsResource(Resource):
    @teams_ns.marshal_list_with(team_model, skip_none=True)
    def get(self):
        session = db.session()
        team_objs = session.scalars(
            select(Team)
        ).all()
        return [team.to_dict() for team in team_objs]
    

@teams_ns.route("/<int:id>/")
class TeamResource(Resource):
    @teams_ns.marshal_with(team_model)
    def get(self, id):
        session = db.session()
        team = session.get(Team, id)
        if team is None:
            return ""
        team_dict = team.to_dict()
        team_dict["roster"] = []
        for player in team.roster:
            team_dict["roster"].append(player.basePlayerDict)
        team_dict["games"] = [game for game in team.games]
        return team_dict
from database.models.team import Team
from sqlalchemy import select
from sqlalchemy import func
from app import db
from flask import Blueprint, jsonify

teams_bp = Blueprint("teams", __name__)


@teams_bp.route("/<int:id>/")
def load_team(id):
    session = db.session()
    team = session.get(
        Team,
        id,
    )
    if team is None:
        return ""
    team_dict = team.to_dict()
    team_dict["roster"] = {}
    for player in team.roster:
        team_dict["roster"][player.id] = {}
        team_dict["roster"][player.id]["name"] = player.name
        team_dict["roster"][player.id]["postion"] = player.position
        team_dict["roster"][player.id]["number"] = player.number
    return jsonify(team_dict)


def fetch_id_from_name(name):
    session = db.session()
    team_id = session.execute(
        select(Team.id).where(func.lower(Team.name) == func.lower(name))
    ).first()
    if team_id is None:
        return "n/a"
    return team_id.id


def fetch_id_from_abbrev(abbrev):
    session = db.session()
    team_id = session.execute(
        select(Team.id).where(Team.abbrev == abbrev)).first()
    if team_id is None:
        return "n/a"
    return team_id.id

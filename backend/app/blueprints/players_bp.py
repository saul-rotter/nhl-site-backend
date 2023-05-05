from database.models.player import Player
from database.models.event import Event
from app import db
from sqlalchemy import select
from flask import Blueprint, jsonify
from sqlalchemy.orm import load_only, selectinload
from database.models.team import Team
from fastapi import APIRouter

router = APIRouter(
    prefix="/items",
    tags=["items"],
    responses={404: {"description": "Not found"}},
)
players_bp = Blueprint("players", __name__)


@players_bp.route("/<int:id>/")
def load_player(id):
    session = db.session()
    player = session.get(Player, id, options=[
                         selectinload(Player.team).load_only(Team.name),])
    if player is None:
        return ""
    player_dict = player.to_dict()
    player_dict["events"] = load_player_events(player)
    player_dict["shifts"] = {}
    for shift in player.shifts:
        if shift.gameId not in player_dict["shifts"]:
            player_dict["shifts"][shift.gameId] = []
        player_dict["shifts"][shift.gameId].append(shift.to_dict())
    return jsonify(player_dict)


def load_team_name(team):
    return team.name


def load_player_role(event, id):
    role = ''
    match id:
        case event.playerId:
            match event.event:
                case 'Zone Entry':
                    role = 'Entry By'
                case 'Zone Exit':
                    role = 'Exit By'
                case 'Shot', 'Goal', 'Missed Shot', 'Blocked Shot':
                    role = 'Shooter'
                case 'Faceoff':
                    role = 'Winner'
                case 'Takeaway':
                    role = 'Takeaway'
                case 'Giveaway':
                    role = 'Giveaway'
                case 'Penalty':
                    role = 'Penalty On'
                case 'Hit':
                    role = 'Hitter'
        case event.oppPlayerId:
            match event.event:
                case 'Zone Entry':
                    role = 'Defender'
                case 'Zone Exit':
                    role = 'Forecheck'
                case 'Shot', 'Goal', 'Missed Shot', 'Blocked Shot':
                    role = 'Goalie'
                case 'Faceoff':
                    role = 'Loser'

                case 'Penalty':
                    role = 'Drew Penalty'

                case 'Hit':
                    role = 'Hittee'

        case event.recoveryId:
            role = "Dump Recover"

        case event.primaryAssistId:
            role = "First Assist"

        case event.secondaryAssistId:
            role = "Second Assist"

        case event.tertiaryAssistId:
            role = "Third Assist"

        case event.retrievalId:
            role = "Puck Retrieval"
    return role


def load_on_ice_events(shift):
    return


def load_player_events(player):
    events = []
    for event in player.events:
        event_dict = event.to_dict()
        event_dict['role'] = load_player_role(event, player.id)
        event_dict['oppTeam'] = (event.oppTeam.name if not (
            event.oppTeam is None) else None)
        event_dict['oppPlayer'] = (event.oppPlayer.name if not (
            event.oppPlayer is None) else None)
        event_dict['recovery'] = (event.recovery.name if not (
            event.recovery is None) else None)
        event_dict['retrieval'] = (event.retrieval.name if not (
            event.retrieval is None) else None)
        event_dict['primaryAssist'] = (event.primaryAssist.name if not (
            event.primaryAssist is None) else None)
        event_dict['secondaryAssist'] = (
            event.secondaryAssist.name if not (event.secondaryAssist is None) else None)
        event_dict['tertiaryAssist'] = (
            event.tertiaryAssist.name if not (event.tertiaryAssist is None) else None)
        events.append(event_dict)
    return events


def fetch_id_from_team_number(team, number):
    session = db.session()
    player_id = session.execute(
        select(Player.id).where(Player.teamId == team, Player.number == number)
    ).first()
    if player_id is None:
        return "n/a"
    return player_id.id

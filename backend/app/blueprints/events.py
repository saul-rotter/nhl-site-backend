from app import db
from database.models.game import Game
from database.models.shift import Shift
from operator import concat


def get_events_for_game(game):
    if not isinstance(game, Game):
        session = db.session()
        game = session.get(
            Game,
            game,
        )
        if game is None:
            return []
    events = game.events
    event_list = []
    for event in events:
        if event.teamId is None:
            continue
        shifts = Shift.get_shift_from_event(event)
        event_list.append(get_dict(event, shifts))
    return event_list


def get_dict(event, shifts):
    event_dict = event.dict
    team_on_ice = []
    opp_team_on_ice = []
    for shift in shifts:
        if event.teamId is None or shift.player.position == 'G':
            continue
        shift.to_dict()
        if shift.teamId == event.teamId:
            team_on_ice.append(shift.player.basePlayerDict)
        else:
            opp_team_on_ice.append(shift.player.basePlayerDict)
    event_dict['team_on_ice'] = team_on_ice
    event_dict['opp_team_on_ice'] = opp_team_on_ice
    return event_dict

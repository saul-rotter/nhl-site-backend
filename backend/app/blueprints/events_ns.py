from flask_restx import fields, Model, Namespace
from app.blueprints.players_ns import player_model
from app.blueprints.teams_ns import team_model
events_ns = Namespace("events", description="Team related operations")

event_model = events_ns.model('Event', {
    'period': fields.String(required=True, description='Period'),
    'game_time': fields.String(required=True, description='Game Time'),
    'home_score': fields.Integer(required=True, description='Home Score'),
    'away_score': fields.Integer(required=True, description='Away Score'),
    'strength': fields.String(required=True, description='Strength'),
    'event': fields.String(required=True, description='Event'),
    'event_type': fields.String(required=True, description='Event Type'),
    'team': fields.Nested(team_model,required=True, description='Team ID'),
    'player': fields.Nested(player_model, required=True, description='Player'),
    'oppTeam': fields.Nested(team_model, required=True, description='Opposing Team ID'),
    'oppPlayer': fields.Nested(player_model, required=True, description='Opposing Player'),
    'team_on_ice': fields.List(fields.Nested(player_model), required=True, description='Team on Ice'),
    'opp_team_on_ice': fields.List(fields.Nested(player_model), required=True, description='Opposing Team on Ice'),
    'play_type': fields.String(required=True, description='Play Type'),
    'chance': fields.String(required=True, description='Chance'),
    'lane': fields.String(required=True, description='Lane'),
    'oddman': fields.String(required=True, description='Oddman'),
    'primary_assist': fields.Nested(player_model, required=True, description='Primary Assist'),
    'primary_lane': fields.String(required=True, description='Primary Lane'),
    'primary_pass_type': fields.String(required=True, description='Primary Pass Type'),
    'primary_zone': fields.String(required=True, description='Primary Zone'),
    'secondary_assist': fields.Nested(player_model, required=True, description='Secondary Assist'),
    'secondary_lane': fields.String(required=True, description='Secondary Lane'),
    'secondary_pass_type': fields.String(required=True, description='Secondary Pass Type'),
    'secondary_zone': fields.String(required=True, description='Secondary Zone'),
    'tertiary_assist': fields.Nested(player_model, required=True, description='Tertiary Assist'),
    'tertiary_lane': fields.String(required=True, description='Tertiary Lane'),
    'tertiary_pass_type': fields.String(required=True, description='Tertiary Pass Type'),
    'tertiary_zone': fields.String(required=True, description='Tertiary Zone'),
    'recovery': fields.Nested(player_model, required=True, description='Recovery'),
    'retrieval': fields.Nested(player_model, required=True, description='Retrieval')
})

from database.models.player import Player
from database.models.event import Event
from app import db
from sqlalchemy import select
from flask import jsonify
from flask_restx import Namespace, Resource
from sqlalchemy.orm import load_only, selectinload
from database.models.team import Team
from flask_restx import Namespace, Resource, fields, Model

players_ns = Namespace("players")

player_model = players_ns.model('Player', {
    'id': fields.Integer(required=True, description='Player ID'),
    'name': fields.String(required=True, description='Player Name'),
    'number': fields.Integer(required=True, description='Player Number'),
    'teamId': fields.Integer(required=True, description='Team ID'),
    'position': fields.String(required=True, description='Player Position'),
    'handedness': fields.String(required=True, description='Player Hand')
})
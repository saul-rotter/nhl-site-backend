from sqlalchemy import select, Integer, String, ForeignKey, func
from sqlalchemy.orm import load_only, selectinload, mapped_column, relationship
from flask import Blueprint, jsonify
from database import Base, DictMixIn

teams_bp = Blueprint("teams", __name__)


class Team(Base, DictMixIn):
    __tablename__ = "teams"

    id = mapped_column(Integer, primary_key=True, index=True)
    abbrev = mapped_column(String)
    city = mapped_column(String)
    name = mapped_column(String)

    games = relationship(
        "Game",
        primaryjoin="or_(Team.id==Game.homeTeamId, " "Team.id==Game.awayTeamId,) ",
    )
    roster = relationship("Player", back_populates="team")

from .team import Team
from sqlalchemy import select, Integer, String, ForeignKey
from sqlalchemy.orm import load_only, selectinload, mapped_column, relationship
from flask import Blueprint, jsonify
from database import Base, DictMixIn

games_bp = Blueprint("games", __name__)


class Game(Base, DictMixIn):
    __tablename__ = "games"

    id = mapped_column(Integer, primary_key=True, index=True)
    season = mapped_column(Integer)
    startTime = mapped_column(String(50))
    homeTeamId = mapped_column(Integer, ForeignKey("teams.id"))
    homeCoach = mapped_column(String(50))
    homeScore = mapped_column(Integer)
    awayTeamId = mapped_column(Integer, ForeignKey("teams.id"))
    awayCoach = mapped_column(String(50))
    awayScore = mapped_column(Integer)

    homeTeam = relationship("Team", foreign_keys=[
                            homeTeamId], back_populates="games")

    awayTeam = relationship("Team", foreign_keys=[
                            awayTeamId], back_populates="games")

    events = relationship("Event", back_populates='game')

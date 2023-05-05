from sqlalchemy import Integer, String, ForeignKey
from database import Base, DictMixIn
from sqlalchemy.orm import mapped_column, relationship, load_only, selectinload
from sqlalchemy import inspect
from sqlalchemy import select
from database.models.player import Player
from database.models.team import Team


class Shift(Base, DictMixIn):
    __tablename__ = "shifts"

    gameId = mapped_column(Integer, ForeignKey("games.id"))
    playerId = mapped_column(Integer, ForeignKey(
        "players.id"), primary_key=True)
    shiftNumber = mapped_column(Integer, primary_key=True)
    teamId = mapped_column(Integer, ForeignKey("teams.id"))
    shiftStart = mapped_column(Integer)
    shiftEnd = mapped_column(Integer)

    player = relationship("Player")
    team = relationship("Team")
    game = relationship("Game")

    @classmethod
    def get_shift_from_event(cls, event):
        session = inspect(event).session
        statement = select(Shift).where((Shift.gameId == event.gameId) & (
            Shift.shiftStart <= event.seconds) & (Shift.shiftEnd > event.seconds)
        ).options(
            selectinload(Shift.team).load_only(Team.name),
            selectinload(Shift.player).load_only(Player.name)
        )
        shifts = session.scalars(
            statement
        ).all()
        return [] if shifts is None else shifts

    #   order_by="[scan.Port.param1, scan.Port.param2, scan.Port.param3]")

from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.orm import mapped_column, relationship
from database import Base, DictMixIn
from sqlalchemy.ext.hybrid import hybrid_property


class Player(Base, DictMixIn):
    __tablename__ = "players"

    id = mapped_column(Integer, primary_key=True, index=True)
    name = mapped_column(String)
    number = mapped_column(Integer)
    teamId = mapped_column(Integer, ForeignKey("teams.id"))
    position = mapped_column(String)
    hand = mapped_column(String)

    team = relationship("Team", back_populates="roster")

    events = relationship(
        "Event",
        primaryjoin="or_(Player.id==Event.playerId, "
        "Player.id==Event.oppPlayerId, "
        "Player.id==Event.recoveryId, "
        "Player.id==Event.retrievalId, "
        "Player.id==Event.primaryAssistId,"
        "Player.id==Event.secondaryAssistId,"
        "Player.id==Event.tertiaryAssistId,)",
    )

    @hybrid_property
    def basePlayerDict(self):
        return {
            'id': self.id,
            'name': self.name,
            'postion': self.position,
        }

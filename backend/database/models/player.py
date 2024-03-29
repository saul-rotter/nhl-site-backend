from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.orm import mapped_column, relationship
from database import Base, DictMixIn
from sqlalchemy.ext.hybrid import hybrid_property


class Player(Base, DictMixIn):
    __tablename__ = "players"

    id = mapped_column(Integer, primary_key=True, index=True, nullable=True)
    name = mapped_column(String(50))
    number = mapped_column(Integer)
    teamId = mapped_column(Integer, ForeignKey("teams.id"))
    position = mapped_column(String(50))
    hand = mapped_column(String(50))

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
            'position': self.position,
            'teamId': self.teamId,
            'handedness':self.hand,
            'number': self.number,
        }

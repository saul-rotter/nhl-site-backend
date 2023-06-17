from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.orm import mapped_column, relationship
from sqlalchemy.ext.hybrid import hybrid_property
from database import Base, DictMixIn
from sqlalchemy import inspect
from sqlalchemy import select


class Event(Base, DictMixIn):
    __tablename__ = "events"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    gameId = mapped_column(Integer, ForeignKey("games.id"))
    period = mapped_column(Integer)
    time = mapped_column(String(50))
    seconds = mapped_column(Integer)
    dateTime = mapped_column(String(50))
    homeScore = mapped_column(Integer)
    awayScore = mapped_column(Integer)
    event = mapped_column(String(50))
    type = mapped_column(String(50))
    teamId = mapped_column(Integer, ForeignKey("teams.id"))
    playerId = mapped_column(Integer, ForeignKey("players.id"))
    oppTeamId = mapped_column(Integer, ForeignKey("teams.id"))
    oppPlayerId = mapped_column(Integer, ForeignKey("players.id"))
    lane = mapped_column(String(50))
    recoveryId = mapped_column(Integer, ForeignKey("players.id"))
    chance = mapped_column(String(50))
    retrievalId = mapped_column(Integer, ForeignKey("players.id"))
    primaryAssistId = mapped_column(Integer, ForeignKey("players.id"))
    secondaryAssistId = mapped_column(Integer, ForeignKey("players.id"))
    tertiaryAssistId = mapped_column(Integer, ForeignKey("players.id"))
    playType = mapped_column(String(50))
    oddman = mapped_column(String(50))
    primaryZone = mapped_column(String(50))
    secondaryZone = mapped_column(String(50))
    tertiaryZone = mapped_column(String(50))
    primaryLane = mapped_column(String(50))
    secondaryLane = mapped_column(String(50))
    tertiaryLane = mapped_column(String(50))
    primaryPassType = mapped_column(String(50))
    secondaryPassType = mapped_column(String(50))
    tertiaryPassType = mapped_column(String(50))

    game = relationship("Game", back_populates='events')
    team = relationship("Team", foreign_keys=[teamId], viewonly=True)
    oppTeam = relationship("Team", foreign_keys=[oppTeamId], viewonly=True)
    player = relationship("Player", foreign_keys=[playerId], viewonly=True)
    oppPlayer = relationship("Player", foreign_keys=[
                             oppPlayerId], viewonly=True)
    recovery = relationship("Player", foreign_keys=[recoveryId], viewonly=True)
    retrieval = relationship("Player", foreign_keys=[
                             retrievalId], viewonly=True)
    primaryAssist = relationship("Player", foreign_keys=[
                                 primaryAssistId], viewonly=True)
    secondaryAssist = relationship("Player", foreign_keys=[
                                   secondaryAssistId], viewonly=True)
    tertiaryAssist = relationship("Player", foreign_keys=[
                                  tertiaryAssistId], viewonly=True)

    @hybrid_property
    def eventPlayers(self):
        return {
            'player': (self.player.basePlayerDict if not (
                self.player is None) else None),
            'oppPlayer': (self.oppPlayer.basePlayerDict if not (
                self.oppPlayer is None) else None),
            'recovery': (self.recovery.basePlayerDict if not (
                self.recovery is None) else None),
            'retrieval': (self.retrieval.basePlayerDict if not (
                self.retrieval is None) else None),
            'primaryAssist': (self.primaryAssist.basePlayerDict if not (
                self.primaryAssist is None) else None),
            'secondaryAssist': (self.secondaryAssist.basePlayerDict if not (
                self.secondaryAssist is None) else None),
            'tertiaryAssist': (self.tertiaryAssist.basePlayerDict if not (
                self.tertiaryAssist is None) else None),
        }

    @hybrid_property
    def eventTeams(self):
        return {
            'team': ({'name': self.team.name, 'id': self.team.id} if not (
                self.team is None) else None),
            'oppTeam': ({'name': self.oppTeam.name, 'id': self.oppTeam.id} if not (
                self.oppTeam is None) else None),
        }

    @hybrid_property
    def dict(self):
        teams = self.eventTeams
        players = self.eventPlayers
        event = self.to_dict()
        return {**event, **teams, **players}

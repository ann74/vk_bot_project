from typing import Optional
from datetime import datetime
from dataclasses import dataclass

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from kts_backend.store.database.sqlalchemy_base import db


@dataclass
class GameScore:
    points: int
    place: int


@dataclass
class Player:
    vk_id: int
    name: str
    last_name: str
    score: Optional[GameScore]


@dataclass
class Game:
    id: int
    created_at: datetime
    chat_id: int
    players: list[Player]


class PlayerModel(db):
    __tablename__ = "players"
    vk_id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=True)

    score = relationship("GameScoreModel")

    def to_dc(self) -> Player:
        return Player(
            vk_id=self.vk_id,
            name=self.name,
            last_name=self.last_name,
            score=self.score.to_dc()
        )


class GameModel(db):
    __tablename__ = "games"
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime(), default=datetime.now)
    chat_id = Column(Integer, nullable=False)

    players = relationship("PlayerModel", secondary="GameScoreModel")

    def to_dc(self) -> Game:
        return Game(
            id=self.id,
            created_at=self.created_at,
            chat_id=self.chat_id,
            players=[player.to_dc for player in self.players]
        )


class GameScoreModel(db):
    __tablename__ = "gamescore"
    id = Column(Integer, primary_key=True)
    game_id = Column(Integer, ForeignKey('games.id', ondelete='CASCADE'), nullable=False)
    player_id = Column(Integer, ForeignKey('players.vk_id', ondelete='CASCADE'), nullable=False)
    points = Column(Integer)
    place = Column(Integer)

    def to_dc(self) -> GameScore:
        return GameScore(
            points=self.points,
            place=self.place
        )

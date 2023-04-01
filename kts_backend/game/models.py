from typing import Optional
from datetime import datetime
from dataclasses import dataclass

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text, Index
from sqlalchemy.orm import relationship

from kts_backend.store.database.sqlalchemy_base import db


@dataclass
class GameScore:
    points: int
    winner: bool


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
    word: str
    is_winner: bool
    players: list[Player]


class ChatModel(db):
    __tablename__ = "chats"
    chat_id = Column(Integer, primary_key=True)
    game_is_active = Column(Boolean, default=False)


class QuestionModel(db):
    __tablename__ = "words"
    id = Column(Integer, primary_key=True)
    word = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=False)


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
            score=self.score.to_dc(),
        )


class GameModel(db):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime(), default=datetime.now)
    chat_id = Column(ForeignKey("chats.chat_id"), index=True)
    word_id = Column(ForeignKey("words.id"))
    word = Column(String(100))
    letters = Column(String(100))
    current_move = Column(Integer)
    is_active = Column(Boolean)
    is_winner = Column(Boolean)

    players = relationship("PlayerModel", secondary="gamescore")

    def to_dc(self) -> Game:
        return Game(
            id=self.id,
            created_at=self.created_at,
            chat_id=self.chat_id,
            word=self.word,
            is_winner=self.is_winner,

            players=[player.to_dc for player in self.players],
        )


class GameScoreModel(db):
    __tablename__ = "gamescore"
    id = Column(Integer, primary_key=True)
    game_id = Column(
        Integer, ForeignKey("games.id", ondelete="CASCADE"), nullable=False
    )
    player_id = Column(
        Integer, ForeignKey("players.vk_id", ondelete="CASCADE"), nullable=False
    )
    points = Column(Integer)
    winner = Column(Boolean)

    def to_dc(self) -> GameScore:
        return GameScore(points=self.points, winner=self.winner)

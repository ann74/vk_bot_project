import typing
from datetime import datetime
from typing import Optional

from aiohttp import ClientSession, TCPConnector
from sqlalchemy import select

from kts_backend.store.base.base_accessor import BaseAccessor
from kts_backend.users.models import (
    Player,
    Game,
    GameModel,
    PlayerModel,
)

if typing.TYPE_CHECKING:
    from kts_backend.web.app import Application


API_PATH = "https://api.vk.com/method/"


class UserAccessor(BaseAccessor):
    def __init__(self, app: "Application", *args, **kwargs):
        super().__init__(app, *args, **kwargs)
        self.session: Optional[ClientSession] = None

    async def connect(self, app: "Application"):
        self.session = ClientSession(connector=TCPConnector(verify_ssl=False))

    async def disconnect(self, app: "Application"):
        if self.session:
            await self.session.close()

    async def get_users(self, chat_id: int) -> list[Player]:
        async with self.session.get(
            self._build_query(
                host=API_PATH,
                method="messages.getConversationMembers",
                params={
                    "access_token": self.app.config.bot.token,
                    "peer_id": 2000000000 + chat_id,
                    "extended": 1,
                },
            )
        ) as resp:
            data = await resp.json()
            users = data["profiles"]
            players = []
            for user in users:
                players.append(
                    Player(
                        vk_id=user["id"],
                        name=user["first_name"],
                        last_name=user["last_name"],
                        score=None,
                    )
                )
        return players

    async def create_user(self, player: Player):
        async with self.app.database.session.begin() as session:
            user = PlayerModel(
                vk_id=player.vk_id,
                name=player.name,
                last_name=player.last_name,
                score=None,
            )
            session.add(user)
            await session.commit()

    async def create_game(self, chat_id: int) -> Game:
        players = await self.get_users(chat_id)
        async with self.app.database.session.begin() as session:
            game = GameModel(
                created_at=datetime.now(), chat_id=chat_id, players=players
            )
            session.add(game)
            await session.commit()
            for player in players:
                await self.create_user(player)
        return game.to_dc()

    async def get_last_game(self, chat_id: int) -> Game:
        async with self.app.database.session.begin() as session:
            query = (
                select(GameModel)
                .where(GameModel.chat_id == chat_id)
                .order_by(GameModel.created_at)
            )
            games = await session.execute(query)
            last_game = games.scalars().last()
            return last_game.to_dc()

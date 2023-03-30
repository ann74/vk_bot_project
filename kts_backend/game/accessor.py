import typing
from datetime import datetime
from typing import Optional

from sqlalchemy import select, and_, update

from kts_backend.game.game_process import GameProcess
from kts_backend.store.base.base_accessor import BaseAccessor
from kts_backend.game.models import (
    Player,
    Game,
    GameModel,
    PlayerModel, ChatModel,
)

if typing.TYPE_CHECKING:
    from kts_backend.web.app import Application


API_PATH = "https://api.vk.com/method/"


class GameAccessor(BaseAccessor):
    class Meta:
        name = "gameaccessor"

    def __init__(self, app: "Application", *args, **kwargs):
        super().__init__(app, *args, **kwargs)
        self.game_process = GameProcess(app)

    # async def connect(self, app: "Application"):
    #     self.game_process = GameProcess(app)

    async def create_user(self, player: Player):
        async with self.app.database.session.begin() as session:
            user = PlayerModel(
                vk_id=player.vk_id,
                name=player.name,
                last_name=player.last_name,
                score=None,
            )
            session.add(user)
            # await session.commit()

    async def create_game(self, chat_id: int) -> Game:
        players = await self.get_users(chat_id)
        async with self.app.database.session.begin() as session:
            game = GameModel(
                created_at=datetime.now(), chat_id=chat_id, players=players
            )
            session.add(game)
            await session.commit()
            for (
                player
            ) in (
                players
            ):  # Не так должно быть игроков создаем раньше, здесь ссылки должны быть
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

    async def get_chats_id(self) -> list[int]:  # ready
        async with self.app.database.session.begin() as session:
            query = select(ChatModel).where(ChatModel.game_is_active == False)
            try:
                chats = await session.execute(query)
            except Exception as e:
                self.logger.error('Exception get_chats_id', exc_info=e)
        chats_id = [obj.chat_id for obj in chats.scalars()]
        return chats_id

    async def update_chat(self, chat_id: int, game_is_active: bool) -> None:
        async with self.app.database.session.begin() as session:
            query = update(ChatModel).where(ChatModel.chat_id == chat_id).values(game_is_active=game_is_active)
            try:
                await session.execute(query)
            except Exception as e:
                self.logger.error('Exception update_chat', exc_info=e)

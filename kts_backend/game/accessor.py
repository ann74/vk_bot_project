import typing
from datetime import datetime
from typing import Optional

from sqlalchemy import select, and_, update

from kts_backend.game.game_start import GameStart
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
        self.gamestart: Optional[GameStart] = None

    async def connect(self, app: "Application"):
        self.gamestart = GameStart(app)
        self.logger.info("start gamestart")
        await self.gamestart.start()

    async def disconnect(self, app: "Application"):
        if self.gamestart and self.gamestart.is_running:
            await self.gamestart.stop()


    # async def get_users(self, chat_id: int) -> list[Player]:
    #     async with self.session.get(
    #         self._build_query(
    #             host=API_PATH,
    #             method="messages.getConversationMembers",
    #             params={
    #                 "access_token": self.app.config.bot.token,
    #                 "peer_id": 2000000000 + chat_id,
    #                 "extended": 1,
    #             },
    #         )
    #     ) as resp:
    #         data = await resp.json()
    #         users = data["profiles"]
    #         players = []
    #         for user in users:
    #             players.append(
    #                 Player(
    #                     vk_id=user["id"],
    #                     name=user["first_name"],
    #                     last_name=user["last_name"],
    #                     score=None,
    #                 )
    #             )
    #     return players

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

    async def get_chats_id(self) -> list[int]:
        async with self.app.database.session.begin() as session:
            query = select(ChatModel).where(and_(ChatModel.game_is_active == False, ChatModel.game_start == False))
            try:
                chats = await session.execute(query)
            except Exception as e:
                self.logger.error('Exception get_chats_id', exc_info=e)
        chats_id = [obj.chat_id for obj in chats.scalars()]
        return chats_id

    async def update_chat(self, chat_id: int, game_is_active: bool, game_start: bool) -> None:
        async with self.app.database.session.begin() as session:
            query = update(ChatModel).where(ChatModel.chat_id == chat_id).values(game_is_active=game_is_active,
                                                                                 game_start=game_start)
            try:
                await session.execute(query)
            except Exception as e:
                self.logger.error('Exception update_chat', exc_info=e)

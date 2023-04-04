import typing
from typing import Optional

from kts_backend.game.models import Player
from kts_backend.store.base.base_accessor import BaseAccessor
from kts_backend.store.bot.handler import Handler
from kts_backend.store.vk_api.dataclasses import Message, Update

if typing.TYPE_CHECKING:
    from kts_backend.web.app import Application


class BotManager(BaseAccessor):
    class Meta:
        name = "botmanager"

    def __init__(self, app: "Application", *args, **kwargs):
        super().__init__(app, *args, **kwargs)
        self.bot = None
        self.handler: Optional[Handler] = None

    async def connect(self, app: "Application"):
        self.handler = Handler(app.store)
        self.logger.info("start handling")
        await self.handler.start()

    async def disconnect(self, app: "Application"):
        if self.handler and self.handler.is_running:
            await self.handler.stop()

    async def handle_updates(self, update: Update):
        self.logger.info(update)
        if update.object.action == "chat_kick_user":
            await self.app.store.game.game_process.leave_chat(update)
        elif update.object.action in ("chat_invite_user", "chat_invite_user_by_link"):
            await self.app.store.game.game_process.invite_chat(update)
        elif update.object.button == "info":
            await self.app.store.game.game_process.game_info(update)
        elif update.object.button == "startgame":
            await self.app.store.game.game_process.start_game(update)
        elif update.object.button == "uniongame":
            await self.app.store.game.game_process.union_game(update)
        elif update.object.button == "drum":
            await self.app.store.game.game_process.drum_cooler(update)
        elif update.object.button == "word":
            await self.app.store.game.game_process.say_word(update)
        elif update.object.button == "leave":
            await self.app.store.game.game_process.leave_game(update)
        elif update.object.body and len(update.object.body) == 1:
            await self.app.store.game.game_process.check_letter(update)
        elif update.object.body and len(update.object.body.split()) == 1:
            await self.app.store.game.game_process.check_word(update)

        else:
            raise NotImplementedError

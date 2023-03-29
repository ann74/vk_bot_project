import typing
from typing import Optional

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
        message = Message(
            user_id=update.object.user_id,
            text=update.object.body,
            peer_id=update.object.peer_id,
        )
        await self.app.senders_queue.put(message)

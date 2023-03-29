import asyncio
import typing

from asyncio import Task
from typing import Optional

from kts_backend.game.keyboards import start_keyboard, start_keyboard_1
from kts_backend.store.vk_api.dataclasses import Message

if typing.TYPE_CHECKING:
    from kts_backend.web.app import Application


class GameStart:
    def __init__(self, app: "Application"):
        self.app = app
        self.is_running = False
        self.gamestart_task: Optional[Task] = None

    async def start(self):
        self.is_running = True
        self.gamestart_task = asyncio.create_task(self.gamestart_message())

    async def stop(self):
        self.is_running = False
        self.gamestart_task.cancel()

    async def gamestart_message(self):
        if self.is_running:
            chats_id = await self.app.store.game.get_chats_id()
            self.app.store.game.logger.info(chats_id)
            for chat_id in chats_id:
                message = Message(
                    text="Поиграем в поле чудес?",
                    peer_id=2000000000 + chat_id,
                    keyboard=start_keyboard,
                )
                await self.app.senders_queue.put(message)
                await self.app.store.game.update_chat(chat_id=chat_id, game_start=True, game_is_active=False)

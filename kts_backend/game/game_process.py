import random
import typing

from typing import Optional

from kts_backend.game.keyboards import start_keyboard, union_keyboard, main_keyboard
from kts_backend.store.vk_api.dataclasses import Message, Update

if typing.TYPE_CHECKING:
    from kts_backend.web.app import Application


class GameProcess:
    def __init__(self, app: "Application"):
        self.app = app
        self.max_members = 3

    async def start_message(self, id_: Optional[int] = None):
        if not id_:
            chats_id = await self.app.store.game.get_chats_id()
        else:
            chats_id = [id_]
        for chat_id in chats_id:
            message = Message(
                text="Поиграем в поле чудес?",
                peer_id=2000000000 + chat_id,
                keyboard=start_keyboard,
            )
            await self.app.senders_queue.put(message)

    async def union_message(self, update: Update):
        message = Message(
            text="Присоединяйтесь к игре, максимум 5 человек",
            peer_id=update.object.peer_id,
            keyboard=union_keyboard,
        )
        await self.app.senders_queue.put(message)

    async def main_message(self, update: Update):
        message = Message(
            text="Начинаем!\nСлово ...\nОписание ...\n Ходит ... \nКрутите барабан или можете назвать слово",
            peer_id=update.object.peer_id,
            keyboard=main_keyboard,
        )
        await self.app.senders_queue.put(message)

    async def start_game(self, update: Update):
        count_members = 1
        await self.union_message(update)

    async def union_game(self, update: Update):
        await self.main_message(update)


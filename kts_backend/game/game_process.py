from collections import deque, defaultdict
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
        self.players_queues = defaultdict(deque)  # Хранит по ключу чатов, в которых активна игра, очередь игроков сразу с именами

    async def start_message(self, id_: Optional[int] = None):
        if not id_:
            chats_id = await self.app.store.game.get_chats_id()
        else:
            chats_id = [id_]
        for chat_id in chats_id:
            message = Message(
                text="Поиграем в поле чудес?",
                peer_id=chat_id,
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

    async def main_message(self, update: Update, word: str, description: str):
        chat_id = update.object.peer_id
        players = []
        for player in self.players_queues[chat_id]:
            players.append('@' + player[1])
        message = Message(
            text=f"Начинаем! В игре {', '.join(players)}. Вопрос: {description} Слово: {word}",
            peer_id=chat_id,
            keyboard=main_keyboard,
        )
        await self.app.senders_queue.put(message)

    async def start_game(self, update: Update):
        chat_id, user_id = update.object.peer_id, update.object.user_id
        await self.app.store.game.create_game(chat_id=chat_id, vk_id=user_id)
        await self.app.store.game.update_chat(chat_id=chat_id, game_is_active=True)
        await self.union_message(update)
        name = await self.app.store.game.get_player_by_id(user_id)
        self.players_queues[chat_id].append((user_id, name))

    @staticmethod
    def get_word_mask(word: str, letters: str) -> str:
        letters_mask = set(letters)
        res = []
        for letter in word:
            if letter in letters_mask:
                res.append('*')
            else:
                res.append(letter)
        return ''.join(res).upper()

    async def union_game(self, update: Update):
        chat_id, user_id = update.object.peer_id, update.object.user_id
        if len(self.players_queues[chat_id]) < self.max_members:
            for member in self.players_queues[chat_id]:
                if member[0] == user_id:
                    break
            else:
                await self.app.store.game.create_player_in_game(vk_id=user_id, chat_id=chat_id)
                name = await self.app.store.game.get_player_by_id(user_id)
                self.players_queues[chat_id].append((user_id, name))
        if len(self.players_queues[chat_id]) == self.max_members:
            await self.app.store.game.update_game_move(chat_id=chat_id, current_move=self.players_queues[chat_id][0][0])
            word, letters, description = await self.app.store.game.get_word_info(chat_id=chat_id, with_description=True)
            word_mask = self.get_word_mask(word, letters)
            await self.main_message(update, word=word_mask, description=description)


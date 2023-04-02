from collections import deque, defaultdict
from random import choice
import typing

from typing import Optional

from kts_backend.game.keyboards import start_keyboard, union_keyboard, main_keyboard
from kts_backend.store.vk_api.dataclasses import Message, Update

if typing.TYPE_CHECKING:
    from kts_backend.web.app import Application


class GameProcess:
    def __init__(self, app: "Application"):
        self.app = app
        self.max_members = 2
        self.players_queues = defaultdict(deque)  # Хранит по ключу чатов, в которых активна игра, очередь игроков сразу с именами и с очками в текущем хожу
        self.points = [0, 10, 20, 50, 100, 150, 200, 500, 'B']

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

    async def move_player(self, chat_id: int):
        current_player = self.players_queues[chat_id][0]
        message = Message(
            text=f"Ходит @{current_player[1]}<br>Крутите барабан или можете сразу назвать слово.",
            peer_id=chat_id,
        )
        await self.app.senders_queue.put(message)

    async def main_message(self, chat_id: int, word: str, description: str):
        players = []
        for player in self.players_queues[chat_id]:
            players.append('@' + player[1])
        message = Message(
            text=f"Начинаем!<br>В игре {', '.join(players)}.<br><br>Вопрос: {description}<br><br>{word}",
            peer_id=chat_id,
            keyboard=main_keyboard,
        )
        await self.app.senders_queue.put(message)
        await self.move_player(chat_id)

    async def start_game(self, update: Update):
        chat_id, user_id = update.object.peer_id, update.object.user_id
        await self.app.store.game.create_game(chat_id=chat_id, vk_id=user_id)
        await self.app.store.game.update_chat(chat_id=chat_id, game_is_active=True)
        await self.union_message(update)
        name = await self.app.store.game.get_player_by_id(user_id)
        self.players_queues[chat_id].append([user_id, name, 0])

    @staticmethod
    def get_word_mask(word: str, letters_mask: set) -> str:
        res = []
        for letter in word:
            if letter in letters_mask:
                res.append('*')
            else:
                res.append(letter)
        return ' '.join(res).upper()

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
            word_mask = self.get_word_mask(word, set(letters))
            await self.main_message(chat_id, word=word_mask, description=description)

    async def answer_player(self, chat_id: int, points: int):
        self.players_queues[chat_id][0][2] = points
        message = Message(
            text=f"У вас {points} очков на барабане. Называйте букву. Или можете назвать слово.",
            peer_id=chat_id,
        )
        await self.app.senders_queue.put(message)

    async def move_transition(self, chat_id: int, message_text: str):
        current_player = self.players_queues[chat_id].popleft()
        current_player[2] = 0
        self.players_queues[chat_id].append(current_player)
        message = Message(
            text=message_text,
            peer_id=chat_id,
        )
        await self.app.senders_queue.put(message)
        await self.move_player(chat_id)

    async def drum_cooler(self, update: Update):
        chat_id, user_id = update.object.peer_id, update.object.user_id
        current_player = self.players_queues[chat_id][0]
        if user_id == current_player[0]:
            user_points = choice(self.points)
            if user_points == 0:
                message_text = 'У вас 0 на барабане, переход хода.'
                await self.move_transition(chat_id, message_text)
            elif user_points == 'B':
                message_text = 'Вы банкрот, все ваши очки сгорают. Ход переходит к следующему игроку.'
                await self.app.store.game.update_player_score(vk_id=user_id, points=0)
                await self.move_transition(chat_id, message_text)
            else:
                await self.answer_player(chat_id=chat_id, points=user_points)

    async def right_letter(self, chat_id: int, word: str, name: str):
        self.app.store.game.logger.info("Буква угадана")
        self.players_queues[chat_id][0][2] = 0
        message = Message(
            text=f"Есть такая буква!<br><br>{word}<br><br>@{name} продолжайте."
                 f" Крутите барабан или можете назвать слово.",
            peer_id=chat_id,
        )
        await self.app.senders_queue.put(message)

    async def check_letter(self, update: Update):
        self.app.store.game.logger.info("Вызвана проверка буквы")
        chat_id, user_id = update.object.peer_id, update.object.user_id
        current_player = self.players_queues[chat_id][0]
        self.app.store.game.logger.info(chat_id, user_id, current_player)
        if user_id == current_player[0] and current_player[0][2] != 0:
            self.app.store.game.logger.info("Букву назвал верный игрок")
            word, letters, _ = await self.app.store.game.get_word_info(chat_id=chat_id, with_description=False)
            letters = set(letters)
            letter = update.object.body.lower()
            if letter in letters:
                self.app.store.game.logger.info("Буква есть в слове")
                letters.remove(letter)
                points = current_player[2]
                await self.app.store.game.update_player_score(vk_id=user_id, points=points)
                await self.app.store.game.update_game_letters(chat_id=chat_id, letters=''.join(letters))
                word_mask = self.get_word_mask(word, letters)
                await self.right_letter(chat_id=chat_id, word=word_mask, name=current_player[1])
            else:
                message_text = "К сожалению такой буквы нет в этом слове. Ход переходит к следующему игроку."
                await self.move_transition(chat_id, message_text)
        else:
            self.app.store.game.logger.info("Букву назвал неверный игрок")


    async def check_word(self, update: Update):
        pass

    async def say_word(self, update: Update):
        pass

    async def leave_game(self, update: Update):
        pass

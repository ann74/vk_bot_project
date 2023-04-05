import asyncio
from collections import deque, defaultdict
from random import choice
import time
import typing

from typing import Optional

from kts_backend.game.keyboards import start_keyboard, union_keyboard, main_keyboard
from kts_backend.store.vk_api.dataclasses import Message, Update

if typing.TYPE_CHECKING:
    from kts_backend.web.app import Application


class GameProcess:
    def __init__(self, app: "Application"):
        self.app = app
        self.max_members = 5
        self.players_queues = defaultdict(deque)  # Хранит по ключу чатов, в которых активна игра, очередь игроков сразу с именами и с очками в текущем хожу
        self.points = [0, 10, 20, 50, 100, 150, 200, 500, 'B']
        self.timeouts = {}  # Хранит по ключу чатов запущен таймаут или нет для присоединения к игре
        self.pins = {}  # Хранит идентефикаторы запиненых сообщений заданий

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
            text=f"Присоединяйтесь к игре, минимум 2 участника, максимум {self.max_members}.",
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
            text=f"Начинаем!<br>В игре {', '.join(players)}.<br>Вопрос: {description}<br>{word}",
            peer_id=chat_id,
            keyboard=main_keyboard,
        )
        # await self.app.senders_queue.put(message)
        conversation_message_id = await self.app.store.sender.send_message(message)
        message_pin = Message(
            peer_id=chat_id,
            conversation_message_id=conversation_message_id,
        )
        self.pins[chat_id] = conversation_message_id
        await self.app.store.sender.pin_message(message_pin)
        await self.move_player(chat_id)

    async def start_game(self, update: Update):
        chat_id, user_id = update.object.peer_id, update.object.user_id
        name = await self.app.store.game.get_player_by_id(user_id)
        if name:
            await self.app.store.game.create_game(chat_id=chat_id, vk_id=user_id)
            await self.app.store.game.update_chat(chat_id=chat_id, game_is_active=True)
            await self.union_message(update)
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

    async def start_game_process(self, chat_id: int):
        # if self.timeouts[chat_id] == 1:
        self.timeouts[chat_id] = 0
        await self.app.store.game.update_game_move(chat_id=chat_id, current_move=self.players_queues[chat_id][0][0])
        word, letters, description = await self.app.store.game.get_word_info(chat_id=chat_id, with_description=True)
        word_mask = self.get_word_mask(word, set(letters))
        await self.main_message(chat_id, word=word_mask, description=description)

    async def union_game(self, update: Update):
        chat_id, user_id = update.object.peer_id, update.object.user_id
        if len(self.players_queues[chat_id]) < self.max_members:
            for member in self.players_queues[chat_id]:
                if member[0] == user_id:
                    break
            else:
                name = await self.app.store.game.get_player_by_id(user_id)
                if name:
                    await self.app.store.game.create_player_in_game(vk_id=user_id, chat_id=chat_id)
                    self.players_queues[chat_id].append([user_id, name, 0])
        if len(self.players_queues[chat_id]) == 2:
            self.timeouts[chat_id] = 1
            asyncio.create_task(self.timout(chat_id=chat_id))
        if len(self.players_queues[chat_id]) == self.max_members:
            await self.start_game_process(chat_id=chat_id)

    async def timout(self, chat_id: int):
        await asyncio.sleep(15)
        if self.timeouts[chat_id] == 1:
            await self.start_game_process(chat_id=chat_id)

    async def answer_player(self, chat_id: int, points: int):
        self.players_queues[chat_id][0][2] = points
        message = Message(
            text=f"У вас {points} очков на барабане. Называйте букву. Или можете назвать слово.",
            peer_id=chat_id,
        )
        await self.app.senders_queue.put(message)

    async def game_finished(self, chat_id: int):
        message = Message(
            text="Игроков больше не осталось. Слово не разгадано. Победителя нет",
            peer_id=chat_id,
        )
        await self.app.senders_queue.put(message)
        del self.players_queues[chat_id]
        await self.app.store.game.update_game_finished(chat_id=chat_id, is_winner=False)
        await self.app.store.game.update_chat(chat_id=chat_id, game_is_active=False)
        await self.app.store.sender.unpin_message(Message(peer_id=chat_id))
        await self.start_message(id_=chat_id)

    async def move_transition(self, chat_id: int, message_text: str, player_delete: bool = False):
        self.app.store.game.logger.info("Ход переходит")
        current_player = self.players_queues[chat_id].popleft()
        if not player_delete:
            current_player[2] = 0
            self.players_queues[chat_id].append(current_player)
        if len(self.players_queues[chat_id]) == 0:
            await self.game_finished(chat_id)
        else:
            self.app.store.game.logger.info(f"Очередь после перехода {self.players_queues[chat_id]}")
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
            if current_player[2] != 0:
                message = "Вы уже покрутили барабан, называйте букву или слово"
                await self.some_message(chat_id=chat_id, message_text=message)
            else:
                user_points = choice(self.points)
                if user_points == 0:
                    message_text = 'У вас 0 на барабане, переход хода.'
                    await self.move_transition(chat_id, message_text)
                elif user_points == 'B':
                    message_text = 'Вы банкрот, все ваши очки сгорают. Ход переходит к следующему игроку.'
                    await self.app.store.game.update_player_score(vk_id=user_id, chat_id=chat_id, points=0, bankrot=True)
                    await self.move_transition(chat_id, message_text)
                else:
                    await self.answer_player(chat_id=chat_id, points=user_points)
        else:
            self.app.store.game.logger.info("Барабан покрутил не тот")

    async def right_letter(self, chat_id: int, word: str, name: str):
        self.players_queues[chat_id][0][2] = 0
        message = Message(
            text=f"Есть такая буква!<br><br>{word}<br><br>@{name} продолжайте."
                 f" Крутите барабан или можете назвать слово.",
            peer_id=chat_id,
        )
        await self.app.senders_queue.put(message)

    async def some_message(self, chat_id: int, message_text: str):
        message = Message(
            text=message_text,
            peer_id=chat_id,
        )
        await self.app.senders_queue.put(message)

    async def word_solved(self, chat_id: int, word: str, name: str, user_id: int):
        points = await self.app.store.game.get_player_score(user_id)
        message = Message(
            text=f"Поздравляю! Вы угадали слово<br><br>{word}<br><br>@{name} вы набрали"
                 f" {points} очков",
            peer_id=chat_id,
        )
        await self.app.senders_queue.put(message)
        del self.players_queues[chat_id]
        await self.app.store.game.update_game_finished(chat_id=chat_id, is_winner=True)
        await self.app.store.game.update_chat(chat_id=chat_id, game_is_active=False)
        await self.app.store.sender.unpin_message(Message(peer_id=chat_id))
        await self.start_message(id_=chat_id)

    async def check_letter(self, update: Update):
        chat_id, user_id = update.object.peer_id, update.object.user_id
        current_player = self.players_queues[chat_id][0]
        if user_id == current_player[0] and current_player[2] != 0:
            word, letters, _ = await self.app.store.game.get_word_info(chat_id=chat_id, with_description=False)
            letters = set(letters)
            letter = update.object.body.lower()
            if letter in letters:
                letters.remove(letter)
                points = current_player[2]
                word_mask = self.get_word_mask(word, letters)
                winner = True if not letters else False
                await self.app.store.game.update_player_score(vk_id=user_id, chat_id=chat_id, points=points, winner=winner)
                await self.app.store.game.update_game_letters(chat_id=chat_id, letters=''.join(letters))
                if not letters:
                    await self.word_solved(chat_id=chat_id, word=word_mask, user_id=user_id, name=current_player[1])
                else:
                    await self.right_letter(chat_id=chat_id, word=word_mask, name=current_player[1])
            else:
                message_text = "К сожалению вы не правильно назвали букву. Ход переходит к следующему игроку."
                await self.move_transition(chat_id, message_text)
        elif user_id == current_player[0] and current_player[2] == 0:
            message_text = "Нужно сначала покрутить барабан"
            await self.some_message(chat_id, message_text)
        # else:
        #     message_text = "Сейчас не ваш ход, не подсказывайте"
        #     await self.some_message(chat_id, message_text)

    async def check_word(self, update: Update):
        chat_id, user_id = update.object.peer_id, update.object.user_id
        current_player = self.players_queues[chat_id][0]
        if user_id == current_player[0]:
            word, letters, _ = await self.app.store.game.get_word_info(chat_id=chat_id, with_description=False)
            user_word = update.object.body.lower()
            if user_word == word:
                word = ' '.join(list(word.upper()))
                points = current_player[2]
                await self.app.store.game.update_player_score(vk_id=user_id, chat_id=chat_id, points=points, winner=True)
                await self.word_solved(chat_id=chat_id, word=word, user_id=user_id, name=current_player[1])
            else:
                message_text = f"@{current_player[1]} вы не верно назвали слово, поэтому покидаете игру." \
                               f"<br>Ход переходит к следующему игроку"
                await self.move_transition(chat_id=chat_id, message_text=message_text, player_delete=True)
        # else:
        #     message_text = "Сейчас не ваш ход, не подсказывайте"
        #     await self.some_message(chat_id, message_text)

    async def say_word(self, update: Update):
        chat_id, user_id = update.object.peer_id, update.object.user_id
        current_player = self.players_queues[chat_id][0]
        if user_id == current_player[0]:
            base_text = "Внимание! Если вы не верно назовете слово, то выйдите из игры."
            if current_player[2] == 0:
                message_text = base_text + "<br>Вы можете крутить барабан или называйте слово"
            else:
                message_text = base_text + "<br>Вы можете назвать букву или слово"
        # else:
        #     message_text = "Не ваш ход. Вы не можете называть слово"
            await self.some_message(chat_id=chat_id, message_text=message_text)

    async def leave_game(self, update: Update):
        chat_id, user_id = update.object.peer_id, update.object.user_id
        current_player = self.players_queues[chat_id][0]
        if user_id == current_player[0]:
            message_text = f"@{current_player[1]} покинул игру. Ход переходит к следующему игроку"
            await self.move_transition(chat_id=chat_id, message_text=message_text, player_delete=True)
        else:
            index = 0
            for ind, member in enumerate(self.players_queues[chat_id]):
                if member[0] == user_id:
                    index = ind
                    break
            if index:
                name = self.players_queues[chat_id][index][1]
                message_text = f"@{name} покинул игру."
                del self.players_queues[chat_id][index]
                await self.some_message(chat_id=chat_id, message_text=message_text)

    async def leave_chat(self, update: Update):
        chat_id = update.object.peer_id
        active_game = await self.app.store.game.get_active_game(chat_id)
        if active_game:
            await self.leave_game(update)

    async def invite_chat(self, update: Update):
        player_base = await self.app.store.game.get_player_by_id(update.object.user_id)
        self.app.store.game.logger.info(player_base)
        if not player_base:
            player = await self.app.store.vk_api.get_user_by_id(update.object.user_id)
            await self.app.store.game.create_user(player)

    async def game_info(self, update: Update):
        chat_id = update.object.peer_id
        game_info = await self.app.store.game.get_last_game(chat_id=chat_id)
        self.app.store.game.logger.info(game_info)
        if not game_info.is_winner:
            word = self.get_word_mask(game_info.word, game_info.letters)
        else:
            word = ' '.join(list(game_info.word)).upper()
        players_info = []
        for player in game_info.players:
            players_info.append(f"@{player.name}, {player.score.points} очков,"
                                f" {'Победитель' if player.score.winner else ''}")
        winner = 'Есть победитель' if game_info.is_winner else 'Победителя нет'
        message = f"Игра начата {game_info.created_at.strftime('%d.%m.%y %H:%M:%S')}<br>" \
                  f"{winner}<br>Загаданное слово - {word}<br>Игроки:<br>" \
                  f"{'<br>'.join(players_info)}"
        await self.some_message(chat_id=chat_id, message_text=message)


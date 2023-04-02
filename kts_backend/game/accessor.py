import typing
from datetime import datetime
from random import choice
from typing import Optional

from sqlalchemy import select, and_, update

from kts_backend.game.game_process import GameProcess
from kts_backend.store.base.base_accessor import BaseAccessor
from kts_backend.game.models import (
    Player,
    Game,
    GameModel, GameScoreModel,
    PlayerModel, ChatModel, QuestionModel
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
            )
            session.add(user)

    async def choice_word(self) -> tuple[int, str]:  # ready
        async with self.app.database.session.begin() as session:
            query = select(QuestionModel)
            words = await session.execute(query)
        word = choice(words.scalars().all())
        return word.id, word.word

    async def create_game(self, chat_id: int, vk_id: int) -> None:  # ready
        word_id, word = await self.choice_word()
        letters_set = set(word[1:-1])
        if word[0] in letters_set:
            letters_set.remove(word[0])
        if word[-1] in letters_set:
            letters_set.remove(word[-1])
        async with self.app.database.session.begin() as session:
            game = GameModel(
                created_at=datetime.now(),
                chat_id=chat_id,
                word_id=word_id,
                word=word,
                letters=''.join(letters_set),
                is_active=True
            )
            session.add(game)
        await self.create_player_in_game(vk_id=vk_id, game_id=game.id)

    async def get_active_game(self, chat_id: int) -> Optional[int]:
        async with self.app.database.session.begin() as session:
            query = select(GameModel.id).where(and_((GameModel.chat_id == chat_id), (GameModel.is_active == True)))
            game = await session.execute(query)
        return game.scalars().first()

    async def create_player_in_game(self, vk_id: int, chat_id: Optional[int] = None, game_id: Optional[int] = None) -> None:   # ready
        if not game_id:
            game_id = await self.get_active_game(chat_id)
        async with self.app.database.session.begin() as session:
            player_game = GameScoreModel(
                game_id=game_id,
                player_id=vk_id,
            )
            session.add(player_game)

    async def get_player_by_id(self, vk_id: int) -> Optional[str]:  # ready
        async with self.app.database.session.begin() as session:
            query = select(PlayerModel).where(PlayerModel.vk_id == vk_id)
            player = await session.execute(query)
            player = player.scalars().first()
        if not player:
            return None
        return f"{player.name} {player.last_name}"

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
            chats = await session.execute(query)
        chats_id = [obj.chat_id for obj in chats.scalars()]
        return chats_id

    async def update_chat(self, chat_id: int, game_is_active: bool) -> None:  # ready
        async with self.app.database.session.begin() as session:
            query = update(ChatModel).where(ChatModel.chat_id == chat_id).values(game_is_active=game_is_active)
            await session.execute(query)

    async def update_game_move(self, chat_id: int, current_move: int) -> None:  # ready
        async with self.app.database.session.begin() as session:
            query = update(GameModel).where(and_((GameModel.chat_id == chat_id),
                                                 (GameModel.is_active == True))).values(current_move=current_move)
            await session.execute(query)

    async def update_game_letters(self, chat_id: int, letters: str) -> None:  # ready
        async with self.app.database.session.begin() as session:
            query = update(GameModel).where(and_((GameModel.chat_id == chat_id),
                                                 (GameModel.is_active == True))).values(letters=letters)
            await session.execute(query)

    async def get_word_info(self, chat_id: int, with_description: bool = False) -> tuple[str, str, Optional[str]]:  # ready
        async with self.app.database.session.begin() as session:
            query = select(GameModel).where(and_((GameModel.chat_id == chat_id), (GameModel.is_active == True)))
            game = await session.execute(query)
        game = game.scalars().first()
        if with_description:
            description = await self.get_word_description(game.word_id)
        else:
            description = None
        return game.word, game.letters, description

    async def get_word_description(self, word_id: int) -> str:  # ready
        async with self.app.database.session.begin() as session:
            query = select(QuestionModel.description).where(QuestionModel.id == word_id)
            description = await session.execute(query)
        return description.scalars().first()

    async def update_player_score(self, vk_id: int, chat_id: int, points: int, winner: bool = False) -> None:
        game_id = await self.get_active_game(chat_id)
        async with self.app.database.session.begin() as session:
            query = update(GameScoreModel).where(and_(GameScoreModel.player_id == vk_id),
                                                 (GameScoreModel.game_id == game_id)
                                                 ).values(points=points, winner=winner)
            await session.execute(query)

    async def get_player_score(self, vk_id: int) -> int:
        async with self.app.database.session.begin() as session:
            query = select(GameScoreModel.points).where(GameScoreModel.player_id == vk_id)
            player_score = await session.execute(query)
        return player_score.scalars().first()

    async def update_game_finished(self, chat_id: int, is_winner: bool) -> None:
        async with self.app.database.session.begin() as session:
            query = update(GameModel).where(and_((GameModel.chat_id == chat_id),
                                                 (GameModel.is_active == True))).values(is_active=False,
                                                                                        is_winner=is_winner)
            await session.execute(query)


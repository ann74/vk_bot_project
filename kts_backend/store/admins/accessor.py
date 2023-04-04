import typing
from hashlib import sha256
from typing import Optional

from asyncpg import UniqueViolationError
from sqlalchemy import select, insert, values, String

from kts_backend.admin.models import Admin, AdminModel
from kts_backend.game.models import QuestionModel, Question
from kts_backend.store.base.base_accessor import BaseAccessor


class AdminAccessor(BaseAccessor):
    class Meta:
        name = "admins"

    # async def connect(self, app: "Application"):
    #     await super().connect(app)
    #     await self.create_admin(
    #         email=app.config.admin.email, password=app.config.admin.password
    #     )

    async def get_by_email(self, email: str) -> Optional[Admin]:
        async with self.app.database.session.begin() as session:
            query = select(AdminModel).where(AdminModel.email == email)
            admin_model = await session.execute(query)
        if admin_model is not None:
            return admin_model.scalars().first()
        return None

    async def create_admin(self, email: str, password: str) -> Optional[Admin]:
        async with self.app.database.session.begin() as session:
            try:
                admin = AdminModel(email=email, password=sha256(password.encode()).hexdigest())
                session.add(admin)
                await session.commit()
            except UniqueViolationError:
                return None
        return admin

    async def get_question_by_word(self, word: str) -> Optional[Question]:
        async with self.app.database.session.begin() as session:
            query = select(QuestionModel).where(QuestionModel.word == word)
            question = await session.execute(query)
        return question.scalars().first()

    async def create_question(self, word: str, description: str) -> Question:
        async with self.app.database.session.begin() as session:
            question = QuestionModel(word=word, description=description)
            session.add(question)
        return Question(id=question.id, word=question.word, description=question.description)

    async def question_list(self, search: Optional[str]):
        async with self.app.database.session.begin() as session:
            if search:
                query = select(QuestionModel).where(QuestionModel.word.like(f'%{search}%'))
            else:
                query = select(QuestionModel)
            questions = await session.execute(query)
        return [Question(id=quest.id,
                         word=quest.word,
                         description=quest.description)
                for quest in questions.scalars()]

from typing import Optional, TYPE_CHECKING

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base, sessionmaker

from kts_backend.store.base.base_accessor import BaseAccessor
from kts_backend.store.database.sqlalchemy_base import db

if TYPE_CHECKING:
    from kts_backend.web.app import Application


class Database(BaseAccessor):
    class Meta:
        name = "database"

    def __init__(self, app: "Application", *args, **kwargs):
        super().__init__(app, *args, **kwargs)
        self._engine: Optional[AsyncEngine] = None
        self._db: Optional[declarative_base] = None
        self.session: Optional[sessionmaker] = None

    async def connect(self, *_: list, **__: dict) -> None:
        self._db = db
        database_url = (
            f"postgresql+asyncpg://{self.app.config.database.database}:"
            f"{self.app.config.database.password}@"
            f"{self.app.config.database.host}/{self.app.config.database.user}"
        )
        self._engine = create_async_engine(database_url, echo=True, future=True)
        self.session = sessionmaker(
            self._engine,
            expire_on_commit=False,
            autoflush=True,
            class_=AsyncSession,
        )

    async def disconnect(self, *_: list, **__: dict) -> None:
        try:
            await self._engine.dispose()
        except Exception as e:
            self.logger.error("Exception", exc_info=e)

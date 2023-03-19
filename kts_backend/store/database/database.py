from typing import Optional, TYPE_CHECKING

from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from kts_backend.store.database.sqlalchemy_base import db

if TYPE_CHECKING:
    from kts_backend.web.app import Application

DATABASE_URL = "postgresql+asyncpg://vkbot:password@localhost/vkbot_qweez"

class Database:
    def __init__(self, app: "Application"):
        self.app = app
        self._engine: Optional[AsyncEngine] = None
        self._db: Optional[declarative_base] = None
        self.session: Optional[sessionmaker] = None

    async def connect(self, *_: list, **__: dict) -> None:
        self._db = db
        self._engine = create_async_engine(DATABASE_URL, echo=True, future=True)
        # self._engine = create_async_engine(URL.create(
        #     drivername="postgresql+asyncpg",
        #     host=self.app.config.database.host,
        #     database=self.app.config.database.database,
        #     username=self.app.config.database.user,
        #     password=self.app.config.database.password,
        #     port=self.app.config.database.port,
        # ))
        self.session = sessionmaker(
            self._engine, expire_on_commit=False, class_=AsyncSession
        )

    async def disconnect(self, *_: list, **__: dict) -> None:
        # if self._db is not None:
        #     await self._db.pop_bind().close()
        try:
            await self._engine.dispose()
        except Exception:
            pass


import typing
from asyncio import Queue

from kts_backend.store.database.database import Database

if typing.TYPE_CHECKING:
    from kts_backend.web.app import Application


class Store:
    def __init__(self, app: "Application"):
        from kts_backend.store.bot.manager import BotManager
        from kts_backend.store.vk_api.accessor import VkApiAccessor
        from kts_backend.store.sender.accessor import SenderAccessor
        from kts_backend.game.accessor import GameAccessor
        from kts_backend.store.admins.accessor import AdminAccessor

        self.vk_api = VkApiAccessor(app)
        self.bots_manager = BotManager(app)
        self.sender = SenderAccessor(app)
        self.game = GameAccessor(app)
        self.admins = AdminAccessor(app)


def setup_store(app: "Application"):
    app.database = Database(app)
    app.store = Store(app)
    app.receivers_queue = Queue()
    app.senders_queue = Queue()

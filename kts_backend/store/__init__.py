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
        from kts_backend.users.accessor import UserAccessor

        self.vk_api = VkApiAccessor(app)
        self.bots_manager = BotManager(app)
        self.sender = SenderAccessor(app)
        self.user = UserAccessor(app)


def setup_store(app: "Application"):
    app.database = Database(app)
    app.on_startup.append(app.database.connect)
    app.on_cleanup.append(app.database.disconnect)
    app.store = Store(app)
    app.receivers_queue = Queue()
    app.senders_queue = Queue()

import asyncio
import pickle
import typing

from asyncio import Task
from typing import Optional

from kts_backend.store import Store

if typing.TYPE_CHECKING:
    from kts_backend.web.app import Application


class Handler:
    def __init__(self, store: Store, app: "Application"):
        self.store = store
        self.app = app
        self.is_running = False
        self.handler_task: Optional[Task] = None

    async def start(self):
        self.is_running = True
        self.handler_task = asyncio.create_task(self.handle_updates())
        await self.store.game.game_process.start_message()

    async def stop(self):
        self.is_running = False
        self.handler_task.cancel()

    async def handle_updates(self):
        while self.is_running:
            async with self.app.rabbitmq.receivers_queue.iterator() as queue_iter:
                async for incoming_update in queue_iter:
                    update = pickle.loads(incoming_update.body)
                    await self.store.bots_manager.handle_updates(update)
                    await incoming_update.ack()


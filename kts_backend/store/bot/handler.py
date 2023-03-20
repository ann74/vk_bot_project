import asyncio

from asyncio import Task, Future
from typing import Optional

from kts_backend.store import Store


class Handler:
    def __init__(self, store: Store):
        self.store = store
        self.is_running = False
        self.handler_task: Optional[Task] = None

    def _done_call_back(self, future: Future):
        if future.exception():
            self.store.bots_manager.logger.exception("handler failed", exc_info=future.exception())

    async def start(self):
        self.is_running = True
        self.handler_task = asyncio.create_task(self.handle_updates())
        self.handler_task.add_done_callback(self._done_call_back)

    async def stop(self):
        self.is_running = False
        await asyncio.wait([self.handler_task], timeout=30)

    async def handle_updates(self):
        while self.is_running or not self.store.bots_manager.app.receivers_queue.empty():
            update = await self.store.bots_manager.app.receivers_queue.get()
            await self.store.bots_manager.handle_updates(update)

import asyncio

from asyncio import Task, Future
from typing import Optional

from kts_backend.store import Store


class Sender:
    def __init__(self, store: Store):
        self.store = store
        self.is_running = False
        self.sender_task: Optional[Task] = None

    def _done_call_back(self, future: Future):
        if future.exception():
            self.store.sender.logger.exception("sender failed", exc_info=future.exception())

    async def start(self):
        self.is_running = True
        self.sender_task = asyncio.create_task(self.send_messages())
        self.sender_task.add_done_callback(self._done_call_back)

    async def stop(self):
        self.is_running = False
        await asyncio.wait([self.sender_task], timeout=1)

    async def send_messages(self):
        while self.is_running:
            message = await self.store.sender.app.senders_queue.get()
            await self.store.sender.send_message(message)

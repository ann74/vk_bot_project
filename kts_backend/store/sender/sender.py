import asyncio

from asyncio import Task
from typing import Optional

from kts_backend.store import Store


class Sender:
    def __init__(self, store: Store):
        self.store = store
        self.is_running = False
        self.sender_task: Optional[Task] = None

    async def start(self):
        self.is_running = True
        self.sender_task = asyncio.create_task(self.send_messages())

    async def stop(self):
        self.is_running = False
        self.sender_task.cancel()

    async def send_messages(self):
        while self.is_running:
            message = await self.store.sender.app.senders_queue.get()
            await self.store.sender.send_message(message)

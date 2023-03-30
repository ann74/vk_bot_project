import asyncio

from asyncio import Task
from typing import Optional

from kts_backend.store import Store


class Handler:
    def __init__(self, store: Store):
        self.store = store
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
            update = await self.store.bots_manager.app.receivers_queue.get()
            await self.store.bots_manager.handle_updates(update)

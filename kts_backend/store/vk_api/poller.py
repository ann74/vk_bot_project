import asyncio

from asyncio import Task, Future
from typing import Optional
from aiohttp import ClientOSError

from kts_backend.store import Store


class Poller:
    def __init__(self, store: Store):
        self.store = store
        self.is_running = False
        self.poll_task: Optional[Task] = None

    def _done_call_back(self, future: Future):
        if future.exception():
            self.store.vk_api.logger.exception(
                "polling failed", exc_info=future.exception()
            )

    async def start(self):
        self.is_running = True
        self.poll_task = asyncio.create_task(self.poll())
        self.poll_task.add_done_callback(self._done_call_back)

    async def stop(self):
        self.is_running = False
        if self.poll_task:
            await asyncio.wait([self.poll_task], timeout=10)  # Не забыть поменять на 30 сек (или 20)

    async def poll(self):
        while self.is_running:
            try:
                await self.store.vk_api.poll()
            except ClientOSError:
                continue
            except Exception as e:
                self.store.vk_api.logger.error("Exception", exc_info=e)

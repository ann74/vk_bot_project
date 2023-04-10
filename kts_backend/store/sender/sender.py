import asyncio
import typing
import pickle

from asyncio import Task
from typing import Optional

from kts_backend.store import Store

if typing.TYPE_CHECKING:
    from kts_backend.web.app import Application

class Sender:
    def __init__(self, store: Store, app: "Application"):
        self.store = store
        self.app = app
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
            async with self.app.rabbitmq.senders_queue.iterator() as queue_iter:
                async for incoming_message in queue_iter:
                    message = pickle.loads(incoming_message.body)
                    await incoming_message.ack()
                    if message.conversation_message_id and not message.text:
                        await self.store.sender.pin_message(message)
                    elif not message.conversation_message_id and not message.text:
                        await self.store.sender.unpin_message(message)
                    else:
                        await self.store.sender.send_message(message)

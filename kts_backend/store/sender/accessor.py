import random
import typing
from typing import Optional

from aiohttp import TCPConnector
from aiohttp.client import ClientSession

from kts_backend.store.base.base_accessor import BaseAccessor
from kts_backend.store.sender.sender import Sender
from kts_backend.store.vk_api.dataclasses import Message

if typing.TYPE_CHECKING:
    from kts_backend.web.app import Application


API_PATH = "https://api.vk.com/method/"


class SenderAccessor(BaseAccessor):
    class Meta:
        name = "sender"

    def __init__(self, app: "Application", *args, **kwargs):
        super().__init__(app, *args, **kwargs)
        self.session: Optional[ClientSession] = None
        self.sender: Optional[Sender] = None

    async def connect(self, app: "Application"):
        self.session = ClientSession(connector=TCPConnector(verify_ssl=False))
        self.sender = Sender(app.store, app)
        self.logger.info("start sending")
        await self.sender.start()

    async def disconnect(self, app: "Application"):
        if self.sender:
            await self.sender.stop()
        if self.session and not self.session.closed:
            await self.session.close()

    @staticmethod
    def _build_query(host: str, method: str, params: dict) -> str:
        url = host + method + "?"
        if "v" not in params:
            params["v"] = "5.131"
        url += "&".join([f"{k}={v}" for k, v in params.items()])
        return url

    async def send_message(self, message: Message) -> None:
        self.logger.info(message)
        if not message.keyboard:
            message.keyboard = ''
        async with self.session.get(
            self._build_query(
                host=API_PATH,
                method="messages.send",
                params={
                    "message": message.text,
                    "access_token": self.app.config.bot.token,
                    "peer_ids": f'{message.peer_id},',
                    "random_id": random.randint(1, 1000000),
                    "keyboard": message.keyboard,
                },
            )
        ) as resp:
            if not resp.ok:
                resp.raise_for_status()
            data = await resp.json()
            self.logger.info(data)
        return data['response'][0]['conversation_message_id']

    async def pin_message(self, message: Message) -> None:
        self.logger.info(message)
        async with self.session.get(
            self._build_query(
                host=API_PATH,
                method="messages.pin",
                params={
                    "access_token": self.app.config.bot.token,
                    "peer_id": message.peer_id,
                    "conversation_message_id": message.conversation_message_id,
                },
            )
        ) as resp:
            if not resp.ok:
                resp.raise_for_status()
            data = await resp.json()
            self.logger.info(data)

    async def unpin_message(self, message: Message) -> None:
        self.logger.info(message)
        async with self.session.get(
            self._build_query(
                host=API_PATH,
                method="messages.unpin",
                params={
                    "access_token": self.app.config.bot.token,
                    "peer_id": message.peer_id,
                },
            )
        ) as resp:
            if not resp.ok:
                resp.raise_for_status()
            data = await resp.json()
            self.logger.info(data)

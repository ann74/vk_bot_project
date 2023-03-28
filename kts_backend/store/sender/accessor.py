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
        self.sender = Sender(app.store)
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
        async with self.session.get(
            self._build_query(
                host=API_PATH,
                method="messages.send",
                params={
                    "message": message.text,
                    "access_token": self.app.config.bot.token,
                    "peer_id": message.peer_id,
                    "random_id": random.randint(1, 1000000),
                    # "user_id": message.user_id,
                },
            )
        ) as resp:
            data = await resp.json()
            self.logger.info(data)

import json
import typing
from typing import Optional

from aiohttp import TCPConnector
from aiohttp.client import ClientSession

from kts_backend.game.models import Player
from kts_backend.store.base.base_accessor import BaseAccessor
from kts_backend.store.vk_api.dataclasses import Update, UpdateObject
from kts_backend.store.vk_api.poller import Poller

if typing.TYPE_CHECKING:
    from kts_backend.web.app import Application

API_PATH = "https://api.vk.com/method/"


class VkApiAccessor(BaseAccessor):
    class Meta:
        name = "vk_api"

    def __init__(self, app: "Application", *args, **kwargs):
        super().__init__(app, *args, **kwargs)
        self.session: Optional[ClientSession] = None
        self.key: Optional[str] = None
        self.server: Optional[str] = None
        self.poller: Optional[Poller] = None
        self.ts: Optional[int] = None

    async def connect(self, app: "Application"):
        self.session = ClientSession(connector=TCPConnector(verify_ssl=False))
        try:
            await self._get_long_poll_service()
        except Exception as e:
            self.logger.error("Exception", exc_info=e)
        self.poller = Poller(app.store)
        self.logger.info("start polling")
        await self.poller.start()

    async def disconnect(self, app: "Application"):
        if self.poller:
            await self.poller.stop()
        if self.session and not self.session.closed:
            await self.session.close()

    @staticmethod
    def _build_query(host: str, method: str, params: dict) -> str:
        url = host + method + "?"
        if "v" not in params:
            params["v"] = "5.131"
        url += "&".join([f"{k}={v}" for k, v in params.items()])
        return url

    async def _get_long_poll_service(self):
        async with self.session.get(
            self._build_query(
                host=API_PATH,
                method="groups.getLongPollServer",
                params={
                    "group_id": self.app.config.bot.group_id,
                    "access_token": self.app.config.bot.token,
                },
            )
        ) as resp:
            data = (await resp.json())["response"]
            self.logger.info(data)
            self.key = data["key"]
            self.server = data["server"]
            self.ts = data["ts"]
            self.logger.info(self.server)

    async def poll(self):
        self.logger.info("new poll request")
        url = self._build_query(
            host=self.server,
            method="",
            params={
                "act": "a_check",
                "key": self.key,
                "ts": self.ts,
                "wait": 30,
            },
        )
        async with self.session.get(url) as resp:
            data = await resp.json()
            self.logger.info(data)
            self.ts = data["ts"]
            raw_updates = data["updates"]
            for raw_update in raw_updates:
                if raw_update["type"] == "message_new":
                    update = Update(
                        type=raw_update["type"],
                        object=UpdateObject(
                            user_id=raw_update["object"]["message"]["from_id"],
                            body=raw_update["object"]["message"]["text"],
                            peer_id=raw_update["object"]["message"]["peer_id"],
                        ),
                    )
                    if raw_update["object"]["message"].get("action"):
                        update.object.action = raw_update["object"]["message"]["action"]["type"]
                        member_id = raw_update["object"]["message"]["action"].get("member_id")
                        if member_id:
                            update.object.user_id = member_id
                    if raw_update["object"]["message"].get("payload"):
                        update.object.button = json.loads(raw_update["object"]["message"]["payload"])["button"]
                else:
                    raise NotImplementedError
                await self.app.rabbitmq.publish_receivers(update)

    async def get_users_from_chat(self, chat_id: int) -> list[Player]:
        async with self.session.get(
            self._build_query(
                host=API_PATH,
                method="messages.getConversationMembers",
                params={
                    "access_token": self.app.config.bot.token,
                    "peer_id": chat_id,
                    "extended": 1,
                },
            )
        ) as resp:
            data = await resp.json()
            users = data["profiles"]
            players = []
            for user in users:
                players.append(
                    Player(
                        vk_id=user["id"],
                        name=user["first_name"],
                        last_name=user["last_name"],
                        score=None,
                    )
                )
        return players

    async def get_user_by_id(self, vk_id: int) -> Player:
        async with self.session.get(
            self._build_query(
                host=API_PATH,
                method="users.get",
                params={
                    "access_token": self.app.config.bot.token,
                    "user_ids": str(vk_id),
                },
            )
        ) as resp:
            data = await resp.json()
            self.logger.info(data)
            player = Player(
                vk_id=vk_id,
                name=data["response"][0]["first_name"],
                last_name=data["response"][0]["last_name"],
            )
        return player

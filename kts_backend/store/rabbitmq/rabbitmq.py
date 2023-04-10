from typing import TYPE_CHECKING, Optional
from aio_pika import connect_robust, RobustConnection, Message as Message_aio_pika
from aio_pika.abc import AbstractChannel, AbstractQueue
import pickle

from kts_backend.store.base.base_accessor import BaseAccessor
from kts_backend.store.vk_api.dataclasses import Update, Message

if TYPE_CHECKING:
    from kts_backend.web.app import Application


class RabbitMQ(BaseAccessor):
    def __init__(self, app: "Application", *args, **kwargs):
        super().__init__(app, *args, **kwargs)
        self.connection: Optional[RobustConnection] = None
        self.chanel: Optional[AbstractChannel] = None
        self.receivers_queue: Optional[AbstractQueue] = None
        self.senders_queue: Optional[AbstractQueue] = None

    async def connect(self, *_: list, **__: dict) -> None:
        self.connection = await connect_robust(
            host=self.app.config.rabbitmq.host,
            port=self.app.config.rabbitmq.port,
            login=self.app.config.rabbitmq.user,
            password=self.app.config.rabbitmq.password,
        )
        self.chanel = await self.connection.channel()
        self.receivers_queue = await self.chanel.declare_queue(name='receivers')
        self.senders_queue = await self.chanel.declare_queue(name='senders')

    async def disconnect(self, *_: list, **__: dict) -> None:
        try:
            await self.connection.close()
        except Exception as e:
            self.logger.error("Exception", exc_info=e)

    async def publish_receivers(self, update: Update):
        await self.chanel.default_exchange.publish(
            Message_aio_pika(body=pickle.dumps(update)),
            routing_key='receivers'
        )

    async def publish_senders(self, message: Message):
        await self.chanel.default_exchange.publish(
            Message_aio_pika(body=pickle.dumps(message)),
            routing_key='senders'
        )


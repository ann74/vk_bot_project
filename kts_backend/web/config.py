import typing
from dataclasses import dataclass

import yaml
import os
from dotenv import load_dotenv

if typing.TYPE_CHECKING:
    from kts_backend.web.app import Application

load_dotenv()

@dataclass
class SessionConfig:
    key: str


@dataclass
class AdminConfig:
    email: str
    password: str


@dataclass
class BotConfig:
    token: str
    group_id: int


@dataclass
class DatabaseConfig:
    host: str
    port: int
    user: str
    password: str
    database: str


@dataclass
class Config:
    admin: AdminConfig
    session: SessionConfig = None
    bot: BotConfig = None
    database: DatabaseConfig = None


def setup_config(app: "Application", config_path: str):
    with open(config_path, "r") as f:
        raw_config = yaml.safe_load(f)

    app.config = Config(
        session=SessionConfig(
            key=raw_config["session"]["key"],
        ),
        admin=AdminConfig(
            email=raw_config["admin"]["email"],
            password=raw_config["admin"]["password"],
        ),
        bot=BotConfig(
            token=os.getenv('BOT_TOKEN'),
            group_id=int(os.getenv('BOT_GROUP_ID')),
        ),
        database=DatabaseConfig(
            host=raw_config["database"]["host"],
            port=raw_config["database"]["port"],
            database=raw_config["database"]["database"],
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
        ),
    )

import typing
from dataclasses import dataclass

import yaml

if typing.TYPE_CHECKING:
    from app.web.app import Application


@dataclass
class SessionConfig:
    key: bytes


@dataclass
class BotConfig:
    token: str
    group_id: int


@dataclass
class DifficultiesConfig:
    title: str
    right_answers_to_win: int
    wrong_answers_to_lose: int


@dataclass
class DatabaseConfig:
    host: str = "localhost"
    port: int = 5432
    user: str = "postgres"
    password: str = "postgres"
    database: str = "project"


@dataclass
class Config:
    session: SessionConfig = None
    bot: BotConfig = None
    database: DatabaseConfig = None
    database_url: str = None


def setup_config(app: "Application", config_path: str):
    with open(config_path, "r") as f:
        raw_config = yaml.safe_load(f)

    app.config = Config(
        session=SessionConfig(key=raw_config["session"]["key"]),
        bot=BotConfig(
            token=raw_config["bot"]["token"],
            group_id=raw_config["bot"]["group_id"]
        ),
        database=DatabaseConfig(
            host=raw_config["database"]["host"],
            port=raw_config["database"]["port"],
            user=raw_config["database"]["user"],
            password=raw_config["database"]["password"],
            database=raw_config["database"]["database"]
        ),
    )
    db_conf = app.config.database
    app.config.database_url = f"postgresql+asyncpg://" \
                              f"{db_conf.user}:" \
                              f"{db_conf.password}@{db_conf.host}:" \
                              f"{db_conf.port}/{db_conf.database}"

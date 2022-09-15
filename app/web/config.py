import typing
from dataclasses import dataclass

import yaml

if typing.TYPE_CHECKING:
    from app.web.app import Application


@dataclass
class SessionConfig:
    key: bytes


@dataclass
class AdminConfig:
    email: str
    password: str


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
    admin: AdminConfig
    difficulty1: DifficultiesConfig
    difficulty2: DifficultiesConfig
    difficulty3: DifficultiesConfig
    session: SessionConfig = None
    bot: BotConfig = None
    database: DatabaseConfig = None
    database_url: str = None


def setup_config(app: "Application", config_path: str):
    with open(config_path, "r") as f:
        raw_config = yaml.safe_load(f)

    app.config = Config(
        admin=AdminConfig(
            email=raw_config["admin"]["email"],
            password=raw_config["admin"]["password"],
        ),
        difficulty1=DifficultiesConfig(
            title=raw_config["difficulty1"]["title"],
            right_answers_to_win=
            raw_config["difficulty1"]["right_answers_to_win"],
            wrong_answers_to_lose=
            raw_config["difficulty1"]["wrong_answers_to_lose"]
        ),
        difficulty2=DifficultiesConfig(
            title=raw_config["difficulty2"]["title"],
            right_answers_to_win=
            raw_config["difficulty2"]["right_answers_to_win"],
            wrong_answers_to_lose=
            raw_config["difficulty2"]["wrong_answers_to_lose"]
        ),
        difficulty3=DifficultiesConfig(
            title=raw_config["difficulty3"]["title"],
            right_answers_to_win=
            raw_config["difficulty3"]["right_answers_to_win"],
            wrong_answers_to_lose=
            raw_config["difficulty3"]["wrong_answers_to_lose"]
        ),
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

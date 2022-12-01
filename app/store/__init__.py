import typing

from app.store.database.database import Database
from app.store.rabbit.rabbitmq import Rabbitmq
from app.store.redis.redis_db import RedisDatabase

if typing.TYPE_CHECKING:
    from app.web.app import Application


class Store:
    def __init__(self, app: "Application"):
        from app.store.quiz.accessor import QuizAccessor
        from app.store.admin.accessor import AdminAccessor
        from app.store.bot.manager import BotManager
        from app.store.smart_peoples.accessor import GameAccessor
        from app.store.vk_api.accessor import VkApiAccessor

        self.app = app
        self.quizzes = QuizAccessor(app)
        self.admins = AdminAccessor(app)
        self.vk_api = VkApiAccessor(app)
        self.game = GameAccessor(app)
        self.bots_manager = BotManager(app)


def setup_store(app: "Application"):
    app.database = Database(app)
    app.redis = RedisDatabase(app)
    app.rabbit = Rabbitmq(app)
    app.on_startup.append(app.database.connect)
    app.on_startup.append(app.redis.connect)
    app.on_startup.append(app.rabbit.connect)
    app.on_cleanup.append(app.redis.disconnect)
    app.on_cleanup.append(app.database.disconnect)
    app.on_cleanup.append(app.rabbit.disconnect)
    app.store = Store(app)

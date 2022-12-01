import json
import random

from typing import Optional, List, TYPE_CHECKING

from aiohttp import TCPConnector
from aiohttp.client import ClientSession

from app.base.base_accessor import BaseAccessor
from app.store.vk_api.dataclasses import (
    Update, UpdateMessage, UpdateCallback, User
)
from app.store.vk_api.poller import Poller

if TYPE_CHECKING:
    from app.web.app import Application


class VkApiAccessor(BaseAccessor):
    def __init__(self, app: "Application", *args, **kwargs):
        super().__init__(app, *args, **kwargs)
        self.session: Optional[ClientSession] = None
        self.key: Optional[str] = None
        self.server: Optional[str] = None
        self.poller: Optional[Poller] = None
        self.ts: Optional[int] = None

    async def connect(self, app: "Application"):
        self.session = ClientSession(connector=TCPConnector(ssl=True))

        await self._get_long_poll_service()
        self.poller = Poller(self.app.store)
        await self.poller.start()

    async def disconnect(self, app: "Application"):
        if self.poller:
            await self.poller.stop()
        if self.session:
            await self.session.close()

    @staticmethod
    def _build_query(host: str, method: str, params: dict) -> str:
        url = host + method + "?"
        if "v" not in params:
            params["v"] = "5.131"
        url += "&".join([f"{k}={v}" for k, v in params.items()])
        return url

    async def _get_long_poll_service(self):
        url = self._build_query(
            host='https://api.vk.com/method/',
            method='groups.getLongPollServer',
            params={'group_id': self.app.config.bot.group_id,
                    'access_token': self.app.config.bot.token})

        async with self.session.get(url) as response:
            data = await response.json()
            self.key = data['response']['key']
            self.server = data['response']['server']
            self.ts = data['response']['ts']

    async def poll(self) -> None:
        url = self._build_query(self.server, '', {
            'act': 'a_check',
            'key': self.key,
            'ts': self.ts,
            'wait': 25
        })

        async with self.session.get(url) as response:
            data = await response.json()
            self.app.logger.info(data)
            if self.ts <= data['ts']:
                self.ts = data['ts']
            for update in data['updates']:
                await self.app.rabbit.publish(json.dumps(update))
            return data['updates']

    async def get_user(self, vk_id: int) -> User:
        url = self._build_query(
            host='https://api.vk.com/method/',
            method='users.get',
            params={
                "user_ids": vk_id,
                "access_token": self.app.config.bot.token
            }
        )

        async with self.session.get(url) as response:
            data = await response.json()
        return User(
            first_name=data["response"][0]["first_name"],
            last_name=data["response"][0]["last_name"]
        )

    async def send_message_event_answer(self, **params) -> None:
        params["access_token"] = self.app.config.bot.token
        url = self._build_query(
            host='https://api.vk.com/method/',
            method='messages.sendMessageEventAnswer',
            params=params
        )
        async with self.session.get(url) as response:
            data = await response.json()
            self.logger.info(data)

    async def send_message(self, **params) -> dict:
        params["random_id"] = random.randint(1, 2 ** 16)
        params["access_token"] = self.app.config.bot.token
        url = self._build_query(
            host='https://api.vk.com/method/',
            method='messages.send',
            params=params
        )

        async with self.session.get(url) as response:
            data = await response.json()
            self.logger.info(data)
        return data

    async def update_message(self, **params) -> None:
        params["random_id"] = random.randint(1, 2 ** 16)
        params["access_token"] = self.app.config.bot.token
        url = self._build_query(
            host='https://api.vk.com/method/',
            method='messages.edit',
            params=params
        )

        async with self.session.get(url) as response:
            data = await response.json()
            self.logger.info(data)

    @staticmethod
    async def build_keyboard(
            buttons: List[List[dict]],
            params: Optional[dict] = None) -> dict:
        if params:
            keyboard = params
        else:
            keyboard = {}
        keyboard["buttons"] = buttons
        return keyboard

    @staticmethod
    async def make_button(params: dict, color: Optional[str] = None) -> dict:
        button = {
            "action": params
        }
        if color:
            button["color"] = color
        return button

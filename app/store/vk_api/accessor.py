import random

from typing import Optional, List, TYPE_CHECKING

from aiohttp import TCPConnector
from aiohttp.client import ClientSession

from app.base.base_accessor import BaseAccessor
from app.store.vk_api.dataclasses import (
    Update, UpdateMessage, UpdateCallback
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
        self.pollers: List[Poller] = []
        self.ts: Optional[int] = None

    async def add_poller(self, poller: Poller):
        self.pollers.append(poller)

    async def remove_poller(self, poller: Poller):
        index = self.pollers.index(poller)
        self.pollers.pop(index)

    async def connect(self, app: "Application"):
        self.session = ClientSession(connector=TCPConnector(ssl=True))

        await self._get_long_poll_service()
        await self.add_poller(Poller(self.app.store))
        await self.pollers[0].start()

    async def disconnect(self, app: "Application"):
        if self.pollers:
            for poller in self.pollers:
                await poller.stop()
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

    async def poll(self) -> List[Optional[Update]]:
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

                updates = list()
                for update in data['updates']:
                    update = await self._create_update(update)
                    if update:
                        updates.append(update)
        return updates

    @staticmethod
    async def _create_update(update: dict) -> Optional[Update]:
        if update['type'] == 'message_new':
            from_id = update['object']['message']['from_id']
            text = update['object']['message']['text']
            peer_id = update['object']['message']['peer_id']
            action = update['object']['message']['action']
            return Update(
                type=update['type'],
                object=UpdateMessage(
                    text=text,
                    user_id=from_id,
                    peer_id=peer_id,
                    action=action
                ))
        elif update['type'] == 'message_event':
            from_id = update['object']['user_id']
            peer_id = update['object']['peer_id']
            payload = update['object']['payload']
            message_id = \
                update['object'].get("conversation_message_id")
            return Update(
                type=update['type'],
                object=UpdateCallback(
                    user_id=from_id,
                    peer_id=peer_id,
                    payload=payload,
                    message_id=message_id
                ))

    async def send_message(self, **params) -> None:
        params["random_id"] = random.randint(1, 2 ** 16)
        params["access_token"] = self.app.config.bot.token
        url = self._build_query(
            host='https://api.vk.com/method/',
            method='messages.send',
            params=params
        )

        if self.session is not None:
            async with self.session.get(url) as response:
                data = await response.json()
                self.logger.info(data)

    async def update_message(self, **params) -> None:
        params["random_id"] = random.randint(1, 2 ** 16)
        params["access_token"] = self.app.config.bot.token
        url = self._build_query(
            host='https://api.vk.com/method/',
            method='messages.edit',
            params=params
        )
        if self.session is not None:
            async with self.session.get(url) as response:
                data = await response.json()
                self.logger.info(data)

    @staticmethod
    async def build_keyboard(
            buttons: List[List[dict]],
            **params) -> dict:
        keyboard = params
        keyboard["buttons"] = buttons
        return keyboard

    @staticmethod
    async def make_button(color: str = None, **params) -> dict:
        button = {
            "action": params
        }
        if color:
            button["color"] = color
        return button

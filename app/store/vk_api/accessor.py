import typing
from random import randint
from typing import Optional

from aiohttp import TCPConnector
from aiohttp.client import ClientSession

from app.base.base_accessor import BaseAccessor
from app.store.vk_api.dataclasses import Message, Update, UpdateObject, UpdateMessage
from app.store.vk_api.poller import Poller

if typing.TYPE_CHECKING:
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
        if self.session is not None:
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

    async def poll(self):
        url = self._build_query(self.server, '', {
            'act': 'a_check',
            'key': self.key,
            'ts': self.ts,
            'wait': 25
        })

        async with self.session.get(url) as response:
            data = await response.json()
            if self.ts <= data['ts']:
                self.ts = data['ts']

                updates = list()
                for update in data['updates']:
                    if update['type'] == 'message_new':
                        from_id = update['object']['message']['from_id']
                        text = update['object']['message']['text']
                        updates.append(Update(
                            type=update['type'],
                            object=UpdateObject(message=UpdateMessage(
                                text=text,
                                id=1,
                                from_id=from_id))))

                if len(updates):
                    await self.app.store.bots_manager.handle_updates(updates)

    async def send_message(self, message: Message) -> None:
        url = self._build_query(
            host='https://api.vk.com/method/',
            method='messages.send',
            params={
                'peer_id': message.user_id,
                'message': message.text,
                'random_id': randint(0, 4096),
                'access_token': self.app.config.bot.token
            }
        )

        if self.session is not None:
            async with self.session.get(url) as response:
                data = await response.json()

from dataclasses import dataclass
from typing import Optional, Union


@dataclass
class Message:
    peer_id: int
    text: str


@dataclass
class User:
    first_name: str
    last_name: str


@dataclass
class UpdateObject:
    user_id: int
    peer_id: int


@dataclass
class UpdateMessage(UpdateObject):
    text: str
    action: Optional[dict] = None
    message_id: Optional[str] = None


@dataclass
class UpdateCallback(UpdateObject):
    payload: dict
    message_id: Optional[str] = None
    event_id: Optional[str] = None


@dataclass
class Update:
    type: str
    object: Union[UpdateMessage, UpdateCallback]

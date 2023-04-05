from dataclasses import dataclass
from typing import Optional, Union


@dataclass
class UpdateObject:
    user_id: int
    peer_id: int
    body: Optional[str] = None
    action: Optional[str] = None
    button: Optional[str] = None
    event_id: Optional[str] = None
    conversation_message_id: Optional[int] = None


@dataclass
class Update:
    type: str
    object: UpdateObject


@dataclass
class Message:
    peer_id: int
    text: Optional[str] = None
    user_id: Optional[int] = None
    keyboard: Optional[str] = None
    event_id: Optional[str] = None
    conversation_message_id: Optional[int] = None

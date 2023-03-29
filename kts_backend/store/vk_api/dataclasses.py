from dataclasses import dataclass
from typing import Optional


@dataclass
class UpdateObject:
    id: int
    user_id: int
    body: str
    peer_id: str
    action: Optional[str]


@dataclass
class Update:
    type: str
    object: UpdateObject


@dataclass
class Message:
    text: str
    peer_id: str
    user_id: Optional[int] = None
    keyboard: Optional[str] = None

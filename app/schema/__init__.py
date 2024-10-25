from enum import Enum
from typing import Optional, Dict

from pydantic import BaseModel, Field


class ReceiveMessage(BaseModel):
    type_: str = Field(alias="type")
    content: str
    kwargs: Optional[Dict]



from pydantic import BaseModel
from datetime import datetime

class Message(BaseModel):
    created_at: datetime
    role: str
    content: str


class Conversation(BaseModel):
    chat_id: str
    created_at: datetime
    messages: list[Message]
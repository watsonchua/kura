from pydantic import BaseModel, Field, computed_field
from datetime import datetime
import uuid
from typing import Union


class Message(BaseModel):
    created_at: datetime
    role: str
    content: str


class Conversation(BaseModel):
    chat_id: str
    created_at: datetime
    messages: list[Message]


class ConversationSummary(BaseModel):
    chat_id: str
    task_description: str
    user_request: str
    metadata: dict


class Cluster(BaseModel):
    id: str = Field(
        default_factory=lambda: uuid.uuid4().hex,
    )
    name: str
    description: str
    chat_ids: list[str]
    parent_id: Union[str, None]

    @computed_field
    def count(self) -> int:
        return len(self.chat_ids)


class GeneratedCluster(BaseModel):
    name: str
    summary: str


class CachedCluster(Cluster):
    umap_embedding: list[float]

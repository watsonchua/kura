from pydantic import BaseModel


class ConversationSummary(BaseModel):
    chat_id: str
    summary: str
    metadata: dict


class GeneratedSummary(BaseModel):
    summary: str

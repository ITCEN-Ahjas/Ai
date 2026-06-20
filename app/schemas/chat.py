from pydantic import BaseModel
from typing import Literal

class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str

class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []

class ChatResponse(BaseModel):
    reply: str

class SuggestRequest(BaseModel):
    message: str
    reply: str

class SuggestResponse(BaseModel):
    questions: list[str]

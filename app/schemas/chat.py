from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    model: str
    messages: List[Message]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = None
    # 其他 OpenAI 参数可按需添加

class Choice(BaseModel):
    index: int
    message: Message
    finish_reason: Optional[str] = None

class ChatResponse(BaseModel):
    id: str
    object: str
    model: str
    choices: List[Choice]
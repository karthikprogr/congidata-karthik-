from pydantic import BaseModel, Field
from typing import Any, Optional

class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    data: Optional[list[dict]] = None

class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)

class AIResponse(BaseModel):
    task_type: str
    status: str
    type: str
    data: Any
    code: Optional[str] = None
    error: Optional[str] = None

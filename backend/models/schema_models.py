from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Any, Dict
from datetime import datetime

# Authentication Schemas
class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, description="Password must be at least 6 characters")

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    email: EmailStr
    role: str
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
    user_id: Optional[int] = None
    role: Optional[str] = None


# Document Schemas
class DocumentOut(BaseModel):
    id: str
    filename: str
    file_type: str
    file_size: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


# Chat Schemas
class MessageCreate(BaseModel):
    content: str

class MessageOut(BaseModel):
    id: str
    session_id: str
    role: str
    content: str
    sources: Optional[Any] = None  # List/dict structure of sources
    created_at: datetime

    class Config:
        from_attributes = True

class ChatSessionCreate(BaseModel):
    title: str

class ChatSessionOut(BaseModel):
    id: str
    title: str
    created_at: datetime

    class Config:
        from_attributes = True

class ChatSessionDetail(ChatSessionOut):
    messages: List[MessageOut] = []

    class Config:
        from_attributes = True


# Extra AI Tool Responses
class SummaryResponse(BaseModel):
    summary: str

class KeywordsResponse(BaseModel):
    keywords: List[str]

class QuestionsResponse(BaseModel):
    questions: List[str]


# Admin Dashboard Schemas
class AdminStats(BaseModel):
    total_users: int
    total_documents: int
    total_queries: int
    system_stats: Dict[str, Any]

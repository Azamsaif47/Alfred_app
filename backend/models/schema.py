from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Text, JSON, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
import uuid
from pydantic import BaseModel
from typing import List , Dict
Base = declarative_base()

# Database Models
class MessageModel(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    thread_id = Column(UUID(as_uuid=True), ForeignKey('threads.thread_id'), nullable=False)
    role = Column(String(255), nullable=True)
    message_content = Column(Text, nullable=False)
    response_metadata = Column(JSON)
    message_id = Column(UUID(as_uuid=True), default=uuid.uuid4, nullable=False)

class ThreadModel(Base):
    __tablename__ = "threads"
    thread_id = Column(UUID(as_uuid=True), primary_key=True)
    name = Column(String)

class ThreadRequest(BaseModel):
    thread_id: uuid.UUID


class UserInput(BaseModel):
    user_input: str
    thread_id: uuid.UUID
    thread_name: str

class MessageCreate(BaseModel):
    thread_id: uuid.UUID
    role: str
    message_content: str
    response_metadata: dict
    message_id: uuid.UUID

class ThreadCreate(BaseModel):
    thread_id: uuid.UUID
    name: str

class ListThreads(BaseModel):
    thread_id: uuid.UUID
    name: str

class MessageListResponse(BaseModel):
    id: int
    thread_id: uuid.UUID
    role: str
    message_content: str
    response_metadata: dict
    message_id: uuid.UUID

class DeleteThreadRequest(BaseModel):
    thread_id: uuid.UUID
    name: str

class UpdateThreadRequest(BaseModel):
    thread_id: uuid.UUID
    new_name: str

class GetMessagesResponse(BaseModel):
    response: List[MessageListResponse]  # List of message objects
    sources: List[Dict]



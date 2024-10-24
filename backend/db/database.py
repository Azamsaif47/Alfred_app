from sqlalchemy.ext.asyncio import AsyncSession, async_session
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
import uuid
from dotenv import load_dotenv
import os

from models import (
   MessageModel,
   ThreadModel,
   MessageCreate
)

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session

async def save_thread_to_db(thread: ThreadModel, db: AsyncSession):
    async with db.begin():
        db.add(thread)  # Add the thread to the session
        await db.commit()  # Commit the transaction

async def thread_exists(thread_id: uuid.UUID, db: AsyncSession) -> bool:
    result = await db.execute(text("SELECT 1 FROM threads WHERE thread_id = :thread_id"), {"thread_id": thread_id})
    return result.fetchone() is not None

async def delete_thread_from_db(thread_id: uuid.UUID, db: AsyncSession):
    async with db.begin():
        await db.execute(text("DELETE FROM threads WHERE thread_id = :thread_id"), {"thread_id": thread_id})

async def save_message_to_db(message: MessageCreate):
    async with async_session() as session:
        message_entry = MessageModel(
            thread_id=message.thread_id,
            role=message.role,
            message_content=message.message_content,
            response_metadata=message.response_metadata,
            message_id=message.message_id  # Use the provided message_id
        )
        session.add(message_entry)
        await session.commit()
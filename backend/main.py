from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
import logging
import re
import json
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Text, JSON, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import text
from assistant import agent
import uuid
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
print(DATABASE_URL)

engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()


async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session

# Database Models
class MessageModel(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, autoincrement=True)
    thread_id = Column(UUID(as_uuid=True), ForeignKey('threads.thread_id'), nullable=False)
    role = Column(String(255), nullable=True)
    message_content = Column(Text, nullable=False)
    response_metadata = Column(JSON)

class ThreadModel(Base):
    __tablename__ = "threads"
    thread_id = Column(UUID(as_uuid=True), primary_key=True)
    name = Column(String)


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

class DeleteThreadRequest(BaseModel):
    thread_id: uuid.UUID
    name: str

class UpdateThreadRequest(BaseModel):
    thread_id: uuid.UUID
    new_name: str



async def save_message_to_db(message: MessageCreate):
    print(f'The save message for db: {message}')
    async with async_session() as session:

        message_entry = MessageModel(
            thread_id=message.thread_id,
            role=message.role,
            message_content=message.message_content,
            response_metadata=message.response_metadata
        )
        session.add(message_entry)
        await session.commit()


async def save_thread_to_db(thread: ThreadCreate):
    async with async_session() as session:
        session.add(ThreadModel(**thread.dict()))
        await session.commit()

async def thread_exists(thread_id: uuid.UUID) -> bool:
    async with async_session() as session:
        result = await session.execute(text("SELECT 1 FROM threads WHERE thread_id = :thread_id"), {"thread_id": thread_id})
        return result.fetchone() is not None

async def delete_thread_from_db(thread_id: uuid.UUID):
    async with async_session() as session:
        await session.execute(text("DELETE FROM threads WHERE thread_id = :thread_id"), {"thread_id": thread_id})
        await session.commit()


async def process_ai_messages(messages, thread_id):

    if not messages:
        print(f"No messages found for thread_id: {thread_id}")
        return


    human_messages = []
    tool_messages = []
    ai_messages = []


    for message in messages:
        message_type = type(message).__name__.replace("Message", "")

        if message_type == "Human":
            human_messages.append(message)
        elif message_type == "Tool":
            tool_messages.append(message)
        elif message_type == "AI":
            ai_messages.append(message)


    last_human_messages = human_messages[-3:]
    last_tool_messages = tool_messages[-3:]
    last_ai_messages = ai_messages[-3:]


    last_three_messages = last_human_messages + last_tool_messages + last_ai_messages

    print(f"Processing the last messages for thread_id {thread_id}: {last_three_messages}")


    for message in last_three_messages:
        print(f"Saving message: {message.content}")
        await save_message_to_db(MessageCreate(
            thread_id=thread_id,
            role=type(message).__name__.replace("Message", ""),
            message_content=message.content,
            response_metadata=message.response_metadata
        ))




async def process_sources(messages):
    print(f"Total messages received: {len(messages)}")


    if not messages:
        print("No messages received.")
        return

    tool_message_content = None


    for message in reversed(messages):
        message_type = type(message).__name__.replace("Message", "")

        if message_type == "Tool":
            tool_message_content = message.content
            break


    if tool_message_content is None:
        print("No Tool message found in the received messages.")
        return

    print("Raw tool_message_content:", tool_message_content)

    try:

        docu = json.loads(tool_message_content)
    except json.JSONDecodeError as e:
        print(f"JSON decoding error: {e}")
        return

    documents = docu.get("context", [])
    document_list = []


    for doc_str in documents:

        matches = re.findall(r"metadata=\{(.*?)\}, page_content='(.*?)'", doc_str, re.DOTALL)
        for metadata_match, page_content_match in matches:
            metadata_str = f"{{{metadata_match}}}"
            try:

                metadata_dict = eval(metadata_str)
                document_list.append({
                    'metadata': metadata_dict,
                    'page_content': page_content_match
                })
            except Exception as e:
                print(f"Error converting metadata to dict: {e}")

    print(document_list)
    return document_list


async def run_ai_thread(user_input: str, thread_id: uuid.UUID, thread_name: str):
    if not await thread_exists(thread_id):
        await save_thread_to_db(ThreadCreate(thread_id=thread_id, name=thread_name))

    res = await agent.ainvoke({"messages": [("human", user_input)]},
                              config={"configurable": {"thread_id": str(thread_id), "thread_name": thread_name}})

    await process_ai_messages(res['messages'], thread_id)
    sources = await process_sources(res['messages'])

    return res['messages'][-1].content if res['messages'] else None, sources



@app.post("/run_ai_thread/")
async def run_ai(user_input: UserInput):
    try:
        print(f"Received input: {user_input}")
        response, sources = await run_ai_thread(user_input.user_input, user_input.thread_id, user_input.thread_name)
        print(f"AI thread started successfully. Response: {response}, Sources: {sources}")
        return {
            "message": "AI thread started successfully.",
            "response": response,
            "sources": sources
        }
    except Exception as e:
        print(f"Error running AI thread: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/threads/", response_model=list[ListThreads])
async def list_threads(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(text("SELECT thread_id, name FROM threads"))
        return [{"thread_id": thread.thread_id, "name": thread.name} for thread in result.fetchall()]
    except Exception as e:
        # Log the error if necessary
        raise HTTPException(status_code=500, detail="An error occurred while fetching threads: " + str(e))

@app.post("/create_thread/", response_model=ThreadCreate)
async def create_thread():
    try:
        thread = ThreadCreate(thread_id=uuid.uuid4(), name="new_chat")
        await save_thread_to_db(thread)
        return thread
    except Exception as e:
        raise HTTPException(status_code=500, detail="An error occurred while creating the thread: " + str(e))



@app.post("/messages/", response_model=list[MessageListResponse])
async def get_messages(thread_request: ThreadRequest, db: AsyncSession = Depends(get_db)):
    thread_id = thread_request.thread_id

    try:
        result = await db.execute(
            text("SELECT * FROM messages WHERE thread_id = :thread_id AND role != 'Tool'"),
            {"thread_id": thread_id}
        )

        messages = result.fetchall()

        if not messages:
            raise HTTPException(status_code=404, detail="No messages found for this thread ID.")

        return [
            MessageListResponse(
                id=message.id,
                thread_id=message.thread_id,
                role=message.role,
                message_content=message.message_content,
                response_metadata=message.response_metadata
            )
            for message in messages
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail="An error occurred while fetching messages: " + str(e))



@app.delete("/delete_thread/")
async def delete_thread(thread_request: DeleteThreadRequest, db: AsyncSession = Depends(get_db)):
    thread_id = thread_request.thread_id
    thread_name = thread_request.name

    try:
        result = await db.execute(
            text("SELECT * FROM threads WHERE thread_id = :thread_id AND name = :name"),
            {"thread_id": thread_id, "name": thread_name}
        )
        thread = result.fetchone()

        if not thread:
            raise HTTPException(status_code=404, detail="Thread not found or name does not match.")

        delete_messages_result = await db.execute(
            text("DELETE FROM messages WHERE thread_id = :thread_id"),
            {"thread_id": thread_id}
        )
        logging.info(f"Deleted {delete_messages_result.rowcount} messages for thread_id: {thread_id}")

        delete_thread_result = await db.execute(
            text("DELETE FROM threads WHERE thread_id = :thread_id"),
            {"thread_id": thread_id}
        )
        logging.info(f"Deleted thread with thread_id: {thread_id}.")

        await db.commit()
        return {"detail": "Thread and its messages deleted successfully."}

    except Exception as e:
        logging.error(f"Error deleting thread and messages: {str(e)}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete thread and messages.")


@app.put("/update_thread_name/")
async def update_thread_name(update_request: UpdateThreadRequest, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(
            text("SELECT * FROM threads WHERE thread_id = :thread_id"),
            {"thread_id": update_request.thread_id}
        )
        thread = result.fetchone()

        if not thread:
            raise HTTPException(status_code=404, detail="Thread not found.")

        await db.execute(
            text("UPDATE threads SET name = :new_name WHERE thread_id = :thread_id"),
            {"new_name": update_request.new_name, "thread_id": update_request.thread_id}
        )
        await db.commit()

        return {"detail": "Thread name updated successfully."}

    except Exception as e:
        logging.error(f"Error updating thread name: {str(e)}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update thread name.")


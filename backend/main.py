from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict
import time
import logging
import re
import json
import ast
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Text, JSON, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import text
from langchain_core.messages import HumanMessage, ToolMessage, AIMessage
from assistant import agent
import uuid
import logging
from json_repair import repair_json
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
    message_id = Column(UUID(as_uuid=True), default=uuid.uuid4, nullable=False)

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


async def save_message_to_db(message: MessageCreate):
    print(f'The save message for db: {message}')
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

    # Separate messages into their respective types
    human_messages = [msg for msg in messages if isinstance(msg, HumanMessage)]
    tool_messages = [msg for msg in messages if isinstance(msg, ToolMessage)]
    ai_messages = [msg for msg in messages if isinstance(msg, AIMessage)]

    messages_to_process = []

    # Get the length of messages to calculate the indices for the conditions
    total_messages = len(messages)

    # Last human message (if it is present in the last 3 messages)
    if human_messages:
        last_human_message = human_messages[-1]
        # Check if the human message is within the last 3 messages
        if messages.index(last_human_message) >= max(0, total_messages - 5):
            messages_to_process.append(last_human_message)

    # Last tool message (if it is present in the last 2 messages)
    if tool_messages:
        last_tool_message = tool_messages[-1]
        # Check if the tool message is within the last 2 messages
        if messages.index(last_tool_message) >= max(0, total_messages - 3):
            messages_to_process.append(last_tool_message)

    # Last AI message (only if it is the last message in the list)
    if ai_messages:
        last_ai_message = ai_messages[-1]
        # Check if the AI message is the last message
        if messages.index(last_ai_message) == total_messages - 1:
            messages_to_process.append(last_ai_message)

    # Limit to one human, one AI, and one tool message
    unique_messages = {}
    for message in messages_to_process:
        role = type(message).__name__.replace("Message", "")
        if role not in unique_messages:
            unique_messages[role] = message

    # Get only the unique messages to process
    messages_to_process = list(unique_messages.values())

    # If no messages meet the conditions, skip saving
    if not messages_to_process:
        return

    # Generate a single UUID for this group of messages
    message_id = uuid.uuid4()

    # Save the messages to the database with the same message_id
    for message in messages_to_process:
        await save_message_to_db(MessageCreate(
            thread_id=thread_id,  # Ensure thread_id is passed
            role=type(message).__name__.replace("Message", ""),  # Convert class name to role
            message_content=message.content,
            response_metadata=message.response_metadata or {},
            message_id=message_id  # Use the generated message_id for all messages
        ))



async def process_sources(messages):

    if not messages:
        print("No messages received.")
        return

    tool_message_content = None

    # Look at only the last three messages
    for message in messages[-2:]:  # Slicing to get the last three messages
        message_type = type(message).__name__.replace("Message", "")

        if message_type == "Tool":
            tool_message_content = message.content
            break

    if tool_message_content is None:
        print("No Tool message found in the last three messages.")
        return

    try:
        docu = json.loads(tool_message_content)
    except json.JSONDecodeError as e:
        print(f"JSON decoding error: {e}")
        return

    documents = docu.get("context", [])
    document_list = []

    for doc_str in documents:
        # Check if doc_str is a string
        if not isinstance(doc_str, str):
            print(f"Expected string but got {type(doc_str).__name__}: {doc_str}")
            continue  # Skip non-string values

        matches = re.findall(r"metadata=\{(.*?)\}, page_content='(.*?)'", doc_str, re.DOTALL)
        for metadata_match, page_content_match in matches:
            metadata_str = f"{{{metadata_match}}}"
            try:
                metadata_dict = eval(metadata_str)  # Use caution with eval
                document_list.append({
                    'metadata': metadata_dict,
                    'page_content': page_content_match
                })
            except Exception as e:
                print(f"Error converting metadata to dict: {e}")

    print(document_list)
    return document_list


async def run_ai_thread(user_input: str, thread_id: uuid.UUID, thread_name: str):
    start_time = time.time()

    # Check if thread exists
    thread_exists_start = time.time()
    if not await thread_exists(thread_id):
        await save_thread_to_db(ThreadCreate(thread_id=thread_id, name=thread_name))
    thread_exists_duration = time.time() - thread_exists_start
    print(f"[DEBUG] Time taken to check and save thread: {thread_exists_duration:.4f} seconds")

    # Invoke the AI agent
    ai_invoke_start = time.time()
    res = await agent.ainvoke(
        {"messages": [("human", user_input)]},
        config={"configurable": {"thread_id": str(thread_id), "thread_name": thread_name}}
    )
    ai_invoke_duration = time.time() - ai_invoke_start
    print(f"[DEBUG] Time taken for AI invocation: {ai_invoke_duration:.4f} seconds")

    # Process AI messages
    process_ai_messages_start = time.time()
    await process_ai_messages(res['messages'], thread_id)
    process_ai_messages_duration = time.time() - process_ai_messages_start
    print(f"[DEBUG] Time taken to process AI messages: {process_ai_messages_duration:.4f} seconds")

    # Process sources
    process_sources_start = time.time()
    sources = await process_sources(res['messages'])
    process_sources_duration = time.time() - process_sources_start
    print(f"[DEBUG] Time taken to process sources: {process_sources_duration:.4f} seconds")

    total_duration = time.time() - start_time
    print(f"[DEBUG] Total time taken for run_ai_thread: {total_duration:.4f} seconds")

    return res['messages'][-1].content if res['messages'] else None, sources


async def get_messages(thread_request, db: AsyncSession):
    thread_id = thread_request.thread_id

    try:
        # Log the thread_id being processed
        logging.info(f"Fetching messages for thread_id: {thread_id}")

        # Fetch messages from the database
        result = await db.execute(
            text("SELECT * FROM messages WHERE thread_id = :thread_id ORDER BY id ASC;"),
            {"thread_id": thread_id}
        )
        messages = result.fetchall()

        # Log the fetched messages
        logging.info(f"Fetched messages: {messages}")

        if not messages:
            raise HTTPException(status_code=404, detail="No messages found for this thread ID.")

        response = []  # List to hold message objects
        sources = []  # List to hold source information

        for message in messages:
            if message.role == 'Tool':
                # Log the tool-related message
                logging.info(f"Processing tool message: {message}")

                tool_info = extract_tool_info(message)

                # Ensure tool_info is a list of dictionaries
                if isinstance(tool_info, list) and all(isinstance(item, dict) for item in tool_info):
                    sources.extend(tool_info)  # Append each dict to the sources list
                else:
                    raise ValueError("Tool info should be a list of dictionaries")

            else:
                # Log the non-tool message
                logging.info(f"Processing regular message: {message}")

                # Ensure response_metadata is a valid dictionary
                try:
                    response_metadata = repair_json(str(message.response_metadata))
                    if not isinstance(response_metadata, dict):
                        response_metadata = {}  # If not a dict, assign an empty dict
                except Exception as e:
                    logging.error(f"Error repairing response_metadata: {e}")
                    response_metadata = {}  # Handle cases where repair_json fails

                # Append message details to the response list, including message_id
                response.append({
                    "id": message.id,
                    "thread_id": message.thread_id,
                    "role": message.role,
                    "message_content": message.message_content,
                    "response_metadata": response_metadata,  # Ensure it's a valid dict
                    "message_id": message.message_id  # Include message_id in the response
                })

        logging.info(f"Response: {response}")
        logging.info(f"Sources: {sources}")

        # Return both response and sources in the dictionary
        return {
            "response": response,
            "sources": sources
        }

    except Exception as e:
        logging.error(f"An error occurred: {e}", exc_info=True)  # Log the full traceback
        raise HTTPException(status_code=500, detail="An error occurred while fetching messages.")




def extract_tool_info(message):
    try:
        # Directly access message_id and context from the message object
        message_id = message.message_id  # Extract the message_id
        message_content = message.message_content  # Get the message_content

        # Parse message_content to extract context
        message_dict = eval(message_content)  # Ensure this is safe
        context = message_dict.get("context", [])
    except Exception as e:
        print(f"Error parsing message content: {e}")
        return []

    document_list = []

    for doc_str in context:
        # Use regex to extract the metadata and page_content from each document string
        matches = re.findall(r"metadata=\{(.*?)\}, page_content='(.*?)'", doc_str, re.DOTALL)
        for metadata_match, page_content_match in matches:
            # Clean up the metadata string if necessary
            metadata_match = metadata_match.replace("\\", "\\\\").replace("\n", "")  # Replace \ and remove newlines

            # Convert the metadata string to a dictionary using ast.literal_eval (safer than eval)
            try:
                metadata_dict = ast.literal_eval(f"{{{metadata_match}}}")
                document_list.append({
                    'source': metadata_dict.get('source'),
                    'page_content': page_content_match,
                    'message_id': message_id  # Include message_id in each document entry
                })
            except Exception as e:
                print(f"Error converting metadata to dict: {e} - metadata: {metadata_match}")

    return document_list



@app.post("/run_ai_thread/")
async def run_ai(user_input: UserInput):
    try:
        response, sources = await run_ai_thread(user_input.user_input, user_input.thread_id, user_input.thread_name)
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



@app.post("/messages/", response_model=GetMessagesResponse)
async def fetch_messages(thread_request: ThreadRequest, db: AsyncSession = Depends(get_db)):
    return await get_messages(thread_request, db)



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


if __name__ == "__main__":
    import uvicorn
    # Start the FastAPI app using uvicorn if the script is run directly
    uvicorn.run(app, host="127.0.0.1", port=8000)
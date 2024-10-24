from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession , async_session
from sqlalchemy import text

from models import (
   ThreadModel,
   MessageModel,
   UserInput,
   ListThreads,
   ThreadCreate,
   GetMessagesResponse,
   DeleteThreadRequest,
   UpdateThreadRequest,
   ThreadRequest
)

from db import save_thread_to_db, get_db
from utils import (
    run_ai_thread,
    get_messages,
)



import uuid
import logging

router = APIRouter()

@router.post("/run_ai_thread/")
async def run_ai(user_input: UserInput, db: AsyncSession = Depends(get_db)):
    try:
        # Pass the 'db' session to the 'run_ai_thread' function
        response, sources = await run_ai_thread(user_input.user_input, user_input.thread_id, user_input.thread_name, db)

        return {
            "message": "AI thread started successfully.",
            "response": response,
            "sources": sources
        }
    except Exception as e:
        print(f"Error running AI thread: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/threads/", response_model=list[ListThreads])
async def list_threads(db: AsyncSession = Depends(get_db)):
    print("GET /threads/ called")
    try:
        result = await db.execute(text("SELECT thread_id, name FROM threads"))
        return [{"thread_id": thread.thread_id, "name": thread.name} for thread in result.fetchall()]
    except Exception as e:
        # Log the error if necessary
        raise HTTPException(status_code=500, detail="An error occurred while fetching threads: " + str(e))


@router.post("/create_thread/", response_model=ThreadCreate)
async def create_thread(db: AsyncSession = Depends(get_db)):
    try:
        # Create an instance of the SQLAlchemy model (ThreadModel)
        thread = ThreadModel(thread_id=uuid.uuid4(), name="new_chat")

        # Pass the SQLAlchemy model to the save_thread_to_db function
        await save_thread_to_db(thread, db)

        # Return the Pydantic model for response
        return ThreadCreate(thread_id=thread.thread_id, name=thread.name)
    except Exception as e:
        raise HTTPException(status_code=500, detail="An error occurred while creating the thread: " + str(e))


@router.post("/messages/", response_model=GetMessagesResponse)
async def fetch_messages(thread_request: ThreadRequest, db: AsyncSession = Depends(get_db)):
    return await get_messages(thread_request, db)



@router.delete("/delete_thread/")
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


@router.put("/update_thread_name/")
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
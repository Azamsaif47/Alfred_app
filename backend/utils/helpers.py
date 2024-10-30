from langchain_core.messages import HumanMessage, ToolMessage, AIMessage
import uuid
from db import save_message_to_db , save_thread_to_db , thread_exists
from models import MessageCreate , ThreadCreate
from sqlalchemy.ext.asyncio import AsyncSession
from services import agent
from fastapi import HTTPException
import time
import logging
import re
import json
import ast
from json_repair import repair_json
from sqlalchemy import text

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


async def run_ai_thread(user_input: str, thread_id: uuid.UUID, thread_name: str, db: AsyncSession):
    if not await thread_exists(thread_id, db):
        await save_thread_to_db(ThreadCreate(thread_id=thread_id, name=thread_name), db)

    res = await agent.ainvoke(
        {"messages": [("human", user_input)]},
        config={"configurable": {"thread_id": str(thread_id), "thread_name": thread_name}}
    )

    await process_ai_messages(res['messages'], thread_id)

    sources = await process_sources(res['messages'])

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
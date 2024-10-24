
from .schema import (
    MessageModel,
    ThreadModel,
    UserInput,
    ListThreads,
    ThreadCreate,
    GetMessagesResponse,
    DeleteThreadRequest,
    UpdateThreadRequest,
    ThreadRequest,
    MessageCreate,
    MessageListResponse,
    Base
)

# Define the models for use
__all__ = [
    'MessageModel',
    'ThreadModel',
    'UserInput',
    'ListThreads',
    'ThreadCreate',
    'GetMessagesResponse',
    'DeleteThreadRequest',
    'UpdateThreadRequest',
    'ThreadRequest',
    'MessageCreate',
    'MessageListResponse',
    'Base'
]

# Optional: Add any initialization code if necessary
# For example, you can set up logging or load configurations

import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("Models initialized.")
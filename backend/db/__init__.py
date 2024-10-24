
from .database import (
    save_thread_to_db,
    save_message_to_db,
    thread_exists,
    delete_thread_from_db,
    get_db
)

# Define the models for use
__all__ = [
    'save_thread_to_db',
    'save_message_to_db',
    'thread_exists',
    'delete_thread_from_db',
    'get_db'
]

# Optional: Add any initialization code if necessary
# For example, you can set up logging or load configurations

import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("database initialized.")
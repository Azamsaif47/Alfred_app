# Import models and functions from schema.py
from main import (
    engine,
    async_session,
    app
)

# Define the models for use
__all__ = [
    'engine',
    'async_session',
    'get_db',
    'app',
]

# Optional: Add any initialization code if necessary
# For example, you can set up logging or load configurations

import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("App initialized.")
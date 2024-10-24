# Import classes and functions from modules
from .assistant import agent
from .tools import (
    list_contacts,
    create_contact,
    get_contact_details,
    find_contact,
    send_email,
    generate_chart,
    retriever_tool,
)

# Define the public API of the services package
__all__ = [
    'agent',
    'list_contacts',
    'create_contact',
    'get_contact_details',
    'find_contact',
    'send_email',
    'generate_chart',
    'retriever_tool',
]

# Optional: Add any initialization code if necessary
# For example, you can set up logging or load configurations
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("services initialized.")
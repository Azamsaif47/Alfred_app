from fastapi import APIRouter

# Import the router from the API module
from .api import router as api_router

# Create a main router to include all your sub-routers
main_router = APIRouter()

# Include the API router with a prefix and tags
main_router.include_router(api_router, prefix="/api", tags=["API"])

__all__ = ["main_router"]


import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("router initialized.")
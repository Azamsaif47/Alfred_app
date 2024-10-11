from logging.config import fileConfig
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from alembic import context
from ..main import Base

# This is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
fileConfig(config.config_file_name)

# Add your model's MetaData object here
target_metadata = Base.metadata

# Define the connection string for your database
DATABASE_URL = "postgresql+asyncpg://postgres:admin@localhost:5432/alfred"

async def run_migrations_online():
    connectable = create_async_engine(DATABASE_URL, future=True)

    async with connectable.connect() as connection:
        await connection.run_sync(context.configure, connection=connection)
        await context.run_migrations()

def main():
    asyncio.run(run_migrations_online())

# Run migrations
if __name__ == "__main__":
    main()

"""database initial migration

Revision ID: 2878a3a212c2
Revises:
Create Date: 2024-10-14 10:22:10.281331

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect
from sqlalchemy import create_engine
import uuid

# revision identifiers, used by Alembic.
revision: str = '2878a3a212c2'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    connection = op.get_bind()
    # Get the database URL from the Alembic config
    url = connection.engine.url

    # Create a separate engine to connect to the server
    server_engine = create_engine(url.set(database=None))  # Remove the database name for server connection

    # Create the database if it does not exist
    db_name = url.database
    with server_engine.connect() as server_connection:
        result = server_connection.execute(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'")
        exists = result.fetchone() is not None

        if not exists:
            server_connection.execute(f"CREATE DATABASE \"{db_name}\"")

    # Now we can create the tables in the database
    inspector = inspect(connection)

    # Check if the 'threads' table exists
    if 'threads' not in inspector.get_table_names():
        # Create 'threads' table
        op.create_table(
            'threads',
            sa.Column('thread_id', postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column('name', sa.String(), nullable=True),
        )

    # Check if the 'messages' table exists
    if 'messages' not in inspector.get_table_names():
        # Create 'messages' table
        op.create_table(
            'messages',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('thread_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('threads.thread_id'), nullable=False),
            sa.Column('role', sa.String(255), nullable=True),
            sa.Column('message_content', sa.Text(), nullable=False),
            sa.Column('response_metadata', sa.JSON(), nullable=True),  # New column 'source' added here
            sa.Column('message_id', postgresql.UUID(as_uuid=True), nullable=False, default=sa.text('uuid_generate_v4()'))  # New column added
        )

def downgrade() -> None:
    connection = op.get_bind()
    inspector = inspect(connection)

    # Drop 'messages' table if it exists
    if 'messages' in inspector.get_table_names():
        op.drop_table('messages')

    # Drop 'threads' table if it exists
    if 'threads' in inspector.get_table_names():
        op.drop_table('threads')

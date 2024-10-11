"""initial migration

Revision ID: 9cf4697f6f45
Revises: 066f1e08d141
Create Date: 2024-10-11 10:06:45.493763

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9cf4697f6f45'
down_revision: Union[str, None] = '066f1e08d141'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

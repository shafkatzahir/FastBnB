"""add property status column

Revision ID: 6230c22a42b2
Revises: 5680a32edae3
Create Date: ...

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6230c22a42b2'
down_revision: Union[str, Sequence[str], None] = '5680a32edae3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# --- NEW: Define the ENUM type ---
propertystatus_enum = sa.Enum('AVAILABLE', 'UNAVAILABLE', name='propertystatus')


def upgrade() -> None:
    """Upgrade schema."""
    # --- Create the ENUM type first ---
    propertystatus_enum.create(op.get_bind())

    # --- Then, add the column ---
    op.add_column('properties',
        sa.Column('status',
            propertystatus_enum,
            nullable=False,
            server_default='AVAILABLE' # Good to set a default
        )
    )


def downgrade() -> None:
    """Downgrade schema."""
    # --- Drop the column first ---
    op.drop_column('properties', 'status')

    # --- Then, drop the ENUM type ---
    propertystatus_enum.drop(op.get_bind())
"""add role and full_name

Revision ID: 0ccf5df710e8
Revises: 5de5b6c36232
Create Date: 2025-09-02 01:20:38.613795
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0ccf5df710e8'
down_revision: str = '5de5b6c36232'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add columns with default values so old rows don't break
    op.add_column('users', sa.Column('full_name', sa.String(), nullable=False, server_default="Unknown"))
    op.add_column('users', sa.Column('role', sa.String(), nullable=False, server_default="Unassigned"))

    # Optional: remove defaults after migration so future rows must provide values
    op.alter_column('users', 'full_name', server_default=None)
    op.alter_column('users', 'role', server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'role')
    op.drop_column('users', 'full_name')

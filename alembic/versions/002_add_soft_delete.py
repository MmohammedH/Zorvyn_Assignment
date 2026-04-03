"""Add is_deleted flag and search index to financial_record

Revision ID: 002
Revises: 001
Create Date: 2026-04-03

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("financial_record") as batch_op:
        batch_op.add_column(
            sa.Column(
                "is_deleted",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            )
        )
        batch_op.create_index("ix_financial_record_is_deleted", ["is_deleted"])


def downgrade() -> None:
    with op.batch_alter_table("financial_record") as batch_op:
        batch_op.drop_index("ix_financial_record_is_deleted")
        batch_op.drop_column("is_deleted")

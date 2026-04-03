"""Initial migration — user and financial_record tables

Revision ID: 001
Revises:
Create Date: 2026-04-03

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_user_email"), "user", ["email"], unique=True)

    op.create_table(
        "financial_record",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("created_by_id", sa.BigInteger(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=False),
        sa.Column("record_date", sa.Date(), nullable=False),
        sa.Column("notes", sa.String(length=1000), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["created_by_id"], ["user.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_financial_record_created_by_id"),
        "financial_record",
        ["created_by_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_financial_record_type"),
        "financial_record",
        ["type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_financial_record_category"),
        "financial_record",
        ["category"],
        unique=False,
    )
    op.create_index(
        op.f("ix_financial_record_record_date"),
        "financial_record",
        ["record_date"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_financial_record_record_date"), table_name="financial_record")
    op.drop_index(op.f("ix_financial_record_category"), table_name="financial_record")
    op.drop_index(op.f("ix_financial_record_type"), table_name="financial_record")
    op.drop_index(op.f("ix_financial_record_created_by_id"), table_name="financial_record")
    op.drop_table("financial_record")
    op.drop_index(op.f("ix_user_email"), table_name="user")
    op.drop_table("user")

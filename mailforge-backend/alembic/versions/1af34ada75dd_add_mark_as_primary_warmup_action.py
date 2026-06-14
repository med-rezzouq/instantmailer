"""add mark_as_primary warmup action"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "1af34ada75dd"
down_revision: Union[str, Sequence[str], None] = "5d96aaff14cd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "warmup_tasks",
        "do_add_to_contacts",
        new_column_name="do_mark_as_primary",
        existing_type=sa.Boolean(),
        existing_nullable=False,
    )

    op.execute("ALTER TYPE warmupaction ADD VALUE IF NOT EXISTS 'mark_as_primary'")


def downgrade() -> None:
    op.execute("""
    DO $$
    BEGIN
        IF EXISTS (
            SELECT 1
            FROM pg_type t
            JOIN pg_enum e ON t.oid = e.enumtypid
            WHERE t.typname = 'warmupaction'
              AND e.enumlabel = 'mark_as_primary'
        ) THEN
            RAISE NOTICE 'Downgrade for enum value mark_as_primary requires manual enum rebuild in PostgreSQL';
        END IF;
    END $$;
    """)

    op.alter_column(
        "warmup_tasks",
        "do_mark_as_primary",
        new_column_name="do_add_to_contacts",
        existing_type=sa.Boolean(),
        existing_nullable=False,
    )
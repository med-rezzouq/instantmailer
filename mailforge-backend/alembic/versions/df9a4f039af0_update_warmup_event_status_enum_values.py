"""update warmup event status enum values"""

from typing import Sequence, Union

from alembic import op


revision: str = "df9a4f039af0"
down_revision: Union[str, Sequence[str], None] = "PUT_NEW_REVISION_ID_HERE"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE warmupeventstatus ADD VALUE IF NOT EXISTS 'started'")
    op.execute("ALTER TYPE warmupeventstatus ADD VALUE IF NOT EXISTS 'running'")
    op.execute("ALTER TYPE warmupeventstatus ADD VALUE IF NOT EXISTS 'finished'")
    op.execute("ALTER TYPE warmupeventstatus ADD VALUE IF NOT EXISTS 'finished_with_error'")


def downgrade() -> None:
    op.execute("""
    DO $$
    BEGIN
        RAISE NOTICE 'Downgrade for enum values on warmupeventstatus requires manual enum rebuild in PostgreSQL';
    END $$;
    """)
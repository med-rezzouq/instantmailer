"""add protocol to warmup tasks

Revision ID: ebf5ace0e3eb
Revises: 307f709f2d65
Create Date: 2026-06-17 14:37:52.710033
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "ebf5ace0e3eb"
down_revision: Union[str, Sequence[str], None] = "307f709f2d65"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    protocol_enum = sa.Enum("oauth", "imap", name="warmuptaskprotocol")
    protocol_enum.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "warmup_tasks",
        sa.Column(
            "protocol",
            protocol_enum,
            nullable=True,
            server_default="oauth",
        ),
    )

    op.execute("UPDATE warmup_tasks SET protocol = 'oauth' WHERE protocol IS NULL")

    op.alter_column("warmup_tasks", "protocol", nullable=False)
    op.alter_column("warmup_tasks", "protocol", server_default=None)


def downgrade() -> None:
    op.drop_column("warmup_tasks", "protocol")

    protocol_enum = sa.Enum("oauth", "imap", name="warmuptaskprotocol")
    protocol_enum.drop(op.get_bind(), checkfirst=True)
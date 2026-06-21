"""make oauth token fields nullable for imap mailboxes

Revision ID: ff1a59958170
Revises: ebf5ace0e3eb
Create Date: 2026-06-17 14:44:24.901947
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "ff1a59958170"
down_revision: Union[str, Sequence[str], None] = "ebf5ace0e3eb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "mailboxes",
        "access_token",
        existing_type=sa.Text(),
        nullable=True,
    )
    op.alter_column(
        "mailboxes",
        "refresh_token",
        existing_type=sa.Text(),
        nullable=True,
    )
    op.alter_column(
        "mailboxes",
        "token_expiry",
        existing_type=sa.DateTime(timezone=True),
        nullable=True,
    )
    op.alter_column(
        "mailboxes",
        "scope",
        existing_type=sa.Text(),
        nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "mailboxes",
        "scope",
        existing_type=sa.Text(),
        nullable=False,
    )
    op.alter_column(
        "mailboxes",
        "token_expiry",
        existing_type=sa.DateTime(timezone=True),
        nullable=False,
    )
    op.alter_column(
        "mailboxes",
        "refresh_token",
        existing_type=sa.Text(),
        nullable=False,
    )
    op.alter_column(
        "mailboxes",
        "access_token",
        existing_type=sa.Text(),
        nullable=False,
    )
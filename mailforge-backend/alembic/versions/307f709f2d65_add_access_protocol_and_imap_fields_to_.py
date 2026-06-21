"""add_access_protocol_and_imap_fields_to_mailboxes

Revision ID: 307f709f2d65
Revises: de6cdef2c0da
Create Date: 2026-06-17 12:58:05.280169

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "307f709f2d65"
down_revision: Union[str, Sequence[str], None] = "de6cdef2c0da"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "mailboxes",
        sa.Column(
            "access_protocol",
            sa.String(),
            nullable=False,
            server_default="oauth2",
        ),
    )
    op.add_column(
        "mailboxes",
        sa.Column("imap_host", sa.String(), nullable=True),
    )
    op.add_column(
        "mailboxes",
        sa.Column("imap_port", sa.Integer(), nullable=True),
    )
    op.add_column(
        "mailboxes",
        sa.Column(
            "imap_ssl",
            sa.Boolean(),
            nullable=True,
            server_default=sa.true(),
        ),
    )
    op.add_column(
        "mailboxes",
        sa.Column("smtp_host", sa.String(), nullable=True),
    )
    op.add_column(
        "mailboxes",
        sa.Column("smtp_port", sa.Integer(), nullable=True),
    )
    op.add_column(
        "mailboxes",
        sa.Column(
            "smtp_tls",
            sa.Boolean(),
            nullable=True,
            server_default=sa.true(),
        ),
    )
    op.add_column(
        "mailboxes",
        sa.Column("username", sa.String(), nullable=True),
    )
    op.add_column(
        "mailboxes",
        sa.Column("password", sa.Text(), nullable=True),
    )
    op.add_column(
        "mailboxes",
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
    )


def downgrade() -> None:
    op.drop_column("mailboxes", "is_active")
    op.drop_column("mailboxes", "password")
    op.drop_column("mailboxes", "username")
    op.drop_column("mailboxes", "smtp_tls")
    op.drop_column("mailboxes", "smtp_port")
    op.drop_column("mailboxes", "smtp_host")
    op.drop_column("mailboxes", "imap_ssl")
    op.drop_column("mailboxes", "imap_port")
    op.drop_column("mailboxes", "imap_host")
    op.drop_column("mailboxes", "access_protocol")
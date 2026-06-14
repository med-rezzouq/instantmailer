"""add oauth_app_id to mailboxes

Revision ID: 46de9c4b377b
Revises: a1b2c3d4e5f6
Create Date: 2026-06-07
"""

from alembic import op
import sqlalchemy as sa


# replace with the actual generated revision id
revision = "46de9c4b377b"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "mailboxes",
        sa.Column("oauth_app_id", sa.Integer(), nullable=True),
    )

    op.create_index(
        "ix_mailboxes_oauth_app_id",
        "mailboxes",
        ["oauth_app_id"],
        unique=False,
    )

    op.create_foreign_key(
        "fk_mailboxes_oauth_app_id_oauth_apps",
        "mailboxes",
        "oauth_apps",
        ["oauth_app_id"],
        ["id"],
    )


def downgrade():
    op.drop_constraint(
        "fk_mailboxes_oauth_app_id_oauth_apps",
        "mailboxes",
        type_="foreignkey",
    )

    op.drop_index(
        "ix_mailboxes_oauth_app_id",
        table_name="mailboxes",
    )

    op.drop_column("mailboxes", "oauth_app_id")
"""add owner_email and project_id to oauth_apps

Revision ID: 5d96aaff14cd
Revises: 900931ba8868
Create Date: 2026-06-14 13:02:37.751456
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "5d96aaff14cd"
down_revision: Union[str, Sequence[str], None] = "900931ba8868"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "oauth_apps",
        sa.Column("owner_email", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "oauth_apps",
        sa.Column("project_id", sa.String(length=255), nullable=True),
    )

    op.create_index(
        "ix_oauth_apps_owner_email",
        "oauth_apps",
        ["owner_email"],
        unique=False,
    )
    op.create_index(
        "ix_oauth_apps_project_id",
        "oauth_apps",
        ["project_id"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_oauth_apps_project_id", table_name="oauth_apps")
    op.drop_index("ix_oauth_apps_owner_email", table_name="oauth_apps")

    op.drop_column("oauth_apps", "project_id")
    op.drop_column("oauth_apps", "owner_email")
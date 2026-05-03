"""add preview text to campaigns"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "095a31514c02"
down_revision = "80defc32a0c5"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("campaigns", sa.Column("preview_text", sa.String(), nullable=True))


def downgrade():
    op.drop_column("campaigns", "preview_text")
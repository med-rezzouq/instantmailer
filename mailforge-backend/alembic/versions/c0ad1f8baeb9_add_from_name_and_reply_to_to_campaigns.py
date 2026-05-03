from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "add_from_name_reply_to_campaigns"
down_revision = "095a31514c02"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("campaigns", sa.Column("from_name", sa.String(), nullable=True))
    op.add_column("campaigns", sa.Column("reply_to", sa.String(), nullable=True))


def downgrade():
    op.drop_column("campaigns", "reply_to")
    op.drop_column("campaigns", "from_name")
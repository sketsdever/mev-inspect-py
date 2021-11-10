"""Add cToken <> underlying token table

Revision ID: 7a34fb3655a2
Revises: 205ce02374b3
Create Date: 2021-11-10 07:33:15.675638

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7a34fb3655a2'
down_revision = '205ce02374b3'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "ctoken_underlying",
        sa.Column("ctoken_address", sa.String(256), nullable=False, primary_key=True),
        sa.Column("ctoken_symbol", sa.String(256), nullable=False),
        sa.Column("underlying_token_address", sa.String(256), nullable=False)
    )

def downgrade():
    op.drop_table("ctoken_underlying")
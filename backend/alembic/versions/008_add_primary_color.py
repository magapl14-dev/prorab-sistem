"""add primary_color to app_settings

Revision ID: 008
Revises: 007
Create Date: 2026-05-29
"""
from alembic import op
import sqlalchemy as sa

revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'app_settings',
        sa.Column('primary_color', sa.String(20), nullable=True),
    )


def downgrade():
    op.drop_column('app_settings', 'primary_color')

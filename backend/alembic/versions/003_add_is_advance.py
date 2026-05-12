"""add is_advance to records

Revision ID: 003
Revises: 002
Create Date: 2026-05-12
"""
from alembic import op
import sqlalchemy as sa

revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('records', sa.Column('is_advance', sa.Boolean(), nullable=False, server_default=sa.false()))


def downgrade():
    op.drop_column('records', 'is_advance')

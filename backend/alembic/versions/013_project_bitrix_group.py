"""add bitrix_group_id to projects

Revision ID: 013
Revises: 012
Create Date: 2026-05-30
"""
from alembic import op
import sqlalchemy as sa

revision = '013'
down_revision = '012'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('projects', sa.Column('bitrix_group_id', sa.String(20), nullable=True))


def downgrade():
    op.drop_column('projects', 'bitrix_group_id')

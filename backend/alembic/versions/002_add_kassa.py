"""add kassa to records

Revision ID: 002
Revises: 001
Create Date: 2026-05-12
"""
from alembic import op
import sqlalchemy as sa

revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('records', sa.Column('kassa', sa.String(200), nullable=True))


def downgrade():
    op.drop_column('records', 'kassa')

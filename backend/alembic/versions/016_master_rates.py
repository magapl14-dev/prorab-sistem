"""master rates catalogue (штукатурка под обои, под покраску, ...)

Revision ID: 016
Revises: 015
Create Date: 2026-07-11
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '016'
down_revision = '015'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'master_rates',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('master_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('masters.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),          # "Штукатурка под обои"
        sa.Column('amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('unit', sa.String(20), nullable=True),            # '₽/м²' и т.п.
        sa.Column('display_order', sa.Integer, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_master_rates_master', 'master_rates', ['master_id'])


def downgrade():
    op.drop_index('ix_master_rates_master', table_name='master_rates')
    op.drop_table('master_rates')

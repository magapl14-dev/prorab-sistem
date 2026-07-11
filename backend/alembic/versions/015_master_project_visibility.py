"""master visibility per project + rate_unit column

Revision ID: 015
Revises: 014
Create Date: 2026-07-11
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '015'
down_revision = '014'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'master_project_visibility',
        sa.Column('master_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('masters.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('mode', sa.String(10), nullable=False),          # 'show' | 'hide'
        sa.Column('set_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('set_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint("mode IN ('show','hide')", name='ck_mpv_mode'),
    )
    op.create_index('ix_mpv_project_mode', 'master_project_visibility', ['project_id', 'mode'])

    # Единица измерения к ставке: '₽/м²', '₽/м.п.', '₽/час', '₽/смена', '₽/день', '₽/шт'…
    op.add_column('masters', sa.Column('rate_unit', sa.String(20), nullable=True))


def downgrade():
    op.drop_column('masters', 'rate_unit')
    op.drop_index('ix_mpv_project_mode', table_name='master_project_visibility')
    op.drop_table('master_project_visibility')

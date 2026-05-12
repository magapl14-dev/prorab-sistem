"""add app_settings table

Revision ID: 004
Revises: 003
Create Date: 2026-05-12
"""
from alembic import op
import sqlalchemy as sa

revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'app_settings',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('app_name', sa.String(100), nullable=False, server_default='WELL DOM'),
        sa.Column('logo_url', sa.Text(), nullable=True),
        sa.Column('favicon_url', sa.Text(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.execute("INSERT INTO app_settings (id, app_name) VALUES (1, 'WELL DOM') ON CONFLICT DO NOTHING")


def downgrade():
    op.drop_table('app_settings')

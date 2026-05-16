"""add photo_camera_only to app_settings

Revision ID: 005
Revises: 004
Create Date: 2026-05-16
"""
from alembic import op
import sqlalchemy as sa

revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'app_settings',
        sa.Column('photo_camera_only', sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade():
    op.drop_column('app_settings', 'photo_camera_only')

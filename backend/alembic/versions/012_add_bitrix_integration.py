"""bitrix24 integration fields

Revision ID: 012
Revises: 011
Create Date: 2026-05-30
"""
from alembic import op
import sqlalchemy as sa

revision = '012'
down_revision = '011'
branch_labels = None
depends_on = None


def upgrade():
    # app_settings
    op.add_column('app_settings', sa.Column('bitrix_enabled', sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column('app_settings', sa.Column('bitrix_domain', sa.String(200), nullable=True))
    op.add_column('app_settings', sa.Column('bitrix_user_id', sa.String(20), nullable=True))
    op.add_column('app_settings', sa.Column('bitrix_webhook_key', sa.String(200), nullable=True))
    op.add_column('app_settings', sa.Column('bitrix_default_responsible_id', sa.String(20), nullable=True))
    op.add_column('app_settings', sa.Column('bitrix_default_group_id', sa.String(20), nullable=True))

    # users
    op.add_column('users', sa.Column('bitrix_user_id', sa.String(20), nullable=True))

    # tasks
    op.add_column('tasks', sa.Column('bitrix_task_id', sa.String(20), nullable=True))
    op.create_index('ix_tasks_bitrix_task_id', 'tasks', ['bitrix_task_id'])


def downgrade():
    op.drop_index('ix_tasks_bitrix_task_id', table_name='tasks')
    op.drop_column('tasks', 'bitrix_task_id')
    op.drop_column('users', 'bitrix_user_id')
    op.drop_column('app_settings', 'bitrix_default_group_id')
    op.drop_column('app_settings', 'bitrix_default_responsible_id')
    op.drop_column('app_settings', 'bitrix_webhook_key')
    op.drop_column('app_settings', 'bitrix_user_id')
    op.drop_column('app_settings', 'bitrix_domain')
    op.drop_column('app_settings', 'bitrix_enabled')

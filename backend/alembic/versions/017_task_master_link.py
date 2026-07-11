"""tasks.master_id — optional master reference (call / open card from task)

Revision ID: 017
Revises: 016
Create Date: 2026-07-11
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '017'
down_revision = '016'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('tasks',
        sa.Column('master_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('masters.id', ondelete='SET NULL'), nullable=True))
    op.create_index('ix_tasks_master', 'tasks', ['master_id'])


def downgrade():
    op.drop_index('ix_tasks_master', table_name='tasks')
    op.drop_column('tasks', 'master_id')

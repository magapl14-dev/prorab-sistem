"""task comments + due_at (with time) + photo.comment_id

Revision ID: 011
Revises: 010
Create Date: 2026-05-29
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '011'
down_revision = '010'
branch_labels = None
depends_on = None


def upgrade():
    # tasks: due_date (Date) → due_at (DateTimeTZ)
    op.add_column('tasks', sa.Column('due_at', sa.DateTime(timezone=True), nullable=True))
    op.execute("UPDATE tasks SET due_at = (due_date::timestamp AT TIME ZONE 'UTC') WHERE due_date IS NOT NULL")
    op.drop_index('ix_tasks_due_date', table_name='tasks')
    op.drop_column('tasks', 'due_date')
    op.create_index('ix_tasks_due_at', 'tasks', ['due_at'])

    # task_comments
    op.create_table(
        'task_comments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('task_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False),
        sa.Column('author_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('text', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_task_comments_task', 'task_comments', ['task_id'])

    # photos.comment_id
    op.add_column('photos', sa.Column('comment_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('task_comments.id', ondelete='CASCADE'), nullable=True))
    op.create_index('ix_photos_comment_id', 'photos', ['comment_id'])


def downgrade():
    op.drop_index('ix_photos_comment_id', table_name='photos')
    op.drop_column('photos', 'comment_id')
    op.drop_index('ix_task_comments_task', table_name='task_comments')
    op.drop_table('task_comments')

    op.add_column('tasks', sa.Column('due_date', sa.Date(), nullable=True))
    op.execute("UPDATE tasks SET due_date = due_at::date WHERE due_at IS NOT NULL")
    op.drop_index('ix_tasks_due_at', table_name='tasks')
    op.drop_column('tasks', 'due_at')
    op.create_index('ix_tasks_due_date', 'tasks', ['due_date'])

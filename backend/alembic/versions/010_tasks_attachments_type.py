"""tasks: type field + photo.task_id + audio support + seed task_type dict

Revision ID: 010
Revises: 009
Create Date: 2026-05-29
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '010'
down_revision = '009'
branch_labels = None
depends_on = None


def upgrade():
    # tasks.type
    op.add_column('tasks', sa.Column('type', sa.String(100), nullable=True))

    # photos: task_id, media_type, duration_sec
    op.add_column('photos', sa.Column('task_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tasks.id', ondelete='CASCADE'), nullable=True))
    op.add_column('photos', sa.Column('media_type', sa.String(20), nullable=False, server_default='image'))
    op.add_column('photos', sa.Column('duration_sec', sa.Integer(), nullable=True))
    op.create_index('ix_photos_task_id', 'photos', ['task_id'])

    # seed task_type dictionary с примерами
    op.execute("""
        INSERT INTO dictionaries (id, kind, value, display_order, active)
        VALUES
            (gen_random_uuid(), 'task_type', 'Общая', 1, true),
            (gen_random_uuid(), 'task_type', 'Закупка', 2, true),
            (gen_random_uuid(), 'task_type', 'Работа', 3, true),
            (gen_random_uuid(), 'task_type', 'Звонок', 4, true),
            (gen_random_uuid(), 'task_type', 'Дизайн', 5, true),
            (gen_random_uuid(), 'task_type', 'Документы', 6, true)
    """)


def downgrade():
    op.execute("DELETE FROM dictionaries WHERE kind = 'task_type'")
    op.drop_index('ix_photos_task_id', table_name='photos')
    op.drop_column('photos', 'duration_sec')
    op.drop_column('photos', 'media_type')
    op.drop_column('photos', 'task_id')
    op.drop_column('tasks', 'type')

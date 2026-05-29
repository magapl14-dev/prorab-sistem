"""add tasks + task_assignees + seed tasks permissions

Revision ID: 009
Revises: 008
Create Date: 2026-05-29
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '009'
down_revision = '008'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'tasks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.id'), nullable=True),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='open'),
        sa.Column('priority', sa.String(20), nullable=True),
        sa.Column('due_date', sa.Date(), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_tasks_project_id', 'tasks', ['project_id'])
    op.create_index('ix_tasks_status', 'tasks', ['status'])
    op.create_index('ix_tasks_due_date', 'tasks', ['due_date'])

    op.create_table(
        'task_assignees',
        sa.Column('task_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tasks.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), primary_key=True),
        sa.Column('assigned_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_task_assignees_user', 'task_assignees', ['user_id'])

    # засеять права на ресурс tasks для уже существующих ролей
    ACTIONS = ["view", "create", "edit", "delete"]
    rp = sa.table(
        'role_permissions',
        sa.column('role', sa.String),
        sa.column('resource', sa.String),
        sa.column('action', sa.String),
        sa.column('allowed', sa.Boolean),
    )
    rows = []
    # admin — всё true
    for a in ACTIONS:
        rows.append({"role": "admin", "resource": "tasks", "action": a, "allowed": True})
    # foreman — всё true
    for a in ACTIONS:
        rows.append({"role": "foreman", "resource": "tasks", "action": a, "allowed": True})
    # client — только view
    for a in ACTIONS:
        rows.append({"role": "client", "resource": "tasks", "action": a, "allowed": a == "view"})
    op.bulk_insert(rp, rows)

    # для кастомных (не системных) ролей — все false, чтобы не было KeyError
    op.execute("""
        INSERT INTO role_permissions (role, resource, action, allowed)
        SELECT r.name, 'tasks', a.action, false
        FROM roles r
        CROSS JOIN (VALUES ('view'),('create'),('edit'),('delete')) AS a(action)
        WHERE r.is_system = false
        ON CONFLICT (role, resource, action) DO NOTHING
    """)


def downgrade():
    op.execute("DELETE FROM role_permissions WHERE resource = 'tasks'")
    op.drop_table('task_assignees')
    op.drop_index('ix_tasks_due_date', table_name='tasks')
    op.drop_index('ix_tasks_status', table_name='tasks')
    op.drop_index('ix_tasks_project_id', table_name='tasks')
    op.drop_table('tasks')

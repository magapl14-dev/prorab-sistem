"""add roles table with system seeds

Revision ID: 007
Revises: 006
Create Date: 2026-05-29
"""
from alembic import op
import sqlalchemy as sa

revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'roles',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(50), nullable=False, unique=True),
        sa.Column('label', sa.String(100), nullable=False),
        sa.Column('is_system', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    # widen role_permissions.role to 50 (was 20)
    op.alter_column('role_permissions', 'role', type_=sa.String(50))

    table = sa.table(
        'roles',
        sa.column('name', sa.String),
        sa.column('label', sa.String),
        sa.column('is_system', sa.Boolean),
    )
    op.bulk_insert(table, [
        {"name": "admin", "label": "Админ", "is_system": True},
        {"name": "foreman", "label": "Прораб", "is_system": True},
        {"name": "client", "label": "Клиент", "is_system": True},
    ])


def downgrade():
    op.drop_table('roles')
    op.alter_column('role_permissions', 'role', type_=sa.String(20))

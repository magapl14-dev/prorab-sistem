"""add role_permissions table with seed

Revision ID: 006
Revises: 005
Create Date: 2026-05-19
"""
from alembic import op
import sqlalchemy as sa

revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


RESOURCES = [
    "expenses",
    "master_payments",
    "client_payments",
    "dashboard",
    "reports",
    "photos",
    "users",
    "projects",
    "dictionaries",
    "branding",
    "permissions",
]
ACTIONS = ["view", "create", "edit", "delete"]

ADMIN_ONLY_RESOURCES = {"users", "projects", "dictionaries", "branding", "permissions"}

# resource: set of actions allowed for foreman
FOREMAN_DEFAULTS = {
    "expenses": {"view", "create", "edit", "delete"},
    "master_payments": {"view", "create", "edit", "delete"},
    "client_payments": {"view", "create", "edit", "delete"},
    "dashboard": {"view"},
    "reports": {"view"},
    "photos": {"view", "create", "delete"},
}

# resource: set of actions allowed for client
CLIENT_DEFAULTS = {
    "client_payments": {"view"},
    "reports": {"view"},
    "photos": {"view"},
}


def upgrade():
    op.create_table(
        'role_permissions',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('resource', sa.String(50), nullable=False),
        sa.Column('action', sa.String(20), nullable=False),
        sa.Column('allowed', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint('role', 'resource', 'action', name='uq_role_perm'),
    )

    rows = []
    for resource in RESOURCES:
        for action in ACTIONS:
            # admin — все права
            rows.append({"role": "admin", "resource": resource, "action": action, "allowed": True})
            # foreman
            foreman_allowed = (
                resource in FOREMAN_DEFAULTS and action in FOREMAN_DEFAULTS[resource]
            )
            rows.append({"role": "foreman", "resource": resource, "action": action, "allowed": foreman_allowed})
            # client
            client_allowed = (
                resource in CLIENT_DEFAULTS and action in CLIENT_DEFAULTS[resource]
            )
            rows.append({"role": "client", "resource": resource, "action": action, "allowed": client_allowed})

    table = sa.table(
        'role_permissions',
        sa.column('role', sa.String),
        sa.column('resource', sa.String),
        sa.column('action', sa.String),
        sa.column('allowed', sa.Boolean),
    )
    op.bulk_insert(table, rows)


def downgrade():
    op.drop_table('role_permissions')

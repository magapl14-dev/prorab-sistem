"""master as a proper entity

Revision ID: 014
Revises: 013
Create Date: 2026-05-30
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '014'
down_revision = '013'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'masters',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('phone', sa.String(30), nullable=True),
        sa.Column('specialty', sa.String(100), nullable=True),
        sa.Column('default_rate', sa.Numeric(12, 2), nullable=True),
        sa.Column('color', sa.String(20), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_masters_name', 'masters', ['name'])

    op.add_column('records', sa.Column('master_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('masters.id'), nullable=True))
    op.create_index('ix_records_master_id', 'records', ['master_id'])

    # Бэкфилл: создаём мастеров из существующих master_payment записей по уникальным именам
    op.execute("""
        INSERT INTO masters (id, name, active, created_at, updated_at)
        SELECT gen_random_uuid(), name, true, NOW(), NOW()
        FROM (
            SELECT DISTINCT TRIM(name) AS name
            FROM records
            WHERE kind = 'master_payment'
              AND name IS NOT NULL
              AND TRIM(name) != ''
              AND deleted_at IS NULL
        ) u
    """)

    # Связываем существующие записи с созданными мастерами
    op.execute("""
        UPDATE records r
        SET master_id = m.id
        FROM masters m
        WHERE r.kind = 'master_payment'
          AND r.name IS NOT NULL
          AND TRIM(r.name) = m.name
          AND r.master_id IS NULL
    """)


def downgrade():
    op.drop_index('ix_records_master_id', table_name='records')
    op.drop_column('records', 'master_id')
    op.drop_index('ix_masters_name', table_name='masters')
    op.drop_table('masters')

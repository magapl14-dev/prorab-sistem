"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-05-11
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS pgcrypto')

    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("phone", sa.String(20), nullable=False, unique=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("pin_hash", sa.String(100), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("email", sa.String(200), nullable=True),
        sa.Column("active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("failed_attempts", sa.Integer, nullable=False, server_default="0"),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_users_phone_active", "users", ["phone"], unique=True, postgresql_where=sa.text("deleted_at IS NULL"))

    op.create_table(
        "projects",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("code", sa.String(100), nullable=False, unique=True),
        sa.Column("name", sa.String(300), nullable=False),
        sa.Column("active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("deadline", sa.Date, nullable=True),
        sa.Column("markup_pct", sa.Numeric(5, 2), server_default="15"),
        sa.Column("foreman_rate_pct", sa.Numeric(5, 2), server_default="2.5"),
        sa.Column("foreman_efficiency", sa.Numeric(5, 2), server_default="100"),
        sa.Column("foreman_fixed", sa.Numeric(12, 2), server_default="0"),
        sa.Column("rentier_foreman_share", sa.Numeric(5, 2), server_default="100"),
        sa.Column("plan_total", sa.Numeric(14, 2), server_default="0"),
        sa.Column("plan_monthly", sa.Numeric(14, 2), server_default="0"),
        sa.Column("whatsapp_url", sa.Text, nullable=True),
        sa.Column("telegram_url", sa.Text, nullable=True),
        sa.Column("gsheet_id", sa.String(100), nullable=True),
        sa.Column("metadata", JSONB, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "user_projects",
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), primary_key=True),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("projects.id"), primary_key=True),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("granted_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("granted_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "records",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("operation_date", sa.Date, nullable=False),
        sa.Column("name", sa.String(500), nullable=True),
        sa.Column("type", sa.String(100), nullable=True),
        sa.Column("category", sa.String(200), nullable=True),
        sa.Column("comment", sa.Text, nullable=True),
        sa.Column("qty", sa.Numeric(10, 3), server_default="1"),
        sa.Column("price", sa.Numeric(12, 2), nullable=True),
        sa.Column("sum_buy", sa.Numeric(14, 2), nullable=True),
        sa.Column("markup_pct_snapshot", sa.Numeric(5, 2), nullable=True),
        sa.Column("sum_sell", sa.Numeric(14, 2), nullable=True),
        sa.Column("commission", sa.Numeric(12, 2), server_default="0"),
        sa.Column("rentier_gross", sa.Numeric(12, 2), server_default="0"),
        sa.Column("rentier_share_snapshot", sa.Numeric(5, 2), nullable=True),
        sa.Column("client_rep_name", sa.String(200), nullable=True),
        sa.Column("payment_amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("payment_date", sa.Date, nullable=True),
        sa.Column("author_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("metadata", JSONB, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_records_project_date", "records", ["project_id", sa.text("operation_date DESC")])
    op.create_index("idx_records_author", "records", ["author_id"], postgresql_where=sa.text("deleted_at IS NULL"))
    op.create_index("idx_records_kind", "records", ["project_id", "kind"])

    op.create_table(
        "photos",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("record_id", UUID(as_uuid=True), sa.ForeignKey("records.id", ondelete="CASCADE"), nullable=True),
        sa.Column("s3_bucket", sa.String(200), nullable=False),
        sa.Column("s3_key", sa.String(500), nullable=False),
        sa.Column("thumb_key", sa.String(500), nullable=True),
        sa.Column("mime_type", sa.String(100), nullable=False),
        sa.Column("size_bytes", sa.Integer, nullable=False),
        sa.Column("width", sa.Integer, nullable=True),
        sa.Column("height", sa.Integer, nullable=True),
        sa.Column("kind", sa.String(20), nullable=False, server_default=sa.text("'receipt'")),
        sa.Column("is_confirmed", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("uploaded_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "audit_log",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("project_id", UUID(as_uuid=True), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("entity_type", sa.String(100), nullable=True),
        sa.Column("entity_id", UUID(as_uuid=True), nullable=True),
        sa.Column("old_value", JSONB, nullable=True),
        sa.Column("new_value", JSONB, nullable=True),
        sa.Column("ip", sa.String(50), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "dictionaries",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("kind", sa.String(30), nullable=False),
        sa.Column("value", sa.String(200), nullable=False),
        sa.Column("display_order", sa.Integer, server_default="0"),
        sa.Column("active", sa.Boolean, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("created_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.UniqueConstraint("kind", "value", name="uq_dictionary_kind_value"),
    )

    # Seed default dictionaries
    op.execute("""
        INSERT INTO dictionaries (kind, value, display_order) VALUES
        ('type', 'Материалы', 1),
        ('type', 'Работы', 2),
        ('type', 'Доставка', 3),
        ('type', 'Уборка', 4),
        ('type', 'Прочее', 5),
        ('category', 'Демонтаж', 1),
        ('category', 'Черновые работы', 2),
        ('category', 'Стяжка пола', 3),
        ('category', 'Электрика', 4),
        ('category', 'Сантехника', 5),
        ('category', 'Отделка стен', 6),
        ('category', 'Потолок', 7),
        ('category', 'Полы', 8),
        ('category', 'Двери/окна', 9),
        ('category', 'Финишная отделка', 10),
        ('category', 'Прочее', 11),
        ('master_payment_type', 'Аванс', 1),
        ('master_payment_type', 'Оплата за работу', 2),
        ('master_payment_type', 'Окончательный расчёт', 3)
    """)


def downgrade():
    op.drop_table("dictionaries")
    op.drop_table("audit_log")
    op.drop_table("photos")
    op.drop_table("records")
    op.drop_table("user_projects")
    op.drop_table("projects")
    op.drop_table("users")

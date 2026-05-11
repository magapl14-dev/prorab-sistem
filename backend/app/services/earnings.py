from decimal import Decimal
from datetime import date
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from ..models.models import Record, Project


async def calc_project_earnings(db: AsyncSession, project: Project, user_id: UUID) -> dict:
    result = await db.execute(
        select(
            func.coalesce(func.sum(Record.sum_buy), 0).label("total_buy"),
            func.coalesce(func.sum(Record.commission), 0).label("total_commission"),
            func.coalesce(func.sum(Record.rentier_gross), 0).label("total_rentier"),
        ).where(
            and_(
                Record.project_id == project.id,
                Record.kind == "expense",
                Record.author_id == user_id,
                Record.deleted_at.is_(None),
            )
        )
    )
    row = result.one()
    total_commission = Decimal(str(row.total_commission))
    total_rentier = Decimal(str(row.total_rentier))
    rentier_foreman = total_rentier * (project.rentier_foreman_share / 100)

    return {
        "project_code": project.code,
        "project_name": project.name,
        "total_expenses": Decimal(str(row.total_buy)),
        "commission": total_commission,
        "rentier_gross": total_rentier,
        "rentier_foreman": rentier_foreman,
        "fixed_monthly": Decimal(str(project.foreman_fixed)),
        "total": total_commission + rentier_foreman + Decimal(str(project.foreman_fixed)),
    }


async def calc_plan(db: AsyncSession, project: Project) -> dict:
    from datetime import datetime, timezone
    today = datetime.now(timezone.utc).date()

    total_result = await db.execute(
        select(func.coalesce(func.sum(Record.sum_buy), 0)).where(
            and_(
                Record.project_id == project.id,
                Record.kind == "expense",
                Record.deleted_at.is_(None),
            )
        )
    )
    spent_total = Decimal(str(total_result.scalar()))

    monthly_result = await db.execute(
        select(func.coalesce(func.sum(Record.sum_buy), 0)).where(
            and_(
                Record.project_id == project.id,
                Record.kind == "expense",
                Record.deleted_at.is_(None),
                func.date_trunc("month", Record.operation_date) == func.date_trunc("month", today),
            )
        )
    )
    spent_monthly = Decimal(str(monthly_result.scalar()))

    plan_total = Decimal(str(project.plan_total)) or Decimal("1")
    plan_monthly = Decimal(str(project.plan_monthly)) or Decimal("1")

    return {
        "project_code": project.code,
        "project_name": project.name,
        "plan_total": Decimal(str(project.plan_total)),
        "plan_monthly": Decimal(str(project.plan_monthly)),
        "spent_total": spent_total,
        "spent_monthly": spent_monthly,
        "progress_total_pct": min(spent_total / plan_total * 100, Decimal("999")),
        "progress_monthly_pct": min(spent_monthly / plan_monthly * 100, Decimal("999")),
    }


def calc_record_financials(record_dict: dict, project: Project) -> dict:
    if record_dict.get("kind") != "expense":
        return record_dict
    price = record_dict.get("price")
    if price is None:
        return record_dict
    qty = Decimal(str(record_dict.get("qty", 1)))
    price = Decimal(str(price))
    sum_buy = qty * price
    markup = Decimal(str(project.markup_pct)) / 100
    sum_sell = sum_buy * (1 + markup)
    rate = Decimal(str(project.foreman_rate_pct)) / 100
    efficiency = Decimal(str(project.foreman_efficiency)) / 100
    commission = sum_buy * rate * efficiency
    rentier_gross = sum_sell - sum_buy - commission
    return {
        **record_dict,
        "sum_buy": sum_buy,
        "markup_pct_snapshot": project.markup_pct,
        "sum_sell": sum_sell,
        "commission": commission,
        "rentier_gross": rentier_gross,
        "rentier_share_snapshot": project.rentier_foreman_share,
    }

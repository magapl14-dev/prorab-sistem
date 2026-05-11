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


async def calc_period_stats(db: AsyncSession, project: Project, user_id: UUID) -> dict:
    import calendar
    from datetime import timedelta
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)

    days_in_month = calendar.monthrange(today.year, today.month)[1]
    working_days = sum(1 for d in range(1, days_in_month + 1)
                       if date(today.year, today.month, d).weekday() < 5)
    daily_fixed = float(project.foreman_fixed) / working_days if working_days and project.foreman_fixed else 0

    def wd_count(start, end):
        return sum(1 for i in range((end - start).days + 1)
                   if (start + timedelta(days=i)).weekday() < 5)

    days_today = 1 if today.weekday() < 5 else 0
    days_week = wd_count(week_start, today)
    days_month = wd_count(month_start, today)

    rentier_share = float(project.rentier_foreman_share) / 100

    async def sum_period(start, end):
        r = await db.execute(
            select(
                func.coalesce(func.sum(Record.commission), 0).label("c"),
                func.coalesce(func.sum(Record.rentier_gross), 0).label("r"),
                func.coalesce(func.sum(Record.sum_buy), 0).label("b"),
                func.count(Record.id).label("n"),
            ).where(and_(
                Record.project_id == project.id,
                Record.kind == "expense",
                Record.author_id == user_id,
                Record.deleted_at.is_(None),
                Record.operation_date >= start,
                Record.operation_date <= end,
            ))
        )
        row = r.one()
        return float(row.c), float(row.r) * rentier_share, float(row.b), int(row.n)

    c_t, r_t, b_t, n_t = await sum_period(today, today)
    c_w, r_w, b_w, n_w = await sum_period(week_start, today)
    c_m, r_m, b_m, n_m = await sum_period(month_start, today)

    return {
        "today":  {"fixed": round(daily_fixed * days_today, 2),  "commission": c_t, "rentier": r_t, "buy": b_t, "count": n_t},
        "week":   {"fixed": round(daily_fixed * days_week, 2),   "commission": c_w, "rentier": r_w, "buy": b_w, "count": n_w},
        "month":  {"fixed": round(daily_fixed * days_month, 2),  "commission": c_m, "rentier": r_m, "buy": b_m, "count": n_m},
        "rate_pct": float(project.foreman_rate_pct),
        "efficiency_pct": float(project.foreman_efficiency),
        "fixed_monthly": float(project.foreman_fixed),
        "rentier_share_pct": float(project.rentier_foreman_share),
        "working_days_month": working_days,
        "daily_fixed": daily_fixed,
    }


async def calc_monthly_breakdown(db: AsyncSession, project: Project, user_id: UUID) -> list:
    rentier_share = float(project.rentier_foreman_share) / 100
    r = await db.execute(
        select(
            func.date_trunc("month", Record.operation_date).label("month"),
            func.coalesce(func.sum(Record.sum_buy), 0).label("buy"),
            func.coalesce(func.sum(Record.commission), 0).label("commission"),
            func.coalesce(func.sum(Record.rentier_gross), 0).label("rentier"),
            func.count(Record.id).label("cnt"),
        ).where(and_(
            Record.project_id == project.id,
            Record.kind == "expense",
            Record.author_id == user_id,
            Record.deleted_at.is_(None),
        )).group_by(func.date_trunc("month", Record.operation_date))
        .order_by(func.date_trunc("month", Record.operation_date).desc())
    )
    result = []
    for row in r.all():
        commission = float(row.commission)
        rentier = float(row.rentier) * rentier_share
        fixed = float(project.foreman_fixed)
        result.append({
            "month": row.month.strftime("%Y-%m"),
            "buy": float(row.buy),
            "commission": commission,
            "rentier": rentier,
            "fixed": fixed,
            "total": fixed + commission + rentier,
            "count": int(row.cnt),
        })
    return result


async def calc_chart14(db: AsyncSession, project: Project, user_id: UUID) -> list:
    from datetime import timedelta
    today = date.today()
    start = today - timedelta(days=13)
    rentier_share = float(project.rentier_foreman_share) / 100

    r = await db.execute(
        select(
            Record.operation_date.label("day"),
            func.coalesce(func.sum(Record.commission), 0).label("c"),
            func.coalesce(func.sum(Record.rentier_gross), 0).label("rv"),
        ).where(and_(
            Record.project_id == project.id,
            Record.kind == "expense",
            Record.author_id == user_id,
            Record.deleted_at.is_(None),
            Record.operation_date >= start,
            Record.operation_date <= today,
        )).group_by(Record.operation_date).order_by(Record.operation_date)
    )
    data = {str(row.day): float(row.c) + float(row.rv) * rentier_share for row in r.all()}
    return [{"date": str(start + timedelta(days=i)),
             "amount": data.get(str(start + timedelta(days=i)), 0)} for i in range(14)]


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

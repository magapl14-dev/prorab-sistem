from decimal import Decimal
from pydantic import BaseModel


class EarningsOut(BaseModel):
    project_code: str
    project_name: str
    total_expenses: Decimal
    commission: Decimal
    rentier_gross: Decimal
    rentier_foreman: Decimal
    fixed_monthly: Decimal
    total: Decimal


class PlanOut(BaseModel):
    project_code: str
    project_name: str
    plan_total: Decimal
    plan_monthly: Decimal
    spent_total: Decimal
    spent_monthly: Decimal
    progress_total_pct: Decimal
    progress_monthly_pct: Decimal

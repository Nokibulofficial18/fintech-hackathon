from datetime import date
from decimal import Decimal
from typing import Dict, List
from pydantic import BaseModel, Field
from app.schemas.common import SupportedCurrency


class CurrencyBalanceSummary(BaseModel):
    """Summary of actual balances per currency."""
    currency: SupportedCurrency
    actual_liquid_amount: Decimal
    accounts_count: int


class FinanceOverviewResponse(BaseModel):
    """Executive financial dashboard snapshot for the student."""
    student_id: str
    student_name: str
    home_currency: SupportedCurrency
    study_currency: SupportedCurrency
    as_of_date: date

    # Balances strictly by currency (NEVER combined without rate)
    balances_by_currency: Dict[str, Decimal]

    # Academic Tuition status
    tuition_amount_due: Decimal
    tuition_due_date: date
    days_until_tuition_due: int

    # Upcoming obligations
    obligations_next_30_days_study_currency: Decimal
    obligations_next_90_days_study_currency: Decimal

    # Estimated monthly burn
    monthly_living_burn_study_currency: Decimal

    # Estimated runway in study currency without converting foreign funds
    study_currency_standalone_runway_months: Decimal

    # Key diagnostic alert flags
    has_imminent_shortfall: bool
    has_funding_gap: bool
    summary_alert: str

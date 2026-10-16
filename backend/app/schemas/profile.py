from datetime import date
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field
from app.schemas.common import SupportedCurrency


class AccountBalance(BaseModel):
    """Current liquid balance held in a specific currency."""
    account_name: str = Field(..., description="Account identifier (e.g. US Student Checking)")
    currency: SupportedCurrency = Field(..., description="Currency of this account")
    actual_balance: Decimal = Field(..., ge=0, description="Verified actual liquid balance")
    as_of_date: date = Field(..., description="Verification date of this balance")
    is_projected: bool = Field(default=False, description="Always False for verified actual balances")


class ExpectedIncome(BaseModel):
    """Expected funding or income event with schedule."""
    source_name: str = Field(..., description="Funding source (e.g. Graduate TA Stipend, Merit Scholarship)")
    amount: Decimal = Field(..., gt=0, description="Gross received amount")
    currency: SupportedCurrency = Field(..., description="Currency of the payout")
    expected_date: date = Field(..., description="Scheduled disbursement date")
    is_recurring: bool = Field(default=False, description="Whether this repeats periodically")
    recurrence_interval_days: Optional[int] = Field(default=None, description="Days between recurrence (e.g. 30)")
    notes: Optional[str] = Field(default=None)


class LivingExpenseItem(BaseModel):
    """Categorized recurring monthly living expense."""
    category: str = Field(..., description="Category (Rent, Groceries, Insurance, Utilities, Transit)")
    monthly_amount: Decimal = Field(..., ge=0, description="Estimated monthly expense")
    currency: SupportedCurrency = Field(..., description="Currency incurred (usually study currency)")
    due_day_of_month: int = Field(default=1, ge=1, le=31, description="Day of month when payment is due")
    is_fixed: bool = Field(default=True, description="Fixed contractual cost vs discretionary")


class TuitionObligation(BaseModel):
    """Academic tuition or institutional fee obligation."""
    term: str = Field(..., description="Academic term (e.g. Fall 2026)")
    amount_due: Decimal = Field(..., gt=0, description="Amount payable to institution")
    currency: SupportedCurrency = Field(..., description="Currency payable in (usually study currency)")
    due_date: date = Field(..., description="Official deadline for payment")
    grace_period_days: int = Field(default=0, ge=0, description="Grace period before late fee penalty")
    late_penalty_fee: Decimal = Field(default=Decimal("150.00"), ge=0, description="Penalty if payment is missed")


class PlannedRemittance(BaseModel):
    """Scheduled cross-border transfer between student's own accounts."""
    plan_name: str = Field(..., description="Description (e.g. Fall Semester Support Remittance)")
    planned_date: date = Field(..., description="Date scheduled to initiate transfer")
    send_amount: Decimal = Field(..., gt=0, description="Amount to send in home currency")
    send_currency: SupportedCurrency = Field(..., description="Origin currency")
    target_currency: SupportedCurrency = Field(..., description="Destination currency")
    estimated_received_amount: Optional[Decimal] = Field(
        default=None,
        description="Estimated received amount after fees and FX conversion",
    )
    notes: Optional[str] = None


class StudentProfileData(BaseModel):
    """Core demographic and university metadata."""
    student_id: str = Field(default="demo-student-china-tanvir")
    full_name: str = Field(default="Tanvir Hasan")
    home_country: str = Field(default="Bangladesh")
    study_country: str = Field(default="China")
    home_currency: SupportedCurrency = Field(default=SupportedCurrency.BDT)
    study_currency: SupportedCurrency = Field(default=SupportedCurrency.CNY)
    university_name: str = Field(default="Tsinghua University")
    program_name: str = Field(default="M.Sc. in Computer Science and Technology")
    intake_term: str = Field(default="Fall 2026")


class FullStudentScenario(BaseModel):
    """Complete, integrated financial state for a student."""
    profile: StudentProfileData
    available_balances: List[AccountBalance]
    expected_income: List[ExpectedIncome]
    monthly_living_expenses: List[LivingExpenseItem]
    tuition_obligations: List[TuitionObligation]
    planned_remittances: List[PlannedRemittance]
    is_synthetic_demo: bool = Field(
        default=True,
        description="Always clearly labeled as synthetic for competition prototype demonstration",
    )

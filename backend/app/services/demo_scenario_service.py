from datetime import date
from decimal import Decimal
from typing import Optional
from app.schemas.common import SupportedCurrency
from app.schemas.profile import (
    StudentProfileData,
    AccountBalance,
    ExpectedIncome,
    LivingExpenseItem,
    TuitionObligation,
    PlannedRemittance,
    FullStudentScenario,
)


def get_china_student_demo_scenario() -> FullStudentScenario:
    """
    Signature BorderWise AI Competition Demo Scenario.
    Student: Tanvir Hasan studying at Tsinghua University (Beijing, China).
    Study Currency: CNY (RMB), Home Currency: BDT.
    Tuition, rent, and daily living expenses are denominated in CNY,
    while family funds originate in BDT in Bangladesh.
    Baseline as-of date: 2026-10-15.
    """
    profile = StudentProfileData(
        student_id="demo-student-china-tanvir",
        full_name="Tanvir Hasan",
        home_country="Bangladesh",
        study_country="China",
        home_currency=SupportedCurrency.BDT,
        study_currency=SupportedCurrency.CNY,
        university_name="Tsinghua University",
        program_name="M.Sc. in Computer Science and Technology",
        intake_term="Fall 2026",
    )

    balances = [
        AccountBalance(
            account_name="China Student Living Account (ICBC Beijing)",
            currency=SupportedCurrency.CNY,
            actual_balance=Decimal("8500.00"),
            as_of_date=date(2026, 10, 15),
            is_projected=False,
        ),
        AccountBalance(
            account_name="Home Student Savings (DBBL Dhaka)",
            currency=SupportedCurrency.BDT,
            actual_balance=Decimal("350000.00"),
            as_of_date=date(2026, 10, 15),
            is_projected=False,
        ),
    ]

    income = [
        ExpectedIncome(
            source_name="CSC University Research Stipend",
            amount=Decimal("3500.00"),
            currency=SupportedCurrency.CNY,
            expected_date=date(2026, 11, 1),
            is_recurring=False,
            notes="Institutional academic stipend credited to ICBC account",
        ),
        ExpectedIncome(
            source_name="Family Education Support Deposit",
            amount=Decimal("150000.00"),
            currency=SupportedCurrency.BDT,
            expected_date=date(2026, 11, 10),
            is_recurring=False,
            notes="Scheduled parental deposit into Dhaka DBBL home savings account",
        ),
    ]

    expenses = [
        LivingExpenseItem(
            category="Student Accommodation Rent (Haidian / Wudaokou)",
            monthly_amount=Decimal("1800.00"),
            currency=SupportedCurrency.CNY,
            due_day_of_month=1,
            is_fixed=True,
        ),
        LivingExpenseItem(
            category="Campus Canteen & Dining",
            monthly_amount=Decimal("1200.00"),
            currency=SupportedCurrency.CNY,
            due_day_of_month=5,
            is_fixed=False,
        ),
        LivingExpenseItem(
            category="Beijing Subway & City Transit",
            monthly_amount=Decimal("150.00"),
            currency=SupportedCurrency.CNY,
            due_day_of_month=10,
            is_fixed=True,
        ),
        LivingExpenseItem(
            category="Mobile Data & Campus Wi-Fi (China Mobile)",
            monthly_amount=Decimal("150.00"),
            currency=SupportedCurrency.CNY,
            due_day_of_month=15,
            is_fixed=True,
        ),
    ]

    tuition = [
        TuitionObligation(
            term="Fall 2026 / Semester 1",
            amount_due=Decimal("24000.00"),
            currency=SupportedCurrency.CNY,
            due_date=date(2026, 11, 15),
            grace_period_days=3,
            late_penalty_fee=Decimal("300.00"),
        )
    ]

    remittances = [
        PlannedRemittance(
            plan_name="Pre-Tuition Family Remittance from Bangladesh",
            planned_date=date(2026, 10, 28),
            send_amount=Decimal("250000.00"),
            send_currency=SupportedCurrency.BDT,
            target_currency=SupportedCurrency.CNY,
            estimated_received_amount=Decimal("14640.00"),
            notes="Family scheduled cross-border remittance from DBBL Dhaka to ICBC Beijing",
        )
    ]

    return FullStudentScenario(
        profile=profile,
        available_balances=balances,
        expected_income=income,
        monthly_living_expenses=expenses,
        tuition_obligations=tuition,
        planned_remittances=remittances,
        is_synthetic_demo=True,
    )


def get_uk_student_demo_scenario() -> FullStudentScenario:
    """
    Signature BorderWise AI Competition Demo Scenario.
    Student: Priya Patel studying at Imperial College London (United Kingdom).
    Study Currency: GBP, Home Currency: INR.
    Tuition, rent, and daily living expenses are denominated in GBP,
    while family funds and planned remittances originate in INR.
    Baseline as-of date: 2026-10-15.
    """
    profile = StudentProfileData(
        student_id="demo-student-uk-priya",
        full_name="Priya Patel",
        home_country="India",
        study_country="United Kingdom",
        home_currency=SupportedCurrency.INR,
        study_currency=SupportedCurrency.GBP,
        university_name="Imperial College London",
        program_name="M.Sc. in Advanced Computing",
        intake_term="Fall 2026 / Michaelmas",
    )

    balances = [
        AccountBalance(
            account_name="UK Student Current Account (Barclays)",
            currency=SupportedCurrency.GBP,
            actual_balance=Decimal("2400.00"),
            as_of_date=date(2026, 10, 15),
            is_projected=False,
        ),
        AccountBalance(
            account_name="Home Student Savings (SBI / HDFC)",
            currency=SupportedCurrency.INR,
            actual_balance=Decimal("950000.00"),
            as_of_date=date(2026, 10, 15),
            is_projected=False,
        ),
    ]

    income = [
        ExpectedIncome(
            source_name="UK Department Research Bursary",
            amount=Decimal("850.00"),
            currency=SupportedCurrency.GBP,
            expected_date=date(2026, 11, 1),
            is_recurring=False,
            notes="Institutional departmental bursary credited to Barclays UK account",
        ),
        ExpectedIncome(
            source_name="Family Education Support Deposit",
            amount=Decimal("300000.00"),
            currency=SupportedCurrency.INR,
            expected_date=date(2026, 11, 10),
            is_recurring=False,
            notes="Scheduled parental deposit into Indian home savings account",
        ),
    ]

    expenses = [
        LivingExpenseItem(
            category="Student Accommodation Rent (Kensington)",
            monthly_amount=Decimal("1200.00"),
            currency=SupportedCurrency.GBP,
            due_day_of_month=1,
            is_fixed=True,
        ),
        LivingExpenseItem(
            category="Groceries & Dining",
            monthly_amount=Decimal("350.00"),
            currency=SupportedCurrency.GBP,
            due_day_of_month=5,
            is_fixed=False,
        ),
        LivingExpenseItem(
            category="Transport (TfL Student Oyster)",
            monthly_amount=Decimal("140.00"),
            currency=SupportedCurrency.GBP,
            due_day_of_month=10,
            is_fixed=True,
        ),
        LivingExpenseItem(
            category="Utilities & High-Speed Mobile/Broadband",
            monthly_amount=Decimal("110.00"),
            currency=SupportedCurrency.GBP,
            due_day_of_month=15,
            is_fixed=True,
        ),
    ]

    tuition = [
        TuitionObligation(
            term="Term 1 / Michaelmas 2026",
            amount_due=Decimal("9250.00"),
            currency=SupportedCurrency.GBP,
            due_date=date(2026, 11, 15),
            grace_period_days=3,
            late_penalty_fee=Decimal("100.00"),
        )
    ]

    remittances = [
        PlannedRemittance(
            plan_name="Planned Pre-Tuition Family Remittance",
            planned_date=date(2026, 10, 25),
            send_amount=Decimal("700000.00"),
            send_currency=SupportedCurrency.INR,
            target_currency=SupportedCurrency.GBP,
            estimated_received_amount=Decimal("6546.39"),
            notes="Family scheduled cross-border remittance from SBI savings to Barclays UK account",
        )
    ]

    return FullStudentScenario(
        profile=profile,
        available_balances=balances,
        expected_income=income,
        monthly_living_expenses=expenses,
        tuition_obligations=tuition,
        planned_remittances=remittances,
        is_synthetic_demo=True,
    )


def get_us_student_demo_scenario() -> FullStudentScenario:
    """
    US Student Synthetic Scenario.
    Student: Aarav Sharma studying at Northeastern University (United States).
    Study Currency: USD, Home Currency: INR.
    Baseline as-of date: 2026-10-15.
    """
    profile = StudentProfileData(
        student_id="demo-student-aarav",
        full_name="Aarav Sharma",
        home_country="India",
        study_country="United States",
        home_currency=SupportedCurrency.INR,
        study_currency=SupportedCurrency.USD,
        university_name="Northeastern University",
        program_name="M.S. in Computer Science",
        intake_term="Fall 2026",
    )

    balances = [
        AccountBalance(
            account_name="US Student Checking (Chase)",
            currency=SupportedCurrency.USD,
            actual_balance=Decimal("4200.00"),
            as_of_date=date(2026, 10, 15),
            is_projected=False,
        ),
        AccountBalance(
            account_name="India Student Savings (HDFC)",
            currency=SupportedCurrency.INR,
            actual_balance=Decimal("650000.00"),
            as_of_date=date(2026, 10, 15),
            is_projected=False,
        ),
    ]

    income = [
        ExpectedIncome(
            source_name="Graduate Merit Scholarship",
            amount=Decimal("3000.00"),
            currency=SupportedCurrency.USD,
            expected_date=date(2026, 11, 1),
            is_recurring=False,
            notes="Direct institutional award credited to US student account",
        ),
        ExpectedIncome(
            source_name="Graduate Teaching Assistantship (TA)",
            amount=Decimal("1200.00"),
            currency=SupportedCurrency.USD,
            expected_date=date(2026, 10, 15),
            is_recurring=True,
            recurrence_interval_days=30,
            notes="Monthly bi-weekly payroll deposit (approximated monthly)",
        ),
        ExpectedIncome(
            source_name="Family Education Support Remittance",
            amount=Decimal("200000.00"),
            currency=SupportedCurrency.INR,
            expected_date=date(2026, 11, 20),
            is_recurring=False,
            notes="Deposit from family into Indian home account",
        ),
    ]

    expenses = [
        LivingExpenseItem(
            category="Rent & Housing",
            monthly_amount=Decimal("1400.00"),
            currency=SupportedCurrency.USD,
            due_day_of_month=1,
            is_fixed=True,
        ),
        LivingExpenseItem(
            category="Groceries & Dining",
            monthly_amount=Decimal("450.00"),
            currency=SupportedCurrency.USD,
            due_day_of_month=5,
            is_fixed=False,
        ),
        LivingExpenseItem(
            category="Student Health Insurance Plan",
            monthly_amount=Decimal("180.00"),
            currency=SupportedCurrency.USD,
            due_day_of_month=10,
            is_fixed=True,
        ),
        LivingExpenseItem(
            category="Utilities & High-Speed Internet",
            monthly_amount=Decimal("120.00"),
            currency=SupportedCurrency.USD,
            due_day_of_month=15,
            is_fixed=True,
        ),
        LivingExpenseItem(
            category="MBTA Transit Pass & Books",
            monthly_amount=Decimal("250.00"),
            currency=SupportedCurrency.USD,
            due_day_of_month=20,
            is_fixed=False,
        ),
    ]

    tuition = [
        TuitionObligation(
            term="Fall 2026",
            amount_due=Decimal("14500.00"),
            currency=SupportedCurrency.USD,
            due_date=date(2026, 11, 15),
            grace_period_days=3,
            late_penalty_fee=Decimal("150.00"),
        )
    ]

    remittances = [
        PlannedRemittance(
            plan_name="Pre-Tuition Cross-Border Remittance",
            planned_date=date(2026, 10, 25),
            send_amount=Decimal("500000.00"),
            send_currency=SupportedCurrency.INR,
            target_currency=SupportedCurrency.USD,
            estimated_received_amount=Decimal("5950.00"),
            notes="Initiated 3 weeks ahead of tuition payment deadline",
        )
    ]

    return FullStudentScenario(
        profile=profile,
        available_balances=balances,
        expected_income=income,
        monthly_living_expenses=expenses,
        tuition_obligations=tuition,
        planned_remittances=remittances,
        is_synthetic_demo=True,
    )


# Active in-memory scenario state (defaults to signature China-Bangladesh student demo)
_active_scenario: FullStudentScenario = get_china_student_demo_scenario()


def get_active_scenario() -> FullStudentScenario:
    """Retrieve the currently active student scenario."""
    global _active_scenario
    return _active_scenario


def reset_active_scenario(scenario_key: str = "china") -> FullStudentScenario:
    """
    Reset the active scenario to a pristine synthetic baseline.
    Supported keys: 'china'/'bd' (Tanvir Hasan, CNY/BDT), 'uk' (Priya Patel, GBP/INR), 'us' (Aarav Sharma, USD/INR).
    Default is 'china'.
    """
    global _active_scenario
    key = scenario_key.lower()
    if key == "us":
        _active_scenario = get_us_student_demo_scenario()
    elif key == "uk":
        _active_scenario = get_uk_student_demo_scenario()
    else:
        _active_scenario = get_china_student_demo_scenario()
    return _active_scenario


def get_seeded_demo_scenario(scenario_key: Optional[str] = None) -> FullStudentScenario:
    """
    Retrieve demo scenario. If scenario_key is provided, loads that specific scenario.
    Otherwise returns the currently active scenario.
    """
    if scenario_key is not None:
        key = scenario_key.lower()
        if key == "us":
            return get_us_student_demo_scenario()
        elif key == "uk":
            return get_uk_student_demo_scenario()
        return get_china_student_demo_scenario()
    return get_active_scenario()

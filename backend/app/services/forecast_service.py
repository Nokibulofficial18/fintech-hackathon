from datetime import date, timedelta
from decimal import Decimal
from typing import Dict, List, Tuple
from app.schemas.common import SupportedCurrency
from app.schemas.profile import FullStudentScenario
from app.schemas.forecast import (
    TimelineEvent,
    DailyCurrencyBalance,
    ShortfallEvent,
    DataCompletenessReport,
    CashFlowForecastResponse,
)
from app.services.fx_service import get_dated_fx_quote, round_money_standard


def evaluate_data_completeness(scenario: FullStudentScenario) -> DataCompletenessReport:
    """Audit data completeness and note missing elements."""
    missing: List[str] = []
    
    has_balances = len(scenario.available_balances) > 0
    if not has_balances:
        missing.append("Verified account liquid balances")

    has_income = len(scenario.expected_income) > 0
    if not has_income:
        missing.append("Expected income or stipend streams")

    has_expenses = len(scenario.monthly_living_expenses) > 0
    if not has_expenses:
        missing.append("Itemized living expense budget")

    has_tuition = len(scenario.tuition_obligations) > 0
    if not has_tuition:
        missing.append("Upcoming academic tuition obligations")

    has_remittances = len(scenario.planned_remittances) > 0

    # Calculate score based on fundamental components
    total_checks = 4
    passed_checks = sum([has_balances, has_income, has_expenses, has_tuition])
    score = round(passed_checks / total_checks, 2)

    notes = (
        "Complete data model supplied."
        if score == 1.0
        else f"Data set is partial ({score * 100:.0f}% complete). Missing: {', '.join(missing)}."
    )

    return DataCompletenessReport(
        completeness_score=score,
        has_verified_actual_balances=has_balances,
        has_scheduled_income=has_income,
        has_itemized_living_expenses=has_expenses,
        has_tuition_deadline=has_tuition,
        has_planned_remittances=has_remittances,
        missing_elements=missing,
        notes=notes,
    )


def generate_cash_flow_forecast(
    scenario: FullStudentScenario,
    start_date: date | None = None,
    horizon_days: int = 90,
    safety_reserve_by_currency: Dict[str, Decimal] | None = None,
) -> CashFlowForecastResponse:
    """
    Simulate a 90-day multi-currency cash flow timeline.
    Separates verified actual starting balances from projected figures, tracks obligations,
    and identifies deficit shortfalls.
    """
    base_date = start_date or date(2026, 10, 15)
    end_date = base_date + timedelta(days=horizon_days)

    if safety_reserve_by_currency is None:
        safety_reserve_by_currency = {
            SupportedCurrency.USD.value: Decimal("500.00"),
            SupportedCurrency.CNY.value: Decimal("3000.00"),
            SupportedCurrency.BDT.value: Decimal("50000.00"),
            SupportedCurrency.INR.value: Decimal("25000.00"),
            SupportedCurrency.GBP.value: Decimal("400.00"),
            SupportedCurrency.CAD.value: Decimal("650.00"),
            SupportedCurrency.EUR.value: Decimal("450.00"),
        }

    # 1. Initialize actual verified balances (Actual vs Projected distinction)
    actual_balances: Dict[str, Decimal] = {}
    for bal in scenario.available_balances:
        curr_key = bal.currency.value
        actual_balances[curr_key] = actual_balances.get(curr_key, Decimal("0.00")) + bal.actual_balance

    # Ensure keys for both home and study currencies exist
    for c in [scenario.profile.home_currency.value, scenario.profile.study_currency.value]:
        if c not in actual_balances:
            actual_balances[c] = Decimal("0.00")

    running_balances = {k: v for k, v in actual_balances.items()}

    # 2. Build list of scheduled timeline events across horizon
    raw_events: List[Tuple[date, str, str, SupportedCurrency, Decimal]] = []
    # (event_date, event_type, description, currency, amount)

    # 2a. Income events
    for inc in scenario.expected_income:
        curr_date = inc.expected_date
        while curr_date <= end_date:
            if curr_date >= base_date:
                raw_events.append((
                    curr_date,
                    "INCOME",
                    f"Income: {inc.source_name}",
                    inc.currency,
                    inc.amount,
                ))
            if not inc.is_recurring or not inc.recurrence_interval_days:
                break
            curr_date = curr_date + timedelta(days=inc.recurrence_interval_days)

    # 2b. Monthly living expenses (generate for each calendar month in horizon)
    cur_cursor = base_date
    while cur_cursor <= end_date:
        for exp in scenario.monthly_living_expenses:
            # construct date for this month
            try:
                exp_date = date(cur_cursor.year, cur_cursor.month, exp.due_day_of_month)
            except ValueError:
                # Handle month with fewer days (e.g. Feb 30 -> Feb 28)
                exp_date = date(cur_cursor.year, cur_cursor.month, 28)

            if base_date <= exp_date <= end_date:
                raw_events.append((
                    exp_date,
                    "LIVING_EXPENSE",
                    f"Expense: {exp.category}",
                    exp.currency,
                    -exp.monthly_amount,
                ))
        # advance cursor by ~28 days to next month
        cur_cursor = (cur_cursor.replace(day=1) + timedelta(days=32)).replace(day=1)

    # 2c. Tuition obligations
    for tuit in scenario.tuition_obligations:
        if base_date <= tuit.due_date <= end_date:
            raw_events.append((
                tuit.due_date,
                "TUITION",
                f"Tuition Deadline: {tuit.term} Institutional Bill",
                tuit.currency,
                -tuit.amount_due,
            ))

    # 2d. Planned Remittances
    # Deducts from send currency on planned_date, adds estimated net to target currency 2 days later
    for rem in scenario.planned_remittances:
        if base_date <= rem.planned_date <= end_date:
            raw_events.append((
                rem.planned_date,
                "REMITTANCE_OUT",
                f"Cross-Border Outflow: {rem.plan_name}",
                rem.send_currency,
                -rem.send_amount,
            ))

            arrival_date = rem.planned_date + timedelta(days=2)
            if arrival_date <= end_date:
                # Determine expected received amount
                if rem.estimated_received_amount:
                    rec_amount = rem.estimated_received_amount
                else:
                    fx_quote = get_dated_fx_quote(rem.send_currency, rem.target_currency, reference_time=None)
                    rec_amount = round_money_standard(rem.send_amount * fx_quote.rate)

                raw_events.append((
                    arrival_date,
                    "REMITTANCE_IN",
                    f"Cross-Border Inflow: {rem.plan_name} (Arrived in {rem.target_currency.value})",
                    rem.target_currency,
                    rec_amount,
                ))

    # Sort events strictly by date
    raw_events.sort(key=lambda x: x[0])

    # 3. Simulate timeline and detect shortfalls
    timeline_events: List[TimelineEvent] = []
    shortfalls: List[ShortfallEvent] = []
    daily_summaries: List[DailyCurrencyBalance] = []

    total_inflows_by_curr: Dict[str, Decimal] = {k: Decimal("0.00") for k in actual_balances}
    total_outflows_by_curr: Dict[str, Decimal] = {k: Decimal("0.00") for k in actual_balances}

    event_counter = 1
    shortfall_counter = 1
    detected_shortfall_currencies = set()

    for ev_date, ev_type, desc, curr, amt in raw_events:
        curr_key = curr.value
        if curr_key not in running_balances:
            running_balances[curr_key] = Decimal("0.00")
            total_inflows_by_curr[curr_key] = Decimal("0.00")
            total_outflows_by_curr[curr_key] = Decimal("0.00")

        start_bal = running_balances[curr_key]
        if amt > Decimal("0.00"):
            total_inflows_by_curr[curr_key] += amt
            inflow = amt
            outflow = Decimal("0.00")
        else:
            total_outflows_by_curr[curr_key] += abs(amt)
            inflow = Decimal("0.00")
            outflow = abs(amt)

        end_bal = start_bal + amt
        running_balances[curr_key] = end_bal

        timeline_events.append(
            TimelineEvent(
                event_id=f"EVT-{event_counter:03d}",
                event_date=ev_date,
                event_type=ev_type,
                description=desc,
                currency=curr,
                amount=amt,
                is_projected=True,
            )
        )
        event_counter += 1

        # Check for shortfall (balance < 0 or below minimum safety reserve)
        reserve_threshold = safety_reserve_by_currency.get(curr_key, Decimal("0.00"))
        is_shortfall = end_bal < Decimal("0.00") or end_bal < reserve_threshold

        deficit_amt = Decimal("0.00")
        if end_bal < Decimal("0.00"):
            deficit_amt = abs(end_bal)
        elif end_bal < reserve_threshold:
            deficit_amt = reserve_threshold - end_bal

        daily_summaries.append(
            DailyCurrencyBalance(
                date=ev_date,
                currency=curr,
                starting_balance=start_bal,
                total_inflow=inflow,
                total_outflow=outflow,
                ending_balance=end_bal,
                is_projected=True,
                is_shortfall=is_shortfall,
                shortfall_amount=deficit_amt,
            )
        )

        # Record discrete shortfall event when entering deficit
        if is_shortfall and curr_key not in detected_shortfall_currencies:
            days_from_start = (ev_date - base_date).days
            urgency = "CRITICAL" if days_from_start <= 30 else ("HIGH" if days_from_start <= 60 else "MEDIUM")
            shortfalls.append(
                ShortfallEvent(
                    shortfall_id=f"SFT-{shortfall_counter:02d}",
                    shortfall_date=ev_date,
                    currency=curr,
                    projected_balance=end_bal,
                    shortfall_amount=deficit_amt,
                    trigger_event=desc,
                    days_from_start=days_from_start,
                    urgency=urgency,
                )
            )
            shortfall_counter += 1
            if end_bal < Decimal("0.00"):
                detected_shortfall_currencies.add(curr_key)

    assumptions = [
        "Forecast is computed for exactly 90 calendar days from the baseline date.",
        "Verified liquid balances reflect actual position; all subsequent transactions are projected.",
        "Monthly living expenses are assumed to be paid on the specified day of month.",
        "Cross-border remittances are modeled with a 2-day banking network transit buffer.",
        "Zero discretionary expense inflation or emergency expenditures are assumed in the baseline scenario.",
    ]

    completeness_report = evaluate_data_completeness(scenario)

    return CashFlowForecastResponse(
        forecast_start_date=base_date,
        forecast_end_date=end_date,
        horizon_days=horizon_days,
        actual_balances_as_of=base_date,
        initial_actual_balances=actual_balances,
        projected_end_balances=running_balances,
        total_inflows_by_currency=total_inflows_by_curr,
        total_outflows_by_currency=total_outflows_by_curr,
        timeline_events=timeline_events,
        daily_summaries=daily_summaries,
        shortfalls=shortfalls,
        assumptions=assumptions,
        data_completeness=completeness_report,
    )

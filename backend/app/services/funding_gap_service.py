from datetime import date, timedelta
from decimal import Decimal
from typing import Dict, List
from app.schemas.profile import FullStudentScenario
from app.schemas.common import SupportedCurrency, DatedFXQuote
from app.schemas.funding_gap import (
    CurrencyObligationItem,
    SingleCurrencyPosition,
    CrossCurrencyConversionOption,
    FundingGapResponse,
)
from app.services.fx_service import get_dated_fx_quote, round_money_standard


def analyze_funding_gap(
    scenario: FullStudentScenario,
    horizon_days: int = 90,
    stale_quote_threshold_hours: int = 24,
    custom_fx_quote: DatedFXQuote | None = None,
    as_of_date: date | None = None,
) -> FundingGapResponse:
    """
    Perform rigorous multi-currency funding-gap analysis.
    Crucial rule: Never silently combine distinct currencies. Each currency position is audited
    independently. Potential cross-currency coverage uses dated, provenance-tracked FX quotes.
    """
    analysis_date = as_of_date or date(2026, 10, 15)
    end_date = analysis_date + timedelta(days=horizon_days)

    home_curr = scenario.profile.home_currency
    study_curr = scenario.profile.study_currency

    # 1. Collect all obligations within the horizon
    obligations: List[CurrencyObligationItem] = []
    obligations_by_curr: Dict[str, Decimal] = {
        home_curr.value: Decimal("0.00"),
        study_curr.value: Decimal("0.00"),
    }

    # 1a. Tuition
    for t in scenario.tuition_obligations:
        if analysis_date <= t.due_date <= end_date:
            obligations.append(
                CurrencyObligationItem(
                    title=f"Tuition: {t.term}",
                    category="TUITION",
                    due_date=t.due_date,
                    currency=t.currency,
                    amount=t.amount_due,
                    is_mandatory=True,
                )
            )
            c_key = t.currency.value
            obligations_by_curr[c_key] = obligations_by_curr.get(c_key, Decimal("0.00")) + t.amount_due

    # 1b. Living expenses accrued across horizon months
    # Approximate months covered in horizon
    months_in_horizon = Decimal(str(round(horizon_days / 30.416, 2)))
    for exp in scenario.monthly_living_expenses:
        total_exp_amt = round_money_standard(exp.monthly_amount * months_in_horizon)
        obligations.append(
            CurrencyObligationItem(
                title=f"Living: {exp.category} ({horizon_days}d projection)",
                category="LIVING",
                due_date=analysis_date + timedelta(days=30),
                currency=exp.currency,
                amount=total_exp_amt,
                is_mandatory=exp.is_fixed,
            )
        )
        c_key = exp.currency.value
        obligations_by_curr[c_key] = obligations_by_curr.get(c_key, Decimal("0.00")) + total_exp_amt

    # 2. Collect resources by currency
    actual_balances: Dict[str, Decimal] = {
        home_curr.value: Decimal("0.00"),
        study_curr.value: Decimal("0.00"),
    }
    for bal in scenario.available_balances:
        c_key = bal.currency.value
        actual_balances[c_key] = actual_balances.get(c_key, Decimal("0.00")) + bal.actual_balance

    expected_inflows: Dict[str, Decimal] = {
        home_curr.value: Decimal("0.00"),
        study_curr.value: Decimal("0.00"),
    }
    for inc in scenario.expected_income:
        curr_d = inc.expected_date
        while curr_d <= end_date:
            if curr_d >= analysis_date:
                c_key = inc.currency.value
                expected_inflows[c_key] = expected_inflows.get(c_key, Decimal("0.00")) + inc.amount
            if not inc.is_recurring or not inc.recurrence_interval_days:
                break
            curr_d = curr_d + timedelta(days=inc.recurrence_interval_days)

    # 3. Build single currency positions (Zero silent conversion)
    currency_positions: Dict[str, SingleCurrencyPosition] = {}
    all_currencies = set(actual_balances.keys()) | set(obligations_by_curr.keys())

    for c_code in all_currencies:
        act = actual_balances.get(c_code, Decimal("0.00"))
        infl = expected_inflows.get(c_code, Decimal("0.00"))
        tot_res = act + infl
        tot_ob = obligations_by_curr.get(c_code, Decimal("0.00"))
        net_pos = tot_res - tot_ob
        has_gap = net_pos < Decimal("0.00")
        gap_amt = abs(net_pos) if has_gap else Decimal("0.00")

        currency_positions[c_code] = SingleCurrencyPosition(
            currency=SupportedCurrency(c_code),
            actual_liquid_balance=act,
            expected_inflows=infl,
            total_available_resources=tot_res,
            total_obligations=tot_ob,
            net_position=net_pos,
            has_direct_gap=has_gap,
            direct_gap_amount=gap_amt,
        )

    # 4. Target study currency gap analysis
    study_pos = currency_positions.get(study_curr.value)
    study_has_shortfall = study_pos.has_direct_gap if study_pos else False
    study_shortfall_amt = study_pos.direct_gap_amount if study_pos else Decimal("0.00")

    # 5. Cross-currency coverage analysis using dated FX quote
    cross_remedy: CrossCurrencyConversionOption | None = None
    rate_warnings: List[str] = []
    has_stale_warning = False

    home_pos = currency_positions.get(home_curr.value)
    available_home_surplus = home_pos.net_position if (home_pos and home_pos.net_position > Decimal("0.00")) else Decimal("0.00")

    if study_has_shortfall and available_home_surplus > Decimal("0.00"):
        # Resolve FX quote with staleness check
        if custom_fx_quote is not None:
            fx_quote = custom_fx_quote
        else:
            fx_quote = get_dated_fx_quote(
                base_currency=home_curr,
                quote_currency=study_curr,
                max_age_hours=stale_quote_threshold_hours,
            )

        if fx_quote.is_stale:
            has_stale_warning = True
            rate_warnings.append(
                f"STALE QUOTE: Rate for {home_curr.value} -> {study_curr.value} is dated "
                f"{fx_quote.timestamp_utc.strftime('%Y-%m-%d %H:%M UTC')}. {fx_quote.staleness_warning}"
            )

        # Realistic transfer fee model (wire fixed fee + 0.5% margin)
        if home_curr == SupportedCurrency.BDT:
            est_fixed_fee = Decimal("500.00")
        elif home_curr == SupportedCurrency.CNY:
            est_fixed_fee = Decimal("18.00")
        elif home_curr == SupportedCurrency.INR:
            est_fixed_fee = Decimal("500.00")
        else:
            est_fixed_fee = Decimal("20.00")
        convertible_home_amt = max(Decimal("0.00"), available_home_surplus - est_fixed_fee)
        net_convertible_study = round_money_standard(convertible_home_amt * fx_quote.rate)

        can_cover = net_convertible_study >= study_shortfall_amt
        rem_gap = max(Decimal("0.00"), study_shortfall_amt - net_convertible_study)

        caveats = [
            f"Quote source: {fx_quote.source} recorded at {fx_quote.timestamp_utc.strftime('%Y-%m-%d %H:%M UTC')}.",
            f"Deducted estimated network wire fee of {est_fixed_fee} {home_curr.value}.",
            "Foreign exchange rates fluctuate prior to actual execution; exact proceeds will vary.",
        ]
        if fx_quote.is_stale:
            caveats.append("WARNING: This conversion estimate is based on a stale quote and must be re-quoted prior to settlement.")

        cross_remedy = CrossCurrencyConversionOption(
            source_currency=home_curr,
            target_currency=study_curr,
            available_surplus_in_source=available_home_surplus,
            dated_fx_quote=fx_quote,
            estimated_provider_fee=est_fixed_fee,
            net_convertible_in_target=net_convertible_study,
            can_cover_full_gap=can_cover,
            remaining_gap_after_conversion=rem_gap,
            conversion_caveats=caveats,
        )

    # 6. Determine summary status
    if not study_has_shortfall:
        summary_status = "FULLY_FUNDED"
    elif cross_remedy and cross_remedy.can_cover_full_gap:
        summary_status = "COVERABLE_VIA_TRANSFER"
    else:
        summary_status = "CRITICAL_DEFICIT"

    audit_notes = [
        f"Obligations analyzed strictly across {horizon_days} calendar days ending {end_date.isoformat()}.",
        "Multi-currency separation preserved: distinct accounts maintained for domestic and international holdings.",
        "Conversions between currencies require explicit execution and are subject to intermediary wire times.",
    ]

    return FundingGapResponse(
        analysis_date=analysis_date,
        horizon_days=horizon_days,
        study_currency=study_curr,
        home_currency=home_curr,
        currency_positions=currency_positions,
        obligations=obligations,
        target_currency_has_shortfall=study_has_shortfall,
        target_currency_shortfall_amount=study_shortfall_amt,
        cross_currency_remedy=cross_remedy,
        has_stale_rate_warning=has_stale_warning,
        rate_warnings=rate_warnings,
        summary_status=summary_status,
        audit_notes=audit_notes,
    )

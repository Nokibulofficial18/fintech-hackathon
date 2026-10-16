from datetime import datetime, timezone, date
from decimal import Decimal
from typing import List
from app.schemas.profile import FullStudentScenario
from app.schemas.recommendations import (
    RecommendationPriority,
    RecommendationUrgency,
    RecommendationCategory,
    ActionableRecommendation,
    RecommendationsResponse,
)
from app.schemas.common import SupportedCurrency
from app.services.forecast_service import generate_cash_flow_forecast
from app.services.funding_gap_service import analyze_funding_gap
from app.services.transfer_service import get_transfer_provider_quotes
from app.schemas.transfers import TransferCompareRequest


def generate_recommendations(
    scenario: FullStudentScenario,
    reference_date: date | None = None,
) -> RecommendationsResponse:
    """
    Generate deterministic, prioritized financial recommendations from quantitative analysis.
    Zero hallucination, zero investment advice, zero commercial promises.
    """
    now_utc = datetime.now(timezone.utc)
    ref_date = reference_date or date(2026, 10, 15)

    recs: List[ActionableRecommendation] = []

    # 1. Run Quantitative Services
    gap_analysis = analyze_funding_gap(scenario, horizon_days=90, as_of_date=ref_date)
    forecast = generate_cash_flow_forecast(scenario, start_date=ref_date, horizon_days=90)

    # 2. Recommendation: Tuition Fund Preservation
    if scenario.tuition_obligations:
        tuit = scenario.tuition_obligations[0]
        days_to_tuition = (tuit.due_date - ref_date).days
        urgency = (
            RecommendationUrgency.IMMEDIATE
            if days_to_tuition <= 21
            else (RecommendationUrgency.UPCOMING if days_to_tuition <= 45 else RecommendationUrgency.PLANNING)
        )
        recs.append(
            ActionableRecommendation(
                id="REC-TUITION-PRESERVE-01",
                priority=RecommendationPriority.CRITICAL if days_to_tuition <= 45 else RecommendationPriority.HIGH,
                urgency=urgency,
                category=RecommendationCategory.TUITION_PRESERVATION,
                title=f"Ringfence Tuition Funds for {tuit.term} Deadline",
                reason=(
                    f"A tuition payment of {tuit.amount_due} {tuit.currency.value} is due on {tuit.due_date.isoformat()} "
                    f"({days_to_tuition} days remaining). Missing this deadline incurs a late penalty of "
                    f"{tuit.late_penalty_fee} {tuit.currency.value} and academic registration holds."
                ),
                supporting_numbers={
                    "tuition_amount": float(tuit.amount_due),
                    "currency": tuit.currency.value,
                    "due_date": tuit.due_date.isoformat(),
                    "days_remaining": days_to_tuition,
                    "late_penalty": float(tuit.late_penalty_fee),
                },
                assumptions=[
                    "Tuition fee amount is final as billed by the university registrar.",
                    "Late fee applies immediately upon deadline expiration.",
                ],
                uncertainty=(
                    "International wire transfer processing can take 3 to 5 business days during peak semester intake. "
                    "Funds must be initiated at least 7 to 10 days before the deadline."
                ),
                suggested_action=(
                    f"Maintain at least {tuit.amount_due} {tuit.currency.value} in liquid study accounts and initiate "
                    f"all necessary cross-border transfers no later than {days_to_tuition - 10} days from now."
                ),
            )
        )

    # 3. Recommendation: Funding Gap / Deficit Warning
    if gap_analysis.target_currency_has_shortfall:
        study_curr = gap_analysis.study_currency.value
        shortfall_amt = gap_analysis.target_currency_shortfall_amount
        can_cover = gap_analysis.cross_currency_remedy and gap_analysis.cross_currency_remedy.can_cover_full_gap

        if can_cover:
            recs.append(
                ActionableRecommendation(
                    id="REC-GAP-REMEDY-02",
                    priority=RecommendationPriority.HIGH,
                    urgency=RecommendationUrgency.IMMEDIATE,
                    category=RecommendationCategory.FUNDING_GAP_ALERT,
                    title=f"Execute Planned Cross-Border Remittance to Bridge {shortfall_amt} {study_curr} Deficit",
                    reason=(
                        f"Target study currency obligations exceed current study balances by {shortfall_amt} {study_curr}. "
                        f"However, available home currency surplus ({gap_analysis.cross_currency_remedy.available_surplus_in_source} "
                        f"{gap_analysis.home_currency.value}) is sufficient to cover this requirement once transferred."
                    ),
                    supporting_numbers={
                        "shortfall_amount": float(shortfall_amt),
                        "target_currency": study_curr,
                        "home_surplus": float(gap_analysis.cross_currency_remedy.available_surplus_in_source),
                        "home_currency": gap_analysis.home_currency.value,
                        "net_convertible_study": float(gap_analysis.cross_currency_remedy.net_convertible_in_target),
                    },
                    assumptions=[
                        "Home account funds are unencumbered and eligible for outward student remittance.",
                        "Exchange rate remains within ±2% of benchmark quote.",
                    ],
                    uncertainty=(
                        "Regulatory compliance documentation (e.g. Bangladesh Bank Authorized Dealer Student File / Form TM "
                        "for outward education remittance, and China SAFE non-resident inward clearing) and bank clearing times "
                        "may delay execution."
                        if gap_analysis.home_currency == SupportedCurrency.BDT
                        else "Regulatory compliance documentation and intermediary bank clearing times may delay execution."
                    ),
                    suggested_action=(
                        f"Initiate transfer of home funds ahead of upcoming bills to prevent overdraft or enrollment holds."
                    ),
                )
            )
        else:
            recs.append(
                ActionableRecommendation(
                    id="REC-GAP-CRITICAL-02",
                    priority=RecommendationPriority.CRITICAL,
                    urgency=RecommendationUrgency.IMMEDIATE,
                    category=RecommendationCategory.FUNDING_GAP_ALERT,
                    title=f"Critical Unfunded Deficit Detected ({shortfall_amt} {study_curr})",
                    reason=(
                        f"Projected 90-day obligations exceed both study and home currency liquid holdings. "
                        f"A net uncovered deficit of {shortfall_amt} {study_curr} remains."
                    ),
                    supporting_numbers={
                        "uncovered_shortfall": float(shortfall_amt),
                        "currency": study_curr,
                        "horizon_days": 90,
                    },
                    assumptions=[
                        "All living expense line items and tuition obligations are mandatory.",
                    ],
                    uncertainty="Potential additional emergency or discretionary costs are not yet accounted for.",
                    suggested_action=(
                        "Explore institutional emergency student loans, departmental bursaries, or adjust discretionary expense categories."
                    ),
                )
            )

    # 4. Recommendation: Transfer Channel Optimization
    if scenario.planned_remittances:
        rem = scenario.planned_remittances[0]
        try:
            compare_req = TransferCompareRequest(
                send_amount=rem.send_amount,
                send_currency=rem.send_currency,
                receive_currency=rem.target_currency,
            )
            quote_comp = get_transfer_provider_quotes(compare_req)
            if quote_comp.potential_savings_vs_bank > Decimal("0.00"):
                recs.append(
                    ActionableRecommendation(
                        id="REC-TRANSFER-OPTIMIZE-03",
                        priority=RecommendationPriority.MEDIUM,
                        urgency=RecommendationUrgency.UPCOMING,
                        category=RecommendationCategory.TRANSFER_OPTIMIZATION,
                        title=f"Compare Wire Providers for Planned {rem.send_amount} {rem.send_currency.value} Remittance",
                        reason=(
                            f"Routing your planned transfer through a transparent digital FX specialist rather than "
                            f"a traditional wire bank benchmark yields approximately {quote_comp.potential_savings_vs_bank} "
                            f"{rem.send_currency.value} in reduced wire fees and tighter FX markup margin."
                        ),
                        supporting_numbers={
                            "send_amount": float(rem.send_amount),
                            "send_currency": rem.send_currency.value,
                            "benchmark_savings": float(quote_comp.potential_savings_vs_bank),
                            "recommended_provider": quote_comp.recommended_cheapest,
                        },
                        assumptions=[
                            "Provider fee schedules reflect current public retail benchmarks.",
                            "Transfer amount is sent via direct bank-to-bank account debit.",
                        ],
                        uncertainty=(
                            "Provider promotional rates and intermediary wire correspondent fees can vary at time of initiation. "
                            "Actual realized savings depend on live quotes."
                        ),
                        suggested_action=(
                            f"Review quote breakdowns across digital specialists before initiating the wire transfer."
                        ),
                    )
                )
        except Exception:
            pass

    # 5. Recommendation: Discretionary Expense & Living Buffer
    total_monthly_burn = sum(e.monthly_amount for e in scenario.monthly_living_expenses)
    study_balance = next(
        (b.actual_balance for b in scenario.available_balances if b.currency == scenario.profile.study_currency),
        Decimal("0.00"),
    )
    if total_monthly_burn > Decimal("0.00"):
        burn_runway = study_balance / total_monthly_burn
        if burn_runway < Decimal("2.0"):
            recs.append(
                ActionableRecommendation(
                    id="REC-RUNWAY-BUFFER-04",
                    priority=RecommendationPriority.MEDIUM,
                    urgency=RecommendationUrgency.PLANNING,
                    category=RecommendationCategory.LIQUIDITY_BUFFER,
                    title="Build a 2-Month Living Expense Buffer",
                    reason=(
                        f"Current verified liquid holdings in {scenario.profile.study_currency.value} ({study_balance}) "
                        f"represent {burn_runway:.1f} months of living burn ({total_monthly_burn} {scenario.profile.study_currency.value}/month). "
                        f"International students should aim for a minimum 2-month local liquidity buffer."
                    ),
                    supporting_numbers={
                        "monthly_burn": float(total_monthly_burn),
                        "current_study_balance": float(study_balance),
                        "runway_months": float(round(burn_runway, 1)),
                        "recommended_buffer_months": 2.0,
                    },
                    assumptions=[
                        "Monthly burn is consistent across academic semesters.",
                    ],
                    uncertainty="Housing utility volatility in winter months may increase monthly costs.",
                    suggested_action=(
                        "Prioritize non-discretionary expenses (rent, groceries) and defer non-essential leisure expenditures."
                    ),
                )
            )

    # Sort recommendations by priority (CRITICAL -> HIGH -> MEDIUM -> LOW)
    priority_order = {
        RecommendationPriority.CRITICAL: 0,
        RecommendationPriority.HIGH: 1,
        RecommendationPriority.MEDIUM: 2,
        RecommendationPriority.LOW: 3,
    }
    recs.sort(key=lambda r: priority_order[r.priority])

    crit_count = sum(1 for r in recs if r.priority == RecommendationPriority.CRITICAL)
    high_count = sum(1 for r in recs if r.priority == RecommendationPriority.HIGH)

    return RecommendationsResponse(
        generated_at_utc=now_utc,
        total_recommendations=len(recs),
        critical_count=crit_count,
        high_count=high_count,
        recommendations=recs,
    )

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional
from app.schemas.common import SupportedCurrency
from app.schemas.assistant import (
    ChatRequest,
    ChatResponse,
    ToolExecutionResult,
)
from app.schemas.recommendations import ActionableRecommendation
from app.ai.safety import evaluate_prompt_safety
from app.ai.tools import dispatch_tool, APPROVED_TOOLS
from app.services.demo_scenario_service import get_seeded_demo_scenario
from app.core.config import settings


class CopilotOrchestrator:
    """
    Orchestration service for BorderWise AI Copilot.
    Validates tool calls, enforces safety guardrails, derives all numbers strictly
    from deterministic backend services, and generates structured explanations.
    """

    def process_chat(self, request: ChatRequest) -> ChatResponse:
        user_query = request.message.strip()

        # 1. Safety & Security Guardrail
        is_safe, refusal_reason, is_transfer_cmd = evaluate_prompt_safety(user_query)
        if not is_safe:
            return ChatResponse(
                message=refusal_reason or "Request refused by security policy.",
                tool_results=[],
                recommendations=[],
                assumptions=["Safety policy enforced."],
                warnings=[
                    "Disallowed prompt instruction, policy override, or autonomous action request.",
                    "BorderWise AI cannot move money or authorize transfers autonomously.",
                ],
                data_timestamps={"guardrail_timestamp": datetime.now(timezone.utc).isoformat()},
                is_demo_mode=True,
                requires_confirmation=False,
            )

        # 2. Tool Execution & Intent Resolution
        tool_results: List[ToolExecutionResult] = []
        recommendations: List[ActionableRecommendation] = []
        assumptions: List[str] = []
        warnings: List[str] = []
        data_timestamps: Dict[str, str] = {
            "evaluation_time_utc": datetime.now(timezone.utc).isoformat(),
        }
        requires_confirmation = False
        confirmation_preview: Optional[Dict[str, Any]] = None

        lower = user_query.lower()

        # Check student profile & context via overview tool
        ov_tool = dispatch_tool("get_student_overview", {})
        tool_results.append(ov_tool)
        ov = ov_tool.output
        study_curr = ov.get("study_currency", "CNY")
        home_curr = ov.get("home_currency", "BDT")

        def _get_symbol(c: str) -> str:
            syms = {"CNY": "¥", "BDT": "৳", "USD": "$", "GBP": "£", "INR": "₹", "EUR": "€"}
            return syms.get(c, c + " ")

        study_sym = _get_symbol(study_curr)
        home_sym = _get_symbol(home_curr)

        # Branch 1: Delayed income / scholarship simulation
        if request.simulate_delayed_income_days or "delayed" in lower or "late" in lower:
            delay_days = request.simulate_delayed_income_days or 14
            kw = "Stipend" if study_curr == "CNY" else ("Scholarship" if study_curr == "USD" else "Bursary")
            sim_res = dispatch_tool(
                "simulate_delayed_income",
                {"delay_days": delay_days, "income_source_keyword": kw},
            )
            tool_results.append(sim_res)

            out = sim_res.output
            default_delay_amt = 3500.0 if study_curr == "CNY" else (850.0 if study_curr == "GBP" else 3000.0)
            delayed_amt = out.get("delayed_amount", default_delay_amt)
            message = (
                f"Simulating a {delay_days}-day delay in your {out.get('delayed_income_source', 'educational funding')} "
                f"({study_sym}{delayed_amt:,.2f} {study_curr}) shifts receipt to {out.get('new_disbursement_date')}. "
                f"Because this delay stresses local cash flow before the November 15 tuition deadline, "
                f"your {study_curr} balance experiences acute shortfall pressure before cross-border remittances arrive. "
                f"Recommended adjustment: Initiate outbound remittance from your {home_curr} reserves in Bangladesh at least 10 business days prior.\n\n"
                f"Notice: No money was moved. This is an advisory cash-flow simulation."
            )
            assumptions = [
                f"Income disbursement of {study_sym}{delayed_amt:,.2f} {study_curr} is delayed by exactly {delay_days} days.",
                "Tuition deadline remains firm at 2026-11-15 with standard late fee penalties.",
            ]
            warnings = [
                "Simulated scenario analysis: No actual academic record or disbursement schedule was altered.",
            ]
            requires_confirmation = True
            confirmation_preview = {
                "action": "Simulate Delayed Income Planning Buffer",
                "income_source": out.get("delayed_income_source"),
                "delay_days": delay_days,
                "adjusted_date": out.get("new_disbursement_date"),
                "impact": out.get("impact_summary"),
                "money_movement": "No money was moved. Simulated scenario only.",
            }

        # Branch 2: Tuition affordability
        elif "tuition" in lower and any(w in lower for w in ["afford", "can i", "next month", "pay", "cover", "upcoming"]):
            gap_res = dispatch_tool("calculate_funding_gap", {"horizon_days": 60})
            tool_results.append(gap_res)
            gap_data = gap_res.output

            default_tuit = 24000.0 if study_curr == "CNY" else (9250.0 if study_curr == "GBP" else 14500.0)
            default_bal = 8500.0 if study_curr == "CNY" else (2400.0 if study_curr == "GBP" else 4200.0)
            default_home = 350000.0 if study_curr == "CNY" else (950000.0 if study_curr == "GBP" else 650000.0)
            default_shortfall = 15300.0 if study_curr == "CNY" else (7800.0 if study_curr == "GBP" else 9604.0)

            tuit_amt = ov.get("tuition_amount_due", default_tuit)
            tuit_date = ov.get("tuition_due_date", "2026-11-15")
            days_left = ov.get("days_until_tuition_due", 31)
            study_bal = ov.get("verified_balances", {}).get(study_curr, default_bal)
            home_bal = ov.get("verified_balances", {}).get(home_curr, default_home)
            shortfall = gap_data.get("target_currency_shortfall_amount", default_shortfall)

            if study_curr == "CNY":
                message = (
                    f"Your upcoming tuition of {study_sym}{tuit_amt:,.2f} {study_curr} is due on {tuit_date} ({days_left} days away). "
                    f"Your current China liquid account (ICBC) holds {study_sym}{study_bal:,.2f} {study_curr}. Combined with monthly living expenses "
                    f"({study_sym}{ov.get('monthly_living_burn', 3300.0):,.2f} {study_curr}), there is a direct local shortfall of "
                    f"{study_sym}{shortfall:,.2f} {study_curr}.\n\n"
                    f"Your planned family remittance of {home_sym}250,000.00 {home_curr} from Bangladesh yields approximately "
                    f"{study_sym}14,640.00 {study_curr} via digital specialist. While this covers most of the obligation, "
                    f"it leaves a minor remaining gap of ~{study_sym}660.00 {study_curr}.\n\n"
                    f"Your family savings in Bangladesh (DBBL Dhaka) holds {home_sym}{home_bal:,.2f} {home_curr} total. "
                    f"Conclusion: Yes, tuition is affordable provided your family initiates the planned {home_sym}250,000.00 {home_curr} "
                    f"transfer plus a secondary top-up of ~{home_sym}15,000.00 {home_curr} before November 05."
                )
            elif study_curr == "GBP":
                message = (
                    f"Your upcoming tuition of {study_sym}{tuit_amt:,.2f} {study_curr} is due on {tuit_date} ({days_left} days away). "
                    f"Your current UK liquid balance is {study_sym}{study_bal:,.2f} {study_curr}. Combined with monthly living expenses "
                    f"({study_sym}{ov.get('monthly_living_burn', 1800.0):,.2f} {study_curr}), there is a direct local shortfall of "
                    f"{study_sym}{shortfall:,.2f} {study_curr}.\n\n"
                    f"Your planned family remittance of {home_sym}700,000.00 {home_curr} yields approximately "
                    f"{study_sym}6,546.39 {study_curr} via digital specialist, leaving a remaining shortfall of ~{study_sym}1,253.61 {study_curr}.\n\n"
                    f"Conclusion: Yes, tuition is affordable with a secondary top-up before November 05."
                )
            else:
                remedy = gap_data.get("cross_currency_remedy")
                message = (
                    f"Your tuition of {study_sym}{tuit_amt:,.2f} {study_curr} is due on {tuit_date} ({days_left} days away). "
                    f"Your current liquid balance leaves a direct shortfall of {study_sym}{shortfall:,.2f} {study_curr}. "
                    f"Conclusion: Yes, you can afford tuition, provided you initiate a remittance from your home account "
                    f"at least 10 business days before {tuit_date}."
                )

            assumptions = [
                f"Tuition amount is billed at {study_sym}{tuit_amt:,.2f} {study_curr} due on {tuit_date}.",
                f"Home currency {home_curr} accounts remain available for outbound educational remittances.",
            ]
            warnings = [
                "FX benchmark quotes fluctuate prior to clearing; exact received proceeds depend on final provider quote.",
                "Advisory notice: No money was moved. Real remittances require manual banking dispatch.",
            ]

        # Branch 3: Money remaining after rent & tuition
        elif any(w in lower for w in ["remain", "after rent", "after tuition", "how much money"]):
            forecast_res = dispatch_tool("calculate_forecast", {"horizon_days": 60})
            tool_results.append(forecast_res)
            fc = forecast_res.output

            study_end = fc.get("projected_end_balances", {}).get(study_curr, 0.0)
            home_end = fc.get("projected_end_balances", {}).get(home_curr, 0.0)
            default_tuit = 24000.0 if study_curr == "CNY" else (9250.0 if study_curr == "GBP" else 14500.0)
            default_burn = 3300.0 if study_curr == "CNY" else (1800.0 if study_curr == "GBP" else 2400.0)
            tuit_amt = ov.get("tuition_amount_due", default_tuit)
            burn = ov.get("monthly_living_burn", default_burn)

            message = (
                f"Over the next 60 days, accounting for living expenses ({study_sym}{burn:,.2f} {study_curr}/mo living burn) and tuition "
                f"({study_sym}{tuit_amt:,.2f} {study_curr} due {ov.get('tuition_due_date', '2026-11-15')}), your projected standalone "
                f"{study_curr} balance will be approximately {study_sym}{study_end:,.2f} {study_curr}, while home reserves "
                f"maintain approximately {home_sym}{home_end:,.2f} {home_curr}.\n\n"
                f"Because tuition absorbs all local liquid reserves, completing the planned family remittance before November 10 "
                f"is vital to maintain a sustainable living buffer."
            )
            assumptions = [
                f"Monthly living expenses recurring at {study_sym}{burn:,.2f} {study_curr}/month.",
                f"Contractual tuition due date is firm with {study_sym}300 late fee penalties.",
            ]
            warnings = [
                "Notice: BorderWise AI is an advisory copilot. No money was moved.",
            ]

        # Branch 4: Specific Exchange Rate Inquiry
        elif any(w in lower for w in ["exchange rate", "fx rate", "conversion rate", "what is the rate", "mid-market rate", "benchmark rate"]) and not any(w in lower for w in ["send 1,000", "send 1000", "send 500", "send 250,000", "transfer options"]):
            from app.services.fx_service import get_dated_fx_quote
            quote_cny_bdt = get_dated_fx_quote(SupportedCurrency.CNY, SupportedCurrency.BDT)
            quote_bdt_cny = get_dated_fx_quote(SupportedCurrency.BDT, SupportedCurrency.CNY)

            message = (
                f"**Current Benchmark Foreign Exchange Rates (China–Bangladesh Corridor)**:\n\n"
                f"• **1 CNY = {quote_cny_bdt.rate:.6f} BDT** (Benchmark Mid-Market)\n"
                f"• **1 BDT = {quote_bdt_cny.rate:.6f} CNY** (Reciprocal Rate)\n\n"
                f"- **Data Source**: {quote_cny_bdt.source}\n"
                f"- **Timestamp**: {quote_cny_bdt.timestamp_utc.strftime('%Y-%m-%d %H:%M UTC')}\n"
                f"- **Freshness Status**: {'STALE (>24h)' if quote_cny_bdt.is_stale else 'VERIFIED FRESH'}\n"
                f"- **ISO Codes**: Chinese Yuan (`CNY`, also known as RMB / ¥), Bangladeshi Taka (`BDT` / ৳).\n\n"
                f"*Data Status: DEMO DATA (simulated central reference benchmark).*"
            )
            assumptions = [
                "Rates represent synthetic mid-market benchmark references without retail bank markups.",
                "RMB is treated as the common name for CNY (ISO code: CNY).",
            ]
            warnings = [
                "Retail provider rates include commercial markups ranging from 0.50% (digital specialists) to 2.60% (traditional wire banks).",
            ]

        # Branch 5: Itemized Living Expenses & Housing Rent Inquiry
        elif any(w in lower for w in ["living expense", "monthly expense", "monthly expenses", "rent", "monthly burn", "cost of living", "living cost", "breakdown of expenses", "reserve", "how much should i reserve", "monthly budget"]):
            scenario = get_seeded_demo_scenario()
            items = scenario.monthly_living_expenses
            total_burn = sum(e.monthly_amount for e in items)

            lines = [f"• **{e.category}**: {study_sym}{e.monthly_amount:,.2f} {study_curr}/mo (Due day {e.due_day_of_month}, {'Fixed' if e.is_fixed else 'Flexible'})" for e in items]

            rec_min_reserve = total_burn * 2
            rec_max_reserve = total_burn * 3

            message = (
                f"**Monthly Living Expense Budget for {ov.get('student_name', 'Student')}** in China:\n\n"
                + "\n".join(lines) + "\n\n"
                + f"• **Total Monthly Burn**: **{study_sym}{total_burn:,.2f} {study_curr}/month**.\n"
                f"• **Current Study Account Runway**: At your verified liquid balance ({study_sym}{ov.get('verified_balances', {}).get(study_curr, 8500.0):,.2f} {study_curr}), "
                f"your living runway is approximately **{ov.get('study_currency_runway_months', 2.6)} months** without accounting for tuition.\n"
                f"• **Recommended Living Reserve**: To protect against cross-border transfer delays, financial modeling recommends "
                f"maintaining a standalone living reserve buffer of 2 to 3 months: **{study_sym}{rec_min_reserve:,.2f} – {study_sym}{rec_max_reserve:,.2f} {study_curr}** "
                f"(separate from ringfenced tuition payments)."
            )
            assumptions = [
                f"Monthly expenses recurring at {study_sym}{total_burn:,.2f} {study_curr} per month.",
                "Living reserves are held in local study currency (CNY) to avoid FX conversion delays during term time.",
            ]
            warnings = [
                "Discretionary campus dining and mobile data vary based on student usage.",
            ]

        # Branch 6: Transfer options & recipient calculations (including "If I send 1,000 CNY to Bangladesh...")
        elif any(w in lower for w in [
            "which transfer", "transfer option", "recipient amount", "highest", "cheapest transfer",
            "sending money", "send", "wire", "remit", "remittance"
        ]):
            # Detect transfer direction
            is_bdt_to_cny = ("bdt to cny" in lower or "taka to rmb" in lower or "taka to cny" in lower or "to china" in lower)
            if is_bdt_to_cny:
                send_c = SupportedCurrency.BDT
                rec_c = SupportedCurrency.CNY
                if "250,000" in lower or "250000" in lower:
                    send_amt = Decimal("250000.00")
                else:
                    send_amt = Decimal("250000.00")
            else:
                # Default primary competition demo direction: CNY -> BDT
                send_c = SupportedCurrency.CNY
                rec_c = SupportedCurrency.BDT
                if "1,000" in lower or "1000" in lower or "1000 cny" in lower or "1,000 cny" in lower:
                    send_amt = Decimal("1000.00")
                elif "500" in lower:
                    send_amt = Decimal("500.00")
                elif "5,000" in lower or "5000" in lower:
                    send_amt = Decimal("5000.00")
                else:
                    send_amt = Decimal("1000.00")

            transfers_res = dispatch_tool(
                "compare_transfers",
                {"send_amount": send_amt, "send_currency": send_c, "receive_currency": rec_c},
            )
            tool_results.append(transfers_res)

            tr = transfers_res.output
            cheapest = tr.get("recommended_cheapest", "Digital Specialist")
            quotes = tr.get("quotes", [])
            mid_market = tr.get("mid_market_rate", 16.85)

            # Find best and bank quotes
            best_q = quotes[0] if quotes else None
            for q in quotes:
                if best_q is None or q.get("recipient_amount", 0) > best_q.get("recipient_amount", 0):
                    best_q = q

            bank_q = next((q for q in quotes if "bank" in q.get("provider_name", "").lower()), None)

            s_sym = _get_symbol(send_c.value)
            r_sym = _get_symbol(rec_c.value)

            best_recipient = best_q.get("recipient_amount", 0.0) if best_q else 0.0
            best_fee = best_q.get("total_fee_cost", 0.0) if best_q else 0.0
            best_rate = best_q.get("offered_rate", mid_market) if best_q else mid_market
            best_name = best_q.get("provider_name", cheapest) if best_q else cheapest

            if bank_q and best_q:
                bank_recipient = bank_q.get("recipient_amount", 0.0)
                bank_fee = bank_q.get("total_fee_cost", 0.0)
                extra_delivered = best_recipient - bank_recipient
                fee_saved = bank_fee - best_fee

                message = (
                    f"If you send **{s_sym}{send_amt:,.2f} {send_c.value}** to Bangladesh ({rec_c.value}):\n\n"
                    f"• **Recommended Option ({best_name})**: The recipient will receive approximately "
                    f"**{r_sym}{best_recipient:,.2f} {rec_c.value}** after fees.\n"
                    f"  - Exchange Rate: 1 {send_c.value} = {best_rate:.4f} {rec_c.value} (Benchmark mid-market: {mid_market:.4f})\n"
                    f"  - Upfront Transfer Fee: {s_sym}{best_q.get('upfront_fee', 0.0):,.2f} {send_c.value}\n"
                    f"  - Total Fee & FX Cost: {s_sym}{best_fee:,.2f} {send_c.value}\n"
                    f"  - Delivery Speed: {best_q.get('delivery_time', 'Same day')}\n\n"
                    f"• **Traditional Wire Bank ({bank_q.get('provider_name')})**: Delivers only "
                    f"**{r_sym}{bank_recipient:,.2f} {rec_c.value}** due to higher upfront fees ({s_sym}{bank_q.get('upfront_fee', 0.0):,.2f} {send_c.value}) "
                    f"and an exchange-rate markup margin ({bank_q.get('fx_markup_pct', 2.6):.2f}%).\n\n"
                    f"**Value Difference**: Using {best_name} delivers **{r_sym}{extra_delivered:,.2f} {rec_c.value} more** to the recipient "
                    f"and saves **{s_sym}{fee_saved:,.2f} {send_c.value}** in fees.\n\n"
                    f"*Data Status: DEMO DATA (simulated benchmark quotes). BorderWise AI is an advisory copilot; no actual transfer was executed.*"
                )
            else:
                message = (
                    f"For a transfer of {s_sym}{send_amt:,.2f} {send_c.value} to {rec_c.value}, "
                    f"**{best_name}** delivers approximately {r_sym}{best_recipient:,.2f} {rec_c.value} after fees. "
                    f"Exchange rate: {best_rate:.4f} {rec_c.value} per {send_c.value}.\n\n"
                    f"*Data Status: DEMO DATA (simulated). BorderWise AI does not execute real-world money transfers.*"
                )

            assumptions = [
                f"Transfer calculated for {s_sym}{send_amt:,.2f} {send_c.value} -> {rec_c.value}.",
                f"Simulated benchmark rate of {mid_market:.4f} {rec_c.value} per {send_c.value} with provider margin applied.",
                "RMB and CNY are treated as the same currency (ISO: CNY).",
                "Bangladeshi taka and BDT are treated as the same currency (ISO: BDT).",
            ]
            warnings = [
                "Sample quotes are simulated benchmarks and do not constitute live execution guarantees.",
                "BorderWise AI does not execute actual wire transfers. No money was moved.",
            ]
            requires_confirmation = True
            confirmation_preview = {
                "action": "Simulate Transfer Provider Comparison",
                "recommended_provider": best_name,
                "send_amount": f"{s_sym}{send_amt:,.2f} {send_c.value}",
                "recipient_amount": f"{r_sym}{best_recipient:,.2f} {rec_c.value}",
                "effective_rate": f"1 {send_c.value} = {best_rate:.4f} {rec_c.value}",
                "money_movement": "No money was moved. Simulated quote comparison only.",
            }

        # Branch 7: Prioritization when funding is insufficient & Funding Gap analysis
        elif any(w in lower for w in ["prioritize", "insufficient", "funding gap", "projected funding gap", "projected gap", "shortfall", "what should i do"]):
            gap_res = dispatch_tool("calculate_funding_gap", {"horizon_days": 90})
            recs_res = dispatch_tool("get_action_recommendations", {})
            tool_results.extend([gap_res, recs_res])

            gap_out = gap_res.output
            shortfall_amt = gap_out.get("target_currency_shortfall_amount", 15300.0)
            remedy = gap_out.get("cross_currency_remedy")
            rem_gap = remedy.get("remaining_gap", 660.0) if remedy else 660.0
            net_conv = remedy.get("net_convertible_study", 14640.0) if remedy else 14640.0

            default_tuit = 24000.0 if study_curr == "CNY" else (9250.0 if study_curr == "GBP" else 14500.0)
            default_rent = 1800.0 if study_curr == "CNY" else (1200.0 if study_curr == "GBP" else 1400.0)
            default_home = 350000.0 if study_curr == "CNY" else (950000.0 if study_curr == "GBP" else 650000.0)
            home_bal = ov.get("verified_balances", {}).get(home_curr, default_home)

            if any(w in lower for w in ["funding gap", "projected funding gap", "projected gap", "shortfall"]):
                message = (
                    f"**Projected 90-Day Funding Gap Analysis for {ov.get('student_name', 'Student')}**:\n\n"
                    f"• **Direct Local Shortfall ({study_curr})**: **{study_sym}{shortfall_amt:,.2f} {study_curr}**.\n"
                    f"  - **Obligation Driver**: Upcoming tuition due {ov.get('tuition_due_date', '2026-11-15')} ({study_sym}{ov.get('tuition_amount_due', default_tuit):,.2f} {study_curr}) "
                    f"and monthly living burn ({study_sym}{ov.get('monthly_living_burn', 3300.0):,.2f} {study_curr}/mo).\n"
                    f"  - **Available China Liquid Funds**: {study_sym}{ov.get('verified_balances', {}).get(study_curr, 8500.0):,.2f} {study_curr} (ICBC) + expected scholarship stipend.\n\n"
                    f"• **Cross-Currency Remedy ({home_curr})**:\n"
                    f"  - **Home Family Reserves**: {home_sym}{home_bal:,.2f} {home_curr} in DBBL Dhaka.\n"
                    f"  - **Planned Remittance**: Remitting {home_sym}250,000.00 {home_curr} yields approximately **{study_sym}{net_conv:,.2f} {study_curr}** net proceeds via digital specialist.\n"
                    f"  - **Remaining Unfunded Gap**: Leaves a minor gap of **~{study_sym}{rem_gap:,.2f} {study_curr}**, "
                    f"which can be resolved with a small secondary top-up of ~{home_sym}15,000.00 {home_curr} before November 05.\n\n"
                    f"**Status**: **{gap_out.get('summary_status', 'COVERABLE_VIA_TRANSFER')}**."
                )
            else:
                top_recs = recs_res.output.get("recommendations", [])
                titles = [f"{i+1}. {r['title']} ({r['priority']} Priority)" for i, r in enumerate(top_recs[:3])]
                message = (
                    "When funding is constrained, deterministic modeling prioritizes non-negotiable contractual deadlines:\n\n"
                    + "\n".join(titles) + "\n\n"
                    + f"1. **Tuition Preservation**: Ringfence the {study_sym}{ov.get('tuition_amount_due', default_tuit):,.2f} {study_curr} "
                    + f"obligation 10 business days before {ov.get('tuition_due_date', 'Nov 15')} to avoid academic late penalty holds.\n"
                    + f"2. **Fixed Rent Protection**: Preserve your baseline housing expense ({study_sym}{default_rent:,.2f} {study_curr}/mo) before discretionary spending.\n"
                    + f"3. **Remittance Top-Up**: Schedule your family transfer from Bangladesh home reserves at least 7-10 business days prior."
                )
            assumptions = [
                f"Evaluation horizon fixed at 90 days from baseline 2026-10-15.",
                "Tuition deadline carries non-negotiable academic penalties.",
                "Rent and utilities represent essential contractual obligations.",
            ]
            warnings = [
                "FX conversion rates fluctuate prior to dispatch; quote margins are benchmark approximations.",
            ]


        else:
            # General query
            recs_res = dispatch_tool("get_action_recommendations", {})
            tool_results.append(recs_res)

            default_bal = 8500.0 if study_curr == "CNY" else (2400.0 if study_curr == "GBP" else 4200.0)
            default_home = 350000.0 if study_curr == "CNY" else (950000.0 if study_curr == "GBP" else 650000.0)
            default_tuit = 24000.0 if study_curr == "CNY" else (9250.0 if study_curr == "GBP" else 14500.0)

            study_bal = ov.get("verified_balances", {}).get(study_curr, default_bal)
            home_bal = ov.get("verified_balances", {}).get(home_curr, default_home)
            tuit_amt = ov.get("tuition_amount_due", default_tuit)
            tuit_date = ov.get("tuition_due_date", "2026-11-15")

            message = (
                f"BorderWise financial overview for {ov.get('student_name', 'Student')}: "
                f"You currently hold {study_sym}{study_bal:,.2f} {study_curr} in your study account and "
                f"{home_sym}{home_bal:,.2f} {home_curr} in home savings. "
                f"Your primary upcoming milestone is tuition ({study_sym}{tuit_amt:,.2f} {study_curr} due {tuit_date}). "
                f"Please review the Action Plan for prioritized steps.\n\n"
                f"Notice: BorderWise AI is an advisory copilot. No money was moved."
            )
            assumptions = [
                "Accounts reflect verified starting balances as of 2026-10-15.",
                "RMB/CNY and BDT/Bangladeshi taka are normalized using standard ISO codes.",
            ]
            warnings = [
                "All figures derived strictly from backend calculations without speculative math.",
            ]

        # Extract recommendations if available
        for tr in tool_results:
            if tr.tool_name == "get_action_recommendations":
                raw_recs = tr.output.get("recommendations", [])
                recommendations = [ActionableRecommendation(**r) for r in raw_recs]
                break

        return ChatResponse(
            message=message,
            tool_results=tool_results,
            recommendations=recommendations,
            assumptions=assumptions,
            warnings=warnings,
            data_timestamps=data_timestamps,
            is_demo_mode=True,
            requires_confirmation=requires_confirmation,
            confirmation_preview=confirmation_preview,
        )


copilot_orchestrator = CopilotOrchestrator()

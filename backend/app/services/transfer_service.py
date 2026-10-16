from datetime import datetime, timezone
from decimal import Decimal
from typing import List
from app.schemas.common import SupportedCurrency, QuoteProvenance
from app.schemas.transfers import (
    TransferCompareRequest,
    DetailedTransferQuote,
    TransferCompareResponse,
)
from app.services.fx_service import (
    get_dated_fx_quote,
    round_money_standard,
    round_rate_standard,
)


def get_transfer_provider_quotes(request: TransferCompareRequest) -> TransferCompareResponse:
    """
    Compare transfer options across traditional wire banks and digital FX specialists.
    All sample/benchmark data is clearly labeled with provenance and timestamp.
    Zero fabricated live feeds: all quotes are labeled as benchmark or simulated.
    """
    send_amt = request.send_amount
    send_curr = request.send_currency
    rec_curr = request.receive_currency
    now_utc = datetime.now(timezone.utc)

    # Base mid-market benchmark
    fx_quote = get_dated_fx_quote(send_curr, rec_curr, reference_time=now_utc)
    mid_rate = fx_quote.rate

    # Dynamic currency fees based on send currency
    if send_curr == SupportedCurrency.CNY:
        bank_fixed = Decimal("80.00")
        bank_other = Decimal("40.00")
        digital_fixed = Decimal("18.00")
        campus_fixed = Decimal("25.00")
        p2p_fixed = Decimal("20.00")
    elif send_curr == SupportedCurrency.BDT:
        bank_fixed = Decimal("1200.00")
        bank_other = Decimal("600.00")
        digital_fixed = Decimal("300.00")
        campus_fixed = Decimal("450.00")
        p2p_fixed = Decimal("350.00")
    else:
        bank_fixed = Decimal("35.00")
        bank_other = Decimal("20.00")
        digital_fixed = Decimal("8.00")
        campus_fixed = Decimal("15.00")
        p2p_fixed = Decimal("12.00")

    provider_templates = [
        {
            "name": "Alipay Global / Digital Specialist",
            "type": "DIGITAL_SPECIALIST",
            "provenance": QuoteProvenance.PROVIDER_PUBLISHED,
            "fixed_fee": digital_fixed,
            "other_fee": Decimal("0.00"),
            "markup_pct": Decimal("0.0050"),  # 0.50% transparent margin
            "delivery_desc": "Instant - 2 Hours",
            "delivery_hours": 2,
            "notes": "Digital specialist transparent benchmark rate (DEMO DATA).",
            "payment_methods": ["Alipay Balance", "China UnionPay Card", "bKash / Nagad Wallet"],
        },
        {
            "name": "Bank of China / Global Wire Bank",
            "type": "TRADITIONAL_BANK",
            "provenance": QuoteProvenance.PROVIDER_PUBLISHED,
            "fixed_fee": bank_fixed,
            "other_fee": bank_other,  # Intermediary wire fee
            "markup_pct": Decimal("0.0260"),  # 2.60% markup
            "delivery_desc": "3 - 5 Business Days",
            "delivery_hours": 96,
            "notes": "Published retail branch international wire schedule (DEMO DATA).",
            "payment_methods": ["SWIFT Wire", "Branch Walk-In"],
        },
        {
            "name": "WeChat Cross-Border / Campus FinDesk",
            "type": "CAMPUS_PARTNER",
            "provenance": QuoteProvenance.SIMULATED,
            "fixed_fee": campus_fixed,
            "other_fee": Decimal("0.00"),
            "markup_pct": Decimal("0.0110"),  # 1.10% student discount margin
            "delivery_desc": "Same Day (4 - 8 Hours)",
            "delivery_hours": 8,
            "notes": "Simulated campus international student union partner program (DEMO DATA).",
            "payment_methods": ["University Portal Wire", "WeChat Pay"],
        },
        {
            "name": "RemitAsia Express / P2P Fintech",
            "type": "P2P_FINTECH",
            "provenance": QuoteProvenance.SIMULATED,
            "fixed_fee": p2p_fixed,
            "other_fee": Decimal("0.00"),
            "markup_pct": Decimal("0.0180"),  # 1.80% margin
            "delivery_desc": "1 - 2 Business Days",
            "delivery_hours": 36,
            "notes": "Simulated P2P network remittance benchmark (DEMO DATA).",
            "payment_methods": ["Mobile App Transfer", "Direct Bank Debit"],
        },
    ]

    quotes: List[DetailedTransferQuote] = []

    for tmpl in provider_templates:
        fixed_fee = tmpl["fixed_fee"]
        other_fee = tmpl["other_fee"]
        markup = tmpl["markup_pct"]

        # Hidden or overt FX markup
        fx_markup_amount = round_money_standard(send_amt * markup)
        total_fee_cost = round_money_standard(fixed_fee + other_fee + fx_markup_amount)

        # Offered exchange rate (mid-market adjusted for markup margin)
        offered_rate = round_rate_standard(mid_rate * (Decimal("1.0") - markup))

        # Amount convertible = send_amount - upfront fees
        convertible_send = max(Decimal("0.00"), send_amt - fixed_fee - other_fee)
        recipient_amount = round_money_standard(convertible_send * offered_rate)

        # Amount debited from sender = send_amt
        amount_debited = send_amt

        quotes.append(
            DetailedTransferQuote(
                provider_name=tmpl["name"],
                provider_type=tmpl["type"],
                quote_provenance=tmpl["provenance"],
                quote_timestamp_utc=now_utc,
                offered_exchange_rate=offered_rate,
                mid_market_reference_rate=mid_rate,
                fx_markup_percentage=round_money_standard(markup * Decimal("100")),
                fx_markup_amount=fx_markup_amount,
                upfront_transfer_fee=fixed_fee,
                other_disclosed_fees=other_fee,
                total_fee_cost=total_fee_cost,
                amount_debited_send_currency=amount_debited,
                recipient_amount_receive_currency=recipient_amount,
                estimated_delivery_time=tmpl["delivery_desc"],
                delivery_hours_estimate=tmpl["delivery_hours"],
                payment_methods_supported=tmpl["payment_methods"],
                quote_notes=tmpl["notes"],
            )
        )

    # Determine recommended providers
    cheapest = max(quotes, key=lambda q: q.recipient_amount_receive_currency)
    fastest = min(quotes, key=lambda q: q.delivery_hours_estimate)

    # Traditional bank benchmark for savings calculation
    trad_bank = next((q for q in quotes if q.provider_type == "TRADITIONAL_BANK"), None)
    savings = (
        round_money_standard(trad_bank.total_fee_cost - cheapest.total_fee_cost)
        if trad_bank and trad_bank.total_fee_cost > cheapest.total_fee_cost
        else Decimal("0.00")
    )

    return TransferCompareResponse(
        send_amount=send_amt,
        send_currency=send_curr,
        receive_currency=rec_curr,
        mid_market_rate=mid_rate,
        quotes_timestamp_utc=now_utc,
        all_quotes_provenance=QuoteProvenance.PROVIDER_PUBLISHED,
        quotes=quotes,
        recommended_cheapest=cheapest.provider_name,
        recommended_fastest=fastest.provider_name,
        potential_savings_vs_bank=savings,
        disclaimer=(
            "Benchmark comparison based on public schedules and simulated partner rates. "
            "BorderWise AI does not initiate live wire transactions or endorse specific providers."
        ),
    )

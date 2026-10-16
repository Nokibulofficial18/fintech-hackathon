from decimal import Decimal, ROUND_HALF_UP
from typing import Dict
from app.schemas.financial import ProviderQuote, TransferCostResponse
from app.schemas.common import SupportedCurrency

# Synthetic baseline mid-market rates for competition demonstration
# Expressed as: 1 unit of base currency = X units of quote currency
SYNTHETIC_RATES: Dict[str, Dict[str, Decimal]] = {
    "CNY": {
        "BDT": Decimal("16.8500"),
        "USD": Decimal("0.1380"),
        "EUR": Decimal("0.1280"),
    },
    "BDT": {
        "CNY": Decimal("0.0593"),
        "USD": Decimal("0.0082"),
    },
    "INR": {
        "USD": Decimal("0.0120"),
        "CAD": Decimal("0.0163"),
        "GBP": Decimal("0.0094"),
        "EUR": Decimal("0.0111"),
        "AUD": Decimal("0.0182"),
    },
    "USD": {
        "INR": Decimal("83.3333"),
        "CNY": Decimal("7.2464"),
        "BDT": Decimal("121.9512"),
        "CAD": Decimal("1.3580"),
        "GBP": Decimal("0.7830"),
        "EUR": Decimal("0.9250"),
        "AUD": Decimal("1.5160"),
    },
    "GBP": {
        "INR": Decimal("106.40"),
        "USD": Decimal("1.2770"),
        "EUR": Decimal("1.1810"),
    },
    "CAD": {
        "INR": Decimal("61.35"),
        "USD": Decimal("0.7360"),
    },
}


def round_money(value: Decimal) -> Decimal:
    """Quantize to 2 decimal places using standard financial half-up rounding."""
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def round_rate(value: Decimal) -> Decimal:
    """Quantize exchange rate to 4 decimal places."""
    return value.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


def get_mid_market_rate(send_currency: str, receive_currency: str) -> Decimal:
    """Retrieve synthetic mid-market FX rate between two currencies."""
    if send_currency == receive_currency:
        return Decimal("1.0000")
    
    if send_currency in SYNTHETIC_RATES and receive_currency in SYNTHETIC_RATES[send_currency]:
        return SYNTHETIC_RATES[send_currency][receive_currency]
    
    # Reciprocal lookup
    if receive_currency in SYNTHETIC_RATES and send_currency in SYNTHETIC_RATES[receive_currency]:
        inv_rate = SYNTHETIC_RATES[receive_currency][send_currency]
        return round_rate(Decimal("1.0") / inv_rate)
    
    # Sensible fallback for unlisted synthetic pairs
    return Decimal("1.0000")


def compare_transfer_providers(
    send_amount: Decimal,
    send_currency: SupportedCurrency,
    receive_currency: SupportedCurrency,
) -> TransferCostResponse:
    """
    Compare transfer options across traditional wire banks and modern digital FX providers.
    All calculations are done with high-precision Decimal.
    """
    mid_rate = get_mid_market_rate(send_currency.value, receive_currency.value)

    # Provider profiles (Fixed upfront fee in send currency, FX markup margin)
    def _get_upfront(bank_cny: str, bank_bdt: str, bank_default: str) -> Decimal:
        if send_currency == SupportedCurrency.CNY:
            return Decimal(bank_cny)
        elif send_currency == SupportedCurrency.BDT:
            return Decimal(bank_bdt)
        elif send_currency == SupportedCurrency.INR:
            return Decimal("1500.00") if bank_cny == "80.00" else (Decimal("450.00") if bank_cny == "18.00" else Decimal("750.00"))
        return Decimal(bank_default)

    provider_configs = [
        {
            "name": "Global Wire Bank (Traditional)",
            "is_traditional": True,
            "upfront_fee": _get_upfront("80.00", "1200.00", "35.00"),
            "markup_percent": Decimal("0.0280"),  # 2.8% hidden markup
        },
        {
            "name": "Alipay / Digital FX Specialist",
            "is_traditional": False,
            "upfront_fee": _get_upfront("18.00", "300.00", "12.00"),
            "markup_percent": Decimal("0.0050"),  # 0.5% transparent markup
        },
        {
            "name": "WeChat / Campus FinDesk",
            "is_traditional": False,
            "upfront_fee": _get_upfront("25.00", "450.00", "20.00"),
            "markup_percent": Decimal("0.0110"),  # 1.1% student discount markup
        },
    ]

    quotes: list[ProviderQuote] = []

    for cfg in provider_configs:
        upfront_fee = cfg["upfront_fee"]
        markup_pct = cfg["markup_percent"]

        # Hidden markup in send currency
        fx_markup_amount = round_money(send_amount * markup_pct)
        total_cost = round_money(upfront_fee + fx_markup_amount)

        # Offered rate after subtracting provider margin
        offered_rate = round_rate(mid_rate * (Decimal("1.0") - markup_pct))

        # Effective amount converted into destination currency
        # Amount converted = send_amount - upfront_fee
        convertible_amount = max(Decimal("0.00"), send_amount - upfront_fee)
        amount_received = round_money(convertible_amount * offered_rate)

        quotes.append(
            ProviderQuote(
                provider_name=cfg["name"],
                is_traditional_bank=cfg["is_traditional"],
                upfront_fee=upfront_fee,
                exchange_rate=offered_rate,
                fx_markup_percentage=round_money(markup_pct * Decimal("100")),
                fx_markup_amount=fx_markup_amount,
                total_cost=total_cost,
                amount_received=amount_received,
            )
        )

    # Identify best option (highest received amount)
    best_quote = max(quotes, key=lambda q: q.amount_received)
    worst_quote = min(quotes, key=lambda q: q.amount_received)
    potential_savings = round_money(worst_quote.total_cost - best_quote.total_cost)

    return TransferCostResponse(
        send_amount=send_amount,
        send_currency=send_currency,
        receive_currency=receive_currency,
        mid_market_rate=mid_rate,
        quotes=quotes,
        recommended_provider=best_quote.provider_name,
        potential_savings=potential_savings,
    )


def calculate_runway_months(
    available_destination_funds: Decimal,
    remaining_tuition_due: Decimal,
    monthly_living_burn: Decimal,
) -> Decimal:
    """
    Calculate financial runway in months:
    (Available Funds - Immediate Tuition) / Monthly Living Expenses.
    """
    if monthly_living_burn <= Decimal("0.00"):
        return Decimal("0.00")

    net_living_funds = available_destination_funds - remaining_tuition_due
    if net_living_funds <= Decimal("0.00"):
        return Decimal("0.00")

    runway = net_living_funds / monthly_living_burn
    return runway.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)

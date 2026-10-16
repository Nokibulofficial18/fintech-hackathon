from datetime import datetime, timezone, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Tuple
from app.schemas.common import SupportedCurrency, DatedFXQuote, QuoteProvenance


# Benchmark mid-market rates for competition demonstration (dated snapshot)
# Stored as: (base, quote) -> (rate, benchmark_timestamp_iso, source_name)
BENCHMARK_RATES: Dict[Tuple[str, str], Tuple[Decimal, str, str]] = {
    ("CNY", "BDT"): (Decimal("16.850000"), "2026-10-15T00:00:00Z", "Central Benchmark Reference (DEMO DATA)"),
    ("BDT", "CNY"): (Decimal("0.059347"), "2026-10-15T00:00:00Z", "Central Benchmark Reference (DEMO DATA)"),
    ("CNY", "USD"): (Decimal("0.138500"), "2026-10-15T00:00:00Z", "Central Benchmark Reference (DEMO DATA)"),
    ("USD", "CNY"): (Decimal("7.220217"), "2026-10-15T00:00:00Z", "Central Benchmark Reference (DEMO DATA)"),
    ("BDT", "USD"): (Decimal("0.008300"), "2026-10-15T00:00:00Z", "Central Benchmark Reference (DEMO DATA)"),
    ("USD", "BDT"): (Decimal("120.481928"), "2026-10-15T00:00:00Z", "Central Benchmark Reference (DEMO DATA)"),
    ("USD", "EUR"): (Decimal("0.925000"), "2026-10-15T00:00:00Z", "Central Benchmark Reference (DEMO DATA)"),
    ("EUR", "USD"): (Decimal("1.081081"), "2026-10-15T00:00:00Z", "Central Benchmark Reference (DEMO DATA)"),
    ("INR", "USD"): (Decimal("0.012000"), "2026-10-15T00:00:00Z", "Central Benchmark Reference (DEMO DATA)"),
    ("USD", "INR"): (Decimal("83.333333"), "2026-10-15T00:00:00Z", "Central Benchmark Reference (DEMO DATA)"),
}


def round_money_standard(value: Decimal) -> Decimal:
    """Standard half-up rounding to 2 decimal places."""
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def round_rate_standard(value: Decimal) -> Decimal:
    """Standard half-up rounding for exchange rates to 6 decimal places."""
    return value.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)


def get_dated_fx_quote(
    base_currency: SupportedCurrency,
    quote_currency: SupportedCurrency,
    reference_time: datetime | None = None,
    max_age_hours: int = 24,
    override_stale_hours: int | None = None,
) -> DatedFXQuote:
    """
    Retrieve a dated FX quote with provenance and staleness verification.
    Ensures conversions are never presented as current without an explicit verification timestamp.
    """
    now = datetime.now(timezone.utc) if reference_time is None else reference_time

    if base_currency == quote_currency:
        return DatedFXQuote(
            base_currency=base_currency,
            quote_currency=quote_currency,
            rate=Decimal("1.000000"),
            timestamp_utc=now,
            source="Parity (Same Currency)",
            provenance=QuoteProvenance.PROVIDER_PUBLISHED,
            is_stale=False,
            staleness_warning=None,
        )

    pair_key = (base_currency.value, quote_currency.value)
    
    if pair_key in BENCHMARK_RATES:
        rate_val, ts_iso, source_name = BENCHMARK_RATES[pair_key]
        quote_ts = datetime.fromisoformat(ts_iso.replace("Z", "+00:00"))
    else:
        # Check reciprocal
        reciprocal_key = (quote_currency.value, base_currency.value)
        if reciprocal_key in BENCHMARK_RATES:
            inv_rate, ts_iso, source_name = BENCHMARK_RATES[reciprocal_key]
            quote_ts = datetime.fromisoformat(ts_iso.replace("Z", "+00:00"))
            rate_val = round_rate_standard(Decimal("1.0") / inv_rate)
        else:
            # Fallback placeholder
            rate_val = Decimal("1.000000")
            quote_ts = now - timedelta(days=2)
            source_name = "Unverified Fallback Estimate"

    # Simulate artificial aging if override_stale_hours is requested
    if override_stale_hours is not None:
        quote_ts = now - timedelta(hours=override_stale_hours)

    age_delta = now - quote_ts
    age_hours = age_delta.total_seconds() / 3600.0
    is_stale = age_hours > max_age_hours

    staleness_warning = None
    if is_stale:
        staleness_warning = (
            f"Quote timestamp ({quote_ts.strftime('%Y-%m-%d %H:%M UTC')}) is {age_hours:.1f} hours old, "
            f"which exceeds the {max_age_hours}-hour freshness threshold. "
            f"Do not treat as current market execution rate."
        )

    return DatedFXQuote(
        base_currency=base_currency,
        quote_currency=quote_currency,
        rate=rate_val,
        timestamp_utc=quote_ts,
        source=source_name,
        provenance=QuoteProvenance.SIMULATED,
        is_stale=is_stale,
        staleness_warning=staleness_warning,
    )

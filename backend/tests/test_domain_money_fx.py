from datetime import datetime, timezone, timedelta
from decimal import Decimal
import pytest
from app.schemas.common import SupportedCurrency, QuoteProvenance, DatedFXQuote
from app.services.fx_service import (
    get_dated_fx_quote,
    round_money_standard,
    round_rate_standard,
)


def test_money_arithmetic_precision():
    """Verify that monetary rounding conforms strictly to standard half-up 2-decimal precision."""
    val1 = Decimal("100.005")
    val2 = Decimal("100.004")
    val3 = Decimal("0.000000001")
    
    assert round_money_standard(val1) == Decimal("100.01")
    assert round_money_standard(val2) == Decimal("100.00")
    assert round_money_standard(val3) == Decimal("0.00")


def test_currency_rate_precision():
    """Verify rate rounding supports 6 decimal places."""
    rate = Decimal("16.85000049")
    assert round_rate_standard(rate) == Decimal("16.850000")


def test_same_currency_parity():
    """Verify exchanging currency for itself yields 1.0 with no markup or delay."""
    quote = get_dated_fx_quote(SupportedCurrency.CNY, SupportedCurrency.CNY)
    assert quote.rate == Decimal("1.000000")
    assert quote.is_stale is False
    assert quote.staleness_warning is None


def test_cny_bdt_benchmark_rates():
    """Verify dated benchmark quotes for CNY -> BDT and reciprocal BDT -> CNY."""
    cny_bdt = get_dated_fx_quote(SupportedCurrency.CNY, SupportedCurrency.BDT, max_age_hours=999999)
    assert cny_bdt.rate == Decimal("16.850000")
    assert cny_bdt.base_currency == SupportedCurrency.CNY
    assert cny_bdt.quote_currency == SupportedCurrency.BDT
    assert "DEMO DATA" in cny_bdt.source

    bdt_cny = get_dated_fx_quote(SupportedCurrency.BDT, SupportedCurrency.CNY, max_age_hours=999999)
    assert bdt_cny.rate == Decimal("0.059347")
    assert bdt_cny.base_currency == SupportedCurrency.BDT
    assert bdt_cny.quote_currency == SupportedCurrency.CNY


def test_stale_rate_detection():
    """Verify that quotes older than threshold are flagged as stale with an explicit warning."""
    # Force artificial age of 30 hours (> 24 hour threshold)
    stale_quote = get_dated_fx_quote(
        SupportedCurrency.CNY,
        SupportedCurrency.BDT,
        max_age_hours=24,
        override_stale_hours=30,
    )
    assert stale_quote.is_stale is True
    assert stale_quote.staleness_warning is not None
    assert "exceeds the 24-hour freshness threshold" in stale_quote.staleness_warning
    assert stale_quote.provenance == QuoteProvenance.SIMULATED


def test_fresh_rate_has_no_warning():
    """Verify that a recently recorded quote has is_stale=False."""
    fresh_override = get_dated_fx_quote(
        SupportedCurrency.CNY,
        SupportedCurrency.BDT,
        max_age_hours=999999,
    )
    assert fresh_override.is_stale is False
    assert fresh_override.staleness_warning is None

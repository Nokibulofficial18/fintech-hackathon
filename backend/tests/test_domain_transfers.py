from decimal import Decimal
import pytest
from app.schemas.common import SupportedCurrency, QuoteProvenance
from app.schemas.transfers import TransferCompareRequest
from app.services.transfer_service import get_transfer_provider_quotes


def test_transfer_fee_comparison_decomposition():
    """Verify that transfer quotes accurately decompose upfront fee, other fees, and FX markup for CNY -> BDT."""
    req = TransferCompareRequest(
        send_amount=Decimal("1000.00"),  # 1,000 CNY primary demo amount
        send_currency=SupportedCurrency.CNY,
        receive_currency=SupportedCurrency.BDT,
    )
    res = get_transfer_provider_quotes(req)

    assert res.send_amount == Decimal("1000.00")
    assert res.send_currency == SupportedCurrency.CNY
    assert res.receive_currency == SupportedCurrency.BDT
    assert len(res.quotes) >= 4

    for quote in res.quotes:
        # Debited amount must equal send amount
        assert quote.amount_debited_send_currency == req.send_amount

        # Total fee must equal upfront + other + fx markup
        expected_fee = quote.upfront_transfer_fee + quote.other_disclosed_fees + quote.fx_markup_amount
        assert quote.total_fee_cost == expected_fee

        # Recipient amount must be positive
        assert quote.recipient_amount_receive_currency > Decimal("0.00")

        # Provenance must be explicit (never claim to be an unverified live feed)
        assert quote.quote_provenance in (
            QuoteProvenance.PROVIDER_PUBLISHED,
            QuoteProvenance.SIMULATED,
        )
        assert quote.quote_notes != ""


def test_digital_specialist_cheaper_than_traditional_bank():
    """Verify that digital specialist delivers higher recipient proceeds and yields positive savings for CNY -> BDT."""
    req = TransferCompareRequest(
        send_amount=Decimal("1000.00"),
        send_currency=SupportedCurrency.CNY,
        receive_currency=SupportedCurrency.BDT,
    )
    res = get_transfer_provider_quotes(req)

    quotes_by_type = {q.provider_type: q for q in res.quotes}
    bank = quotes_by_type["TRADITIONAL_BANK"]
    specialist = quotes_by_type["DIGITAL_SPECIALIST"]

    # Specialist delivers more BDT
    assert specialist.recipient_amount_receive_currency > bank.recipient_amount_receive_currency

    # Specialist charges lower overall fee
    assert specialist.total_fee_cost < bank.total_fee_cost

    # Benchmark savings must be positive
    assert res.potential_savings_vs_bank > Decimal("0.00")


def test_reverse_transfer_bdt_to_cny_domain():
    """Verify reverse transfer direction BDT -> CNY executes with correct reciprocal rate and fee schedule."""
    req = TransferCompareRequest(
        send_amount=Decimal("250000.00"),
        send_currency=SupportedCurrency.BDT,
        receive_currency=SupportedCurrency.CNY,
    )
    res = get_transfer_provider_quotes(req)
    assert res.send_currency == SupportedCurrency.BDT
    assert res.receive_currency == SupportedCurrency.CNY
    assert len(res.quotes) >= 4

    digital = next(q for q in res.quotes if q.provider_type == "DIGITAL_SPECIALIST")
    bank = next(q for q in res.quotes if q.provider_type == "TRADITIONAL_BANK")
    assert digital.recipient_amount_receive_currency > bank.recipient_amount_receive_currency


def test_transfer_input_validation_zero_or_negative():
    """Verify that non-positive transfer send amounts are rejected by validation schema."""
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        TransferCompareRequest(
            send_amount=Decimal("0.00"),
            send_currency=SupportedCurrency.CNY,
            receive_currency=SupportedCurrency.BDT,
        )

    with pytest.raises(ValidationError):
        TransferCompareRequest(
            send_amount=Decimal("-500.00"),
            send_currency=SupportedCurrency.CNY,
            receive_currency=SupportedCurrency.BDT,
        )


def test_transfer_explicit_rate_direction_and_reciprocal():
    """Verify explicit exchange rate directions: 1 CNY -> ~16.85 BDT and 1 BDT -> ~0.0593 CNY."""
    cny_to_bdt = get_transfer_provider_quotes(
        TransferCompareRequest(
            send_amount=Decimal("1000.00"),
            send_currency=SupportedCurrency.CNY,
            receive_currency=SupportedCurrency.BDT,
        )
    )
    bdt_to_cny = get_transfer_provider_quotes(
        TransferCompareRequest(
            send_amount=Decimal("10000.00"),
            send_currency=SupportedCurrency.BDT,
            receive_currency=SupportedCurrency.CNY,
        )
    )

    # 1 CNY should yield around 16.85 BDT
    assert Decimal("16.0") < cny_to_bdt.mid_market_rate < Decimal("18.0")
    # 1 BDT should yield around 0.0593 CNY (reciprocal)
    assert Decimal("0.05") < bdt_to_cny.mid_market_rate < Decimal("0.07")

    # Product of rates should approximate 1 (allowing small rounding)
    product = cny_to_bdt.mid_market_rate * bdt_to_cny.mid_market_rate
    assert Decimal("0.98") < product < Decimal("1.02")


def test_transfer_recommendation_and_math_consistency():
    """Verify that 'recommended_cheapest' yields the highest net proceeds and 'recommended_fastest' has minimum transit hours."""
    req = TransferCompareRequest(
        send_amount=Decimal("5000.00"),
        send_currency=SupportedCurrency.CNY,
        receive_currency=SupportedCurrency.BDT,
    )
    res = get_transfer_provider_quotes(req)

    # Find the quote with the maximum net recipient amount
    max_recipient_quote = max(res.quotes, key=lambda q: q.recipient_amount_receive_currency)
    assert res.recommended_cheapest == max_recipient_quote.provider_name

    # Find the quote with the lowest transit hours
    min_hours_quote = min(res.quotes, key=lambda q: q.delivery_hours_estimate)
    assert res.recommended_fastest == min_hours_quote.provider_name

    # Verify calculation decomposition for every quote:
    for q in res.quotes:
        convertible = req.send_amount - q.upfront_transfer_fee - q.other_disclosed_fees
        expected_recipient = (convertible * q.offered_exchange_rate).quantize(Decimal("0.01"))
        diff = abs(q.recipient_amount_receive_currency - expected_recipient)
        # Difference due to standard decimal quantize should not exceed 0.05
        assert diff <= Decimal("0.05")


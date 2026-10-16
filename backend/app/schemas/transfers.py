from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field
from app.schemas.common import SupportedCurrency, QuoteProvenance


class TransferCompareRequest(BaseModel):
    """Parameters for comparing transfer provider quotes."""
    send_amount: Decimal = Field(..., gt=0, description="Amount to transfer in send currency")
    send_currency: SupportedCurrency = Field(default=SupportedCurrency.CNY)
    receive_currency: SupportedCurrency = Field(default=SupportedCurrency.BDT)
    speed_preference: Optional[str] = Field(
        default=None,
        description="Filter or prioritize: 'FASTEST', 'CHEAPEST', or 'BALANCED'",
    )


class DetailedTransferQuote(BaseModel):
    """Rigorous breakdown of a transfer provider quote."""
    provider_name: str
    provider_type: str = Field(..., description="TRADITIONAL_BANK, DIGITAL_SPECIALIST, CAMPUS_PARTNER, P2P_FINTECH")
    quote_provenance: QuoteProvenance = Field(
        ...,
        description="SIMULATED, PROVIDER_PUBLISHED, or LIVE_API. Distinguishes benchmark data from live feeds.",
    )
    quote_timestamp_utc: datetime = Field(..., description="Timestamp when the benchmark quote was captured")

    # Rates
    offered_exchange_rate: Decimal = Field(..., description="Exchange rate applied to the transfer")
    mid_market_reference_rate: Decimal = Field(..., description="Interbank mid-market rate benchmark")
    fx_markup_percentage: Decimal = Field(..., description="Hidden or stated currency margin in percent")
    fx_markup_amount: Decimal = Field(..., description="Value of margin retained in send currency")

    # Fees
    upfront_transfer_fee: Decimal = Field(..., description="Fixed wire or network fee charged to sender")
    other_disclosed_fees: Decimal = Field(
        default=Decimal("0.00"),
        description="Additional disclosed fees (e.g. intermediary correspondent bank charges)",
    )
    total_fee_cost: Decimal = Field(
        ...,
        description="upfront_transfer_fee + other_disclosed_fees + fx_markup_amount in send currency",
    )

    # Net figures
    amount_debited_send_currency: Decimal = Field(..., description="Total cash deducted from sender account")
    recipient_amount_receive_currency: Decimal = Field(..., description="Net funds credited to recipient account")

    # Delivery & SLA
    estimated_delivery_time: str = Field(..., description="e.g. 'Instant - 4 hours', '1-2 business days'")
    delivery_hours_estimate: int = Field(..., ge=1, description="Estimated transit hours for ranking")
    payment_methods_supported: List[str] = Field(default_factory=lambda: ["Bank Debit / ACH", "Wire"])

    # Disclaimers & Notes
    quote_notes: str = Field(..., description="Explicit disclaimer of rate validity or benchmark status")


class TransferCompareResponse(BaseModel):
    """Comprehensive comparison of transfer options."""
    send_amount: Decimal
    send_currency: SupportedCurrency
    receive_currency: SupportedCurrency
    mid_market_rate: Decimal
    quotes_timestamp_utc: datetime
    all_quotes_provenance: QuoteProvenance

    quotes: List[DetailedTransferQuote]

    recommended_cheapest: str
    recommended_fastest: str
    potential_savings_vs_bank: Decimal = Field(
        ...,
        description="Savings in send currency when choosing best digital provider over traditional bank",
    )

    disclaimer: str = Field(
        default="Sample benchmark demonstration. BorderWise does not initiate live money transfers.",
    )

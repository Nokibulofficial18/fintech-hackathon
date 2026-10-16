from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from pydantic import BaseModel, Field


class SupportedCurrency(str, Enum):
    """Supported ISO-4217 Currency Codes."""
    CNY = "CNY"  # Chinese Yuan (RMB / ¥)
    BDT = "BDT"  # Bangladeshi Taka (৳)
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    INR = "INR"
    CAD = "CAD"
    SGD = "SGD"
    AUD = "AUD"


class QuoteProvenance(str, Enum):
    """Clear labeling of rate and quote origins."""
    SIMULATED = "SIMULATED"
    PROVIDER_PUBLISHED = "PROVIDER_PUBLISHED"
    LIVE_API = "LIVE_API"


class MoneyAmount(BaseModel):
    """Standardized representation of monetary amounts with explicit currency."""
    amount: Decimal = Field(..., ge=0, description="Non-negative monetary value")
    currency: SupportedCurrency = Field(..., description="ISO-4217 Currency Code")


class DatedFXQuote(BaseModel):
    """
    Dated foreign exchange quote with full provenance and staleness indicators.
    Enforces that conversion rates are never assumed to be live or unverified.
    """
    base_currency: SupportedCurrency = Field(..., description="Currency being exchanged from")
    quote_currency: SupportedCurrency = Field(..., description="Currency being received")
    rate: Decimal = Field(..., gt=0, description="Exchange rate (1 base = rate quote)")
    timestamp_utc: datetime = Field(..., description="UTC timestamp when the quote was recorded")
    source: str = Field(..., description="Origin of the rate (e.g. Synthetic Central Benchmark)")
    provenance: QuoteProvenance = Field(
        default=QuoteProvenance.SIMULATED,
        description="Explicit provenance: SIMULATED, PROVIDER_PUBLISHED, or LIVE_API",
    )
    is_stale: bool = Field(
        default=False,
        description="True if the quote exceeds maximum freshness window (>24 hours)",
    )
    staleness_warning: str | None = Field(
        default=None,
        description="Explanation if quote is stale or unverified",
    )

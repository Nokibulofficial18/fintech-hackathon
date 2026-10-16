from datetime import date
from decimal import Decimal
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from app.schemas.common import SupportedCurrency, DatedFXQuote
from app.schemas.profile import FullStudentScenario


class FundingGapRequest(BaseModel):
    """Parameters for funding-gap analysis."""
    scenario: Optional[FullStudentScenario] = Field(
        default=None,
        description="Optional custom student scenario. If omitted, uses seeded demo scenario.",
    )
    horizon_days: int = Field(
        default=90,
        ge=1,
        le=365,
        description="Horizon for upcoming obligations (e.g. 30, 60, or 90 days).",
    )
    stale_quote_threshold_hours: int = Field(
        default=24,
        ge=1,
        description="Maximum permissible age of an FX quote before flagging as stale.",
    )
    custom_fx_quote: Optional[DatedFXQuote] = Field(
        default=None,
        description="Optional custom FX quote for simulation.",
    )


class CurrencyObligationItem(BaseModel):
    """Specific obligation contributing to funding needs."""
    title: str
    category: str  # TUITION, RENT, LIVING, REMITTANCE
    due_date: date
    currency: SupportedCurrency
    amount: Decimal
    is_mandatory: bool = True


class SingleCurrencyPosition(BaseModel):
    """Standalone financial position for a single currency without cross-currency mixing."""
    currency: SupportedCurrency
    actual_liquid_balance: Decimal
    expected_inflows: Decimal
    total_available_resources: Decimal
    total_obligations: Decimal
    net_position: Decimal = Field(..., description="total_available_resources - total_obligations")
    has_direct_gap: bool = Field(..., description="True if net_position < 0 in this specific currency")
    direct_gap_amount: Decimal = Field(..., ge=0, description="Amount needed strictly in this currency")


class CrossCurrencyConversionOption(BaseModel):
    """
    Transparent analysis of whether surplus in another currency can cover a deficit.
    Never silently combined: explicit FX rate, fee, and staleness metadata are provided.
    """
    source_currency: SupportedCurrency
    target_currency: SupportedCurrency
    available_surplus_in_source: Decimal
    dated_fx_quote: DatedFXQuote
    estimated_provider_fee: Decimal
    net_convertible_in_target: Decimal
    can_cover_full_gap: bool
    remaining_gap_after_conversion: Decimal
    conversion_caveats: List[str]


class FundingGapResponse(BaseModel):
    """Rigorous funding-gap audit reporting distinct currencies and dated conversions."""
    analysis_date: date
    horizon_days: int
    study_currency: SupportedCurrency
    home_currency: SupportedCurrency

    # Distinct currency positions (NEVER silently merged)
    currency_positions: Dict[str, SingleCurrencyPosition]

    # Specific obligations analyzed
    obligations: List[CurrencyObligationItem]

    # Target currency direct gap status
    target_currency_has_shortfall: bool
    target_currency_shortfall_amount: Decimal

    # Cross-currency potential conversion evaluation (if surplus exists in home currency)
    cross_currency_remedy: Optional[CrossCurrencyConversionOption] = None

    # Stale rate warnings
    has_stale_rate_warning: bool
    rate_warnings: List[str]

    # Summary diagnostic narrative
    summary_status: str = Field(..., description="CRITICAL_DEFICIT, COVERABLE_VIA_TRANSFER, or FULLY_FUNDED")
    audit_notes: List[str]

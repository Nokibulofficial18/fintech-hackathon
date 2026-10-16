from decimal import Decimal
from pydantic import BaseModel, Field
from app.schemas.common import SupportedCurrency


class TransferCostRequest(BaseModel):
    """Input payload for cross-border transfer cost analysis."""
    send_amount: Decimal = Field(..., gt=0, description="Amount to send in home currency")
    send_currency: SupportedCurrency = Field(default=SupportedCurrency.CNY)
    receive_currency: SupportedCurrency = Field(default=SupportedCurrency.BDT)


class ProviderQuote(BaseModel):
    """Breakdown of transfer fees and rates for a specific provider."""
    provider_name: str
    is_traditional_bank: bool
    upfront_fee: Decimal = Field(..., description="Fixed wire or transaction fee in send currency")
    exchange_rate: Decimal = Field(..., description="Offered exchange rate")
    fx_markup_percentage: Decimal = Field(..., description="Percentage markup applied by provider")
    fx_markup_amount: Decimal = Field(..., description="Hidden FX margin in send currency")
    total_cost: Decimal = Field(..., description="Upfront fee + FX markup in send currency")
    amount_received: Decimal = Field(..., description="Estimated received amount in destination currency")


class TransferCostResponse(BaseModel):
    """Comparison of transfer options."""
    send_amount: Decimal
    send_currency: SupportedCurrency
    receive_currency: SupportedCurrency
    mid_market_rate: Decimal
    quotes: list[ProviderQuote]
    recommended_provider: str
    potential_savings: Decimal

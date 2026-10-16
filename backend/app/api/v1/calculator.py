from fastapi import APIRouter
from app.schemas.financial import TransferCostRequest, TransferCostResponse
from app.services.financial_calc import compare_transfer_providers

router = APIRouter(prefix="/calculator", tags=["Financial Calculator"])


@router.post("/compare-transfers", response_model=TransferCostResponse)
def compare_transfers(request: TransferCostRequest) -> TransferCostResponse:
    """
    Compare transfer options between traditional wire banks and fintech FX providers.
    Uses precise Decimal calculations to expose hidden FX markups and fees.
    """
    return compare_transfer_providers(
        send_amount=request.send_amount,
        send_currency=request.send_currency,
        receive_currency=request.receive_currency,
    )

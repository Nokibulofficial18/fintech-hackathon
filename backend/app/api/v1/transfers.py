from fastapi import APIRouter
from app.schemas.transfers import TransferCompareRequest, TransferCompareResponse
from app.services.transfer_service import get_transfer_provider_quotes

router = APIRouter(prefix="/transfers", tags=["Cross-Border Transfers"])


@router.post("/compare", response_model=TransferCompareResponse)
def compare_transfers(request: TransferCompareRequest) -> TransferCompareResponse:
    """
    Compare configurable cross-border transfer options using clearly labeled benchmark data.
    Provides exchange rate, upfront fee, correspondent bank fees, FX markup, debited/received amounts,
    estimated delivery times, and quote provenance.
    """
    return get_transfer_provider_quotes(request)

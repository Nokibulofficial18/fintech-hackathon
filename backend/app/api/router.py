from fastapi import APIRouter
from app.api.v1.health import router as health_router
from app.api.v1.demo import router as demo_router
from app.api.v1.finance import router as finance_router
from app.api.v1.transfers import router as transfers_router
from app.api.v1.recommendations import router as recommendations_router
from app.api.v1.calculator import router as calculator_router
from app.api.v1.assistant import router as assistant_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health_router)
api_router.include_router(demo_router)
api_router.include_router(finance_router)
api_router.include_router(transfers_router)
api_router.include_router(recommendations_router)
api_router.include_router(calculator_router)
api_router.include_router(assistant_router)

from typing import Optional
from fastapi import APIRouter, Query
from pydantic import BaseModel
from app.schemas.profile import FullStudentScenario
from app.services.demo_scenario_service import (
    get_seeded_demo_scenario,
    reset_active_scenario,
    get_active_scenario,
)

router = APIRouter(prefix="/demo", tags=["Demo & Scenarios"])


class ResetDemoRequest(BaseModel):
    scenario: Optional[str] = "china"  # "china" or "us"


class ResetDemoResponse(BaseModel):
    status: str = "success"
    message: str
    scenario: FullStudentScenario


@router.get("/scenario", response_model=FullStudentScenario)
def get_demo_scenario(scenario: Optional[str] = Query(default=None, description="Select 'china' or 'us'")) -> FullStudentScenario:
    """
    Retrieve the synthetic international student scenario for demo and testing.
    Defaults to signature China-Bangladesh student scenario (Tanvir Hasan: Tsinghua University, CNY/BDT).
    """
    if scenario is not None:
        reset_active_scenario(scenario)
    return get_active_scenario()


@router.post("/reset", response_model=ResetDemoResponse)
@router.post("/scenario/reset", response_model=ResetDemoResponse)
def reset_demo(req: Optional[ResetDemoRequest] = None) -> ResetDemoResponse:
    """
    Reset the active demo scenario to a pristine synthetic baseline state.
    Guarantees mathematically consistent reproducible demonstration.
    """
    key = req.scenario if req and req.scenario else "china"
    active = reset_active_scenario(key)
    if key.lower() in ("china", "bd", "cny"):
        label = "China-Bangladesh Student (Tanvir Hasan, CNY/BDT)"
    elif key.lower() == "us":
        label = "US Student (Aarav Sharma, USD/INR)"
    else:
        label = "UK Student (Priya Patel, GBP/INR)"
    return ResetDemoResponse(
        status="success",
        message=f"BorderWise synthetic demo state successfully reset to {label}.",
        scenario=active,
    )

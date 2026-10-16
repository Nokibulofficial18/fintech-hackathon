from datetime import datetime
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """System health and diagnostic status."""
    status: str = Field(..., json_schema_extra={"example": "healthy"})
    app_name: str = Field(..., json_schema_extra={"example": "BorderWise AI"})
    version: str = Field(..., json_schema_extra={"example": "0.1.0"})
    environment: str = Field(..., json_schema_extra={"example": "development"})
    timestamp_utc: datetime = Field(..., description="UTC timestamp of the health check")
    database: str = Field(..., json_schema_extra={"example": "connected"})
    ai_mode: str = Field(..., json_schema_extra={"example": "mock"})

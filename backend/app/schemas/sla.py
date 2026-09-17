from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class CaseSLAResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    case_id: int
    response_target_hours: int
    resolution_target_hours: int
    response_due_at: datetime
    resolution_due_at: datetime
    first_responded_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    response_status: str
    resolution_status: str
    is_breached: bool
    breached_at: Optional[datetime] = None
    warning_issued_at: Optional[datetime] = None
    created_at: datetime

    # Plain language & UI calculation fields
    response_remaining_text: str = ""
    resolution_remaining_text: str = ""
    response_progress_percentage: float = 0.0
    resolution_progress_percentage: float = 0.0


class RiskSignalItem(BaseModel):
    key: str
    label: str
    severity: str  # "low", "medium", "high", "critical"
    description: str


class RiskAnalysisResponse(BaseModel):
    case_id: int
    risk_score: int  # 0 to 100
    risk_tier: str  # "low", "medium", "high", "critical"
    risk_factors: List[str] = []
    signals: List[RiskSignalItem] = []
    evaluated_at: datetime

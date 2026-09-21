import json
from datetime import datetime
from typing import List, Optional, Any
from pydantic import BaseModel, ConfigDict, field_validator


class DuplicateCaseMatch(BaseModel):
    case_id: int
    case_number: str
    title: str
    similarity_score: float
    status: str
    reason: str


class AIAnalysisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    case_id: int
    suggested_category_id: Optional[int] = None
    suggested_category_name: Optional[str] = None
    suggested_category_code: Optional[str] = None
    suggested_priority: Optional[str] = None
    suggested_severity: Optional[str] = None
    confidence_score: float
    summary: Optional[str] = None
    key_details: Optional[List[str]] = None
    missing_information: Optional[List[str]] = None
    recommended_action: Optional[str] = None
    suggested_team_id: Optional[int] = None
    suggested_team_name: Optional[str] = None
    risk_insight: Optional[str] = None
    duplicate_cases: Optional[List[DuplicateCaseMatch]] = None
    created_at: datetime

    @field_validator("key_details", "missing_information", mode="before")
    @classmethod
    def parse_json_list(cls, v: Any) -> Optional[List[str]]:
        if isinstance(v, str):
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
            except Exception:
                return [v] if v.strip() else []
        return v

    @field_validator("duplicate_cases", mode="before")
    @classmethod
    def parse_duplicate_matches(cls, v: Any) -> Optional[List[Any]]:
        if isinstance(v, str):
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
            except Exception:
                return []
        return v


class AIDraftRequest(BaseModel):
    draft_type: str = "information_request"  # information_request, progress_update, resolution_message, escalation_summary
    context_notes: Optional[str] = None


class AIDraftResponse(BaseModel):
    draft_type: str
    subject: str
    body_text: str
    suggested_recipients: Optional[str] = None


class AIApplySuggestionsRequest(BaseModel):
    apply_category: bool = True
    apply_priority: bool = True
    apply_team: bool = False


class AICaseSummaryResponse(BaseModel):
    case_id: int
    case_number: str
    summary: str
    current_stage: str
    unresolved_blockers: List[str]
    last_activity: Optional[str] = None


class AIVisionAnalyzeRequest(BaseModel):
    image_base64: Optional[str] = None
    filename: Optional[str] = None
    gps_latitude: Optional[float] = None
    gps_longitude: Optional[float] = None
    landmark_hint: Optional[str] = None
    voice_note: Optional[str] = None


class AIVisionAnalyzeResponse(BaseModel):
    detected_issue: str
    category_id: Optional[int] = None
    category_code: Optional[str] = None
    category_name: Optional[str] = None
    suggested_title: str
    suggested_description: str
    suggested_priority: str
    suggested_severity: str
    confidence_score: float
    visual_tags: List[str]
    recommended_action: str
    landmark_inferred: Optional[str] = None
    image_summary: str


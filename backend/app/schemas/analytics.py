from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class TimeSeriesMetric(BaseModel):
    date: str
    new_cases: int
    resolved_cases: int


class DepartmentPerformance(BaseModel):
    department_id: int
    department_name: str
    total_cases: int
    active_cases: int
    resolved_cases: int
    sla_compliance_percent: float


class CategoryPerformance(BaseModel):
    category_id: int
    category_name: str
    total_cases: int
    active_cases: int
    resolved_cases: int


class WardPerformance(BaseModel):
    ward: str
    total_cases: int
    active_cases: int
    resolved_cases: int
    high_risk_cases: int
    top_category: Optional[str] = None
    avg_resolution_hours: Optional[float] = None


class AIOperationalInsight(BaseModel):
    id: str
    insight_type: str  # hotspot, bottleneck, recurring_pattern, anomaly
    severity: str      # critical, high, medium, low
    title: str
    description: str
    recommendation: str
    affected_ward: Optional[str] = None
    affected_category: Optional[str] = None


class ManagerAnalyticsResponse(BaseModel):
    total_cases: int
    active_cases: int
    resolved_cases: int
    reopened_cases: int
    escalated_cases: int
    resolution_rate_percent: float
    sla_compliance_percent: float
    avg_resolution_time_hours: float
    cases_by_status: Dict[str, int]
    cases_by_priority: Dict[str, int]
    cases_by_severity: Dict[str, int]
    department_metrics: List[DepartmentPerformance]
    category_metrics: List[CategoryPerformance]
    ward_metrics: List[WardPerformance]
    time_series_trends: List[TimeSeriesMetric]
    ai_operational_insights: List[AIOperationalInsight]


class OperatorWorkload(BaseModel):
    operator_id: int
    operator_name: str
    active_cases: int
    completed_cases: int
    overdue_cases: int


class TeamLeadAnalyticsResponse(BaseModel):
    team_id: Optional[int] = None
    team_name: Optional[str] = None
    department_id: Optional[int] = None
    department_name: Optional[str] = None
    total_cases: int
    active_cases: int
    at_risk_cases: int
    active_escalations: int
    unassigned_cases: int
    sla_compliance_percent: float
    avg_resolution_time_hours: float
    operator_workloads: List[OperatorWorkload]


class OperatorAnalyticsResponse(BaseModel):
    operator_id: int
    operator_name: str
    assigned_active_count: int
    high_priority_count: int
    waiting_info_count: int
    at_risk_count: int
    active_escalations_count: int
    pending_tasks_count: int
    completed_this_week_count: int


class CitizenActivitySummary(BaseModel):
    case_id: int
    case_number: str
    title: str
    action: str
    notes: Optional[str] = None
    timestamp: datetime


class CitizenAnalyticsResponse(BaseModel):
    citizen_id: int
    total_reported: int
    active_count: int
    waiting_info_count: int
    pending_confirmation_count: int
    resolved_count: int
    recent_activity: List[CitizenActivitySummary]


class WardIntelligenceResponse(BaseModel):
    ward_summaries: List[WardPerformance]
    top_hotspots: List[WardPerformance]
    total_wards_tracked: int


class AuditLogEntry(BaseModel):
    id: int
    case_id: int
    case_number: Optional[str] = None
    actor_id: Optional[int] = None
    actor_name: Optional[str] = None
    actor_role: Optional[str] = None
    action: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime


class SystemStatsResponse(BaseModel):
    total_users: int
    users_by_role: Dict[str, int]
    total_departments: int
    total_teams: int
    total_categories: int
    total_cases: int
    total_escalations: int
    total_notifications_sent: int
    database_status: str = "healthy"

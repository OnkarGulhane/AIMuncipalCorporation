import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_

from app.models.case import Case, CaseStatus, CasePriority, CaseSeverity, CaseTimeline
from app.models.organization import Department, Category, Team
from app.models.user import User, UserRole
from app.models.sla import CaseSLA, SLAStatus
from app.models.escalation import CaseEscalation, EscalationStatus
from app.models.activity import CaseTask, TaskStatus
from app.schemas.analytics import (
    TimeSeriesMetric,
    DepartmentPerformance,
    CategoryPerformance,
    WardPerformance,
    AIOperationalInsight,
    ManagerAnalyticsResponse,
    OperatorWorkload,
    TeamLeadAnalyticsResponse,
    OperatorAnalyticsResponse,
    CitizenActivitySummary,
    CitizenAnalyticsResponse,
    WardIntelligenceResponse,
)

logger = logging.getLogger(__name__)


class AnalyticsService:
    @staticmethod
    def get_manager_analytics(
        db: Session,
        department_id: Optional[int] = None,
        days: int = 30,
    ) -> ManagerAnalyticsResponse:
        """
        Computes executive operational metrics, SLA performance, ward distributions,
        time-series trends, and AI operational insights.
        """
        query = db.query(Case)
        if department_id:
            query = query.filter(Case.department_id == department_id)

        all_cases = query.all()
        total_cases = len(all_cases)

        # Status aggregations
        status_counts: Dict[str, int] = defaultdict(int)
        priority_counts: Dict[str, int] = defaultdict(int)
        severity_counts: Dict[str, int] = defaultdict(int)

        resolved_count = 0
        active_count = 0
        reopened_count = 0
        escalated_count = 0

        resolution_times_hours: List[float] = []

        closed_statuses = {CaseStatus.CLOSED.value, CaseStatus.CONFIRMED.value}
        inactive_statuses = closed_statuses | {CaseStatus.CANCELLED.value, CaseStatus.DUPLICATE.value}

        for c in all_cases:
            status_counts[c.status] += 1
            priority_counts[c.priority] += 1
            severity_counts[c.severity] += 1

            if c.status in closed_statuses:
                resolved_count += 1
                if c.closed_at and c.created_at:
                    dur_seconds = (c.closed_at - c.created_at).total_seconds()
                    resolution_times_hours.append(max(0.1, dur_seconds / 3600.0))
            elif c.status not in inactive_statuses:
                active_count += 1

            if c.status == CaseStatus.REOPENED.value:
                reopened_count += 1

            if getattr(c, "is_escalated", False):
                escalated_count += 1

        resolution_rate = round((resolved_count / total_cases * 100), 1) if total_cases > 0 else 0.0
        avg_res_time = (
            round(sum(resolution_times_hours) / len(resolution_times_hours), 1)
            if resolution_times_hours
            else 0.0
        )

        # SLA Performance
        sla_query = db.query(CaseSLA)
        if department_id:
            sla_query = sla_query.join(Case, CaseSLA.case_id == Case.id).filter(Case.department_id == department_id)
        slas = sla_query.all()
        total_slas = len(slas)
        breached_slas = sum(1 for s in slas if s.is_breached)
        sla_compliance = (
            round(((total_slas - breached_slas) / total_slas * 100), 1)
            if total_slas > 0
            else 100.0
        )

        # Department performance
        dept_metrics: List[DepartmentPerformance] = []
        departments = db.query(Department).all()
        for d in departments:
            d_cases = [c for c in all_cases if c.department_id == d.id]
            d_total = len(d_cases)
            d_res = sum(1 for c in d_cases if c.status in closed_statuses)
            d_act = sum(1 for c in d_cases if c.status not in inactive_statuses)
            d_sla_tot = sum(1 for s in slas if s.case_rel and s.case_rel.department_id == d.id)
            d_sla_brk = sum(1 for s in slas if s.case_rel and s.case_rel.department_id == d.id and s.is_breached)
            d_comp = round(((d_sla_tot - d_sla_brk) / d_sla_tot * 100), 1) if d_sla_tot > 0 else 100.0

            dept_metrics.append(
                DepartmentPerformance(
                    department_id=d.id,
                    department_name=d.name,
                    total_cases=d_total,
                    active_cases=d_act,
                    resolved_cases=d_res,
                    sla_compliance_percent=d_comp,
                )
            )

        # Category performance
        cat_metrics: List[CategoryPerformance] = []
        categories = db.query(Category).all()
        for cat in categories:
            cat_cases = [c for c in all_cases if c.category_id == cat.id]
            cat_total = len(cat_cases)
            cat_res = sum(1 for c in cat_cases if c.status in closed_statuses)
            cat_act = sum(1 for c in cat_cases if c.status not in inactive_statuses)
            if cat_total > 0:
                cat_metrics.append(
                    CategoryPerformance(
                        category_id=cat.id,
                        category_name=cat.name,
                        total_cases=cat_total,
                        active_cases=cat_act,
                        resolved_cases=cat_res,
                    )
                )

        # Ward metrics
        ward_metrics = AnalyticsService._compute_ward_performance(all_cases, closed_statuses, inactive_statuses)

        # Time series trends (past 7 days)
        now = datetime.now(timezone.utc)
        time_trends: List[TimeSeriesMetric] = []
        for i in range(6, -1, -1):
            target_date = (now - timedelta(days=i)).date()
            date_str = target_date.strftime("%Y-%m-%d")
            new_c = sum(1 for c in all_cases if c.created_at and c.created_at.date() == target_date)
            res_c = sum(1 for c in all_cases if c.closed_at and c.closed_at.date() == target_date)
            time_trends.append(TimeSeriesMetric(date=date_str, new_cases=new_c, resolved_cases=res_c))

        # AI Operational Insights
        ai_insights = AnalyticsService._generate_ai_operational_insights(
            all_cases=all_cases,
            ward_metrics=ward_metrics,
            cat_metrics=cat_metrics,
            sla_compliance=sla_compliance,
        )

        return ManagerAnalyticsResponse(
            total_cases=total_cases,
            active_cases=active_count,
            resolved_cases=resolved_count,
            reopened_cases=reopened_count,
            escalated_cases=escalated_count,
            resolution_rate_percent=resolution_rate,
            sla_compliance_percent=sla_compliance,
            avg_resolution_time_hours=avg_res_time,
            cases_by_status=dict(status_counts),
            cases_by_priority=dict(priority_counts),
            cases_by_severity=dict(severity_counts),
            department_metrics=dept_metrics,
            category_metrics=cat_metrics,
            ward_metrics=ward_metrics,
            time_series_trends=time_trends,
            ai_operational_insights=ai_insights,
        )

    @staticmethod
    def _compute_ward_performance(
        cases: List[Case], closed_statuses: set, inactive_statuses: set
    ) -> List[WardPerformance]:
        ward_groups: Dict[str, List[Case]] = defaultdict(list)
        for c in cases:
            w = c.ward or "Unspecified Ward"
            ward_groups[w].append(c)

        results = []
        for w, w_cases in ward_groups.items():
            tot = len(w_cases)
            res = sum(1 for c in w_cases if c.status in closed_statuses)
            act = sum(1 for c in w_cases if c.status not in inactive_statuses)
            hr = sum(
                1
                for c in w_cases
                if c.severity in [CaseSeverity.CRITICAL.value, CaseSeverity.MAJOR.value]
                or c.priority in [CasePriority.CRITICAL.value, CasePriority.HIGH.value]
                or getattr(c, "is_escalated", False)
            )

            # Top category
            cat_counts: Dict[str, int] = defaultdict(int)
            for c in w_cases:
                if c.category:
                    cat_counts[c.category.name] += 1
            top_cat = max(cat_counts.items(), key=lambda x: x[1])[0] if cat_counts else None

            # Average resolution hours
            res_hours = [
                (c.closed_at - c.created_at).total_seconds() / 3600.0
                for c in w_cases
                if c.closed_at and c.created_at and c.status in closed_statuses
            ]
            avg_h = round(sum(res_hours) / len(res_hours), 1) if res_hours else None

            results.append(
                WardPerformance(
                    ward=w,
                    total_cases=tot,
                    active_cases=act,
                    resolved_cases=res,
                    high_risk_cases=hr,
                    top_category=top_cat,
                    avg_resolution_hours=avg_h,
                )
            )

        # Sort by total cases descending
        results.sort(key=lambda x: x.total_cases, reverse=True)
        return results

    @staticmethod
    def _generate_ai_operational_insights(
        all_cases: List[Case],
        ward_metrics: List[WardPerformance],
        cat_metrics: List[CategoryPerformance],
        sla_compliance: float,
    ) -> List[AIOperationalInsight]:
        insights = []

        # 1. Ward Hotspot Insight
        if ward_metrics:
            top_ward = ward_metrics[0]
            if top_ward.active_cases >= 2:
                insights.append(
                    AIOperationalInsight(
                        id="INS-01",
                        insight_type="hotspot",
                        severity="high" if top_ward.high_risk_cases > 0 else "medium",
                        title=f"Grievance Cluster in {top_ward.ward}",
                        description=f"{top_ward.ward} accounts for {top_ward.total_cases} complaints with {top_ward.active_cases} currently active.",
                        recommendation=f"Deploy additional inspection squads for {top_ward.top_category or 'general civic issues'} in {top_ward.ward}.",
                        affected_ward=top_ward.ward,
                        affected_category=top_ward.top_category,
                    )
                )

        # 2. SLA Bottleneck Insight
        if sla_compliance < 90.0:
            insights.append(
                AIOperationalInsight(
                    id="INS-02",
                    insight_type="bottleneck",
                    severity="critical" if sla_compliance < 75.0 else "high",
                    title="SLA Compliance Degradation Alert",
                    description=f"Overall resolution compliance has dropped to {sla_compliance}%, indicating backlog risk.",
                    recommendation="Review unassigned queue and reallocate operators to near-breach tickets.",
                )
            )

        # 3. Category Surge Insight
        if cat_metrics:
            top_cat = max(cat_metrics, key=lambda x: x.active_cases)
            if top_cat.active_cases >= 2:
                insights.append(
                    AIOperationalInsight(
                        id="INS-03",
                        insight_type="recurring_pattern",
                        severity="medium",
                        title=f"High Volume in {top_cat.category_name}",
                        description=f"{top_cat.category_name} has {top_cat.active_cases} active open grievances awaiting resolution.",
                        recommendation=f"Prioritize materials and contractor scheduling for {top_cat.category_name}.",
                        affected_category=top_cat.category_name,
                    )
                )

        # Default fallback insight if clean system
        if not insights:
            insights.append(
                AIOperationalInsight(
                    id="INS-00",
                    insight_type="anomaly",
                    severity="low",
                    title="Operations Running Optimally",
                    description="All municipal departments and field squads are operating within healthy SLA parameters.",
                    recommendation="Maintain current inspection frequency and monitor preventive maintenance schedules.",
                )
            )

        return insights

    @staticmethod
    def get_team_lead_analytics(db: Session, user: User) -> TeamLeadAnalyticsResponse:
        """
        Computes team-level workload, operator distribution, at-risk cases, and team SLA compliance.
        """
        dept_id = user.department_id
        team_id = user.team_id

        query = db.query(Case)
        if dept_id:
            query = query.filter(Case.department_id == dept_id)
        if team_id:
            query = query.filter(Case.team_id == team_id)

        team_cases = query.all()
        closed_statuses = {CaseStatus.CLOSED.value, CaseStatus.CONFIRMED.value, CaseStatus.CANCELLED.value, CaseStatus.DUPLICATE.value}

        total_cases = len(team_cases)
        active_cases = sum(1 for c in team_cases if c.status not in closed_statuses)
        escalated_cases = sum(1 for c in team_cases if getattr(c, "is_escalated", False))
        unassigned_cases = sum(1 for c in team_cases if c.assigned_to_id is None and c.status not in closed_statuses)
        at_risk_cases = sum(
            1
            for c in team_cases
            if c.status not in closed_statuses
            and (c.severity in [CaseSeverity.CRITICAL.value, CaseSeverity.MAJOR.value] or getattr(c, "is_escalated", False))
        )

        # SLA Performance
        case_ids = [c.id for c in team_cases]
        slas = db.query(CaseSLA).filter(CaseSLA.case_id.in_(case_ids)).all() if case_ids else []
        total_slas = len(slas)
        breached_slas = sum(1 for s in slas if s.is_breached)
        sla_comp = (
            round(((total_slas - breached_slas) / total_slas * 100), 1)
            if total_slas > 0
            else 100.0
        )

        res_times = [
            (c.closed_at - c.created_at).total_seconds() / 3600.0
            for c in team_cases
            if c.closed_at and c.created_at and c.status in {CaseStatus.CLOSED.value, CaseStatus.CONFIRMED.value}
        ]
        avg_res_time = round(sum(res_times) / len(res_times), 1) if res_times else 0.0

        # Operators in team / dept
        op_query = db.query(User).filter(User.role == UserRole.OPERATOR.value)
        if dept_id:
            op_query = op_query.filter(User.department_id == dept_id)
        operators = op_query.all()

        workloads: List[OperatorWorkload] = []
        for op in operators:
            op_cases = [c for c in team_cases if c.assigned_to_id == op.id]
            op_act = sum(1 for c in op_cases if c.status not in closed_statuses)
            op_done = sum(1 for c in op_cases if c.status in {CaseStatus.CLOSED.value, CaseStatus.CONFIRMED.value})
            op_overdue = sum(1 for c in op_cases if getattr(c, "is_escalated", False) or (c.sla and c.sla.is_breached))

            workloads.append(
                OperatorWorkload(
                    operator_id=op.id,
                    operator_name=op.full_name,
                    active_cases=op_act,
                    completed_cases=op_done,
                    overdue_cases=op_overdue,
                )
            )

        dept_obj = db.query(Department).filter(Department.id == dept_id).first() if dept_id else None
        team_obj = db.query(Team).filter(Team.id == team_id).first() if team_id else None

        return TeamLeadAnalyticsResponse(
            team_id=team_id,
            team_name=team_obj.name if team_obj else None,
            department_id=dept_id,
            department_name=dept_obj.name if dept_obj else None,
            total_cases=total_cases,
            active_cases=active_cases,
            at_risk_cases=at_risk_cases,
            active_escalations=escalated_cases,
            unassigned_cases=unassigned_cases,
            sla_compliance_percent=sla_comp,
            avg_resolution_time_hours=avg_res_time,
            operator_workloads=workloads,
        )

    @staticmethod
    def get_operator_analytics(db: Session, user: User) -> OperatorAnalyticsResponse:
        """
        Computes operator personal workload, queue metrics, and pending tasks.
        """
        assigned_cases = db.query(Case).filter(Case.assigned_to_id == user.id).all()
        closed_statuses = {CaseStatus.CLOSED.value, CaseStatus.CONFIRMED.value, CaseStatus.CANCELLED.value, CaseStatus.DUPLICATE.value}

        active_cases = [c for c in assigned_cases if c.status not in closed_statuses]
        active_count = len(active_cases)

        high_priority = sum(
            1 for c in active_cases if c.priority in [CasePriority.CRITICAL.value, CasePriority.HIGH.value]
        )
        waiting_info = sum(1 for c in active_cases if c.status == CaseStatus.WAITING_INFO.value)
        at_risk = sum(
            1
            for c in active_cases
            if c.severity in [CaseSeverity.CRITICAL.value, CaseSeverity.MAJOR.value]
            or getattr(c, "is_escalated", False)
        )
        escalations = sum(1 for c in active_cases if getattr(c, "is_escalated", False))

        # Pending tasks assigned to operator
        pending_tasks = (
            db.query(CaseTask)
            .filter(CaseTask.assigned_to_id == user.id, CaseTask.status == TaskStatus.PENDING.value)
            .count()
        )

        # Completed this week
        now = datetime.now(timezone.utc)
        week_ago = now - timedelta(days=7)
        completed_week = sum(
            1
            for c in assigned_cases
            if c.status in {CaseStatus.CLOSED.value, CaseStatus.CONFIRMED.value}
            and c.closed_at
            and c.closed_at >= week_ago
        )

        return OperatorAnalyticsResponse(
            operator_id=user.id,
            operator_name=user.full_name,
            assigned_active_count=active_count,
            high_priority_count=high_priority,
            waiting_info_count=waiting_info,
            at_risk_count=at_risk,
            active_escalations_count=escalations,
            pending_tasks_count=pending_tasks,
            completed_this_week_count=completed_week,
        )

    @staticmethod
    def get_citizen_analytics(db: Session, user: User) -> CitizenAnalyticsResponse:
        """
        Computes citizen personal complaint summary and recent activity timeline.
        """
        citizen_cases = db.query(Case).filter(Case.citizen_id == user.id).all()
        closed_statuses = {CaseStatus.CLOSED.value, CaseStatus.CONFIRMED.value, CaseStatus.CANCELLED.value, CaseStatus.DUPLICATE.value}

        total = len(citizen_cases)
        active = sum(1 for c in citizen_cases if c.status not in closed_statuses)
        waiting_info = sum(1 for c in citizen_cases if c.status == CaseStatus.WAITING_INFO.value)
        pending_conf = sum(1 for c in citizen_cases if c.status == CaseStatus.RESOLUTION_PROPOSED.value)
        resolved = sum(1 for c in citizen_cases if c.status in {CaseStatus.CLOSED.value, CaseStatus.CONFIRMED.value})

        # Recent activities from timeline
        case_ids = [c.id for c in citizen_cases]
        recent_entries: List[CitizenActivitySummary] = []
        if case_ids:
            timelines = (
                db.query(CaseTimeline)
                .filter(CaseTimeline.case_id.in_(case_ids), CaseTimeline.is_internal == False)
                .order_by(CaseTimeline.created_at.desc())
                .limit(5)
                .all()
            )
            case_map = {c.id: c for c in citizen_cases}
            for t in timelines:
                c_obj = case_map.get(t.case_id)
                recent_entries.append(
                    CitizenActivitySummary(
                        case_id=t.case_id,
                        case_number=c_obj.case_number if c_obj else f"Case #{t.case_id}",
                        title=c_obj.title if c_obj else "Civic Complaint",
                        action=t.action,
                        notes=t.notes,
                        timestamp=t.created_at,
                    )
                )

        return CitizenAnalyticsResponse(
            citizen_id=user.id,
            total_reported=total,
            active_count=active,
            waiting_info_count=waiting_info,
            pending_confirmation_count=pending_conf,
            resolved_count=resolved,
            recent_activity=recent_entries,
        )

    @staticmethod
    def get_ward_intelligence(db: Session) -> WardIntelligenceResponse:
        """
        Computes ward-level geospatial and complaint clustering intelligence.
        """
        all_cases = db.query(Case).all()
        closed_statuses = {CaseStatus.CLOSED.value, CaseStatus.CONFIRMED.value}
        inactive_statuses = closed_statuses | {CaseStatus.CANCELLED.value, CaseStatus.DUPLICATE.value}

        ward_metrics = AnalyticsService._compute_ward_performance(all_cases, closed_statuses, inactive_statuses)
        top_hotspots = [w for w in ward_metrics if w.active_cases > 0][:5]

        return WardIntelligenceResponse(
            ward_summaries=ward_metrics,
            top_hotspots=top_hotspots,
            total_wards_tracked=len(ward_metrics),
        )


analytics_service = AnalyticsService()

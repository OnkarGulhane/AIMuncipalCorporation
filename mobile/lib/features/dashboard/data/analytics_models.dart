class TimeSeriesMetricModel {
  final String date;
  final int newCases;
  final int resolvedCases;

  TimeSeriesMetricModel({
    required this.date,
    required this.newCases,
    required this.resolvedCases,
  });

  factory TimeSeriesMetricModel.fromJson(Map<String, dynamic> json) {
    return TimeSeriesMetricModel(
      date: json['date'] as String,
      newCases: json['new_cases'] as int? ?? 0,
      resolvedCases: json['resolved_cases'] as int? ?? 0,
    );
  }
}

class DepartmentPerformanceModel {
  final int departmentId;
  final String departmentName;
  final int totalCases;
  final int activeCases;
  final int resolvedCases;
  final double slaCompliancePercent;

  DepartmentPerformanceModel({
    required this.departmentId,
    required this.departmentName,
    required this.totalCases,
    required this.activeCases,
    required this.resolvedCases,
    required this.slaCompliancePercent,
  });

  factory DepartmentPerformanceModel.fromJson(Map<String, dynamic> json) {
    return DepartmentPerformanceModel(
      departmentId: json['department_id'] as int,
      departmentName: json['department_name'] as String,
      totalCases: json['total_cases'] as int? ?? 0,
      activeCases: json['active_cases'] as int? ?? 0,
      resolvedCases: json['resolved_cases'] as int? ?? 0,
      slaCompliancePercent: (json['sla_compliance_percent'] as num?)?.toDouble() ?? 100.0,
    );
  }
}

class CategoryPerformanceModel {
  final int categoryId;
  final String categoryName;
  final int totalCases;
  final int activeCases;
  final int resolvedCases;

  CategoryPerformanceModel({
    required this.categoryId,
    required this.categoryName,
    required this.totalCases,
    required this.activeCases,
    required this.resolvedCases,
  });

  factory CategoryPerformanceModel.fromJson(Map<String, dynamic> json) {
    return CategoryPerformanceModel(
      categoryId: json['category_id'] as int,
      categoryName: json['category_name'] as String,
      totalCases: json['total_cases'] as int? ?? 0,
      activeCases: json['active_cases'] as int? ?? 0,
      resolvedCases: json['resolved_cases'] as int? ?? 0,
    );
  }
}

class WardPerformanceModel {
  final String ward;
  final int totalCases;
  final int activeCases;
  final int resolvedCases;
  final int highRiskCases;
  final String? topCategory;
  final double? avgResolutionHours;

  WardPerformanceModel({
    required this.ward,
    required this.totalCases,
    required this.activeCases,
    required this.resolvedCases,
    required this.highRiskCases,
    this.topCategory,
    this.avgResolutionHours,
  });

  factory WardPerformanceModel.fromJson(Map<String, dynamic> json) {
    return WardPerformanceModel(
      ward: json['ward'] as String,
      totalCases: json['total_cases'] as int? ?? 0,
      activeCases: json['active_cases'] as int? ?? 0,
      resolvedCases: json['resolved_cases'] as int? ?? 0,
      highRiskCases: json['high_risk_cases'] as int? ?? 0,
      topCategory: json['top_category'] as String?,
      avgResolutionHours: (json['avg_resolution_hours'] as num?)?.toDouble(),
    );
  }
}

class AIOperationalInsightModel {
  final String id;
  final String insightType;
  final String severity;
  final String title;
  final String description;
  final String recommendation;
  final String? affectedWard;
  final String? affectedCategory;

  AIOperationalInsightModel({
    required this.id,
    required this.insightType,
    required this.severity,
    required this.title,
    required this.description,
    required this.recommendation,
    this.affectedWard,
    this.affectedCategory,
  });

  factory AIOperationalInsightModel.fromJson(Map<String, dynamic> json) {
    return AIOperationalInsightModel(
      id: json['id'] as String,
      insightType: json['insight_type'] as String? ?? 'anomaly',
      severity: json['severity'] as String? ?? 'medium',
      title: json['title'] as String,
      description: json['description'] as String,
      recommendation: json['recommendation'] as String,
      affectedWard: json['affected_ward'] as String?,
      affectedCategory: json['affected_category'] as String?,
    );
  }
}

class ManagerAnalyticsModel {
  final int totalCases;
  final int activeCases;
  final int resolvedCases;
  final int reopenedCases;
  final int escalatedCases;
  final double resolutionRatePercent;
  final double slaCompliancePercent;
  final double avgResolutionTimeHours;
  final Map<String, int> casesByStatus;
  final Map<String, int> casesByPriority;
  final Map<String, int> casesBySeverity;
  final List<DepartmentPerformanceModel> departmentMetrics;
  final List<CategoryPerformanceModel> categoryMetrics;
  final List<WardPerformanceModel> wardMetrics;
  final List<TimeSeriesMetricModel> timeSeriesTrends;
  final List<AIOperationalInsightModel> aiOperationalInsights;

  ManagerAnalyticsModel({
    required this.totalCases,
    required this.activeCases,
    required this.resolvedCases,
    required this.reopenedCases,
    required this.escalatedCases,
    required this.resolutionRatePercent,
    required this.slaCompliancePercent,
    required this.avgResolutionTimeHours,
    required this.casesByStatus,
    required this.casesByPriority,
    required this.casesBySeverity,
    required this.departmentMetrics,
    required this.categoryMetrics,
    required this.wardMetrics,
    required this.timeSeriesTrends,
    required this.aiOperationalInsights,
  });

  factory ManagerAnalyticsModel.fromJson(Map<String, dynamic> json) {
    final deptList = json['department_metrics'] as List<dynamic>? ?? [];
    final catList = json['category_metrics'] as List<dynamic>? ?? [];
    final wardList = json['ward_metrics'] as List<dynamic>? ?? [];
    final trendList = json['time_series_trends'] as List<dynamic>? ?? [];
    final insightList = json['ai_operational_insights'] as List<dynamic>? ?? [];

    return ManagerAnalyticsModel(
      totalCases: json['total_cases'] as int? ?? 0,
      activeCases: json['active_cases'] as int? ?? 0,
      resolvedCases: json['resolved_cases'] as int? ?? 0,
      reopenedCases: json['reopened_cases'] as int? ?? 0,
      escalatedCases: json['escalated_cases'] as int? ?? 0,
      resolutionRatePercent: (json['resolution_rate_percent'] as num?)?.toDouble() ?? 0.0,
      slaCompliancePercent: (json['sla_compliance_percent'] as num?)?.toDouble() ?? 100.0,
      avgResolutionTimeHours: (json['avg_resolution_time_hours'] as num?)?.toDouble() ?? 0.0,
      casesByStatus: Map<String, int>.from(json['cases_by_status'] as Map? ?? {}),
      casesByPriority: Map<String, int>.from(json['cases_by_priority'] as Map? ?? {}),
      casesBySeverity: Map<String, int>.from(json['cases_by_severity'] as Map? ?? {}),
      departmentMetrics: deptList.map((d) => DepartmentPerformanceModel.fromJson(d as Map<String, dynamic>)).toList(),
      categoryMetrics: catList.map((c) => CategoryPerformanceModel.fromJson(c as Map<String, dynamic>)).toList(),
      wardMetrics: wardList.map((w) => WardPerformanceModel.fromJson(w as Map<String, dynamic>)).toList(),
      timeSeriesTrends: trendList.map((t) => TimeSeriesMetricModel.fromJson(t as Map<String, dynamic>)).toList(),
      aiOperationalInsights: insightList.map((i) => AIOperationalInsightModel.fromJson(i as Map<String, dynamic>)).toList(),
    );
  }
}

class OperatorWorkloadModel {
  final int operatorId;
  final String operatorName;
  final int activeCases;
  final int completedCases;
  final int overdueCases;

  OperatorWorkloadModel({
    required this.operatorId,
    required this.operatorName,
    required this.activeCases,
    required this.completedCases,
    required this.overdueCases,
  });

  factory OperatorWorkloadModel.fromJson(Map<String, dynamic> json) {
    return OperatorWorkloadModel(
      operatorId: json['operator_id'] as int,
      operatorName: json['operator_name'] as String,
      activeCases: json['active_cases'] as int? ?? 0,
      completedCases: json['completed_cases'] as int? ?? 0,
      overdueCases: json['overdue_cases'] as int? ?? 0,
    );
  }
}

class TeamLeadAnalyticsModel {
  final int? teamId;
  final String? teamName;
  final int? departmentId;
  final String? departmentName;
  final int totalCases;
  final int activeCases;
  final int atRiskCases;
  final int activeEscalations;
  final int unassignedCases;
  final double slaCompliancePercent;
  final double avgResolutionTimeHours;
  final List<OperatorWorkloadModel> operatorWorkloads;

  TeamLeadAnalyticsModel({
    this.teamId,
    this.teamName,
    this.departmentId,
    this.departmentName,
    required this.totalCases,
    required this.activeCases,
    required this.atRiskCases,
    required this.activeEscalations,
    required this.unassignedCases,
    required this.slaCompliancePercent,
    required this.avgResolutionTimeHours,
    required this.operatorWorkloads,
  });

  factory TeamLeadAnalyticsModel.fromJson(Map<String, dynamic> json) {
    final workloads = json['operator_workloads'] as List<dynamic>? ?? [];
    return TeamLeadAnalyticsModel(
      teamId: json['team_id'] as int?,
      teamName: json['team_name'] as String?,
      departmentId: json['department_id'] as int?,
      departmentName: json['department_name'] as String?,
      totalCases: json['total_cases'] as int? ?? 0,
      activeCases: json['active_cases'] as int? ?? 0,
      atRiskCases: json['at_risk_cases'] as int? ?? 0,
      activeEscalations: json['active_escalations'] as int? ?? 0,
      unassignedCases: json['unassigned_cases'] as int? ?? 0,
      slaCompliancePercent: (json['sla_compliance_percent'] as num?)?.toDouble() ?? 100.0,
      avgResolutionTimeHours: (json['avg_resolution_time_hours'] as num?)?.toDouble() ?? 0.0,
      operatorWorkloads: workloads.map((w) => OperatorWorkloadModel.fromJson(w as Map<String, dynamic>)).toList(),
    );
  }
}

class OperatorAnalyticsModel {
  final int operatorId;
  final String operatorName;
  final int assignedActiveCount;
  final int highPriorityCount;
  final int waitingInfoCount;
  final int atRiskCount;
  final int activeEscalationsCount;
  final int pendingTasksCount;
  final int completedThisWeekCount;

  OperatorAnalyticsModel({
    required this.operatorId,
    required this.operatorName,
    required this.assignedActiveCount,
    required this.highPriorityCount,
    required this.waitingInfoCount,
    required this.atRiskCount,
    required this.activeEscalationsCount,
    required this.pendingTasksCount,
    required this.completedThisWeekCount,
  });

  factory OperatorAnalyticsModel.fromJson(Map<String, dynamic> json) {
    return OperatorAnalyticsModel(
      operatorId: json['operator_id'] as int,
      operatorName: json['operator_name'] as String,
      assignedActiveCount: json['assigned_active_count'] as int? ?? 0,
      highPriorityCount: json['high_priority_count'] as int? ?? 0,
      waitingInfoCount: json['waiting_info_count'] as int? ?? 0,
      atRiskCount: json['at_risk_count'] as int? ?? 0,
      activeEscalationsCount: json['active_escalations_count'] as int? ?? 0,
      pendingTasksCount: json['pending_tasks_count'] as int? ?? 0,
      completedThisWeekCount: json['completed_this_week_count'] as int? ?? 0,
    );
  }
}

class CitizenActivitySummaryModel {
  final int caseId;
  final String caseNumber;
  final String title;
  final String action;
  final String? notes;
  final DateTime timestamp;

  CitizenActivitySummaryModel({
    required this.caseId,
    required this.caseNumber,
    required this.title,
    required this.action,
    this.notes,
    required this.timestamp,
  });

  factory CitizenActivitySummaryModel.fromJson(Map<String, dynamic> json) {
    return CitizenActivitySummaryModel(
      caseId: json['case_id'] as int,
      caseNumber: json['case_number'] as String,
      title: json['title'] as String,
      action: json['action'] as String,
      notes: json['notes'] as String?,
      timestamp: DateTime.parse(json['timestamp'] as String),
    );
  }
}

class CitizenAnalyticsModel {
  final int citizenId;
  final int totalReported;
  final int activeCount;
  final int waitingInfoCount;
  final int pendingConfirmationCount;
  final int resolvedCount;
  final List<CitizenActivitySummaryModel> recentActivity;

  CitizenAnalyticsModel({
    required this.citizenId,
    required this.totalReported,
    required this.activeCount,
    required this.waitingInfoCount,
    required this.pendingConfirmationCount,
    required this.resolvedCount,
    required this.recentActivity,
  });

  factory CitizenAnalyticsModel.fromJson(Map<String, dynamic> json) {
    final acts = json['recent_activity'] as List<dynamic>? ?? [];
    return CitizenAnalyticsModel(
      citizenId: json['citizen_id'] as int,
      totalReported: json['total_reported'] as int? ?? 0,
      activeCount: json['active_count'] as int? ?? 0,
      waitingInfoCount: json['waiting_info_count'] as int? ?? 0,
      pendingConfirmationCount: json['pending_confirmation_count'] as int? ?? 0,
      resolvedCount: json['resolved_count'] as int? ?? 0,
      recentActivity: acts.map((a) => CitizenActivitySummaryModel.fromJson(a as Map<String, dynamic>)).toList(),
    );
  }
}

class SystemStatsModel {
  final int totalUsers;
  final Map<String, int> usersByRole;
  final int totalDepartments;
  final int totalTeams;
  final int totalCategories;
  final int totalCases;
  final int totalEscalations;
  final int totalNotificationsSent;
  final String databaseStatus;

  SystemStatsModel({
    required this.totalUsers,
    required this.usersByRole,
    required this.totalDepartments,
    required this.totalTeams,
    required this.totalCategories,
    required this.totalCases,
    required this.totalEscalations,
    required this.totalNotificationsSent,
    required this.databaseStatus,
  });

  factory SystemStatsModel.fromJson(Map<String, dynamic> json) {
    return SystemStatsModel(
      totalUsers: json['total_users'] as int? ?? 0,
      usersByRole: Map<String, int>.from(json['users_by_role'] as Map? ?? {}),
      totalDepartments: json['total_departments'] as int? ?? 0,
      totalTeams: json['total_teams'] as int? ?? 0,
      totalCategories: json['total_categories'] as int? ?? 0,
      totalCases: json['total_cases'] as int? ?? 0,
      totalEscalations: json['total_escalations'] as int? ?? 0,
      totalNotificationsSent: json['total_notifications_sent'] as int? ?? 0,
      databaseStatus: json['database_status'] as String? ?? 'healthy',
    );
  }
}

class AuditLogEntryModel {
  final int id;
  final int caseId;
  final String? caseNumber;
  final int? actorId;
  final String? actorName;
  final String? actorRole;
  final String action;
  final String? oldValue;
  final String? newValue;
  final String? notes;
  final DateTime createdAt;

  AuditLogEntryModel({
    required this.id,
    required this.caseId,
    this.caseNumber,
    this.actorId,
    this.actorName,
    this.actorRole,
    required this.action,
    this.oldValue,
    this.newValue,
    this.notes,
    required this.createdAt,
  });

  factory AuditLogEntryModel.fromJson(Map<String, dynamic> json) {
    return AuditLogEntryModel(
      id: json['id'] as int,
      caseId: json['case_id'] as int,
      caseNumber: json['case_number'] as String?,
      actorId: json['actor_id'] as int?,
      actorName: json['actor_name'] as String?,
      actorRole: json['actor_role'] as String?,
      action: json['action'] as String,
      oldValue: json['old_value'] as String?,
      newValue: json['new_value'] as String?,
      notes: json['notes'] as String?,
      createdAt: DateTime.parse(json['created_at'] as String),
    );
  }
}

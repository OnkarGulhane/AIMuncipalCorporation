import 'package:flutter/material.dart';

class CaseSLAModel {
  final int id;
  final int caseId;
  final int responseTargetHours;
  final int resolutionTargetHours;
  final DateTime responseDueAt;
  final DateTime resolutionDueAt;
  final DateTime? firstRespondedAt;
  final DateTime? resolvedAt;
  final String responseStatus;
  final String resolutionStatus;
  final bool isBreached;
  final DateTime? breachedAt;
  final DateTime? warningIssuedAt;
  final DateTime createdAt;
  final String responseRemainingText;
  final String resolutionRemainingText;
  final double responseProgressPercentage;
  final double resolutionProgressPercentage;

  CaseSLAModel({
    required this.id,
    required this.caseId,
    required this.responseTargetHours,
    required this.resolutionTargetHours,
    required this.responseDueAt,
    required this.resolutionDueAt,
    this.firstRespondedAt,
    this.resolvedAt,
    required this.responseStatus,
    required this.resolutionStatus,
    required this.isBreached,
    this.breachedAt,
    this.warningIssuedAt,
    required this.createdAt,
    required this.responseRemainingText,
    required this.resolutionRemainingText,
    required this.responseProgressPercentage,
    required this.resolutionProgressPercentage,
  });

  factory CaseSLAModel.fromJson(Map<String, dynamic> json) {
    return CaseSLAModel(
      id: json['id'] as int,
      caseId: json['case_id'] as int,
      responseTargetHours: json['response_target_hours'] as int? ?? 8,
      resolutionTargetHours: json['resolution_target_hours'] as int? ?? 48,
      responseDueAt: DateTime.parse(json['response_due_at'] as String),
      resolutionDueAt: DateTime.parse(json['resolution_due_at'] as String),
      firstRespondedAt: json['first_responded_at'] != null ? DateTime.parse(json['first_responded_at'] as String) : null,
      resolvedAt: json['resolved_at'] != null ? DateTime.parse(json['resolved_at'] as String) : null,
      responseStatus: json['response_status'] as String? ?? 'within_target',
      resolutionStatus: json['resolution_status'] as String? ?? 'within_target',
      isBreached: json['is_breached'] as bool? ?? false,
      breachedAt: json['breached_at'] != null ? DateTime.parse(json['breached_at'] as String) : null,
      warningIssuedAt: json['warning_issued_at'] != null ? DateTime.parse(json['warning_issued_at'] as String) : null,
      createdAt: DateTime.parse(json['created_at'] as String),
      responseRemainingText: json['response_remaining_text'] as String? ?? '',
      resolutionRemainingText: json['resolution_remaining_text'] as String? ?? '',
      responseProgressPercentage: (json['response_progress_percentage'] as num?)?.toDouble() ?? 0.0,
      resolutionProgressPercentage: (json['resolution_progress_percentage'] as num?)?.toDouble() ?? 0.0,
    );
  }

  Color get statusColor {
    if (isBreached || resolutionStatus == 'breached') {
      return Colors.red;
    }
    if (resolutionStatus == 'approaching_breach') {
      return Colors.orange;
    }
    if (resolutionStatus == 'met') {
      return Colors.green;
    }
    return Colors.teal;
  }
}

class RiskSignalItem {
  final String key;
  final String label;
  final String severity;
  final String description;

  RiskSignalItem({
    required this.key,
    required this.label,
    required this.severity,
    required this.description,
  });

  factory RiskSignalItem.fromJson(Map<String, dynamic> json) {
    return RiskSignalItem(
      key: json['key'] as String? ?? '',
      label: json['label'] as String? ?? '',
      severity: json['severity'] as String? ?? 'low',
      description: json['description'] as String? ?? '',
    );
  }
}

class RiskAnalysisModel {
  final int caseId;
  final int riskScore;
  final String riskTier;
  final List<String> riskFactors;
  final List<RiskSignalItem> signals;
  final DateTime evaluatedAt;

  RiskAnalysisModel({
    required this.caseId,
    required this.riskScore,
    required this.riskTier,
    required this.riskFactors,
    required this.signals,
    required this.evaluatedAt,
  });

  factory RiskAnalysisModel.fromJson(Map<String, dynamic> json) {
    return RiskAnalysisModel(
      caseId: json['case_id'] as int,
      riskScore: json['risk_score'] as int? ?? 0,
      riskTier: json['risk_tier'] as String? ?? 'low',
      riskFactors: (json['risk_factors'] as List? ?? []).map((e) => e.toString()).toList(),
      signals: (json['signals'] as List? ?? [])
          .map((e) => RiskSignalItem.fromJson(e as Map<String, dynamic>))
          .toList(),
      evaluatedAt: DateTime.parse(json['evaluated_at'] as String),
    );
  }

  Color get tierColor {
    switch (riskTier.toLowerCase()) {
      case 'critical':
        return Colors.red;
      case 'high':
        return Colors.deepOrange;
      case 'medium':
        return Colors.amber.shade800;
      case 'low':
      default:
        return Colors.green;
    }
  }
}

class EscalationModel {
  final int id;
  final int caseId;
  final String? caseNumber;
  final String? caseTitle;
  final int? escalatedById;
  final String? escalatedByName;
  final int? escalatedToId;
  final String? escalatedToName;
  final String triggerType;
  final String reason;
  final String status;
  final String? resolutionNotes;
  final int? resolvedById;
  final String? resolvedByName;
  final DateTime? resolvedAt;
  final DateTime createdAt;

  EscalationModel({
    required this.id,
    required this.caseId,
    this.caseNumber,
    this.caseTitle,
    this.escalatedById,
    this.escalatedByName,
    this.escalatedToId,
    this.escalatedToName,
    required this.triggerType,
    required this.reason,
    required this.status,
    this.resolutionNotes,
    this.resolvedById,
    this.resolvedByName,
    this.resolvedAt,
    required this.createdAt,
  });

  factory EscalationModel.fromJson(Map<String, dynamic> json) {
    return EscalationModel(
      id: json['id'] as int,
      caseId: json['case_id'] as int,
      caseNumber: json['case_number'] as String?,
      caseTitle: json['case_title'] as String?,
      escalatedById: json['escalated_by_id'] as int?,
      escalatedByName: json['escalated_by_name'] as String?,
      escalatedToId: json['escalated_to_id'] as int?,
      escalatedToName: json['escalated_to_name'] as String?,
      triggerType: json['trigger_type'] as String? ?? 'manual',
      reason: json['reason'] as String? ?? '',
      status: json['status'] as String? ?? 'active',
      resolutionNotes: json['resolution_notes'] as String?,
      resolvedById: json['resolved_by_id'] as int?,
      resolvedByName: json['resolved_by_name'] as String?,
      resolvedAt: json['resolved_at'] != null ? DateTime.parse(json['resolved_at'] as String) : null,
      createdAt: DateTime.parse(json['created_at'] as String),
    );
  }

  bool get isActive => status.toLowerCase() == 'active';
}

import 'package:flutter/material.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../auth/data/auth_models.dart';

enum CaseStatus {
  reported,
  understood,
  assigned,
  investigated,
  actionTaken,
  resolutionProposed,
  confirmed,
  closed,
  waitingInfo,
  escalated,
  duplicate,
  reopened,
  cancelled;

  static CaseStatus fromString(String val) {
    switch (val.toLowerCase()) {
      case 'understood':
        return CaseStatus.understood;
      case 'assigned':
        return CaseStatus.assigned;
      case 'investigated':
        return CaseStatus.investigated;
      case 'action_taken':
        return CaseStatus.actionTaken;
      case 'resolution_proposed':
        return CaseStatus.resolutionProposed;
      case 'confirmed':
        return CaseStatus.confirmed;
      case 'closed':
        return CaseStatus.closed;
      case 'waiting_info':
        return CaseStatus.waitingInfo;
      case 'escalated':
        return CaseStatus.escalated;
      case 'duplicate':
        return CaseStatus.duplicate;
      case 'reopened':
        return CaseStatus.reopened;
      case 'cancelled':
        return CaseStatus.cancelled;
      case 'reported':
      default:
        return CaseStatus.reported;
    }
  }

  String get displayName {
    switch (this) {
      case CaseStatus.reported:
        return 'Reported';
      case CaseStatus.understood:
        return 'Understood';
      case CaseStatus.assigned:
        return 'Assigned';
      case CaseStatus.investigated:
        return 'Investigated';
      case CaseStatus.actionTaken:
        return 'Action Taken';
      case CaseStatus.resolutionProposed:
        return 'Resolution Proposed';
      case CaseStatus.confirmed:
        return 'Confirmed';
      case CaseStatus.closed:
        return 'Closed';
      case CaseStatus.waitingInfo:
        return 'Waiting Info';
      case CaseStatus.escalated:
        return 'Escalated';
      case CaseStatus.duplicate:
        return 'Duplicate';
      case CaseStatus.reopened:
        return 'Reopened';
      case CaseStatus.cancelled:
        return 'Cancelled';
    }
  }

  Color get badgeColor {
    switch (this) {
      case CaseStatus.reported:
        return const Color(0xFF64748B); // Slate
      case CaseStatus.understood:
        return const Color(0xFF6366F1); // Indigo
      case CaseStatus.assigned:
        return AppColors.primary; // Blue
      case CaseStatus.investigated:
        return const Color(0xFF0284C7); // Cyan
      case CaseStatus.actionTaken:
        return AppColors.secondary; // Teal
      case CaseStatus.resolutionProposed:
        return const Color(0xFF10B981); // Emerald
      case CaseStatus.confirmed:
      case CaseStatus.closed:
        return const Color(0xFF059669); // Dark green
      case CaseStatus.waitingInfo:
        return const Color(0xFFF59E0B); // Amber
      case CaseStatus.escalated:
      case CaseStatus.reopened:
        return AppColors.statusError; // Red
      case CaseStatus.duplicate:
      case CaseStatus.cancelled:
        return const Color(0xFF94A3B8); // Muted
    }
  }

  int get stepIndex {
    switch (this) {
      case CaseStatus.reported:
        return 0;
      case CaseStatus.understood:
        return 1;
      case CaseStatus.assigned:
        return 2;
      case CaseStatus.investigated:
        return 3;
      case CaseStatus.actionTaken:
        return 4;
      case CaseStatus.resolutionProposed:
        return 5;
      case CaseStatus.confirmed:
        return 6;
      case CaseStatus.closed:
        return 7;
      default:
        return 2;
    }
  }
}

enum CasePriority {
  low,
  medium,
  high,
  critical;

  static CasePriority fromString(String val) {
    switch (val.toLowerCase()) {
      case 'low':
        return CasePriority.low;
      case 'high':
        return CasePriority.high;
      case 'critical':
        return CasePriority.critical;
      case 'medium':
      default:
        return CasePriority.medium;
    }
  }

  Color get color {
    switch (this) {
      case CasePriority.low:
        return const Color(0xFF10B981);
      case CasePriority.medium:
        return const Color(0xFFF59E0B);
      case CasePriority.high:
        return const Color(0xFFEF4444);
      case CasePriority.critical:
        return const Color(0xFF991B1B);
    }
  }
}

class CaseTimelineModel {
  final int id;
  final int caseId;
  final int? actorId;
  final String action;
  final String? oldValue;
  final String? newValue;
  final String? notes;
  final bool isInternal;
  final DateTime createdAt;

  CaseTimelineModel({
    required this.id,
    required this.caseId,
    this.actorId,
    required this.action,
    this.oldValue,
    this.newValue,
    this.notes,
    required this.isInternal,
    required this.createdAt,
  });

  factory CaseTimelineModel.fromJson(Map<String, dynamic> json) {
    return CaseTimelineModel(
      id: json['id'] as int,
      caseId: json['case_id'] as int,
      actorId: json['actor_id'] as int?,
      action: json['action'] as String? ?? 'UPDATED',
      oldValue: json['old_value'] as String?,
      newValue: json['new_value'] as String?,
      notes: json['notes'] as String?,
      isInternal: json['is_internal'] as bool? ?? false,
      createdAt: json['created_at'] != null
          ? DateTime.tryParse(json['created_at'].toString()) ?? DateTime.now()
          : DateTime.now(),
    );
  }
}

class CaseModel {
  final int id;
  final String caseNumber;
  final String title;
  final String description;
  final CaseStatus status;
  final CasePriority priority;
  final String severity;
  final int citizenId;
  final int? departmentId;
  final int? categoryId;
  final int? teamId;
  final int? assignedToId;
  final String? ward;
  final String? landmark;
  final String? address;
  final String? resolutionNotes;
  final String? rejectionReason;
  final DateTime? closedAt;
  final bool isEscalated;
  final DateTime createdAt;
  final DateTime updatedAt;
  final UserModel? citizen;
  final UserModel? assignedTo;
  final List<CaseTimelineModel> timeline;

  CaseModel({
    required this.id,
    required this.caseNumber,
    required this.title,
    required this.description,
    required this.status,
    required this.priority,
    required this.severity,
    required this.citizenId,
    this.departmentId,
    this.categoryId,
    this.teamId,
    this.assignedToId,
    this.ward,
    this.landmark,
    this.address,
    this.resolutionNotes,
    this.rejectionReason,
    this.closedAt,
    this.isEscalated = false,
    required this.createdAt,
    required this.updatedAt,
    this.citizen,
    this.assignedTo,
    this.timeline = const [],
  });

  factory CaseModel.fromJson(Map<String, dynamic> json) {
    return CaseModel(
      id: json['id'] as int,
      caseNumber: json['case_number'] as String,
      title: json['title'] as String,
      description: json['description'] as String,
      status: CaseStatus.fromString(json['status'] as String? ?? 'reported'),
      priority: CasePriority.fromString(json['priority'] as String? ?? 'medium'),
      severity: json['severity'] as String? ?? 'moderate',
      citizenId: json['citizen_id'] as int,
      departmentId: json['department_id'] as int?,
      categoryId: json['category_id'] as int?,
      teamId: json['team_id'] as int?,
      assignedToId: json['assigned_to_id'] as int?,
      ward: json['ward'] as String?,
      landmark: json['landmark'] as String?,
      address: json['address'] as String?,
      resolutionNotes: json['resolution_notes'] as String?,
      rejectionReason: json['rejection_reason'] as String?,
      closedAt: json['closed_at'] != null ? DateTime.tryParse(json['closed_at'].toString()) : null,
      isEscalated: json['is_escalated'] as bool? ?? false,
      createdAt: json['created_at'] != null
          ? DateTime.tryParse(json['created_at'].toString()) ?? DateTime.now()
          : DateTime.now(),
      updatedAt: json['updated_at'] != null
          ? DateTime.tryParse(json['updated_at'].toString()) ?? DateTime.now()
          : DateTime.now(),
      citizen: json['citizen'] != null ? UserModel.fromJson(json['citizen'] as Map<String, dynamic>) : null,
      assignedTo: json['assigned_to'] != null ? UserModel.fromJson(json['assigned_to'] as Map<String, dynamic>) : null,
      timeline: json['timeline'] != null
          ? (json['timeline'] as List).map((t) => CaseTimelineModel.fromJson(t as Map<String, dynamic>)).toList()
          : [],
    );
  }
}

class CaseListResponseModel {
  final List<CaseModel> items;
  final int total;
  final int page;
  final int size;

  CaseListResponseModel({
    required this.items,
    required this.total,
    required this.page,
    required this.size,
  });

  factory CaseListResponseModel.fromJson(Map<String, dynamic> json) {
    return CaseListResponseModel(
      items: (json['items'] as List? ?? []).map((i) => CaseModel.fromJson(i as Map<String, dynamic>)).toList(),
      total: json['total'] as int? ?? 0,
      page: json['page'] as int? ?? 1,
      size: json['size'] as int? ?? 50,
    );
  }
}

class UnifiedTimelineItemModel {
  final String id;
  final String eventType;
  final String title;
  final String? description;
  final int? actorId;
  final String? actorName;
  final String? actorRole;
  final bool isInternal;
  final Map<String, dynamic>? metadata;
  final DateTime timestamp;

  UnifiedTimelineItemModel({
    required this.id,
    required this.eventType,
    required this.title,
    this.description,
    this.actorId,
    this.actorName,
    this.actorRole,
    this.isInternal = false,
    this.metadata,
    required this.timestamp,
  });

  factory UnifiedTimelineItemModel.fromJson(Map<String, dynamic> json) {
    return UnifiedTimelineItemModel(
      id: json['id'] as String? ?? '',
      eventType: json['event_type'] as String? ?? 'general',
      title: json['title'] as String? ?? 'Update',
      description: json['description'] as String?,
      actorId: json['actor_id'] as int?,
      actorName: json['actor_name'] as String?,
      actorRole: json['actor_role'] as String?,
      isInternal: json['is_internal'] as bool? ?? false,
      metadata: json['metadata'] as Map<String, dynamic>?,
      timestamp: json['timestamp'] != null
          ? DateTime.tryParse(json['timestamp'].toString()) ?? DateTime.now()
          : DateTime.now(),
    );
  }
}

class UnifiedTimelineResponseModel {
  final int caseId;
  final String caseNumber;
  final int totalEvents;
  final List<UnifiedTimelineItemModel> timeline;

  UnifiedTimelineResponseModel({
    required this.caseId,
    required this.caseNumber,
    required this.totalEvents,
    required this.timeline,
  });

  factory UnifiedTimelineResponseModel.fromJson(Map<String, dynamic> json) {
    return UnifiedTimelineResponseModel(
      caseId: json['case_id'] as int? ?? 0,
      caseNumber: json['case_number'] as String? ?? '',
      totalEvents: json['total_events'] as int? ?? 0,
      timeline: (json['timeline'] as List? ?? [])
          .map((item) => UnifiedTimelineItemModel.fromJson(item as Map<String, dynamic>))
          .toList(),
    );
  }
}


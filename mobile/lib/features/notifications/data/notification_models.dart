class NotificationItem {
  final int id;
  final int userId;
  final int? caseId;
  final String? caseNumber;
  final String? caseTitle;
  final String title;
  final String message;
  final String eventType;
  final String channel;
  final bool isRead;
  final DateTime? readAt;
  final String deliveryStatus;
  final DateTime createdAt;

  NotificationItem({
    required this.id,
    required this.userId,
    this.caseId,
    this.caseNumber,
    this.caseTitle,
    required this.title,
    required this.message,
    required this.eventType,
    required this.channel,
    required this.isRead,
    this.readAt,
    required this.deliveryStatus,
    required this.createdAt,
  });

  factory NotificationItem.fromJson(Map<String, dynamic> json) {
    return NotificationItem(
      id: json['id'] as int,
      userId: json['user_id'] as int,
      caseId: json['case_id'] as int?,
      caseNumber: json['case_number'] as String?,
      caseTitle: json['case_title'] as String?,
      title: json['title'] as String,
      message: json['message'] as String,
      eventType: json['event_type'] as String? ?? 'status_changed',
      channel: json['channel'] as String? ?? 'in_app',
      isRead: json['is_read'] as bool? ?? false,
      readAt: json['read_at'] != null ? DateTime.parse(json['read_at'] as String) : null,
      deliveryStatus: json['delivery_status'] as String? ?? 'delivered',
      createdAt: DateTime.parse(json['created_at'] as String),
    );
  }
}

class NotificationListResponse {
  final List<NotificationItem> items;
  final int total;
  final int unreadCount;
  final int page;
  final int size;

  NotificationListResponse({
    required this.items,
    required this.total,
    required this.unreadCount,
    required this.page,
    required this.size,
  });

  factory NotificationListResponse.fromJson(Map<String, dynamic> json) {
    final rawList = json['items'] as List<dynamic>? ?? [];
    return NotificationListResponse(
      items: rawList.map((item) => NotificationItem.fromJson(item as Map<String, dynamic>)).toList(),
      total: json['total'] as int? ?? 0,
      unreadCount: json['unread_count'] as int? ?? 0,
      page: json['page'] as int? ?? 1,
      size: json['size'] as int? ?? 50,
    );
  }
}

class NotificationPreference {
  final int userId;
  final bool emailEnabled;
  final bool inAppEnabled;
  final bool notifyOnAssignment;
  final bool notifyOnStatusChange;
  final bool notifyOnSlaWarning;
  final bool notifyOnEscalation;
  final bool notifyOnMessages;

  NotificationPreference({
    required this.userId,
    required this.emailEnabled,
    required this.inAppEnabled,
    required this.notifyOnAssignment,
    required this.notifyOnStatusChange,
    required this.notifyOnSlaWarning,
    required this.notifyOnEscalation,
    required this.notifyOnMessages,
  });

  factory NotificationPreference.fromJson(Map<String, dynamic> json) {
    return NotificationPreference(
      userId: json['user_id'] as int,
      emailEnabled: json['email_enabled'] as bool? ?? true,
      inAppEnabled: json['in_app_enabled'] as bool? ?? true,
      notifyOnAssignment: json['notify_on_assignment'] as bool? ?? true,
      notifyOnStatusChange: json['notify_on_status_change'] as bool? ?? true,
      notifyOnSlaWarning: json['notify_on_sla_warning'] as bool? ?? true,
      notifyOnEscalation: json['notify_on_escalation'] as bool? ?? true,
      notifyOnMessages: json['notify_on_messages'] as bool? ?? true,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'email_enabled': emailEnabled,
      'in_app_enabled': inAppEnabled,
      'notify_on_assignment': notifyOnAssignment,
      'notify_on_status_change': notifyOnStatusChange,
      'notify_on_sla_warning': notifyOnSlaWarning,
      'notify_on_escalation': notifyOnEscalation,
      'notify_on_messages': notifyOnMessages,
    };
  }
}

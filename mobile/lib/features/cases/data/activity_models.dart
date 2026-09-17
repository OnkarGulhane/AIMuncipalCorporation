class CaseMessageModel {
  final int id;
  final int caseId;
  final int senderId;
  final String? senderName;
  final String? senderRole;
  final String message;
  final String messageType;
  final bool isFromCitizen;
  final DateTime createdAt;

  CaseMessageModel({
    required this.id,
    required this.caseId,
    required this.senderId,
    this.senderName,
    this.senderRole,
    required this.message,
    required this.messageType,
    required this.isFromCitizen,
    required this.createdAt,
  });

  factory CaseMessageModel.fromJson(Map<String, dynamic> json) {
    return CaseMessageModel(
      id: json['id'] ?? 0,
      caseId: json['case_id'] ?? 0,
      senderId: json['sender_id'] ?? 0,
      senderName: json['sender_name'],
      senderRole: json['sender_role'],
      message: json['message'] ?? '',
      messageType: json['message_type'] ?? 'general',
      isFromCitizen: json['is_from_citizen'] ?? false,
      createdAt: json['created_at'] != null
          ? DateTime.tryParse(json['created_at']) ?? DateTime.now()
          : DateTime.now(),
    );
  }
}

class InternalNoteModel {
  final int id;
  final int caseId;
  final int authorId;
  final String? authorName;
  final String? authorRole;
  final String note;
  final String noteType;
  final DateTime createdAt;

  InternalNoteModel({
    required this.id,
    required this.caseId,
    required this.authorId,
    this.authorName,
    this.authorRole,
    required this.note,
    required this.noteType,
    required this.createdAt,
  });

  factory InternalNoteModel.fromJson(Map<String, dynamic> json) {
    return InternalNoteModel(
      id: json['id'] ?? 0,
      caseId: json['case_id'] ?? 0,
      authorId: json['author_id'] ?? 0,
      authorName: json['author_name'],
      authorRole: json['author_role'],
      note: json['note'] ?? '',
      noteType: json['note_type'] ?? 'general',
      createdAt: json['created_at'] != null
          ? DateTime.tryParse(json['created_at']) ?? DateTime.now()
          : DateTime.now(),
    );
  }
}

class CaseTaskModel {
  final int id;
  final int caseId;
  final String title;
  final String? description;
  final String status;
  final int? assignedToId;
  final String? assignedToName;
  final int createdById;
  final String? createdByName;
  final DateTime? dueDate;
  final DateTime? completedAt;
  final int order;
  final DateTime createdAt;
  final DateTime updatedAt;

  CaseTaskModel({
    required this.id,
    required this.caseId,
    required this.title,
    this.description,
    required this.status,
    this.assignedToId,
    this.assignedToName,
    required this.createdById,
    this.createdByName,
    this.dueDate,
    this.completedAt,
    required this.order,
    required this.createdAt,
    required this.updatedAt,
  });

  factory CaseTaskModel.fromJson(Map<String, dynamic> json) {
    return CaseTaskModel(
      id: json['id'] ?? 0,
      caseId: json['case_id'] ?? 0,
      title: json['title'] ?? '',
      description: json['description'],
      status: json['status'] ?? 'pending',
      assignedToId: json['assigned_to_id'],
      assignedToName: json['assigned_to_name'],
      createdById: json['created_by_id'] ?? 0,
      createdByName: json['created_by_name'],
      dueDate: json['due_date'] != null ? DateTime.tryParse(json['due_date']) : null,
      completedAt: json['completed_at'] != null ? DateTime.tryParse(json['completed_at']) : null,
      order: json['order'] ?? 0,
      createdAt: json['created_at'] != null
          ? DateTime.tryParse(json['created_at']) ?? DateTime.now()
          : DateTime.now(),
      updatedAt: json['updated_at'] != null
          ? DateTime.tryParse(json['updated_at']) ?? DateTime.now()
          : DateTime.now(),
    );
  }

  bool get isCompleted => status.toLowerCase() == 'completed';
}

class CaseInvestigationModel {
  final int id;
  final int caseId;
  final int investigatorId;
  final String? investigatorName;
  final String? observations;
  final String? actionsTaken;
  final String? findings;
  final String? evidenceNotes;
  final String? followUpRequirements;
  final DateTime createdAt;
  final DateTime updatedAt;

  CaseInvestigationModel({
    required this.id,
    required this.caseId,
    required this.investigatorId,
    this.investigatorName,
    this.observations,
    this.actionsTaken,
    this.findings,
    this.evidenceNotes,
    this.followUpRequirements,
    required this.createdAt,
    required this.updatedAt,
  });

  factory CaseInvestigationModel.fromJson(Map<String, dynamic> json) {
    return CaseInvestigationModel(
      id: json['id'] ?? 0,
      caseId: json['case_id'] ?? 0,
      investigatorId: json['investigator_id'] ?? 0,
      investigatorName: json['investigator_name'],
      observations: json['observations'],
      actionsTaken: json['actions_taken'],
      findings: json['findings'],
      evidenceNotes: json['evidence_notes'],
      followUpRequirements: json['follow_up_requirements'],
      createdAt: json['created_at'] != null
          ? DateTime.tryParse(json['created_at']) ?? DateTime.now()
          : DateTime.now(),
      updatedAt: json['updated_at'] != null
          ? DateTime.tryParse(json['updated_at']) ?? DateTime.now()
          : DateTime.now(),
    );
  }
}

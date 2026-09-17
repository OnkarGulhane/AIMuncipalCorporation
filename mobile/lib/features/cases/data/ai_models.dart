class DuplicateCaseModel {
  final int caseId;
  final String caseNumber;
  final String title;
  final double similarityScore;
  final String status;
  final String reason;

  DuplicateCaseModel({
    required this.caseId,
    required this.caseNumber,
    required this.title,
    required this.similarityScore,
    required this.status,
    required this.reason,
  });

  factory DuplicateCaseModel.fromJson(Map<String, dynamic> json) {
    return DuplicateCaseModel(
      caseId: json['case_id'] ?? 0,
      caseNumber: json['case_number'] ?? '',
      title: json['title'] ?? '',
      similarityScore: (json['similarity_score'] as num?)?.toDouble() ?? 0.0,
      status: json['status'] ?? '',
      reason: json['reason'] ?? '',
    );
  }
}

class AIAnalysisModel {
  final int id;
  final int caseId;
  final int? suggestedCategoryId;
  final String? suggestedCategoryName;
  final String? suggestedCategoryCode;
  final String? suggestedPriority;
  final String? suggestedSeverity;
  final double confidenceScore;
  final String? summary;
  final List<String> keyDetails;
  final List<String> missingInformation;
  final String? recommendedAction;
  final int? suggestedTeamId;
  final String? suggestedTeamName;
  final String? riskInsight;
  final List<DuplicateCaseModel> duplicateCases;
  final DateTime createdAt;

  AIAnalysisModel({
    required this.id,
    required this.caseId,
    this.suggestedCategoryId,
    this.suggestedCategoryName,
    this.suggestedCategoryCode,
    this.suggestedPriority,
    this.suggestedSeverity,
    required this.confidenceScore,
    this.summary,
    required this.keyDetails,
    required this.missingInformation,
    this.recommendedAction,
    this.suggestedTeamId,
    this.suggestedTeamName,
    this.riskInsight,
    required this.duplicateCases,
    required this.createdAt,
  });

  factory AIAnalysisModel.fromJson(Map<String, dynamic> json) {
    return AIAnalysisModel(
      id: json['id'] ?? 0,
      caseId: json['case_id'] ?? 0,
      suggestedCategoryId: json['suggested_category_id'],
      suggestedCategoryName: json['suggested_category_name'],
      suggestedCategoryCode: json['suggested_category_code'],
      suggestedPriority: json['suggested_priority'],
      suggestedSeverity: json['suggested_severity'],
      confidenceScore: (json['confidence_score'] as num?)?.toDouble() ?? 0.0,
      summary: json['summary'],
      keyDetails: (json['key_details'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          [],
      missingInformation: (json['missing_information'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          [],
      recommendedAction: json['recommended_action'],
      suggestedTeamId: json['suggested_team_id'],
      suggestedTeamName: json['suggested_team_name'],
      riskInsight: json['risk_insight'],
      duplicateCases: (json['duplicate_cases'] as List<dynamic>?)
              ?.map((e) => DuplicateCaseModel.fromJson(e as Map<String, dynamic>))
              .toList() ??
          [],
      createdAt: json['created_at'] != null
          ? DateTime.tryParse(json['created_at']) ?? DateTime.now()
          : DateTime.now(),
    );
  }
}

class AIDraftModel {
  final String draftType;
  final String subject;
  final String bodyText;
  final String? suggestedRecipients;

  AIDraftModel({
    required this.draftType,
    required this.subject,
    required this.bodyText,
    this.suggestedRecipients,
  });

  factory AIDraftModel.fromJson(Map<String, dynamic> json) {
    return AIDraftModel(
      draftType: json['draft_type'] ?? 'information_request',
      subject: json['subject'] ?? '',
      bodyText: json['body_text'] ?? '',
      suggestedRecipients: json['suggested_recipients'],
    );
  }
}

class AICaseSummaryModel {
  final int caseId;
  final String caseNumber;
  final String summary;
  final String currentStage;
  final List<String> unresolvedBlockers;
  final String? lastActivity;

  AICaseSummaryModel({
    required this.caseId,
    required this.caseNumber,
    required this.summary,
    required this.currentStage,
    required this.unresolvedBlockers,
    this.lastActivity,
  });

  factory AICaseSummaryModel.fromJson(Map<String, dynamic> json) {
    return AICaseSummaryModel(
      caseId: json['case_id'] ?? 0,
      caseNumber: json['case_number'] ?? '',
      summary: json['summary'] ?? '',
      currentStage: json['current_stage'] ?? '',
      unresolvedBlockers: (json['unresolved_blockers'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          [],
      lastActivity: json['last_activity'],
    );
  }
}

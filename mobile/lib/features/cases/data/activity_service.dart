import '../../../core/network/api_client.dart';
import '../../auth/data/auth_service.dart';
import 'activity_models.dart';

class ActivityService {
  final ApiClient _apiClient;

  ActivityService({ApiClient? apiClient}) : _apiClient = apiClient ?? ApiClient();

  // ---------------------------------------------------------------------------
  // Messages
  // ---------------------------------------------------------------------------
  Future<ApiResponse<List<CaseMessageModel>>> getMessages(int caseId) async {
    final token = AuthService.currentToken;
    return _apiClient.get<List<CaseMessageModel>>(
      '/api/v1/cases/$caseId/messages',
      token: token,
      fromJson: (json) {
        final list = json as List<dynamic>;
        return list.map((item) => CaseMessageModel.fromJson(item as Map<String, dynamic>)).toList();
      },
    );
  }

  Future<ApiResponse<CaseMessageModel>> sendMessage(
    int caseId, {
    required String message,
    String messageType = 'general',
  }) async {
    final token = AuthService.currentToken;
    return _apiClient.post<CaseMessageModel>(
      '/api/v1/cases/$caseId/messages',
      token: token,
      body: {
        'message': message,
        'message_type': messageType,
      },
      fromJson: (json) => CaseMessageModel.fromJson(json as Map<String, dynamic>),
    );
  }

  // ---------------------------------------------------------------------------
  // Internal Notes (Staff-only)
  // ---------------------------------------------------------------------------
  Future<ApiResponse<List<InternalNoteModel>>> getInternalNotes(int caseId) async {
    final token = AuthService.currentToken;
    return _apiClient.get<List<InternalNoteModel>>(
      '/api/v1/cases/$caseId/internal-notes',
      token: token,
      fromJson: (json) {
        final list = json as List<dynamic>;
        return list.map((item) => InternalNoteModel.fromJson(item as Map<String, dynamic>)).toList();
      },
    );
  }

  Future<ApiResponse<InternalNoteModel>> createInternalNote(
    int caseId, {
    required String note,
    String noteType = 'general',
  }) async {
    final token = AuthService.currentToken;
    return _apiClient.post<InternalNoteModel>(
      '/api/v1/cases/$caseId/internal-notes',
      token: token,
      body: {
        'note': note,
        'note_type': noteType,
      },
      fromJson: (json) => InternalNoteModel.fromJson(json as Map<String, dynamic>),
    );
  }

  // ---------------------------------------------------------------------------
  // Tasks
  // ---------------------------------------------------------------------------
  Future<ApiResponse<List<CaseTaskModel>>> getTasks(int caseId) async {
    final token = AuthService.currentToken;
    return _apiClient.get<List<CaseTaskModel>>(
      '/api/v1/cases/$caseId/tasks',
      token: token,
      fromJson: (json) {
        final list = json as List<dynamic>;
        return list.map((item) => CaseTaskModel.fromJson(item as Map<String, dynamic>)).toList();
      },
    );
  }

  Future<ApiResponse<CaseTaskModel>> createTask(
    int caseId, {
    required String title,
    String? description,
    int? assignedToId,
    DateTime? dueDate,
    int order = 0,
  }) async {
    final token = AuthService.currentToken;
    return _apiClient.post<CaseTaskModel>(
      '/api/v1/cases/$caseId/tasks',
      token: token,
      body: {
        'title': title,
        'description': description,
        'assigned_to_id': assignedToId,
        'due_date': dueDate?.toIso8601String(),
        'order': order,
      },
      fromJson: (json) => CaseTaskModel.fromJson(json as Map<String, dynamic>),
    );
  }

  Future<ApiResponse<CaseTaskModel>> updateTaskStatus(
    int caseId,
    int taskId, {
    required String status,
  }) async {
    final token = AuthService.currentToken;
    return _apiClient.patch<CaseTaskModel>(
      '/api/v1/cases/$caseId/tasks/$taskId',
      token: token,
      body: {'status': status},
      fromJson: (json) => CaseTaskModel.fromJson(json as Map<String, dynamic>),
    );
  }

  // ---------------------------------------------------------------------------
  // Investigations
  // ---------------------------------------------------------------------------
  Future<ApiResponse<List<CaseInvestigationModel>>> getInvestigations(int caseId) async {
    final token = AuthService.currentToken;
    return _apiClient.get<List<CaseInvestigationModel>>(
      '/api/v1/cases/$caseId/investigations',
      token: token,
      fromJson: (json) {
        final list = json as List<dynamic>;
        return list.map((item) => CaseInvestigationModel.fromJson(item as Map<String, dynamic>)).toList();
      },
    );
  }

  Future<ApiResponse<CaseInvestigationModel>> recordInvestigation(
    int caseId, {
    String? observations,
    String? actionsTaken,
    String? findings,
    String? evidenceNotes,
    String? followUpRequirements,
  }) async {
    final token = AuthService.currentToken;
    return _apiClient.post<CaseInvestigationModel>(
      '/api/v1/cases/$caseId/investigations',
      token: token,
      body: {
        'observations': observations,
        'actions_taken': actionsTaken,
        'findings': findings,
        'evidence_notes': evidenceNotes,
        'follow_up_requirements': followUpRequirements,
      },
      fromJson: (json) => CaseInvestigationModel.fromJson(json as Map<String, dynamic>),
    );
  }
}

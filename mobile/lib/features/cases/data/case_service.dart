import '../../../core/network/api_client.dart';
import '../../auth/data/auth_service.dart';
import 'case_models.dart';

class CaseService {
  final ApiClient _apiClient;

  CaseService({ApiClient? apiClient}) : _apiClient = apiClient ?? ApiClient();

  Future<ApiResponse<CaseModel>> createCase({
    required String title,
    required String description,
    int? categoryId,
    int? departmentId,
    String? ward,
    String? landmark,
    String? address,
    String? priority,
  }) async {
    final token = AuthService.currentToken;
    return _apiClient.post<CaseModel>(
      '/api/v1/cases',
      token: token,
      body: {
        'title': title,
        'description': description,
        'category_id': categoryId,
        'department_id': departmentId,
        'ward': ward,
        'landmark': landmark,
        'address': address,
        'priority': priority ?? 'medium',
      },
      fromJson: (json) => CaseModel.fromJson(json as Map<String, dynamic>),
    );
  }

  Future<ApiResponse<CaseListResponseModel>> listCases({
    String? status,
    String? priority,
    String? severity,
    int? departmentId,
    int? categoryId,
    int? teamId,
    String? ward,
    int? assignedToId,
    int? citizenId,
    String? search,
    bool? isOverdue,
    bool? isAtRisk,
    String sortBy = 'created_at',
    String sortOrder = 'desc',
    int page = 1,
    int size = 50,
  }) async {
    final token = AuthService.currentToken;
    final queryParams = <String, String>{
      'page': page.toString(),
      'size': size.toString(),
      'sort_by': sortBy,
      'sort_order': sortOrder,
    };
    if (status != null && status.isNotEmpty) queryParams['status'] = status;
    if (priority != null && priority.isNotEmpty) queryParams['priority'] = priority;
    if (severity != null && severity.isNotEmpty) queryParams['severity'] = severity;
    if (departmentId != null) queryParams['department_id'] = departmentId.toString();
    if (categoryId != null) queryParams['category_id'] = categoryId.toString();
    if (teamId != null) queryParams['team_id'] = teamId.toString();
    if (ward != null && ward.isNotEmpty) queryParams['ward'] = ward;
    if (assignedToId != null) queryParams['assigned_to_id'] = assignedToId.toString();
    if (citizenId != null) queryParams['citizen_id'] = citizenId.toString();
    if (search != null && search.isNotEmpty) queryParams['search'] = search;
    if (isOverdue != null) queryParams['is_overdue'] = isOverdue.toString();
    if (isAtRisk != null) queryParams['is_at_risk'] = isAtRisk.toString();

    final queryString = Uri(queryParameters: queryParams).query;
    return _apiClient.get<CaseListResponseModel>(
      '/api/v1/cases?$queryString',
      token: token,
      fromJson: (json) => CaseListResponseModel.fromJson(json as Map<String, dynamic>),
    );
  }

  Future<ApiResponse<UnifiedTimelineResponseModel>> getUnifiedTimeline(int caseId) async {
    final token = AuthService.currentToken;
    return _apiClient.get<UnifiedTimelineResponseModel>(
      '/api/v1/cases/$caseId/timeline',
      token: token,
      fromJson: (json) => UnifiedTimelineResponseModel.fromJson(json as Map<String, dynamic>),
    );
  }


  Future<ApiResponse<CaseModel>> getCaseDetails(int caseId) async {
    final token = AuthService.currentToken;
    return _apiClient.get<CaseModel>(
      '/api/v1/cases/$caseId',
      token: token,
      fromJson: (json) => CaseModel.fromJson(json as Map<String, dynamic>),
    );
  }

  Future<ApiResponse<CaseModel>> updateStatus({
    required int caseId,
    required String newStatus,
    String? reason,
    String? resolutionNotes,
  }) async {
    final token = AuthService.currentToken;
    final uri = '/api/v1/cases/$caseId/status';
    final res = await _apiClient.post<CaseModel>(
      uri,
      token: token,
      body: {
        'new_status': newStatus,
        'reason': reason,
        'resolution_notes': resolutionNotes,
      },
      fromJson: (json) => CaseModel.fromJson(json as Map<String, dynamic>),
    );
    return res;
  }

  Future<ApiResponse<CaseModel>> confirmResolution(int caseId, {String? notes}) async {
    final token = AuthService.currentToken;
    return _apiClient.post<CaseModel>(
      '/api/v1/cases/$caseId/confirm-resolution',
      token: token,
      body: {'notes': notes},
      fromJson: (json) => CaseModel.fromJson(json as Map<String, dynamic>),
    );
  }

  Future<ApiResponse<CaseModel>> rejectResolution(int caseId, {required String rejectionReason}) async {
    final token = AuthService.currentToken;
    return _apiClient.post<CaseModel>(
      '/api/v1/cases/$caseId/reject-resolution',
      token: token,
      body: {'rejection_reason': rejectionReason},
      fromJson: (json) => CaseModel.fromJson(json as Map<String, dynamic>),
    );
  }
}

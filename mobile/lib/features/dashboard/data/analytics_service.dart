import '../../../core/network/api_client.dart';
import '../../auth/data/auth_service.dart';
import 'analytics_models.dart';

class AnalyticsService {
  final ApiClient _apiClient;

  AnalyticsService({ApiClient? apiClient}) : _apiClient = apiClient ?? ApiClient();

  Future<ApiResponse<ManagerAnalyticsModel>> getManagerAnalytics({int? departmentId, int days = 30}) async {
    final token = AuthService.currentToken;
    String url = '/api/v1/analytics/manager?days=$days';
    if (departmentId != null) url += '&department_id=$departmentId';

    return await _apiClient.get<ManagerAnalyticsModel>(
      url,
      token: token,
      fromJson: (json) => ManagerAnalyticsModel.fromJson(json as Map<String, dynamic>),
    );
  }

  Future<ApiResponse<TeamLeadAnalyticsModel>> getTeamLeadAnalytics() async {
    final token = AuthService.currentToken;
    return await _apiClient.get<TeamLeadAnalyticsModel>(
      '/api/v1/analytics/team-lead',
      token: token,
      fromJson: (json) => TeamLeadAnalyticsModel.fromJson(json as Map<String, dynamic>),
    );
  }

  Future<ApiResponse<OperatorAnalyticsModel>> getOperatorAnalytics() async {
    final token = AuthService.currentToken;
    return await _apiClient.get<OperatorAnalyticsModel>(
      '/api/v1/analytics/operator',
      token: token,
      fromJson: (json) => OperatorAnalyticsModel.fromJson(json as Map<String, dynamic>),
    );
  }

  Future<ApiResponse<CitizenAnalyticsModel>> getCitizenAnalytics() async {
    final token = AuthService.currentToken;
    return await _apiClient.get<CitizenAnalyticsModel>(
      '/api/v1/analytics/citizen',
      token: token,
      fromJson: (json) => CitizenAnalyticsModel.fromJson(json as Map<String, dynamic>),
    );
  }

  Future<ApiResponse<SystemStatsModel>> getSystemStats() async {
    final token = AuthService.currentToken;
    return await _apiClient.get<SystemStatsModel>(
      '/api/v1/admin/system-stats',
      token: token,
      fromJson: (json) => SystemStatsModel.fromJson(json as Map<String, dynamic>),
    );
  }

  Future<ApiResponse<List<AuditLogEntryModel>>> getAuditLogs({int limit = 50, int offset = 0}) async {
    final token = AuthService.currentToken;
    return await _apiClient.get<List<AuditLogEntryModel>>(
      '/api/v1/admin/audit-logs?limit=$limit&offset=$offset',
      token: token,
      fromJson: (json) {
        final list = json as List<dynamic>? ?? [];
        return list.map((e) => AuditLogEntryModel.fromJson(e as Map<String, dynamic>)).toList();
      },
    );
  }
}

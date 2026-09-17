import '../../../core/network/api_client.dart';
import '../../auth/data/auth_service.dart';
import 'sla_models.dart';

class SLAService {
  final ApiClient _apiClient;

  SLAService({ApiClient? apiClient}) : _apiClient = apiClient ?? ApiClient();

  Future<ApiResponse<CaseSLAModel>> getCaseSLA(int caseId) async {
    final token = AuthService.currentToken;
    return _apiClient.get<CaseSLAModel>(
      '/api/v1/cases/$caseId/sla',
      token: token,
      fromJson: (json) => CaseSLAModel.fromJson(json as Map<String, dynamic>),
    );
  }

  Future<ApiResponse<CaseSLAModel>> recalculateCaseSLA(int caseId) async {
    final token = AuthService.currentToken;
    return _apiClient.post<CaseSLAModel>(
      '/api/v1/cases/$caseId/sla/recalculate',
      token: token,
      body: {},
      fromJson: (json) => CaseSLAModel.fromJson(json as Map<String, dynamic>),
    );
  }

  Future<ApiResponse<RiskAnalysisModel>> getCaseRisk(int caseId) async {
    final token = AuthService.currentToken;
    return _apiClient.get<RiskAnalysisModel>(
      '/api/v1/cases/$caseId/risk',
      token: token,
      fromJson: (json) => RiskAnalysisModel.fromJson(json as Map<String, dynamic>),
    );
  }

  Future<ApiResponse<List<EscalationModel>>> getCaseEscalations(int caseId) async {
    final token = AuthService.currentToken;
    return _apiClient.get<List<EscalationModel>>(
      '/api/v1/cases/$caseId/escalations',
      token: token,
      fromJson: (json) => (json as List).map((e) => EscalationModel.fromJson(e as Map<String, dynamic>)).toList(),
    );
  }

  Future<ApiResponse<EscalationModel>> createEscalation(
    int caseId, {
    required String reason,
    String triggerType = 'operator_request',
    int? escalatedToId,
  }) async {
    final token = AuthService.currentToken;
    return _apiClient.post<EscalationModel>(
      '/api/v1/cases/$caseId/escalations',
      token: token,
      body: {
        'reason': reason,
        'trigger_type': triggerType,
        if (escalatedToId != null) 'escalated_to_id': escalatedToId,
      },
      fromJson: (json) => EscalationModel.fromJson(json as Map<String, dynamic>),
    );
  }

  Future<ApiResponse<EscalationModel>> updateEscalation(
    int caseId,
    int escalationId, {
    required String status,
    String? resolutionNotes,
  }) async {
    final token = AuthService.currentToken;
    return _apiClient.patch<EscalationModel>(
      '/api/v1/cases/$caseId/escalations/$escalationId',
      token: token,
      body: {
        'status': status,
        if (resolutionNotes != null) 'resolution_notes': resolutionNotes,
      },
      fromJson: (json) => EscalationModel.fromJson(json as Map<String, dynamic>),
    );
  }

  Future<ApiResponse<List<EscalationModel>>> getAllEscalations({String? status}) async {
    final token = AuthService.currentToken;
    final query = status != null ? '?status=$status' : '';
    return _apiClient.get<List<EscalationModel>>(
      '/api/v1/escalations$query',
      token: token,
      fromJson: (json) => (json as List).map((e) => EscalationModel.fromJson(e as Map<String, dynamic>)).toList(),
    );
  }

  Future<ApiResponse<Map<String, dynamic>>> triggerAutomationSweep() async {
    final token = AuthService.currentToken;
    return _apiClient.post<Map<String, dynamic>>(
      '/api/v1/automation/sweep-slas-and-risks',
      token: token,
      body: {},
      fromJson: (json) => json as Map<String, dynamic>,
    );
  }
}

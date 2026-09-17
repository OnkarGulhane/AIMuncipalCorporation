import '../../../core/network/api_client.dart';
import '../../auth/data/auth_service.dart';
import 'case_models.dart';
import 'ai_models.dart';

class AIService {
  final ApiClient _apiClient;

  AIService({ApiClient? apiClient}) : _apiClient = apiClient ?? ApiClient();

  Future<ApiResponse<AIAnalysisModel>> getAnalysis(int caseId) async {
    final token = AuthService.currentToken;
    return _apiClient.get<AIAnalysisModel>(
      '/api/v1/cases/$caseId/ai-analysis',
      token: token,
      fromJson: (json) => AIAnalysisModel.fromJson(json as Map<String, dynamic>),
    );
  }

  Future<ApiResponse<AIAnalysisModel>> runAnalysis(int caseId) async {
    final token = AuthService.currentToken;
    return _apiClient.post<AIAnalysisModel>(
      '/api/v1/cases/$caseId/ai-analysis',
      token: token,
      body: {},
      fromJson: (json) => AIAnalysisModel.fromJson(json as Map<String, dynamic>),
    );
  }

  Future<ApiResponse<CaseModel>> applySuggestions(
    int caseId, {
    bool applyCategory = true,
    bool applyPriority = true,
    bool applyTeam = true,
  }) async {
    final token = AuthService.currentToken;
    return _apiClient.post<CaseModel>(
      '/api/v1/cases/$caseId/ai/apply-suggestions',
      token: token,
      body: {
        'apply_category': applyCategory,
        'apply_priority': applyPriority,
        'apply_team': applyTeam,
      },
      fromJson: (json) => CaseModel.fromJson(json as Map<String, dynamic>),
    );
  }

  Future<ApiResponse<AIDraftModel>> generateDraft(
    int caseId, {
    required String draftType,
    String? contextNotes,
  }) async {
    final token = AuthService.currentToken;
    return _apiClient.post<AIDraftModel>(
      '/api/v1/cases/$caseId/ai/draft-communication',
      token: token,
      body: {
        'draft_type': draftType,
        'context_notes': contextNotes,
      },
      fromJson: (json) => AIDraftModel.fromJson(json as Map<String, dynamic>),
    );
  }

  Future<ApiResponse<AICaseSummaryModel>> getCaseSummary(int caseId) async {
    final token = AuthService.currentToken;
    return _apiClient.get<AICaseSummaryModel>(
      '/api/v1/cases/$caseId/summary',
      token: token,
      fromJson: (json) => AICaseSummaryModel.fromJson(json as Map<String, dynamic>),
    );
  }
}

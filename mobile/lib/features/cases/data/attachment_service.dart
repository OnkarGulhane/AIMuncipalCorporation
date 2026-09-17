import '../../../core/network/api_client.dart';
import '../../auth/data/auth_service.dart';
import 'attachment_models.dart';

class AttachmentService {
  final ApiClient _apiClient;

  AttachmentService({ApiClient? apiClient}) : _apiClient = apiClient ?? ApiClient();

  Future<ApiResponse<List<CaseAttachmentModel>>> getAttachments(int caseId) async {
    final token = AuthService.currentToken;
    return _apiClient.get<List<CaseAttachmentModel>>(
      '/api/v1/cases/$caseId/attachments',
      token: token,
      fromJson: (json) {
        final list = json as List<dynamic>;
        return list
            .map((item) => CaseAttachmentModel.fromJson(item as Map<String, dynamic>))
            .toList();
      },
    );
  }

  Future<ApiResponse<void>> deleteAttachment(int caseId, int attachmentId) async {
    final token = AuthService.currentToken;
    return _apiClient.delete<void>(
      '/api/v1/cases/$caseId/attachments/$attachmentId',
      token: token,
      fromJson: (_) {},
    );
  }

  String getDownloadUrl(int caseId, int attachmentId) {
    return '${_apiClient.baseUrl}/api/v1/cases/$caseId/attachments/$attachmentId/download';
  }
}

import '../../../core/network/api_client.dart';
import '../../auth/data/auth_service.dart';
import 'notification_models.dart';

class NotificationService {
  final ApiClient _apiClient;

  NotificationService({ApiClient? apiClient}) : _apiClient = apiClient ?? ApiClient();

  Future<ApiResponse<NotificationListResponse>> getNotifications({
    bool unreadOnly = false,
    int page = 1,
    int size = 50,
  }) async {
    final token = AuthService.currentToken;
    return await _apiClient.get<NotificationListResponse>(
      '/api/v1/notifications?unread_only=$unreadOnly&page=$page&size=$size',
      token: token,
      fromJson: (json) => NotificationListResponse.fromJson(json as Map<String, dynamic>),
    );
  }

  Future<ApiResponse<int>> getUnreadCount() async {
    final token = AuthService.currentToken;
    return await _apiClient.get<int>(
      '/api/v1/notifications/unread-count',
      token: token,
      fromJson: (json) => (json as Map<String, dynamic>)['unread_count'] as int? ?? 0,
    );
  }

  Future<ApiResponse<NotificationItem>> markAsRead(int notificationId) async {
    final token = AuthService.currentToken;
    return await _apiClient.patch<NotificationItem>(
      '/api/v1/notifications/$notificationId/read',
      token: token,
      fromJson: (json) => NotificationItem.fromJson(json as Map<String, dynamic>),
    );
  }

  Future<ApiResponse<int>> markAllAsRead() async {
    final token = AuthService.currentToken;
    return await _apiClient.post<int>(
      '/api/v1/notifications/mark-all-read',
      token: token,
      fromJson: (json) => (json as Map<String, dynamic>)['marked_read_count'] as int? ?? 0,
    );
  }

  Future<ApiResponse<void>> deleteNotification(int notificationId) async {
    final token = AuthService.currentToken;
    return await _apiClient.delete<void>(
      '/api/v1/notifications/$notificationId',
      token: token,
    );
  }

  Future<ApiResponse<NotificationPreference>> getPreferences() async {
    final token = AuthService.currentToken;
    return await _apiClient.get<NotificationPreference>(
      '/api/v1/notifications/preferences',
      token: token,
      fromJson: (json) => NotificationPreference.fromJson(json as Map<String, dynamic>),
    );
  }

  Future<ApiResponse<NotificationPreference>> updatePreferences(Map<String, dynamic> updates) async {
    final token = AuthService.currentToken;
    return await _apiClient.put<NotificationPreference>(
      '/api/v1/notifications/preferences',
      token: token,
      body: updates,
      fromJson: (json) => NotificationPreference.fromJson(json as Map<String, dynamic>),
    );
  }
}

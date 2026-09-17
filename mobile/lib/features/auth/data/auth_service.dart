import '../../../core/network/api_client.dart';
import 'auth_models.dart';

class AuthService {
  final ApiClient _apiClient;

  // In-memory token cache for state
  static String? _cachedToken;
  static UserModel? _currentUser;

  AuthService({ApiClient? apiClient}) : _apiClient = apiClient ?? ApiClient();

  static String? get currentToken => _cachedToken;
  static UserModel? get currentUser => _currentUser;
  static bool get isAuthenticated => _cachedToken != null && _currentUser != null;

  static void logout() {
    _cachedToken = null;
    _currentUser = null;
  }

  Future<ApiResponse<AuthResponseModel>> register({
    required String fullName,
    required String email,
    required String password,
    String? phoneNumber,
    String? ward,
  }) async {
    final response = await _apiClient.post<AuthResponseModel>(
      '/api/v1/auth/register',
      body: {
        'full_name': fullName,
        'email': email,
        'password': password,
        'phone_number': phoneNumber,
        'ward': ward,
      },
      fromJson: (json) => AuthResponseModel.fromJson(json as Map<String, dynamic>),
    );

    if (response.isSuccess && response.data != null) {
      _cachedToken = response.data!.accessToken;
      _currentUser = response.data!.user;
    }

    return response;
  }

  Future<ApiResponse<AuthResponseModel>> login({
    required String email,
    required String password,
  }) async {
    final response = await _apiClient.post<AuthResponseModel>(
      '/api/v1/auth/login',
      body: {
        'email': email,
        'password': password,
      },
      fromJson: (json) => AuthResponseModel.fromJson(json as Map<String, dynamic>),
    );

    if (response.isSuccess && response.data != null) {
      _cachedToken = response.data!.accessToken;
      _currentUser = response.data!.user;
    }

    return response;
  }

  Future<ApiResponse<UserModel>> getProfile() async {
    if (_cachedToken == null) {
      return ApiResponse(
        isSuccess: false,
        errorMessage: 'Not authenticated',
        statusCode: 401,
      );
    }

    final response = await _apiClient.get<UserModel>(
      '/api/v1/auth/me',
      token: _cachedToken,
      fromJson: (json) => UserModel.fromJson(json as Map<String, dynamic>),
    );

    if (response.isSuccess && response.data != null) {
      _currentUser = response.data;
    }

    return response;
  }
}

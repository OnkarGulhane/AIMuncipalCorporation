class AppConfig {
  static const String appName = 'AI Case Manager';
  static const String appVersion = '1.0.0';

  // API Base URL (Configurable for emulator / local device / production)
  // For Android emulator: http://10.0.2.2:8000
  // For Windows / Web / iOS simulator: http://127.0.0.1:8000
  static const String baseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://127.0.0.1:8000',
  );

  static const String apiV1Prefix = '/api/v1';

  static const Duration requestTimeout = Duration(seconds: 15);
}

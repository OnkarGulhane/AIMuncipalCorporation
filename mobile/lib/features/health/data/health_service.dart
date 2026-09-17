import '../../../core/network/api_client.dart';

class SystemHealthInfo {
  final String status;
  final String project;
  final String version;
  final String environment;
  final String timestamp;

  SystemHealthInfo({
    required this.status,
    required this.project,
    required this.version,
    required this.environment,
    required this.timestamp,
  });

  factory SystemHealthInfo.fromJson(Map<String, dynamic> json) {
    return SystemHealthInfo(
      status: json['status'] ?? 'unknown',
      project: json['project'] ?? 'AI Case Manager',
      version: json['version'] ?? '1.0.0',
      environment: json['environment'] ?? 'development',
      timestamp: json['timestamp'] ?? '',
    );
  }
}

class SystemReadyInfo {
  final String status;
  final String database;
  final String timestamp;

  SystemReadyInfo({
    required this.status,
    required this.database,
    required this.timestamp,
  });

  factory SystemReadyInfo.fromJson(Map<String, dynamic> json) {
    return SystemReadyInfo(
      status: json['status'] ?? 'unknown',
      database: json['database'] ?? 'unknown',
      timestamp: json['timestamp'] ?? '',
    );
  }
}

class HealthService {
  final ApiClient _apiClient;

  HealthService({ApiClient? apiClient}) : _apiClient = apiClient ?? ApiClient();

  Future<ApiResponse<SystemHealthInfo>> checkLiveness() async {
    return _apiClient.get<SystemHealthInfo>(
      '/health',
      fromJson: (json) => SystemHealthInfo.fromJson(json as Map<String, dynamic>),
    );
  }

  Future<ApiResponse<SystemReadyInfo>> checkReadiness() async {
    return _apiClient.get<SystemReadyInfo>(
      '/ready',
      fromJson: (json) => SystemReadyInfo.fromJson(json as Map<String, dynamic>),
    );
  }
}

import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import '../config/app_config.dart';

class ApiResponse<T> {
  final bool isSuccess;
  final T? data;
  final String? errorMessage;
  final int statusCode;

  ApiResponse({
    required this.isSuccess,
    this.data,
    this.errorMessage,
    required this.statusCode,
  });
}

class ApiClient {
  final http.Client _client;
  final String baseUrl;

  ApiClient({http.Client? client, String? baseUrl})
      : _client = client ?? http.Client(),
        baseUrl = baseUrl ?? AppConfig.baseUrl;

  Map<String, String> _buildHeaders({String? token}) {
    final headers = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    };
    if (token != null && token.isNotEmpty) {
      headers['Authorization'] = 'Bearer $token';
    }
    return headers;
  }

  Future<ApiResponse<T>> get<T>(
    String path, {
    String? token,
    T Function(dynamic json)? fromJson,
  }) async {
    try {
      final uri = Uri.parse('$baseUrl$path');
      final response = await _client
          .get(uri, headers: _buildHeaders(token: token))
          .timeout(AppConfig.requestTimeout);

      return _handleResponse(response, fromJson);
    } on SocketException {
      return ApiResponse(
        isSuccess: false,
        errorMessage: 'Network error: Cannot reach the server. Please check your connection.',
        statusCode: 0,
      );
    } on TimeoutException {
      return ApiResponse(
        isSuccess: false,
        errorMessage: 'Connection timed out. The server took too long to respond.',
        statusCode: 408,
      );
    } catch (e) {
      return ApiResponse(
        isSuccess: false,
        errorMessage: 'An unexpected error occurred: ${e.toString()}',
        statusCode: -1,
      );
    }
  }

  Future<ApiResponse<T>> post<T>(
    String path, {
    Map<String, dynamic>? body,
    String? token,
    T Function(dynamic json)? fromJson,
  }) async {
    try {
      final uri = Uri.parse('$baseUrl$path');
      final response = await _client
          .post(
            uri,
            headers: _buildHeaders(token: token),
            body: body != null ? jsonEncode(body) : null,
          )
          .timeout(AppConfig.requestTimeout);

      return _handleResponse(response, fromJson);
    } on SocketException {
      return ApiResponse(
        isSuccess: false,
        errorMessage: 'Network error: Cannot reach the server. Please check your connection.',
        statusCode: 0,
      );
    } on TimeoutException {
      return ApiResponse(
        isSuccess: false,
        errorMessage: 'Connection timed out. The server took too long to respond.',
        statusCode: 408,
      );
    } catch (e) {
      return ApiResponse(
        isSuccess: false,
        errorMessage: 'An unexpected error occurred: ${e.toString()}',
        statusCode: -1,
      );
    }
  }

  ApiResponse<T> _handleResponse<T>(
    http.Response response,
    T Function(dynamic json)? fromJson,
  ) {
    if (response.statusCode >= 200 && response.statusCode < 300) {
      try {
        final decoded = response.body.isNotEmpty ? jsonDecode(response.body) : null;
        final data = fromJson != null && decoded != null ? fromJson(decoded) : decoded as T?;
        return ApiResponse(
          isSuccess: true,
          data: data,
          statusCode: response.statusCode,
        );
      } catch (e) {
        return ApiResponse(
          isSuccess: false,
          errorMessage: 'Failed to parse server response.',
          statusCode: response.statusCode,
        );
      }
    } else {
      String errorMessage = 'Server returned error status ${response.statusCode}';
      try {
        final decoded = jsonDecode(response.body);
        if (decoded is Map && decoded.containsKey('detail')) {
          final detail = decoded['detail'];
          errorMessage = detail is String ? detail : jsonEncode(detail);
        }
      } catch (_) {}
      return ApiResponse(
        isSuccess: false,
        errorMessage: errorMessage,
        statusCode: response.statusCode,
      );
    }
  }
}

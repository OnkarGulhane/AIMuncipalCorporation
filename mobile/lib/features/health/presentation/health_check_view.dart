import 'package:flutter/material.dart';
import '../../../core/config/app_config.dart';
import '../../../core/theme/app_colors.dart';
import '../data/health_service.dart';

class HealthCheckView extends StatefulWidget {
  const HealthCheckView({super.key});

  @override
  State<HealthCheckView> createState() => _HealthCheckViewState();
}

class _HealthCheckViewState extends State<HealthCheckView> {
  final HealthService _healthService = HealthService();
  bool _isLoading = false;
  SystemHealthInfo? _healthInfo;
  SystemReadyInfo? _readyInfo;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _checkBackendHealth();
  }

  Future<void> _checkBackendHealth() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    final healthRes = await _healthService.checkLiveness();
    final readyRes = await _healthService.checkReadiness();

    if (!mounted) return;

    setState(() {
      _isLoading = false;
      if (healthRes.isSuccess && readyRes.isSuccess) {
        _healthInfo = healthRes.data;
        _readyInfo = readyRes.data;
        _errorMessage = null;
      } else {
        _errorMessage = healthRes.errorMessage ?? readyRes.errorMessage ?? 'Connection failed';
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('AI Case Manager'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            tooltip: 'Ping Backend',
            onPressed: _isLoading ? null : _checkBackendHealth,
          ),
        ],
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(20.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Header Card
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(
                  gradient: const LinearGradient(
                    colors: [AppColors.primary, AppColors.primaryDark],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                  borderRadius: BorderRadius.circular(16),
                  boxShadow: [
                    BoxShadow(
                      color: AppColors.primary.withOpacity(0.2),
                      blurRadius: 10,
                      offset: const Offset(0, 4),
                    ),
                  ],
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Municipal Case Management',
                      style: TextStyle(
                        color: Colors.white70,
                        fontSize: 14,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                    const SizedBox(height: 6),
                    const Text(
                      'System Foundation (Phase 1)',
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 22,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 12),
                    Text(
                      'API Host: ${AppConfig.baseUrl}',
                      style: const TextStyle(
                        color: Colors.white60,
                        fontSize: 12,
                        fontFamily: 'monospace',
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 24),

              const Text(
                'Foundation Status',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.w600,
                  color: AppColors.textPrimary,
                ),
              ),
              const SizedBox(height: 12),

              if (_isLoading)
                const Center(
                  child: Padding(
                    padding: EdgeInsets.symmetric(vertical: 40),
                    child: CircularProgressIndicator(),
                  ),
                )
              else if (_errorMessage != null)
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: AppColors.statusError.withOpacity(0.08),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: AppColors.statusError.withOpacity(0.3)),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Row(
                        children: [
                          Icon(Icons.error_outline, color: AppColors.statusError),
                          SizedBox(width: 8),
                          Text(
                            'Backend Disconnected',
                            style: TextStyle(
                              color: AppColors.statusError,
                              fontWeight: FontWeight.bold,
                              fontSize: 16,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 8),
                      Text(
                        _errorMessage!,
                        style: const TextStyle(
                          color: AppColors.textPrimary,
                          fontSize: 14,
                        ),
                      ),
                      const SizedBox(height: 12),
                      ElevatedButton.icon(
                        onPressed: _checkBackendHealth,
                        icon: const Icon(Icons.refresh, size: 18),
                        label: const Text('Retry Connection'),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: AppColors.statusError,
                        ),
                      ),
                    ],
                  ),
                )
              else if (_healthInfo != null && _readyInfo != null)
                Column(
                  children: [
                    _buildStatusCard(
                      title: 'FastAPI Backend',
                      subtitle: '${_healthInfo!.project} v${_healthInfo!.version}',
                      status: _healthInfo!.status.toUpperCase(),
                      isOk: _healthInfo!.status == 'healthy',
                      icon: Icons.api,
                    ),
                    const SizedBox(height: 12),
                    _buildStatusCard(
                      title: 'Database Connectivity',
                      subtitle: 'PostgreSQL / Supabase Engine Ready',
                      status: _readyInfo!.database.toUpperCase(),
                      isOk: _readyInfo!.database == 'connected',
                      icon: Icons.storage,
                    ),
                  ],
                ),

              const Spacer(),
              Center(
                child: Text(
                  'Phase 1 Architecture Baseline Verified',
                  style: TextStyle(
                    fontSize: 12,
                    color: AppColors.textMuted,
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildStatusCard({
    required String title,
    required String subtitle,
    required String status,
    required bool isOk,
    required IconData icon,
  }) {
    final statusColor = isOk ? AppColors.statusSuccess : AppColors.statusError;

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.border),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(
              color: statusColor.withOpacity(0.1),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Icon(icon, color: statusColor, size: 24),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: const TextStyle(
                    fontWeight: FontWeight.w600,
                    fontSize: 15,
                    color: AppColors.textPrimary,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  subtitle,
                  style: const TextStyle(
                    fontSize: 13,
                    color: AppColors.textSecondary,
                  ),
                ),
              ],
            ),
          ),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
            decoration: BoxDecoration(
              color: statusColor.withOpacity(0.12),
              borderRadius: BorderRadius.circular(20),
            ),
            child: Text(
              status,
              style: TextStyle(
                color: statusColor,
                fontWeight: FontWeight.bold,
                fontSize: 12,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

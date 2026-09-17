import 'package:flutter/material.dart';
import '../theme/app_colors.dart';

class AppErrorState extends StatelessWidget {
  final String title;
  final String message;
  final String? actionHint;
  final VoidCallback? onRetry;
  final VoidCallback? onGoBack;
  final bool isCompact;

  const AppErrorState({
    super.key,
    this.title = 'Something Went Wrong',
    required this.message,
    this.actionHint,
    this.onRetry,
    this.onGoBack,
    this.isCompact = false,
  });

  factory AppErrorState.networkError({VoidCallback? onRetry}) {
    return AppErrorState(
      title: 'Connection Unavailable',
      message: 'Unable to reach the municipal server. Please check your internet connection.',
      actionHint: 'Check your Wi-Fi or mobile data, then tap Retry below.',
      onRetry: onRetry,
    );
  }

  factory AppErrorState.permissionDenied({VoidCallback? onContactAdmin}) {
    return AppErrorState(
      title: 'Access Restricted',
      message: 'You do not have permission to view this department or perform this administrative action.',
      actionHint: 'Please contact your departmental administrator if you require elevated privileges.',
      onRetry: onContactAdmin,
    );
  }

  static Widget degradedAiBanner({VoidCallback? onRefresh}) {
    return Container(
      margin: const EdgeInsets.symmetric(vertical: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: const Color(0xFFFFFBEB), // Amber 50
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: const Color(0xFFFDE68A)), // Amber 200
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(Icons.info_outline_rounded, color: AppColors.statusWarning, size: 20),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'AI Insights Temporarily Unavailable',
                  style: TextStyle(
                    fontWeight: FontWeight.bold,
                    fontSize: 13,
                    color: Color(0xFF92400E),
                  ),
                ),
                const SizedBox(height: 2),
                const Text(
                  'Core municipal case triage and assignment remains active. Automated analysis will resume shortly.',
                  style: TextStyle(
                    fontSize: 12,
                    color: Color(0xFFB45309),
                  ),
                ),
              ],
            ),
          ),
          if (onRefresh != null) ...[
            const SizedBox(width: 8),
            IconButton(
              icon: const Icon(Icons.refresh, size: 18, color: Color(0xFF92400E)),
              onPressed: onRefresh,
              tooltip: 'Retry AI Analysis',
              constraints: const BoxConstraints(),
              padding: EdgeInsets.zero,
            ),
          ],
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    if (isCompact) {
      return Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: AppColors.statusError.withOpacity(0.08),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: AppColors.statusError.withOpacity(0.2)),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.error_outline_rounded, color: AppColors.statusError, size: 20),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    title,
                    style: const TextStyle(fontWeight: FontWeight.bold, color: AppColors.statusError),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 6),
            Text(message, style: const TextStyle(fontSize: 13, color: AppColors.textPrimary)),
            if (actionHint != null) ...[
              const SizedBox(height: 4),
              Text(
                actionHint!,
                style: const TextStyle(fontSize: 12, color: AppColors.textSecondary, fontStyle: FontStyle.italic),
              ),
            ],
            if (onRetry != null) ...[
              const SizedBox(height: 10),
              Align(
                alignment: Alignment.centerRight,
                child: TextButton.icon(
                  onPressed: onRetry,
                  icon: const Icon(Icons.refresh, size: 16),
                  label: const Text('Retry'),
                  style: TextButton.styleFrom(
                    foregroundColor: AppColors.statusError,
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                  ),
                ),
              ),
            ],
          ],
        ),
      );
    }

    final theme = Theme.of(context);
    return Center(
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 32.0, vertical: 48.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: AppColors.statusError.withOpacity(0.1),
                shape: BoxShape.circle,
              ),
              child: const Icon(
                Icons.warning_amber_rounded,
                size: 52,
                color: AppColors.statusError,
              ),
            ),
            const SizedBox(height: 20),
            Text(
              title,
              textAlign: TextAlign.center,
              style: theme.textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.bold,
                color: AppColors.textPrimary,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              message,
              textAlign: TextAlign.center,
              style: theme.textTheme.bodyMedium?.copyWith(
                color: AppColors.textSecondary,
                height: 1.4,
              ),
            ),
            if (actionHint != null) ...[
              const SizedBox(height: 8),
              Text(
                actionHint!,
                textAlign: TextAlign.center,
                style: theme.textTheme.bodySmall?.copyWith(
                  color: AppColors.textMuted,
                  fontStyle: FontStyle.italic,
                ),
              ),
            ],
            const SizedBox(height: 24),
            Wrap(
              spacing: 12,
              runSpacing: 12,
              alignment: WrapAlignment.center,
              children: [
                if (onRetry != null)
                  FilledButton.icon(
                    onPressed: onRetry,
                    icon: const Icon(Icons.refresh, size: 18),
                    label: const Text('Retry'),
                    style: FilledButton.styleFrom(
                      backgroundColor: AppColors.primary,
                      foregroundColor: Colors.white,
                      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                    ),
                  ),
                if (onGoBack != null)
                  OutlinedButton(
                    onPressed: onGoBack,
                    style: OutlinedButton.styleFrom(
                      foregroundColor: AppColors.textPrimary,
                      side: const BorderSide(color: AppColors.border),
                      padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 12),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                    ),
                    child: const Text('Go Back'),
                  ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

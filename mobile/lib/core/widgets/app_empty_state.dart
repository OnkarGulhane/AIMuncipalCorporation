import 'package:flutter/material.dart';
import '../theme/app_colors.dart';

class AppEmptyState extends StatelessWidget {
  final IconData icon;
  final String title;
  final String description;
  final String? primaryActionLabel;
  final VoidCallback? onPrimaryAction;
  final String? secondaryActionLabel;
  final VoidCallback? onSecondaryAction;
  final Color? iconColor;

  const AppEmptyState({
    super.key,
    required this.icon,
    required this.title,
    required this.description,
    this.primaryActionLabel,
    this.onPrimaryAction,
    this.secondaryActionLabel,
    this.onSecondaryAction,
    this.iconColor,
  });

  factory AppEmptyState.noCases({VoidCallback? onReportComplaint}) {
    return AppEmptyState(
      icon: Icons.assignment_outlined,
      title: 'No Active Complaints',
      description: 'There are no active municipal complaints to display at this time.',
      primaryActionLabel: onReportComplaint != null ? 'Report a Complaint' : null,
      onPrimaryAction: onReportComplaint,
      iconColor: AppColors.primary,
    );
  }

  factory AppEmptyState.noSearchResults({
    VoidCallback? onClearFilters,
    VoidCallback? onBroadenSearch,
  }) {
    return AppEmptyState(
      icon: Icons.search_off_rounded,
      title: 'No Matching Results',
      description: 'We could not find any complaints matching your criteria. Try adjusting keywords or clearing active filters.',
      primaryActionLabel: onClearFilters != null ? 'Clear All Filters' : null,
      onPrimaryAction: onClearFilters,
      secondaryActionLabel: onBroadenSearch != null ? 'Broaden Search' : null,
      onSecondaryAction: onBroadenSearch,
      iconColor: AppColors.textMuted,
    );
  }

  factory AppEmptyState.noTasks({VoidCallback? onAddTask}) {
    return AppEmptyState(
      icon: Icons.task_alt_rounded,
      title: 'No Active Tasks',
      description: 'All field tasks have been completed or none are currently scheduled for this case.',
      primaryActionLabel: onAddTask != null ? 'Create Field Task' : null,
      onPrimaryAction: onAddTask,
      iconColor: AppColors.secondary,
    );
  }

  factory AppEmptyState.noNotifications({VoidCallback? onRefresh}) {
    return AppEmptyState(
      icon: Icons.notifications_none_rounded,
      title: "You're All Caught Up!",
      description: 'There are no new alerts, status updates, or notifications at this moment.',
      primaryActionLabel: onRefresh != null ? 'Refresh Inbox' : null,
      onPrimaryAction: onRefresh,
      iconColor: AppColors.accent,
    );
  }

  factory AppEmptyState.noRelatedCases() {
    return const AppEmptyState(
      icon: Icons.hub_outlined,
      title: 'No Duplicate Cases Detected',
      description: 'AI triage did not identify any similar or duplicate complaints in this ward.',
      iconColor: AppColors.statusSuccess,
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Center(
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 32.0, vertical: 48.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          crossAxisAlignment: CrossAxisAlignment.center,
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: (iconColor ?? AppColors.primary).withOpacity(0.08),
                shape: BoxShape.circle,
              ),
              child: Icon(
                icon,
                size: 52,
                color: iconColor ?? AppColors.primary,
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
              description,
              textAlign: TextAlign.center,
              style: theme.textTheme.bodyMedium?.copyWith(
                color: AppColors.textSecondary,
                height: 1.4,
              ),
            ),
            if (primaryActionLabel != null || secondaryActionLabel != null) ...[
              const SizedBox(height: 24),
              Wrap(
                spacing: 12,
                runSpacing: 12,
                alignment: WrapAlignment.center,
                children: [
                  if (primaryActionLabel != null && onPrimaryAction != null)
                    FilledButton(
                      onPressed: onPrimaryAction,
                      style: FilledButton.styleFrom(
                        backgroundColor: AppColors.primary,
                        foregroundColor: Colors.white,
                        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                      ),
                      child: Text(primaryActionLabel!),
                    ),
                  if (secondaryActionLabel != null && onSecondaryAction != null)
                    OutlinedButton(
                      onPressed: onSecondaryAction,
                      style: OutlinedButton.styleFrom(
                        foregroundColor: AppColors.primary,
                        side: const BorderSide(color: AppColors.border),
                        padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 12),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                      ),
                      child: Text(secondaryActionLabel!),
                    ),
                ],
              ),
            ],
          ],
        ),
      ),
    );
  }
}

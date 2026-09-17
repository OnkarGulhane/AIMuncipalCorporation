import 'package:flutter/material.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/widgets/app_empty_state.dart';
import '../../../core/widgets/app_error_state.dart';
import '../data/case_models.dart';
import '../data/case_service.dart';

class CaseTimelineWidget extends StatefulWidget {
  final int caseId;

  const CaseTimelineWidget({super.key, required this.caseId});

  @override
  State<CaseTimelineWidget> createState() => _CaseTimelineWidgetState();
}

class _CaseTimelineWidgetState extends State<CaseTimelineWidget> {
  final CaseService _caseService = CaseService();
  bool _isLoading = true;
  String? _errorMessage;
  UnifiedTimelineResponseModel? _timelineData;

  @override
  void initState() {
    super.initState();
    _fetchTimeline();
  }

  Future<void> _fetchTimeline() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    final res = await _caseService.getUnifiedTimeline(widget.caseId);
    if (mounted) {
      setState(() {
        _isLoading = false;
        if (res.isSuccess && res.data != null) {
          _timelineData = res.data;
        } else {
          _errorMessage = res.errorMessage ?? 'Failed to load case timeline.';
        }
      });
    }
  }

  IconData _getEventIcon(String eventType) {
    switch (eventType.toLowerCase()) {
      case 'case_created':
        return Icons.add_circle_outline_rounded;
      case 'status_change':
        return Icons.sync_alt_rounded;
      case 'citizen_message':
        return Icons.person_outline_rounded;
      case 'staff_update':
        return Icons.support_agent_rounded;
      case 'internal_note':
        return Icons.lock_outline_rounded;
      case 'task_completed':
        return Icons.check_circle_outline_rounded;
      case 'task_pending':
      case 'task_in_progress':
        return Icons.playlist_add_check_rounded;
      case 'investigation':
        return Icons.policy_outlined;
      case 'escalation':
        return Icons.priority_high_rounded;
      case 'attachment':
        return Icons.attach_file_rounded;
      case 'ai_analysis':
        return Icons.auto_awesome_rounded;
      case 'resolution_proposed':
        return Icons.flag_outlined;
      case 'resolution_confirmed':
        return Icons.verified_outlined;
      case 'resolution_rejected':
        return Icons.replay_rounded;
      default:
        return Icons.radio_button_checked_rounded;
    }
  }

  Color _getEventColor(String eventType) {
    switch (eventType.toLowerCase()) {
      case 'case_created':
      case 'resolution_confirmed':
      case 'task_completed':
        return AppColors.statusSuccess;
      case 'status_change':
      case 'staff_update':
        return AppColors.primaryLight;
      case 'citizen_message':
        return AppColors.secondary;
      case 'internal_note':
        return Colors.blueGrey;
      case 'escalation':
      case 'resolution_rejected':
        return AppColors.statusError;
      case 'ai_analysis':
        return AppColors.accent;
      case 'resolution_proposed':
      case 'investigation':
        return AppColors.statusWarning;
      default:
        return AppColors.primary;
    }
  }

  String _formatTimestamp(DateTime dt) {
    final now = DateTime.now();
    final difference = now.difference(dt);

    if (difference.inMinutes < 60) {
      return '${difference.inMinutes}m ago';
    } else if (difference.inHours < 24) {
      return '${difference.inHours}h ago';
    } else if (difference.inDays < 7) {
      return '${difference.inDays}d ago';
    } else {
      return '${dt.day}/${dt.month}/${dt.year} ${dt.hour.toString().padLeft(2, '0')}:${dt.minute.toString().padLeft(2, '0')}';
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return const Center(
        child: Padding(
          padding: EdgeInsets.all(32.0),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              CircularProgressIndicator(),
              SizedBox(height: 16),
              Text('Loading timeline events...', style: TextStyle(color: AppColors.textSecondary)),
            ],
          ),
        ),
      );
    }

    if (_errorMessage != null) {
      return AppErrorState(
        message: _errorMessage!,
        onRetry: _fetchTimeline,
        isCompact: true,
      );
    }

    final events = _timelineData?.timeline ?? [];
    if (events.isEmpty) {
      return const AppEmptyState(
        icon: Icons.history_rounded,
        title: 'No Timeline Events',
        description: 'Case lifecycle events will appear here as work progresses.',
      );
    }

    return RefreshIndicator(
      onRefresh: _fetchTimeline,
      child: ListView.builder(
        shrinkWrap: true,
        physics: const NeverScrollableScrollPhysics(),
        itemCount: events.length,
        itemBuilder: (context, index) {
          final event = events[index];
          final isLast = index == events.length - 1;
          final color = _getEventColor(event.eventType);

          return Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Left Column: Node Icon & Vertical Connecting Line
              Column(
                children: [
                  Container(
                    width: 36,
                    height: 36,
                    decoration: BoxDecoration(
                      color: color.withOpacity(0.12),
                      shape: BoxShape.circle,
                      border: Border.all(color: color, width: 2),
                    ),
                    child: Icon(
                      _getEventIcon(event.eventType),
                      size: 18,
                      color: color,
                    ),
                  ),
                  if (!isLast)
                    Container(
                      width: 2,
                      height: 50,
                      color: AppColors.border,
                      margin: const EdgeInsets.symmetric(vertical: 4),
                    ),
                ],
              ),
              const SizedBox(width: 14),

              // Right Column: Event Card Details
              Expanded(
                child: Container(
                  margin: const EdgeInsets.only(bottom: 16),
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: event.isInternal ? const Color(0xFFF1F5F9) : Colors.white,
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(
                      color: event.isInternal ? Colors.blueGrey.withOpacity(0.3) : AppColors.border,
                    ),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Expanded(
                            child: Text(
                              event.title,
                              style: const TextStyle(
                                fontWeight: FontWeight.bold,
                                fontSize: 14,
                                color: AppColors.textPrimary,
                              ),
                            ),
                          ),
                          if (event.isInternal)
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                              decoration: BoxDecoration(
                                color: Colors.blueGrey.withOpacity(0.15),
                                borderRadius: BorderRadius.circular(4),
                              ),
                              child: const Text(
                                'INTERNAL',
                                style: TextStyle(
                                  fontSize: 10,
                                  fontWeight: FontWeight.bold,
                                  color: Colors.blueGrey,
                                ),
                              ),
                            ),
                        ],
                      ),
                      if (event.description != null && event.description!.isNotEmpty) ...[
                        const SizedBox(height: 4),
                        Text(
                          event.description!,
                          style: const TextStyle(fontSize: 13, color: AppColors.textSecondary, height: 1.3),
                        ),
                      ],
                      const SizedBox(height: 8),
                      Row(
                        children: [
                          if (event.actorName != null) ...[
                            Icon(Icons.account_circle_outlined, size: 14, color: AppColors.textMuted),
                            const SizedBox(width: 4),
                            Text(
                              event.actorName!,
                              style: const TextStyle(fontSize: 11, color: AppColors.textSecondary, fontWeight: FontWeight.w500),
                            ),
                            const SizedBox(width: 12),
                          ],
                          Icon(Icons.access_time, size: 14, color: AppColors.textMuted),
                          const SizedBox(width: 4),
                          Text(
                            _formatTimestamp(event.timestamp),
                            style: const TextStyle(fontSize: 11, color: AppColors.textMuted),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ),
            ],
          );
        },
      ),
    );
  }
}

import 'package:flutter/material.dart';
import '../../../core/theme/app_colors.dart';
import '../data/notification_models.dart';
import '../data/notification_service.dart';

class NotificationsScreen extends StatefulWidget {
  const NotificationsScreen({super.key});

  @override
  State<NotificationsScreen> createState() => _NotificationsScreenState();
}

class _NotificationsScreenState extends State<NotificationsScreen> {
  final NotificationService _service = NotificationService();
  bool _isLoading = true;
  bool _unreadOnly = false;
  List<NotificationItem> _notifications = [];
  int _unreadCount = 0;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _loadNotifications();
  }

  Future<void> _loadNotifications() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    final res = await _service.getNotifications(unreadOnly: _unreadOnly);
    if (!mounted) return;

    if (res.isSuccess && res.data != null) {
      setState(() {
        _notifications = res.data!.items;
        _unreadCount = res.data!.unreadCount;
        _isLoading = false;
      });
    } else {
      setState(() {
        _errorMessage = res.errorMessage ?? 'Failed to load notifications.';
        _isLoading = false;
      });
    }
  }

  Future<void> _markAsRead(NotificationItem item) async {
    if (item.isRead) return;
    final res = await _service.markAsRead(item.id);
    if (res.isSuccess && mounted) {
      setState(() {
        _notifications = _notifications.map((n) {
          if (n.id == item.id) {
            return NotificationItem(
              id: n.id,
              userId: n.userId,
              caseId: n.caseId,
              caseNumber: n.caseNumber,
              caseTitle: n.caseTitle,
              title: n.title,
              message: n.message,
              eventType: n.eventType,
              channel: n.channel,
              isRead: true,
              readAt: DateTime.now(),
              deliveryStatus: n.deliveryStatus,
              createdAt: n.createdAt,
            );
          }
          return n;
        }).toList();
        if (_unreadCount > 0) _unreadCount--;
      });
    }
  }

  Future<void> _markAllAsRead() async {
    final res = await _service.markAllAsRead();
    if (res.isSuccess && mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('All notifications marked as read.'),
          backgroundColor: AppColors.secondary,
        ),
      );
      _loadNotifications();
    }
  }

  Future<void> _deleteNotification(NotificationItem item) async {
    final res = await _service.deleteNotification(item.id);
    if (res.isSuccess && mounted) {
      setState(() {
        _notifications.removeWhere((n) => n.id == item.id);
        if (!item.isRead && _unreadCount > 0) _unreadCount--;
      });
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Notification removed.'),
          duration: Duration(seconds: 2),
        ),
      );
    }
  }

  void _showPreferencesSheet() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (_) => _NotificationPreferencesSheet(service: _service),
    );
  }

  IconData _getEventIcon(String eventType) {
    switch (eventType) {
      case 'case_created':
        return Icons.note_add_outlined;
      case 'assignment':
        return Icons.person_add_outlined;
      case 'status_changed':
        return Icons.published_with_changes_outlined;
      case 'information_requested':
        return Icons.help_outline;
      case 'resolution_proposed':
        return Icons.verified_outlined;
      case 'confirmed':
        return Icons.check_circle_outline;
      case 'closed':
        return Icons.lock_outline;
      case 'reopened':
        return Icons.refresh_outlined;
      case 'sla_warning':
        return Icons.timer_outlined;
      case 'escalation':
      case 'escalation_resolved':
        return Icons.warning_amber_rounded;
      case 'citizen_response':
      case 'staff_update':
        return Icons.chat_bubble_outline;
      case 'task_assigned':
        return Icons.task_alt_outlined;
      default:
        return Icons.notifications_none;
    }
  }

  Color _getEventColor(String eventType) {
    switch (eventType) {
      case 'escalation':
      case 'sla_warning':
        return AppColors.accent;
      case 'confirmed':
      case 'closed':
      case 'escalation_resolved':
        return AppColors.secondary;
      case 'resolution_proposed':
      case 'task_assigned':
        return AppColors.primary;
      case 'information_requested':
      case 'reopened':
        return AppColors.warning;
      default:
        return AppColors.primary;
    }
  }

  String _formatTimeAgo(DateTime dt) {
    final diff = DateTime.now().difference(dt);
    if (diff.inSeconds < 60) return 'Just now';
    if (diff.inMinutes < 60) return '${diff.inMinutes}m ago';
    if (diff.inHours < 24) return '${diff.inHours}h ago';
    if (diff.inDays < 7) return '${diff.inDays}d ago';
    return '${dt.day}/${dt.month}/${dt.year}';
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Row(
          children: [
            const Text('Notifications', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
            if (_unreadCount > 0) ...[
              const SizedBox(width: 8),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                decoration: BoxDecoration(
                  color: AppColors.accent,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Text(
                  '$_unreadCount new',
                  style: const TextStyle(color: Colors.white, fontSize: 11, fontWeight: FontWeight.bold),
                ),
              ),
            ],
          ],
        ),
        actions: [
          if (_unreadCount > 0)
            IconButton(
              icon: const Icon(Icons.done_all),
              tooltip: 'Mark all as read',
              onPressed: _markAllAsRead,
            ),
          IconButton(
            icon: const Icon(Icons.tune_rounded),
            tooltip: 'Notification Preferences',
            onPressed: _showPreferencesSheet,
          ),
        ],
      ),
      body: Column(
        children: [
          // Filter Chips
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            child: Row(
              children: [
                FilterChip(
                  label: const Text('All'),
                  selected: !_unreadOnly,
                  onSelected: (val) {
                    if (_unreadOnly) {
                      setState(() => _unreadOnly = false);
                      _loadNotifications();
                    }
                  },
                ),
                const SizedBox(width: 8),
                FilterChip(
                  label: Text('Unread (${_unreadCount})'),
                  selected: _unreadOnly,
                  onSelected: (val) {
                    if (!_unreadOnly) {
                      setState(() => _unreadOnly = true);
                      _loadNotifications();
                    }
                  },
                ),
              ],
            ),
          ),
          const Divider(height: 1),

          // Content List
          Expanded(
            child: _isLoading
                ? const Center(child: CircularProgressIndicator())
                : _errorMessage != null
                    ? Center(
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            const Icon(Icons.error_outline, size: 48, color: AppColors.accent),
                            const SizedBox(height: 12),
                            Text(_errorMessage!, style: const TextStyle(color: AppColors.textMuted)),
                            const SizedBox(height: 12),
                            ElevatedButton(
                              onPressed: _loadNotifications,
                              child: const Text('Retry'),
                            ),
                          ],
                        ),
                      )
                    : _notifications.isEmpty
                        ? Center(
                            child: Column(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                Icon(
                                  _unreadOnly ? Icons.mark_email_read_outlined : Icons.notifications_none,
                                  size: 56,
                                  color: AppColors.textMuted.withOpacity(0.5),
                                ),
                                const SizedBox(height: 12),
                                Text(
                                  _unreadOnly ? 'No unread notifications' : 'No notifications yet',
                                  style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600, color: AppColors.textSecondary),
                                ),
                                const SizedBox(height: 4),
                                const Text(
                                  'You will receive case updates, SLA alerts, and messages here.',
                                  style: TextStyle(fontSize: 12, color: AppColors.textMuted),
                                ),
                              ],
                            ),
                          )
                        : RefreshIndicator(
                            onRefresh: _loadNotifications,
                            child: ListView.separated(
                              padding: const EdgeInsets.symmetric(vertical: 8),
                              itemCount: _notifications.length,
                              separatorBuilder: (_, __) => const Divider(height: 1, indent: 64),
                              itemBuilder: (context, index) {
                                final item = _notifications[index];
                                final iconColor = _getEventColor(item.eventType);

                                return Dismissible(
                                  key: Key('notif_${item.id}'),
                                  direction: DismissDirection.endToStart,
                                  background: Container(
                                    color: AppColors.accent,
                                    alignment: Alignment.centerRight,
                                    padding: const EdgeInsets.symmetric(horizontal: 20),
                                    child: const Icon(Icons.delete_outline, color: Colors.white),
                                  ),
                                  onDismissed: (_) => _deleteNotification(item),
                                  child: InkWell(
                                    onTap: () => _markAsRead(item),
                                    child: Container(
                                      color: item.isRead ? Colors.transparent : AppColors.primary.withOpacity(0.04),
                                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                                      child: Row(
                                        crossAxisAlignment: CrossAxisAlignment.start,
                                        children: [
                                          Container(
                                            padding: const EdgeInsets.all(10),
                                            decoration: BoxDecoration(
                                              color: iconColor.withOpacity(0.12),
                                              shape: BoxShape.circle,
                                            ),
                                            child: Icon(_getEventIcon(item.eventType), color: iconColor, size: 20),
                                          ),
                                          const SizedBox(width: 12),
                                          Expanded(
                                            child: Column(
                                              crossAxisAlignment: CrossAxisAlignment.start,
                                              children: [
                                                Row(
                                                  children: [
                                                    if (item.caseNumber != null) ...[
                                                      Container(
                                                        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                                        decoration: BoxDecoration(
                                                          color: AppColors.surface,
                                                          borderRadius: BorderRadius.circular(4),
                                                          border: Border.all(color: AppColors.border),
                                                        ),
                                                        child: Text(
                                                          item.caseNumber!,
                                                          style: const TextStyle(
                                                            fontSize: 11,
                                                            fontWeight: FontWeight.bold,
                                                            color: AppColors.primary,
                                                          ),
                                                        ),
                                                      ),
                                                      const SizedBox(width: 6),
                                                    ],
                                                    Expanded(
                                                      child: Text(
                                                        item.title,
                                                        style: TextStyle(
                                                          fontSize: 13,
                                                          fontWeight: item.isRead ? FontWeight.w600 : FontWeight.bold,
                                                          color: item.isRead ? AppColors.textPrimary : AppColors.primaryDark,
                                                        ),
                                                        maxLines: 1,
                                                        overflow: TextOverflow.ellipsis,
                                                      ),
                                                    ),
                                                    const SizedBox(width: 6),
                                                    Text(
                                                      _formatTimeAgo(item.createdAt),
                                                      style: const TextStyle(fontSize: 11, color: AppColors.textMuted),
                                                    ),
                                                  ],
                                                ),
                                                const SizedBox(height: 4),
                                                Text(
                                                  item.message,
                                                  style: TextStyle(
                                                    fontSize: 13,
                                                    color: item.isRead ? AppColors.textSecondary : AppColors.textPrimary,
                                                  ),
                                                  maxLines: 2,
                                                  overflow: TextOverflow.ellipsis,
                                                ),
                                              ],
                                            ),
                                          ),
                                          if (!item.isRead) ...[
                                            const SizedBox(width: 8),
                                            Container(
                                              width: 8,
                                              height: 8,
                                              margin: const EdgeInsets.only(top: 6),
                                              decoration: const BoxDecoration(
                                                color: AppColors.primary,
                                                shape: BoxShape.circle,
                                              ),
                                            ),
                                          ],
                                        ],
                                      ),
                                    ),
                                  ),
                                );
                              },
                            ),
                          ),
          ),
        ],
      ),
    );
  }
}

class _NotificationPreferencesSheet extends StatefulWidget {
  final NotificationService service;

  const _NotificationPreferencesSheet({required this.service});

  @override
  State<_NotificationPreferencesSheet> createState() => _NotificationPreferencesSheetState();
}

class _NotificationPreferencesSheetState extends State<_NotificationPreferencesSheet> {
  bool _isLoading = true;
  NotificationPreference? _prefs;

  @override
  void initState() {
    super.initState();
    _loadPrefs();
  }

  Future<void> _loadPrefs() async {
    final res = await widget.service.getPreferences();
    if (mounted && res.isSuccess && res.data != null) {
      setState(() {
        _prefs = res.data;
        _isLoading = false;
      });
    } else if (mounted) {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _savePref(String key, bool value) async {
    if (_prefs == null) return;
    final updates = {key: value};
    final res = await widget.service.updatePreferences(updates);
    if (mounted && res.isSuccess && res.data != null) {
      setState(() => _prefs = res.data);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.only(
        left: 20,
        right: 20,
        top: 20,
        bottom: MediaQuery.of(context).viewInsets.bottom + 24,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text(
                'Notification Preferences',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
              ),
              IconButton(
                icon: const Icon(Icons.close),
                onPressed: () => Navigator.pop(context),
              ),
            ],
          ),
          const SizedBox(height: 8),
          const Text(
            'Choose how and when you receive grievance notifications and alerts.',
            style: TextStyle(fontSize: 13, color: AppColors.textMuted),
          ),
          const SizedBox(height: 16),
          if (_isLoading)
            const Center(child: Padding(padding: EdgeInsets.all(24), child: CircularProgressIndicator()))
          else if (_prefs != null) ...[
            const Text('Delivery Channels', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: AppColors.primary)),
            SwitchListTile(
              title: const Text('Email Notifications'),
              subtitle: const Text('Receive branded email summaries for case updates'),
              value: _prefs!.emailEnabled,
              onChanged: (val) => _savePref('email_enabled', val),
            ),
            SwitchListTile(
              title: const Text('In-App Notifications'),
              subtitle: const Text('Show badges and live feed items inside the app'),
              value: _prefs!.inAppEnabled,
              onChanged: (val) => _savePref('in_app_enabled', val),
            ),
            const Divider(),
            const Text('Event Alerts', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: AppColors.primary)),
            SwitchListTile(
              title: const Text('Case Assignments'),
              subtitle: const Text('Alert when a case is assigned or reassigned'),
              value: _prefs!.notifyOnAssignment,
              onChanged: (val) => _savePref('notify_on_assignment', val),
            ),
            SwitchListTile(
              title: const Text('Status Changes'),
              subtitle: const Text('Alert on state transitions (Investigated, Resolved, Closed)'),
              value: _prefs!.notifyOnStatusChange,
              onChanged: (val) => _savePref('notify_on_status_change', val),
            ),
            SwitchListTile(
              title: const Text('SLA & Risk Warnings'),
              subtitle: const Text('Alert when resolution deadline approaches breach threshold'),
              value: _prefs!.notifyOnSlaWarning,
              onChanged: (val) => _savePref('notify_on_sla_warning', val),
            ),
            SwitchListTile(
              title: const Text('Escalations'),
              subtitle: const Text('Alert on automatic or manual case escalations'),
              value: _prefs!.notifyOnEscalation,
              onChanged: (val) => _savePref('notify_on_escalation', val),
            ),
            SwitchListTile(
              title: const Text('Messages & Comments'),
              subtitle: const Text('Alert when a citizen or officer posts a message'),
              value: _prefs!.notifyOnMessages,
              onChanged: (val) => _savePref('notify_on_messages', val),
            ),
          ],
        ],
      ),
    );
  }
}

import 'package:flutter/material.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../auth/data/auth_models.dart';
import '../../../auth/data/auth_service.dart';
import '../data/case_models.dart';
import '../data/case_service.dart';
import '../data/activity_models.dart';
import '../data/activity_service.dart';
import '../data/attachment_models.dart';
import '../data/attachment_service.dart';

class CaseDetailScreen extends StatefulWidget {
  final int caseId;

  const CaseDetailScreen({super.key, required this.caseId});

  @override
  State<CaseDetailScreen> createState() => _CaseDetailScreenState();
}

class _CaseDetailScreenState extends State<CaseDetailScreen> with SingleTickerProviderStateMixin {
  final CaseService _caseService = CaseService();
  final ActivityService _activityService = ActivityService();
  final AttachmentService _attachmentService = AttachmentService();

  late TabController _tabController;
  bool _isLoading = true;
  CaseModel? _caseData;
  String? _errorMessage;

  // Activities Data
  List<CaseMessageModel> _messages = [];
  List<InternalNoteModel> _internalNotes = [];
  List<CaseTaskModel> _tasks = [];
  List<CaseInvestigationModel> _investigations = [];
  List<CaseAttachmentModel> _attachments = [];

  bool _isSendingMessage = false;
  final TextEditingController _messageController = TextEditingController();

  bool get _isCitizen => AuthService.currentUser?.role == UserRole.requester;

  @override
  void initState() {
    super.initState();
    final tabCount = _isCitizen ? 3 : 6;
    _tabController = TabController(length: tabCount, vsync: this);
    _loadAllData();
  }

  @override
  void dispose() {
    _tabController.dispose();
    _messageController.dispose();
    super.dispose();
  }

  Future<void> _loadAllData() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    final caseRes = await _caseService.getCaseDetails(widget.caseId);
    if (!mounted) return;

    if (!caseRes.isSuccess || caseRes.data == null) {
      setState(() {
        _isLoading = false;
        _errorMessage = caseRes.errorMessage ?? 'Failed to load case details.';
      });
      return;
    }

    _caseData = caseRes.data;

    // Load messages
    final msgRes = await _activityService.getMessages(widget.caseId);
    if (msgRes.isSuccess && msgRes.data != null) {
      _messages = msgRes.data!;
    }

    // Load attachments
    final attRes = await _attachmentService.getAttachments(widget.caseId);
    if (attRes.isSuccess && attRes.data != null) {
      _attachments = attRes.data!;
    }

    // Load staff-only activities
    if (!_isCitizen) {
      final noteRes = await _activityService.getInternalNotes(widget.caseId);
      if (noteRes.isSuccess && noteRes.data != null) {
        _internalNotes = noteRes.data!;
      }

      final taskRes = await _activityService.getTasks(widget.caseId);
      if (taskRes.isSuccess && taskRes.data != null) {
        _tasks = taskRes.data!;
      }

      final invRes = await _activityService.getInvestigations(widget.caseId);
      if (invRes.isSuccess && invRes.data != null) {
        _investigations = invRes.data!;
      }
    }

    setState(() {
      _isLoading = false;
    });
  }

  // ---------------------------------------------------------------------------
  // Action Handlers
  // ---------------------------------------------------------------------------

  Future<void> _handleSendMessage() async {
    final text = _messageController.text.trim();
    if (text.isEmpty) return;

    setState(() => _isSendingMessage = true);
    final res = await _activityService.sendMessage(widget.caseId, message: text);
    if (!mounted) return;
    setState(() => _isSendingMessage = false);

    if (res.isSuccess) {
      _messageController.clear();
      final msgRes = await _activityService.getMessages(widget.caseId);
      if (msgRes.isSuccess && msgRes.data != null) {
        setState(() => _messages = msgRes.data!);
      }
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(res.errorMessage ?? 'Failed to send message.')),
      );
    }
  }

  Future<void> _showAddInternalNoteDialog() async {
    final noteController = TextEditingController();
    String noteType = 'general';

    final added = await showDialog<bool>(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setDialogState) => AlertDialog(
          title: const Row(
            children: [
              Icon(Icons.lock_outline, color: AppColors.statusWarning, size: 20),
              SizedBox(width: 8),
              Text('New Internal Note', style: TextStyle(fontSize: 16)),
            ],
          ),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: AppColors.statusWarning.withOpacity(0.12),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: const Text(
                  '⚠️ Strictly Private to Municipal Staff. Never visible to citizen.',
                  style: TextStyle(fontSize: 11, color: AppColors.statusWarning, fontWeight: FontWeight.bold),
                ),
              ),
              const SizedBox(height: 12),
              DropdownButtonFormField<String>(
                value: noteType,
                decoration: const InputDecoration(labelText: 'Note Type', isDense: true),
                items: const [
                  DropdownMenuItem(value: 'general', child: Text('General')),
                  DropdownMenuItem(value: 'investigation_discussion', child: Text('Investigation Discussion')),
                  DropdownMenuItem(value: 'management_note', child: Text('Management Note')),
                  DropdownMenuItem(value: 'handover', child: Text('Shift Handover')),
                ],
                onChanged: (val) => setDialogState(() => noteType = val ?? 'general'),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: noteController,
                maxLines: 4,
                decoration: const InputDecoration(
                  labelText: 'Note Content',
                  hintText: 'Enter confidential observations or team instructions...',
                ),
              ),
            ],
          ),
          actions: [
            TextButton(onPressed: () => Navigator.of(ctx).pop(false), child: const Text('Cancel')),
            ElevatedButton(
              onPressed: () {
                if (noteController.text.trim().isNotEmpty) {
                  Navigator.of(ctx).pop(true);
                }
              },
              child: const Text('Save Note'),
            ),
          ],
        ),
      ),
    );

    if (added == true && noteController.text.trim().isNotEmpty) {
      final res = await _activityService.createInternalNote(
        widget.caseId,
        note: noteController.text.trim(),
        noteType: noteType,
      );
      if (res.isSuccess) {
        _loadAllData();
      }
    }
  }

  Future<void> _showAddTaskDialog() async {
    final titleController = TextEditingController();
    final descController = TextEditingController();

    final added = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Add Subtask', style: TextStyle(fontSize: 16)),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: titleController,
              decoration: const InputDecoration(labelText: 'Task Title', hintText: 'e.g. Inspect water pressure valve'),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: descController,
              maxLines: 2,
              decoration: const InputDecoration(labelText: 'Description (Optional)', hintText: 'Specific instructions for team'),
            ),
          ],
        ),
        actions: [
          TextButton(onPressed: () => Navigator.of(ctx).pop(false), child: const Text('Cancel')),
          ElevatedButton(
            onPressed: () {
              if (titleController.text.trim().isNotEmpty) {
                Navigator.of(ctx).pop(true);
              }
            },
            child: const Text('Add Task'),
          ),
        ],
      ),
    );

    if (added == true && titleController.text.trim().isNotEmpty) {
      final res = await _activityService.createTask(
        widget.caseId,
        title: titleController.text.trim(),
        description: descController.text.trim().isNotEmpty ? descController.text.trim() : null,
      );
      if (res.isSuccess) {
        _loadAllData();
      }
    }
  }

  Future<void> _handleToggleTaskStatus(CaseTaskModel task) async {
    final newStatus = task.isCompleted ? 'pending' : 'completed';
    final res = await _activityService.updateTaskStatus(widget.caseId, task.id, status: newStatus);
    if (res.isSuccess) {
      _loadAllData();
    }
  }

  Future<void> _showLogInvestigationDialog() async {
    final obsController = TextEditingController();
    final actionsController = TextEditingController();
    final findingsController = TextEditingController();
    final followUpController = TextEditingController();

    final saved = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Log Investigation Record', style: TextStyle(fontSize: 16)),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: obsController,
                maxLines: 2,
                decoration: const InputDecoration(labelText: 'Field Observations', hintText: 'What did you inspect on site?'),
              ),
              const SizedBox(height: 10),
              TextField(
                controller: actionsController,
                maxLines: 2,
                decoration: const InputDecoration(labelText: 'Actions Taken', hintText: 'What initial measures were applied?'),
              ),
              const SizedBox(height: 10),
              TextField(
                controller: findingsController,
                maxLines: 2,
                decoration: const InputDecoration(labelText: 'Root Cause Findings', hintText: 'Underlying cause of issue'),
              ),
              const SizedBox(height: 10),
              TextField(
                controller: followUpController,
                maxLines: 2,
                decoration: const InputDecoration(labelText: 'Follow-up Requirements', hintText: 'Pending materials or squad needs'),
              ),
            ],
          ),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.of(ctx).pop(false), child: const Text('Cancel')),
          ElevatedButton(
            onPressed: () => Navigator.of(ctx).pop(true),
            child: const Text('Save Investigation'),
          ),
        ],
      ),
    );

    if (saved == true) {
      final res = await _activityService.recordInvestigation(
        widget.caseId,
        observations: obsController.text.trim().isNotEmpty ? obsController.text.trim() : null,
        actionsTaken: actionsController.text.trim().isNotEmpty ? actionsController.text.trim() : null,
        findings: findingsController.text.trim().isNotEmpty ? findingsController.text.trim() : null,
        followUpRequirements: followUpController.text.trim().isNotEmpty ? followUpController.text.trim() : null,
      );
      if (res.isSuccess) {
        _loadAllData();
      }
    }
  }

  Future<void> _handleConfirmResolution() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Confirm Resolution'),
        content: const Text('Are you satisfied that this municipal issue has been properly resolved on-site?'),
        actions: [
          TextButton(onPressed: () => Navigator.of(ctx).pop(false), child: const Text('Cancel')),
          ElevatedButton(
            onPressed: () => Navigator.of(ctx).pop(true),
            style: ElevatedButton.styleFrom(backgroundColor: AppColors.statusSuccess),
            child: const Text('Confirm & Close'),
          ),
        ],
      ),
    );

    if (confirmed == true) {
      final res = await _caseService.confirmResolution(widget.caseId);
      if (res.isSuccess) {
        _loadAllData();
      }
    }
  }

  Future<void> _handleRejectResolution() async {
    final reasonController = TextEditingController();
    final rejected = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Reject Resolution & Reopen'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Please explain what is still incomplete:'),
            const SizedBox(height: 10),
            TextField(
              controller: reasonController,
              maxLines: 3,
              decoration: const InputDecoration(hintText: 'e.g. Loose sand was placed instead of asphalt...'),
            ),
          ],
        ),
        actions: [
          TextButton(onPressed: () => Navigator.of(ctx).pop(false), child: const Text('Cancel')),
          ElevatedButton(
            onPressed: () {
              if (reasonController.text.trim().isNotEmpty) {
                Navigator.of(ctx).pop(true);
              }
            },
            style: ElevatedButton.styleFrom(backgroundColor: AppColors.statusError),
            child: const Text('Submit & Reopen'),
          ),
        ],
      ),
    );

    if (rejected == true && reasonController.text.trim().isNotEmpty) {
      final res = await _caseService.rejectResolution(
        widget.caseId,
        rejectionReason: reasonController.text.trim(),
      );
      if (res.isSuccess) {
        _loadAllData();
      }
    }
  }

  Future<void> _handleStaffStatusAdvance(String targetStatus) async {
    String? resolutionNotes;
    if (targetStatus == 'resolution_proposed') {
      final notesController = TextEditingController();
      final proceed = await showDialog<bool>(
        context: context,
        builder: (ctx) => AlertDialog(
          title: const Text('Propose Resolution'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Text('Describe actions taken and findings:'),
              const SizedBox(height: 10),
              TextField(
                controller: notesController,
                maxLines: 3,
                decoration: const InputDecoration(hintText: 'e.g. Cleared 2 metric tons of silt, tested drainage flow.'),
              ),
            ],
          ),
          actions: [
            TextButton(onPressed: () => Navigator.of(ctx).pop(false), child: const Text('Cancel')),
            ElevatedButton(onPressed: () => Navigator.of(ctx).pop(true), child: const Text('Submit Resolution')),
          ],
        ),
      );
      if (proceed != true) return;
      resolutionNotes = notesController.text.trim();
    }

    final res = await _caseService.updateStatus(
      caseId: widget.caseId,
      newStatus: targetStatus,
      resolutionNotes: resolutionNotes,
    );
    if (res.isSuccess) {
      _loadAllData();
    }
  }

  // ---------------------------------------------------------------------------
  // Build Methods
  // ---------------------------------------------------------------------------

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(_caseData != null ? _caseData!.caseNumber : 'Case Details'),
        actions: [
          IconButton(icon: const Icon(Icons.refresh), onPressed: _loadAllData),
        ],
        bottom: TabBar(
          controller: _tabController,
          isScrollable: true,
          tabs: _isCitizen
              ? const [
                  Tab(text: 'Overview & Timeline'),
                  Tab(text: 'Messages & Updates'),
                  Tab(text: 'Evidence & Files'),
                ]
              : const [
                  Tab(text: 'Overview'),
                  Tab(text: 'Messages'),
                  Tab(text: '🔒 Internal Notes'),
                  Tab(text: 'Tasks'),
                  Tab(text: 'Investigation'),
                  Tab(text: 'Evidence & Files'),
                ],
        ),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _errorMessage != null
              ? Center(
                  child: Padding(
                    padding: const EdgeInsets.all(24.0),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        const Icon(Icons.error_outline, size: 48, color: AppColors.statusError),
                        const SizedBox(height: 12),
                        Text(_errorMessage!, textAlign: TextAlign.center),
                        const SizedBox(height: 16),
                        ElevatedButton(onPressed: _loadAllData, child: const Text('Retry')),
                      ],
                    ),
                  ),
                )
              : _caseData == null
                  ? const Center(child: Text('Case not found.'))
                  : TabBarView(
                      controller: _tabController,
                      children: _isCitizen
                          ? [
                              _buildOverviewTab(),
                              _buildMessagesTab(),
                              _buildEvidenceTab(),
                            ]
                          : [
                              _buildOverviewTab(),
                              _buildMessagesTab(),
                              _buildInternalNotesTab(),
                              _buildTasksTab(),
                              _buildInvestigationTab(),
                              _buildEvidenceTab(),
                            ],
                    ),
    );
  }

  // ---------------------------------------------------------------------------
  // Tab 1: Overview & Timeline
  // ---------------------------------------------------------------------------
  Widget _buildOverviewTab() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildLifecycleTracker(_caseData!.status),
          const SizedBox(height: 16),

          // Header Card
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: AppColors.surface,
              borderRadius: BorderRadius.circular(14),
              border: Border.all(color: AppColors.border),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      _caseData!.caseNumber,
                      style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: AppColors.primary),
                    ),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                      decoration: BoxDecoration(
                        color: _caseData!.status.badgeColor.withOpacity(0.12),
                        borderRadius: BorderRadius.circular(20),
                      ),
                      child: Text(
                        _caseData!.status.displayName.toUpperCase(),
                        style: TextStyle(color: _caseData!.status.badgeColor, fontWeight: FontWeight.bold, fontSize: 11),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 10),
                Text(
                  _caseData!.title,
                  style: const TextStyle(fontSize: 17, fontWeight: FontWeight.bold, color: AppColors.textPrimary),
                ),
                const SizedBox(height: 8),
                Text(
                  _caseData!.description,
                  style: const TextStyle(fontSize: 14, color: AppColors.textSecondary, height: 1.4),
                ),
                const Divider(height: 20),
                Row(
                  children: [
                    const Icon(Icons.location_on_outlined, size: 16, color: AppColors.textMuted),
                    const SizedBox(width: 4),
                    Text(
                      '${_caseData!.ward ?? "Ward 12"} ${_caseData!.landmark != null ? "• ${_caseData!.landmark}" : ""}',
                      style: const TextStyle(fontSize: 12, color: AppColors.textSecondary),
                    ),
                  ],
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),

          // Citizen Resolution Card
          if (_isCitizen && _caseData!.status == CaseStatus.resolutionProposed) ...[
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: AppColors.statusSuccess.withOpacity(0.08),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: AppColors.statusSuccess.withOpacity(0.3)),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Row(
                    children: [
                      Icon(Icons.check_circle_outline, color: AppColors.statusSuccess),
                      SizedBox(width: 8),
                      Text('Resolution Proposed by Municipal Staff',
                          style: TextStyle(fontWeight: FontWeight.bold, color: AppColors.statusSuccess, fontSize: 15)),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Text(
                    _caseData!.resolutionNotes ?? 'The field team reports this issue has been resolved.',
                    style: const TextStyle(fontSize: 13),
                  ),
                  const SizedBox(height: 14),
                  Row(
                    children: [
                      Expanded(
                        child: ElevatedButton.icon(
                          onPressed: _handleConfirmResolution,
                          icon: const Icon(Icons.check, size: 18),
                          label: const Text('Confirm & Close'),
                          style: ElevatedButton.styleFrom(backgroundColor: AppColors.statusSuccess),
                        ),
                      ),
                      const SizedBox(width: 10),
                      Expanded(
                        child: OutlinedButton.icon(
                          onPressed: _handleRejectResolution,
                          icon: const Icon(Icons.refresh, size: 18),
                          label: const Text('Reject / Reopen'),
                          style: OutlinedButton.styleFrom(
                            foregroundColor: AppColors.statusError,
                            side: const BorderSide(color: AppColors.statusError),
                          ),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),
          ],

          // Staff Action Bar
          if (!_isCitizen) ...[
            const Text('Staff Action Bar', style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                if (_caseData!.status == CaseStatus.reported || _caseData!.status == CaseStatus.understood)
                  ElevatedButton.icon(
                    onPressed: () => _handleStaffStatusAdvance('assigned'),
                    icon: const Icon(Icons.assignment_ind, size: 16),
                    label: const Text('Take Ownership'),
                  ),
                if (_caseData!.status == CaseStatus.assigned || _caseData!.status == CaseStatus.reopened)
                  ElevatedButton.icon(
                    onPressed: () => _handleStaffStatusAdvance('investigated'),
                    icon: const Icon(Icons.search, size: 16),
                    label: const Text('Mark Investigated'),
                  ),
                if (_caseData!.status == CaseStatus.investigated)
                  ElevatedButton.icon(
                    onPressed: () => _handleStaffStatusAdvance('action_taken'),
                    icon: const Icon(Icons.build_outlined, size: 16),
                    label: const Text('Record Action Taken'),
                  ),
                if (_caseData!.status == CaseStatus.actionTaken)
                  ElevatedButton.icon(
                    onPressed: () => _handleStaffStatusAdvance('resolution_proposed'),
                    icon: const Icon(Icons.task_alt, size: 16),
                    label: const Text('Propose Resolution'),
                    style: ElevatedButton.styleFrom(backgroundColor: AppColors.statusSuccess),
                  ),
              ],
            ),
            const SizedBox(height: 20),
          ],

          // Timeline
          const Text('Chronological Case Journey', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
          const SizedBox(height: 10),

          if (_caseData!.timeline.isEmpty)
            const Text('No timeline records yet.')
          else
            ListView.separated(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              itemCount: _caseData!.timeline.length,
              separatorBuilder: (_, __) => const SizedBox(height: 10),
              itemBuilder: (context, idx) {
                final entry = _caseData!.timeline[idx];
                return Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: AppColors.surface,
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: AppColors.border),
                  ),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Container(
                        padding: const EdgeInsets.all(8),
                        decoration: BoxDecoration(
                          color: AppColors.primary.withOpacity(0.08),
                          shape: BoxShape.circle,
                        ),
                        child: const Icon(Icons.history, size: 18, color: AppColors.primary),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                Text(
                                  entry.action.replaceAll('_', ' ').toUpperCase(),
                                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12),
                                ),
                                Text(
                                  '${entry.createdAt.hour.toString().padLeft(2, "0")}:${entry.createdAt.minute.toString().padLeft(2, "0")}',
                                  style: const TextStyle(fontSize: 11, color: AppColors.textMuted),
                                ),
                              ],
                            ),
                            if (entry.notes != null) ...[
                              const SizedBox(height: 4),
                              Text(entry.notes!, style: const TextStyle(fontSize: 12, color: AppColors.textSecondary)),
                            ],
                          ],
                        ),
                      ),
                    ],
                  ),
                );
              },
            ),
        ],
      ),
    );
  }

  // ---------------------------------------------------------------------------
  // Tab 2: Messages (Citizen <-> Staff Communication)
  // ---------------------------------------------------------------------------
  Widget _buildMessagesTab() {
    return Column(
      children: [
        Expanded(
          child: _messages.isEmpty
              ? Center(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(Icons.chat_bubble_outline, size: 48, color: AppColors.textMuted.withOpacity(0.5)),
                      const SizedBox(height: 8),
                      const Text('No messages on this case yet.'),
                      const SizedBox(height: 4),
                      const Text('Ask questions or share updates below.', style: TextStyle(fontSize: 12, color: AppColors.textMuted)),
                    ],
                  ),
                )
              : ListView.separated(
                  padding: const EdgeInsets.all(16),
                  itemCount: _messages.length,
                  separatorBuilder: (_, __) => const SizedBox(height: 12),
                  itemBuilder: (context, idx) {
                    final msg = _messages[idx];
                    final isMe = (_isCitizen && msg.isFromCitizen) || (!_isCitizen && !msg.isFromCitizen);

                    return Align(
                      alignment: isMe ? Alignment.centerRight : Alignment.centerLeft,
                      child: Container(
                        constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.78),
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: isMe ? AppColors.primary : AppColors.surface,
                          borderRadius: BorderRadius.only(
                            topLeft: const Radius.circular(14),
                            topRight: const Radius.circular(14),
                            bottomLeft: isMe ? const Radius.circular(14) : const Radius.circular(2),
                            bottomRight: isMe ? const Radius.circular(2) : const Radius.circular(14),
                          ),
                          border: isMe ? null : Border.all(color: AppColors.border),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                Text(
                                  msg.senderName ?? (msg.isFromCitizen ? 'Citizen' : 'Municipal Staff'),
                                  style: TextStyle(
                                    fontWeight: FontWeight.bold,
                                    fontSize: 11,
                                    color: isMe ? Colors.white70 : AppColors.primary,
                                  ),
                                ),
                                const SizedBox(width: 6),
                                Text(
                                  '${msg.createdAt.hour.toString().padLeft(2, "0")}:${msg.createdAt.minute.toString().padLeft(2, "0")}',
                                  style: TextStyle(
                                    fontSize: 9,
                                    color: isMe ? Colors.white60 : AppColors.textMuted,
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 4),
                            Text(
                              msg.message,
                              style: TextStyle(
                                fontSize: 13,
                                color: isMe ? Colors.white : AppColors.textPrimary,
                              ),
                            ),
                          ],
                        ),
                      ),
                    );
                  },
                ),
        ),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
          decoration: BoxDecoration(
            color: AppColors.surface,
            border: Border(top: BorderSide(color: AppColors.border)),
          ),
          child: SafeArea(
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _messageController,
                    decoration: InputDecoration(
                      hintText: _isCitizen ? 'Ask question or provide update...' : 'Reply to citizen...',
                      border: OutlineInputBorder(borderRadius: BorderRadius.circular(24)),
                      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                      isDense: true,
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                IconButton(
                  onPressed: _isSendingMessage ? null : _handleSendMessage,
                  icon: _isSendingMessage
                      ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2))
                      : const Icon(Icons.send, color: AppColors.primary),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }

  // ---------------------------------------------------------------------------
  // Tab 3: Internal Notes (Staff Only)
  // ---------------------------------------------------------------------------
  Widget _buildInternalNotesTab() {
    return Column(
      children: [
        Container(
          margin: const EdgeInsets.all(12),
          padding: const EdgeInsets.all(10),
          decoration: BoxDecoration(
            color: AppColors.statusWarning.withOpacity(0.12),
            borderRadius: BorderRadius.circular(8),
            border: Border.all(color: AppColors.statusWarning.withOpacity(0.3)),
          ),
          child: const Row(
            children: [
              Icon(Icons.shield_outlined, color: AppColors.statusWarning, size: 20),
              SizedBox(width: 8),
              Expanded(
                child: Text(
                  'CONFIDENTIAL: These notes are strictly visible to municipal staff and are completely hidden from citizens.',
                  style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: AppColors.statusWarning),
                ),
              ),
            ],
          ),
        ),
        Expanded(
          child: _internalNotes.isEmpty
              ? const Center(child: Text('No internal notes recorded yet.'))
              : ListView.separated(
                  padding: const EdgeInsets.symmetric(horizontal: 16),
                  itemCount: _internalNotes.length,
                  separatorBuilder: (_, __) => const SizedBox(height: 10),
                  itemBuilder: (context, idx) {
                    final note = _internalNotes[idx];
                    return Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: AppColors.surface,
                        borderRadius: BorderRadius.circular(10),
                        border: Border.all(color: AppColors.border),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              Text(
                                '${note.authorName ?? "Staff"} (${note.authorRole ?? "Staff"})',
                                style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12, color: AppColors.primary),
                              ),
                              Container(
                                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                decoration: BoxDecoration(
                                  color: AppColors.primary.withOpacity(0.1),
                                  borderRadius: BorderRadius.circular(4),
                                ),
                                child: Text(
                                  note.noteType.replaceAll('_', ' ').toUpperCase(),
                                  style: const TextStyle(fontSize: 9, fontWeight: FontWeight.bold, color: AppColors.primary),
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 6),
                          Text(note.note, style: const TextStyle(fontSize: 13, height: 1.3)),
                          const SizedBox(height: 6),
                          Text(
                            '${note.createdAt.day}/${note.createdAt.month}/${note.createdAt.year} ${note.createdAt.hour.toString().padLeft(2, "0")}:${note.createdAt.minute.toString().padLeft(2, "0")}',
                            style: const TextStyle(fontSize: 10, color: AppColors.textMuted),
                          ),
                        ],
                      ),
                    );
                  },
                ),
        ),
        Padding(
          padding: const EdgeInsets.all(12.0),
          child: ElevatedButton.icon(
            onPressed: _showAddInternalNoteDialog,
            icon: const Icon(Icons.add_comment_outlined, size: 18),
            label: const Text('Add Private Internal Note'),
            style: ElevatedButton.styleFrom(minimumSize: const Size.fromHeight(44)),
          ),
        ),
      ],
    );
  }

  // ---------------------------------------------------------------------------
  // Tab 4: Tasks (Staff Only Checklist)
  // ---------------------------------------------------------------------------
  Widget _buildTasksTab() {
    return Column(
      children: [
        Expanded(
          child: _tasks.isEmpty
              ? const Center(child: Text('No tasks created for this case yet.'))
              : ListView.separated(
                  padding: const EdgeInsets.all(16),
                  itemCount: _tasks.length,
                  separatorBuilder: (_, __) => const SizedBox(height: 10),
                  itemBuilder: (context, idx) {
                    final task = _tasks[idx];
                    return Container(
                      decoration: BoxDecoration(
                        color: AppColors.surface,
                        borderRadius: BorderRadius.circular(10),
                        border: Border.all(color: AppColors.border),
                      ),
                      child: CheckboxListTile(
                        value: task.isCompleted,
                        onChanged: (val) => _handleToggleTaskStatus(task),
                        title: Text(
                          task.title,
                          style: TextStyle(
                            fontWeight: FontWeight.bold,
                            fontSize: 13,
                            decoration: task.isCompleted ? TextDecoration.lineThrough : null,
                            color: task.isCompleted ? AppColors.textMuted : AppColors.textPrimary,
                          ),
                        ),
                        subtitle: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            if (task.description != null && task.description!.isNotEmpty) ...[
                              const SizedBox(height: 2),
                              Text(task.description!, style: const TextStyle(fontSize: 12, color: AppColors.textSecondary)),
                            ],
                            const SizedBox(height: 4),
                            Text(
                              'Assigned: ${task.assignedToName ?? "Unassigned"} • Status: ${task.status.toUpperCase()}',
                              style: const TextStyle(fontSize: 10, color: AppColors.textMuted),
                            ),
                          ],
                        ),
                        controlAffinity: ListTileControlAffinity.leading,
                      ),
                    );
                  },
                ),
        ),
        Padding(
          padding: const EdgeInsets.all(12.0),
          child: ElevatedButton.icon(
            onPressed: _showAddTaskDialog,
            icon: const Icon(Icons.add_task, size: 18),
            label: const Text('Add Subtask'),
            style: ElevatedButton.styleFrom(minimumSize: const Size.fromHeight(44)),
          ),
        ),
      ],
    );
  }

  // ---------------------------------------------------------------------------
  // Tab 5: Investigation (Staff Only Findings)
  // ---------------------------------------------------------------------------
  Widget _buildInvestigationTab() {
    return Column(
      children: [
        Expanded(
          child: _investigations.isEmpty
              ? const Center(child: Text('No formal investigation logs recorded yet.'))
              : ListView.separated(
                  padding: const EdgeInsets.all(16),
                  itemCount: _investigations.length,
                  separatorBuilder: (_, __) => const SizedBox(height: 12),
                  itemBuilder: (context, idx) {
                    final inv = _investigations[idx];
                    return Container(
                      padding: const EdgeInsets.all(14),
                      decoration: BoxDecoration(
                        color: AppColors.surface,
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: AppColors.border),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              Text(
                                'Investigator: ${inv.investigatorName ?? "Field Inspector"}',
                                style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: AppColors.primary),
                              ),
                              Text(
                                '${inv.createdAt.day}/${inv.createdAt.month}/${inv.createdAt.year}',
                                style: const TextStyle(fontSize: 10, color: AppColors.textMuted),
                              ),
                            ],
                          ),
                          const Divider(height: 16),
                          if (inv.observations != null) ...[
                            const Text('Field Observations', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 11, color: AppColors.textMuted)),
                            Text(inv.observations!, style: const TextStyle(fontSize: 13)),
                            const SizedBox(height: 8),
                          ],
                          if (inv.actionsTaken != null) ...[
                            const Text('Actions Taken', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 11, color: AppColors.textMuted)),
                            Text(inv.actionsTaken!, style: const TextStyle(fontSize: 13)),
                            const SizedBox(height: 8),
                          ],
                          if (inv.findings != null) ...[
                            const Text('Root Cause Findings', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 11, color: AppColors.textMuted)),
                            Text(inv.findings!, style: const TextStyle(fontSize: 13)),
                            const SizedBox(height: 8),
                          ],
                          if (inv.followUpRequirements != null) ...[
                            const Text('Follow-up Requirements', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 11, color: AppColors.textMuted)),
                            Text(inv.followUpRequirements!, style: const TextStyle(fontSize: 13)),
                          ],
                        ],
                      ),
                    );
                  },
                ),
        ),
        Padding(
          padding: const EdgeInsets.all(12.0),
          child: ElevatedButton.icon(
            onPressed: _showLogInvestigationDialog,
            icon: const Icon(Icons.note_alt_outlined, size: 18),
            label: const Text('Log Investigation Record'),
            style: ElevatedButton.styleFrom(minimumSize: const Size.fromHeight(44)),
          ),
        ),
      ],
    );
  }

  // ---------------------------------------------------------------------------
  // Tab: Evidence & Files
  // ---------------------------------------------------------------------------
  Widget _buildEvidenceTab() {
    return Column(
      children: [
        Expanded(
          child: _attachments.isEmpty
              ? Center(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(Icons.folder_open_outlined, size: 48, color: AppColors.textMuted.withOpacity(0.5)),
                      const SizedBox(height: 8),
                      const Text('No evidence or attachments uploaded yet.'),
                      const SizedBox(height: 4),
                      const Text('Photos and documents uploaded for this case will appear here.',
                          style: TextStyle(fontSize: 12, color: AppColors.textMuted)),
                    ],
                  ),
                )
              : ListView.separated(
                  padding: const EdgeInsets.all(16),
                  itemCount: _attachments.length,
                  separatorBuilder: (_, __) => const SizedBox(height: 12),
                  itemBuilder: (context, idx) {
                    final att = _attachments[idx];
                    return Container(
                      padding: const EdgeInsets.all(14),
                      decoration: BoxDecoration(
                        color: AppColors.surface,
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: AppColors.border),
                      ),
                      child: Row(
                        children: [
                          Container(
                            padding: const EdgeInsets.all(12),
                            decoration: BoxDecoration(
                              color: AppColors.primary.withOpacity(0.08),
                              borderRadius: BorderRadius.circular(10),
                            ),
                            child: Icon(att.fileIcon, color: AppColors.primary, size: 24),
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  att.originalFilename,
                                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
                                  maxLines: 1,
                                  overflow: TextOverflow.ellipsis,
                                ),
                                const SizedBox(height: 4),
                                if (att.description != null && att.description!.isNotEmpty) ...[
                                  Text(att.description!, style: const TextStyle(fontSize: 12, color: AppColors.textSecondary)),
                                  const SizedBox(height: 4),
                                ],
                                Row(
                                  children: [
                                    Text(
                                      att.formattedSize,
                                      style: const TextStyle(fontSize: 11, color: AppColors.textMuted, fontWeight: FontWeight.w600),
                                    ),
                                    const SizedBox(width: 8),
                                    Text(
                                      '• ${att.uploadedByName ?? "User"}',
                                      style: const TextStyle(fontSize: 11, color: AppColors.textMuted),
                                    ),
                                  ],
                                ),
                              ],
                            ),
                          ),
                          IconButton(
                            icon: const Icon(Icons.download_rounded, color: AppColors.primary),
                            tooltip: 'Download file',
                            onPressed: () {
                              ScaffoldMessenger.of(context).showSnackBar(
                                SnackBar(content: Text('Downloading ${att.originalFilename}...')),
                              );
                            },
                          ),
                        ],
                      ),
                    );
                  },
                ),
        ),
      ],
    );
  }

  Widget _buildLifecycleTracker(CaseStatus currentStatus) {
    final steps = ['Reported', 'Assigned', 'Investigated', 'Action', 'Resolved', 'Closed'];
    final currentIndex = currentStatus.stepIndex.clamp(0, steps.length - 1);

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 14),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('Lifecycle Stage', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: AppColors.textMuted)),
          const SizedBox(height: 10),
          Row(
            children: List.generate(steps.length, (idx) {
              final isCompleted = idx <= currentIndex;
              return Expanded(
                child: Column(
                  children: [
                    Container(
                      height: 8,
                      margin: const EdgeInsets.symmetric(horizontal: 2),
                      decoration: BoxDecoration(
                        color: isCompleted ? AppColors.primary : AppColors.border,
                        borderRadius: BorderRadius.circular(4),
                      ),
                    ),
                    const SizedBox(height: 6),
                    Text(
                      steps[idx],
                      style: TextStyle(
                        fontSize: 9,
                        fontWeight: isCompleted ? FontWeight.bold : FontWeight.normal,
                        color: isCompleted ? AppColors.textPrimary : AppColors.textMuted,
                      ),
                    ),
                  ],
                ),
              );
            }),
          ),
        ],
      ),
    );
  }
}

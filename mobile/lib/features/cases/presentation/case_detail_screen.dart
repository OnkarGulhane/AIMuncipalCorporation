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
import '../data/ai_models.dart';
import '../data/ai_service.dart';
import '../data/sla_models.dart';
import '../data/sla_service.dart';
import 'case_timeline_widget.dart';


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
  final AIService _aiService = AIService();
  final SLAService _slaService = SLAService();

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

  // AI Data
  AIAnalysisModel? _aiAnalysis;
  AICaseSummaryModel? _aiSummary;
  bool _isAnalyzingAI = false;

  // SLA & Escalation Data
  CaseSLAModel? _slaData;
  RiskAnalysisModel? _riskData;
  List<EscalationModel> _escalations = [];

  bool _isSendingMessage = false;
  final TextEditingController _messageController = TextEditingController();

  bool get _isCitizen => AuthService.currentUser?.role == UserRole.requester;
  bool get _isLeadOrManager =>
      AuthService.currentUser?.role == UserRole.teamLead ||
      AuthService.currentUser?.role == UserRole.manager ||
      AuthService.currentUser?.role == UserRole.administrator;

  @override
  void initState() {
    super.initState();
    final tabCount = _isCitizen ? 3 : 7;
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

    // Load SLA data
    final slaRes = await _slaService.getCaseSLA(widget.caseId);
    if (slaRes.isSuccess && slaRes.data != null) {
      _slaData = slaRes.data;
    }

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

    // Load staff-only activities, AI, Risk, and Escalations
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

      // Load AI analysis and summary
      final aiRes = await _aiService.getAnalysis(widget.caseId);
      if (aiRes.isSuccess && aiRes.data != null) {
        _aiAnalysis = aiRes.data;
      }

      final summaryRes = await _aiService.getCaseSummary(widget.caseId);
      if (summaryRes.isSuccess && summaryRes.data != null) {
        _aiSummary = summaryRes.data;
      }

      // Load Risk analysis
      final riskRes = await _slaService.getCaseRisk(widget.caseId);
      if (riskRes.isSuccess && riskRes.data != null) {
        _riskData = riskRes.data;
      }

      // Load Escalations
      final escRes = await _slaService.getCaseEscalations(widget.caseId);
      if (escRes.isSuccess && escRes.data != null) {
        _escalations = escRes.data!;
      }
    }

    setState(() {
      _isLoading = false;
    });
  }


  // ---------------------------------------------------------------------------
  // Action Handlers
  // ---------------------------------------------------------------------------

  Future<void> _handleRunAIAnalysis() async {
    setState(() => _isAnalyzingAI = true);
    final res = await _aiService.runAnalysis(widget.caseId);
    if (!mounted) return;
    setState(() => _isAnalyzingAI = false);

    if (res.isSuccess && res.data != null) {
      setState(() => _aiAnalysis = res.data);
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('AI triage and case analysis updated successfully.')),
      );
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(res.errorMessage ?? 'Failed to run AI analysis.')),
      );
    }
  }

  Future<void> _handleApplyAISuggestions() async {
    final res = await _aiService.applySuggestions(
      widget.caseId,
      applyCategory: true,
      applyPriority: true,
      applyTeam: true,
    );

    if (res.isSuccess) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Applied AI recommendations to live case!')),
      );
      _loadAllData();
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(res.errorMessage ?? 'Failed to apply suggestions.')),
      );
    }
  }

  Future<void> _showCommunicationCopilotDialog({String defaultType = 'information_request'}) async {
    String draftType = defaultType;
    final notesController = TextEditingController();
    AIDraftModel? generatedDraft;
    bool isGenerating = false;

    await showDialog(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setDialogState) => AlertDialog(
          title: const Row(
            children: [
              Icon(Icons.auto_awesome, color: AppColors.primary, size: 22),
              SizedBox(width: 8),
              Text('AI Communication Copilot', style: TextStyle(fontSize: 16)),
            ],
          ),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                DropdownButtonFormField<String>(
                  value: draftType,
                  decoration: const InputDecoration(labelText: 'Draft Type', isDense: true),
                  items: const [
                    DropdownMenuItem(value: 'information_request', child: Text('Information Request')),
                    DropdownMenuItem(value: 'progress_update', child: Text('Progress Update')),
                    DropdownMenuItem(value: 'resolution_message', child: Text('Resolution Notification')),
                    DropdownMenuItem(value: 'escalation_summary', child: Text('Internal Escalation Memo')),
                  ],
                  onChanged: (val) {
                    if (val != null) {
                      setDialogState(() {
                        draftType = val;
                        generatedDraft = null;
                      });
                    }
                  },
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: notesController,
                  decoration: const InputDecoration(
                    labelText: 'Context Instructions (Optional)',
                    hintText: 'e.g. Ask specifically for house number',
                  ),
                ),
                const SizedBox(height: 14),
                ElevatedButton.icon(
                  onPressed: isGenerating
                      ? null
                      : () async {
                          setDialogState(() => isGenerating = true);
                          final res = await _aiService.generateDraft(
                            widget.caseId,
                            draftType: draftType,
                            contextNotes: notesController.text.trim().isNotEmpty
                                ? notesController.text.trim()
                                : null,
                          );
                          setDialogState(() {
                            isGenerating = false;
                            if (res.isSuccess) {
                              generatedDraft = res.data;
                            }
                          });
                        },
                  icon: isGenerating
                      ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2))
                      : const Icon(Icons.auto_fix_high, size: 18),
                  label: const Text('Generate Draft with AI'),
                  style: ElevatedButton.styleFrom(minimumSize: const Size.fromHeight(40)),
                ),
                if (generatedDraft != null) ...[
                  const SizedBox(height: 16),
                  const Text('Generated Draft:', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12, color: AppColors.textMuted)),
                  const SizedBox(height: 6),
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: AppColors.surface,
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: AppColors.border),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('Subject: ${generatedDraft!.subject}',
                            style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12)),
                        const Divider(height: 12),
                        Text(generatedDraft!.bodyText, style: const TextStyle(fontSize: 12, height: 1.3)),
                      ],
                    ),
                  ),
                ],
              ],
            ),
          ),
          actions: [
            TextButton(onPressed: () => Navigator.of(ctx).pop(), child: const Text('Close')),
            if (generatedDraft != null)
              ElevatedButton.icon(
                onPressed: () {
                  _messageController.text = generatedDraft!.bodyText;
                  Navigator.of(ctx).pop();
                  _tabController.animateTo(2); // Switch to Messages tab
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('AI draft copied into message box.')),
                  );
                },
                icon: const Icon(Icons.copy, size: 16),
                label: const Text('Insert into Message Box'),
              ),
          ],
        ),
      ),
    );
  }

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

  Future<void> _handleRecalculateSLA() async {
    final res = await _slaService.recalculateCaseSLA(widget.caseId);
    if (res.isSuccess && res.data != null) {
      setState(() => _slaData = res.data);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('SLA targets recalculated successfully.')),
        );
      }
    }
  }

  Future<void> _showEscalateDialog() async {
    final reasonController = TextEditingController();
    String triggerType = 'operator_request';

    final proceeded = await showDialog<bool>(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setDialogState) => AlertDialog(
          title: const Row(
            children: [
              Icon(Icons.warning_amber_rounded, color: AppColors.statusError, size: 22),
              SizedBox(width: 8),
              Text('Escalate Case', style: TextStyle(fontSize: 16)),
            ],
          ),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              DropdownButtonFormField<String>(
                value: triggerType,
                decoration: const InputDecoration(labelText: 'Escalation Trigger', isDense: true),
                items: const [
                  DropdownMenuItem(value: 'operator_request', child: Text('Operator Request (Need Help)')),
                  DropdownMenuItem(value: 'safety_critical', child: Text('Critical Safety Hazard')),
                  DropdownMenuItem(value: 'sla_breach', child: Text('SLA Target Breach')),
                  DropdownMenuItem(value: 'repeated_complaint', child: Text('Repeated / Unresolved Complaint')),
                  DropdownMenuItem(value: 'risk_threshold', child: Text('High Operational Risk')),
                ],
                onChanged: (val) => setDialogState(() => triggerType = val ?? 'operator_request'),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: reasonController,
                maxLines: 3,
                decoration: const InputDecoration(
                  labelText: 'Escalation Reason',
                  hintText: 'Explain why senior management / team lead intervention is required...',
                ),
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
              child: const Text('Confirm Escalation'),
            ),
          ],
        ),
      ),
    );

    if (proceeded == true && reasonController.text.trim().isNotEmpty) {
      final res = await _slaService.createEscalation(
        widget.caseId,
        reason: reasonController.text.trim(),
        triggerType: triggerType,
      );
      if (res.isSuccess) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Case escalated to Team Lead & Manager.')),
          );
        }
        _loadAllData();
      }
    }
  }

  Future<void> _showResolveEscalationDialog(EscalationModel escalation) async {
    final notesController = TextEditingController();

    final proceeded = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Resolve Escalation', style: TextStyle(fontSize: 16)),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Reason: ${escalation.reason}', style: const TextStyle(fontSize: 13, color: AppColors.textSecondary)),
            const SizedBox(height: 12),
            TextField(
              controller: notesController,
              maxLines: 3,
              decoration: const InputDecoration(
                labelText: 'Resolution Notes',
                hintText: 'Describe management action or resources allocated...',
              ),
            ),
          ],
        ),
        actions: [
          TextButton(onPressed: () => Navigator.of(ctx).pop(false), child: const Text('Cancel')),
          ElevatedButton(
            onPressed: () => Navigator.of(ctx).pop(true),
            style: ElevatedButton.styleFrom(backgroundColor: AppColors.statusSuccess),
            child: const Text('Mark Resolved'),
          ),
        ],
      ),
    );

    if (proceeded == true) {
      final res = await _slaService.updateEscalation(
        widget.caseId,
        escalation.id,
        status: 'resolved',
        resolutionNotes: notesController.text.trim().isNotEmpty ? notesController.text.trim() : null,
      );
      if (res.isSuccess) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Escalation marked as resolved.')),
          );
        }
        _loadAllData();
      }
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
                  Tab(text: '🤖 AI Copilot'),
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
                              _buildAICopilotTab(),
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
    final activeEscalation = _escalations.where((e) => e.isActive).firstOrNull;

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildLifecycleTracker(_caseData!.status),
          const SizedBox(height: 16),

          // Escalation Alert Banner
          if (_caseData!.isEscalated || activeEscalation != null) ...[
            _buildEscalationBanner(activeEscalation),
            const SizedBox(height: 16),
          ],

          // SLA & Deadlines Card
          if (_slaData != null) ...[
            _buildSLACard(),
            const SizedBox(height: 16),
          ],

          // Multi-Signal Operational Risk Card (Staff Only)
          if (!_isCitizen && _riskData != null) ...[
            _buildRiskAnalysisCard(),
            const SizedBox(height: 16),
          ],

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
                ElevatedButton.icon(
                  onPressed: _showEscalateDialog,
                  icon: const Icon(Icons.warning_amber_rounded, size: 16),
                  label: const Text('Escalate Case'),
                  style: ElevatedButton.styleFrom(backgroundColor: AppColors.statusError),
                ),
              ],
            ),
            const SizedBox(height: 20),
          ],


          // Timeline Section
          const Text('Chronological Case Journey', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
          const SizedBox(height: 10),
          CaseTimelineWidget(caseId: widget.caseId),
        ],
      ),
    );
  }


  // ---------------------------------------------------------------------------
  // Tab 2: AI Copilot & Insights (Staff Only)
  // ---------------------------------------------------------------------------
  Widget _buildAICopilotTab() {
    if (_aiAnalysis == null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.auto_awesome, size: 48, color: AppColors.primary),
              const SizedBox(height: 12),
              const Text('AI Triage & Copilot Not Run Yet', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
              const SizedBox(height: 6),
              const Text('Run AI understanding to generate category, priority, and next-step recommendations.',
                  textAlign: TextAlign.center, style: TextStyle(fontSize: 13, color: AppColors.textSecondary)),
              const SizedBox(height: 18),
              ElevatedButton.icon(
                onPressed: _isAnalyzingAI ? null : _handleRunAIAnalysis,
                icon: _isAnalyzingAI
                    ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2))
                    : const Icon(Icons.play_arrow_rounded),
                label: const Text('Run AI Analysis Now'),
              ),
            ],
          ),
        ),
      );
    }

    final confPct = (_aiAnalysis!.confidenceScore * 100).toInt();

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header Triage Summary Card
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: [AppColors.primary.withOpacity(0.08), AppColors.secondary.withOpacity(0.06)],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
              borderRadius: BorderRadius.circular(14),
              border: Border.all(color: AppColors.primary.withOpacity(0.2)),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Row(
                      children: [
                        const Icon(Icons.auto_awesome, color: AppColors.primary, size: 20),
                        const SizedBox(width: 8),
                        Text('AI Triage Engine ($confPct% Confidence)',
                            style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: AppColors.primary)),
                      ],
                    ),
                    IconButton(
                      icon: const Icon(Icons.refresh, size: 18, color: AppColors.primary),
                      tooltip: 'Re-run AI Analysis',
                      onPressed: _handleRunAIAnalysis,
                    ),
                  ],
                ),
                const SizedBox(height: 10),
                Text(_aiAnalysis!.summary ?? 'No summary available.', style: const TextStyle(fontSize: 13, height: 1.4)),
                const Divider(height: 20),
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: [
                    Chip(
                      label: Text('Category: ${_aiAnalysis!.suggestedCategoryName ?? "General"}'),
                      backgroundColor: AppColors.surface,
                      labelStyle: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold),
                    ),
                    Chip(
                      label: Text('Priority: ${_aiAnalysis!.suggestedPriority?.toUpperCase() ?? "MEDIUM"}'),
                      backgroundColor: AppColors.surface,
                      labelStyle: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: AppColors.statusWarning),
                    ),
                    if (_aiAnalysis!.suggestedTeamName != null)
                      Chip(
                        label: Text('Team: ${_aiAnalysis!.suggestedTeamName}'),
                        backgroundColor: AppColors.surface,
                        labelStyle: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: AppColors.secondary),
                      ),
                  ],
                ),
                const SizedBox(height: 12),
                ElevatedButton.icon(
                  onPressed: _handleApplyAISuggestions,
                  icon: const Icon(Icons.done_all, size: 16),
                  label: const Text('Apply AI Suggestions to Case'),
                  style: ElevatedButton.styleFrom(minimumSize: const Size.fromHeight(40)),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),

          // Risk Alert Card (if any)
          if (_aiAnalysis!.riskInsight != null) ...[
            Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: AppColors.statusError.withOpacity(0.08),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: AppColors.statusError.withOpacity(0.3)),
              ),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Icon(Icons.warning_amber_rounded, color: AppColors.statusError, size: 22),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Text(
                      _aiAnalysis!.riskInsight!,
                      style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: AppColors.statusError, height: 1.3),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),
          ],

          // Missing Information Section
          if (_aiAnalysis!.missingInformation.isNotEmpty) ...[
            const Text('Missing Information Flags', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
            const SizedBox(height: 8),
            Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: AppColors.surface,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: AppColors.border),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  ..._aiAnalysis!.missingInformation.map(
                    (msg) => Padding(
                      padding: const EdgeInsets.symmetric(vertical: 4),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Icon(Icons.help_outline, color: AppColors.statusWarning, size: 16),
                          const SizedBox(width: 8),
                          Expanded(child: Text(msg, style: const TextStyle(fontSize: 12))),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 10),
                  OutlinedButton.icon(
                    onPressed: () => _showCommunicationCopilotDialog(defaultType: 'information_request'),
                    icon: const Icon(Icons.chat_bubble_outline, size: 16),
                    label: const Text('Draft Query with Copilot'),
                    style: OutlinedButton.styleFrom(minimumSize: const Size.fromHeight(36)),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),
          ],

          // Recommended Next Action Card
          if (_aiAnalysis!.recommendedAction != null) ...[
            const Text('Recommended Next Step', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
            const SizedBox(height: 8),
            Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: AppColors.surface,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: AppColors.border),
              ),
              child: Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(8),
                    decoration: BoxDecoration(
                      color: AppColors.secondary.withOpacity(0.1),
                      shape: BoxShape.circle,
                    ),
                    child: const Icon(Icons.bolt, color: AppColors.secondary, size: 20),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Text(_aiAnalysis!.recommendedAction!, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w500)),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),
          ],

          // Communication Copilot Triggers
          const Text('Communication Copilot', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
          const SizedBox(height: 8),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              ActionChip(
                avatar: const Icon(Icons.question_answer_outlined, size: 16),
                label: const Text('Info Request Draft'),
                onPressed: () => _showCommunicationCopilotDialog(defaultType: 'information_request'),
              ),
              ActionChip(
                avatar: const Icon(Icons.update, size: 16),
                label: const Text('Progress Update Draft'),
                onPressed: () => _showCommunicationCopilotDialog(defaultType: 'progress_update'),
              ),
              ActionChip(
                avatar: const Icon(Icons.task_alt, size: 16),
                label: const Text('Resolution Draft'),
                onPressed: () => _showCommunicationCopilotDialog(defaultType: 'resolution_message'),
              ),
              ActionChip(
                avatar: const Icon(Icons.warning_outlined, size: 16),
                label: const Text('Escalation Memo'),
                onPressed: () => _showCommunicationCopilotDialog(defaultType: 'escalation_summary'),
              ),
            ],
          ),
          const SizedBox(height: 20),

          // Duplicate / Similar Complaints
          if (_aiAnalysis!.duplicateCases.isNotEmpty) ...[
            const Text('Potential Similar / Duplicate Complaints', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
            const SizedBox(height: 8),
            ListView.separated(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              itemCount: _aiAnalysis!.duplicateCases.length,
              separatorBuilder: (_, __) => const SizedBox(height: 8),
              itemBuilder: (context, idx) {
                final dup = _aiAnalysis!.duplicateCases[idx];
                final matchPct = (dup.similarityScore * 100).toInt();
                return Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: AppColors.surface,
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: AppColors.border),
                  ),
                  child: Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                        decoration: BoxDecoration(
                          color: AppColors.primary.withOpacity(0.1),
                          borderRadius: BorderRadius.circular(6),
                        ),
                        child: Text('$matchPct% Match',
                            style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 11, color: AppColors.primary)),
                      ),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text('${dup.caseNumber}: ${dup.title}',
                                style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12),
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis),
                            const SizedBox(height: 2),
                            Text(dup.reason, style: const TextStyle(fontSize: 11, color: AppColors.textSecondary)),
                          ],
                        ),
                      ),
                    ],
                  ),
                );
              },
            ),
          ],
        ],
      ),
    );
  }

  // ---------------------------------------------------------------------------
  // Tab 3: Messages (Citizen <-> Staff Communication)
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
  // Tab 4: Internal Notes (Staff Only)
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
  // Tab 5: Tasks (Staff Only Checklist)
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
  // Tab 6: Investigation (Staff Only Findings)
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
  // Tab 7: Evidence & Files
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

  Widget _buildEscalationBanner(EscalationModel? activeEscalation) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AppColors.statusError.withOpacity(0.09),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.statusError.withOpacity(0.35), width: 1.5),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.warning_amber_rounded, color: AppColors.statusError, size: 22),
              const SizedBox(width: 8),
              const Expanded(
                child: Text(
                  'CASE ESCALATED TO LEADERSHIP',
                  style: TextStyle(fontWeight: FontWeight.bold, color: AppColors.statusError, fontSize: 13, letterSpacing: 0.5),
                ),
              ),
              if (_isLeadOrManager && activeEscalation != null)
                TextButton.icon(
                  onPressed: () => _showResolveEscalationDialog(activeEscalation),
                  icon: const Icon(Icons.check_circle_outline, size: 16, color: AppColors.statusSuccess),
                  label: const Text('Resolve', style: TextStyle(color: AppColors.statusSuccess, fontWeight: FontWeight.bold, fontSize: 12)),
                ),
            ],
          ),
          if (activeEscalation != null) ...[
            const SizedBox(height: 6),
            Text(
              activeEscalation.reason,
              style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w500, color: AppColors.textPrimary),
            ),
            const SizedBox(height: 4),
            Text(
              'Trigger: ${activeEscalation.triggerType.replaceAll("_", " ").toUpperCase()} • Logged by ${activeEscalation.escalatedByName ?? "System"}',
              style: const TextStyle(fontSize: 11, color: AppColors.textSecondary),
            ),
          ] else ...[
            const SizedBox(height: 6),
            const Text(
              'This case has been flagged for prioritized managerial intervention.',
              style: TextStyle(fontSize: 12, color: AppColors.textSecondary),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildSLACard() {
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
              const Row(
                children: [
                  Icon(Icons.timer_outlined, size: 18, color: AppColors.primary),
                  SizedBox(width: 6),
                  Text('SLA & Resolution Target', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                ],
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: _slaData!.statusColor.withOpacity(0.12),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Text(
                  _slaData!.resolutionRemainingText,
                  style: TextStyle(color: _slaData!.statusColor, fontWeight: FontWeight.bold, fontSize: 11),
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          ClipRRect(
            borderRadius: BorderRadius.circular(4),
            child: LinearProgressIndicator(
              value: (_slaData!.resolutionProgressPercentage / 100.0).clamp(0.0, 1.0),
              backgroundColor: AppColors.border,
              valueColor: AlwaysStoppedAnimation<Color>(_slaData!.statusColor),
              minHeight: 6,
            ),
          ),
          const SizedBox(height: 10),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                'Target: ${_slaData!.resolutionTargetHours}h resolution • ${_slaData!.responseTargetHours}h first action',
                style: const TextStyle(fontSize: 11, color: AppColors.textSecondary),
              ),
              if (!_isCitizen)
                InkWell(
                  onTap: _handleRecalculateSLA,
                  child: const Text('Recalculate', style: TextStyle(fontSize: 11, color: AppColors.primary, fontWeight: FontWeight.bold)),
                ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildRiskAnalysisCard() {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: _riskData!.tierColor.withOpacity(0.3)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  Icon(Icons.shield_outlined, size: 18, color: _riskData!.tierColor),
                  const SizedBox(width: 6),
                  Text(
                    'Operational Risk (${_riskData!.riskScore}/100)',
                    style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: _riskData!.tierColor),
                  ),
                ],
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: _riskData!.tierColor.withOpacity(0.12),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Text(
                  '${_riskData!.riskTier.toUpperCase()} RISK',
                  style: TextStyle(color: _riskData!.tierColor, fontWeight: FontWeight.bold, fontSize: 11),
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          ..._riskData!.riskFactors.map(
            (factor) => Padding(
              padding: const EdgeInsets.symmetric(vertical: 2.0),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('• ', style: TextStyle(color: _riskData!.tierColor, fontWeight: FontWeight.bold)),
                  Expanded(
                    child: Text(factor, style: const TextStyle(fontSize: 12, color: AppColors.textSecondary)),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}


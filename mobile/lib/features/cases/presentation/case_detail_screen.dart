import 'package:flutter/material.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../auth/data/auth_models.dart';
import '../../../auth/data/auth_service.dart';
import '../data/case_models.dart';
import '../data/case_service.dart';

class CaseDetailScreen extends StatefulWidget {
  final int caseId;

  const CaseDetailScreen({super.key, required this.caseId});

  @override
  State<CaseDetailScreen> createState() => _CaseDetailScreenState();
}

class _CaseDetailScreenState extends State<CaseDetailScreen> {
  final CaseService _caseService = CaseService();
  bool _isLoading = true;
  CaseModel? _caseData;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _loadCaseDetails();
  }

  Future<void> _loadCaseDetails() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    final res = await _caseService.getCaseDetails(widget.caseId);

    if (!mounted) return;

    setState(() {
      _isLoading = false;
      if (res.isSuccess && res.data != null) {
        _caseData = res.data;
      } else {
        _errorMessage = res.errorMessage ?? 'Failed to load case details.';
      }
    });
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
        _loadCaseDetails();
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
        _loadCaseDetails();
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
      _loadCaseDetails();
    }
  }

  @override
  Widget build(BuildContext context) {
    final currentUser = AuthService.currentUser;
    final isCitizen = currentUser?.role == UserRole.requester;

    return Scaffold(
      appBar: AppBar(
        title: Text(_caseData != null ? _caseData!.caseNumber : 'Case Details'),
        actions: [
          IconButton(icon: const Icon(Icons.refresh), onPressed: _loadCaseDetails),
        ],
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
                        ElevatedButton(onPressed: _loadCaseDetails, child: const Text('Retry')),
                      ],
                    ),
                  ),
                )
              : _caseData == null
                  ? const Center(child: Text('Case not found.'))
                  : SingleChildScrollView(
                      padding: const EdgeInsets.all(16.0),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          // Lifecycle Progress Indicator
                          _buildLifecycleTracker(_caseData!.status),
                          const SizedBox(height: 20),

                          // Header Card
                          Container(
                            padding: const EdgeInsets.all(18),
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
                                  style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: AppColors.textPrimary),
                                ),
                                const SizedBox(height: 10),
                                Text(
                                  _caseData!.description,
                                  style: const TextStyle(fontSize: 14, color: AppColors.textSecondary, height: 1.4),
                                ),
                                const Divider(height: 24),
                                Row(
                                  children: [
                                    const Icon(Icons.location_on_outlined, size: 16, color: AppColors.textMuted),
                                    const SizedBox(width: 4),
                                    Text('${_caseData!.ward ?? "Ward 12"} ${_caseData!.landmark != null ? "• ${_caseData!.landmark}" : ""}',
                                        style: const TextStyle(fontSize: 12, color: AppColors.textSecondary)),
                                  ],
                                ),
                              ],
                            ),
                          ),
                          const SizedBox(height: 16),

                          // Resolution Confirmation Card for Citizen
                          if (isCitizen && _caseData!.status == CaseStatus.resolutionProposed) ...[
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

                          // Staff Quick Action Bar
                          if (!isCitizen) ...[
                            const Text('Operator Actions', style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold)),
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

                          // Case Timeline
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
                                                  entry.action.replaceAll('_', ' '),
                                                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
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
                    ),
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

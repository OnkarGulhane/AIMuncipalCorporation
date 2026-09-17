import 'package:flutter/material.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../auth/data/auth_models.dart';
import '../../../cases/data/case_models.dart';
import '../../../cases/data/case_service.dart';
import '../../../cases/presentation/case_detail_screen.dart';
import '../../../cases/presentation/create_case_screen.dart';
import '../../data/analytics_models.dart';
import '../../data/analytics_service.dart';

// ---------------------------------------------------------------------------
// 1. CITIZEN / REQUESTER VIEW
// ---------------------------------------------------------------------------
class CitizenDashboardView extends StatefulWidget {
  final UserModel user;

  const CitizenDashboardView({super.key, required this.user});

  @override
  State<CitizenDashboardView> createState() => _CitizenDashboardViewState();
}

class _CitizenDashboardViewState extends State<CitizenDashboardView> {
  final CaseService _caseService = CaseService();
  final AnalyticsService _analyticsService = AnalyticsService();

  bool _isLoading = true;
  List<CaseModel> _myCases = [];
  CitizenAnalyticsModel? _analytics;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    setState(() => _isLoading = true);
    final caseRes = await _caseService.listCases();
    final anaRes = await _analyticsService.getCitizenAnalytics();

    if (!mounted) return;
    setState(() {
      _isLoading = false;
      if (caseRes.isSuccess && caseRes.data != null) {
        _myCases = caseRes.data!.items;
      }
      if (anaRes.isSuccess && anaRes.data != null) {
        _analytics = anaRes.data;
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final activeCount = _analytics?.activeCount ?? _myCases.where((c) => c.status != CaseStatus.closed && c.status != CaseStatus.confirmed).length;
    final waitingInfo = _analytics?.waitingInfoCount ?? 0;
    final pendingConf = _analytics?.pendingConfirmationCount ?? 0;
    final resolvedCount = _analytics?.resolvedCount ?? 0;

    return RefreshIndicator(
      onRefresh: _loadData,
      child: ListView(
        padding: const EdgeInsets.all(16.0),
        children: [
          // Welcome Card
          Container(
            padding: const EdgeInsets.all(18),
            decoration: BoxDecoration(
              gradient: const LinearGradient(
                colors: [AppColors.primary, AppColors.primaryLight],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
              borderRadius: BorderRadius.circular(16),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Namaste, ${widget.user.fullName.split(" ").first}!',
                  style: const TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 4),
                Text(
                  'Reporting Ward: ${widget.user.ward ?? "Ward 12"}',
                  style: const TextStyle(color: Colors.white70, fontSize: 13),
                ),
                const SizedBox(height: 16),
                ElevatedButton.icon(
                  onPressed: () {
                    Navigator.of(context).push(
                      MaterialPageRoute(builder: (_) => const CreateCaseScreen()),
                    ).then((_) => _loadData());
                  },
                  icon: const Icon(Icons.add_photo_alternate, size: 20),
                  label: const Text('Report New Complaint'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.white,
                    foregroundColor: AppColors.primary,
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),

          // Summary Stats Grid
          Row(
            children: [
              _buildMetricCard('Active', activeCount.toString(), Icons.pending_actions, AppColors.primary),
              const SizedBox(width: 8),
              _buildMetricCard('Action Needed', waitingInfo.toString(), Icons.help_outline, AppColors.warning),
              const SizedBox(width: 8),
              _buildMetricCard('Pending Review', pendingConf.toString(), Icons.verified_outlined, const Color(0xFF0284C7)),
              const SizedBox(width: 8),
              _buildMetricCard('Resolved', resolvedCount.toString(), Icons.check_circle_outline, AppColors.secondary),
            ],
          ),
          const SizedBox(height: 20),

          // Quick Report Categories
          const Text(
            'Quick Report Categories',
            style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: AppColors.textPrimary),
          ),
          const SizedBox(height: 10),

          Row(
            children: [
              _buildCategoryTile(Icons.traffic, 'Road & Potholes', AppColors.primary, 'Pothole'),
              const SizedBox(width: 10),
              _buildCategoryTile(Icons.delete_outline, 'Garbage Overflow', AppColors.secondary, 'Garbage'),
              const SizedBox(width: 10),
              _buildCategoryTile(Icons.water_drop_outlined, 'Water Supply', const Color(0xFF0284C7), 'Water'),
            ],
          ),
          const SizedBox(height: 24),

          // My Complaints Section
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text(
                'My Grievance Trackers',
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: AppColors.textPrimary),
              ),
              Text(
                '${_myCases.length} Cases',
                style: const TextStyle(color: AppColors.textMuted, fontSize: 13),
              ),
            ],
          ),
          const SizedBox(height: 10),

          if (_isLoading)
            const Center(child: Padding(padding: EdgeInsets.all(24.0), child: CircularProgressIndicator()))
          else if (_myCases.isEmpty)
            Container(
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                color: AppColors.surface,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: AppColors.border),
              ),
              child: const Column(
                children: [
                  Icon(Icons.inbox_outlined, size: 36, color: AppColors.textMuted),
                  SizedBox(height: 8),
                  Text('No complaints reported yet.', style: TextStyle(color: AppColors.textSecondary, fontWeight: FontWeight.bold)),
                  Text('Use the button above to report a civic issue.', style: TextStyle(color: AppColors.textMuted, fontSize: 12)),
                ],
              ),
            )
          else
            ListView.separated(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              itemCount: _myCases.length,
              separatorBuilder: (_, __) => const SizedBox(height: 10),
              itemBuilder: (context, idx) {
                final item = _myCases[idx];
                return InkWell(
                  onTap: () {
                    Navigator.of(context).push(
                      MaterialPageRoute(builder: (_) => CaseDetailScreen(caseId: item.id)),
                    ).then((_) => _loadData());
                  },
                  child: Container(
                    padding: const EdgeInsets.all(16),
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
                              item.caseNumber,
                              style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: AppColors.primary),
                            ),
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                              decoration: BoxDecoration(
                                color: item.status.badgeColor.withOpacity(0.12),
                                borderRadius: BorderRadius.circular(12),
                              ),
                              child: Text(
                                item.status.displayName,
                                style: TextStyle(color: item.status.badgeColor, fontSize: 11, fontWeight: FontWeight.bold),
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 8),
                        Text(item.title, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w600)),
                        const SizedBox(height: 6),
                        Text(
                          '${item.ward ?? "Ward 12"} • Reported ${_formatDate(item.createdAt)}',
                          style: const TextStyle(color: AppColors.textMuted, fontSize: 12),
                        ),
                      ],
                    ),
                  ),
                );
              },
            ),
        ],
      ),
    );
  }

  String _formatDate(DateTime dt) {
    return '${dt.day}/${dt.month}/${dt.year}';
  }

  Widget _buildMetricCard(String label, String value, IconData icon, Color color) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 8),
        decoration: BoxDecoration(
          color: color.withOpacity(0.08),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: color.withOpacity(0.2)),
        ),
        child: Column(
          children: [
            Icon(icon, color: color, size: 18),
            const SizedBox(height: 4),
            Text(value, style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: color)),
            const SizedBox(height: 2),
            Text(label, textAlign: TextAlign.center, maxLines: 1, overflow: TextOverflow.ellipsis, style: const TextStyle(fontSize: 10, color: AppColors.textSecondary)),
          ],
        ),
      ),
    );
  }

  Widget _buildCategoryTile(IconData icon, String title, Color color, String catTag) {
    return Expanded(
      child: InkWell(
        onTap: () {
          Navigator.of(context).push(
            MaterialPageRoute(builder: (_) => CreateCaseScreen(initialCategory: catTag)),
          ).then((_) => _loadData());
        },
        child: Container(
          padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 8),
          decoration: BoxDecoration(
            color: color.withOpacity(0.08),
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: color.withOpacity(0.2)),
          ),
          child: Column(
            children: [
              Icon(icon, color: color, size: 26),
              const SizedBox(height: 8),
              Text(
                title,
                textAlign: TextAlign.center,
                style: TextStyle(color: color, fontSize: 11, fontWeight: FontWeight.bold),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

// ---------------------------------------------------------------------------
// 2. CASE OPERATOR VIEW
// ---------------------------------------------------------------------------
class OperatorDashboardView extends StatefulWidget {
  final UserModel user;

  const OperatorDashboardView({super.key, required this.user});

  @override
  State<OperatorDashboardView> createState() => _OperatorDashboardViewState();
}

class _OperatorDashboardViewState extends State<OperatorDashboardView> {
  final CaseService _caseService = CaseService();
  final AnalyticsService _analyticsService = AnalyticsService();

  bool _isLoading = true;
  List<CaseModel> _queueCases = [];
  OperatorAnalyticsModel? _analytics;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    setState(() => _isLoading = true);
    final caseRes = await _caseService.listCases();
    final anaRes = await _analyticsService.getOperatorAnalytics();

    if (!mounted) return;
    setState(() {
      _isLoading = false;
      if (caseRes.isSuccess && caseRes.data != null) {
        _queueCases = resFilter(caseRes.data!.items);
      }
      if (anaRes.isSuccess && anaRes.data != null) {
        _analytics = anaRes.data;
      }
    });
  }

  List<CaseModel> resFilter(List<CaseModel> items) {
    return items;
  }

  @override
  Widget build(BuildContext context) {
    final activeAssigned = _analytics?.assignedActiveCount ?? _queueCases.where((c) => c.status == CaseStatus.assigned).length;
    final highPriority = _analytics?.highPriorityCount ?? _queueCases.where((c) => c.priority == CasePriority.high || c.priority == CasePriority.critical).length;
    final pendingTasks = _analytics?.pendingTasksCount ?? 0;
    final escalations = _analytics?.activeEscalationsCount ?? 0;

    return RefreshIndicator(
      onRefresh: _loadData,
      child: ListView(
        padding: const EdgeInsets.all(16.0),
        children: [
          Row(
            children: [
              _buildMetricTile('Assigned Queue', activeAssigned.toString(), AppColors.primary),
              const SizedBox(width: 8),
              _buildMetricTile('High / Critical', highPriority.toString(), AppColors.statusError),
              const SizedBox(width: 8),
              _buildMetricTile('Pending Tasks', pendingTasks.toString(), const Color(0xFF0284C7)),
              const SizedBox(width: 8),
              _buildMetricTile('Escalated', escalations.toString(), AppColors.accent),
            ],
          ),
          const SizedBox(height: 20),

          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text(
                'Operational Case Queue',
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: AppColors.textPrimary),
              ),
              Text(
                '${_queueCases.length} items',
                style: const TextStyle(fontSize: 12, color: AppColors.textMuted),
              ),
            ],
          ),
          const SizedBox(height: 10),

          if (_isLoading)
            const Center(child: Padding(padding: EdgeInsets.all(24.0), child: CircularProgressIndicator()))
          else if (_queueCases.isEmpty)
            Container(
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                color: AppColors.surface,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: AppColors.border),
              ),
              child: const Center(
                child: Text('No active cases assigned to your queue.', style: TextStyle(color: AppColors.textMuted)),
              ),
            )
          else
            ListView.separated(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              itemCount: _queueCases.length,
              separatorBuilder: (_, __) => const SizedBox(height: 10),
              itemBuilder: (context, idx) {
                final item = _queueCases[idx];
                return InkWell(
                  onTap: () {
                    Navigator.of(context).push(
                      MaterialPageRoute(builder: (_) => CaseDetailScreen(caseId: item.id)),
                    ).then((_) => _loadData());
                  },
                  child: Container(
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
                              '${item.caseNumber} • ${item.ward ?? "Ward 12"}',
                              style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: AppColors.textSecondary),
                            ),
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                              decoration: BoxDecoration(
                                color: item.status.badgeColor.withOpacity(0.12),
                                borderRadius: BorderRadius.circular(10),
                              ),
                              child: Text(
                                item.status.displayName,
                                style: TextStyle(color: item.status.badgeColor, fontSize: 10, fontWeight: FontWeight.bold),
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 6),
                        Text(item.title, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w600)),
                        const SizedBox(height: 6),
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Text('Priority: ${item.priority.name.toUpperCase()}',
                                style: TextStyle(fontSize: 11, color: item.priority.color, fontWeight: FontWeight.bold)),
                            const Text('Open Workspace →', style: TextStyle(fontSize: 12, color: AppColors.primary, fontWeight: FontWeight.w600)),
                          ],
                        ),
                      ],
                    ),
                  ),
                );
              },
            ),
        ],
      ),
    );
  }

  Widget _buildMetricTile(String label, String value, Color color) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 6),
        decoration: BoxDecoration(
          color: color.withOpacity(0.08),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: color.withOpacity(0.2)),
        ),
        child: Column(
          children: [
            Text(value, style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: color)),
            const SizedBox(height: 4),
            Text(label, textAlign: TextAlign.center, maxLines: 1, overflow: TextOverflow.ellipsis, style: TextStyle(fontSize: 10, color: color, fontWeight: FontWeight.w600)),
          ],
        ),
      ),
    );
  }
}

// ---------------------------------------------------------------------------
// 3. TEAM LEAD / SUPERVISOR VIEW
// ---------------------------------------------------------------------------
class TeamLeadDashboardView extends StatefulWidget {
  final UserModel user;

  const TeamLeadDashboardView({super.key, required this.user});

  @override
  State<TeamLeadDashboardView> createState() => _TeamLeadDashboardViewState();
}

class _TeamLeadDashboardViewState extends State<TeamLeadDashboardView> {
  final AnalyticsService _service = AnalyticsService();
  bool _isLoading = true;
  TeamLeadAnalyticsModel? _analytics;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() => _isLoading = true);
    final res = await _service.getTeamLeadAnalytics();
    if (!mounted) return;
    setState(() {
      _isLoading = false;
      if (res.isSuccess && res.data != null) {
        _analytics = res.data;
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return RefreshIndicator(
      onRefresh: _load,
      child: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : ListView(
              padding: const EdgeInsets.all(16.0),
              children: [
                // Team Banner
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    gradient: const LinearGradient(
                      colors: [Color(0xFF7C3AED), Color(0xFF6D28D9)],
                    ),
                    borderRadius: BorderRadius.circular(14),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(_analytics?.teamName ?? 'Field Response Squad', style: const TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold)),
                      const SizedBox(height: 4),
                      Text('Department: ${_analytics?.departmentName ?? widget.user.department ?? "Municipal Operations"}', style: const TextStyle(color: Colors.white70, fontSize: 12)),
                      const SizedBox(height: 14),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceAround,
                        children: [
                          _LeadMetric('Team Cases', '${_analytics?.totalCases ?? 0}'),
                          _LeadMetric('SLA Compliance', '${_analytics?.slaCompliancePercent.toStringAsFixed(1) ?? "100"}%'),
                          _LeadMetric('Escalations', '${_analytics?.activeEscalations ?? 0} Active'),
                        ],
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 20),

                // Operator Workload Roster
                const Text('Field Operator Workloads', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                const SizedBox(height: 10),

                if (_analytics?.operatorWorkloads.isEmpty ?? true)
                  Container(
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: AppColors.surface,
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: AppColors.border),
                    ),
                    child: const Text('No operators assigned to this department squad.', style: TextStyle(color: AppColors.textMuted)),
                  )
                else
                  ListView.separated(
                    shrinkWrap: true,
                    physics: const NeverScrollableScrollPhysics(),
                    itemCount: _analytics!.operatorWorkloads.length,
                    separatorBuilder: (_, __) => const SizedBox(height: 8),
                    itemBuilder: (context, idx) {
                      final op = _analytics!.operatorWorkloads[idx];
                      return Container(
                        padding: const EdgeInsets.all(14),
                        decoration: BoxDecoration(
                          color: AppColors.surface,
                          borderRadius: BorderRadius.circular(12),
                          border: Border.all(color: AppColors.border),
                        ),
                        child: Row(
                          children: [
                            CircleAvatar(
                              backgroundColor: AppColors.primary.withOpacity(0.12),
                              child: Text(op.operatorName.substring(0, 1).toUpperCase(), style: const TextStyle(color: AppColors.primary, fontWeight: FontWeight.bold)),
                            ),
                            const SizedBox(width: 12),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(op.operatorName, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                                  const SizedBox(height: 2),
                                  Text('${op.completedCases} completed • ${op.overdueCases} overdue', style: const TextStyle(fontSize: 11, color: AppColors.textMuted)),
                                ],
                              ),
                            ),
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                              decoration: BoxDecoration(
                                color: op.activeCases > 5 ? AppColors.warning.withOpacity(0.12) : AppColors.primary.withOpacity(0.12),
                                borderRadius: BorderRadius.circular(12),
                              ),
                              child: Text(
                                '${op.activeCases} active',
                                style: TextStyle(
                                  color: op.activeCases > 5 ? AppColors.warning : AppColors.primary,
                                  fontWeight: FontWeight.bold,
                                  fontSize: 12,
                                ),
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
}

class _LeadMetric extends StatelessWidget {
  final String label;
  final String value;
  const _LeadMetric(this.label, this.value);

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Text(value, style: const TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold)),
        Text(label, style: const TextStyle(color: Colors.white70, fontSize: 11)),
      ],
    );
  }
}

// ---------------------------------------------------------------------------
// 4. MUNICIPAL MANAGER VIEW
// ---------------------------------------------------------------------------
class ManagerDashboardView extends StatefulWidget {
  final UserModel user;

  const ManagerDashboardView({super.key, required this.user});

  @override
  State<ManagerDashboardView> createState() => _ManagerDashboardViewState();
}

class _ManagerDashboardViewState extends State<ManagerDashboardView> {
  final AnalyticsService _service = AnalyticsService();
  bool _isLoading = true;
  ManagerAnalyticsModel? _data;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() => _isLoading = true);
    final res = await _service.getManagerAnalytics();
    if (!mounted) return;
    setState(() {
      _isLoading = false;
      if (res.isSuccess && res.data != null) {
        _data = res.data;
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return RefreshIndicator(
      onRefresh: _load,
      child: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : ListView(
              padding: const EdgeInsets.all(16.0),
              children: [
                const Text('City-Wide Grievance Intelligence', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                const SizedBox(height: 12),

                // KPI Grid
                Row(
                  children: [
                    _buildStatCard('Total Cases', '${_data?.totalCases ?? 0}', Icons.bar_chart, AppColors.primary),
                    const SizedBox(width: 10),
                    _buildStatCard('Resolution Rate', '${_data?.resolutionRatePercent.toStringAsFixed(1) ?? "0"}%', Icons.check_circle, AppColors.statusSuccess),
                  ],
                ),
                const SizedBox(height: 10),
                Row(
                  children: [
                    _buildStatCard('Avg Resolution', '${_data?.avgResolutionTimeHours.toStringAsFixed(1) ?? "0"}h', Icons.timer, AppColors.secondary),
                    const SizedBox(width: 10),
                    _buildStatCard('SLA Compliance', '${_data?.slaCompliancePercent.toStringAsFixed(1) ?? "100"}%', Icons.verified, const Color(0xFF0284C7)),
                  ],
                ),
                const SizedBox(height: 20),

                // AI Operational Insights Card
                const Text('AI Operational Insights', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                const SizedBox(height: 10),

                if (_data?.aiOperationalInsights.isNotEmpty ?? false)
                  ..._data!.aiOperationalInsights.map((ins) {
                    final isHigh = ins.severity == 'critical' || ins.severity == 'high';
                    return Container(
                      margin: const EdgeInsets.only(bottom: 10),
                      padding: const EdgeInsets.all(14),
                      decoration: BoxDecoration(
                        color: (isHigh ? AppColors.accent : AppColors.primary).withOpacity(0.06),
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: (isHigh ? AppColors.accent : AppColors.primary).withOpacity(0.2)),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              Icon(Icons.auto_awesome, color: isHigh ? AppColors.accent : AppColors.primary, size: 20),
                              const SizedBox(width: 8),
                              Expanded(
                                child: Text(ins.title, style: TextStyle(fontWeight: FontWeight.bold, color: isHigh ? AppColors.accent : AppColors.primary, fontSize: 14)),
                              ),
                            ],
                          ),
                          const SizedBox(height: 6),
                          Text(ins.description, style: const TextStyle(fontSize: 13)),
                          const SizedBox(height: 6),
                          Text('💡 Recommendation: ${ins.recommendation}', style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: AppColors.textSecondary)),
                        ],
                      ),
                    );
                  }).toList()
                else
                  const SizedBox(),

                const SizedBox(height: 16),

                // Ward Intelligence Hotspots
                const Text('Ward Hotspots & Response Times', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                const SizedBox(height: 10),

                if (_data?.wardMetrics.isNotEmpty ?? false)
                  ListView.separated(
                    shrinkWrap: true,
                    physics: const NeverScrollableScrollPhysics(),
                    itemCount: _data!.wardMetrics.length,
                    separatorBuilder: (_, __) => const SizedBox(height: 8),
                    itemBuilder: (context, idx) {
                      final w = _data!.wardMetrics[idx];
                      return Container(
                        padding: const EdgeInsets.all(14),
                        decoration: BoxDecoration(
                          color: AppColors.surface,
                          borderRadius: BorderRadius.circular(12),
                          border: Border.all(color: AppColors.border),
                        ),
                        child: Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(w.ward, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                                const SizedBox(height: 2),
                                Text('${w.activeCases} active • ${w.highRiskCases} high risk', style: const TextStyle(fontSize: 12, color: AppColors.textMuted)),
                              ],
                            ),
                            Column(
                              crossAxisAlignment: CrossAxisAlignment.end,
                              children: [
                                Text('${w.totalCases} Total', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: AppColors.primary)),
                                if (w.topCategory != null)
                                  Text(w.topCategory!, style: const TextStyle(fontSize: 11, color: AppColors.textSecondary)),
                              ],
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

  Widget _buildStatCard(String title, String value, IconData icon, Color color) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: AppColors.surface,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: AppColors.border),
        ),
        child: Row(
          children: [
            Icon(icon, color: color, size: 28),
            const SizedBox(width: 12),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(value, style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: color)),
                Text(title, style: const TextStyle(fontSize: 11, color: AppColors.textMuted)),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

// ---------------------------------------------------------------------------
// 5. ADMINISTRATOR VIEW
// ---------------------------------------------------------------------------
class AdminDashboardView extends StatefulWidget {
  final UserModel user;

  const AdminDashboardView({super.key, required this.user});

  @override
  State<AdminDashboardView> createState() => _AdminDashboardViewState();
}

class _AdminDashboardViewState extends State<AdminDashboardView> {
  final AnalyticsService _service = AnalyticsService();
  bool _isLoading = true;
  SystemStatsModel? _stats;
  List<AuditLogEntryModel> _auditLogs = [];

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() => _isLoading = true);
    final statRes = await _service.getSystemStats();
    final logRes = await _service.getAuditLogs(limit: 5);

    if (!mounted) return;
    setState(() {
      _isLoading = false;
      if (statRes.isSuccess && statRes.data != null) {
        _stats = statRes.data;
      }
      if (logRes.isSuccess && logRes.data != null) {
        _auditLogs = logRes.data!;
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return RefreshIndicator(
      onRefresh: _load,
      child: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : ListView(
              padding: const EdgeInsets.all(16.0),
              children: [
                const Text('System Administration & Health', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                const SizedBox(height: 14),

                _buildAdminTile(Icons.people_outline, 'User Accounts', '${_stats?.totalUsers ?? 0} Total Active Accounts', AppColors.primary),
                const SizedBox(height: 10),
                _buildAdminTile(Icons.business_outlined, 'Departments & Teams', '${_stats?.totalDepartments ?? 0} Depts • ${_stats?.totalTeams ?? 0} Squads', AppColors.secondary),
                const SizedBox(height: 10),
                _buildAdminTile(Icons.category_outlined, 'Categories & Policies', '${_stats?.totalCategories ?? 0} Categories configured', const Color(0xFF8B5CF6)),
                const SizedBox(height: 10),
                _buildAdminTile(Icons.security, 'System Security & Database', 'PostgreSQL ${_stats?.databaseStatus ?? "Healthy"}', AppColors.statusSuccess),
                const SizedBox(height: 20),

                const Text('Recent Audit History', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                const SizedBox(height: 10),

                if (_auditLogs.isEmpty)
                  Container(
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: AppColors.surface,
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: AppColors.border),
                    ),
                    child: const Text('No audit events logged yet.', style: TextStyle(color: AppColors.textMuted)),
                  )
                else
                  ListView.separated(
                    shrinkWrap: true,
                    physics: const NeverScrollableScrollPhysics(),
                    itemCount: _auditLogs.length,
                    separatorBuilder: (_, __) => const SizedBox(height: 8),
                    itemBuilder: (context, idx) {
                      final log = _auditLogs[idx];
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
                                Text(log.caseNumber ?? 'System', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12, color: AppColors.primary)),
                                Text(
                                  '${log.createdAt.hour}:${log.createdAt.minute.toString().padLeft(2, '0')}',
                                  style: const TextStyle(fontSize: 11, color: AppColors.textMuted),
                                ),
                              ],
                            ),
                            const SizedBox(height: 4),
                            Text('${log.actorName ?? "System"}: ${log.action.replaceAll("_", " ").toUpperCase()}', style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600)),
                            if (log.notes != null) ...[
                              const SizedBox(height: 2),
                              Text(log.notes!, style: const TextStyle(fontSize: 12, color: AppColors.textMuted), maxLines: 2, overflow: TextOverflow.ellipsis),
                            ],
                          ],
                        ),
                      );
                    },
                  ),
              ],
            ),
    );
  }

  Widget _buildAdminTile(IconData icon, String title, String subtitle, Color color) {
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
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(
              color: color.withOpacity(0.1),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Icon(icon, color: color, size: 24),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w600)),
                Text(subtitle, style: const TextStyle(fontSize: 12, color: AppColors.textMuted)),
              ],
            ),
          ),
          const Icon(Icons.chevron_right, color: AppColors.textMuted),
        ],
      ),
    );
  }
}

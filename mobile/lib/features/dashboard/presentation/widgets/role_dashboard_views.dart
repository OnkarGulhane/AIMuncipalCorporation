import 'package:flutter/material.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../auth/data/auth_models.dart';
import '../../../cases/data/case_models.dart';
import '../../../cases/data/case_service.dart';
import '../../../cases/presentation/case_detail_screen.dart';
import '../../../cases/presentation/create_case_screen.dart';

// --- CITIZEN / REQUESTER VIEW ---
class CitizenDashboardView extends StatefulWidget {
  final UserModel user;

  const CitizenDashboardView({super.key, required this.user});

  @override
  State<CitizenDashboardView> createState() => _CitizenDashboardViewState();
}

class _CitizenDashboardViewState extends State<CitizenDashboardView> {
  final CaseService _caseService = CaseService();
  bool _isLoading = true;
  List<CaseModel> _myCases = [];

  @override
  void initState() {
    super.initState();
    _loadCases();
  }

  Future<void> _loadCases() async {
    setState(() => _isLoading = true);
    final res = await _caseService.listCases();
    if (!mounted) return;
    setState(() {
      _isLoading = false;
      if (res.isSuccess && res.data != null) {
        _myCases = res.data!.items;
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return RefreshIndicator(
      onRefresh: _loadCases,
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
                  'Reporting Ward: ${widget.user.ward ?? "Shivaji Nagar - Ward 12"}',
                  style: const TextStyle(color: Colors.white70, fontSize: 13),
                ),
                const SizedBox(height: 16),
                ElevatedButton.icon(
                  onPressed: () {
                    Navigator.of(context).push(
                      MaterialPageRoute(builder: (_) => const CreateCaseScreen()),
                    ).then((_) => _loadCases());
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
          const SizedBox(height: 20),

          // Quick Report Categories
          const Text(
            'Quick Report Categories',
            style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: AppColors.textPrimary),
          ),
          const SizedBox(height: 12),

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

          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text(
                'My Active Complaints',
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
                    ).then((_) => _loadCases());
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

  Widget _buildCategoryTile(IconData icon, String title, Color color, String catTag) {
    return Expanded(
      child: InkWell(
        onTap: () {
          Navigator.of(context).push(
            MaterialPageRoute(builder: (_) => CreateCaseScreen(initialCategory: catTag)),
          ).then((_) => _loadCases());
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

// --- CASE OPERATOR VIEW ---
class OperatorDashboardView extends StatefulWidget {
  final UserModel user;

  const OperatorDashboardView({super.key, required this.user});

  @override
  State<OperatorDashboardView> createState() => _OperatorDashboardViewState();
}

class _OperatorDashboardViewState extends State<OperatorDashboardView> {
  final CaseService _caseService = CaseService();
  bool _isLoading = true;
  List<CaseModel> _queueCases = [];

  @override
  void initState() {
    super.initState();
    _loadQueue();
  }

  Future<void> _loadQueue() async {
    setState(() => _isLoading = true);
    final res = await _caseService.listCases();
    if (!mounted) return;
    setState(() {
      _isLoading = false;
      if (res.isSuccess && res.data != null) {
        _queueCases = res.data!.items;
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final assignedCount = _queueCases.where((c) => c.status == CaseStatus.assigned).length;
    final highPriorityCount = _queueCases.where((c) => c.priority == CasePriority.high || c.priority == CasePriority.critical).length;

    return RefreshIndicator(
      onRefresh: _loadQueue,
      child: ListView(
        padding: const EdgeInsets.all(16.0),
        children: [
          Row(
            children: [
              _buildMetricTile('Assigned Queue', assignedCount.toString(), AppColors.primary),
              const SizedBox(width: 10),
              _buildMetricTile('High / Critical', highPriorityCount.toString(), AppColors.statusError),
              const SizedBox(width: 10),
              _buildMetricTile('Total Cases', _queueCases.length.toString(), AppColors.secondary),
            ],
          ),
          const SizedBox(height: 20),

          const Text(
            'Operational Case Queue',
            style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: AppColors.textPrimary),
          ),
          const SizedBox(height: 10),

          if (_isLoading)
            const Center(child: Padding(padding: EdgeInsets.all(24.0), child: CircularProgressIndicator()))
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
                    ).then((_) => _loadQueue());
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
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: color.withOpacity(0.08),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: color.withOpacity(0.2)),
        ),
        child: Column(
          children: [
            Text(value, style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: color)),
            const SizedBox(height: 4),
            Text(label, textAlign: TextAlign.center, style: TextStyle(fontSize: 11, color: color)),
          ],
        ),
      ),
    );
  }
}

// --- TEAM LEAD / SUPERVISOR VIEW ---
class TeamLeadDashboardView extends StatelessWidget {
  final UserModel user;

  const TeamLeadDashboardView({super.key, required this.user});

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(16.0),
      children: [
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
              const Text('Road Rapid Response Team Roster', style: TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold)),
              const SizedBox(height: 4),
              Text('Department: ${user.department ?? "Roads & Infrastructure"}', style: const TextStyle(color: Colors.white70, fontSize: 12)),
              const SizedBox(height: 12),
              const Row(
                mainAxisAlignment: MainAxisAlignment.spaceAround,
                children: [
                  _LeadMetric('Team Load', '24 Cases'),
                  _LeadMetric('SLA Met', '94.2%'),
                  _LeadMetric('Escalations', '2 Active'),
                ],
              ),
            ],
          ),
        ),
        const SizedBox(height: 20),

        const Text('At-Risk & Escalated Complaints', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
        const SizedBox(height: 10),

        _buildEscalationTile(
          caseNum: 'MC-2026-0799',
          title: 'Culvert block causing road flooding in heavy rain',
          operator: 'Rohan Deshmukh',
          reason: 'SLA breach approaching (< 2 hours remaining)',
        ),
      ],
    );
  }

  Widget _buildEscalationTile({
    required String caseNum,
    required String title,
    required String operator,
    required String reason,
  }) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.statusError.withOpacity(0.3)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(caseNum, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12)),
              const Chip(
                label: Text('ESCALATED', style: TextStyle(fontSize: 10, color: Colors.white, fontWeight: FontWeight.bold)),
                backgroundColor: AppColors.statusError,
                padding: EdgeInsets.zero,
                visualDensity: VisualDensity.compact,
              ),
            ],
          ),
          const SizedBox(height: 4),
          Text(title, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14)),
          const SizedBox(height: 6),
          Text('Assigned Operator: $operator', style: const TextStyle(fontSize: 12, color: AppColors.textSecondary)),
          Text('Reason: $reason', style: const TextStyle(fontSize: 12, color: AppColors.statusError)),
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

// --- MUNICIPAL MANAGER VIEW ---
class ManagerDashboardView extends StatelessWidget {
  final UserModel user;

  const ManagerDashboardView({super.key, required this.user});

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(16.0),
      children: [
        const Text('City-Wide Operations & Analytics', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
        const SizedBox(height: 12),

        Row(
          children: [
            _buildStatCard('Total Volume', '1,428', Icons.bar_chart, AppColors.primary),
            const SizedBox(width: 10),
            _buildStatCard('Resolved', '1,280', Icons.check_circle, AppColors.statusSuccess),
          ],
        ),
        const SizedBox(height: 10),
        Row(
          children: [
            _buildStatCard('Avg Resolution', '26.4h', Icons.timer, AppColors.secondary),
            const SizedBox(width: 10),
            _buildStatCard('SLA Compliance', '91.8%', Icons.verified, const Color(0xFF0284C7)),
          ],
        ),
        const SizedBox(height: 20),

        const Text('AI Pattern & Ward Hotspots', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
        const SizedBox(height: 10),

        Container(
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: AppColors.accent.withOpacity(0.06),
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: AppColors.accent.withOpacity(0.2)),
          ),
          child: const Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Icon(Icons.auto_awesome, color: AppColors.accent, size: 20),
                  SizedBox(width: 8),
                  Text('Emerging Cluster Alert (AI)', style: TextStyle(fontWeight: FontWeight.bold, color: AppColors.accent)),
                ],
              ),
              SizedBox(height: 8),
              Text(
                'High density of road damage complaints detected in Ward 12 near Shivaji Nagar main artery over last 48 hours. Suggesting preventive road resurfacing inspection.',
                style: TextStyle(fontSize: 13),
              ),
            ],
          ),
        ),
      ],
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

// --- ADMINISTRATOR VIEW ---
class AdminDashboardView extends StatelessWidget {
  final UserModel user;

  const AdminDashboardView({super.key, required this.user});

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(16.0),
      children: [
        const Text('System Administration & Master Data', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
        const SizedBox(height: 14),

        _buildAdminTile(Icons.people_outline, 'User & Staff Management', 'Configure accounts, roles, and status', AppColors.primary),
        const SizedBox(height: 10),
        _buildAdminTile(Icons.business_outlined, 'Departments & Teams', '5 Active Departments, 12 Teams', AppColors.secondary),
        const SizedBox(height: 10),
        _buildAdminTile(Icons.category_outlined, 'Categories & SLA Policies', '6 Categories, Standard SLAs configured', const Color(0xFF8B5CF6)),
        const SizedBox(height: 10),
        _buildAdminTile(Icons.security, 'Server-Side RBAC & Audit Trails', 'Audit log active, all transitions verified', AppColors.statusError),
      ],
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

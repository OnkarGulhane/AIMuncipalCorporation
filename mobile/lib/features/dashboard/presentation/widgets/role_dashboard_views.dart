import 'package:flutter/material.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../auth/data/auth_models.dart';

// --- CITIZEN / REQUESTER VIEW ---
class CitizenDashboardView extends StatelessWidget {
  final UserModel user;

  const CitizenDashboardView({super.key, required this.user});

  @override
  Widget build(BuildContext context) {
    return ListView(
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
                'Namaste, ${user.fullName.split(" ").first}!',
                style: const TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 4),
              Text(
                'Reporting Zone: ${user.ward ?? "Shivaji Nagar - Ward 12"}',
                style: const TextStyle(color: Colors.white70, fontSize: 13),
              ),
              const SizedBox(height: 16),
              ElevatedButton.icon(
                onPressed: () {},
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

        // Section Title
        const Text(
          'Quick Report Categories',
          style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: AppColors.textPrimary),
        ),
        const SizedBox(height: 12),

        // Quick Category Grid
        Row(
          children: [
            _buildCategoryTile(Icons.traffic, 'Road & Potholes', AppColors.primary),
            const SizedBox(width: 10),
            _buildCategoryTile(Icons.delete_outline, 'Garbage Overflow', AppColors.secondary),
            const SizedBox(width: 10),
            _buildCategoryTile(Icons.water_drop_outlined, 'Water Supply', const Color(0xFF0284C7)),
          ],
        ),
        const SizedBox(height: 24),

        const Text(
          'My Active Cases',
          style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: AppColors.textPrimary),
        ),
        const SizedBox(height: 10),

        _buildCaseCard(
          caseNumber: 'MC-2026-0891',
          title: 'Deep Pothole near Main Market Corner',
          status: 'Investigating',
          statusColor: AppColors.statusInfo,
          date: 'Reported 3 hours ago',
          department: 'Roads & Infrastructure',
        ),
        const SizedBox(height: 10),
        _buildCaseCard(
          caseNumber: 'MC-2026-0842',
          title: 'Streetlight Blinking continuously',
          status: 'Resolution Proposed',
          statusColor: AppColors.statusSuccess,
          date: 'Needs your confirmation',
          department: 'Electrical & Street Lighting',
          showConfirmAction: true,
        ),
      ],
    );
  }

  Widget _buildCategoryTile(IconData icon, String title, Color color) {
    return Expanded(
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
    );
  }

  Widget _buildCaseCard({
    required String caseNumber,
    required String title,
    required String status,
    required Color statusColor,
    required String date,
    required String department,
    bool showConfirmAction = false,
  }) {
    return Container(
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
                caseNumber,
                style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12, color: AppColors.textSecondary),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: statusColor.withOpacity(0.12),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Text(
                  status,
                  style: TextStyle(color: statusColor, fontSize: 11, fontWeight: FontWeight.bold),
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(title, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w600)),
          const SizedBox(height: 4),
          Text('$department • $date', style: const TextStyle(color: AppColors.textMuted, fontSize: 12)),
          if (showConfirmAction) ...[
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                  child: ElevatedButton(
                    onPressed: () {},
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppColors.statusSuccess,
                      padding: const EdgeInsets.symmetric(vertical: 8),
                    ),
                    child: const Text('Confirm Resolution', style: TextStyle(fontSize: 12)),
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: OutlinedButton(
                    onPressed: () {},
                    style: OutlinedButton.styleFrom(
                      foregroundColor: AppColors.statusError,
                      side: const BorderSide(color: AppColors.statusError),
                      padding: const EdgeInsets.symmetric(vertical: 8),
                    ),
                    child: const Text('Reject / Reopen', style: TextStyle(fontSize: 12)),
                  ),
                ),
              ],
            ),
          ],
        ],
      ),
    );
  }
}

// --- CASE OPERATOR VIEW ---
class OperatorDashboardView extends StatelessWidget {
  final UserModel user;

  const OperatorDashboardView({super.key, required this.user});

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(16.0),
      children: [
        Row(
          children: [
            _buildMetricTile('Assigned Queue', '8', AppColors.primary),
            const SizedBox(width: 10),
            _buildMetricTile('High Priority', '3', AppColors.statusError),
            const SizedBox(width: 10),
            _buildMetricTile('SLA At-Risk', '1', AppColors.statusWarning),
          ],
        ),
        const SizedBox(height: 20),

        const Text(
          'Active Case Queue',
          style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: AppColors.textPrimary),
        ),
        const SizedBox(height: 10),

        _buildOperatorCaseItem(
          caseNum: 'MC-2026-0891',
          title: 'Road Cave-in on MG Road Junction',
          ward: 'Ward 12',
          priority: 'CRITICAL',
          priorityColor: AppColors.statusError,
          slaRemaining: '4 hrs remaining',
          aiSummary: 'AI identified high public risk. Immediate road closure task suggested.',
        ),
        const SizedBox(height: 10),
        _buildOperatorCaseItem(
          caseNum: 'MC-2026-0887',
          title: 'Pothole patch needed near school entrance',
          ward: 'Ward 12',
          priority: 'HIGH',
          priorityColor: AppColors.statusWarning,
          slaRemaining: '18 hrs remaining',
          aiSummary: 'Matching 2 duplicate complaints. Asphalt batch dispatch recommended.',
        ),
      ],
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

  Widget _buildOperatorCaseItem({
    required String caseNum,
    required String title,
    required String ward,
    required String priority,
    required Color priorityColor,
    required String slaRemaining,
    required String aiSummary,
  }) {
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
              Text('$caseNum • $ward', style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: AppColors.textSecondary)),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                decoration: BoxDecoration(
                  color: priorityColor.withOpacity(0.12),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Text(priority, style: TextStyle(color: priorityColor, fontSize: 10, fontWeight: FontWeight.bold)),
              ),
            ],
          ),
          const SizedBox(height: 6),
          Text(title, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w600)),
          const SizedBox(height: 8),
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: AppColors.accent.withOpacity(0.06),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Row(
              children: [
                const Icon(Icons.auto_awesome, color: AppColors.accent, size: 16),
                const SizedBox(width: 6),
                Expanded(child: Text(aiSummary, style: const TextStyle(fontSize: 12, color: AppColors.textPrimary))),
              ],
            ),
          ),
          const SizedBox(height: 8),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(slaRemaining, style: TextStyle(fontSize: 11, color: AppColors.statusError, fontWeight: FontWeight.w600)),
              TextButton(onPressed: () {}, child: const Text('Open Workspace →', style: TextStyle(fontSize: 12))),
            ],
          ),
        ],
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

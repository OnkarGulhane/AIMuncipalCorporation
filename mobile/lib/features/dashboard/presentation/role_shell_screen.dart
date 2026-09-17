import 'package:flutter/material.dart';
import '../../../core/theme/app_colors.dart';
import '../../auth/data/auth_models.dart';
import '../../auth/data/auth_service.dart';
import '../../auth/presentation/login_screen.dart';
import '../../notifications/presentation/notifications_screen.dart';
import '../../cases/presentation/case_search_screen.dart';
import 'widgets/role_dashboard_views.dart';


class RoleShellScreen extends StatefulWidget {
  final UserModel user;

  const RoleShellScreen({super.key, required this.user});

  @override
  State<RoleShellScreen> createState() => _RoleShellScreenState();
}

class _RoleShellScreenState extends State<RoleShellScreen> {
  int _selectedIndex = 0;

  Widget _getDashboardView() {
    switch (widget.user.role) {
      case UserRole.requester:
        return CitizenDashboardView(user: widget.user);
      case UserRole.operator:
        return OperatorDashboardView(user: widget.user);
      case UserRole.teamLead:
        return TeamLeadDashboardView(user: widget.user);
      case UserRole.manager:
        return ManagerDashboardView(user: widget.user);
      case UserRole.administrator:
        return AdminDashboardView(user: widget.user);
    }
  }

  Widget _getBodyForIndex(int index) {
    if (index == 0) {
      return _getDashboardView();
    }
    // Citizen Alerts tab (index 2)
    if (widget.user.role == UserRole.requester && index == 2) {
      return const NotificationsScreen();
    }

    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(Icons.construction, size: 48, color: AppColors.textMuted),
          const SizedBox(height: 12),
          Text(
            '${widget.user.role.displayName} Tab: ${_getNavigationItems()[index].label}',
            style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 4),
          const Text('Connected to Phase 3 Role Shell', style: TextStyle(color: AppColors.textMuted, fontSize: 13)),
        ],
      ),
    );
  }

  List<BottomNavigationBarItem> _getNavigationItems() {
    switch (widget.user.role) {
      case UserRole.requester:
        return const [
          BottomNavigationBarItem(icon: Icon(Icons.home_outlined), activeIcon: Icon(Icons.home), label: 'Home'),
          BottomNavigationBarItem(icon: Icon(Icons.assignment_outlined), activeIcon: Icon(Icons.assignment), label: 'My Cases'),
          BottomNavigationBarItem(icon: Icon(Icons.notifications_outlined), activeIcon: Icon(Icons.notifications), label: 'Alerts'),
          BottomNavigationBarItem(icon: Icon(Icons.person_outline), activeIcon: Icon(Icons.person), label: 'Profile'),
        ];
      case UserRole.operator:
        return const [
          BottomNavigationBarItem(icon: Icon(Icons.inbox_outlined), activeIcon: Icon(Icons.inbox), label: 'Queue'),
          BottomNavigationBarItem(icon: Icon(Icons.task_alt_outlined), activeIcon: Icon(Icons.task_alt), label: 'Tasks'),
          BottomNavigationBarItem(icon: Icon(Icons.schedule_outlined), activeIcon: Icon(Icons.schedule), label: 'SLAs'),
          BottomNavigationBarItem(icon: Icon(Icons.person_outline), activeIcon: Icon(Icons.person), label: 'Profile'),
        ];
      case UserRole.teamLead:
        return const [
          BottomNavigationBarItem(icon: Icon(Icons.dashboard_outlined), activeIcon: Icon(Icons.dashboard), label: 'Team'),
          BottomNavigationBarItem(icon: Icon(Icons.warning_amber_outlined), activeIcon: Icon(Icons.warning_amber), label: 'At-Risk'),
          BottomNavigationBarItem(icon: Icon(Icons.people_outline), activeIcon: Icon(Icons.people), label: 'Roster'),
          BottomNavigationBarItem(icon: Icon(Icons.person_outline), activeIcon: Icon(Icons.person), label: 'Profile'),
        ];
      case UserRole.manager:
        return const [
          BottomNavigationBarItem(icon: Icon(Icons.analytics_outlined), activeIcon: Icon(Icons.analytics), label: 'Overview'),
          BottomNavigationBarItem(icon: Icon(Icons.map_outlined), activeIcon: Icon(Icons.map), label: 'Wards'),
          BottomNavigationBarItem(icon: Icon(Icons.auto_awesome_outlined), activeIcon: Icon(Icons.auto_awesome), label: 'Insights'),
          BottomNavigationBarItem(icon: Icon(Icons.person_outline), activeIcon: Icon(Icons.person), label: 'Profile'),
        ];
      case UserRole.administrator:
        return const [
          BottomNavigationBarItem(icon: Icon(Icons.admin_panel_settings_outlined), activeIcon: Icon(Icons.admin_panel_settings), label: 'Admin'),
          BottomNavigationBarItem(icon: Icon(Icons.business_outlined), activeIcon: Icon(Icons.business), label: 'Depts'),
          BottomNavigationBarItem(icon: Icon(Icons.history_outlined), activeIcon: Icon(Icons.history), label: 'Audit'),
          BottomNavigationBarItem(icon: Icon(Icons.person_outline), activeIcon: Icon(Icons.person), label: 'Profile'),
        ];
    }
  }

  void _handleSignOut() {
    AuthService.logout();
    Navigator.of(context).pushAndRemoveUntil(
      MaterialPageRoute(builder: (_) => const LoginScreen()),
      (route) => false,
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Row(
          children: [
            const Icon(Icons.account_balance, color: AppColors.primary, size: 24),
            const SizedBox(width: 8),
            Text(
              '${widget.user.role.displayName} Portal',
              style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.search_rounded),
            tooltip: 'Search Complaints',
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => const CaseSearchScreen()),
              );
            },
          ),
          IconButton(
            icon: const Icon(Icons.notifications_outlined),
            tooltip: 'Notifications',
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => const NotificationsScreen()),
              );
            },
          ),
          IconButton(
            icon: const Icon(Icons.logout),
            tooltip: 'Sign Out',
            onPressed: _handleSignOut,
          ),
        ],

      ),
      body: _getBodyForIndex(_selectedIndex),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _selectedIndex,
        onTap: (idx) => setState(() => _selectedIndex = idx),
        type: BottomNavigationBarType.fixed,
        selectedItemColor: AppColors.primary,
        unselectedItemColor: AppColors.textMuted,
        items: _getNavigationItems(),
      ),
    );
  }
}


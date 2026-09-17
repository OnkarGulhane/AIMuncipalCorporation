import 'package:flutter_test/flutter_test.dart';
import 'package:ai_case_manager/features/auth/data/auth_models.dart';
import 'package:ai_case_manager/features/cases/data/case_models.dart';
import 'package:ai_case_manager/features/cases/data/ai_models.dart';
import 'package:ai_case_manager/features/cases/data/sla_models.dart';
import 'package:ai_case_manager/features/notifications/data/notification_models.dart';
import 'package:ai_case_manager/features/dashboard/data/analytics_models.dart';

void main() {
  group('Auth Models Unit Tests', () {
    test('UserModel deserialization from JSON', () {
      final json = {
        'id': 101,
        'email': 'citizen@city.gov',
        'full_name': 'Ramesh Kumar',
        'role': 'requester',
        'ward': 'Ward 04',
        'is_active': true,
        'created_at': '2026-09-17T10:00:00Z',
      };

      final user = UserModel.fromJson(json);
      expect(user.id, 101);
      expect(user.email, 'citizen@city.gov');
      expect(user.role, UserRole.requester);
      expect(user.ward, 'Ward 04');
      expect(user.isActive, true);
    });
  });

  group('Case Models Unit Tests', () {
    test('CaseModel and UnifiedTimelineResponseModel deserialization', () {
      final caseJson = {
        'id': 201,
        'case_number': 'MC-2026-0042',
        'title': 'Broken drainage slab',
        'description': 'Footpath concrete slab cracked open near bus shelter.',
        'status': 'assigned',
        'priority': 'high',
        'severity': 'major',
        'citizen_id': 101,
        'ward': 'Ward 12',
        'landmark': 'Near Bus Shelter',
        'is_escalated': false,
        'created_at': '2026-09-17T11:00:00Z',
        'updated_at': '2026-09-17T11:30:00Z',
      };

      final caseModel = CaseModel.fromJson(caseJson);
      expect(caseModel.id, 201);
      expect(caseModel.caseNumber, 'MC-2026-0042');
      expect(caseModel.status, CaseStatus.assigned);
      expect(caseModel.priority, CasePriority.high);

      final timelineJson = {
        'case_id': 201,
        'case_number': 'MC-2026-0042',
        'total_events': 1,
        'timeline': [
          {
            'id': 'timeline_1',
            'event_type': 'case_created',
            'title': 'Case Created',
            'description': 'Complaint registered by citizen.',
            'actor_id': 101,
            'actor_name': 'Ramesh Kumar',
            'actor_role': 'requester',
            'is_internal': false,
            'timestamp': '2026-09-17T11:00:00Z',
          }
        ],
      };

      final timeline = UnifiedTimelineResponseModel.fromJson(timelineJson);
      expect(timeline.caseId, 201);
      expect(timeline.totalEvents, 1);
      expect(timeline.timeline.first.title, 'Case Created');
      expect(timeline.timeline.first.isInternal, false);
    });
  });

  group('AI Models Unit Tests', () {
    test('AIAnalysisModel deserialization', () {
      final json = {
        'id': 1,
        'case_id': 201,
        'suggested_category_id': 5,
        'suggested_category_name': 'Drainage',
        'suggested_category_code': 'DRAINAGE',
        'suggested_priority': 'high',
        'suggested_severity': 'major',
        'confidence_score': 0.88,
        'summary': 'AI triage identified issue as Drainage with HIGH priority.',
        'key_details': ['Footpath safety hazard'],
        'missing_information': ['Exact slab dimensions'],
        'recommended_action': 'Dispatch masonry squad with replacement slab.',
        'created_at': '2026-09-17T11:05:00Z',
      };

      final aiModel = AIAnalysisModel.fromJson(json);
      expect(aiModel.caseId, 201);
      expect(aiModel.confidenceScore, 0.88);
      expect(aiModel.suggestedCategoryName, 'Drainage');
      expect(aiModel.keyDetails.length, 1);
    });
  });

  group('SLA & Escalation Models Unit Tests', () {
    test('CaseSLAModel and EscalationModel deserialization', () {
      final slaJson = {
        'id': 10,
        'case_id': 201,
        'response_deadline': '2026-09-17T15:00:00Z',
        'resolution_deadline': '2026-09-18T11:00:00Z',
        'status': 'pending',
        'time_remaining_str': '23h 30m',
        'is_overdue': false,
        'is_at_risk': false,
        'created_at': '2026-09-17T11:00:00Z',
      };

      final sla = CaseSLAModel.fromJson(slaJson);
      expect(sla.caseId, 201);
      expect(sla.status, 'pending');
      expect(sla.isOverdue, false);
    });
  });

  group('Notification & Analytics Models Unit Tests', () {
    test('NotificationItem and ManagerAnalyticsModel deserialization', () {
      final notifJson = {
        'id': 501,
        'event_type': 'case_created',
        'title': 'Complaint Registered: MC-2026-0042',
        'message': 'Your complaint has been queued for triage.',
        'is_read': false,
        'created_at': '2026-09-17T11:00:00Z',
      };

      final notif = NotificationItem.fromJson(notifJson);
      expect(notif.id, 501);
      expect(notif.isRead, false);

      final analyticsJson = {
        'total_cases': 120,
        'active_cases': 35,
        'resolved_cases': 85,
        'escalated_cases': 4,
        'reopened_cases': 2,
        'sla_compliance_rate': 94.5,
        'avg_resolution_hours': 14.2,
        'category_metrics': [],
        'department_metrics': [],
        'ward_metrics': [],
        'volume_trends': [],
        'operational_insights': [
          {
            'type': 'hotspot',
            'severity': 'high',
            'title': 'Ward 12 Pothole Surge',
            'description': '15 complaints filed in 48 hours.',
          }
        ],
      };

      final managerAnalytics = ManagerAnalyticsModel.fromJson(analyticsJson);
      expect(managerAnalytics.totalCases, 120);
      expect(managerAnalytics.slaComplianceRate, 94.5);
      expect(managerAnalytics.operationalInsights.first.title, 'Ward 12 Pothole Surge');
    });
  });
}

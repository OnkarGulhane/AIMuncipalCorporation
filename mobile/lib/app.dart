import 'package:flutter/material.dart';
import 'core/theme/app_theme.dart';
import 'features/health/presentation/health_check_view.dart';

class AICaseManagerApp extends StatelessWidget {
  const AICaseManagerApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'AI Case Manager',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.lightTheme,
      home: const HealthCheckView(),
    );
  }
}

import 'package:flutter/material.dart';
import '../../../../core/theme/app_colors.dart';
import '../data/case_models.dart';
import '../data/case_service.dart';
import '../data/ai_service.dart';
import '../data/ai_models.dart';
import 'case_detail_screen.dart';

class CreateCaseScreen extends StatefulWidget {
  final String? initialCategory;

  const CreateCaseScreen({super.key, this.initialCategory});

  @override
  State<CreateCaseScreen> createState() => _CreateCaseScreenState();
}

class _CreateCaseScreenState extends State<CreateCaseScreen> {
  final _formKey = GlobalKey<FormState>();
  final _titleController = TextEditingController();
  final _descriptionController = TextEditingController();
  final _wardController = TextEditingController(text: 'Ward 12 - Shivaji Nagar');
  final _landmarkController = TextEditingController();
  final CaseService _caseService = CaseService();
  final AIService _aiService = AIService();

  int? _selectedCategoryId;
  String _selectedPriority = 'medium';
  bool _isLoading = false;
  bool _isAiScanning = false;
  AIVisionAnalyzeModel? _visionResult;
  String? _errorMessage;

  final List<Map<String, dynamic>> _categories = [
    {'id': 1, 'name': 'Potholes & Road Damage', 'dept': 'Roads & Infrastructure'},
    {'id': 2, 'name': 'Garbage Dump & Waste Overflow', 'dept': 'Solid Waste Management'},
    {'id': 3, 'name': 'Water Pipeline Leakage / Contamination', 'dept': 'Water Supply'},
    {'id': 4, 'name': 'Streetlight Not Working / Dark Spot', 'dept': 'Electrical & Lighting'},
    {'id': 5, 'name': 'Blocked Drainage / Sewer Overflow', 'dept': 'Drainage & Stormwater'},
    {'id': 6, 'name': 'Fallen Tree / Road Obstruction', 'dept': 'Roads & Infrastructure'},
  ];

  Future<void> _triggerAiVisionScan({String sampleType = 'pothole'}) async {
    setState(() {
      _isAiScanning = true;
      _errorMessage = null;
    });

    final filename = sampleType == 'garbage'
        ? 'garbage_overflow_dump_container.png'
        : (sampleType == 'water' ? 'water_pipe_leak_rupture.jpg' : 'severe_road_asphalt_pothole.jpg');
    final landmark = sampleType == 'garbage'
        ? 'Near Shivaji Park Sector 4'
        : (sampleType == 'water' ? 'Near Water Reservoir Tank' : 'Opposite City Bank ATM, MG Road');

    final res = await _aiService.analyzeVision(
      filename: filename,
      landmarkHint: landmark,
      voiceNote: 'Automated camera scan for municipal civic damage triage',
    );

    if (!mounted) return;

    setState(() {
      _isAiScanning = false;
    });

    if (res.isSuccess && res.data != null) {
      final v = res.data!;
      setState(() {
        _visionResult = v;
        _titleController.text = v.suggestedTitle;
        _descriptionController.text = v.suggestedDescription;
        if (v.categoryId != null) {
          _selectedCategoryId = v.categoryId;
        }
        _selectedPriority = v.suggestedPriority.toLowerCase();
        if (v.landmarkInferred != null && _landmarkController.text.isEmpty) {
          _landmarkController.text = v.landmarkInferred!;
        }
      });

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('✨ AI Vision: Auto-filled complaint (${v.categoryName})'),
          backgroundColor: AppColors.statusSuccess,
          duration: const Duration(seconds: 3),
        ),
      );
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(res.errorMessage ?? 'Failed to complete vision scan'),
          backgroundColor: AppColors.statusError,
        ),
      );
    }
  }

  Future<void> _submitComplaint() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    final res = await _caseService.createCase(
      title: _titleController.text.trim(),
      description: _descriptionController.text.trim(),
      categoryId: _selectedCategoryId,
      ward: _wardController.text.trim(),
      landmark: _landmarkController.text.trim().isNotEmpty ? _landmarkController.text.trim() : null,
      priority: _selectedPriority,
    );

    if (!mounted) return;

    setState(() {
      _isLoading = false;
    });

    if (res.isSuccess && res.data != null) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Complaint ${res.data!.caseNumber} created successfully!'),
          backgroundColor: AppColors.statusSuccess,
        ),
      );
      Navigator.of(context).pushReplacement(
        MaterialPageRoute(builder: (_) => CaseDetailScreen(caseId: res.data!.id)),
      );
    } else {
      setState(() {
        _errorMessage = res.errorMessage ?? 'Failed to submit complaint.';
      });
    }
  }

  @override
  void dispose() {
    _titleController.dispose();
    _descriptionController.dispose();
    _wardController.dispose();
    _landmarkController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Report New Complaint'),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(20.0),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                if (_errorMessage != null) ...[
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: AppColors.statusError.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(10),
                      border: Border.all(color: AppColors.statusError.withOpacity(0.3)),
                    ),
                    child: Text(_errorMessage!, style: const TextStyle(color: AppColors.statusError)),
                  ),
                  const SizedBox(height: 16),
                ],

                // =============================================================
                // AI CAMERA / PHOTO ZERO-TYPING BANNER
                // =============================================================
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: AppColors.primary.withOpacity(0.06),
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: AppColors.primary.withOpacity(0.3), width: 1.5),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Container(
                            padding: const EdgeInsets.all(8),
                            decoration: BoxDecoration(
                              color: AppColors.primary.withOpacity(0.12),
                              borderRadius: BorderRadius.circular(10),
                            ),
                            child: const Icon(Icons.photo_camera_back, color: AppColors.primary, size: 22),
                          ),
                          const SizedBox(width: 12),
                          const Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  '📸 AI Camera Auto-Fill',
                                  style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                                ),
                                Text(
                                  'Zero-typing: Snap photo & AI detects damage category, priority & details',
                                  style: TextStyle(fontSize: 11, color: Colors.black54),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 12),
                      if (_isAiScanning) ...[
                        const Center(
                          child: Padding(
                            padding: EdgeInsets.symmetric(vertical: 8.0),
                            child: Row(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                SizedBox(
                                  width: 16,
                                  height: 16,
                                  child: CircularProgressIndicator(strokeWidth: 2),
                                ),
                                SizedBox(width: 10),
                                Text(
                                  '⚡ Scanning photo & detecting civic damage...',
                                  style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: AppColors.primary),
                                ),
                              ],
                            ),
                          ),
                        ),
                      ] else ...[
                        Wrap(
                          spacing: 8,
                          runSpacing: 8,
                          children: [
                            ElevatedButton.icon(
                              onPressed: () => _triggerAiVisionScan(sampleType: 'pothole'),
                              icon: const Icon(Icons.add_a_photo, size: 16),
                              label: const Text('📸 Snap / Scan Photo', style: TextStyle(fontSize: 12)),
                              style: ElevatedButton.styleFrom(
                                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                              ),
                            ),
                            OutlinedButton.icon(
                              onPressed: () => _triggerAiVisionScan(sampleType: 'garbage'),
                              icon: const Icon(Icons.delete_outline, size: 16),
                              label: const Text('Demo Waste', style: TextStyle(fontSize: 12)),
                              style: OutlinedButton.styleFrom(
                                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                              ),
                            ),
                            OutlinedButton.icon(
                              onPressed: () => _triggerAiVisionScan(sampleType: 'water'),
                              icon: const Icon(Icons.water_drop_outlined, size: 16),
                              label: const Text('Demo Pipe Leak', style: TextStyle(fontSize: 12)),
                              style: OutlinedButton.styleFrom(
                                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                              ),
                            ),
                          ],
                        ),
                      ],
                      if (_visionResult != null) ...[
                        const SizedBox(height: 12),
                        Container(
                          padding: const EdgeInsets.all(10),
                          decoration: BoxDecoration(
                            color: Colors.white,
                            borderRadius: BorderRadius.circular(10),
                            border: Border.all(color: AppColors.statusSuccess.withOpacity(0.4)),
                          ),
                          child: Row(
                            children: [
                              const Icon(Icons.check_circle, color: AppColors.statusSuccess, size: 18),
                              const SizedBox(width: 8),
                              Expanded(
                                child: Text(
                                  '✨ AI Vision: ${_visionResult!.categoryName} (${(_visionResult!.confidenceScore * 100).toInt()}% confidence) — Form Auto-Filled!',
                                  style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: AppColors.statusSuccess),
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ],
                  ),
                ),
                const SizedBox(height: 20),

                // Category Selection
                const Text('Complaint Category', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                const SizedBox(height: 8),
                DropdownButtonFormField<int>(
                  value: _selectedCategoryId,
                  decoration: const InputDecoration(
                    prefixIcon: Icon(Icons.category_outlined),
                  ),
                  items: _categories.map((c) {
                    return DropdownMenuItem<int>(
                      value: c['id'] as int,
                      child: Text(c['name'] as String, style: const TextStyle(fontSize: 14)),
                    );
                  }).toList(),
                  onChanged: (val) => setState(() => _selectedCategoryId = val),
                ),
                const SizedBox(height: 16),

                // Complaint Title
                const Text('Short Summary / Title', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                const SizedBox(height: 8),
                TextFormField(
                  controller: _titleController,
                  decoration: const InputDecoration(
                    hintText: 'e.g. Broken water pipe near main temple',
                    prefixIcon: Icon(Icons.title),
                  ),
                  validator: (val) => val == null || val.trim().length < 3 ? 'Enter a brief title' : null,
                ),
                const SizedBox(height: 16),

                // Detailed Description
                const Text('Detailed Description', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                const SizedBox(height: 8),
                TextFormField(
                  controller: _descriptionController,
                  maxLines: 4,
                  decoration: const InputDecoration(
                    hintText: 'Describe the problem clearly (e.g., location, severity, duration)...',
                  ),
                  validator: (val) => val == null || val.trim().length < 5 ? 'Please provide detailed description' : null,
                ),
                const SizedBox(height: 16),

                // Ward / Area
                const Text('Ward / Area', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                const SizedBox(height: 8),
                TextFormField(
                  controller: _wardController,
                  decoration: const InputDecoration(
                    prefixIcon: Icon(Icons.location_city_outlined),
                  ),
                  validator: (val) => val == null || val.trim().isEmpty ? 'Enter ward or area' : null,
                ),
                const SizedBox(height: 16),

                // Landmark
                const Text('Nearest Landmark (Optional)', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                const SizedBox(height: 8),
                TextFormField(
                  controller: _landmarkController,
                  decoration: const InputDecoration(
                    hintText: 'e.g. Near Shanti Medical / Opposite Bank',
                    prefixIcon: Icon(Icons.place_outlined),
                  ),
                ),
                const SizedBox(height: 16),

                // Priority
                const Text('Urgency Level', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                const SizedBox(height: 8),
                SegmentedButton<String>(
                  segments: const [
                    ButtonSegment(value: 'low', label: Text('Low')),
                    ButtonSegment(value: 'medium', label: Text('Medium')),
                    ButtonSegment(value: 'high', label: Text('High')),
                    ButtonSegment(value: 'critical', label: Text('Critical')),
                  ],
                  selected: {_selectedPriority},
                  onSelectionChanged: (val) => setState(() => _selectedPriority = val.first),
                ),
                const SizedBox(height: 28),

                // Submit Button
                ElevatedButton(
                  onPressed: _isLoading ? null : _submitComplaint,
                  child: _isLoading
                      ? const SizedBox(
                          height: 20,
                          width: 20,
                          child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                        )
                      : const Text('Submit Civic Complaint'),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

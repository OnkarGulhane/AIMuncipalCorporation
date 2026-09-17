import 'package:flutter/material.dart';
import '../../../../core/theme/app_colors.dart';
import '../data/case_models.dart';
import '../data/case_service.dart';
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

  int? _selectedCategoryId;
  String _selectedPriority = 'medium';
  bool _isLoading = false;
  String? _errorMessage;

  final List<Map<String, dynamic>> _categories = [
    {'id': 1, 'name': 'Potholes & Road Damage', 'dept': 'Roads & Infrastructure'},
    {'id': 2, 'name': 'Garbage Dump & Waste Overflow', 'dept': 'Solid Waste Management'},
    {'id': 3, 'name': 'Water Pipeline Leakage / Contamination', 'dept': 'Water Supply'},
    {'id': 4, 'name': 'Streetlight Not Working / Dark Spot', 'dept': 'Electrical & Lighting'},
    {'id': 5, 'name': 'Blocked Drainage / Sewer Overflow', 'dept': 'Drainage & Stormwater'},
    {'id': 6, 'name': 'Fallen Tree / Road Obstruction', 'dept': 'Roads & Infrastructure'},
  ];

  @override
  void initState() {
    super.initState();
    if (widget.initialCategory != null) {
      final match = _categories.firstWhere(
        (c) => c['name'].toString().toLowerCase().contains(widget.initialCategory!.toLowerCase()),
        orElse: () => _categories.first,
      );
      _selectedCategoryId = match['id'] as int;
    } else {
      _selectedCategoryId = _categories.first['id'] as int;
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

import 'dart:async';
import 'package:flutter/material.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/widgets/app_empty_state.dart';
import '../../../core/widgets/app_error_state.dart';
import '../data/case_models.dart';
import '../data/case_service.dart';
import 'case_detail_screen.dart';

class CaseSearchScreen extends StatefulWidget {
  const CaseSearchScreen({super.key});

  @override
  State<CaseSearchScreen> createState() => _CaseSearchScreenState();
}

class _CaseSearchScreenState extends State<CaseSearchScreen> {
  final CaseService _caseService = CaseService();
  final TextEditingController _searchController = TextEditingController();
  Timer? _debounceTimer;

  bool _isLoading = false;
  String? _errorMessage;
  List<CaseModel> _results = [];
  int _totalCount = 0;

  // Active filters
  String? _selectedStatus;
  String? _selectedPriority;
  String? _selectedWard;
  bool _isOverdueOnly = false;
  bool _isAtRiskOnly = false;
  String _sortBy = 'created_at';
  String _sortOrder = 'desc';

  final List<String> _statusOptions = [
    'reported',
    'understood',
    'assigned',
    'investigated',
    'action_taken',
    'resolution_proposed',
    'confirmed',
    'closed',
    'escalated',
  ];

  final List<String> _priorityOptions = [
    'low',
    'medium',
    'high',
    'critical',
  ];

  final List<String> _wardOptions = [
    'Ward 01 - South Central',
    'Ward 04 - East Corridor',
    'Ward 08 - Old City',
    'Ward 12 - North Industrial',
    'Ward 15 - West Suburbs',
  ];

  @override
  void initState() {
    super.initState();
    _performSearch();
  }

  @override
  void dispose() {
    _debounceTimer?.cancel();
    _searchController.dispose();
    super.dispose();
  }

  void _onSearchChanged(String query) {
    _debounceTimer?.cancel();
    _debounceTimer = Timer(const Duration(milliseconds: 400), () {
      _performSearch();
    });
  }

  Future<void> _performSearch() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    final res = await _caseService.listCases(
      search: _searchController.text.trim().isNotEmpty ? _searchController.text.trim() : null,
      status: _selectedStatus,
      priority: _selectedPriority,
      ward: _selectedWard,
      isOverdue: _isOverdueOnly ? true : null,
      isAtRisk: _isAtRiskOnly ? true : null,
      sortBy: _sortBy,
      sortOrder: _sortOrder,
    );

    if (mounted) {
      setState(() {
        _isLoading = false;
        if (res.isSuccess && res.data != null) {
          _results = res.data!.items;
          _totalCount = res.data!.total;
        } else {
          _errorMessage = res.errorMessage ?? 'Failed to execute complaint search.';
        }
      });
    }
  }

  void _clearAllFilters() {
    setState(() {
      _searchController.clear();
      _selectedStatus = null;
      _selectedPriority = null;
      _selectedWard = null;
      _isOverdueOnly = false;
      _isAtRiskOnly = false;
      _sortBy = 'created_at';
      _sortOrder = 'desc';
    });
    _performSearch();
  }

  void _openFilterBottomSheet() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.white,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) {
        return StatefulBuilder(
          builder: (context, setModalState) {
            return Padding(
              padding: EdgeInsets.only(
                left: 20,
                right: 20,
                top: 20,
                bottom: MediaQuery.of(context).viewInsets.bottom + 24,
              ),
              child: SingleChildScrollView(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Text(
                          'Filter Complaints',
                          style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                        ),
                        TextButton(
                          onPressed: () {
                            setModalState(() {
                              _selectedStatus = null;
                              _selectedPriority = null;
                              _selectedWard = null;
                              _isOverdueOnly = false;
                              _isAtRiskOnly = false;
                            });
                          },
                          child: const Text('Reset'),
                        ),
                      ],
                    ),
                    const Divider(),
                    const SizedBox(height: 8),

                    // Status Chips
                    const Text('Case Status', style: TextStyle(fontWeight: FontWeight.w600, fontSize: 13)),
                    const SizedBox(height: 6),
                    Wrap(
                      spacing: 8,
                      runSpacing: 4,
                      children: _statusOptions.map((st) {
                        final isSelected = _selectedStatus == st;
                        return ChoiceChip(
                          label: Text(st.replaceAll('_', ' ').toUpperCase(), style: const TextStyle(fontSize: 11)),
                          selected: isSelected,
                          selectedColor: AppColors.primary.withOpacity(0.15),
                          onSelected: (val) {
                            setModalState(() {
                              _selectedStatus = val ? st : null;
                            });
                          },
                        );
                      }).toList(),
                    ),
                    const SizedBox(height: 16),

                    // Priority Chips
                    const Text('Priority Level', style: TextStyle(fontWeight: FontWeight.w600, fontSize: 13)),
                    const SizedBox(height: 6),
                    Wrap(
                      spacing: 8,
                      runSpacing: 4,
                      children: _priorityOptions.map((pr) {
                        final isSelected = _selectedPriority == pr;
                        return ChoiceChip(
                          label: Text(pr.toUpperCase(), style: const TextStyle(fontSize: 11)),
                          selected: isSelected,
                          selectedColor: AppColors.statusWarning.withOpacity(0.15),
                          onSelected: (val) {
                            setModalState(() {
                              _selectedPriority = val ? pr : null;
                            });
                          },
                        );
                      }).toList(),
                    ),
                    const SizedBox(height: 16),

                    // Ward Selector
                    const Text('Municipal Ward', style: TextStyle(fontWeight: FontWeight.w600, fontSize: 13)),
                    const SizedBox(height: 6),
                    DropdownButtonFormField<String>(
                      value: _selectedWard,
                      hint: const Text('All Municipal Wards'),
                      isExpanded: true,
                      decoration: InputDecoration(
                        border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                        contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                      ),
                      items: [
                        const DropdownMenuItem<String>(value: null, child: Text('All Municipal Wards')),
                        ..._wardOptions.map((w) => DropdownMenuItem(value: w, child: Text(w))),
                      ],
                      onChanged: (val) {
                        setModalState(() {
                          _selectedWard = val;
                        });
                      },
                    ),
                    const SizedBox(height: 16),

                    // SLA Flags
                    CheckboxListTile(
                      title: const Text('Overdue Complaints Only', style: TextStyle(fontSize: 13)),
                      value: _isOverdueOnly,
                      dense: true,
                      contentPadding: EdgeInsets.zero,
                      onChanged: (val) {
                        setModalState(() {
                          _isOverdueOnly = val ?? false;
                        });
                      },
                    ),
                    CheckboxListTile(
                      title: const Text('At-Risk / Approaching SLA Breach', style: TextStyle(fontSize: 13)),
                      value: _isAtRiskOnly,
                      dense: true,
                      contentPadding: EdgeInsets.zero,
                      onChanged: (val) {
                        setModalState(() {
                          _isAtRiskOnly = val ?? false;
                        });
                      },
                    ),
                    const SizedBox(height: 16),

                    SizedBox(
                      width: double.infinity,
                      child: FilledButton(
                        onPressed: () {
                          Navigator.pop(context);
                          _performSearch();
                        },
                        style: FilledButton.styleFrom(
                          backgroundColor: AppColors.primary,
                          padding: const EdgeInsets.symmetric(vertical: 14),
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                        ),
                        child: const Text('Apply Filters'),
                      ),
                    ),
                  ],
                ),
              ),
            );
          },
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    final hasActiveFilters = _selectedStatus != null ||
        _selectedPriority != null ||
        _selectedWard != null ||
        _isOverdueOnly ||
        _isAtRiskOnly;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Search & Filter Complaints'),
        backgroundColor: AppColors.primary,
        foregroundColor: Colors.white,
        actions: [
          IconButton(
            icon: Badge(
              isLabelVisible: hasActiveFilters,
              child: const Icon(Icons.filter_list_rounded),
            ),
            tooltip: 'Filter Options',
            onPressed: _openFilterBottomSheet,
          ),
        ],
      ),
      body: Column(
        children: [
          // Search Bar
          Container(
            padding: const EdgeInsets.all(12),
            color: Colors.white,
            child: TextField(
              controller: _searchController,
              onChanged: _onSearchChanged,
              decoration: InputDecoration(
                hintText: 'Search by case #, keyword, ward, landmark...',
                prefixIcon: const Icon(Icons.search, color: AppColors.primary),
                suffixIcon: _searchController.text.isNotEmpty
                    ? IconButton(
                        icon: const Icon(Icons.clear, size: 20),
                        onPressed: () {
                          _searchController.clear();
                          _performSearch();
                        },
                      )
                    : null,
                filled: true,
                fillColor: const Color(0xFFF8FAFC),
                contentPadding: const EdgeInsets.symmetric(vertical: 12),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                  borderSide: const BorderSide(color: AppColors.border),
                ),
                enabledBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                  borderSide: const BorderSide(color: AppColors.border),
                ),
              ),
            ),
          ),

          // Active filter tags row
          if (hasActiveFilters)
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
              color: const Color(0xFFF1F5F9),
              child: Row(
                children: [
                  const Icon(Icons.filter_alt_outlined, size: 16, color: AppColors.textSecondary),
                  const SizedBox(width: 6),
                  Expanded(
                    child: SingleChildScrollView(
                      scrollDirection: Axis.horizontal,
                      child: Row(
                        children: [
                          if (_selectedStatus != null)
                            Padding(
                              padding: const EdgeInsets.only(right: 6),
                              child: Chip(
                                label: Text('Status: ${_selectedStatus!.replaceAll('_', ' ')}'),
                                onDeleted: () {
                                  setState(() => _selectedStatus = null);
                                  _performSearch();
                                },
                              ),
                            ),
                          if (_selectedPriority != null)
                            Padding(
                              padding: const EdgeInsets.only(right: 6),
                              child: Chip(
                                label: Text('Priority: ${_selectedPriority!.toUpperCase()}'),
                                onDeleted: () {
                                  setState(() => _selectedPriority = null);
                                  _performSearch();
                                },
                              ),
                            ),
                          if (_selectedWard != null)
                            Padding(
                              padding: const EdgeInsets.only(right: 6),
                              child: Chip(
                                label: Text(_selectedWard!),
                                onDeleted: () {
                                  setState(() => _selectedWard = null);
                                  _performSearch();
                                },
                              ),
                            ),
                          if (_isOverdueOnly)
                            Padding(
                              padding: const EdgeInsets.only(right: 6),
                              child: Chip(
                                label: const Text('Overdue'),
                                onDeleted: () {
                                  setState(() => _isOverdueOnly = false);
                                  _performSearch();
                                },
                              ),
                            ),
                        ],
                      ),
                    ),
                  ),
                  TextButton(
                    onPressed: _clearAllFilters,
                    style: TextButton.styleFrom(visualDensity: VisualDensity.compact),
                    child: const Text('Clear All', style: TextStyle(fontSize: 12)),
                  ),
                ],
              ),
            ),

          // Results counter
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  'Found $_totalCount ${_totalCount == 1 ? 'complaint' : 'complaints'}',
                  style: const TextStyle(fontWeight: FontWeight.w600, color: AppColors.textSecondary, fontSize: 13),
                ),
                DropdownButton<String>(
                  value: _sortBy,
                  underline: const SizedBox(),
                  style: const TextStyle(fontSize: 12, color: AppColors.primary, fontWeight: FontWeight.bold),
                  items: const [
                    DropdownMenuItem(value: 'created_at', child: Text('Sort: Date Filed')),
                    DropdownMenuItem(value: 'priority', child: Text('Sort: Priority')),
                    DropdownMenuItem(value: 'status', child: Text('Sort: Status')),
                  ],
                  onChanged: (val) {
                    if (val != null) {
                      setState(() => _sortBy = val);
                      _performSearch();
                    }
                  },
                ),
              ],
            ),
          ),

          // Results List / States
          Expanded(
            child: _isLoading
                ? const Center(child: CircularProgressIndicator())
                : _errorMessage != null
                    ? AppErrorState(message: _errorMessage!, onRetry: _performSearch)
                    : _results.isEmpty
                        ? AppEmptyState.noSearchResults(
                            onClearFilters: hasActiveFilters ? _clearAllFilters : null,
                            onBroadenSearch: () {
                              _searchController.clear();
                              _performSearch();
                            },
                          )
                        : ListView.separated(
                            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                            itemCount: _results.length,
                            separatorBuilder: (_, __) => const SizedBox(height: 10),
                            itemBuilder: (context, index) {
                              final c = _results[index];
                              return Card(
                                elevation: 0,
                                shape: RoundedRectangleBorder(
                                  borderRadius: BorderRadius.circular(12),
                                  side: const BorderSide(color: AppColors.border),
                                ),
                                child: InkWell(
                                  borderRadius: BorderRadius.circular(12),
                                  onTap: () {
                                    Navigator.push(
                                      context,
                                      MaterialPageRoute(
                                        builder: (_) => CaseDetailScreen(caseId: c.id),
                                      ),
                                    );
                                  },
                                  child: Padding(
                                    padding: const EdgeInsets.all(14.0),
                                    child: Column(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      children: [
                                        Row(
                                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                          children: [
                                            Text(
                                              c.caseNumber,
                                              style: const TextStyle(
                                                fontWeight: FontWeight.bold,
                                                fontSize: 12,
                                                color: AppColors.primary,
                                              ),
                                            ),
                                            Container(
                                              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                                              decoration: BoxDecoration(
                                                color: c.status.color.withOpacity(0.12),
                                                borderRadius: BorderRadius.circular(6),
                                              ),
                                              child: Text(
                                                c.status.displayName,
                                                style: TextStyle(
                                                  fontSize: 11,
                                                  fontWeight: FontWeight.bold,
                                                  color: c.status.color,
                                                ),
                                              ),
                                            ),
                                          ],
                                        ),
                                        const SizedBox(height: 6),
                                        Text(
                                          c.title,
                                          style: const TextStyle(
                                            fontWeight: FontWeight.bold,
                                            fontSize: 15,
                                            color: AppColors.textPrimary,
                                          ),
                                        ),
                                        const SizedBox(height: 4),
                                        Text(
                                          c.description,
                                          maxLines: 2,
                                          overflow: TextOverflow.ellipsis,
                                          style: const TextStyle(fontSize: 13, color: AppColors.textSecondary),
                                        ),
                                        const SizedBox(height: 10),
                                        Row(
                                          children: [
                                            if (c.ward != null) ...[
                                              Icon(Icons.location_on_outlined, size: 14, color: AppColors.textMuted),
                                              const SizedBox(width: 3),
                                              Text(
                                                c.ward!,
                                                style: const TextStyle(fontSize: 11, color: AppColors.textSecondary),
                                              ),
                                              const Spacer(),
                                            ],
                                            Container(
                                              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                              decoration: BoxDecoration(
                                                color: c.priority.color.withOpacity(0.1),
                                                borderRadius: BorderRadius.circular(4),
                                              ),
                                              child: Text(
                                                c.priority.displayName.toUpperCase(),
                                                style: TextStyle(
                                                  fontSize: 10,
                                                  fontWeight: FontWeight.bold,
                                                  color: c.priority.color,
                                                ),
                                              ),
                                            ),
                                          ],
                                        ),
                                      ],
                                    ),
                                  ),
                                ),
                              );
                            },
                          ),
          ),
        ],
      ),
    );
  }
}

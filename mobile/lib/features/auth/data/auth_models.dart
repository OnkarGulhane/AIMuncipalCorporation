enum UserRole {
  requester,
  operator,
  teamLead,
  manager,
  administrator;

  static UserRole fromString(String role) {
    switch (role.toLowerCase()) {
      case 'operator':
        return UserRole.operator;
      case 'team_lead':
        return UserRole.teamLead;
      case 'manager':
        return UserRole.manager;
      case 'administrator':
        return UserRole.administrator;
      case 'requester':
      default:
        return UserRole.requester;
    }
  }

  String get displayName {
    switch (this) {
      case UserRole.requester:
        return 'Citizen / Requester';
      case UserRole.operator:
        return 'Case Operator';
      case UserRole.teamLead:
        return 'Team Lead';
      case UserRole.manager:
        return 'Municipal Manager';
      case UserRole.administrator:
        return 'Administrator';
    }
  }

  String get value {
    switch (this) {
      case UserRole.requester:
        return 'requester';
      case UserRole.operator:
        return 'operator';
      case UserRole.teamLead:
        return 'team_lead';
      case UserRole.manager:
        return 'manager';
      case UserRole.administrator:
        return 'administrator';
    }
  }
}

class UserModel {
  final int id;
  final String email;
  final String fullName;
  final String? phoneNumber;
  final UserRole role;
  final String? department;
  final String? ward;
  final bool isActive;
  final bool isVerified;
  final DateTime createdAt;

  UserModel({
    required this.id,
    required this.email,
    required this.fullName,
    this.phoneNumber,
    required this.role,
    this.department,
    this.ward,
    required this.isActive,
    required this.isVerified,
    required this.createdAt,
  });

  factory UserModel.fromJson(Map<String, dynamic> json) {
    return UserModel(
      id: json['id'] as int,
      email: json['email'] as String,
      fullName: json['full_name'] as String,
      phoneNumber: json['phone_number'] as String?,
      role: UserRole.fromString(json['role'] as String? ?? 'requester'),
      department: json['department'] as String?,
      ward: json['ward'] as String?,
      isActive: json['is_active'] as bool? ?? true,
      isVerified: json['is_verified'] as bool? ?? true,
      createdAt: json['created_at'] != null
          ? DateTime.tryParse(json['created_at'].toString()) ?? DateTime.now()
          : DateTime.now(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'email': email,
      'full_name': fullName,
      'phone_number': phoneNumber,
      'role': role.value,
      'department': department,
      'ward': ward,
      'is_active': isActive,
      'is_verified': isVerified,
      'created_at': createdAt.toIso8601String(),
    };
  }
}

class AuthResponseModel {
  final String accessToken;
  final String tokenType;
  final UserModel user;

  AuthResponseModel({
    required this.accessToken,
    required this.tokenType,
    required this.user,
  });

  factory AuthResponseModel.fromJson(Map<String, dynamic> json) {
    return AuthResponseModel(
      accessToken: json['access_token'] as String,
      tokenType: json['token_type'] as String? ?? 'bearer',
      user: UserModel.fromJson(json['user'] as Map<String, dynamic>),
    );
  }
}

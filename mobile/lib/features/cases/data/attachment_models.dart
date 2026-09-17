import 'package:flutter/material.dart';

class CaseAttachmentModel {
  final int id;
  final int caseId;
  final int uploadedById;
  final String? uploadedByName;
  final String? uploadedByRole;
  final String originalFilename;
  final int fileSize;
  final String contentType;
  final String? description;
  final bool isPublicToCitizen;
  final DateTime createdAt;

  CaseAttachmentModel({
    required this.id,
    required this.caseId,
    required this.uploadedById,
    this.uploadedByName,
    this.uploadedByRole,
    required this.originalFilename,
    required this.fileSize,
    required this.contentType,
    this.description,
    required this.isPublicToCitizen,
    required this.createdAt,
  });

  factory CaseAttachmentModel.fromJson(Map<String, dynamic> json) {
    return CaseAttachmentModel(
      id: json['id'] ?? 0,
      caseId: json['case_id'] ?? 0,
      uploadedById: json['uploaded_by_id'] ?? 0,
      uploadedByName: json['uploaded_by_name'],
      uploadedByRole: json['uploaded_by_role'],
      originalFilename: json['original_filename'] ?? 'attachment',
      fileSize: json['file_size'] ?? 0,
      contentType: json['content_type'] ?? 'application/octet-stream',
      description: json['description'],
      isPublicToCitizen: json['is_public_to_citizen'] ?? true,
      createdAt: json['created_at'] != null
          ? DateTime.tryParse(json['created_at']) ?? DateTime.now()
          : DateTime.now(),
    );
  }

  String get formattedSize {
    if (fileSize < 1024) return '$fileSize B';
    if (fileSize < 1024 * 1024) return '${(fileSize / 1024).toStringAsFixed(1)} KB';
    return '${(fileSize / (1024 * 1024)).toStringAsFixed(2)} MB';
  }

  bool get isImage =>
      contentType.startsWith('image/') ||
      originalFilename.toLowerCase().endsWith('.jpg') ||
      originalFilename.toLowerCase().endsWith('.jpeg') ||
      originalFilename.toLowerCase().endsWith('.png') ||
      originalFilename.toLowerCase().endsWith('.webp');

  bool get isPdf =>
      contentType == 'application/pdf' ||
      originalFilename.toLowerCase().endsWith('.pdf');

  IconData get fileIcon {
    if (isImage) return Icons.image_outlined;
    if (isPdf) return Icons.picture_as_pdf_outlined;
    if (contentType.startsWith('video/')) return Icons.video_file_outlined;
    return Icons.insert_drive_file_outlined;
  }
}

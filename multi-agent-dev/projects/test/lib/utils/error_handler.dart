import 'dart:async';
import 'dart:io';
import 'package:flutter/material.dart';

class ErrorHandler {
  // Singleton instance
  static final ErrorHandler _instance = ErrorHandler._internal();
  factory ErrorHandler() => _instance;
  ErrorHandler._internal();

  // Error handling methods
  void handleError(BuildContext context, dynamic error, {String? customMessage}) {
    String message = customMessage ?? 'An error occurred';
    
    if (error is SocketException) {
      message = 'Network error: Unable to connect to the server';
    } else if (error is TimeoutException) {
      message = 'Connection timeout: Please try again later';
    } else if (error is FormatException) {
      message = 'Data format error: Please contact support';
    }
    
    _showErrorSnackBar(context, message);
    
    // Log the error (you could integrate with a logging service here)
    debugPrint('ERROR: ${error.toString()}');
  }
  
  void _showErrorSnackBar(BuildContext context, String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: Colors.red[700],
        duration: const Duration(seconds: 5),
        action: SnackBarAction(
          label: 'Dismiss',
          textColor: Colors.white,
          onPressed: () {
            ScaffoldMessenger.of(context).hideCurrentSnackBar();
          },
        ),
      ),
    );
  }
  
  // Widget for error states in the UI
  Widget errorWidget(String message, {VoidCallback? onRetry}) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(
            Icons.error_outline,
            color: Colors.red,
            size: 60,
          ),
          const SizedBox(height: 16),
          Text(
            message,
            style: const TextStyle(fontSize: 16),
            textAlign: TextAlign.center,
          ),
          if (onRetry != null) ...[
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: onRetry,
              child: const Text('Retry'),
            ),
          ],
        ],
      ),
    );
  }
}

// Extension for try-catch simplification
extension FutureExtensions<T> on Future<T> {
  Future<T> handleError(BuildContext context, {String? customMessage}) async {
    try {
      return await this;
    } catch (e) {
      ErrorHandler().handleError(context, e, customMessage: customMessage);
      rethrow;
    }
  }
}

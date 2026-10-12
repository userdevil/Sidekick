import 'dart:async';
import 'package:flutter/foundation.dart';
import 'config_service.dart';

class ReminderService extends ChangeNotifier {
  ReminderService({required this.configService}) {
    configService.addListener(_onConfigChanged);
    _scheduleNext();
  }

  final ConfigService configService;
  Timer? _timer;
  bool _isPopupActive = false;
  VoidCallback? onTriggerPopup;

  bool get isPopupActive => _isPopupActive;

  void _onConfigChanged() {
    _scheduleNext();
  }

  void _scheduleNext() {
    _timer?.cancel();
    final intervalMs = configService.config.intervalMinutes * 60 * 1000;
    _timer = Timer(Duration(milliseconds: intervalMs), () {
      triggerPopup();
    });
  }

  void triggerPopup({bool isTest = false}) {
    _isPopupActive = true;
    notifyListeners();
    onTriggerPopup?.call();
  }

  void onPopupDismissed() {
    _isPopupActive = false;
    notifyListeners();
    _scheduleNext();
  }

  @override
  void dispose() {
    configService.removeListener(_onConfigChanged);
    _timer?.cancel();
    super.dispose();
  }
}

import 'dart:convert';
import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/app_config.dart';

class ConfigService extends ChangeNotifier {
  ConfigService() {
    _load();
  }

  static const String _prefKey = 'sidekick_config';
  AppConfig _config = const AppConfig();

  AppConfig get config => _config;

  File get _legacyConfigFile {
    final home = Platform.environment['USERPROFILE'] ??
        Platform.environment['HOME'] ??
        '';
    return File('$home/.sidekick/config.json');
  }

  Future<void> _load() async {
    try {
      // 1. Try legacy ~/.sidekick/config.json if available
      final legacyFile = _legacyConfigFile;
      if (await legacyFile.exists()) {
        final content = await legacyFile.readAsString();
        final map = jsonDecode(content) as Map<String, dynamic>;
        _config = AppConfig.fromJson(map);
        notifyListeners();
        return;
      }
    } catch (e) {
      debugPrint('[ConfigService] Legacy config load error: $e');
    }

    try {
      // 2. Try SharedPreferences
      final prefs = await SharedPreferences.getInstance();
      final raw = prefs.getString(_prefKey);
      if (raw != null) {
        final map = jsonDecode(raw) as Map<String, dynamic>;
        _config = AppConfig.fromJson(map);
        notifyListeners();
      }
    } catch (e) {
      debugPrint('[ConfigService] SharedPreferences load error: $e');
    }
  }

  Future<void> updateConfig(AppConfig newConfig) async {
    _config = newConfig;
    notifyListeners();

    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString(_prefKey, jsonEncode(_config.toJson()));
    } catch (e) {
      debugPrint('[ConfigService] SharedPreferences save error: $e');
    }

    try {
      final file = _legacyConfigFile;
      if (!await file.parent.exists()) {
        await file.parent.create(recursive: true);
      }
      await file.writeAsString(jsonEncode(_config.toJson()));
    } catch (e) {
      debugPrint('[ConfigService] Legacy file save error: $e');
    }
  }
}

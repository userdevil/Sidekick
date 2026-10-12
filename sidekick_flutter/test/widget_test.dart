import 'package:flutter_test/flutter_test.dart';
import 'package:sidekick_flutter/models/app_config.dart';

void main() {
  group('AppConfig Tests', () {
    test('default configuration values are correct', () {
      const config = AppConfig();
      expect(config.intervalMinutes, 30);
      expect(config.popupDurationSeconds, 15);
      expect(config.soundEnabled, true);
    });

    test('random message comes from default messages list', () {
      const config = AppConfig();
      final msg = config.getRandomMessage();
      expect(AppConfig.defaultMessages.contains(msg), true);
    });

    test('json serialization and deserialization works roundtrip', () {
      const config = AppConfig(
        intervalMinutes: 45,
        popupDurationSeconds: 20,
        soundEnabled: false,
      );

      final json = config.toJson();
      final fromJson = AppConfig.fromJson(json);

      expect(fromJson.intervalMinutes, 45);
      expect(fromJson.popupDurationSeconds, 20);
      expect(fromJson.soundEnabled, false);
    });

    test('copyWith properly overrides selected fields', () {
      const config = AppConfig();
      final updated = config.copyWith(intervalMinutes: 60);

      expect(updated.intervalMinutes, 60);
      expect(updated.popupDurationSeconds, 15);
      expect(updated.soundEnabled, true);
    });
  });
}

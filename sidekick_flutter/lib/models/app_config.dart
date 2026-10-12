import 'dart:math';

/// Configuration data for Sidekick.
class AppConfig {
  const AppConfig({
    this.intervalMinutes = 30,
    this.popupDurationSeconds = 15,
    this.soundEnabled = true,
  });

  final int intervalMinutes;
  final int popupDurationSeconds;
  final bool soundEnabled;

  static const List<String> defaultMessages = [
    "Hey! Time for a water break! 💧\nDid you drink a glass of water?",
    "Hydration check! 🥤\nDid you drink some water recently?",
    "Stay refreshed, superstar! 🌟\nHave you had a glass of water?",
    "Your cells need fuel! 💧\nDid you take a water break?",
    "Friendly reminder from your buddy! 💦\nDid you drink water?",
    "Sip sip hooray! 🎉\nDid you drink a glass of water?",
    "Keep that energy up! ⚡\nHave you had fresh water today?",
  ];

  String getRandomMessage() {
    final random = Random();
    return defaultMessages[random.nextInt(defaultMessages.length)];
  }

  AppConfig copyWith({
    int? intervalMinutes,
    int? popupDurationSeconds,
    bool? soundEnabled,
  }) {
    return AppConfig(
      intervalMinutes: intervalMinutes ?? this.intervalMinutes,
      popupDurationSeconds: popupDurationSeconds ?? this.popupDurationSeconds,
      soundEnabled: soundEnabled ?? this.soundEnabled,
    );
  }

  Map<String, dynamic> toJson() => {
        'interval_minutes': intervalMinutes,
        'popup_duration_seconds': popupDurationSeconds,
        'sound_enabled': soundEnabled,
      };

  factory AppConfig.fromJson(Map<String, dynamic> json) {
    return AppConfig(
      intervalMinutes: (json['interval_minutes'] as num?)?.toInt() ?? 30,
      popupDurationSeconds:
          (json['popup_duration_seconds'] as num?)?.toInt() ?? 15,
      soundEnabled: json['sound_enabled'] as bool? ?? true,
    );
  }
}

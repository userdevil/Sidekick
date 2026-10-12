import 'package:flutter/material.dart';
import '../models/app_config.dart';

class SettingsDialog extends StatefulWidget {
  const SettingsDialog({
    super.key,
    required this.initialConfig,
    required this.onSave,
    required this.onTest,
  });

  final AppConfig initialConfig;
  final ValueChanged<AppConfig> onSave;
  final VoidCallback onTest;

  @override
  State<SettingsDialog> createState() => _SettingsDialogState();
}

class _SettingsDialogState extends State<SettingsDialog> {
  late int _intervalMinutes;
  late int _popupDurationSeconds;
  late bool _soundEnabled;

  @override
  void initState() {
    super.initState();
    _intervalMinutes = widget.initialConfig.intervalMinutes;
    _popupDurationSeconds = widget.initialConfig.popupDurationSeconds;
    _soundEnabled = widget.initialConfig.soundEnabled;
  }

  String _intervalLabel(int mins) {
    if (mins < 60) {
      return 'Every $mins minute${mins != 1 ? 's' : ''}';
    }
    final h = mins ~/ 60;
    final m = mins % 60;
    return 'Every $h hour${h != 1 ? 's' : ''}${m > 0 ? ' $m min' : ''}';
  }

  @override
  Widget build(BuildContext context) {
    const bg = Color(0xFFE3F2FD);
    const accent = Color(0xFF1565C0);
    const textFg = Color(0xFF37474F);

    return Dialog(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      backgroundColor: bg,
      elevation: 16,
      child: Container(
        width: 420,
        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 20),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Header
            const Center(
              child: Text(
                '💧 Sidekick Settings',
                style: TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.bold,
                  color: accent,
                  fontFamily: 'Segoe UI',
                ),
              ),
            ),
            const SizedBox(height: 4),
            const Center(
              child: Text(
                'Stay hydrated, stay healthy!',
                style: TextStyle(
                  fontSize: 12,
                  fontStyle: FontStyle.italic,
                  color: Color(0xFF78909C),
                ),
              ),
            ),
            const SizedBox(height: 18),

            // Interval Section
            Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: Colors.white.withValues(alpha: 0.65),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: const Color(0xFFBBDEFB)),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text(
                        '⏱ Reminder Interval',
                        style: TextStyle(
                          fontWeight: FontWeight.bold,
                          color: accent,
                          fontSize: 13,
                        ),
                      ),
                      Text(
                        _intervalLabel(_intervalMinutes),
                        style: const TextStyle(
                          fontSize: 12.5,
                          fontWeight: FontWeight.w600,
                          color: textFg,
                        ),
                      ),
                    ],
                  ),
                  Slider(
                    value: _intervalMinutes.toDouble(),
                    min: 1,
                    max: 120,
                    divisions: 119,
                    activeColor: accent,
                    onChanged: (val) {
                      setState(() {
                        _intervalMinutes = val.round();
                      });
                    },
                  ),
                  // Preset pills
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                    children: [5, 15, 30, 45, 60, 90].map((mins) {
                      final isSelected = _intervalMinutes == mins;
                      return InkWell(
                        onTap: () {
                          setState(() {
                            _intervalMinutes = mins;
                          });
                        },
                        borderRadius: BorderRadius.circular(6),
                        child: Container(
                          padding: const EdgeInsets.symmetric(
                              horizontal: 8, vertical: 4),
                          decoration: BoxDecoration(
                            color: isSelected ? accent : const Color(0xFFBBDEFB),
                            borderRadius: BorderRadius.circular(6),
                          ),
                          child: Text(
                            '${mins}m',
                            style: TextStyle(
                              fontSize: 11,
                              fontWeight: FontWeight.bold,
                              color: isSelected ? Colors.white : accent,
                            ),
                          ),
                        ),
                      );
                    }).toList(),
                  ),
                ],
              ),
            ),

            const SizedBox(height: 14),

            // Popup Duration Section
            Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: Colors.white.withValues(alpha: 0.65),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: const Color(0xFFBBDEFB)),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text(
                        '🕐 Popup Duration',
                        style: TextStyle(
                          fontWeight: FontWeight.bold,
                          color: accent,
                          fontSize: 13,
                        ),
                      ),
                      Text(
                        '$_popupDurationSeconds seconds',
                        style: const TextStyle(
                          fontSize: 12.5,
                          fontWeight: FontWeight.w600,
                          color: textFg,
                        ),
                      ),
                    ],
                  ),
                  Slider(
                    value: _popupDurationSeconds.toDouble(),
                    min: 5,
                    max: 60,
                    divisions: 55,
                    activeColor: accent,
                    onChanged: (val) {
                      setState(() {
                        _popupDurationSeconds = val.round();
                      });
                    },
                  ),
                ],
              ),
            ),

            const SizedBox(height: 12),

            // Sound Toggle
            CheckboxListTile(
              value: _soundEnabled,
              onChanged: (val) {
                setState(() {
                  _soundEnabled = val ?? true;
                });
              },
              title: const Text(
                '🔊 Play notification sound',
                style: TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w500,
                  color: textFg,
                ),
              ),
              activeColor: accent,
              dense: true,
              contentPadding: EdgeInsets.zero,
              controlAffinity: ListTileControlAffinity.leading,
            ),

            const SizedBox(height: 16),

            // Actions
            Row(
              children: [
                OutlinedButton.icon(
                  onPressed: () {
                    widget.onTest();
                    Navigator.of(context).pop();
                  },
                  icon: const Icon(Icons.notifications_active, size: 16),
                  label: const Text('Test'),
                  style: OutlinedButton.styleFrom(
                    backgroundColor: const Color(0xFFC8E6C9),
                    foregroundColor: const Color(0xFF2E7D32),
                    side: const BorderSide(color: Color(0xFFA5D6A7)),
                  ),
                ),
                const Spacer(),
                TextButton(
                  onPressed: () => Navigator.of(context).pop(),
                  child: const Text('Cancel', style: TextStyle(color: textFg)),
                ),
                const SizedBox(width: 8),
                ElevatedButton(
                  onPressed: () {
                    final updated = widget.initialConfig.copyWith(
                      intervalMinutes: _intervalMinutes,
                      popupDurationSeconds: _popupDurationSeconds,
                      soundEnabled: _soundEnabled,
                    );
                    widget.onSave(updated);
                    Navigator.of(context).pop();
                  },
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF1E88E5),
                    foregroundColor: Colors.white,
                  ),
                  child: const Text('Save'),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

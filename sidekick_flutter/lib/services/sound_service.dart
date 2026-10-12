import 'dart:ffi';
import 'dart:io';
import 'package:flutter/foundation.dart';

typedef _MessageBeepNative = Int32 Function(Uint32 uType);
typedef _MessageBeepDart = int Function(int uType);

/// Plays Windows native sound chimes via Win32 MessageBeep.
class SoundService {
  static _MessageBeepDart? _messageBeep;
  static bool _initialized = false;

  static void _init() {
    if (_initialized) return;
    _initialized = true;
    if (Platform.isWindows) {
      try {
        final user32 = DynamicLibrary.open('user32.dll');
        _messageBeep = user32
            .lookupFunction<_MessageBeepNative, _MessageBeepDart>('MessageBeep');
      } catch (e) {
        debugPrint('[SoundService] Could not load user32.dll MessageBeep: $e');
      }
    }
  }

  /// System Exclamation (Popup appearance)
  static void playExclamation() {
    _init();
    try {
      _messageBeep?.call(0x00000030); // MB_ICONEXCLAMATION
    } catch (_) {}
  }

  /// System Asterisk (Joyful celebration sound)
  static void playAsterisk() {
    _init();
    try {
      _messageBeep?.call(0x00000040); // MB_ICONASTERISK
    } catch (_) {}
  }

  /// System Hand / Stop (Sad negative sound)
  static void playHand() {
    _init();
    try {
      _messageBeep?.call(0x00000010); // MB_ICONHAND
    } catch (_) {}
  }
}

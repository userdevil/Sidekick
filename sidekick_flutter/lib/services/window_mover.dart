import 'dart:ffi';
import 'dart:io';
import 'package:ffi/ffi.dart';
import 'package:flutter/material.dart';
import 'package:window_manager/window_manager.dart';

typedef _FindWindowWNative = IntPtr Function(
    Pointer<Utf16> lpClassName, Pointer<Utf16> lpWindowName);
typedef _FindWindowWDart = int Function(
    Pointer<Utf16> lpClassName, Pointer<Utf16> lpWindowName);

typedef _SetWindowPosNative = Int32 Function(IntPtr hWnd, IntPtr hWndInsertAfter,
    Int32 X, Int32 Y, Int32 cx, Int32 cy, Uint32 uFlags);
typedef _SetWindowPosDart = int Function(
    int hWnd, int hWndInsertAfter, int X, int Y, int cx, int cy, int uFlags);

/// High-performance window positioning helper using direct Win32 FFI with
/// fallback to windowManager.setPosition.
class WindowMover {
  static int _hwnd = 0;
  static _SetWindowPosDart? _setWindowPos;
  static bool _initialized = false;

  // Win32 constants
  static const int _swpNosize = 0x0001;
  static const int _swpNozorder = 0x0004;
  static const int _swpNoactivate = 0x0010;

  static void init(String windowTitle) {
    if (_initialized) return;
    _initialized = true;

    if (Platform.isWindows) {
      try {
        final user32 = DynamicLibrary.open('user32.dll');
        final findWindow = user32
            .lookupFunction<_FindWindowWNative, _FindWindowWDart>('FindWindowW');
        _setWindowPos = user32
            .lookupFunction<_SetWindowPosNative, _SetWindowPosDart>('SetWindowPos');

        final titlePtr = windowTitle.toNativeUtf16();
        _hwnd = findWindow(nullptr, titlePtr);
        calloc.free(titlePtr);
      } catch (e) {
        debugPrint('[WindowMover] FFI setup failed: $e');
      }
    }
  }

  /// Sets window position synchronously via Win32 FFI (0 latency),
  /// or asynchronously via windowManager.
  static void setPosition(double x, double y) {
    if (_hwnd != 0 && _setWindowPos != null) {
      _setWindowPos!(
        _hwnd,
        0,
        x.round(),
        y.round(),
        0,
        0,
        _swpNosize | _swpNozorder | _swpNoactivate,
      );
    } else {
      windowManager.setPosition(Offset(x, y));
    }
  }
}

import 'dart:io';
import 'package:flutter/material.dart';
import 'package:tray_manager/tray_manager.dart';
import 'package:window_manager/window_manager.dart';

import 'services/config_service.dart';
import 'services/reminder_service.dart';
import 'services/window_mover.dart';
import 'ui/mascot_overlay.dart';
import 'ui/settings_dialog.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Initialize WindowManager
  await windowManager.ensureInitialized();

  const windowOptions = WindowOptions(
    size: Size(380, 430),
    backgroundColor: Colors.transparent,
    skipTaskbar: true,
    titleBarStyle: TitleBarStyle.hidden,
    alwaysOnTop: true,
  );

  await windowManager.waitUntilReadyToShow(windowOptions, () async {
    await windowManager.setAsFrameless();
    await windowManager.setHasShadow(false);
    await windowManager.hide();
  });

  WindowMover.init('sidekick_flutter');

  final configService = ConfigService();
  final reminderService = ReminderService(configService: configService);

  runApp(
    SidekickApp(
      configService: configService,
      reminderService: reminderService,
    ),
  );
}

class SidekickApp extends StatefulWidget {
  const SidekickApp({
    super.key,
    required this.configService,
    required this.reminderService,
  });

  final ConfigService configService;
  final ReminderService reminderService;

  @override
  State<SidekickApp> createState() => _SidekickAppState();
}

class _SidekickAppState extends State<SidekickApp> with TrayListener {
  final GlobalKey<MascotOverlayState> _mascotKey = GlobalKey<MascotOverlayState>();

  @override
  void initState() {
    super.initState();
    trayManager.addListener(this);
    _initTray();

    widget.reminderService.onTriggerPopup = () {
      _mascotKey.currentState?.startAnimation();
    };

    // First greeting popup after a short boot delay (like original Python app)
    Future.delayed(const Duration(milliseconds: 1400), () {
      if (mounted) {
        widget.reminderService.triggerPopup();
      }
    });
  }

  Future<void> _initTray() async {
    try {
      final iconPath = Platform.isWindows
          ? 'assets/tray_icon.ico'
          : 'assets/tray_icon.png';
      await trayManager.setIcon(iconPath);
      await trayManager.setToolTip('Sidekick 💧');

      final menu = Menu(
        items: [
          MenuItem(
            key: 'drink_now',
            label: '💧  Drink Water Now!',
          ),
          MenuItem(
            key: 'settings',
            label: '⚙  Settings',
          ),
          MenuItem.separator(),
          MenuItem(
            key: 'quit',
            label: '❌  Quit',
          ),
        ],
      );
      await trayManager.setContextMenu(menu);
    } catch (e) {
      debugPrint('[Sidekick] Tray setup error: $e');
    }
  }

  @override
  void onTrayIconMouseDown() {
    trayManager.popUpContextMenu();
  }

  @override
  void onTrayIconRightMouseDown() {
    trayManager.popUpContextMenu();
  }

  @override
  void onTrayMenuItemClick(MenuItem menuItem) {
    switch (menuItem.key) {
      case 'drink_now':
        widget.reminderService.triggerPopup();
        break;
      case 'settings':
        _openSettings();
        break;
      case 'quit':
        trayManager.destroy();
        windowManager.destroy();
        exit(0);
    }
  }

  void _openSettings() {
    windowManager.show();
    final ctx = _mascotKey.currentContext;
    if (ctx != null) {
      showDialog(
        context: ctx,
        barrierColor: Colors.black26,
        builder: (dialogCtx) => SettingsDialog(
          initialConfig: widget.configService.config,
          onSave: (newConfig) {
            widget.configService.updateConfig(newConfig);
          },
          onTest: () {
            widget.reminderService.triggerPopup(isTest: true);
          },
        ),
      );
    }
  }

  @override
  void dispose() {
    trayManager.removeListener(this);
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Sidekick',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        fontFamily: 'Segoe UI',
        useMaterial3: true,
        colorSchemeSeed: const Color(0xFF0288D1),
      ),
      home: Scaffold(
        backgroundColor: Colors.transparent,
        body: MascotOverlay(
          key: _mascotKey,
          configService: widget.configService,
          onDismissed: () {
            widget.reminderService.onPopupDismissed();
          },
        ),
      ),
    );
  }
}

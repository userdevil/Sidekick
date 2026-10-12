import 'dart:async';
import 'dart:math';
import 'package:flutter/material.dart';
import 'package:screen_retriever/screen_retriever.dart';
import 'package:window_manager/window_manager.dart';

import '../models/particle.dart';
import '../services/config_service.dart';
import '../services/sound_service.dart';
import '../services/window_mover.dart';
import 'particles_painter.dart';
import 'settings_dialog.dart';
import 'speech_bubble.dart';
import 'water_buddy_widget.dart';

enum MascotState {
  walkIn,
  idle,
  positiveReaction,
  runAway,
  negativeReaction,
  walkBackSad,
  hidden,
}

class MascotOverlay extends StatefulWidget {
  const MascotOverlay({
    super.key,
    required this.configService,
    required this.onDismissed,
  });

  final ConfigService configService;
  final VoidCallback onDismissed;

  @override
  State<MascotOverlay> createState() => MascotOverlayState();
}

class MascotOverlayState extends State<MascotOverlay>
    with SingleTickerProviderStateMixin {
  static const double winW = 380;
  static const double winH = 430;
  static const double targetStopX = 85.0;

  double _screenWidth = 1920;
  double _screenHeight = 1080;
  double _groundY = 600;
  double _currentX = -winW;

  MascotState _state = MascotState.hidden;
  int _frameCount = 0;
  double _walkPhase = 0.0;
  double _runPhase = 0.0;
  double _sadPhase = 0.0;
  double _idlePhase = 0.0;
  int _reactionTimer = 0;

  String _currentMessage = '';
  bool _showButtons = false;

  final List<Particle> _particles = [];
  Timer? _loopTimer;
  Timer? _timeoutTimer;

  // Repaint notifier for 60 FPS particles
  final ValueNotifier<int> _ticker = ValueNotifier<int>(0);

  @override
  void initState() {
    super.initState();
    _initScreenMetrics();
  }

  Future<void> _initScreenMetrics() async {
    try {
      final primary = await screenRetriever.getPrimaryDisplay();
      _screenWidth = primary.size.width;
      _screenHeight = primary.size.height;
    } catch (_) {
      // Safe fallback
    }
    _groundY = _screenHeight - winH - 45;
  }

  /// Starts the mascot animation sequence
  Future<void> startAnimation({String? customMessage}) async {
    await _initScreenMetrics();
    _timeoutTimer?.cancel();

    _currentMessage = customMessage ??
        widget.configService.config.getRandomMessage();
    _state = MascotState.walkIn;
    _frameCount = 0;
    _walkPhase = 0.0;
    _runPhase = 0.0;
    _sadPhase = 0.0;
    _idlePhase = 0.0;
    _reactionTimer = 0;
    _showButtons = false;
    _particles.clear();
    _currentX = -winW;

    WindowMover.setPosition(_currentX, _groundY);
    await windowManager.show();
    await windowManager.setAlwaysOnTop(true);

    if (widget.configService.config.soundEnabled) {
      SoundService.playExclamation();
    }

    _startLoop();
  }

  void _startLoop() {
    _loopTimer?.cancel();
    _loopTimer = Timer.periodic(const Duration(milliseconds: 25), (_) {
      if (!mounted) return;
      _tick();
    });
  }

  void _tick() {
    _frameCount++;
    _updateParticles();

    switch (_state) {
      case MascotState.walkIn:
        _tickWalkIn();
        break;
      case MascotState.idle:
        _tickIdle();
        break;
      case MascotState.positiveReaction:
        _tickPositiveReaction();
        break;
      case MascotState.runAway:
        _tickRunAway();
        break;
      case MascotState.negativeReaction:
        _tickNegativeReaction();
        break;
      case MascotState.walkBackSad:
        _tickWalkBackSad();
        break;
      case MascotState.hidden:
        _loopTimer?.cancel();
        return;
    }

    _ticker.value = _frameCount;
    if (mounted) setState(() {});
  }

  // ── 1. Walk In ──────────────────────────────────────────────────────────
  void _tickWalkIn() {
    _walkPhase += 0.22;
    const walkSpeed = 5.5;
    _currentX += walkSpeed;

    final bobY = sin(_walkPhase).abs() * 8.5;

    // Footstep ripple
    if (bobY < 1.2 && Random().nextDouble() < 0.4) {
      _particles.add(
        Particle(
          type: ParticleType.footstepRipple,
          x: 190 + (Random().nextDouble() * 30 - 15),
          y: 395,
          color: const Color(0xFF81D4FA),
          size: 6,
          maxLife: 12,
        ),
      );
    }

    final winY = _groundY - bobY;
    WindowMover.setPosition(_currentX, winY);

    if (_currentX >= targetStopX) {
      _currentX = targetStopX;
      WindowMover.setPosition(_currentX, _groundY);
      _state = MascotState.idle;
      _showButtons = true;

      // Auto-dismiss timeout
      _timeoutTimer = Timer(
        Duration(seconds: widget.configService.config.popupDurationSeconds),
        () {
          if (_state == MascotState.idle) {
            _onPositive();
          }
        },
      );
    }
  }

  // ── 2. Idle ─────────────────────────────────────────────────────────────
  void _tickIdle() {
    _idlePhase += 0.08;

    // Sparkles
    if (_frameCount % 20 == 0) {
      final rnd = Random();
      _particles.add(
        Particle(
          type: ParticleType.sparkle,
          x: 190 + (rnd.nextDouble() * 120 - 60),
          y: 280 + (rnd.nextDouble() * 100 - 60),
          size: 4 + rnd.nextDouble() * 3,
          color: rnd.nextBool()
              ? const Color(0xFFFFD54F)
              : const Color(0xFF81D4FA),
          maxLife: 14,
        ),
      );
    }
  }

  // ── 3. Positive Reaction ─────────────────────────────────────────────────
  void _onPositive() {
    if (_state != MascotState.idle && _state != MascotState.walkIn) return;
    _timeoutTimer?.cancel();
    _showButtons = false;
    _state = MascotState.positiveReaction;
    _reactionTimer = 0;
    _currentMessage = "WOOHOO! 🎉 Awesome job!\nStay hydrated, superstar! 💧✨";

    if (widget.configService.config.soundEnabled) {
      SoundService.playAsterisk();
    }

    // Burst celebration confetti
    final colors = [
      const Color(0xFFFFD54F),
      const Color(0xFF4FC3F7),
      const Color(0xFF81C784),
      const Color(0xFFFF8A80),
      const Color(0xFFBA68C8),
      const Color(0xFF4DD0E1),
    ];
    final rnd = Random();
    for (int i = 0; i < 28; i++) {
      _particles.add(
        Particle(
          type: ParticleType.confetti,
          x: 190 + (rnd.nextDouble() * 80 - 40),
          y: 240 + (rnd.nextDouble() * 40 - 20),
          vx: rnd.nextDouble() * 12 - 6,
          vy: -(rnd.nextDouble() * 7 + 3),
          size: rnd.nextDouble() * 4 + 3,
          color: colors[rnd.nextInt(colors.length)],
          isCircle: rnd.nextBool(),
          maxLife: 45,
        ),
      );
    }
  }

  void _tickPositiveReaction() {
    _reactionTimer++;
    if (_reactionTimer >= 26) {
      _state = MascotState.runAway;
      _runPhase = 0.0;
    }
  }

  // ── 4. Run Away Happily ──────────────────────────────────────────────────
  void _tickRunAway() {
    _runPhase += 0.42;
    const runSpeed = 16.5;
    _currentX += runSpeed;

    final bobY = sin(_runPhase).abs() * 14.0;
    WindowMover.setPosition(_currentX, _groundY - bobY);

    // Speed puffs
    if (_frameCount % 2 == 0) {
      final rnd = Random();
      _particles.add(
        Particle(
          type: ParticleType.speedPuff,
          x: 120 + (rnd.nextDouble() * 20 - 10),
          y: 360 + (rnd.nextDouble() * 14 - 7),
          vx: -5.0,
          vy: -0.5,
          size: rnd.nextDouble() * 5 + 4,
          color: const Color(0xCCB2EBF2),
          maxLife: 15,
        ),
      );
    }

    if (_currentX > _screenWidth + 60) {
      _finishAndClose();
    }
  }

  // ── 5. Negative Reaction ─────────────────────────────────────────────────
  void _onNegative() {
    if (_state != MascotState.idle && _state != MascotState.walkIn) return;
    _timeoutTimer?.cancel();
    _showButtons = false;
    _state = MascotState.negativeReaction;
    _reactionTimer = 0;
    _currentMessage = "Aww... 🥺 Please go grab\na glass of water now, okay? 💔";

    if (widget.configService.config.soundEnabled) {
      SoundService.playHand();
    }

    // Add sad rain cloud
    _particles.add(
      Particle(
        type: ParticleType.sadCloud,
        x: 190,
        y: 155,
        color: const Color(0xFF90A4AE),
        maxLife: 300,
      ),
    );
  }

  void _tickNegativeReaction() {
    _reactionTimer++;

    // Raindrops falling
    if (_reactionTimer % 4 == 0) {
      final rnd = Random();
      _particles.add(
        Particle(
          type: ParticleType.rainDrop,
          x: 190 + (rnd.nextDouble() * 44 - 22),
          y: 175,
          vx: -0.3,
          vy: 5.0,
          color: const Color(0xFF29B6F6),
          maxLife: 22,
        ),
      );
    }

    if (_reactionTimer >= 32) {
      _state = MascotState.walkBackSad;
      _sadPhase = 0.0;
    }
  }

  // ── 6. Walk Back Sadly ───────────────────────────────────────────────────
  void _tickWalkBackSad() {
    _sadPhase += 0.14;
    const sadSpeed = 3.6;
    _currentX -= sadSpeed;

    final bobY = sin(_sadPhase).abs() * 5.0;
    WindowMover.setPosition(_currentX, _groundY - bobY);

    if (_frameCount % 8 == 0) {
      final rnd = Random();
      _particles.add(
        Particle(
          type: ParticleType.rainDrop,
          x: 190 + (rnd.nextDouble() * 40 - 20),
          y: 175,
          vx: -0.3,
          vy: 5.0,
          color: const Color(0xFF29B6F6),
          maxLife: 22,
        ),
      );
    }

    if (_currentX < -winW - 40) {
      _finishAndClose();
    }
  }

  void _finishAndClose() {
    _state = MascotState.hidden;
    _loopTimer?.cancel();
    _timeoutTimer?.cancel();
    windowManager.hide();
    widget.onDismissed();
  }

  void _updateParticles() {
    for (final p in _particles) {
      p.update();
    }
    _particles.removeWhere((p) => p.isDead);
  }

  void _openSettings() {
    showDialog(
      context: context,
      barrierColor: Colors.black26,
      builder: (ctx) => SettingsDialog(
        initialConfig: widget.configService.config,
        onSave: (newConfig) {
          widget.configService.updateConfig(newConfig);
        },
        onTest: () {
          startAnimation();
        },
      ),
    );
  }

  @override
  void dispose() {
    _loopTimer?.cancel();
    _timeoutTimer?.cancel();
    _ticker.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (_state == MascotState.hidden) {
      return const SizedBox.shrink();
    }

    // Calculate Mascot visual transforms
    double bobY = 0.0;
    double angleDeg = 0.0;
    bool facingRight = true;
    bool isSad = false;
    double jumpY = 0.0;

    switch (_state) {
      case MascotState.walkIn:
        bobY = sin(_walkPhase).abs() * 8.5;
        angleDeg = sin(_walkPhase) * 3.5;
        facingRight = true;
        break;
      case MascotState.idle:
        bobY = sin(_idlePhase) * 3.0;
        facingRight = true;
        break;
      case MascotState.positiveReaction:
        final t = _reactionTimer / 26.0;
        jumpY = -sin(t * pi) * 28.0;
        angleDeg = sin(_reactionTimer * 0.4) * 5.0;
        facingRight = true;
        break;
      case MascotState.runAway:
        bobY = sin(_runPhase).abs() * 14.0;
        angleDeg = -11.0; // forward lean
        facingRight = true;
        break;
      case MascotState.negativeReaction:
        final t = min(1.0, _reactionTimer / 20.0);
        bobY = -t * 8.0;
        angleDeg = 2.0;
        isSad = true;
        facingRight = true;
        break;
      case MascotState.walkBackSad:
        bobY = sin(_sadPhase).abs() * 5.0;
        angleDeg = 3.5;
        facingRight = false;
        isSad = true;
        break;
      case MascotState.hidden:
        break;
    }

    final spriteAsset = facingRight
        ? 'assets/character_right.png'
        : 'assets/character_left.png';

    return Material(
      color: Colors.transparent,
      child: SizedBox(
        width: winW,
        height: winH,
        child: Stack(
          alignment: Alignment.bottomCenter,
          children: [
            // 1. Ground Shadow
            Positioned(
              bottom: 12,
              child: Container(
                width: 96 + bobY * 1.5,
                height: 14,
                decoration: BoxDecoration(
                  color: const Color(0x6690A4AE),
                  borderRadius: BorderRadius.all(
                    Radius.elliptical(96 + bobY * 1.5, 14),
                  ),
                ),
              ),
            ),

            // 2. Dynamic Particles Layer
            Positioned.fill(
              child: CustomPaint(
                painter: ParticlesPainter(
                  particles: _particles,
                  repaintNotifier: _ticker,
                ),
              ),
            ),

            // 3. Floating Water Buddy (Idle Companion)
            if (_state == MascotState.idle)
              Positioned(
                bottom: 220,
                right: 70,
                child: WaterBuddyWidget(idlePhase: _idlePhase),
              ),

            // 4. Mascot Sprite
            Positioned(
              bottom: 16 - bobY - jumpY,
              child: GestureDetector(
                onTap: _onPositive,
                child: Transform.rotate(
                  angle: angleDeg * pi / 180,
                  alignment: Alignment.bottomCenter,
                  child: ColorFiltered(
                    colorFilter: isSad
                        ? const ColorFilter.mode(
                            Color(0x334FC3F7),
                            BlendMode.srcATop,
                          )
                        : const ColorFilter.mode(
                            Colors.transparent,
                            BlendMode.dst,
                          ),
                    child: Image.asset(
                      spriteAsset,
                      height: 250,
                      fit: BoxFit.contain,
                    ),
                  ),
                ),
              ),
            ),

            // 5. Glasses Star Glint (during positive jump)
            if (_state == MascotState.positiveReaction && _reactionTimer < 20)
              Positioned(
                bottom: 200 - jumpY,
                child: const Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(
                      '✦',
                      style: TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.bold,
                        color: Color(0xFFFFF9C4),
                      ),
                    ),
                    SizedBox(width: 28),
                    Text(
                      '✦',
                      style: TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.bold,
                        color: Color(0xFFFFF9C4),
                      ),
                    ),
                  ],
                ),
              ),

            // 6. Speech Bubble UI
            if (_state != MascotState.hidden &&
                _state != MascotState.walkIn &&
                _currentMessage.isNotEmpty)
              Positioned(
                top: 8,
                child: SpeechBubble(
                  message: _currentMessage,
                  showButtons: _showButtons,
                  onPositive: _onPositive,
                  onNegative: _onNegative,
                  onSettings: _openSettings,
                ),
              ),
          ],
        ),
      ),
    );
  }
}

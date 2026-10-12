import 'package:flutter/material.dart';

enum ParticleType {
  confetti,
  rainDrop,
  speedPuff,
  footstepRipple,
  sparkle,
  sadCloud,
}

class Particle {
  Particle({
    required this.type,
    required this.x,
    required this.y,
    this.vx = 0.0,
    this.vy = 0.0,
    this.size = 4.0,
    this.color = Colors.blue,
    required this.maxLife,
    this.isCircle = true,
  }) : currentLife = maxLife;

  final ParticleType type;
  double x;
  double y;
  double vx;
  double vy;
  double size;
  Color color;
  final int maxLife;
  int currentLife;
  final bool isCircle;

  bool get isDead => currentLife <= 0;

  double get progress => (maxLife - currentLife) / maxLife;

  void update() {
    currentLife--;
    x += vx;
    y += vy;

    switch (type) {
      case ParticleType.confetti:
        vy += 0.25; // gravity
        vx *= 0.98; // air drag
        break;
      case ParticleType.rainDrop:
        vy += 0.1;
        break;
      case ParticleType.speedPuff:
        vx *= 0.92;
        size *= 0.96;
        break;
      case ParticleType.footstepRipple:
        size += 1.2;
        break;
      case ParticleType.sparkle:
      case ParticleType.sadCloud:
        break;
    }
  }
}

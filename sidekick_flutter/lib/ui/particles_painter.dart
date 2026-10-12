import 'package:flutter/material.dart';
import '../models/particle.dart';

class ParticlesPainter extends CustomPainter {
  ParticlesPainter({required this.particles, required this.repaintNotifier})
      : super(repaint: repaintNotifier);

  final List<Particle> particles;
  final Listenable repaintNotifier;

  @override
  void paint(Canvas canvas, Size size) {
    for (final p in particles) {
      if (p.isDead) continue;
      final alpha = (1.0 - p.progress).clamp(0.0, 1.0);
      final paint = Paint()
        ..color = p.color.withValues(alpha: p.color.a * alpha)
        ..style = PaintingStyle.fill;

      switch (p.type) {
        case ParticleType.confetti:
          if (p.isCircle) {
            canvas.drawCircle(Offset(p.x, p.y), p.size, paint);
          } else {
            canvas.drawRect(
              Rect.fromCenter(
                center: Offset(p.x, p.y),
                width: p.size * 1.6,
                height: p.size * 1.6,
              ),
              paint,
            );
          }
          break;

        case ParticleType.rainDrop:
          final linePaint = Paint()
            ..color = p.color.withValues(alpha: alpha)
            ..strokeWidth = 2.0
            ..strokeCap = StrokeCap.round;
          canvas.drawLine(
            Offset(p.x, p.y),
            Offset(p.x - 1, p.y + 8),
            linePaint,
          );
          break;

        case ParticleType.speedPuff:
          canvas.drawCircle(Offset(p.x, p.y), p.size, paint);
          break;

        case ParticleType.footstepRipple:
          final strokePaint = Paint()
            ..color = p.color.withValues(alpha: alpha)
            ..style = PaintingStyle.stroke
            ..strokeWidth = 1.5;
          canvas.drawOval(
            Rect.fromCenter(
              center: Offset(p.x, p.y),
              width: p.size * 2,
              height: p.size * 0.7,
            ),
            strokePaint,
          );
          break;

        case ParticleType.sparkle:
          final sparklePaint = Paint()
            ..color = p.color.withValues(alpha: alpha)
            ..strokeWidth = 1.5
            ..strokeCap = StrokeCap.round;
          canvas.drawLine(
            Offset(p.x - p.size, p.y),
            Offset(p.x + p.size, p.y),
            sparklePaint,
          );
          canvas.drawLine(
            Offset(p.x, p.y - p.size),
            Offset(p.x, p.y + p.size),
            sparklePaint,
          );
          break;

        case ParticleType.sadCloud:
          canvas.drawCircle(Offset(p.x - 20, p.y), 24, paint);
          canvas.drawCircle(Offset(p.x + 15, p.y - 6), 28, paint);
          canvas.drawCircle(Offset(p.x + 35, p.y + 4), 20, paint);
          break;
      }
    }
  }

  @override
  bool shouldRepaint(covariant ParticlesPainter oldDelegate) => true;
}

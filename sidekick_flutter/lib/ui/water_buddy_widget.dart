import 'dart:math';
import 'package:flutter/material.dart';

class WaterBuddyWidget extends StatelessWidget {
  const WaterBuddyWidget({super.key, required this.idlePhase});

  final double idlePhase;

  @override
  Widget build(BuildContext context) {
    final bobY = sin(idlePhase * 1.4) * 6.0;

    return Transform.translate(
      offset: Offset(0, bobY),
      child: CustomPaint(
        size: const Size(28, 34),
        painter: _WaterBuddyPainter(),
      ),
    );
  }
}

class _WaterBuddyPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final cx = size.width / 2;
    final cy = size.height / 2 + 3;
    final r = size.width / 2;

    // 1. Water Drop Body
    final path = Path();
    // Tip at top
    path.moveTo(cx, 2);
    // Curves to round bottom
    path.cubicTo(cx + r, cy - 4, cx + r, cy + r, cx, cy + r);
    path.cubicTo(cx - r, cy + r, cx - r, cy - 4, cx, 2);
    path.close();

    final bodyPaint = Paint()
      ..color = const Color(0xFF4FC3F7)
      ..style = PaintingStyle.fill;
    canvas.drawPath(path, bodyPaint);

    final borderPaint = Paint()
      ..color = const Color(0xFF0288D1)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.6;
    canvas.drawPath(path, borderPaint);

    // 2. Eyes
    final eyePaint = Paint()
      ..color = const Color(0xFF1A237E)
      ..style = PaintingStyle.fill;

    canvas.drawOval(
      Rect.fromCenter(center: Offset(cx - 4.5, cy + 1), width: 3.2, height: 4.5),
      eyePaint,
    );
    canvas.drawOval(
      Rect.fromCenter(center: Offset(cx + 4.5, cy + 1), width: 3.2, height: 4.5),
      eyePaint,
    );

    // 3. Smile
    final smilePaint = Paint()
      ..color = const Color(0xFFE91E63)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.4
      ..strokeCap = StrokeCap.round;

    final smilePath = Path()
      ..addArc(
        Rect.fromCenter(center: Offset(cx, cy + 3.5), width: 9, height: 7),
        0.3,
        2.5,
      );
    canvas.drawPath(smilePath, smilePaint);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

import 'dart:async';
import 'package:flutter/material.dart';

class SpeechBubble extends StatefulWidget {
  const SpeechBubble({
    super.key,
    required this.message,
    required this.showButtons,
    required this.onPositive,
    required this.onNegative,
    required this.onSettings,
  });

  final String message;
  final bool showButtons;
  final VoidCallback onPositive;
  final VoidCallback onNegative;
  final VoidCallback onSettings;

  @override
  State<SpeechBubble> createState() => _SpeechBubbleState();
}

class _SpeechBubbleState extends State<SpeechBubble> {
  String _displayedText = '';
  int _charIndex = 0;
  Timer? _typewriterTimer;

  @override
  void initState() {
    super.initState();
    _startTypewriter();
  }

  @override
  void didUpdateWidget(covariant SpeechBubble oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.message != widget.message) {
      _startTypewriter();
    }
  }

  void _startTypewriter() {
    _typewriterTimer?.cancel();
    _displayedText = '';
    _charIndex = 0;

    _typewriterTimer = Timer.periodic(const Duration(milliseconds: 30), (timer) {
      if (!mounted) {
        timer.cancel();
        return;
      }
      if (_charIndex < widget.message.length) {
        setState(() {
          _charIndex = (_charIndex + 2).clamp(0, widget.message.length);
          _displayedText = widget.message.substring(0, _charIndex);
        });
      } else {
        timer.cancel();
      }
    });
  }

  @override
  void dispose() {
    _typewriterTimer?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Stack(
          children: [
            // Speech bubble container
            Container(
              width: 330,
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(18),
                border: Border.all(color: const Color(0xFF0288D1), width: 2.2),
                boxShadow: const [
                  BoxShadow(
                    color: Color(0x33455A64),
                    blurRadius: 8,
                    offset: Offset(2, 4),
                  ),
                ],
              ),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  // Text with typewriter effect
                  Padding(
                    padding: const EdgeInsets.only(top: 4, bottom: 10, right: 20),
                    child: Text(
                      _displayedText,
                      textAlign: TextAlign.center,
                      style: const TextStyle(
                        fontFamily: 'Segoe UI',
                        fontSize: 13.5,
                        fontWeight: FontWeight.bold,
                        color: Color(0xFF1E293B),
                        height: 1.35,
                      ),
                    ),
                  ),

                  // Interactive buttons
                  if (widget.showButtons)
                    Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        // Positive button
                        Expanded(
                          child: ElevatedButton(
                            onPressed: widget.onPositive,
                            style: ElevatedButton.styleFrom(
                              backgroundColor: const Color(0xFF0288D1),
                              foregroundColor: Colors.white,
                              elevation: 2,
                              padding: const EdgeInsets.symmetric(vertical: 10),
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(10),
                              ),
                            ),
                            child: const Text(
                              '💧 Yes, drank!',
                              style: TextStyle(
                                fontSize: 12.5,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ),
                        ),
                        const SizedBox(width: 8),
                        // Negative button
                        Expanded(
                          child: OutlinedButton(
                            onPressed: widget.onNegative,
                            style: OutlinedButton.styleFrom(
                              backgroundColor: const Color(0xFFFFF1F2),
                              foregroundColor: const Color(0xFFBE123C),
                              side: const BorderSide(color: Color(0xFFFDA4AF)),
                              padding: const EdgeInsets.symmetric(vertical: 10),
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(10),
                              ),
                            ),
                            child: const Text(
                              '😢 Not yet',
                              style: TextStyle(
                                fontSize: 12.5,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ),
                        ),
                      ],
                    ),
                ],
              ),
            ),

            // Top-right Settings Button
            Positioned(
              top: 8,
              right: 8,
              child: InkWell(
                onTap: widget.onSettings,
                borderRadius: BorderRadius.circular(14),
                child: Container(
                  width: 26,
                  height: 26,
                  decoration: BoxDecoration(
                    color: const Color(0xFFF1F5F9),
                    shape: BoxShape.circle,
                    border: Border.all(color: const Color(0xFFCBD5E1)),
                  ),
                  child: const Center(
                    child: Text(
                      '⚙',
                      style: TextStyle(fontSize: 12, color: Color(0xFF64748B)),
                    ),
                  ),
                ),
              ),
            ),
          ],
        ),

        // Pointer triangle pointing downwards
        CustomPaint(
          size: const Size(22, 12),
          painter: _BubblePointerPainter(),
        ),
      ],
    );
  }
}

class _BubblePointerPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final path = Path()
      ..moveTo(0, 0)
      ..lineTo(size.width / 2, size.height)
      ..lineTo(size.width, 0)
      ..close();

    final fillPaint = Paint()
      ..color = Colors.white
      ..style = PaintingStyle.fill;

    final strokePaint = Paint()
      ..color = const Color(0xFF0288D1)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2.2;

    canvas.drawPath(path, fillPaint);
    canvas.drawLine(Offset.zero, Offset(size.width / 2, size.height), strokePaint);
    canvas.drawLine(Offset(size.width, 0), Offset(size.width / 2, size.height), strokePaint);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

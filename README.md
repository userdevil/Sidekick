# 💧 Sidekick — Animated Desktop Mascot & Companion

**Sidekick** is a customizable Windows desktop companion that walks onto your screen to remind you to drink water and take healthy breaks. Built with Python and Tkinter, it supports **both custom photo avatars and real video clips**, interactive speech bubbles, and emotional animated reactions.

![Platform](https://img.shields.io/badge/Platform-Windows-blue) ![Python](https://img.shields.io/badge/Python-3.9+-brightgreen) ![License](https://img.shields.io/badge/License-MIT-purple)

---

## ✨ Features & Animation Flow

1. **🚶‍♂️ Walks In from Left**:
   - The character (from video or cutout photo) walks in from the left edge of your screen with rhythmic stride bobbing, swaying tilt, and footstep ripples.
   - Stops above your Windows taskbar.

2. **💬 Interactive Speech Bubble**:
   - A rounded speech bubble appears with typewriter effect:
     *"Hey! Time for a water break! 💧 Did you drink a glass of water?"*
   - A floating water droplet companion bobs near his shoulder.
   - Interactive response options:
     - `[ 💧 Yes, drank! ]` (Positive response)
     - `[ 😢 Not yet ]` (Negative response)
     - `[ ⚙ ]` (Settings button in top right)
     - *(Clicking directly on the character also triggers the positive reaction!)*

3. **🎉 Positive Response (`Yes, drank!`)**:
   - Joyful celebration jump!
   - Sunglasses star glint (`✦`) and colorful confetti & water bubbles explosion!
   - Happy sound chime (`SystemAsterisk`).
   - Leans forward into a sprint and **runs across the screen from left to right happily** with speed trails (`💨 ═ ═`)!

4. **😢 Negative Response (`Not yet`)**:
   - Slumps down sadly with a drooping head.
   - A sad raincloud (`🌧️`) forms above him with falling raindrops (`💧`).
   - Turns around to face left.
   - **Walks back to the left sadly** with slow, heavy, dejected footsteps.

5. **🎥 Video Character Mode (New!)**:
   - Drop your own video clips directly into the project folder:
     - `walk.mp4` / `walk.gif` — Played during the walk-in animation.
     - `happy.mp4` / `happy.gif` — Played during the positive reaction and run.
     - `sad.mp4` / `sad.gif` — Played during the negative sad walk-back.
     - `character.mp4` / `character.gif` — Universal single-video fallback.
   - **Green-Screen Chroma Key**: Automatically removes green backgrounds so your video character floats seamlessly on the desktop.
   - If no video files are present, it seamlessly falls back to the high-res cutout photo sprites!

6. **⚙️ Settings Window**:
   - Customize interval (1–120 minutes) with quick-set presets (`5m`, `15m`, `30m`, `45m`, `60m`, `90m`).
   - Sound notification toggle.
   - **"🔔 Test" button**: immediately triggers the walk-in animation so you can test either response anytime!
   - Settings persist to `~/.sidekick/config.json`.

7. **📌 System Tray**:
   - Runs in the Windows system tray with a water droplet icon.
   - Right-click tray menu:
     - `💧 Drink Water Now!` (Triggers animation immediately)
     - `⚙ Settings`
     - `❌ Quit`

---

## 🎬 How to Use Your Own Video Clips

1. Record or export short clips (2–4 seconds each, 24–30 FPS).
2. For best results, use a green background or solid backdrop so the app can key out the background.
3. Save the files into the root folder using any of these names:
   - `walk.mp4` (or `.gif`, `.webm`)
   - `happy.mp4`
   - `sad.mp4`
   *(or simply `character.mp4` for a single universal loop)*
4. Run Sidekick — it will automatically detect and play the video frames!

---

## 🚀 Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/userdevil/Sidekick.git
cd Sidekick
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Run Sidekick
- **Double-click:** `install_and_run.bat`
- **Or via command line (background mode, no console window):**
```bash
pythonw main.pyw
```

---

## 📁 Project Structure

```
Sidekick/
├── main.pyw           # App entry point (.pyw = silent background)
├── app.py             # Controller, timer loop & system tray integration
├── popup.py           # Animated walking mascot & interactive speech bubble
├── video_character.py # Video player, chroma-key & frame extraction engine
├── character_loader.py# Sprite processor & frame transform cache
├── settings_ui.py     # Settings window (interval, sounds, test trigger)
├── config.py          # JSON configuration persistence
├── character_right.png# Right-facing character sprite
├── character_left.png # Left-facing character sprite
├── character_clean.png# Clean cutout character
├── requirements.txt   # Python dependencies
├── install_and_run.bat# One-click Windows launcher
└── README.md          # Documentation
```

---

## 🔮 Future Roadmap (AI Integration)

Sidekick is designed to grow into an intelligent desktop companion:
- **Dynamic Dialogue**: AI-generated responses (OpenAI / Gemini / Ollama) based on your work patterns and mood.
- **Voice Interactions**: AI text-to-speech for vocal greetings and voice check-ins.
- **Vision Tracking**: Lightweight webcam posture & hydration detection.
- **Productivity Agent**: Meeting reminders, focus timers, and daily motivation check-ins.

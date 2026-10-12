"""
Water Reminder — Main application controller.

Manages the reminder timer, system-tray icon (if pystray + Pillow are
installed), and coordinates popups and the settings window.
"""

import tkinter as tk
import threading
import sys

# Optional tray support ────────────────────────────────────────────────
try:
    import pystray                        # type: ignore[import-untyped]
    from PIL import Image, ImageDraw      # type: ignore[import-untyped]
    HAS_TRAY = True
except ImportError:
    HAS_TRAY = False

# Optional sound support (built-in on Windows) ────────────────────────
try:
    import winsound                       # type: ignore[import-untyped]
    HAS_SOUND = True
except ImportError:
    HAS_SOUND = False

from config import Config
from popup import WalkingCharacterWindow
from settings_ui import SettingsWindow


class WaterReminderApp:
    """Top-level application: timer → popup → dismiss → repeat."""

    def __init__(self):
        self.config = Config()

        self.root = tk.Tk()
        self.root.title('Sidekick')
        self.root.withdraw()              # Hidden root window

        self.popup = None
        self.timer_id = None
        self.running = True

        if HAS_TRAY:
            self._setup_tray()

        # First popup after a short delay
        self.root.after(1200, self._show_popup)

        # Start recurring timer
        self._schedule_next()

    # ── Public ────────────────────────────────────────────────────────

    def run(self):
        """Enter the Tk main loop (blocks until quit)."""
        self.root.mainloop()

    # ── Timer ─────────────────────────────────────────────────────────

    def _schedule_next(self):
        if self.timer_id is not None:
            self.root.after_cancel(self.timer_id)
        interval_ms = self.config.interval_minutes * 60 * 1000
        self.timer_id = self.root.after(interval_ms, self._on_timer)

    def _on_timer(self):
        self._show_popup()
        self._schedule_next()

    # ── Popup ─────────────────────────────────────────────────────────

    def _show_popup(self):
        if self.popup is not None:
            try:
                self.popup._finish_and_close()
            except Exception:
                pass
            self.popup = None

        # Notification sound
        if self.config.sound_enabled and HAS_SOUND:
            try:
                winsound.PlaySound(
                    'SystemExclamation',
                    winsound.SND_ALIAS | winsound.SND_ASYNC)
            except Exception:
                pass

        message = self.config.get_random_message()
        self.popup = WalkingCharacterWindow(
            self.root,
            message=message,
            sound_enabled=self.config.sound_enabled,
            on_dismiss=self._on_popup_dismissed,
            on_settings=self._show_settings)

    def _on_popup_dismissed(self):
        self.popup = None

    # ── Settings ──────────────────────────────────────────────────────

    def _show_settings(self):
        SettingsWindow(
            self.root, self.config,
            on_save=self._on_settings_saved)

    def _on_settings_saved(self, test=False):
        self._schedule_next()             # Re-arm with new interval
        if test:
            self.root.after(400, self._show_popup)

    # ── System tray ───────────────────────────────────────────────────

    def _setup_tray(self):
        icon_image = self._make_tray_icon()

        menu = pystray.Menu(
            pystray.MenuItem(
                '💧  Drink Water Now!',
                lambda *_: self.root.after(0, self._show_popup)),
            pystray.MenuItem(
                '⚙  Settings',
                lambda *_: self.root.after(0, self._show_settings)),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                '❌  Quit',
                lambda *_: self.root.after(0, self._quit)),
        )

        self.tray = pystray.Icon(
            'Sidekick', icon_image,
            'Sidekick 💧', menu)

        t = threading.Thread(target=self.tray.run, daemon=True)
        t.start()

    @staticmethod
    def _make_tray_icon():
        """Create a 64×64 water-drop icon for the system tray."""
        size = 64
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)

        # Drop body (circle + triangle)
        d.ellipse([14, 26, 50, 58], fill='#4FC3F7', outline='#29B6F6', width=2)
        d.polygon([(32, 6), (17, 34), (47, 34)], fill='#4FC3F7')
        d.ellipse([16, 28, 48, 56], fill='#4FC3F7')   # Smooth overlap
        # Highlight
        d.ellipse([20, 28, 32, 42], fill='#B3E5FC')
        d.ellipse([22, 30, 28, 36], fill='#E1F5FE')

        return img

    # ── Quit ──────────────────────────────────────────────────────────

    def _quit(self):
        self.running = False
        if HAS_TRAY and hasattr(self, 'tray'):
            try:
                self.tray.stop()
            except Exception:
                pass
        self.root.quit()

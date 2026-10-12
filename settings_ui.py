"""Settings dialog for Water Reminder app."""

import tkinter as tk
from tkinter import ttk


class SettingsWindow:
    """A themed settings dialog for configuring reminder interval, duration, and sound."""

    def __init__(self, root, config, on_save=None):
        self.config = config
        self.on_save = on_save

        self.win = tk.Toplevel(root)
        self.win.title('💧 Sidekick — Settings')
        self.win.geometry('420x440')
        self.win.resizable(False, False)
        self.win.configure(bg='#E3F2FD')

        # Modal behaviour
        self.win.transient(root)
        self.win.grab_set()

        self._create_widgets()
        self._center()

    # ── Widgets ───────────────────────────────────────────────────────

    def _create_widgets(self):
        bg = '#E3F2FD'
        accent = '#1565C0'
        fg = '#37474F'

        # ── Title ──
        tk.Label(
            self.win, text='💧 Sidekick Settings',
            font=('Segoe UI', 17, 'bold'), bg=bg, fg=accent,
        ).pack(pady=(22, 6))

        tk.Label(
            self.win, text='Stay hydrated, stay healthy!',
            font=('Segoe UI', 10, 'italic'), bg=bg, fg='#78909C',
        ).pack(pady=(0, 14))

        # ── Interval ──
        interval_frame = tk.LabelFrame(
            self.win, text=' ⏱  Reminder Interval ',
            font=('Segoe UI', 10, 'bold'), bg=bg, fg=accent,
            padx=20, pady=12)
        interval_frame.pack(fill=tk.X, padx=22, pady=6)

        self.interval_var = tk.IntVar(value=self.config.interval_minutes)
        self.interval_label = tk.Label(
            interval_frame,
            text=self._interval_text(self.config.interval_minutes),
            font=('Segoe UI', 12), bg=bg, fg=fg)
        self.interval_label.pack()

        ttk.Scale(
            interval_frame, from_=1, to=120,
            variable=self.interval_var, orient=tk.HORIZONTAL,
            command=self._on_interval_change,
        ).pack(fill=tk.X, pady=6)

        # Quick-set buttons
        qf = tk.Frame(interval_frame, bg=bg)
        qf.pack(fill=tk.X, pady=(2, 0))
        for mins in (5, 15, 30, 45, 60, 90):
            tk.Button(
                qf, text=f'{mins}m',
                font=('Segoe UI', 9), bg='#BBDEFB', fg=accent,
                activebackground='#90CAF9', relief=tk.FLAT, padx=8,
                command=lambda m=mins: self._quick_set(m),
            ).pack(side=tk.LEFT, padx=3)

        # ── Popup Duration ──
        dur_frame = tk.LabelFrame(
            self.win, text=' 🕐  Popup Duration ',
            font=('Segoe UI', 10, 'bold'), bg=bg, fg=accent,
            padx=20, pady=12)
        dur_frame.pack(fill=tk.X, padx=22, pady=6)

        self.duration_var = tk.IntVar(value=self.config.popup_duration)
        self.duration_label = tk.Label(
            dur_frame,
            text=f'{self.config.popup_duration} seconds',
            font=('Segoe UI', 12), bg=bg, fg=fg)
        self.duration_label.pack()

        ttk.Scale(
            dur_frame, from_=5, to=60,
            variable=self.duration_var, orient=tk.HORIZONTAL,
            command=self._on_duration_change,
        ).pack(fill=tk.X, pady=6)

        # ── Sound toggle ──
        self.sound_var = tk.BooleanVar(value=self.config.sound_enabled)
        tk.Checkbutton(
            self.win, text='  🔊  Play notification sound',
            variable=self.sound_var,
            font=('Segoe UI', 10), bg=bg, fg=fg,
            activebackground=bg, selectcolor=bg,
        ).pack(padx=22, pady=10, anchor=tk.W)

        # ── Action buttons ──
        btn_frame = tk.Frame(self.win, bg=bg)
        btn_frame.pack(fill=tk.X, padx=22, pady=(6, 16))

        tk.Button(
            btn_frame, text='💾  Save',
            font=('Segoe UI', 11, 'bold'),
            bg='#1E88E5', fg='white', activebackground='#1565C0',
            relief=tk.FLAT, padx=22, pady=5,
            command=self._save,
        ).pack(side=tk.RIGHT, padx=5)

        tk.Button(
            btn_frame, text='Cancel',
            font=('Segoe UI', 11),
            bg='#ECEFF1', fg=fg, activebackground='#CFD8DC',
            relief=tk.FLAT, padx=22, pady=5,
            command=self.win.destroy,
        ).pack(side=tk.RIGHT, padx=5)

        tk.Button(
            btn_frame, text='🔔  Test',
            font=('Segoe UI', 11),
            bg='#C8E6C9', fg='#2E7D32', activebackground='#A5D6A7',
            relief=tk.FLAT, padx=16, pady=5,
            command=self._test_popup,
        ).pack(side=tk.LEFT, padx=5)

    # ── Callbacks ─────────────────────────────────────────────────────

    @staticmethod
    def _interval_text(mins):
        if mins < 60:
            return f'Every {mins} minute{"s" if mins != 1 else ""}'
        h, m = divmod(mins, 60)
        parts = [f'{h} hour{"s" if h != 1 else ""}']
        if m:
            parts.append(f'{m} min')
        return 'Every ' + ' '.join(parts)

    def _on_interval_change(self, val):
        mins = int(float(val))
        self.interval_label.config(text=self._interval_text(mins))

    def _on_duration_change(self, val):
        secs = int(float(val))
        self.duration_label.config(text=f'{secs} seconds')

    def _quick_set(self, minutes):
        self.interval_var.set(minutes)
        self.interval_label.config(text=self._interval_text(minutes))

    def _save(self):
        self.config.interval_minutes = self.interval_var.get()
        self.config.popup_duration = self.duration_var.get()
        self.config.sound_enabled = self.sound_var.get()
        if self.on_save:
            self.on_save()
        self.win.destroy()

    def _test_popup(self):
        """Fire a test popup so the user can preview the character."""
        if self.on_save:
            # Temporarily save so the popup uses current settings
            self.config.popup_duration = self.duration_var.get()
            self.on_save(test=True)

    def _center(self):
        self.win.update_idletasks()
        w = self.win.winfo_width()
        h = self.win.winfo_height()
        sw = self.win.winfo_screenwidth()
        sh = self.win.winfo_screenheight()
        self.win.geometry(f'+{(sw - w) // 2}+{(sh - h) // 2}')

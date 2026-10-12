"""
Desktop walking character window with interactive water reminder.

Flow:
1. Character walks in from the left side of the screen.
2. Stops and displays an animated speech bubble asking if you drank water,
   with interactive buttons:
     - [ 💧 Yes, drank! ]  (Positive)
     - [ 😢 Not yet ]      (Negative)
     - [ ⚙ ]               (Settings)
3. If Positive:
   - Celebrates with confetti, sunglasses glint, and happy jump!
   - Runs fast left-to-right happily off the screen with speed trails!
4. If Negative:
   - Droops sadly with a raincloud and falling water drips.
   - Turns around and walks back to the left sadly off-screen.
"""

import tkinter as tk
import math
import random
import os

try:
    import winsound
    HAS_SOUND = True
except ImportError:
    HAS_SOUND = False

from character_loader import SpriteManager


class WalkingCharacterWindow:
    """Animated desktop mascot that walks in, asks for water check, and responds."""

    TRANS_COLOR = '#FF00FF'
    WIN_W = 380
    WIN_H = 430
    FRAME_MS = 25  # ~40 FPS

    # Animation states
    STATE_WALK_IN = 0
    STATE_IDLE = 1
    STATE_POSITIVE_REACTION = 2
    STATE_RUN_AWAY = 3
    STATE_NEGATIVE_REACTION = 4
    STATE_WALK_BACK_SAD = 5
    STATE_DONE = 6

    def __init__(self, root, message=None, sound_enabled=True,
                 on_dismiss=None, on_settings=None):
        self.root = root
        self.custom_message = message
        self.sound_enabled = sound_enabled
        self.on_dismiss = on_dismiss
        self.on_settings = on_settings

        self.sprite_mgr = SpriteManager(root)

        # Coordinate setup
        self.win = tk.Toplevel(root)
        self.win.overrideredirect(True)
        self.win.attributes('-topmost', True)
        self.win.attributes('-transparentcolor', self.TRANS_COLOR)
        self.win.config(bg=self.TRANS_COLOR)

        self.sw = self.win.winfo_screenwidth()
        self.sh = self.win.winfo_screenheight()

        # Ground position (above taskbar)
        self.ground_y = self.sh - self.WIN_H - 45
        self.current_x = -float(self.WIN_W)
        self.target_stop_x = 85.0

        self.win.geometry(f'{self.WIN_W}x{self.WIN_H}+{int(self.current_x)}+{int(self.ground_y)}')

        # Canvas
        self.c = tk.Canvas(
            self.win, width=self.WIN_W, height=self.WIN_H,
            bg=self.TRANS_COLOR, highlightthickness=0)
        self.c.pack()

        # Character canvas anchors
        self.char_cx = 190
        self.char_cy = 280

        # Animation variables
        self.state = self.STATE_WALK_IN
        self.frame_count = 0
        self.walk_phase = 0.0
        self.run_phase = 0.0
        self.sad_phase = 0.0
        self.idle_phase = 0.0
        self.reaction_timer = 0

        # Speech & UI state
        self.bubble_visible = False
        self.text_full = ""
        self.text_displayed = ""
        self.text_char_idx = 0
        self.buttons_visible = False
        self.btn_pos_hover = False
        self.btn_neg_hover = False
        self.btn_set_hover = False

        # Visual elements
        self.particles = []
        self.footstep_particles = []
        self.current_char_image = None

        self._build_static_canvas()
        self._bind_events()
        self._tick()

    # ══════════════════════════════════════════════════════════════════
    #  Canvas Elements Setup
    # ══════════════════════════════════════════════════════════════════

    def _build_static_canvas(self):
        # 1. Ground Shadow
        self.shadow_item = self.c.create_oval(
            self.char_cx - 50, self.char_cy + 115,
            self.char_cx + 50, self.char_cy + 130,
            fill='#B0BEC5', outline='', tags='shadow')

        # 2. Character Sprite
        initial_frame = self.sprite_mgr.get_frame(facing_right=True, angle_deg=0)
        self.current_char_image = initial_frame
        self.char_item = self.c.create_image(
            self.char_cx, self.char_cy, image=self.current_char_image, tags='char')

        # 3. Glasses Glint (hidden initially)
        self.glint_items = []
        for gx, gy in [(self.char_cx - 20, self.char_cy - 92), (self.char_cx + 8, self.char_cy - 92)]:
            g1 = self.c.create_line(gx - 7, gy, gx + 7, gy, fill='#FFF9C4', width=2, state='hidden', tags='glint')
            g2 = self.c.create_line(gx, gy - 7, gx, gy + 7, fill='#FFF9C4', width=2, state='hidden', tags='glint')
            self.glint_items.extend([g1, g2])

        # 4. Floating Water Buddy (Idle companion)
        self.buddy_body = self.c.create_oval(
            0, 0, 1, 1, fill='#4FC3F7', outline='#0288D1', width=1.5, state='hidden', tags='buddy')
        self.buddy_tip = self.c.create_polygon(
            0, 0, 0, 0, 0, 0, fill='#4FC3F7', outline='', state='hidden', tags='buddy')
        self.buddy_eye1 = self.c.create_oval(0, 0, 1, 1, fill='#1A237E', outline='', state='hidden', tags='buddy')
        self.buddy_eye2 = self.c.create_oval(0, 0, 1, 1, fill='#1A237E', outline='', state='hidden', tags='buddy')
        self.buddy_smile = self.c.create_arc(0, 0, 1, 1, start=200, extent=140, style=tk.ARC,
                                            outline='#E91E63', width=1.5, state='hidden', tags='buddy')

        # 5. Speech Bubble
        self._build_bubble_ui()

    def _build_bubble_ui(self):
        # Bubble bounds
        self.bx1, self.by1 = 25, 12
        self.bx2, self.by2 = 355, 138
        r = 18

        # Shadow
        bubble_pts_shadow = self._rounded_rect(self.bx1 + 2, self.by1 + 3, self.bx2 + 2, self.by2 + 3, r)
        self.bubble_shadow = self.c.create_polygon(
            bubble_pts_shadow, fill='#CFD8DC', outline='', smooth=True, state='hidden', tags='bubble')

        # Bubble body
        bubble_pts = self._rounded_rect(self.bx1, self.by1, self.bx2, self.by2, r)
        self.bubble_body = self.c.create_polygon(
            bubble_pts, fill='#FFFFFF', outline='#0288D1', width=2.5, smooth=True, state='hidden', tags='bubble')

        # Pointer
        self.bubble_pointer = self.c.create_polygon(
            174, self.by2 - 2, 206, self.by2 - 2, 190, self.by2 + 22,
            fill='#FFFFFF', outline='#0288D1', width=2.5, state='hidden', tags='bubble')
        self.bubble_pointer_cover = self.c.create_line(
            173, self.by2 - 1, 207, self.by2 - 1, fill='#FFFFFF', width=6, state='hidden', tags='bubble')

        # Title/Text
        self.bubble_text = self.c.create_text(
            190, 48, text='', font=('Segoe UI', 11, 'bold'),
            fill='#1E293B', justify=tk.CENTER, state='hidden', tags='bubble')

        # Positive Button: [ 💧 Yes, drank! ]
        pos_pts = self._rounded_rect(42, 85, 185, 122, 12)
        self.btn_pos_body = self.c.create_polygon(
            pos_pts, fill='#0288D1', outline='#0277BD', width=1.5, smooth=True, state='hidden', tags='btn_pos')
        self.btn_pos_text = self.c.create_text(
            113, 103, text='💧 Yes, drank!', font=('Segoe UI', 10, 'bold'),
            fill='#FFFFFF', state='hidden', tags='btn_pos')

        # Negative Button: [ 😢 Not yet ]
        neg_pts = self._rounded_rect(195, 85, 338, 122, 12)
        self.btn_neg_body = self.c.create_polygon(
            neg_pts, fill='#FFF1F2', outline='#FDA4AF', width=1.5, smooth=True, state='hidden', tags='btn_neg')
        self.btn_neg_text = self.c.create_text(
            266, 103, text='😢 Not yet', font=('Segoe UI', 10, 'bold'),
            fill='#BE123C', state='hidden', tags='btn_neg')

        # Settings Button: [ ⚙ ]
        self.btn_set_body = self.c.create_oval(
            326, 18, 348, 40, fill='#F1F5F9', outline='#CBD5E1', width=1, state='hidden', tags='btn_set')
        self.btn_set_text = self.c.create_text(
            337, 29, text='⚙', font=('Segoe UI', 9), fill='#64748B', state='hidden', tags='btn_set')

    # ══════════════════════════════════════════════════════════════════
    #  Event Handlers
    # ══════════════════════════════════════════════════════════════════

    def _bind_events(self):
        # Click on character: counts as positive response!
        self.c.tag_bind('char', '<Button-1>', lambda _: self._on_positive_clicked())

        # Positive button click & hover
        self.c.tag_bind('btn_pos', '<Button-1>', lambda _: self._on_positive_clicked())
        self.c.tag_bind('btn_pos', '<Enter>', lambda _: self._hover_btn('pos', True))
        self.c.tag_bind('btn_pos', '<Leave>', lambda _: self._hover_btn('pos', False))

        # Negative button click & hover
        self.c.tag_bind('btn_neg', '<Button-1>', lambda _: self._on_negative_clicked())
        self.c.tag_bind('btn_neg', '<Enter>', lambda _: self._hover_btn('neg', True))
        self.c.tag_bind('btn_neg', '<Leave>', lambda _: self._hover_btn('neg', False))

        # Settings button click & hover
        self.c.tag_bind('btn_set', '<Button-1>', lambda _: self._on_settings_clicked())
        self.c.tag_bind('btn_set', '<Enter>', lambda _: self._hover_btn('set', True))
        self.c.tag_bind('btn_set', '<Leave>', lambda _: self._hover_btn('set', False))

    def _hover_btn(self, btn, is_hover):
        if not self.buttons_visible:
            return
        if btn == 'pos':
            self.c.itemconfigure(self.btn_pos_body, fill='#039BE5' if is_hover else '#0288D1')
            self.win.config(cursor='hand2' if is_hover else '')
        elif btn == 'neg':
            self.c.itemconfigure(self.btn_neg_body, fill='#FFE4E6' if is_hover else '#FFF1F2')
            self.win.config(cursor='hand2' if is_hover else '')
        elif btn == 'set':
            self.c.itemconfigure(self.btn_set_body, fill='#E2E8F0' if is_hover else '#F1F5F9')
            self.win.config(cursor='hand2' if is_hover else '')

    def _on_positive_clicked(self):
        if self.state not in (self.STATE_IDLE, self.STATE_WALK_IN):
            return
        self._hide_buttons()
        self.state = self.STATE_POSITIVE_REACTION
        self.reaction_timer = 0
        if self.sound_enabled and HAS_SOUND:
            try:
                winsound.PlaySound('SystemAsterisk', winsound.SND_ALIAS | winsound.SND_ASYNC)
            except Exception:
                pass
        self._set_bubble_text("WOOHOO! 🎉 Awesome job!\nStay hydrated, superstar! 💧✨")
        self._spawn_celebration_confetti()

    def _on_negative_clicked(self):
        if self.state not in (self.STATE_IDLE, self.STATE_WALK_IN):
            return
        self._hide_buttons()
        self.state = self.STATE_NEGATIVE_REACTION
        self.reaction_timer = 0
        if self.sound_enabled and HAS_SOUND:
            try:
                winsound.PlaySound('SystemHand', winsound.SND_ALIAS | winsound.SND_ASYNC)
            except Exception:
                pass
        self._set_bubble_text("Aww... 🥺 Please go grab\na glass of water now, okay? 💔")
        self._spawn_sad_cloud()

    def _on_settings_clicked(self):
        if self.on_settings:
            self.on_settings()

    # ══════════════════════════════════════════════════════════════════
    #  Main Animation Tick
    # ══════════════════════════════════════════════════════════════════

    def _tick(self):
        if self.state == self.STATE_DONE:
            return

        self.frame_count += 1

        # ── State Machine Dispatch ──
        if self.state == self.STATE_WALK_IN:
            self._tick_walk_in()
        elif self.state == self.STATE_IDLE:
            self._tick_idle()
        elif self.state == self.STATE_POSITIVE_REACTION:
            self._tick_positive_reaction()
        elif self.state == self.STATE_RUN_AWAY:
            self._tick_run_away()
        elif self.state == self.STATE_NEGATIVE_REACTION:
            self._tick_negative_reaction()
        elif self.state == self.STATE_WALK_BACK_SAD:
            self._tick_walk_back_sad()

        # Update dynamic particle physics
        self._update_particles()

        # Update typewriter text
        self._tick_typewriter()

        # Schedule next frame
        if self.state != self.STATE_DONE:
            try:
                self.win.after(self.FRAME_MS, self._tick)
            except tk.TclError:
                pass

    # ── STATE 0: WALK IN FROM LEFT ───────────────────────────────────

    def _tick_walk_in(self):
        self.walk_phase += 0.22
        walk_speed = 5.5
        self.current_x += walk_speed

        # Sinusoidal stride bob & sway tilt
        bob_y = abs(math.sin(self.walk_phase)) * 8.5
        sway_angle = math.sin(self.walk_phase) * 3.5

        # Footstep dust/ripple effect at step bottom
        if bob_y < 1.2 and random.random() < 0.4:
            self._add_footstep_ripple()

        # Update window geometry
        current_y = self.ground_y - bob_y
        self._move_window(self.current_x, current_y)

        # Update character frame
        frame = self.sprite_mgr.get_frame(facing_right=True, angle_deg=sway_angle)
        self._set_char_sprite(frame)

        # Shadow scales with bob
        shadow_w = 48 + bob_y * 1.5
        self.c.coords(self.shadow_item,
                      self.char_cx - shadow_w, self.char_cy + 115,
                      self.char_cx + shadow_w, self.char_cy + 130)

        # Arrived at destination?
        if self.current_x >= self.target_stop_x:
            self.current_x = self.target_stop_x
            self._move_window(self.current_x, self.ground_y)
            self.state = self.STATE_IDLE
            self._show_bubble_and_buttons()

    # ── STATE 1: IDLE WAITING FOR RESPONSE ───────────────────────────

    def _tick_idle(self):
        self.idle_phase += 0.08

        # Gentle breathing bob
        bob_y = math.sin(self.idle_phase) * 3.0
        frame = self.sprite_mgr.get_frame(facing_right=True, angle_deg=0.0)
        self._set_char_sprite(frame)

        # Move character on canvas slightly for breathing
        self.c.coords(self.char_item, self.char_cx, self.char_cy + bob_y)

        # Water droplet buddy floats & bobs near his shoulder
        self._update_buddy(bob_y)

        # Sparkles occasionally
        if self.frame_count % 18 == 0:
            self._add_sparkle()

        # Auto-dismiss timeout: if no interaction for 60 seconds, gently walk away
        if self.frame_count > 60 * 40:
            self._on_positive_clicked()

    def _update_buddy(self, char_bob):
        bx = self.char_cx + 80
        by = self.char_cy - 70 + math.sin(self.idle_phase * 1.4) * 6.0
        r = 13

        # Make buddy visible
        for item in (self.buddy_body, self.buddy_tip, self.buddy_eye1, self.buddy_eye2, self.buddy_smile):
            self.c.itemconfigure(item, state='normal')

        self.c.coords(self.buddy_body, bx - r, by - r + 3, bx + r, by + r + 3)
        self.c.coords(self.buddy_tip, bx, by - r - 8, bx - r + 2, by - 3, bx + r - 2, by - 3)
        self.c.coords(self.buddy_eye1, bx - 6, by - 2, bx - 2, by + 2)
        self.c.coords(self.buddy_eye2, bx + 2, by - 2, bx + 6, by + 2)
        self.c.coords(self.buddy_smile, bx - 5, by + 1, bx + 5, by + 8)

    def _hide_buddy(self):
        for item in (self.buddy_body, self.buddy_tip, self.buddy_eye1, self.buddy_eye2, self.buddy_smile):
            self.c.itemconfigure(item, state='hidden')

    # ── STATE 2: POSITIVE CELEBRATION REACTION ───────────────────────

    def _tick_positive_reaction(self):
        self.reaction_timer += 1
        self._hide_buddy()

        # Celebration jump!
        t = self.reaction_timer / 26.0
        jump_y = -math.sin(t * math.pi) * 28.0

        # Sunglasses glint
        for g in self.glint_items:
            self.c.itemconfigure(g, state='normal')
            self.c.move(g, 0, jump_y if self.reaction_timer == 1 else 0)

        # Excited slight rocking
        angle = math.sin(self.reaction_timer * 0.4) * 5.0
        frame = self.sprite_mgr.get_frame(facing_right=True, angle_deg=angle)
        self._set_char_sprite(frame)

        self.c.coords(self.char_item, self.char_cx, self.char_cy + jump_y)

        # Transition to run away
        if self.reaction_timer >= 26:
            for g in self.glint_items:
                self.c.itemconfigure(g, state='hidden')
            self.state = self.STATE_RUN_AWAY
            self.run_phase = 0.0

    # ── STATE 3: RUN AWAY HAPPILY LEFT TO RIGHT ──────────────────────

    def _tick_run_away(self):
        self.run_phase += 0.42
        run_speed = 16.5
        self.current_x += run_speed

        # Running bounce and energetic forward lean!
        bob_y = abs(math.sin(self.run_phase)) * 14.0
        lean_angle = -11.0  # forward sprint lean

        frame = self.sprite_mgr.get_frame(facing_right=True, angle_deg=lean_angle)
        self._set_char_sprite(frame)

        current_y = self.ground_y - bob_y
        self._move_window(self.current_x, current_y)

        # Running speed lines & dust puffs behind feet
        if self.frame_count % 2 == 0:
            self._add_speed_puff()

        # Off-screen right check
        if self.current_x > self.sw + 60:
            self._finish_and_close()

    # ── STATE 4: NEGATIVE SAD REACTION ───────────────────────────────

    def _tick_negative_reaction(self):
        self.reaction_timer += 1
        self._hide_buddy()

        # Droop down sadly
        t = min(1.0, self.reaction_timer / 20.0)
        droop_y = t * 8.0

        # Sad slouch frame
        frame = self.sprite_mgr.get_frame(facing_right=True, angle_deg=2.0, is_sad=True)
        self._set_char_sprite(frame)
        self.c.coords(self.char_item, self.char_cx, self.char_cy + droop_y)

        # Spawn raindrops from sad cloud
        if self.reaction_timer % 4 == 0:
            self._add_sad_rain_drop()

        if self.reaction_timer >= 32:
            self.state = self.STATE_WALK_BACK_SAD
            self.sad_phase = 0.0

    # ── STATE 5: WALK BACK SADLY TO LEFT ─────────────────────────────

    def _tick_walk_back_sad(self):
        self.sad_phase += 0.14
        sad_speed = 3.6
        self.current_x -= sad_speed

        # Heavy, slow, dejected footsteps
        bob_y = abs(math.sin(self.sad_phase)) * 5.0
        slump_angle = 3.5  # head down forward tilt facing left

        # Left-facing sad frame
        frame = self.sprite_mgr.get_frame(facing_right=False, angle_deg=slump_angle, is_sad=True)
        self._set_char_sprite(frame)

        current_y = self.ground_y - bob_y
        self._move_window(self.current_x, current_y)

        # Occasional teardrop
        if self.frame_count % 8 == 0:
            self._add_sad_rain_drop()

        # Off-screen left check
        if self.current_x < -float(self.WIN_W) - 40:
            self._finish_and_close()

    # ══════════════════════════════════════════════════════════════════
    #  UI & Speech Bubble Controls
    # ══════════════════════════════════════════════════════════════════

    def _show_bubble_and_buttons(self):
        self.bubble_visible = True

        # Show bubble elements
        for item in (self.bubble_shadow, self.bubble_body,
                     self.bubble_pointer, self.bubble_pointer_cover,
                     self.bubble_text, self.btn_set_body, self.btn_set_text):
            self.c.itemconfigure(item, state='normal')

        msg = self.custom_message or "Hey! Time for a water break! 💧\nDid you drink a glass of water?"
        self._set_bubble_text(msg)

        # Show buttons
        self.buttons_visible = True
        for item in (self.btn_pos_body, self.btn_pos_text,
                     self.btn_neg_body, self.btn_neg_text):
            self.c.itemconfigure(item, state='normal')

        if self.sound_enabled and HAS_SOUND:
            try:
                winsound.PlaySound('SystemExclamation', winsound.SND_ALIAS | winsound.SND_ASYNC)
            except Exception:
                pass

    def _hide_buttons(self):
        self.buttons_visible = False
        for item in (self.btn_pos_body, self.btn_pos_text,
                     self.btn_neg_body, self.btn_neg_text,
                     self.btn_set_body, self.btn_set_text):
            self.c.itemconfigure(item, state='hidden')
        self.win.config(cursor='')

    def _set_bubble_text(self, text):
        self.text_full = text
        self.text_char_idx = 0
        self.text_displayed = ""
        self.c.itemconfigure(self.bubble_text, text="")

    def _tick_typewriter(self):
        if self.text_char_idx < len(self.text_full):
            self.text_char_idx += 2  # 2 characters per tick for snappy feel
            self.text_displayed = self.text_full[:self.text_char_idx]
            self.c.itemconfigure(self.bubble_text, text=self.text_displayed)

    # ══════════════════════════════════════════════════════════════════
    #  Particles & Visual Effects
    # ══════════════════════════════════════════════════════════════════

    def _spawn_celebration_confetti(self):
        colors = ['#FFD54F', '#4FC3F7', '#81C784', '#FF8A80', '#BA68C8', '#4DD0E1']
        for _ in range(24):
            x = self.char_cx + random.randint(-40, 40)
            y = self.char_cy - 40 + random.randint(-30, 20)
            vx = random.uniform(-6.0, 6.0)
            vy = random.uniform(-9.0, -2.0)
            size = random.randint(3, 7)
            clr = random.choice(colors)
            shape = random.choice(['oval', 'rect', 'star'])
            if shape == 'oval':
                item = self.c.create_oval(x - size, y - size, x + size, y + size, fill=clr, outline='')
            else:
                item = self.c.create_rectangle(x - size, y - size, x + size, y + size, fill=clr, outline='')
            self.particles.append({'item': item, 'x': x, 'y': y, 'vx': vx, 'vy': vy, 'life': 45})

    def _spawn_sad_cloud(self):
        # Draw small dark cloud above head
        cx = self.char_cx
        cy = self.char_cy - 125
        cloud1 = self.c.create_oval(cx - 30, cy - 10, cx + 10, cy + 18, fill='#90A4AE', outline='')
        cloud2 = self.c.create_oval(cx - 10, cy - 18, cx + 32, cy + 14, fill='#78909C', outline='')
        cloud3 = self.c.create_oval(cx - 20, cy - 6, cx + 25, cy + 20, fill='#B0BEC5', outline='')
        self.particles.extend([
            {'item': cloud1, 'x': cx, 'y': cy, 'vx': 0, 'vy': 0, 'life': 300},
            {'item': cloud2, 'x': cx, 'y': cy, 'vx': 0, 'vy': 0, 'life': 300},
            {'item': cloud3, 'x': cx, 'y': cy, 'vx': 0, 'vy': 0, 'life': 300},
        ])

    def _add_sad_rain_drop(self):
        x = self.char_cx + random.randint(-22, 22)
        y = self.char_cy - 105
        item = self.c.create_line(x, y, x - 1, y + 8, fill='#29B6F6', width=2)
        self.particles.append({'item': item, 'x': x, 'y': y, 'vx': -0.3, 'vy': 5.0, 'life': 22})

    def _add_speed_puff(self):
        # Smoke/wind puff behind running character
        x = self.char_cx - 70 + random.randint(-10, 10)
        y = self.char_cy + 85 + random.randint(-8, 8)
        size = random.randint(4, 9)
        item = self.c.create_oval(x - size, y - size, x + size, y + size,
                                  fill='#E0F7FA', outline='#B2EBF2', width=1)
        self.particles.append({'item': item, 'x': x, 'y': y, 'vx': -5.0, 'vy': -0.5, 'life': 14})

    def _add_footstep_ripple(self):
        x = self.char_cx + random.randint(-15, 15)
        y = self.char_cy + 120
        item = self.c.create_oval(x - 6, y - 2, x + 6, y + 2, outline='#81D4FA', width=1.5)
        self.particles.append({'item': item, 'x': x, 'y': y, 'vx': 0, 'vy': 0, 'life': 10, 'grow': True})

    def _add_sparkle(self):
        x = self.char_cx + random.randint(-60, 60)
        y = self.char_cy + random.randint(-80, 40)
        sz = random.randint(3, 6)
        color = random.choice(['#FFD54F', '#81D4FA', '#FFFFFF'])
        s1 = self.c.create_line(x - sz, y, x + sz, y, fill=color, width=1.5)
        s2 = self.c.create_line(x, y - sz, x, y + sz, fill=color, width=1.5)
        self.win.after(350, lambda: [self.c.delete(i) for i in (s1, s2)])

    def _update_particles(self):
        alive = []
        for p in self.particles:
            p['life'] -= 1
            if p['life'] <= 0:
                try:
                    self.c.delete(p['item'])
                except tk.TclError:
                    pass
                continue

            p['x'] += p.get('vx', 0)
            p['y'] += p.get('vy', 0)
            p['vy'] = p.get('vy', 0) + 0.25  # gravity

            try:
                if p.get('grow'):
                    r = (10 - p['life']) * 1.5
                    self.c.coords(p['item'], p['x'] - r, p['y'] - r * 0.4, p['x'] + r, p['y'] + r * 0.4)
                else:
                    self.c.move(p['item'], p.get('vx', 0), p.get('vy', 0))
                alive.append(p)
            except tk.TclError:
                pass
        self.particles = alive

    # ══════════════════════════════════════════════════════════════════
    #  Window & Helpers
    # ══════════════════════════════════════════════════════════════════

    def _move_window(self, x, y):
        try:
            self.win.geometry(f'+{int(x)}+{int(y)}')
        except tk.TclError:
            pass

    def _set_char_sprite(self, frame):
        self.current_char_image = frame
        self.c.itemconfigure(self.char_item, image=self.current_char_image)

    def _finish_and_close(self):
        self.state = self.STATE_DONE
        try:
            self.win.destroy()
        except tk.TclError:
            pass
        if self.on_dismiss:
            self.on_dismiss()

    @staticmethod
    def _rounded_rect(x1, y1, x2, y2, r):
        pts = []
        for arc_cx, arc_cy, start, end in [
            (x1 + r, y1 + r, 90, 180),
            (x1 + r, y2 - r, 180, 270),
            (x2 - r, y2 - r, 270, 360),
            (x2 - r, y1 + r, 0, 90),
        ]:
            for deg in range(start, end + 1, 9):
                a = math.radians(deg)
                pts += [arc_cx + r * math.cos(a), arc_cy + r * math.sin(a)]
        return pts

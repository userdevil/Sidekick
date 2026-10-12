"""
Video Character Player for Sidekick.

Supports playing animated video clips for character actions:
  - walk.mp4 / walk.gif   -> Played while walking onto the screen
  - happy.mp4 / happy.gif -> Played when user responds positively (celebration & run)
  - sad.mp4 / sad.gif     -> Played when user responds negatively (sad walk-back)
  - character.mp4 / .gif  -> Universal fallback if a single video is provided

Features:
  - Real-time chroma-key background removal (green screen / solid background)
  - Alpha transparency composited onto Tkinter transparent color (#FF00FF)
  - Automatic circular portal framing option for regular room-background videos
  - High-performance frame preloading and caching for 60 FPS playback
  - Seamless fallback to static cutout sprites if no video files are present
"""

import os
import math
from PIL import Image, ImageTk

try:
    import cv2
    import numpy as np
    HAS_OPENCV = True
except ImportError:
    HAS_OPENCV = False

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TARGET_HEIGHT = 250


class VideoCharacterManager:
    """Manages video playback and frame extraction for desktop character animations."""

    ACTION_WALK = 'walk'
    ACTION_HAPPY = 'happy'
    ACTION_SAD = 'sad'
    ACTION_IDLE = 'idle'

    # Supported video extensions
    VIDEO_EXTENSIONS = ('.mp4', '.avi', '.mov', '.webm', '.gif', '.mkv')

    def __init__(self, master_tk, chroma_key_color='green', use_portal_mask=False):
        self.master = master_tk
        self.chroma_key_color = chroma_key_color
        self.use_portal_mask = use_portal_mask

        # Cached frames: dict of {action: list of ImageTk.PhotoImage}
        self.frames_right = {}
        self.frames_left = {}

        # Scan and load any available videos
        self._load_available_videos()

    def has_video_support(self):
        """Return True if any action video is loaded and ready."""
        return any(len(frames) > 0 for frames in self.frames_right.values())

    def has_action(self, action):
        """Check if a specific action video is loaded."""
        return action in self.frames_right and len(self.frames_right[action]) > 0

    def get_frame(self, action, frame_index, facing_right=True):
        """
        Retrieve the appropriate PhotoImage frame for the given action and tick.
        Loops automatically through the video's frames.
        """
        # Fallback to universal action if specific action is missing
        if action not in self.frames_right or len(self.frames_right[action]) == 0:
            if 'universal' in self.frames_right and len(self.frames_right['universal']) > 0:
                action = 'universal'
            else:
                return None

        frames = self.frames_right[action] if facing_right else self.frames_left[action]
        if not frames:
            return None

        idx = frame_index % len(frames)
        return frames[idx]

    def get_frame_count(self, action):
        """Return number of frames available for an action."""
        if action in self.frames_right:
            return len(self.frames_right[action])
        if 'universal' in self.frames_right:
            return len(self.frames_right['universal'])
        return 0

    # ══════════════════════════════════════════════════════════════════
    #  Video Detection & Loading
    # ══════════════════════════════════════════════════════════════════

    def _load_available_videos(self):
        """Search the project directory for video action clips."""
        action_files = {
            self.ACTION_WALK: self._find_video_file(['walk', 'walking', 'walk_cycle']),
            self.ACTION_HAPPY: self._find_video_file(['happy', 'run', 'running', 'celebrate', 'cheer']),
            self.ACTION_SAD: self._find_video_file(['sad', 'walk_back', 'disappointed', 'cry']),
            'universal': self._find_video_file(['character', 'video', 'avatar', 'mascot']),
        }

        for action, file_path in action_files.items():
            if file_path:
                print(f"[Sidekick] Found video for '{action}': {os.path.basename(file_path)}")
                self._load_video_clip(action, file_path)

    def _find_video_file(self, base_names):
        """Check if any matching video file exists in the directory."""
        for name in base_names:
            for ext in self.VIDEO_EXTENSIONS:
                path = os.path.join(BASE_DIR, f"{name}{ext}")
                if os.path.isfile(path):
                    return path
        return None

    def _load_video_clip(self, action, video_path):
        """Extract and process all frames from a video file into Tkinter PhotoImages."""
        raw_pil_frames = []

        if video_path.lower().endswith('.gif'):
            raw_pil_frames = self._extract_gif_frames(video_path)
        elif HAS_OPENCV:
            raw_pil_frames = self._extract_opencv_frames(video_path)

        if not raw_pil_frames:
            return

        right_list = []
        left_list = []

        for pil_img in raw_pil_frames:
            # Process transparency / chroma-key
            processed = self._apply_transparency(pil_img)

            # Resize to display height
            tw = int(processed.width * (TARGET_HEIGHT / processed.height))
            resized_r = processed.resize((tw, TARGET_HEIGHT), Image.Resampling.LANCZOS)
            resized_l = resized_r.transpose(Image.FLIP_LEFT_RIGHT)

            # Composite onto magenta (#FF00FF)
            tk_r = self._composite_to_tk(resized_r)
            tk_l = self._composite_to_tk(resized_l)

            right_list.append(tk_r)
            left_list.append(tk_l)

        self.frames_right[action] = right_list
        self.frames_left[action] = left_list
        print(f"[Sidekick] Loaded {len(right_list)} frames for '{action}'.")

    # ══════════════════════════════════════════════════════════════════
    #  Frame Extraction
    # ══════════════════════════════════════════════════════════════════

    def _extract_opencv_frames(self, path):
        """Extract frames using OpenCV VideoCapture."""
        cap = cv2.VideoCapture(path)
        frames = []
        max_frames = 120  # Limit to 120 frames (~4-5s loop) to conserve memory

        while cap.isOpened() and len(frames) < max_frames:
            ret, bgr_frame = cap.read()
            if not ret or bgr_frame is None:
                break
            # Convert BGR to RGB
            rgb = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(rgb)
            frames.append(pil_img)

        cap.release()
        return frames

    def _extract_gif_frames(self, path):
        """Extract frames from an animated GIF."""
        from PIL import ImageSequence
        gif = Image.open(path)
        frames = []
        for frame in ImageSequence.Iterator(gif):
            frames.append(frame.convert('RGBA'))
            if len(frames) >= 120:
                break
        return frames

    # ══════════════════════════════════════════════════════════════════
    #  Chroma-Key & Transparency Processing
    # ══════════════════════════════════════════════════════════════════

    def _apply_transparency(self, pil_img):
        """Apply green-screen chroma key or circular mask if needed."""
        # If image already has clean alpha (e.g. transparent GIF/PNG)
        if pil_img.mode == 'RGBA':
            return pil_img

        pil_img = pil_img.convert('RGB')

        if not HAS_OPENCV:
            return pil_img.convert('RGBA')

        np_img = np.array(pil_img)

        # 1. Chroma-key background removal (Green Screen)
        if self.chroma_key_color == 'green':
            hsv = cv2.cvtColor(np_img, cv2.COLOR_RGB2HSV)
            # Standard green screen HSV range
            lower_green = np.array([35, 45, 45])
            upper_green = np.array([85, 255, 255])
            mask = cv2.inRange(hsv, lower_green, upper_green)

            # Invert mask: character is 255, background is 0
            char_mask = cv2.bitwise_not(mask)

            # Clean edges with morphological smoothing
            kernel = np.ones((3, 3), np.uint8)
            char_mask = cv2.morphologyEx(char_mask, cv2.MORPH_OPEN, kernel)
            char_mask = cv2.morphologyEx(char_mask, cv2.MORPH_CLOSE, kernel)

            # Assemble RGBA
            rgba = cv2.cvtColor(np_img, cv2.COLOR_RGB2RGBA)
            rgba[:, :, 3] = char_mask
            return Image.fromarray(rgba)

        # 2. Circular portal mask (for videos with standard backgrounds)
        if self.use_portal_mask:
            w, h = pil_img.size
            side = min(w, h)
            left = (w - side) // 2
            top = (h - side) // 2
            cropped = pil_img.crop((left, top, left + side, top + side))

            mask = Image.new('L', (side, side), 0)
            from PIL import ImageDraw
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0, side - 1, side - 1), fill=255)

            rgba = cropped.convert('RGBA')
            rgba.putalpha(mask)
            return rgba

        return pil_img.convert('RGBA')

    def _composite_to_tk(self, rgba_img):
        """Composite RGBA onto transparent magenta (#FF00FF) with clean binary mask."""
        alpha = rgba_img.split()[3].point(lambda p: 255 if p > 80 else 0)
        bg = Image.new('RGB', rgba_img.size, (255, 0, 255))
        bg.paste(rgba_img, (0, 0), alpha)
        return ImageTk.PhotoImage(bg)

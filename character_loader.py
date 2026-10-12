"""
Character loader and sprite frame cache.
Extracts the cutout from the photo if needed and caches rotated/transformed frames.
"""

import os
import math
from PIL import Image, ImageOps, ImageTk

# Base directory for assets
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PHOTO_PATH = os.path.join(BASE_DIR, 'IMG_20250407_112242293_MF_PORTRAIT.jpg')
SPRITE_RIGHT = os.path.join(BASE_DIR, 'character_right.png')
SPRITE_LEFT = os.path.join(BASE_DIR, 'character_left.png')

# Display dimensions
TARGET_HEIGHT = 250


def ensure_character_sprites():
    """Ensure clean cutout sprites exist for right and left facing."""
    if os.path.isfile(SPRITE_RIGHT) and os.path.isfile(SPRITE_LEFT):
        return

    # If photo exists, extract cutout
    if os.path.isfile(PHOTO_PATH):
        try:
            import cv2
            import numpy as np

            pil_img = Image.open(PHOTO_PATH)
            pil_img = ImageOps.exif_transpose(pil_img)
            h = 600
            w = int(pil_img.width * (h / pil_img.height))
            pil_img = pil_img.resize((w, h), Image.Resampling.LANCZOS)
            img_np = np.array(pil_img)
            img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)

            mask = np.zeros(img_bgr.shape[:2], np.uint8)
            bgdModel = np.zeros((1, 65), np.float64)
            fgdModel = np.zeros((1, 65), np.float64)
            rect = (int(w * 0.05), int(h * 0.02), int(w * 0.9), int(h * 0.97))
            cv2.grabCut(img_bgr, mask, rect, bgdModel, fgdModel, 4, cv2.GC_INIT_WITH_RECT)
            mask2 = np.where((mask == 2) | (mask == 0), 0, 1).astype('uint8')
            kernel = np.ones((3, 3), np.uint8)
            mask2 = cv2.morphologyEx(mask2, cv2.MORPH_CLOSE, kernel)

            # Crop
            y_indices, x_indices = np.where(mask2 > 0)
            if len(y_indices) > 0 and len(x_indices) > 0:
                ymin, ymax = y_indices.min(), y_indices.max()
                xmin, xmax = x_indices.min(), x_indices.max()
                img_bgr = img_bgr[ymin:ymax + 1, xmin:xmax + 1]
                mask2 = mask2[ymin:ymax + 1, xmin:xmax + 1]

            rgba = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2BGRA)
            rgba[:, :, 3] = mask2 * 255

            # Save clean sprites
            clean_pil = Image.fromarray(cv2.cvtColor(rgba, cv2.COLOR_BGRA2RGBA))
            clean_pil.save(SPRITE_RIGHT)
            clean_pil.transpose(Image.FLIP_LEFT_RIGHT).save(SPRITE_LEFT)
            return
        except Exception as e:
            print("Error generating cutout:", e)

    # Fallback placeholder if no photo
    if not os.path.isfile(SPRITE_RIGHT):
        fallback = Image.new('RGBA', (130, 250), (66, 165, 245, 255))
        fallback.save(SPRITE_RIGHT)
        fallback.save(SPRITE_LEFT)


class SpriteManager:
    """Loads and caches transformed Tkinter-compatible character frames."""

    def __init__(self, master_tk):
        self.master = master_tk
        ensure_character_sprites()

        # Load base right-facing sprite
        raw_r = Image.open(SPRITE_RIGHT).convert('RGBA')
        tw = int(raw_r.width * (TARGET_HEIGHT / raw_r.height))
        self.base_right = raw_r.resize((tw, TARGET_HEIGHT), Image.Resampling.LANCZOS)
        self.base_left = self.base_right.transpose(Image.FLIP_LEFT_RIGHT)
        self.width = tw
        self.height = TARGET_HEIGHT

        self.cache = {}

    def get_frame(self, facing_right=True, angle_deg=0.0, scale_y=1.0, is_sad=False):
        """
        Returns a cached ImageTk.PhotoImage composited onto magenta (#FF00FF).
        """
        key = (facing_right, int(round(angle_deg)), round(scale_y, 2), is_sad)
        if key in self.cache:
            return self.cache[key]

        img = self.base_right if facing_right else self.base_left
        img = img.copy()

        # Sad effect: slight tint towards cool blue
        if is_sad:
            r, g, b, a = img.split()
            r = r.point(lambda p: int(p * 0.75))
            b = b.point(lambda p: min(255, int(p * 1.15)))
            img = Image.merge('RGBA', (r, g, b, a))

        # Vertical squash & stretch
        if scale_y != 1.0:
            sh = max(10, int(self.height * scale_y))
            sw = max(10, int(self.width * (1.0 + (1.0 - scale_y) * 0.4)))
            img = img.resize((sw, sh), Image.Resampling.BILINEAR)

        # Rotation
        if int(round(angle_deg)) != 0:
            img = img.rotate(angle_deg, resample=Image.Resampling.BILINEAR, expand=True)

        # Composite cleanly onto transparent color (#FF00FF)
        alpha = img.split()[3].point(lambda p: 255 if p > 90 else 0)
        bg = Image.new('RGB', img.size, (255, 0, 255))
        bg.paste(img, (0, 0), alpha)

        tk_img = ImageTk.PhotoImage(bg)
        self.cache[key] = tk_img
        return tk_img

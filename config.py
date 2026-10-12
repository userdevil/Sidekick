"""Configuration management for Water Reminder app."""

import json
import os
import random

CONFIG_DIR = os.path.join(os.path.expanduser('~'), '.sidekick')
CONFIG_FILE = os.path.join(CONFIG_DIR, 'config.json')

WATER_MESSAGES = [
    "Hey! Time for a water break! 💧\nDid you drink a glass of water?",
    "Hydration check! 🥤\nDid you drink some water recently?",
    "Stay refreshed, superstar! 🌟\nHave you had a glass of water?",
    "Your cells need fuel! 💧\nDid you take a water break?",
    "Friendly reminder from your buddy! 💦\nDid you drink water?",
    "Sip sip hooray! 🎉\nDid you drink a glass of water?",
    "Keep that energy up! ⚡\nHave you had fresh water today?",
]

DEFAULT_CONFIG = {
    'interval_minutes': 30,
    'popup_duration_seconds': 15,
    'sound_enabled': True,
}


class Config:
    """Manages app configuration with JSON file persistence."""

    def __init__(self):
        os.makedirs(CONFIG_DIR, exist_ok=True)
        self.data = self._load()

    def _load(self):
        try:
            with open(CONFIG_FILE, 'r') as f:
                data = json.load(f)
                for key, val in DEFAULT_CONFIG.items():
                    data.setdefault(key, val)
                return data
        except (FileNotFoundError, json.JSONDecodeError):
            return DEFAULT_CONFIG.copy()

    def save(self):
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.data, f, indent=2)

    @property
    def interval_minutes(self):
        return self.data['interval_minutes']

    @interval_minutes.setter
    def interval_minutes(self, value):
        self.data['interval_minutes'] = max(1, int(value))
        self.save()

    @property
    def popup_duration(self):
        return self.data['popup_duration_seconds']

    @popup_duration.setter
    def popup_duration(self, value):
        self.data['popup_duration_seconds'] = max(5, int(value))
        self.save()

    @property
    def sound_enabled(self):
        return self.data['sound_enabled']

    @sound_enabled.setter
    def sound_enabled(self, value):
        self.data['sound_enabled'] = bool(value)
        self.save()

    def get_random_message(self):
        return random.choice(WATER_MESSAGES)

const fs = require('fs');
const path = require('path');
const os = require('os');

const CONFIG_DIR = path.join(os.homedir(), '.sidekick');
const CONFIG_FILE = path.join(CONFIG_DIR, 'config.json');

const DEFAULT_CONFIG = {
  interval_minutes: 30,
  popup_duration_seconds: 15,
  sound_enabled: true,
};

const WATER_MESSAGES = [
  "Hey! Time for a water break! 💧\nDid you drink a glass of water?",
  "Hydration check! 🥤\nDid you drink some water recently?",
  "Stay refreshed, superstar! 🌟\nHave you had a glass of water?",
  "Your cells need fuel! 💧\nDid you take a water break?",
  "Friendly reminder from your buddy! 💦\nDid you drink water?",
  "Sip sip hooray! 🎉\nDid you drink a glass of water?",
  "Keep that energy up! ⚡\nHave you had fresh water today?",
];

class ConfigManager {
  constructor() {
    this.config = this.load();
  }

  load() {
    try {
      if (fs.existsSync(CONFIG_FILE)) {
        const raw = fs.readFileSync(CONFIG_FILE, 'utf8');
        const data = JSON.parse(raw);
        return { ...DEFAULT_CONFIG, ...data };
      }
    } catch (e) {
      console.error('[ConfigManager] Error reading config file:', e);
    }
    return { ...DEFAULT_CONFIG };
  }

  save(newConfig) {
    try {
      if (!fs.existsSync(CONFIG_DIR)) {
        fs.mkdirSync(CONFIG_DIR, { recursive: true });
      }
      this.config = { ...this.config, ...newConfig };
      fs.writeFileSync(CONFIG_FILE, JSON.stringify(this.config, null, 2), 'utf8');
      return true;
    } catch (e) {
      console.error('[ConfigManager] Error writing config file:', e);
      return false;
    }
  }

  getRandomMessage() {
    const idx = Math.floor(Math.random() * WATER_MESSAGES.length);
    return WATER_MESSAGES[idx];
  }
}

module.exports = new ConfigManager();

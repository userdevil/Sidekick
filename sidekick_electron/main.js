const { app, BrowserWindow, Tray, Menu, ipcMain, screen } = require('electron');
const path = require('path');
const configManager = require('./config');

let mainWindow = null;
let settingsWindow = null;
let tray = null;
let reminderTimer = null;

const WIN_W = 380;
const WIN_H = 430;

function createMainWindow() {
  mainWindow = new BrowserWindow({
    width: WIN_W,
    height: WIN_H,
    transparent: true,
    frame: false,
    alwaysOnTop: true,
    skipTaskbar: true,
    resizable: false,
    hasShadow: false,
    show: false,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
    },
  });

  mainWindow.loadFile('index.html');

  // Ensure window is always on top even over full-screen apps
  mainWindow.setAlwaysOnTop(true, 'screen-saver');

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

function createSettingsWindow() {
  if (settingsWindow) {
    settingsWindow.focus();
    return;
  }

  settingsWindow = new BrowserWindow({
    width: 440,
    height: 480,
    resizable: false,
    title: '💧 Sidekick — Settings',
    autoHideMenuBar: true,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
    },
  });

  settingsWindow.loadFile('settings.html');

  settingsWindow.on('closed', () => {
    settingsWindow = null;
  });
}

function createTray() {
  const iconPath = path.join(__dirname, 'assets', 'tray_icon.png');
  tray = new Tray(iconPath);
  tray.setToolTip('Sidekick 💧');

  const contextMenu = Menu.buildFromTemplate([
    {
      label: '💧  Drink Water Now!',
      click: () => triggerPopup(),
    },
    {
      label: '⚙  Settings',
      click: () => createSettingsWindow(),
    },
    { type: 'separator' },
    {
      label: '❌  Quit',
      click: () => {
        app.isQuitting = true;
        app.quit();
      },
    },
  ]);

  tray.setContextMenu(contextMenu);
  tray.on('click', () => triggerPopup());
}

function scheduleNextReminder() {
  if (reminderTimer) clearTimeout(reminderTimer);

  const minutes = configManager.config.interval_minutes || 30;
  const ms = minutes * 60 * 1000;

  reminderTimer = setTimeout(() => {
    triggerPopup();
    scheduleNextReminder();
  }, ms);
}

function triggerPopup(isTest = false) {
  if (!mainWindow || mainWindow.isDestroyed()) return;

  const primaryDisplay = screen.getPrimaryDisplay();
  const workArea = primaryDisplay.workArea || primaryDisplay.bounds || { x: 0, y: 0, width: 1920, height: 1080 };
  const screenWidth = workArea.width || 1920;
  const screenHeight = workArea.height || 1080;
  const workAreaY = workArea.y || 0;
  const groundY = Math.round(workAreaY + screenHeight - WIN_H - 10);

  const message = configManager.getRandomMessage();
  const config = configManager.config;

  mainWindow.webContents.send('start-animation', {
    message,
    screenWidth,
    screenHeight,
    groundY,
    config,
    isTest,
  });

  // Start offscreen left
  try {
    mainWindow.setPosition(-WIN_W, groundY);
    mainWindow.show();
  } catch (err) {
    console.error('[Sidekick] Error showing window:', err);
  }
}

// ── IPC Handlers ──────────────────────────────────────────────────────────

ipcMain.on('set-window-pos', (event, arg1, arg2) => {
  if (!mainWindow || mainWindow.isDestroyed()) return;

  let x, y;
  if (typeof arg1 === 'object' && arg1 !== null) {
    x = arg1.x;
    y = arg1.y;
  } else {
    x = arg1;
    y = arg2;
  }

  const posX = Math.trunc(Number(x));
  const posY = Math.trunc(Number(y));

  if (Number.isFinite(posX) && Number.isFinite(posY)) {
    try {
      mainWindow.setPosition(posX, posY);
    } catch (_) {
      // Safely ignore platform bounds rejection when window exits off-screen
    }
  }
});

ipcMain.on('animation-finished', () => {
  if (mainWindow && !mainWindow.isDestroyed()) {
    mainWindow.hide();
  }
  scheduleNextReminder();
});

ipcMain.on('open-settings', () => {
  createSettingsWindow();
});

ipcMain.on('get-config', (event) => {
  event.returnValue = configManager.config;
});

ipcMain.on('save-config', (event, newConfig) => {
  configManager.save(newConfig);
  scheduleNextReminder();
});

ipcMain.on('trigger-test-popup', () => {
  triggerPopup(true);
});

// ── App Lifecycle ─────────────────────────────────────────────────────────

app.whenReady().then(() => {
  createMainWindow();
  createTray();
  scheduleNextReminder();

  // Trigger first friendly greeting popup after 1.5 seconds
  setTimeout(() => {
    triggerPopup();
  }, 1500);
});

app.on('window-all-closed', (e) => {
  // Keep app alive in tray even if settings window is closed
  e.preventDefault();
});

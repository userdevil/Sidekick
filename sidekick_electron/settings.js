const { ipcRenderer } = require('electron');

const intervalSlider = document.getElementById('interval-slider');
const intervalLabel = document.getElementById('interval-label');
const durationSlider = document.getElementById('duration-slider');
const durationLabel = document.getElementById('duration-label');
const soundCheckbox = document.getElementById('sound-checkbox');
const btnTest = document.getElementById('btn-test');
const btnCancel = document.getElementById('btn-cancel');
const btnSave = document.getElementById('btn-save');
const pills = document.querySelectorAll('.pill');

let config = ipcRenderer.sendSync('get-config') || {
  interval_minutes: 30,
  popup_duration_seconds: 15,
  sound_enabled: true,
};

function formatInterval(mins) {
  if (mins < 60) {
    return `Every ${mins} minute${mins !== 1 ? 's' : ''}`;
  }
  const h = Math.floor(mins / 60);
  const m = mins % 60;
  return `Every ${h} hour${h !== 1 ? 's' : ''}${m > 0 ? ` ${m} min` : ''}`;
}

function updateUI() {
  intervalSlider.value = config.interval_minutes;
  intervalLabel.textContent = formatInterval(config.interval_minutes);

  durationSlider.value = config.popup_duration_seconds;
  durationLabel.textContent = `${config.popup_duration_seconds} seconds`;

  soundCheckbox.checked = !!config.sound_enabled;

  pills.forEach((p) => {
    const val = parseInt(p.getAttribute('data-val'), 10);
    p.classList.toggle('active', val === config.interval_minutes);
  });
}

// ── Event Listeners ──

intervalSlider.addEventListener('input', (e) => {
  const val = parseInt(e.target.value, 10);
  config.interval_minutes = val;
  intervalLabel.textContent = formatInterval(val);
  pills.forEach((p) => {
    const pVal = parseInt(p.getAttribute('data-val'), 10);
    p.classList.toggle('active', pVal === val);
  });
});

durationSlider.addEventListener('input', (e) => {
  const val = parseInt(e.target.value, 10);
  config.popup_duration_seconds = val;
  durationLabel.textContent = `${val} seconds`;
});

soundCheckbox.addEventListener('change', (e) => {
  config.sound_enabled = e.target.checked;
});

pills.forEach((p) => {
  p.addEventListener('click', () => {
    const val = parseInt(p.getAttribute('data-val'), 10);
    config.interval_minutes = val;
    updateUI();
  });
});

btnTest.addEventListener('click', () => {
  ipcRenderer.send('save-config', config);
  ipcRenderer.send('trigger-test-popup');
  window.close();
});

btnCancel.addEventListener('click', () => {
  window.close();
});

btnSave.addEventListener('click', () => {
  ipcRenderer.send('save-config', config);
  window.close();
});

// Initialize on load
updateUI();

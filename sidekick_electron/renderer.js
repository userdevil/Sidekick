const { ipcRenderer } = require('electron');

// UI Elements
const container = document.getElementById('container');
const fxCanvas = document.getElementById('fx-canvas');
const ctx = fxCanvas.getContext('2d');
const shadow = document.getElementById('shadow');
const mascotWrapper = document.getElementById('mascot-wrapper');
const charCanvas = document.getElementById('character-canvas');
const videoSource = document.getElementById('video-source');
const glintLeft = document.getElementById('glint-left');
const glintRight = document.getElementById('glint-right');
const waterBuddy = document.getElementById('water-buddy');
const bubbleContainer = document.getElementById('bubble-container');
const bubbleText = document.getElementById('bubble-text');
const btnYes = document.getElementById('btn-yes');
const btnNo = document.getElementById('btn-no');
const btnSettings = document.getElementById('btn-settings');

// State Constants
const STATE_WALK_IN = 0;
const STATE_IDLE = 1;
const STATE_POSITIVE = 2;
const STATE_RUN_AWAY = 3;
const STATE_NEGATIVE = 4;
const STATE_WALK_BACK_SAD = 5;
const STATE_HIDDEN = 6;

const WIN_W = 380;
const WIN_H = 430;
const TARGET_STOP_X = 85.0;

const path = require('path');

// Video file mappings (absolute paths for 100% reliability)
const VIDEOS = {
  walk_in: path.join(__dirname, 'assets', 'videos', 'water_3.mp4'),       // walking left to right intro
  idle_drink: path.join(__dirname, 'assets', 'videos', 'water_2.mp4'),    // stand and drink water while asking
  positive_walk: path.join(__dirname, 'assets', 'videos', 'water_4.mp4'), // walking left to right after positive
  sad_back: path.join(__dirname, 'assets', 'videos', 'water_1.mp4'),      // walking sadly back
};

let currentState = STATE_HIDDEN;
let currentX = -WIN_W;
let groundY = 500;
let screenWidth = 1920;
let screenHeight = 1080;
let appConfig = { sound_enabled: true, popup_duration_seconds: 15 };

let frameCount = 0;
let reactionTimer = 0;
let animationLoopId = null;

// Typewriter state
let fullMessage = "";
let currentChars = 0;
let typewriterTimer = null;
let autoDismissTimer = null;

// Particles
let particles = [];

// ══════════════════════════════════════════════════════════════════════════
//  Real-Time WebGL Green-Screen Chroma Key Engine
// ══════════════════════════════════════════════════════════════════════════

class ChromaKeyEngine {
  constructor(canvas, video) {
    this.canvas = canvas;
    this.video = video;
    this.gl = canvas.getContext('webgl', { premultipliedAlpha: false, alpha: true });
    this.hasWebGL = !!this.gl;
    this.texture = null;

    if (this.hasWebGL) {
      this._initWebGL();
    } else {
      this.ctx2d = canvas.getContext('2d');
    }
  }

  _initWebGL() {
    const gl = this.gl;

    const vsSource = `
      attribute vec2 a_position;
      varying vec2 v_texCoord;
      void main() {
        gl_Position = vec4(a_position, 0.0, 1.0);
        v_texCoord = vec2((a_position.x + 1.0) / 2.0, 1.0 - (a_position.y + 1.0) / 2.0);
      }
    `;

    const fsSource = `
      precision mediump float;
      uniform sampler2D u_image;
      varying vec2 v_texCoord;

      void main() {
        vec4 color = texture2D(u_image, v_texCoord);

        float maxRB = max(color.r, color.b);
        float greenDiff = color.g - maxRB;

        // Emerald Green Screen Detection
        if (color.g > 0.43 && color.g > color.r * 1.3 && color.g > color.b * 1.15 && greenDiff > 0.09) {
          if (greenDiff > 0.17) {
            discard; // Transparent
          } else {
            float alpha = (0.17 - greenDiff) / 0.08;
            gl_FragColor = vec4(color.r, maxRB, color.b, alpha * color.a);
          }
        } else {
          // Despill green reflection on edges
          if (color.g > maxRB && greenDiff > 0.04) {
            gl_FragColor = vec4(color.r, maxRB, color.b, color.a);
          } else {
            gl_FragColor = color;
          }
        }
      }
    `;

    function createShader(type, source) {
      const shader = gl.createShader(type);
      gl.shaderSource(shader, source);
      gl.compileShader(shader);
      return shader;
    }

    const program = gl.createProgram();
    gl.attachShader(program, createShader(gl.VERTEX_SHADER, vsSource));
    gl.attachShader(program, createShader(gl.FRAGMENT_SHADER, fsSource));
    gl.linkProgram(program);
    gl.useProgram(program);

    // Setup rectangle quad
    const posBuffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, posBuffer);
    gl.bufferData(
      gl.ARRAY_BUFFER,
      new Float32Array([
        -1.0, -1.0,
         1.0, -1.0,
        -1.0,  1.0,
        -1.0,  1.0,
         1.0, -1.0,
         1.0,  1.0,
      ]),
      gl.STATIC_DRAW
    );

    const posAttr = gl.getAttribLocation(program, 'a_position');
    gl.enableVertexAttribArray(posAttr);
    gl.vertexAttribPointer(posAttr, 2, gl.FLOAT, false, 0, 0);

    // Texture
    this.texture = gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D, this.texture);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
  }

  play(videoPath, loop = true) {
    if (this.currentVideoPath === videoPath && !this.video.paused) {
      return;
    }
    this.currentVideoPath = videoPath;
    this.video.src = videoPath;
    this.video.loop = loop;
    this.video.muted = true;
    this.video.playsInline = true;
    this.video.oncanplay = () => {
      this.video.play().catch((e) => console.log('[Video] Play notice:', e));
    };
    this.video.load();
    this.video.play().catch(() => {});
  }

  render() {
    if (!this.video || this.video.readyState < 2) return;

    if (this.hasWebGL) {
      const gl = this.gl;
      gl.viewport(0, 0, this.canvas.width, this.canvas.height);
      gl.clearColor(0.0, 0.0, 0.0, 0.0);
      gl.clear(gl.COLOR_BUFFER_BIT);

      gl.bindTexture(gl.TEXTURE_2D, this.texture);
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, this.video);
      gl.drawArrays(gl.TRIANGLES, 0, 6);
    } else if (this.ctx2d) {
      // 2D Canvas Fallback
      const ctx = this.ctx2d;
      ctx.drawImage(this.video, 0, 0, this.canvas.width, this.canvas.height);
      const imgData = ctx.getImageData(0, 0, this.canvas.width, this.canvas.height);
      const d = imgData.data;
      for (let i = 0; i < d.length; i += 4) {
        const r = d[i], g = d[i + 1], b = d[i + 2];
        const maxRB = Math.max(r, b);
        if (g > 110 && g > r * 1.3 && g > b * 1.15 && g - maxRB > 25) {
          d[i + 3] = 0;
        }
      }
      ctx.putImageData(imgData, 0, 0);
    }
  }
}

const chromaPlayer = new ChromaKeyEngine(charCanvas, videoSource);

// ══════════════════════════════════════════════════════════════════════════
//  Web Audio Synthesizer
// ══════════════════════════════════════════════════════════════════════════

let audioCtx = null;
function getAudioCtx() {
  if (!audioCtx) {
    audioCtx = new (window.AudioContext || window.webkitAudioContext)();
  }
  return audioCtx;
}

function playTone(freq, duration, type = 'sine', startTime = 0) {
  if (!appConfig.sound_enabled) return;
  try {
    const actx = getAudioCtx();
    const osc = actx.createOscillator();
    const gain = actx.createGain();
    osc.type = type;
    osc.frequency.setValueAtTime(freq, actx.currentTime + startTime);
    gain.gain.setValueAtTime(0.18, actx.currentTime + startTime);
    gain.gain.exponentialRampToValueAtTime(0.001, actx.currentTime + startTime + duration);
    osc.connect(gain);
    gain.connect(actx.destination);
    osc.start(actx.currentTime + startTime);
    osc.stop(actx.currentTime + startTime + duration);
  } catch (e) {
    console.error('[Audio] Error playing tone:', e);
  }
}

function playExclamation() {
  playTone(523.25, 0.15, 'sine', 0);     // C5
  playTone(659.25, 0.25, 'triangle', 0.1); // E5
}

function playCelebration() {
  playTone(523.25, 0.12, 'sine', 0);     // C5
  playTone(659.25, 0.12, 'sine', 0.08);  // E5
  playTone(783.99, 0.12, 'sine', 0.16);  // G5
  playTone(1046.50, 0.35, 'triangle', 0.24); // C6
}

function playSadChime() {
  playTone(392.00, 0.25, 'sine', 0);     // G4
  playTone(311.13, 0.40, 'triangle', 0.15); // Eb4
}

// ══════════════════════════════════════════════════════════════════════════
//  IPC Listener: Start Animation
// ══════════════════════════════════════════════════════════════════════════

ipcRenderer.on('start-animation', (event, data) => {
  screenWidth = Number(data.screenWidth) || 1920;
  screenHeight = Number(data.screenHeight) || 1080;
  groundY = Number(data.groundY) || (screenHeight - WIN_H - 10);
  appConfig = data.config || appConfig;
  fullMessage = data.message || "Hey! Time for a water break! 💧\nDid you drink a glass of water?";

  startWalkIn();
});

function startWalkIn() {
  clearTimers();
  currentState = STATE_WALK_IN;
  currentX = -WIN_W;
  frameCount = 0;
  reactionTimer = 0;
  particles = [];

  // Reset UI
  charCanvas.className = '';
  bubbleContainer.style.display = 'none';
  waterBuddy.style.display = 'none';
  glintLeft.style.display = 'none';
  glintRight.style.display = 'none';

  // 1. Play Video: water_3.mp4 (walking left to right intro)
  chromaPlayer.play(VIDEOS.walk_in, true);

  playExclamation();
  ipcRenderer.send('set-window-pos', { x: currentX, y: groundY });

  if (animationLoopId) cancelAnimationFrame(animationLoopId);
  animationLoopId = requestAnimationFrame(animationLoop);
}

// ══════════════════════════════════════════════════════════════════════════
//  Main Animation Loop
// ══════════════════════════════════════════════════════════════════════════

function animationLoop() {
  frameCount++;
  chromaPlayer.render();
  updateParticles();
  renderParticles();

  switch (currentState) {
    case STATE_WALK_IN:
      tickWalkIn();
      break;
    case STATE_IDLE:
      tickIdle();
      break;
    case STATE_POSITIVE:
      tickPositive();
      break;
    case STATE_RUN_AWAY:
      tickRunAway();
      break;
    case STATE_NEGATIVE:
      tickNegative();
      break;
    case STATE_WALK_BACK_SAD:
      tickWalkBackSad();
      break;
    case STATE_HIDDEN:
      return;
  }

  animationLoopId = requestAnimationFrame(animationLoop);
}

// ── 1. Walk In ────────────────────────────────────────────────────────────

function tickWalkIn() {
  const walkSpeed = 5.2;
  currentX += walkSpeed;

  // Stride footprint ripple
  if (frameCount % 18 === 0) {
    addFootstepRipple();
  }

  // Move window smoothly
  ipcRenderer.send('set-window-pos', { x: currentX, y: groundY });

  if (currentX >= TARGET_STOP_X) {
    currentX = TARGET_STOP_X;
    ipcRenderer.send('set-window-pos', { x: currentX, y: groundY });
    enterIdleState();
  }
}

// ── 2. Idle State: Stand & Drink Water ────────────────────────────────────

function enterIdleState() {
  currentState = STATE_IDLE;
  waterBuddy.style.display = 'block';

  // 2. Play Video: water_2.mp4 (stand and drinking water while asking)
  chromaPlayer.play(VIDEOS.idle_drink, true);

  // Show speech bubble with typewriter text
  bubbleContainer.style.display = 'flex';
  document.getElementById('bubble-buttons').style.display = 'flex';
  startTypewriter(fullMessage);

  // Auto-dismiss timeout
  autoDismissTimer = setTimeout(() => {
    if (currentState === STATE_IDLE) {
      handlePositive();
    }
  }, (appConfig.popup_duration_seconds || 15) * 1000);
}

function tickIdle() {
  // Water buddy bobs smoothly
  const buddyBob = Math.sin(frameCount * 0.1) * 5.0;
  waterBuddy.style.transform = `translateY(${-buddyBob}px)`;

  // Sparkles
  if (frameCount % 24 === 0) {
    addSparkle();
  }
}

// ── 3. Positive Reaction: Celebrate & Walk Off Right ──────────────────────

function handlePositive() {
  if (currentState !== STATE_IDLE && currentState !== STATE_WALK_IN) return;
  clearTimers();

  currentState = STATE_POSITIVE;
  reactionTimer = 0;
  waterBuddy.style.display = 'none';
  document.getElementById('bubble-buttons').style.display = 'none';

  startTypewriter("WOOHOO! 🎉 Awesome job!\nStay hydrated, superstar! 💧✨");
  playCelebration();
  spawnConfetti();

  // Sunglasses glint
  glintLeft.style.display = 'block';
  glintRight.style.display = 'block';

  // 3. Play Video: water_4.mp4 (walking continuously left to right)
  chromaPlayer.play(VIDEOS.positive_walk, true);
}

function tickPositive() {
  reactionTimer++;

  if (reactionTimer >= 24) {
    glintLeft.style.display = 'none';
    glintRight.style.display = 'none';
    currentState = STATE_RUN_AWAY;
  }
}

// ── 4. Walk Away Happily ──────────────────────────────────────────────────

function tickRunAway() {
  const runSpeed = 12.0;
  currentX += runSpeed;

  ipcRenderer.send('set-window-pos', { x: currentX, y: groundY });

  // Speed puffs
  if (frameCount % 3 === 0) {
    addSpeedPuff();
  }

  if (currentX > screenWidth + 60) {
    finishAndClose();
  }
}

// ── 5. Negative Reaction: Sad Slump & Walk Back Left ──────────────────────

function handleNegative() {
  if (currentState !== STATE_IDLE && currentState !== STATE_WALK_IN) return;
  clearTimers();

  currentState = STATE_NEGATIVE;
  reactionTimer = 0;
  waterBuddy.style.display = 'none';
  document.getElementById('bubble-buttons').style.display = 'none';

  startTypewriter("Aww... 🥺 Please go grab\na glass of water now, okay? 💔");
  playSadChime();
  charCanvas.classList.add('sad-tint');

  // Sad raincloud
  particles.push({
    type: 'sadCloud',
    x: 190,
    y: 135,
    life: 300,
    maxLife: 300,
  });

  // 4. Play Video: water_1.mp4 (walking sadly back)
  chromaPlayer.play(VIDEOS.sad_back, true);
}

function tickNegative() {
  reactionTimer++;

  // Falling raindrops
  if (reactionTimer % 4 === 0) {
    addRainDrop();
  }

  if (reactionTimer >= 30) {
    currentState = STATE_WALK_BACK_SAD;
  }
}

// ── 6. Walk Back Sadly ────────────────────────────────────────────────────

function tickWalkBackSad() {
  const sadSpeed = 4.5;
  currentX -= sadSpeed;

  ipcRenderer.send('set-window-pos', { x: currentX, y: groundY });

  if (frameCount % 6 === 0) {
    addRainDrop();
  }

  if (currentX < -WIN_W - 40) {
    finishAndClose();
  }
}

function finishAndClose() {
  currentState = STATE_HIDDEN;
  clearTimers();
  if (animationLoopId) cancelAnimationFrame(animationLoopId);
  ctx.clearRect(0, 0, WIN_W, WIN_H);
  if (videoSource) videoSource.pause();
  ipcRenderer.send('animation-finished');
}

function clearTimers() {
  if (typewriterTimer) clearInterval(typewriterTimer);
  if (autoDismissTimer) clearTimeout(autoDismissTimer);
}

// ── Typewriter Effect ─────────────────────────────────────────────────────

function startTypewriter(text) {
  if (typewriterTimer) clearInterval(typewriterTimer);
  bubbleText.textContent = "";
  currentChars = 0;

  typewriterTimer = setInterval(() => {
    if (currentChars < text.length) {
      currentChars += 2;
      bubbleText.textContent = text.substring(0, Math.min(text.length, currentChars));
    } else {
      clearInterval(typewriterTimer);
    }
  }, 28);
}

// ── Particles Physics ─────────────────────────────────────────────────────

function spawnConfetti() {
  const colors = ['#FFD54F', '#4FC3F7', '#81C784', '#FF8A80', '#BA68C8', '#4DD0E1'];
  for (let i = 0; i < 28; i++) {
    particles.push({
      type: 'confetti',
      x: 190 + (Math.random() * 80 - 40),
      y: 240 + (Math.random() * 40 - 20),
      vx: Math.random() * 12 - 6,
      vy: -(Math.random() * 7 + 3),
      size: Math.random() * 4 + 3,
      color: colors[Math.floor(Math.random() * colors.length)],
      isCircle: Math.random() > 0.5,
      life: 45,
      maxLife: 45,
    });
  }
}

function addRainDrop() {
  particles.push({
    type: 'rainDrop',
    x: 190 + (Math.random() * 44 - 22),
    y: 155,
    vx: -0.3,
    vy: 5.0,
    color: '#29B6F6',
    life: 22,
    maxLife: 22,
  });
}

function addSpeedPuff() {
  particles.push({
    type: 'speedPuff',
    x: 120 + (Math.random() * 20 - 10),
    y: 360 + (Math.random() * 14 - 7),
    vx: -5.0,
    vy: -0.5,
    size: Math.random() * 5 + 4,
    color: 'rgba(178, 235, 242, 0.75)',
    life: 15,
    maxLife: 15,
  });
}

function addFootstepRipple() {
  particles.push({
    type: 'footstepRipple',
    x: 190 + (Math.random() * 30 - 15),
    y: 395,
    color: '#81D4FA',
    size: 6,
    life: 12,
    maxLife: 12,
  });
}

function addSparkle() {
  particles.push({
    type: 'sparkle',
    x: 190 + (Math.random() * 120 - 60),
    y: 260 + (Math.random() * 100 - 60),
    size: 4 + Math.random() * 3,
    color: Math.random() > 0.5 ? '#FFD54F' : '#81D4FA',
    life: 14,
    maxLife: 14,
  });
}

function updateParticles() {
  for (let i = particles.length - 1; i >= 0; i--) {
    const p = particles[i];
    p.life--;
    if (p.life <= 0) {
      particles.splice(i, 1);
      continue;
    }
    p.x += p.vx || 0;
    p.y += p.vy || 0;

    if (p.type === 'confetti') {
      p.vy += 0.25; // gravity
      p.vx *= 0.98;
    } else if (p.type === 'footstepRipple') {
      p.size += 1.2;
    } else if (p.type === 'speedPuff') {
      p.vx *= 0.92;
      p.size *= 0.96;
    }
  }
}

function renderParticles() {
  ctx.clearRect(0, 0, WIN_W, WIN_H);

  for (const p of particles) {
    const alpha = Math.max(0, p.life / p.maxLife);
    ctx.save();
    ctx.globalAlpha = alpha;

    if (p.type === 'confetti') {
      ctx.fillStyle = p.color;
      if (p.isCircle) {
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        ctx.fill();
      } else {
        ctx.fillRect(p.x - p.size, p.y - p.size, p.size * 2, p.size * 2);
      }
    } else if (p.type === 'rainDrop') {
      ctx.strokeStyle = p.color;
      ctx.lineWidth = 2.0;
      ctx.lineCap = 'round';
      ctx.beginPath();
      ctx.moveTo(p.x, p.y);
      ctx.lineTo(p.x - 1, p.y + 8);
      ctx.stroke();
    } else if (p.type === 'speedPuff') {
      ctx.fillStyle = p.color;
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
      ctx.fill();
    } else if (p.type === 'footstepRipple') {
      ctx.strokeStyle = p.color;
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.ellipse(p.x, p.y, p.size * 2, p.size * 0.7, 0, 0, Math.PI * 2);
      ctx.stroke();
    } else if (p.type === 'sparkle') {
      ctx.strokeStyle = p.color;
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.moveTo(p.x - p.size, p.y);
      ctx.lineTo(p.x + p.size, p.y);
      ctx.moveTo(p.x, p.y - p.size);
      ctx.lineTo(p.x, p.y + p.size);
      ctx.stroke();
    } else if (p.type === 'sadCloud') {
      ctx.fillStyle = '#78909C';
      ctx.beginPath();
      ctx.arc(p.x - 20, p.y, 24, 0, Math.PI * 2);
      ctx.arc(p.x + 15, p.y - 6, 28, 0, Math.PI * 2);
      ctx.arc(p.x + 35, p.y + 4, 20, 0, Math.PI * 2);
      ctx.fill();
    }

    ctx.restore();
  }
}

// ── Event Handlers ────────────────────────────────────────────────────────

mascotWrapper.addEventListener('click', () => handlePositive());
btnYes.addEventListener('click', (e) => {
  e.stopPropagation();
  handlePositive();
});
btnNo.addEventListener('click', (e) => {
  e.stopPropagation();
  handleNegative();
});
btnSettings.addEventListener('click', (e) => {
  e.stopPropagation();
  ipcRenderer.send('open-settings');
});

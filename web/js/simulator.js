/**
 * Luna Dimmer - 网页端调光与护眼物理光学仿真引擎 (Optical Simulation Engine)
 * 实时仿真 Win32 硬件背光通信 (DDC/CI I2C)、RGB Gamma 曲线无级衰减与 Living Luminary 昼夜灵动光球
 */

// 系统重置默认初始态 (100% 满光，0% 暖色，无任意捏造或预设偏置)
let currentBrightness = 100;
let isBoost = false;
let currentWarmth = 0;

const sliderFill = document.getElementById('sliderFill');
const boostChip = document.getElementById('boostChip');
const orbPreview = document.getElementById('orbPreview');
const luminaryTitle = document.getElementById('luminaryTitle');
const luminaryStatus = document.getElementById('luminaryStatus');
const ambientGlow = document.getElementById('ambientGlow');
const screenDimmerLayer = document.getElementById('screenDimmerLayer');
const screenWarmthLayer = document.getElementById('screenWarmthLayer');

// Telemetry DOM elements
const metricPowerVal = document.getElementById('metricPowerVal');
const metricHwLevelSub = document.getElementById('metricHwLevelSub');
const metricLuxVal = document.getElementById('metricLuxVal');
const metricOverlayVal = document.getElementById('metricOverlayVal');
const metricOverlayBadge = document.getElementById('metricOverlayBadge');
const metricTempKelvin = document.getElementById('metricTempKelvin');
const metricBlueCutSub = document.getElementById('metricBlueCutSub');
const pipeHwStatus = document.getElementById('pipeHwStatus');
const pipeGammaStatus = document.getElementById('pipeGammaStatus');

// 缓存主控制卡片胶囊轨宽度，杜绝在 updateDisplay 高频事件中触发 Layout Thrashing
let cachedTrackWidth = '406px';
function updateCachedTrackWidth() {
  const mainTrack = document.getElementById('sliderTrack');
  if (mainTrack && mainTrack.clientWidth) {
    cachedTrackWidth = mainTrack.clientWidth + 'px';
    const clips = document.querySelectorAll('.capsule-layer-clip');
    clips.forEach(clip => {
      clip.style.width = cachedTrackWidth;
    });
  }
}
window.addEventListener('resize', updateCachedTrackWidth, { passive: true });

// 全站唯一通知 API（样式统一由 luna.css 的 #webToast 定义）
let webToastTimer = null;
function showWebToast(msg) {
  let toast = document.getElementById('webToast');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'webToast';
    document.body.appendChild(toast);
  }
  toast.textContent = msg;
  toast.classList.add('show');
  if (webToastTimer) clearTimeout(webToastTimer);
  webToastTimer = setTimeout(() => toast.classList.remove('show'), 2600);
}

// -------------------------------------------------------------------------
// 60FPS LIVE PHYSICAL GAMMA RAMP CANVAS VISUALIZER (Zero-Blur High Performance)
// -------------------------------------------------------------------------
function drawLiveGammaRamp(bVal, wVal) {
  const canvas = document.getElementById('gammaCanvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const w = canvas.width;
  const h = canvas.height;

  ctx.clearRect(0, 0, w, h);

  // Grid background
  ctx.strokeStyle = 'rgba(255, 255, 255, 0.05)';
  ctx.lineWidth = 1;
  const gridX = w / 12;
  for (let x = gridX; x < w; x += gridX) {
    ctx.beginPath();
    ctx.moveTo(x, 0);
    ctx.lineTo(x, h);
    ctx.stroke();
  }
  const gridY = h / 6;
  for (let y = gridY; y < h; y += gridY) {
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(w, y);
    ctx.stroke();
  }

  // Calculate coefficients based on brightness and warmth
  const bFactor = 0.2 + (bVal / 100.0) * 0.8;
  const wRatio = wVal / 100.0;
  const rFactor = bFactor * 1.0;
  const gFactor = bFactor * (1.0 - wRatio * 0.15);
  const bColorFactor = bFactor * (1.0 - wRatio * 0.72); // Blue cut down by up to 72%

  // Update legend numbers
  const legR = document.getElementById('legR');
  const legG = document.getElementById('legG');
  const legB = document.getElementById('legB');
  if (legR) legR.textContent = rFactor.toFixed(2);
  if (legG) legG.textContent = gFactor.toFixed(2);
  if (legB) legB.textContent = bColorFactor.toFixed(2);

  // Draw R, G, B Gamma curves (双通道轻量无高斯模糊荧光线，消除掉帧)
  function drawCurve(factor, color, glowColor) {
    ctx.save();
    // 1. 底层微透光晕线
    ctx.strokeStyle = glowColor;
    ctx.lineWidth = 4.0;
    ctx.beginPath();
    for (let i = 0; i <= 50; i++) {
      const normX = i / 50.0;
      const normY = Math.pow(normX, 2.2) * factor;
      const px = 10 + normX * (w - 20);
      const py = (h - 8) - normY * (h - 16);
      if (i === 0) ctx.moveTo(px, py);
      else ctx.lineTo(px, py);
    }
    ctx.stroke();

    // 2. 顶层高亮细线
    ctx.strokeStyle = color;
    ctx.lineWidth = 1.8;
    ctx.stroke();
    ctx.restore();
  }

  drawCurve(bColorFactor, '#60A5FA', 'rgba(96, 165, 250, 0.25)'); // Blue
  drawCurve(gFactor, '#34D399', 'rgba(52, 211, 153, 0.25)');       // Green
  drawCurve(rFactor, '#F87171', 'rgba(248, 113, 113, 0.25)');       // Red
}

if (typeof document !== 'undefined') {
  document.addEventListener('DOMContentLoaded', () => {
    drawLiveGammaRamp(currentBrightness, currentWarmth);
  });
}

function updateDisplay() {
  if (window.LunaSound) window.LunaSound.tick();
  window.currentBrightness = currentBrightness;
  window.currentWarmth = currentWarmth;
  const bText = currentBrightness + '%';
  const sliderValBase = document.getElementById('sliderValBase');
  const sliderValFill = document.getElementById('sliderValFill');
  if (sliderValBase) sliderValBase.textContent = bText;
  if (sliderValFill) sliderValFill.textContent = bText;
  if (sliderFill) {
    sliderFill.style.width = currentBrightness + '%';
    if (currentBrightness === 0) {
      sliderFill.classList.add('zero-width');
    } else {
      sliderFill.classList.remove('zero-width');
    }
  }

  const wText = currentWarmth + '%';
  const warmthValBase = document.getElementById('warmthValBase');
  const warmthValFill = document.getElementById('warmthValFill');
  if (warmthValBase) warmthValBase.textContent = wText;
  if (warmthValFill) warmthValFill.textContent = wText;
  const warmthFill = document.getElementById('warmthFill');
  if (warmthFill) {
    warmthFill.style.width = currentWarmth + '%';
    if (currentWarmth === 0) {
      warmthFill.classList.add('zero-width');
    } else {
      warmthFill.classList.remove('zero-width');
    }
  }

  // Live Gamma Ramp Visualizer
  drawLiveGammaRamp(currentBrightness, currentWarmth);

  // 1. Living Luminary State
  const d = (typeof I18N_DATA !== 'undefined' && I18N_DATA[currentLang]) ? I18N_DATA[currentLang] : {
    mockTitleDay: '日间清晰工作',
    mockStatusDay: '☀️ 充足自然光环境',
    mockTitleNight: '晚间舒适护眼',
    mockStatusNight: '🌙 熄灯护眼模式',
    mockStatusSleep: '🛌 助眠微光中 (12秒微光脉动)'
  };
  if (luminaryTitle) luminaryTitle.textContent = (d && d.appTitle) ? d.appTitle : ((currentLang === 'zh') ? '月光屏幕调光器' : 'Luna Dimmer');
  const iconBase = document.getElementById('sliderIconBase');
  const iconFill = document.getElementById('sliderIconFill');
  if (currentBrightness >= 70) {
    if (iconBase) iconBase.textContent = '☀️';
    if (iconFill) iconFill.textContent = '☀️';
    if (orbPreview) {
      orbPreview.style.background = 'radial-gradient(circle, #ffe285 20%, #f5a623 80%)';
      orbPreview.style.boxShadow = '0 0 24px rgba(245, 166, 35, 0.7)';
    }
    if (luminaryStatus) luminaryStatus.textContent = (d && d.mockStatusDay) ? d.mockStatusDay : '☀️ 日间工作模式';
  } else if (currentBrightness >= 20) {
    if (iconBase) iconBase.textContent = '🌙';
    if (iconFill) iconFill.textContent = '🌙';
    if (orbPreview) {
      orbPreview.style.background = 'radial-gradient(circle, #f8fafc 10%, #cbd5e1 75%, #94a3b8 100%)';
      orbPreview.style.boxShadow = '0 0 16px rgba(255, 255, 255, 0.35)';
    }
    if (luminaryStatus) luminaryStatus.textContent = (d && d.mockStatusNight) ? d.mockStatusNight : '🌙 熄灯护眼模式';
  } else {
    if (iconBase) iconBase.textContent = '🛌';
    if (iconFill) iconFill.textContent = '🛌';
    if (orbPreview) {
      orbPreview.style.background = 'radial-gradient(circle, #e2e8f0 10%, #475569 80%)';
      orbPreview.style.boxShadow = '0 0 12px rgba(226, 232, 240, 0.25)';
    }
    if (luminaryStatus) {
      if (currentBrightness <= 10) {
        luminaryStatus.textContent = (currentLang === 'zh')
          ? '🛌 助眠微光中 (按 Esc 或点击恢复原状)'
          : '🛌 Bedtime Glow (Press Esc or Click Reset)';
      } else {
        luminaryStatus.textContent = (d && d.mockStatusSleep) ? d.mockStatusSleep : '🛌 助眠微光中 (12秒微光脉动)';
      }
    }
  }

  // 2. Telemetry Calculations
  const hwBrightness = Math.max(10, currentBrightness);
  const estPower = (4.2 + (hwBrightness / 100) * 23.8).toFixed(1);
  const powerSaved = Math.round((1 - (estPower / 28.0)) * 100);
  if (metricPowerVal) metricPowerVal.textContent = estPower;
  const metricPowerUnit = document.getElementById('metricPowerUnit');
  if (metricPowerUnit) {
    metricPowerUnit.textContent = (currentLang === 'zh') ? `W (省电 ~${powerSaved}%)` : `W (Saved ~${powerSaved}%)`;
  }
  if (metricHwLevelSub) {
    metricHwLevelSub.textContent = (currentLang === 'zh')
      ? `DDC/CI 硬件寄存器: ${hwBrightness}% (省电 ~${powerSaved}%)`
      : `DDC/CI Hardware Register: ${hwBrightness}% (Saved ~${powerSaved}%)`;
  }
  if (pipeHwStatus) pipeHwStatus.textContent = `DIRECT_LINK_OK (${hwBrightness}%)`;

  // Overlay Alpha calculation (Safe Visual Floor capped at 0.80 / 0.82)
  let overlayAlpha = 0.00;
  if (currentBrightness <= 10) {
    const factor = (10 - currentBrightness) / 10.0;
    overlayAlpha = isBoost ? (factor * 0.82) : (factor * 0.80);
    if (metricOverlayBadge) {
      metricOverlayBadge.textContent = (currentLang === 'zh') ? '深度激活中' : 'Deep Active';
      metricOverlayBadge.style.color = '#38BDF8';
    }
  } else {
    if (metricOverlayBadge) {
      metricOverlayBadge.textContent = (currentLang === 'zh') ? '待机中 (0.00)' : 'Standby (0.00)';
      metricOverlayBadge.style.color = '#64748B';
    }
  }
  if (metricOverlayVal) metricOverlayVal.textContent = overlayAlpha.toFixed(2);

  // Lux reduction
  let luxFactor = (currentBrightness / 100.0);
  if (currentBrightness <= 10) {
    luxFactor *= (1.0 - overlayAlpha);
  }
  const luxReduction = ((1.0 - luxFactor) * 100).toFixed(1);
  if (metricLuxVal) metricLuxVal.textContent = (luxReduction === '0.0' ? '0.0' : '-' + luxReduction);
  const metricLuxSub = document.getElementById('metricLuxSub');
  if (metricLuxSub) {
    if (currentBrightness === 100 && currentWarmth === 0) {
      metricLuxSub.textContent = (currentLang === 'zh') ? '系统默认满光状态' : 'Default full-light state';
    } else {
      metricLuxSub.textContent = (currentLang === 'zh') ? '滤光衰减生效中' : 'Optical filter active';
    }
  }

  // Color temperature calculation (6500K down to 2200K)
  const kelvin = Math.round(6500 - (currentWarmth / 100.0) * 4300);
  if (metricTempKelvin) metricTempKelvin.textContent = kelvin;
  if (metricBlueCutSub) {
    metricBlueCutSub.textContent = (currentLang === 'zh')
      ? `蓝光波峰衰减: -${currentWarmth}%`
      : `Blue Peak Cut: -${currentWarmth}%`;
  }
  if (pipeGammaStatus) pipeGammaStatus.textContent = `CURVE_APPLIED (${kelvin}K)`;

  // 3. Real-time Fullscreen Optical Simulation Layer Reactions (人机安全微光底限 RFC-21)
  let dimFactor = 0;
  if (currentBrightness >= 80) {
    dimFactor = ((100 - currentBrightness) / 20) * 0.12;
  } else if (currentBrightness >= 20) {
    dimFactor = 0.12 + ((80 - currentBrightness) / 60) * 0.38;
  } else {
    // 20% -> 0.50, 0% -> 0.80 (保留 20% 安全微光与可读性，杜绝纯黑陷阱)
    dimFactor = 0.50 + ((20 - currentBrightness) / 20.0) * 0.30;
  }
  if (isBoost) {
    dimFactor = Math.min(0.82, dimFactor * 1.05);
  } else {
    dimFactor = Math.min(0.80, dimFactor);
  }
  if (screenDimmerLayer) {
    screenDimmerLayer.style.opacity = dimFactor.toFixed(3);
  }

  // Low-Light Rescue Affordance (人机安全微光底限 RFC-21)
  const btnMockReset = document.getElementById('btnMockReset');
  if (btnMockReset) {
    if (currentBrightness <= 10) {
      btnMockReset.classList.add('rescue-glow');
      btnMockReset.title = (currentLang === 'zh')
        ? '太暗看不清？点击这里立即恢复系统原状 (或按 Ctrl+Alt+Backspace 紧急唤醒)'
        : 'Too dark? Click here to restore defaults (or press Ctrl+Alt+Backspace)';
    } else {
      btnMockReset.classList.remove('rescue-glow');
      btnMockReset.title = (currentLang === 'zh')
        ? '一键恢复屏幕亮度和色温为系统初始状态'
        : 'Reset screen brightness and color to system defaults';
    }
  }

  // Warmth candlelight hue layer: 0% -> 0.00, up to 100% -> 0.72
  const warmthFactor = currentWarmth / 100.0;
  if (screenWarmthLayer) {
    screenWarmthLayer.style.opacity = (warmthFactor * 0.72).toFixed(3);
  }

  // Ambient background glow color shift
  if (ambientGlow) {
    const warmR = Math.round(56 + warmthFactor * (255 - 56));
    const warmG = Math.round(189 - warmthFactor * (189 - 140));
    const warmB = Math.round(248 - warmthFactor * (248 - 25));
    ambientGlow.style.background = `radial-gradient(circle, rgba(${warmR}, ${warmG}, ${warmB}, ${0.12 + warmthFactor * 0.14}) 0%, rgba(245, 179, 56, ${0.05 + warmthFactor * 0.12}) 45%, transparent 70%)`;
    let bgLight = currentBrightness / 100;
    if (isBoost) bgLight *= 0.45;
    ambientGlow.style.opacity = Math.max(0.15, Math.min(1.0, 0.2 + bgLight * 0.8));
  }

  const warmthChipEl = document.getElementById('warmthChip');
  if (warmthChipEl) {
    warmthChipEl.classList.toggle('active', currentWarmth > 0);
  }
}

// Unified pointer drag handler for continuous 60/120FPS slider dragging (0% ~ 100%)
function initSliderDrag(trackId, onUpdate, minVal = 0, maxVal = 100) {
  const track = document.getElementById(trackId);
  if (!track) return;
  let isDragging = false;

  function updateFromEvent(e) {
    const rect = track.getBoundingClientRect();
    const x = Math.max(0, Math.min(e.clientX - rect.left, rect.width));
    const val = Math.round((x / rect.width) * (maxVal - minVal) + minVal);
    onUpdate(Math.max(minVal, Math.min(maxVal, val)));
  }

  track.addEventListener('pointerdown', (e) => {
    isDragging = true;
    try { track.setPointerCapture(e.pointerId); } catch (_) {}
    updateFromEvent(e);
  });

  track.addEventListener('pointermove', (e) => {
    if (!isDragging) return;
    updateFromEvent(e);
  });

  const stopDrag = (e) => {
    if (isDragging) {
      isDragging = false;
      try { track.releasePointerCapture(e.pointerId); } catch (_) {}
    }
  };

  track.addEventListener('pointerup', stopDrag);
  track.addEventListener('pointercancel', stopDrag);

  // Support mouse wheel micro-adjustment on hover (+/-1% per tick)
  track.addEventListener('wheel', (e) => {
    e.preventDefault();
    const delta = e.deltaY < 0 ? 1 : -1;
    const cur = (trackId === 'warmthTrack') ? currentWarmth : currentBrightness;
    const next = Math.max(minVal, Math.min(maxVal, cur + delta));
    onUpdate(next);
  }, { passive: false });
}

// Attach continuous dragging
initSliderDrag('sliderTrack', (val) => {
  currentBrightness = val;
  updateDisplay();
}, 0, 100);

initSliderDrag('warmthTrack', (val) => {
  currentWarmth = val;
  updateDisplay();
}, 0, 100);

function toggleBoost() {
  isBoost = !isBoost;
  if (boostChip) boostChip.classList.toggle('active', isBoost);
  updateDisplay();
}

function toggleWarmthMode() {
  if (currentWarmth > 0) {
    currentWarmth = 0;
  } else {
    currentWarmth = 50;
  }
  const warmthFillEl = document.getElementById('warmthFill');
  if (warmthFillEl) warmthFillEl.style.width = currentWarmth + '%';
  const warmthValBase = document.getElementById('warmthValBase');
  const warmthValFill = document.getElementById('warmthValFill');
  if (warmthValBase) warmthValBase.textContent = currentWarmth + '%';
  if (warmthValFill) warmthValFill.textContent = currentWarmth + '%';
  const warmthChip = document.getElementById('warmthChip');
  if (warmthChip) warmthChip.classList.toggle('active', currentWarmth > 0);
  updateDisplay();
  if (currentWarmth > 0) {
    showWebToast((currentLang === 'zh') ? '🌙 已开启舒缓防蓝光模式 (50% 加州暖阳色温)' : '🌙 Night Shift active (50% warm amber)');
  } else {
    showWebToast((currentLang === 'zh') ? '☀️ 已关闭防蓝光，恢复日光冷白' : '☀️ Night Shift disabled, daylight white restored');
  }
}

function resetToSystemDefault() {
  currentBrightness = 100;
  currentWarmth = 0;
  isBoost = false;
  if (boostChip) boostChip.classList.remove('active');
  const warmthChip = document.getElementById('warmthChip');
  if (warmthChip) warmthChip.classList.remove('active');
  const warmthFillEl = document.getElementById('warmthFill');
  if (warmthFillEl) warmthFillEl.style.width = '0%';
  const warmthValBase = document.getElementById('warmthValBase');
  const warmthValFill = document.getElementById('warmthValFill');
  if (warmthValBase) warmthValBase.textContent = '0%';
  if (warmthValFill) warmthValFill.textContent = '0%';
  document.querySelectorAll('.presets-row .preset-pill').forEach(p => p.classList.remove('active'));
  updateDisplay();
  showWebToast((currentLang === 'zh')
    ? '↺ 已重置为系统默认初始屏幕状态 (100% 亮度 · 0% 色温)'
    : '↺ Reset to system defaults (100% Brightness · 0% Warmth)');
}

let stealthStartTime = 0;
let stealthStartPos = null;

function triggerStealthSim() {
  if (window.LunaSound) window.LunaSound.stealth();
  const layer = document.getElementById('screenDimmerLayer');
  if (layer) {
    layer.style.opacity = '0.995';
  }
  stealthStartTime = Date.now();
  stealthStartPos = null;
  window.isWebStealthMode = true;
  showWebToast((currentLang === 'zh')
    ? '🎧 已切入黑屏挂机模式 (晃动鼠标或按任意键苏醒)'
    : '🎧 Pure Blackout mode active (wiggle mouse to wake)');
}

function exitStealthSim() {
  if (!window.isWebStealthMode) return;
  window.isWebStealthMode = false;
  if (window.LunaSound) window.LunaSound.wake();
  stealthStartPos = null;
  updateDisplay();
  showWebToast((currentLang === 'zh') ? '☀️ 屏幕已柔和苏醒' : '☀️ Screen gently awakened');
}

// 全局鼠标晃动苏醒检测 (智能 350ms 防抖 + 25px 晃动阈值判定)
window.addEventListener('pointermove', (e) => {
  if (!window.isWebStealthMode) return;

  if (Date.now() - stealthStartTime < 350) {
    stealthStartPos = { x: e.clientX, y: e.clientY };
    return;
  }
  if (!stealthStartPos) {
    stealthStartPos = { x: e.clientX, y: e.clientY };
    return;
  }
  const dx = e.clientX - stealthStartPos.x;
  const dy = e.clientY - stealthStartPos.y;
  if (dx * dx + dy * dy >= 625) { // 25px 位移阈值
    exitStealthSim();
  }
});

// 聚光灯微光透镜模拟 (Ctrl+Alt+F)
let isSpotlightActive = false;
function toggleSpotlightSim() {
  isSpotlightActive = !isSpotlightActive;
  showWebToast(isSpotlightActive ? '🔦 暗夜微光聚光灯已开启 (随鼠标透光)' : '🔦 暗夜微光聚光灯已关闭');
}

// 键盘盲操导航 (Left / Right 1% 步进, Shift 5%, Esc/Any-key 苏醒, Ctrl+Alt 快捷盲操)
window.addEventListener('keydown', (e) => {
  if (window.isWebStealthMode) {
    exitStealthSim();
    return;
  }

  // Ctrl + Alt 组合键盲操
  if (e.ctrlKey && e.altKey) {
    const k = e.key.toUpperCase();
    if (k === 'ARROWUP') {
      e.preventDefault();
      currentBrightness = Math.min(100, currentBrightness + 5);
      updateDisplay();
      showWebToast(`☀️ 亮度: ${currentBrightness}%`);
      return;
    }
    if (k === 'ARROWDOWN') {
      e.preventDefault();
      currentBrightness = Math.max(0, currentBrightness - 5);
      updateDisplay();
      showWebToast(`🌙 亮度: ${currentBrightness}%`);
      return;
    }
    if (k === 'S') {
      e.preventDefault();
      if (typeof applyPreset === 'function') applyPreset(5, 75, null, 'sleep');
      return;
    }
    if (k === 'B') {
      e.preventDefault();
      triggerStealthSim();
      return;
    }
    if (k === 'F') {
      e.preventDefault();
      toggleSpotlightSim();
      return;
    }
    if (k === 'BACKSPACE') {
      e.preventDefault();
      resetToSystemDefault();
      return;
    }
  }

  // 方向键微调（仅在指针悬停于控制面板、或面板本身获得焦点时生效）
  // 目的：1:1 还原桌面端键盘盲操，同时避免在页面浏览时劫持方向键滚动。
  const panelEl = document.querySelector('.luna-control-card');
  const panelActive = window.__lunaPanelHovered === true
    || (panelEl && panelEl.contains(document.activeElement));
  if (!panelActive) return;

  const step = e.shiftKey ? 5 : 1;
  if (e.key === 'ArrowRight' || e.key === 'ArrowUp') {
    e.preventDefault();
    currentBrightness = Math.min(100, currentBrightness + step);
    updateDisplay();
  } else if (e.key === 'ArrowLeft' || e.key === 'ArrowDown') {
    e.preventDefault();
    currentBrightness = Math.max(0, currentBrightness - step);
    updateDisplay();
  } else if (e.key === 'Escape') {
    exitStealthSim();
  }
});

// 主题状态使用 window 属性，避免与 modals.js 各自声明 let 造成
// 「Identifier 'currentWebTheme' has already been declared」而整段脚本失效。
window.currentWebTheme = 'dark';

function setWebTheme(theme) {
  window.currentWebTheme = theme;
  const cards = document.querySelectorAll('.luna-control-card');
  cards.forEach(card => {
    card.classList.remove('theme-light', 'theme-liquid-glass');
    if (theme === 'light') card.classList.add('theme-light');
    if (theme === 'liquid_glass') card.classList.add('theme-liquid-glass');
  });
  document.body.classList.remove('theme-light', 'theme-liquid-glass');
  if (theme === 'light') document.body.classList.add('theme-light');
  if (theme === 'liquid_glass') document.body.classList.add('theme-liquid-glass');

  const btnDark = document.getElementById('macThemeDarkBtn');
  const btnLight = document.getElementById('macThemeLightBtn');
  const btnGlass = document.getElementById('macThemeGlassBtn');
  if (btnDark) btnDark.classList.toggle('active', theme === 'dark');
  if (btnLight) btnLight.classList.toggle('active', theme === 'light');
  if (btnGlass) btnGlass.classList.toggle('active', theme === 'liquid_glass');

  const pillBtn = document.getElementById('btnThemeTogglePill');
  if (pillBtn) {
    if (theme === 'light') pillBtn.textContent = (currentLang === 'zh') ? '☀️ 浅色' : '☀️ Light';
    else if (theme === 'liquid_glass') pillBtn.textContent = (currentLang === 'zh') ? '💧 液态玻璃' : '💧 Liquid Glass';
    else pillBtn.textContent = (currentLang === 'zh') ? '🌙 深色' : '🌙 Dark';
  }

  // 唯一的主题切换提示（不再由 modals.js 重复实现）
  if (theme === 'light') {
    showWebToast(currentLang === 'zh' ? '☀️ 已切换至纯净浅色模式' : '☀️ Light theme activated');
  } else if (theme === 'liquid_glass') {
    showWebToast(currentLang === 'zh' ? '💧 已切换至苹果液态玻璃效果' : '💧 Apple Liquid Glass activated');
  } else {
    showWebToast(currentLang === 'zh' ? '🌙 已切换至暗夜深色模式' : '🌙 Dark theme activated');
  }
}

function toggleWebThemeQuick() {
  const order = ['dark', 'light', 'liquid_glass'];
  const cur = window.currentWebTheme || 'dark';
  const next = order[(order.indexOf(cur) + 1) % order.length];
  setWebTheme(next);
}

// 页面装载初始化
document.addEventListener('DOMContentLoaded', () => {
  updateCachedTrackWidth();
  updateDisplay();

  // 记录指针是否悬停在 1:1 控制面板内，用于键盘方向键权限判定
  const panelEl = document.querySelector('.luna-control-card');
  if (panelEl) {
    panelEl.addEventListener('pointerenter', () => { window.__lunaPanelHovered = true; });
    panelEl.addEventListener('pointerleave', () => { window.__lunaPanelHovered = false; });
  }
});

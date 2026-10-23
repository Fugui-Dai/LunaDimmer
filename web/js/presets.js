/**
 * Luna Dimmer - 官方场景预设与自定义管理器 (Scene Presets & Customizer)
 * 包含 6 组常用场景预设（白天办公、夜间阅读、睡前极暗、午间休息、自定义 1、自定义 2）
 * 支持物理屏幕参数抓取、实时效果预览与持久化应用
 */

// 快捷场景预设点击应用与右键保存
function applyPreset(brightness, warmth, el, presetKey) {
  currentBrightness = brightness;
  currentWarmth = warmth;
  if (presetKey) {
    window.currentActivePresetKey = presetKey;
  }
  if (brightness <= 5) {
    isBoost = true;
  } else {
    isBoost = false;
  }
  updateDisplay();
  if (window.LunaSound) window.LunaSound.preset();
  const pills = document.querySelectorAll('.presets-row .preset-pill');
  pills.forEach(p => p.classList.remove('active'));
  if (el) el.classList.add('active');
  const chip = document.getElementById('boostChip');
  if (chip) chip.classList.toggle('active', isBoost);
}

// 场景药丸的唯一渲染入口：自定义保存 / 恢复出厂 / 语言切换后统一复用
function renderPresetPills() {
  const pills = document.querySelectorAll('.presets-row .preset-pill');
  const keys = ['work', 'night', 'sleep', 'noon', 'custom_1', 'custom_2'];
  pills.forEach((pill, idx) => {
    const data = webScenePresets[keys[idx]];
    if (!data) return;
    pill.textContent = `${data.icon} ${data.name} ${data.brightness}%`;
  });
}

function saveWebPreset(name, b, w, el, event) {
  if (event) event.preventDefault();
  const tip = currentLang === 'zh' ? `✓ 已将当前屏幕光感保存为「${name}」预设` : `✓ Saved current screen optics to "${name}"`;
  showWebToast(tip);
}


// Web Preset Customizer Management Logic
    // =========================================================
    const DEFAULT_WEB_SCENE_PRESETS = {
      work: { name: '白天办公', icon: '☀️', brightness: 90, warmth: 0, boost_2x: false },
      night: { name: '夜间阅读', icon: '🌙', brightness: 30, warmth: 45, boost_2x: false },
      sleep: { name: '睡前极暗', icon: '🛌', brightness: 5, warmth: 70, boost_2x: true },
      noon: { name: '午间休息', icon: '☕', brightness: 65, warmth: 25, boost_2x: false },
      custom_1: { name: '自定义1', icon: '🎨', brightness: 50, warmth: 35, boost_2x: false },
      custom_2: { name: '自定义2', icon: '🌟', brightness: 20, warmth: 55, boost_2x: false }
    };

    let webScenePresets = JSON.parse(JSON.stringify(DEFAULT_WEB_SCENE_PRESETS));
    let currentEditPresetKey = 'custom_1';

    function openWebPresetCustomizer(presetKey = 'custom_1') {
      const modal = document.getElementById('webPresetCustomizerModal');
      if (modal) modal.classList.add('active');

      // 复用 switchWebPresetEdit 完成「选中标签 + 载入表单」，避免重复实现
      const keys = ['work', 'night', 'sleep', 'noon', 'custom_1', 'custom_2'];
      const idx = Math.max(0, keys.indexOf(presetKey));
      const tabBtn = document.querySelectorAll('#webPresetTabs .mac-seg-btn')[idx];
      switchWebPresetEdit(presetKey, tabBtn);
    }

    function closeWebPresetCustomizer() {
      const modal = document.getElementById('webPresetCustomizerModal');
      if (modal) modal.classList.remove('active');
    }

    function switchWebPresetEdit(key, el) {
      currentEditPresetKey = key;
      document.querySelectorAll('#webPresetTabs .mac-seg-btn').forEach(b => b.classList.remove('active'));
      if (el) el.classList.add('active');
      loadWebPresetToForm(key);
    }

    function loadWebPresetToForm(key) {
      const data = webScenePresets[key] || DEFAULT_WEB_SCENE_PRESETS[key];
      const nameInput = document.getElementById('webPresetNameInput');
      const bSlider = document.getElementById('webPresetBrightSlider');
      const bVal = document.getElementById('webPresetBrightVal');
      const wSlider = document.getElementById('webPresetWarmthSlider');
      const wVal = document.getElementById('webPresetWarmthVal');
      const boostSw = document.getElementById('webPresetBoostSwitch');

      if (nameInput) nameInput.value = data.name;
      if (bSlider) bSlider.value = data.brightness;
      if (bVal) bVal.textContent = data.brightness + '%';
      if (wSlider) wSlider.value = data.warmth;
      if (wVal) wVal.textContent = data.warmth + '%';
      if (boostSw) boostSw.checked = !!data.boost_2x;

      const tip = document.getElementById('webPresetCustomizerTip');
      if (tip) tip.textContent = (currentLang === 'zh') ? `✓ 正在编辑「${data.name}」` : `✓ Editing "${data.name}"`;
    }

    function onWebPresetNameInput(val) {
      if (webScenePresets[currentEditPresetKey]) {
        webScenePresets[currentEditPresetKey].name = val.trim();
      }
    }

    function onWebPresetBrightInput(val) {
      const bVal = document.getElementById('webPresetBrightVal');
      if (bVal) bVal.textContent = val + '%';
      if (webScenePresets[currentEditPresetKey]) {
        webScenePresets[currentEditPresetKey].brightness = parseInt(val, 10);
      }
    }

    function onWebPresetWarmthInput(val) {
      const wVal = document.getElementById('webPresetWarmthVal');
      if (wVal) wVal.textContent = val + '%';
      if (webScenePresets[currentEditPresetKey]) {
        webScenePresets[currentEditPresetKey].warmth = parseInt(val, 10);
      }
    }

    function onWebPresetBoostChange(checked) {
      if (webScenePresets[currentEditPresetKey]) {
        webScenePresets[currentEditPresetKey].boost_2x = checked;
      }
    }

    function captureCurrentScreenToPreset() {
      const b = typeof currentBrightness !== 'undefined' ? currentBrightness : 50;
      const w = typeof currentWarmth !== 'undefined' ? currentWarmth : 0;
      const bSlider = document.getElementById('webPresetBrightSlider');
      const bVal = document.getElementById('webPresetBrightVal');
      const wSlider = document.getElementById('webPresetWarmthSlider');
      const wVal = document.getElementById('webPresetWarmthVal');

      if (bSlider) bSlider.value = b;
      if (bVal) bVal.textContent = b + '%';
      if (wSlider) wSlider.value = w;
      if (wVal) wVal.textContent = w + '%';

      if (webScenePresets[currentEditPresetKey]) {
        webScenePresets[currentEditPresetKey].brightness = b;
        webScenePresets[currentEditPresetKey].warmth = w;
      }

      const tip = document.getElementById('webPresetCustomizerTip');
      if (tip) tip.textContent = (currentLang === 'zh')
        ? `✓ 已抓取屏幕状态：${b}% 亮度 · ${w}% 色温`
        : `✓ Captured screen state: ${b}% Brightness · ${w}% Warmth`;
    }

    function previewWebPresetLive() {
      const bSlider = document.getElementById('webPresetBrightSlider');
      const wSlider = document.getElementById('webPresetWarmthSlider');
      const b = bSlider ? parseInt(bSlider.value, 10) : 50;
      const w = wSlider ? parseInt(wSlider.value, 10) : 0;
      applyPreset(b, w, null);
      const tip = document.getElementById('webPresetCustomizerTip');
      if (tip) tip.textContent = (currentLang === 'zh')
        ? `👁️ 正在实时预览当前滑块效果 (${b}% / ${w}%)`
        : `👁️ Live previewing current slider values (${b}% / ${w}%)`;
    }

    function resetWebPresetToDefault() {
      webScenePresets[currentEditPresetKey] = JSON.parse(JSON.stringify(DEFAULT_WEB_SCENE_PRESETS[currentEditPresetKey]));
      loadWebPresetToForm(currentEditPresetKey);
      const tip = document.getElementById('webPresetCustomizerTip');
      if (tip) tip.textContent = (currentLang === 'zh') ? `✓ 已恢复出厂默认值` : `✓ Restored factory defaults`;
    }

    function saveWebPresetCustomizer() {
      const data = webScenePresets[currentEditPresetKey];
      applyPreset(data.brightness, data.warmth, null);
      showWebToast((currentLang === 'zh')
        ? `💾 预设已保存: ${data.name} (${data.brightness}% 亮度 · ${data.warmth}% 色温)`
        : `💾 Preset saved: ${data.name} (${data.brightness}% Brightness · ${data.warmth}% Warmth)`);
      closeWebPresetCustomizer();

      // 刷新药丸 UI（统一走 renderPresetPills）
      renderPresetPills();
    }

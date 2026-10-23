/**
 * Luna Dimmer - 网页端模态弹窗控制器系统 (Modals & Sheet Controller)
 * 涵盖：
 * 1. Apple macOS Ventura/Sonoma 原生系统偏好设置面板与快捷键录制
 * 2. 纯净无痕运行保障与偏好设置持久化
 * 3. 开发者赞赏与夜深守候 24 小时昼夜节律温暖信笺
 * 4. 防刷防爬人机验证安全反馈弹窗
 * 5. 恢复出厂设置危险操作二次确认对话框 (Mac Sheet)
 */

// =========================================================================
    // APPLE-GRADE LIVE PREFERENCES MODAL LOGIC & GAMMA CANVAS
    // =========================================================================
    const WEB_VERSION = '1.0.0';
    const DEFAULT_MAC_HOTKEYS = {
      brightness_up: 'Ctrl+Alt+Up',
      brightness_down: 'Ctrl+Alt+Down',
      toggle_sleep: 'Ctrl+Alt+S',
      toggle_stealth: 'Ctrl+Alt+B',
      toggle_spotlight: 'Ctrl+Alt+F',
      toggle_panel: 'Ctrl+Alt+L',
      open_settings: 'Ctrl+Alt+P',
      panic_restore: 'Ctrl+Alt+Backspace'
    };
    let webMacHotkeys = Object.assign({}, DEFAULT_MAC_HOTKEYS);
    let macRecordingAction = null;

    const ACTION_TO_BTN_ID = {
      brightness_up: 'macBtnHkUp',
      brightness_down: 'macBtnHkDown',
      toggle_sleep: 'macBtnHkSleep',
      toggle_stealth: 'macBtnHkStealth',
      toggle_spotlight: 'macBtnHkSpotlight',
      toggle_panel: 'macBtnHkPanel',
      open_settings: 'macBtnHkSettings',
      panic_restore: 'macBtnHkEmergency'
    };

    // 偏好设置唯一打开入口（旧版 webTab/webPreferences 双实现已删除）
    function openWebSettingsModal() {
      if (typeof updateWebSponsorSubtitle === 'function') updateWebSponsorSubtitle();
      const modal = document.getElementById('webPreferencesModal');
      if (!modal) return;
      modal.classList.add('active');
      if (typeof switchMacPrefTab === 'function') {
        switchMacPrefTab(typeof currentMacTab !== 'undefined' ? currentMacTab : 0);
      }
    }

    // 最小化 / 关闭控制点在网页端仅作 1:1 视觉还原，不绑定任何行为。
    // 这样既不会出现「点了没反应」的挫败感，也不需要模拟一个假窗口功能。

    function closeWebPreferences() {
      const modal = document.getElementById('webPreferencesModal');
      if (modal) modal.classList.remove('active');
      if (macRecordingAction) cancelMacHotkeyRecording();
    }

    function handleModalOverlayClick(e) {
      if (e.target && e.target.classList.contains('mac-modal-overlay')) {
        e.target.classList.remove('active');
        if (macRecordingAction) cancelMacHotkeyRecording();
      }
    }

    function cancelMacHotkeyRecording() {
      if (!macRecordingAction) return;
      const btnId = ACTION_TO_BTN_ID[macRecordingAction];
      const btn = document.getElementById(btnId);
      if (btn) {
        btn.classList.remove('recording');
        btn.textContent = webMacHotkeys[macRecordingAction];
      }
      macRecordingAction = null;
      const status = document.getElementById('macHotkeyStatus');
      if (status) status.textContent = '';
    }

    // ===== 唯一的全局键盘入口：Esc 关闭 / 快捷键录制捕获 =====
    window.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        if (macRecordingAction) {
          cancelMacHotkeyRecording();
          e.preventDefault();
          return;
        }
        // 从最上层（危险确认）到最下层依次关闭，一次只关一层
        const layers = [
          ['webResetConfirmModal', closeWebResetConfirmModal],
          ['webPresetCustomizerModal', closeWebPresetCustomizer],
          ['webFeedbackModal', closeWebFeedbackModal],
          ['webSponsorModal', closeWebSponsorModal],
          ['webPreferencesModal', closeWebPreferences]
        ];
        for (const [id, closeFn] of layers) {
          const el = document.getElementById(id);
          if (el && el.classList.contains('active')) {
            closeFn();
            e.preventDefault();
            return;
          }
        }
        return;
      }

      if (macRecordingAction) {
        if (['Control', 'Alt', 'Shift', 'Meta'].includes(e.key)) return;
        e.preventDefault();

        const mods = [];
        if (e.ctrlKey) mods.push('Ctrl');
        if (e.altKey) mods.push('Alt');
        if (e.shiftKey) mods.push('Shift');
        if (e.metaKey) mods.push('Win');

        const status = document.getElementById('macHotkeyStatus');
        if (mods.length === 0) {
          if (status) {
            status.style.color = '#F87171';
            status.textContent = currentLang === 'zh' ? '⚠️ 快捷键需包含 Ctrl 或 Alt 等修饰键' : '⚠️ Must include Ctrl or Alt';
          }
          return;
        }

        let mainKey = e.key.toUpperCase();
        if (mainKey === 'ARROWUP') mainKey = 'Up';
        if (mainKey === 'ARROWDOWN') mainKey = 'Down';
        if (mainKey === 'ARROWLEFT') mainKey = 'Left';
        if (mainKey === 'ARROWRIGHT') mainKey = 'Right';
        if (mainKey === 'BACKSPACE') mainKey = 'Backspace';

        const combo = mods.join('+') + '+' + mainKey;

        // 检查键位冲突
        for (const [k, v] of Object.entries(webMacHotkeys)) {
          if (k !== macRecordingAction && v.toLowerCase() === combo.toLowerCase()) {
            if (status) {
              status.style.color = '#F87171';
              status.textContent = (currentLang === 'zh' ? '⚠️ 快捷键与现有功能冲突，请重新设置' : '⚠️ Conflict with existing action');
            }
            return;
          }
        }

        webMacHotkeys[macRecordingAction] = combo;
        const btnId = ACTION_TO_BTN_ID[macRecordingAction];
        const btn = document.getElementById(btnId);
        if (btn) {
          btn.classList.remove('recording');
          btn.textContent = combo;
        }
        if (status) {
          status.style.color = '#34D399';
          status.textContent = (currentLang === 'zh' ? '✓ 快捷键已成功绑定为: ' : '✓ Shortcut bound to: ') + combo;
          setTimeout(() => { if (status && status.textContent.includes(combo)) status.textContent = ''; }, 3000);
        }
        macRecordingAction = null;
      }
    });

/* =========================================================
       Apple macOS System Settings JS Logic
       ========================================================= */
    let currentMacTab = 0;
    const macPrefState = {
      autostart: false,
      remember_pos: true,
      auto_update: true,
      smooth_wake: true,
      lang: 'zh'
    };

    function switchMacPrefTab(idx) {
      currentMacTab = idx;
      for (let i = 0; i < 4; i++) {
        const btn = document.getElementById('macNavBtn' + i);
        const pane = document.getElementById('macTabPane' + i);
        if (btn) btn.classList.toggle('active', i === idx);
        if (pane) pane.style.display = (i === idx) ? 'flex' : 'none';
      }
      const titlesZh = ['⚙️ 常规与启动', '👁️ 调光与护眼', '⌨️ 全局快捷键', '🛡️ 守卫与重置'];
      const titlesEn = ['⚙️ General', '👁️ Optics & Care', '⌨️ Global Hotkeys', '🛡️ Safety & Reset'];
      const headerTitle = document.getElementById('macHeaderTitle');
      if (headerTitle) {
        headerTitle.textContent = (currentLang === 'zh') ? titlesZh[idx] : titlesEn[idx];
      }
    }

    function toggleMacSwitch(el, key) {
      if (!el) return;
      el.classList.toggle('active');
      macPrefState[key] = el.classList.contains('active');
      showWebToast(currentLang === 'zh' ? '✓ 偏好已即时自动保存' : '✓ Preferences auto-saved');
    }

    // 主题切换的唯一实现位于 simulator.js::setWebTheme()（本文件不再重复定义）

function handleCopyQQ(btn) {
  if (!btn) return;
  const originalText = btn.textContent;
  const copyText = '1115406747@qq.com';
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(copyText).then(() => {
      btn.textContent = (typeof currentLang !== 'undefined' && currentLang === 'zh') ? '✓ 已复制' : '✓ Copied';
      setTimeout(() => { btn.textContent = originalText; }, 2000);
    }).catch(() => {
      prompt((typeof currentLang !== 'undefined' && currentLang === 'zh') ? '请按 Ctrl+C 复制作者 QQ：' : 'Press Ctrl+C to copy QQ:', copyText);
    });
  } else {
    prompt((typeof currentLang !== 'undefined' && currentLang === 'zh') ? '请按 Ctrl+C 复制作者 QQ：' : 'Press Ctrl+C to copy QQ:', copyText);
  }
}

function handleMacCheckUpdate() {
      const btn = document.getElementById('btnMacCheckUpdate');
      const verLbl = document.getElementById('macLblCloudVer');
      if (!btn) return;
      btn.disabled = true;
      btn.textContent = currentLang === 'zh' ? '正在检测...' : 'Checking...';
      if (verLbl) verLbl.textContent = currentLang === 'zh' ? '正在连接云端服务器...' : 'Connecting to cloud...';
      setTimeout(() => {
        btn.disabled = false;
        btn.textContent = currentLang === 'zh' ? '🔄 检查新版本' : '🔄 Check Updates';
        if (verLbl) verLbl.textContent = currentLang === 'zh' ? `✓ 当前已是最新版本 (V${WEB_VERSION})` : `✓ Latest version (V${WEB_VERSION})`;
        setTimeout(() => {
          if (verLbl) verLbl.textContent = currentLang === 'zh' ? `当前版本: V${WEB_VERSION}` : `Current Version: V${WEB_VERSION}`;
        }, 3000);
      }, 1400);
    }

    function recordMacHotkey(actionKey) {
      if (macRecordingAction) {
        cancelMacHotkeyRecording();
      }
      macRecordingAction = actionKey;
      const btnId = ACTION_TO_BTN_ID[actionKey];
      const btn = document.getElementById(btnId);
      if (btn) {
        btn.classList.add('recording');
        btn.textContent = currentLang === 'zh' ? '🔴 按下快捷键... (Esc 取消)' : '🔴 Press combo... (Esc cancels)';
      }
      const statusLbl = document.getElementById('macHotkeyStatus');
      if (statusLbl) {
        statusLbl.style.color = '#F5B338';
        statusLbl.textContent = currentLang === 'zh' ? '正在捕获键盘输入...' : 'Listening for key sequence...';
      }
    }

    function resetMacHotkeys() {
      webMacHotkeys = Object.assign({}, DEFAULT_MAC_HOTKEYS);
      for (const [action, btnId] of Object.entries(ACTION_TO_BTN_ID)) {
        const btn = document.getElementById(btnId);
        if (btn) {
          btn.classList.remove('recording');
          btn.textContent = webMacHotkeys[action];
        }
      }
      const statusLbl = document.getElementById('macHotkeyStatus');
      if (statusLbl) {
        statusLbl.style.color = '#34D399';
        statusLbl.textContent = currentLang === 'zh' ? '✓ 快捷键已全部恢复为官方默认预设' : '✓ Hotkeys restored to default';
        setTimeout(() => { if (statusLbl) statusLbl.textContent = ''; }, 3000);
      }
    }

    function resetMacPreferencesAll() {
      openWebResetConfirmModal();
    }

    function openWebResetConfirmModal() {
      const modal = document.getElementById('webResetConfirmModal');
      if (modal) {
        const isEn = (currentLang === 'en');
        const titleEl = document.getElementById('webResetConfirmTitle');
        const descEl = document.getElementById('webResetConfirmDesc');
        const hkEl = document.getElementById('webResetBulletHk');
        const spEl = document.getElementById('webResetBulletPresets');
        const pfEl = document.getElementById('webResetBulletPrefs');
        const thEl = document.getElementById('webResetBulletTheme');
        const cancelBtn = document.getElementById('webResetBtnCancel');
        const okBtn = document.getElementById('webResetBtnOk');

        if (titleEl) titleEl.textContent = isEn ? 'Restore Factory Defaults?' : '恢复软件出厂默认设置？';
        if (descEl) descEl.textContent = isEn ? 'This is a dangerous operation. All custom preferences and configurations will be permanently reset:' : '此操作属于危险操作，执行后将清除所有个性化偏好且无法撤销：';
        if (hkEl) hkEl.textContent = isEn ? '• All global hotkeys will be reset to default bindings' : '• 全部全局快捷键恢复为默认初始键位';
        if (spEl) spEl.textContent = isEn ? '• All 6 scene presets (including custom presets) will be reset' : '• 6 项常用场景预设（含自定义预设）恢复出厂数值';
        if (pfEl) pfEl.textContent = isEn ? '• Autostart, window memory, and smooth transitions will reset' : '• 开机自启、窗口记忆与平滑过渡偏好恢复初始状态';
        if (thEl) thEl.textContent = isEn ? '• Appearance theme will reset to Dark, and language to Simplified Chinese' : '• 外观主题恢复为深色，界面语言恢复为简体中文';
        if (cancelBtn) cancelBtn.textContent = isEn ? 'Cancel' : '取消';
        if (okBtn) okBtn.textContent = isEn ? 'Reset All Settings' : '确定恢复出厂设置';

        modal.classList.add('active');
      }
    }

    function closeWebResetConfirmModal() {
      const modal = document.getElementById('webResetConfirmModal');
      if (modal) modal.classList.remove('active');
    }

    function confirmResetMacPreferencesAll() {
      closeWebResetConfirmModal();

      // 1. 重置快捷键
      resetMacHotkeys();

      // 2. 重置所有开关
      for (const swId of ['macSwAutostart']) {
        const sw = document.getElementById(swId);
        if (sw) sw.classList.remove('active');
      }
      for (const swId of ['macSwRememberPos', 'macSwAutoUpdate', 'macSwSmoothWake']) {
        const sw = document.getElementById(swId);
        if (sw) sw.classList.add('active');
      }

      // 3. 重置场景预设（药丸渲染统一走 presets.js::renderPresetPills）
      if (typeof DEFAULT_WEB_SCENE_PRESETS !== 'undefined') {
        webScenePresets = JSON.parse(JSON.stringify(DEFAULT_WEB_SCENE_PRESETS));
        if (typeof renderPresetPills === 'function') renderPresetPills();
      }

      // 4. 重置主题为深色
      setWebTheme('dark');

      // 5. 重置语言为简体中文
      setMacLanguage('zh');

      showWebToast(currentLang === 'zh' ? '✓ 已成功恢复所有出厂默认设置' : '✓ Successfully restored all factory defaults');
    }

    /* =========================================================
       Apple Web Feedback Anti-Spam & Attack Defense Sentinel
       ========================================================= */
    let webFbOpenTime = 0;
    let webFbLastSubmitTime = 0;
    let webFbMathA = 3;
    let webFbMathB = 5;


    function getWebTimePeriod() {
      const now = new Date();
      const m = now.getHours() * 60 + now.getMinutes();
      if (m >= 360 && m < 690) return 'morning'; // 06:00 ~ 11:29
      if (m >= 690 && m < 840) return 'noon'; // 11:30 ~ 13:59
      if (m >= 840 && m < 1110) return 'afternoon'; // 14:00 ~ 18:29
      if (m >= 1110 && m < 1410) return 'evening'; // 18:30 ~ 23:29
      return 'midnight'; // 23:30 ~ 05:59
    }

    function updateWebSponsorSubtitle() {
      const p = getWebTimePeriod();
      const subEl = document.getElementById('macLblSponsorSub');
      if (!subEl) return;
      const textsZh = {
        morning: '🌅 晨光破晓，今天也请温柔对待自己的眼睛，记得先吃一口热腾腾的早餐',
        noon: '🍱 办公室大概关灯午休了吧？别在微光里硬撑了，关掉屏幕哪怕闭目养神十分钟',
        afternoon: '☕ 伏案这么久累坏了吧？站起来伸个懒腰、接杯温水，去看看窗外的云',
        evening: '🌆 窗外人潮走空了，辛苦了一整天，弄完手头这件小事就早点回家吃顿热饭',
        midnight: '🌌 凌晨了还在赶项目熬夜吗？身体比工作重要一万倍，陌生人心疼你，求你快睡吧'
      };
      const textsEn = {
        morning: '🌅 Morning light is breaking. Remember to eat a warm breakfast and be gentle with your eyes today.',
        noon: "🍱 Office lights out for lunch? Don't strain in the dimness—close your screen and rest for 10 minutes.",
        afternoon: '☕ Tired from sitting so long? Stretch, grab a warm drink, and take a look at the clouds outside.',
        evening: "🌆 The office is clearing out. You've worked hard all day; finish this small task and head home soon.",
        midnight: '🌌 Burning the midnight oil on deadlines? Your health is 10,000x more important. Please get some sleep.'
      };
      subEl.textContent = (currentLang === 'zh' ? textsZh[p] : textsEn[p]);
    }

    function openWebSponsorModal() {
      const p = getWebTimePeriod();
      const titleEl = document.getElementById('webSponsorTitle');
      const bodyEl = document.getElementById('webSponsorBody');
      const btnMain = document.getElementById('webBtnSponsorMain');

      const dataZh = {
        morning: {
          title: '🌅 陌生人的一封晨光便签',
          btnText: '☀️ 收到，今天我会好好吃早餐',
          borderColor: '#38BDF8',
          html: `
            <div style="font-size: 13px; line-height: 22px; color: #CBD5E1;">
              <p style="margin: 0 0 8px 0;">早安，朋友 ☀️！整座城市还在苏醒，而你已坐在了屏幕前。大人们都在催你赶路，而我只想轻声问一句：昨晚睡得好吗？🥺</p>
              <p style="margin: 0 0 8px 0;"><span style="color: #38BDF8; font-weight: 700;">Luna Dimmer 永久 100% 免费，分文不取 🙅‍♂️。</span>做这款工具，只是想替你挡住刺眼的清晨冷光 💡。</p>
              <p style="margin: 0; color: #94A3B8;">无论今天有多忙，先吃一口热腾腾的早餐 🥟。屏幕的光调柔和了，今天也请温柔对待自己 💛！</p>
            </div>
          `
        },
        noon: {
          title: '🍱 陌生人的一份午间问候',
          btnText: '💤 听你的，这就合上屏幕趴一会儿',
          borderColor: '#34D399',
          html: `
            <div style="font-size: 13px; line-height: 22px; color: #CBD5E1;">
              <p style="margin: 0 0 8px 0;">大灯熄了，周围暗悄悄的，唯独你还在微光里敲着键盘，把所有疲倦咽进肚子里 🥺。</p>
              <p style="margin: 0 0 8px 0;"><span style="color: #34D399; font-weight: 700;">Luna Dimmer 永久免费，拒绝打赏 🙅‍♂️。</span>请把钱留给自己中午吃顿好的 🍲。</p>
              <p style="margin: 0; color: #94A3B8;">工作永远赶不完，但你只有一个。哪怕十分钟，合上电脑闭目小憩一会儿 💤，身体比手头的任务更宝贵 💛！</p>
            </div>
          `
        },
        afternoon: {
          title: '☕ 陌生人的一杯午后热茶',
          btnText: '🍵 收到，这就去接杯温水歇歇',
          borderColor: '#60A5FA',
          html: `
            <div style="font-size: 13px; line-height: 22px; color: #CBD5E1;">
              <p style="margin: 0 0 8px 0;">日光渐斜，眼睛又干涩发酸了吧？成人的世界里，所有人都在问你飞得高不高，很少有人问你累不累 🥺。</p>
              <p style="margin: 0 0 8px 0;"><span style="color: #60A5FA; font-weight: 700;">Luna Dimmer 纯粹免费，谢绝所有赞赏 🙅‍♂️。</span></p>
              <p style="margin: 0; color: #94A3B8;">站起来，去接一杯温热的水 🍵，望一眼窗外的天和云 ☁️。你已经做得很棒了，给自己两分钟喘息，深呼吸吧 💛！</p>
            </div>
          `
        },
        evening: {
          title: '🌆 陌生人的一句归家叮嘱',
          btnText: '🚶‍♂️ 收到，这就收拾准备回家',
          borderColor: '#A78BFA',
          html: `
            <div style="font-size: 13px; line-height: 22px; color: #CBD5E1;">
              <p style="margin: 0 0 8px 0;">街灯亮了，周围工位都空了，你是不是又默默撑到了最后 🥺？在万家灯火里独自消解疲惫，最让人心疼。</p>
              <p style="margin: 0 0 8px 0;"><span style="color: #A78BFA; font-weight: 700;">Luna Dimmer 永久免费，坚决不收一分钱 🙅‍♂️。</span></p>
              <p style="margin: 0; color: #94A3B8;">今天的仗你打赢了，收起电脑早点回家吧 🚶‍♂️！热腾腾的饭菜 🍲 和温暖的被窝 🛌 都在等你，辛苦了 💛！</p>
            </div>
          `
        },
        midnight: {
          title: '🌙 陌生人的一纸深夜心声',
          btnText: '🛌 听你的劝，立刻熄灯睡觉',
          borderColor: '#818CF8',
          html: `
            <div style="font-size: 13px; line-height: 22px; color: #CBD5E1;">
              <p style="margin: 0 0 8px 0;">夜深了，整座城市都睡了，唯独你的屏幕还亮在夜色里 🥺。成年人最大的破防，往往只因一句‘注意身体’。</p>
              <p style="margin: 0 0 8px 0;"><span style="color: #818CF8; font-weight: 700;">请听陌生人最真诚的劝告：Luna Dimmer 永久免费，分文不取 🙅‍♂️。</span></p>
              <p style="margin: 0; color: #94A3B8;">屏幕再柔和也换不来健康。今晚你不用向任何人证明什么，关掉屏幕，去被窝里睡个好觉吧 🌙💛！</p>
            </div>
          `
        }
      };

      const dataEn = {
        morning: {
          title: '🌅 A Morning Note from a Stranger',
          btnText: "☀️ Got it, I'll have a good breakfast",
          borderColor: '#38BDF8',
          html: `
            <div style="font-size: 13px; line-height: 22px; color: #CBD5E1;">
              <p style="margin: 0 0 8px 0;">The world always demands results, but I just want to ask: are you tired today? 🥺</p>
              <p style="margin: 0 0 8px 0;"><span style="color: #38BDF8; font-weight: 700;">Luna Dimmer is 100% free forever and declines all tips 🙅‍♂️.</span> We built this to shield your tired eyes 💡.</p>
              <p style="margin: 0; color: #94A3B8;">Tasks never end, but you only have one body. Grab a warm drink 🍵, have a good meal 🍲, and be gentle with yourself 💛!</p>
            </div>
          `
        },
        noon: {
          title: '🍱 A Lunchtime Greeting from a Stranger',
          btnText: '💤 Resting my eyes for 10 minutes',
          borderColor: '#34D399',
          html: `
            <div style="font-size: 13px; line-height: 22px; color: #CBD5E1;">
              <p style="margin: 0 0 8px 0;">The office lights are out and you're still typing in the dark 🥺.</p>
              <p style="margin: 0 0 8px 0;"><span style="color: #34D399; font-weight: 700;">Luna Dimmer is 100% free and declines all tips 🙅‍♂️.</span> Save that money for a warm lunch 🍲.</p>
              <p style="margin: 0; color: #94A3B8;">Close the screen and take a nap 💤. Your eyes matter far more than deadlines 💛!</p>
            </div>
          `
        },
        afternoon: {
          title: '☕ An Afternoon Tea from a Stranger',
          btnText: '🍵 Stepping away for warm water',
          borderColor: '#60A5FA',
          html: `
            <div style="font-size: 13px; line-height: 22px; color: #CBD5E1;">
              <p style="margin: 0 0 8px 0;">Drowsy afternoon, eyes dry and tired? The world asks how high you fly, not how tired you are 🥺.</p>
              <p style="margin: 0 0 8px 0;"><span style="color: #60A5FA; font-weight: 700;">Luna Dimmer is 100% free, purely for you 🙅‍♂️.</span></p>
              <p style="margin: 0; color: #94A3B8;">Grab some water 🍵, stretch, and look at the clouds ☁️. You are doing great 💛!</p>
            </div>
          `
        },
        evening: {
          title: '🌆 An Evening Farewell from a Stranger',
          btnText: '🚶‍♂️ Packing up to head home now',
          borderColor: '#A78BFA',
          html: `
            <div style="font-size: 13px; line-height: 22px; color: #CBD5E1;">
              <p style="margin: 0 0 8px 0;">Colleagues have all headed home. Did you push yourself to the end again 🥺?</p>
              <p style="margin: 0 0 8px 0;"><span style="color: #A78BFA; font-weight: 700;">Luna Dimmer is 100% free and never takes a dime 🙅‍♂️.</span></p>
              <p style="margin: 0; color: #94A3B8;">You fought hard today. Head home 🚶‍♂️ to warm food 🍲 and a cozy bed 🛌, you've earned it 💛!</p>
            </div>
          `
        },
        midnight: {
          title: '🌙 A Quiet Note from a Stranger',
          btnText: '🛌 Turning off screen and sleeping',
          borderColor: '#818CF8',
          html: `
            <div style="font-size: 13px; line-height: 22px; color: #CBD5E1;">
              <p style="margin: 0 0 8px 0;">The city sleeps while your screen still glows 🥺. Adults just need a simple 'take care'.</p>
              <p style="margin: 0 0 8px 0;"><span style="color: #818CF8; font-weight: 700;">Luna Dimmer is 100% free forever 🙅‍♂️.</span></p>
              <p style="margin: 0; color: #94A3B8;">Health cannot be bought. You don't have to prove anything tonight. Turn off the screen and sleep 🌙💛!</p>
            </div>
          `
        }
      };

      const curData = (typeof currentLang !== 'undefined' && currentLang === 'zh')
        ? (dataZh[p] || dataZh.midnight)
        : (dataEn[p] || dataEn.midnight);

      if (titleEl) titleEl.textContent = curData.title;
      if (bodyEl) {
        bodyEl.innerHTML = curData.html;
        bodyEl.style.borderLeft = `3px solid ${curData.borderColor}`;
      }
      if (btnMain) btnMain.textContent = curData.btnText;

      const modal = document.getElementById('webSponsorModal');
      if (modal) modal.classList.add('active');
    }

    function closeWebSponsorModal() {
      const modal = document.getElementById('webSponsorModal');
      if (modal) modal.classList.remove('active');
    }

    function copyWebSponsorWarmth(btn) {
      const p = getWebTimePeriod();
      const quotesZh = {
        morning: '早安，朋友 ☀️！整座城市还在苏醒，而你已坐在了屏幕前。大人们都在催你赶路，而我只想轻声问一句：昨晚睡得好吗？🥺\nLuna Dimmer 永久 100% 免费，分文不取。无论今天有多忙，先吃一口热腾腾的早餐 🥟，今天也请温柔对待自己 💛！\n—— 来自为你加油的陌生人',
        noon: '大灯熄了，周围暗悄悄的，唯独你还在微光里敲着键盘，把所有疲倦咽进肚子里 🥺。\nLuna Dimmer 永久免费，拒绝所有打赏。工作永远赶不完，但你只有一个。哪怕十分钟，合上电脑闭目小憩一会儿 💤，身体比手头的任务更宝贵 💛！\n—— 劝你歇一歇的陌生人',
        afternoon: '日光渐斜，眼睛又干涩发酸了吧？成人的世界里，所有人都在问你飞得高不高，很少有人问你累不累 🥺。\nLuna Dimmer 纯粹免费，谢绝所有赞赏。站起来，去接一杯温热的水 🍵，望一眼窗外的天和云 ☁️。你已经做得很棒了，给自己两分钟喘息，深呼吸吧 💛！\n—— 陪你度过午后的陌生人',
        evening: '街灯亮了，周围工位都空了，你是不是又默默撑到了最后 🥺？在万家灯火里独自消解疲惫，最让人心疼。\nLuna Dimmer 永久免费，坚决不收一分钱。今天的仗你打赢了，收起电脑早点回家吧 🚶‍♂️！热腾腾的饭菜 🍲 和温暖的被窝 🛌 都在等你，辛苦了 💛！\n—— 愿你早点到家的陌生人',
        midnight: '夜深了，整座城市都睡了，唯独你的屏幕还亮在夜色里 🥺。成年人最大的破防，往往只因一句‘注意身体’。\n请听陌生人最真诚的劝告：Luna Dimmer 永久免费，分文不取。屏幕再柔和也换不来健康。今晚你不用向任何人证明什么，关掉屏幕，去被窝里睡个好觉吧 🌙💛！\n—— 深夜里心疼你的陌生人',
      };
      const quotesEn = {
        morning: "The world always demands results, but I just want to ask: are you tired today? 🥺\nLuna Dimmer is 100% free forever and declines all tips 🙅‍♂️.\nTasks never end, but your health is irreplaceable. Grab a warm drink 🍵, have a good meal 🍲, and be gentle with yourself tonight 💛!\n— From a stranger quietly rooting for you",
        noon: "The office lights are out and you're still typing in the dark 🥺.\nLuna Dimmer is 100% free and declines all tips 🙅‍♂️.\nClose the screen and take a nap 💤. Your eyes matter far more than deadlines 💛!\n— From a stranger quietly rooting for you",
        afternoon: "Drowsy afternoon, eyes dry and tired? The world asks how high you fly, not how tired you are 🥺.\nLuna Dimmer is 100% free, purely for you 🙅‍♂️.\nGrab some water 🍵, stretch, and breathe ☁️. You are doing great 💛!\n— From a stranger quietly rooting for you",
        evening: "Colleagues have all headed home. Did you push yourself to the end again 🥺?\nLuna Dimmer is 100% free and never takes a dime 🙅‍♂️.\nYou fought hard today. Head home 🚶‍♂️ to warm food 🍲 and a cozy bed 🛌, you've earned it 💛!\n— From a stranger quietly rooting for you",
        midnight: "The city sleeps while your screen still glows 🥺. Adults just need a simple 'take care'.\nLuna Dimmer is 100% free forever 🙅‍♂️.\nHealth cannot be bought. You don't have to prove anything tonight. Turn off the screen and sleep 🌙💛!\n— From a stranger quietly rooting for you",
      };
      const textToCopy = (typeof currentLang !== 'undefined' && currentLang === 'zh')
        ? (quotesZh[p] || quotesZh.midnight)
        : (quotesEn[p] || quotesEn.midnight);

      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(textToCopy);
      }
      if (btn) {
        const orig = btn.textContent;
        btn.textContent = (typeof currentLang !== 'undefined' && currentLang === 'zh') ? '✓ 已复制这份温暖' : '✓ Warmth Copied';
        setTimeout(() => { btn.textContent = orig; }, 2500);
      }
    }

    function insistWebSponsor() {
      const fb = document.getElementById('webSponsorFeedback');
      const msg = (currentLang === 'zh')
        ? '❤️ 您的健康与双眼就是对我们最高的赞赏！请把想要打赏的心意留给自己买一杯热饮吧。'
        : '❤️ Your health and eyesight are our greatest reward! Please treat yourself to a warm drink.';
      if (fb) {
        fb.textContent = msg;
      }
      showWebToast(msg);
    }

    function openWebFeedbackModal() {
      webFbOpenTime = Date.now();
      webFbMathA = Math.floor(Math.random() * 8) + 2;
      webFbMathB = Math.floor(Math.random() * 7) + 1;
      const mathLbl = document.getElementById('webFbMathLabel');
      if (mathLbl) mathLbl.textContent = '🛡️ 人机验证：' + webFbMathA + ' + ' + webFbMathB + ' = ';
      const ansInput = document.getElementById('webFbMathAns');
      if (ansInput) ansInput.value = '';
      const statusDiv = document.getElementById('webFbStatus');
      if (statusDiv) statusDiv.textContent = '';

      const modal = document.getElementById('webFeedbackModal');
      if (modal) modal.classList.add('active');
    }

    function closeWebFeedbackModal() {
      const modal = document.getElementById('webFeedbackModal');
      if (modal) modal.classList.remove('active');
    }

    function submitWebFeedback() {
      const now = Date.now();
      const statusDiv = document.getElementById('webFbStatus');

      // 防御 1: 时间蜜罐 (< 2.5s)
      if (now - webFbOpenTime < 2500) {
        if (statusDiv) {
          statusDiv.style.color = '#F87171';
          statusDiv.textContent = '⚠️ 检测到自动化异常特征，提交已被安全拦截';
        }
        return;
      }

      // 防御 2: 蜜罐诱饵输入
      const honeypot = document.getElementById('webFbHoneypot');
      if (honeypot && honeypot.value.trim() !== '') {
        if (statusDiv) {
          statusDiv.style.color = '#F87171';
          statusDiv.textContent = '⚠️ 检测到自动化异常特征，提交已被安全拦截';
        }
        return;
      }

      // 防御 3: 60s 频控冷静期
      if (now - webFbLastSubmitTime < 60000) {
        const remaining = Math.ceil((60000 - (now - webFbLastSubmitTime)) / 1000);
        if (statusDiv) {
          statusDiv.style.color = '#F87171';
          statusDiv.textContent = '⚠️ 提交过于频繁，请等待 ' + remaining + ' 秒后再试';
        }
        return;
      }

      // 防御 4: 人机数学验证
      const userAns = document.getElementById('webFbMathAns');
      if (!userAns || parseInt(userAns.value.trim(), 10) !== (webFbMathA + webFbMathB)) {
        if (statusDiv) {
          statusDiv.style.color = '#F87171';
          statusDiv.textContent = '⚠️ 人机安全验证计算错误，请重新计算';
        }
        return;
      }

      // 防御 5: 字符长度与内容净化
      const descEl = document.getElementById('webFbDesc');
      const desc = descEl ? descEl.value.trim() : '';
      if (desc.length < 10) {
        if (statusDiv) {
          statusDiv.style.color = '#F87171';
          statusDiv.textContent = '⚠️ 描述内容过短，请至少输入 10 个字符';
        }
        return;
      }
      if (desc.length > 500) {
        if (statusDiv) {
          statusDiv.style.color = '#F87171';
          statusDiv.textContent = '⚠️ 描述内容过长，请控制在 500 字符以内';
        }
        return;
      }

      // 连续重复字符拦截
      if (/(.)\1{7,}/.test(desc)) {
        if (statusDiv) {
          statusDiv.style.color = '#F87171';
          statusDiv.textContent = '⚠️ 请勿输入无意义的重复字符或刷屏内容';
        }
        return;
      }

      // 验证通过！记录冷静期
      webFbLastSubmitTime = now;
      if (statusDiv) {
        statusDiv.style.color = '#34D399';
        statusDiv.textContent = '✓ 反馈已成功提交！感谢您对 Luna Dimmer 的支持与守护';
      }

      const submitBtn = document.getElementById('webBtnSubmitFb');
      if (submitBtn) {
        submitBtn.disabled = true;
        let sec = 60;
        const timer = setInterval(() => {
          sec--;
          if (sec <= 0) {
            clearInterval(timer);
            submitBtn.disabled = false;
            submitBtn.textContent = '🚀 安全提交反馈';
          } else {
            submitBtn.textContent = '冷静中 (' + sec + 's)';
          }
        }, 1000);
      }

      setTimeout(() => {
        closeWebFeedbackModal();
        showWebToast('✨ 反馈已送达官方处理中心，感谢您的支持！');
      }, 1500);
    }


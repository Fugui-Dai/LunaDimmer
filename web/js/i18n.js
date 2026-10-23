/**
 * Luna Dimmer - 网页端国际化与多语言引擎 (i18n Localization Engine)
 * 提供 100% 全域双语 (简体中文 zh-CN ↔ 英语 en-US) 即时无缝热重绘
 */

let currentLang = 'zh';

const I18N_DATA = {
  zh: {
    docTitle: '月光屏幕调光器 (Luna Dimmer) - 软硬双轨暗环境护眼工具',
    btnLang: 'EN',
    navWorkbench: '控制面板',
    navFeatures: '双轨架构',
    navHotkeys: '全局热键',
    navFaq: '常见问答',
    navGetWin: '获取 Windows 版',

    // Stage Header
    stageTitle: '把屏幕，调成刚刚好的一点微光',
    stageCapPanel: '1:1 还原 Windows 原生面板 · 拖动滑块',
    stageCapTelemetry: '实时遥测同步跳动 · 10%~100% 物理背光 / 1%~10% 穿透遮罩',
    heroDownloadCta: '下载 Windows 免安装版',

    // Control Mockup Card
    appTitle: '月光屏幕调光器',
    ctrlSettingsTip: '偏好设置与全局热键',
    ctrlMinTip: '最小化到系统托盘',
    ctrlCloseTip: '退出软件 (100% 恢复系统初始屏幕亮度与色彩)',
    mockStatusDay: '☀️ 日间工作模式',
    mockStatusNight: '🌙 熄灯护眼模式',
    mockStatusSleep: '🛌 助眠微光中 (12秒微光脉动)',
    themeDark: '🌙 深色',
    themeLight: '☀️ 浅色',
    themeGlass: '💧 液态玻璃',
    themeToggleTip: '快捷切换深色、浅色与液态玻璃主题',
    mockReset: '↺ 恢复原状',
    mockResetTip: '一键恢复屏幕亮度和色温为系统初始状态',

    // Brightness & Warmth Sliders
    sliderBrightTitle: '屏幕亮度',
    boostChipText: '⚡ 深度压暗 ⚡',
    warmthTitle: '护眼色温',
    warmthChipText: '🌙 舒缓防蓝光',
    warmthChipTip: '点击一键开启/关闭 50% 舒缓防蓝光护眼模式',

    // Scene Presets
    presetsTitle: '常用场景预设',
    presetsCustomizeBtn: '⚙️ 自定义',
    presetsCustomizeTip: '自定义情境名称、目标亮度、色温与深度压暗',
    presetPills: [
      { text: '☀️ 白天办公 90%', tip: '☀️ 白天办公 (90% 亮度 / 0% 色温)' },
      { text: '🌙 夜间阅读 30%', tip: '🌙 夜间阅读 (30% 亮度 / 45% 色温)' },
      { text: '🛌 睡前极暗 5%', tip: '🛌 睡前极暗 (5% 亮度 / 70% 色温)' },
      { text: '☕ 午间休息 65%', tip: '☕ 午间休息 (65% 亮度 / 25% 色温)\n左键单击：应用预设\n右键单击：保存当前为本预设' },
      { text: '🎨 自定义1 50%', tip: '🎨 自定义1 (50% 亮度 / 35% 色温)\n左键单击：应用预设\n右键单击：保存当前为本预设' },
      { text: '🌟 自定义2 20%', tip: '🌟 自定义2 (20% 亮度 / 55% 色温)\n左键单击：应用预设\n右键单击：保存当前为本预设' }
    ],

    // Stealth Card & Guide Bar
    stealthTitle: '🎧 一键黑屏挂机 (听歌/下载防刺眼)',
    stealthSub: '(按任意键或晃动鼠标柔和点亮屏幕)',
    keyboardGuideBar: '支持键盘 <kbd>←</kbd> <kbd>→</kbd> 键 1% 精细微调 · <kbd>Shift</kbd>+<kbd>→</kbd> 5% 步进',

    // Telemetry Panel
    telemetryTitle: '实时工程遥测控制台',
    telemetryTag: 'DDC/CI I2C + GDI Gamma',
    metricPowerLabel: '物理背光功耗',
    metricPowerBus: '● I2C直通',
    metricPowerSaved: 'W (省电 ~0%)',
    metricHwPrefix: 'DDC/CI 硬件寄存器',
    metricHwSaved: '省电',
    metricLuxLabel: '光通量削减比',
    metricLuxBadge: '● 护眼指数',
    metricLuxSub: '系统默认满光状态',
    metricLuxSubDim: '滤光衰减生效中',
    metricOverlayLabel: 'Win32 深度遮罩层',
    metricOverlayBadgeStandby: '待机中 (0.00)',
    metricOverlayBadgeActive: '深度激活中',
    metricOverlaySub: 'WS_EX_TRANSPARENT 零延迟穿透',
    metricTempLabel: '色温曲率 / 蓝光削减',
    metricTempBadge: '● 烛光护眼',
    metricBlueCutPrefix: '蓝光波峰衰减',
    gammaHeader: '物理 Gamma 2.2 波形监视器',
    pipe01Label: '[PIPE-01] DDC/CI 硬件背光通信:',
    pipe02Label: '[PIPE-02] Win32 零延迟鼠标穿透:',
    pipe03Label: '[PIPE-03] 16-bit Gamma 色温变换:',
    pipe04Label: '[PIPE-04] 非破坏性生命周期恢复哨兵:',
    pipe04Status: 'ARMED (100% 退出自动还原)',

    // Bento Features
    secFeaturesTitle: '双轨无级协同 · 比显示器最低亮度再暗一点',
    secFeaturesDesc: '告别液晶漏光与干涩刺痛，专为午休关灯、深夜加班与暗室办公打磨的双轨护眼架构。',
    bento1Title: '硬件背光 + 深度穿透遮罩双轨衔接',
    bento1Desc: '普通显示器物理调至 0% 依然有 30~50 nits 的刺眼漏光。Luna Dimmer 采用双轨无缝过渡技术：10%~100% 精确调控硬件功耗，滑至 10% 自动无缝接入 1%~10% 的微光遮罩，彻底杜绝刺眼强光。',
    bento1BadTitle: '传统软件 / 显示器 0%',
    bento1BadDesc: '依然存在 35 nits 液晶漏光，深夜刺目',
    bento1GoodTitle: 'Luna Dimmer 双轨压暗',
    bento1GoodDesc: '降至 1~3 nits 微光，温润似墨玉',
    bento2Title: '拟态天体动态核心 Living Luminary',
    bento2Desc: '呼应宇宙天体运行规律。日间满光呈现金色日冕高光；晚间切换为银白静谧冷月；极暗助眠时自主进入 12 秒星光呼吸脉动，呼吸与心跳同频。',
    bento3Title: '100% 鼠标穿透与无焦点抢占',
    bento3Desc: '基于 Win32 <code>WS_EX_TRANSPARENT | WS_EX_LAYERED | WS_EX_NOACTIVATE</code> 原生封装，遮罩层绝不阻挡游戏光标、拖拽操作与全屏打字，零输入延迟。',
    bento4Title: '无痕生命周期与硬件恢复保障',
    bento4Desc: '遵循非破坏性原则。启动时自动在内存备份系统初始硬件背光与 Gamma 色温曲线，退出时 100% 毫秒级复原屏幕初始状态，绝不修改注册表，绝不污染系统显示设置。',
    bento5Title: '键盘方向键 1% 精细微调',
    bento5Desc: '焦点无论在面板何处，敲击键盘 ← / → 键即时进行 1% 细腻步进调节；按住 Shift 5% 跳调，满足深夜对微光“多 1% 太亮、少 1% 太暗”的极致苛求。',

    // Hotkeys Section
    secHotkeysTitle: '全局键盘盲操工作流',
    secHotkeysDesc: '无需唤出主界面，在全屏看剧、敲代码或躺在床上时随手调节。',
    thCombo: '按键组合',
    thAction: '动作效果',
    thIntent: '设计意图',
    hotkeyRows: [
      { act: '<b>急救脱困：一键重置为系统默认 100% 状态</b>', intent: '全黑迷航安全底线，闭着眼睛敲击瞬间还原物理屏幕' },
      { act: '精细 1% 步进调节亮度 (Shift 键 5%)', intent: '面板激活时无需鼠标对准滑块，敲击键盘方向键即可微调' },
      { act: '全局快速调节亮度 (步长 5%)', intent: '无论正在全屏游戏还是浏览网页，全局毫秒级微调' },
      { act: '一键切入助眠极暗 (5%)', intent: '睡前摸黑一按即生效，无需开灯找鼠标' },
      { act: '一键黑屏挂机 (听歌/下载防刺眼)', intent: '一秒进入 99.5% 纯黑遮罩听歌挂机，晃动鼠标苏醒' },
      { act: '暗夜微光聚光灯透视', intent: '暗夜或挂机模式下随鼠标开辟微光透镜光圈，看清局部文字' },
      { act: '呼出 / 隐藏控制面板', intent: '在屏幕正中或托盘吸附位置快速切换显示' },
      { act: '打开偏好设置中心', intent: '在任意桌面状态下一键呼出设置面板，支持按键捕获与冲突检测' }
    ],

    // FAQ Section
    secFaqTitle: '常见问答与技术答疑',
    secFaqDesc: '关于暗环境护眼调光、硬件功耗与系统安全的所有疑问，都在这里解答。',
    faqList: [
      {
        q: 'Q: 为什么不直接调显示器硬件按键，而要用双轨调光？',
        a: '绝大多数液晶显示器即使把物理按键拉到 0%，实际发光仍有 30~50 nits，在漆黑卧室里依然刺目漏光。Luna Dimmer 既能调节物理背光降低功耗，又能在 10% 处自动无缝叠加深度深空遮罩，比硬件按键更暗更柔和，黑夜看屏温润如纸。'
      },
      {
        q: 'Q: 关闭或卸载后会对屏幕色彩有残留影响吗？',
        a: '绝不。Luna Dimmer 严格遵循“非破坏性生命周期”原则：启动时毫秒级备份系统原始物理背光与 Gamma 色温曲线，退出软件或点击“一键重置”时 100% 恢复初始硬件状态，零残留、零隐患。'
      },
      {
        q: 'Q: 极暗或挂机后如何随时唤醒脱困？',
        a: '随时敲击全局紧急快捷键 <b>Ctrl + Alt + Backspace</b>（或轻按 Esc 键）即可瞬间复原系统默认 100% 满光；挂机时晃动鼠标光标亦可 1.5 秒柔和苏醒，从容告别强光刺激。'
      }
    ],

    // Footer
    footerCopyright: '© 2026 月光屏幕调光器 (Luna Dimmer). 遵循 MIT 开源协议。',
    footerPrivacy: '🛡️ 100% 本地运算 · 零遥测上传 · 零联网追踪',

    // Preferences Modal
    prefSidebarTitle: '偏好设置',
    prefTabs: ['常规与启动', '调光与护眼', '全局快捷键', '安全守护与重置'],
    macLblThemeTitle: '外观主题',
    macLblThemeSub: '在深色、浅色与液态玻璃之间即时无缝切换',
    macThemeDark: '🌙 深色',
    macThemeLight: '☀️ 浅色',
    macThemeGlass: '💧 液态玻璃',
    macLblLang: '界面语言',
    macLblLangSub: '动态即时重绘，无需重启客户端',
    macLblAutostart: '开机时自动后台静默启动',
    macLblAutostartSub: 'Windows 登录后自动最小化常驻托盘，不弹窗打扰',
    macLblRememberPos: '记忆主控制面板上次拖拽停靠位置',
    macLblRememberPosSub: '关闭此项后每次自动吸附在右下角任务栏托盘正上方',
    macLblAutoUpdate: '启动时自动检查新版本',
    macLblAutoUpdateSub: '启动时在后台静默检测是否有更稳定或高性能版本',
    macLblFullscreenGuard: '全屏游戏与演示时禁止快捷键弹窗抢焦点',
    macLblFullscreenGuardSub: '处于全屏独占应用时快捷键仅在后台平滑调光，不打断游戏与视频',
    macLblCloudVer: '当前版本: V1.0.0',
    macLblOfficialSite: '官方网站',
    macBtnVisitSite: '🌐 访问官网',
    macLblContactQQ: '联系作者 / QQ',
    macBtnCopyQQ: '📋 复制',
    btnMacCheckUpdate: '🔄 检查新版本',

    // Tab 1: Optics
    macLblHwChannel: '当前显示器调光方式：',
    macLblHwChannelSub: '通过 DDC/CI I2C 物理通道直接调控显示器背光',
    macLblHwReady: '🟢 硬件物理背光调节 (支持 DDC/CI 物理硬件通信)',
    macLblSmoothWake: '黑屏唤醒时启用 1.5 秒平滑渐亮 (防强光刺眼)',
    macLblSmoothWakeSub: '夜间唤醒屏幕时以柔和曲线逐渐变亮，避免瞬间强光刺激眼睛',

    // Tab 2: Hotkeys
    macLblHkGroup: '全局快捷键设置 (点击键帽录制新按键)',
    macBtnResetHk: '↺ 恢复默认快捷键',
    macHkList: {
      up: '☀️ 快速调亮 (+5%)',
      down: '🌙 快速调暗 (-5%)',
      sleep: '🛌 切换睡前极暗模式 (5%)',
      stealth: '🎧 切换黑屏挂机模式',
      spotlight: '🔦 切换微光聚光灯透视',
      panel: '🎛️ 显示 / 隐藏控制面板',
      settings: '⚙️ 打开软件设置面板',
      emergency: '🚨 紧急恢复满亮 (防误触黑屏)'
    },

    // Tab 3: Safety & Reset
    macLblSafetyTitle: '纯净无痕运行保障声明',
    macLblSafety: '安全不破坏系统：软件退出或崩溃时，100% 自动还原屏幕原本物理亮度和色温，绝不修改注册表。独立守护哨兵进程监听主 PID，毫秒级无痕自愈。',
    macLblFbTitle: '问题与体验反馈',
    macLblFbSub: '遇到异常缺陷或有改进建议？欢迎随时向工程师团队反馈',
    macBtnOpenFb: '提交使用反馈',
    macLblSponsorTitle: '开发者赞赏与心意',
    macLblSponsorSub: '一份来自开发团队写在深夜里的真诚心声',
    macBtnOpenSponsor: '☕ 打赏支持',
    macLblResetTitle: '恢复软件出厂默认设置',
    macLblResetSub: '将所有光感、偏好、开机项与全局快捷键重置为出厂预设',
    macBtnResetAll: '恢复出厂设置',
    macLblAutoSave: '✓ 偏好设置即时生效并自动保存',
    macBtnDone: '完成',

    // Preset Customizer Modal
    webPresetModalTitle: '🎨 自定义常用场景预设',
    webPresetTabs: ['☀️ 白天', '🌙 夜间', '🛌 睡前', '☕ 午间', '🎨 自定1', '🌟 自定2'],
    webPresetLblName: '预设显示名称',
    webPresetLblNameSub: '在主控制面板和快捷菜单中显示的标题',
    webPresetLblBright: '目标屏幕亮度',
    webPresetLblBrightSub: '切换到此情境时的显示器物理背光与微光',
    webPresetLblWarmth: '防蓝光护眼色温',
    webPresetLblWarmthSub: '暖色琥珀色调深度过滤高能短波蓝光',
    webPresetLblBoost: '2x 深度压暗滤镜',
    webPresetLblBoostSub: '突破硬件最低物理背光，实现暗夜微透镜',
    webPresetBtnCapture: '📍 抓取当前屏幕参数',
    webPresetBtnPreview: '👁️ 实时预览效果',
    webPresetBtnReset: '↺ 恢复出厂默认',
    webPresetTip: '✓ 修改将自动同步到主控制面板',
    webPresetBtnCancel: '取消',
    webPresetBtnSave: '💾 保存并应用',

    // Feedback Modal
    webFbModalTitle: '💬 问题与体验反馈 (V1.0.0)',
    webFbLblCategory: '反馈分类：',
    webFbOptions: [
      '🐛 遇到异常缺陷 (Bug Report)',
      '💡 体验与功能建议 (Feature Request)',
      '🖥️ 显示器硬件兼容问题 (Hardware)'
    ],
    webFbDescPlaceholder: '请详细描述发生场景、屏幕型号或改进建议 (10~500 字)...',
    webFbContactPlaceholder: '联系方式 (可选，邮箱/微信，便于向您答复进展)',
    webFbMathLabel: '🛡️ 人机验证：',
    webFbSnapshotLabel: '附加只读环境快照 (无敏感隐私)',
    webBtnSubmitFb: '🚀 安全提交反馈',

    // Reset Confirm Modal
    webResetConfirmTitle: '恢复软件出厂默认设置？',
    webResetConfirmDesc: '此操作属于危险操作，执行后将清除所有个性化偏好且无法撤销：',
    webResetBulletHk: '• 全部全局快捷键恢复为默认初始键位',
    webResetBulletPresets: '• 6 项常用场景预设（含自定义预设）恢复出厂数值',
    webResetBulletPrefs: '• 开机自启、窗口记忆与平滑过渡偏好恢复初始状态',
    webResetBulletTheme: '• 外观主题恢复为深色，界面语言恢复为简体中文',
    webResetBtnCancel: '取消',
    webResetBtnOk: '确定恢复出厂设置'
  },

  en: {
    docTitle: 'Luna Dimmer - Dual-Track Low-Light Eye-Care & Hardware Dimming Tool',
    btnLang: '中文',
    navWorkbench: 'Control Deck',
    navFeatures: 'Dual-Track',
    navHotkeys: 'Hotkeys',
    navFaq: 'FAQ',
    navGetWin: 'Get for Windows',

    // Stage Header
    stageTitle: 'Tune your screen to just the right amount of light',
    stageCapPanel: '1:1 native Windows panel · drag to adjust',
    stageCapTelemetry: 'Live telemetry · 10–100% backlight / 1–10% overlay, seamlessly blended',
    heroDownloadCta: 'Download for Windows',

    // Control Mockup Card
    appTitle: 'Luna Dimmer',
    ctrlSettingsTip: 'Preferences & Global Hotkeys',
    ctrlMinTip: 'Minimize to System Tray',
    ctrlCloseTip: 'Exit (100% Restore Original Brightness & Color)',
    mockStatusDay: '☀️ Daylight Mode',
    mockStatusNight: '🌙 Night Eye-Care Mode',
    mockStatusSleep: '🛌 Sleep Micro-Glow (12s Pulse)',
    themeDark: '🌙 Dark',
    themeLight: '☀️ Light',
    themeGlass: '💧 Liquid Glass',
    themeToggleTip: 'Toggle Dark, Light, and Liquid Glass Themes',
    mockReset: '↺ Reset Defaults',
    mockResetTip: 'Reset brightness and warmth to system defaults',

    // Brightness & Warmth Sliders
    sliderBrightTitle: 'Screen Brightness',
    boostChipText: '⚡ 2x Boost ⚡',
    warmthTitle: 'Eye-Care Warmth',
    warmthChipText: '🌙 Night Shift',
    warmthChipTip: 'Click to toggle 50% soothing night shift eye-care mode',

    // Scene Presets
    presetsTitle: 'Scene Presets',
    presetsCustomizeBtn: '⚙️ Customize',
    presetsCustomizeTip: 'Customize preset names, target brightness, warmth & 2x boost',
    presetPills: [
      { text: '☀️ Work 90%', tip: '☀️ Daytime Work (90% Brightness / 0% Warmth)' },
      { text: '🌙 Reading 30%', tip: '🌙 Night Reading (30% Brightness / 45% Warmth)' },
      { text: '🛌 Sleep 5%', tip: '🛌 Sleep Micro-Glow (5% Brightness / 70% Warmth)' },
      { text: '☕ Break 65%', tip: '☕ Lunch Break (65% Brightness / 25% Warmth)\nLeft click: Apply preset\nRight click: Save current as preset' },
      { text: '🎨 Custom 1 50%', tip: '🎨 Custom 1 (50% Brightness / 35% Warmth)\nLeft click: Apply preset\nRight click: Save current as preset' },
      { text: '🌟 Custom 2 20%', tip: '🌟 Custom 2 (20% Brightness / 55% Warmth)\nLeft click: Apply preset\nRight click: Save current as preset' }
    ],

    // Stealth Card & Guide Bar
    stealthTitle: '🎧 Pure Blackout (Sleep & Music)',
    stealthSub: '(Press any key or wiggle mouse to wake)',
    keyboardGuideBar: 'Keyboard <kbd>←</kbd> <kbd>→</kbd> 1% fine-tuning · <kbd>Shift</kbd>+<kbd>→</kbd> 5% step',

    // Telemetry Panel
    telemetryTitle: 'Live Engineering Telemetry',
    telemetryTag: 'DDC/CI I2C + GDI Gamma',
    metricPowerLabel: 'Backlight Power',
    metricPowerBus: '● I2C Direct',
    metricPowerSaved: 'W (Saved ~0%)',
    metricHwPrefix: 'DDC/CI Hardware Register',
    metricHwSaved: 'Saved',
    metricLuxLabel: 'Luminous Flux Cut',
    metricLuxBadge: '● Eye-Care Index',
    metricLuxSub: 'Default full-light state',
    metricLuxSubDim: 'Optical filter active',
    metricOverlayLabel: 'Win32 Deep Shader',
    metricOverlayBadgeStandby: 'Standby (0.00)',
    metricOverlayBadgeActive: 'Deep Active',
    metricOverlaySub: 'WS_EX_TRANSPARENT Zero-Lag Pass',
    metricTempLabel: 'Color Curve / Blue Light Cut',
    metricTempBadge: '● Candlelight',
    metricBlueCutPrefix: 'Blue Peak Cut',
    gammaHeader: 'Gamma 2.2 Waveform Monitor',
    pipe01Label: '[PIPE-01] DDC/CI Hardware Backlight Link:',
    pipe02Label: '[PIPE-02] Win32 Zero-Lag Mouse Pass-Through:',
    pipe03Label: '[PIPE-03] 16-bit Gamma Color Transformation:',
    pipe04Label: '[PIPE-04] Non-Destructive Restore Guard:',
    pipe04Status: 'ARMED (100% Exit Auto-Restore)',

    // Bento Features
    secFeaturesTitle: 'Dual-Track Synergy: Dimmer Than Your Monitor Minimum',
    secFeaturesDesc: 'Say goodbye to glare and eye strain. A dual-track eye-care architecture built for lunch-break blackouts, late overtime and dim rooms.',
    bento1Title: 'Hardware Backlight + Deep Click-Through Shader',
    bento1Desc: 'Physical displays at 0% still leak 30~50 nits of piercing glare. Luna Dimmer employs seamless dual-track transition: 10%~100% governs physical backlight power; slipping below 10% seamlessly engages a 1%~10% micro-depth shader, eliminating glare entirely.',
    bento1BadTitle: 'Standard Software / Monitor 0%',
    bento1BadDesc: 'Still leaks ~35 nits LCD glow, harsh in pitch darkness',
    bento1GoodTitle: 'Luna Dimmer Dual-Track Dimming',
    bento1GoodDesc: 'Drops down to 1~3 nits ink micro-glow, soft as paper',
    bento2Title: 'Living Luminary Celestial Dynamic Core',
    bento2Desc: 'Mirrors the rhythm of the cosmos. Full daylight produces a golden solar corona; night mode shifts to a serene silver-white moon; sleep mode engages a 12-second starlight breathing pulse, synchronizing with natural calm.',
    bento3Title: '100% Mouse Click-Through & Zero Focus Stealing',
    bento3Desc: 'Native encapsulation with Win32 <code>WS_EX_TRANSPARENT | WS_EX_LAYERED | WS_EX_NOACTIVATE</code>. The overlay never obstructs gaming crosshairs, drag & drop, or full-screen typing—zero input lag.',
    bento4Title: 'Clean Lifecycle & Hardware Restoration Guarantee',
    bento4Desc: 'Built on non-destructive engineering principles. Upon launch, original hardware backlight and Gamma curves are snapshotted in RAM. On exit, factory display state is restored in milliseconds—never modifying registry or polluting system display profiles.',
    bento5Title: 'Keyboard Arrow Keys 1% Precision Micro-Stepping',
    bento5Desc: 'Regardless of active focus, tap ← / → keys for 1% surgical increments, or hold Shift for 5% jumps—fulfilling midnight\'s uncompromising need where 1% more is too bright, and 1% less is too dark.',

    // Hotkeys Section
    secHotkeysTitle: 'Global Blind-Operation Hotkey Workflow',
    secHotkeysDesc: 'Fine-tune anywhere without opening windows—whether watching movies, writing code, or relaxing in bed.',
    thCombo: 'Key Shortcut',
    thAction: 'Action & Effect',
    thIntent: 'Design Intent',
    hotkeyRows: [
      { act: '<b>Panic Escape: Instant Reset to System 100%</b>', intent: 'Safety failsafe in pitch darkness; restores full physical display blindfolded' },
      { act: 'Precision 1% brightness stepping (Shift for 5%)', intent: 'No need to aim with mouse; tap arrow keys directly to fine-tune' },
      { act: 'Global quick brightness tuning (5% step)', intent: 'Micro-adjust in milliseconds over full-screen games or browser apps' },
      { act: 'One-touch switch to Sleep Micro-Glow (5%)', intent: 'One press before sleep in the dark, no need to turn on lights or find mouse' },
      { act: 'One-touch Blackout (Music & downloads without glare)', intent: 'Enter 99.5% pure black mask instantly; wiggle mouse gently to wake' },
      { act: 'Night Spotlight Flashlight Beam', intent: 'Cuts a gentle flashlight aperture following cursor to inspect local text' },
      { act: 'Show / Hide Control Panel', intent: 'Toggle panel instantly at screen center or docked above system tray' },
      { act: 'Open Preferences Center', intent: 'Open settings anytime from desktop, with key capture & conflict detection' }
    ],

    // FAQ Section
    secFaqTitle: 'Frequently Asked Questions & Technical FAQ',
    secFaqDesc: 'All answers regarding low-light eye-care dimming, hardware power, and system safety.',
    faqList: [
      {
        q: 'Q: Why not just use monitor hardware buttons instead of dual-track dimming?',
        a: 'Most LCD monitors still produce 30~50 nits of glare even when physical buttons are set to 0%, causing severe eye fatigue in dark rooms. Luna Dimmer adjusts physical backlight to cut power, and seamlessly overlays a deep optical shader at 10%—making the screen vastly dimmer and softer than hardware buttons allow, gentle as ink on paper.'
      },
      {
        q: 'Q: Will there be any residual color distortion after closing or uninstalling?',
        a: 'Never. Luna Dimmer strictly adheres to non-destructive design principles: backing up system physical backlight and Gamma curves in RAM on launch, and restoring 100% original hardware states on exit or reset—zero residue, zero side effects.'
      },
      {
        q: 'Q: How do I wake up or escape anytime from extreme dimming or blackout?',
        a: 'Press global emergency shortcut <b>Ctrl + Alt + Backspace</b> (or tap Esc) anytime to instantly restore full 100% system daylight; during blackout mode, gently wiggling the mouse also smoothly wakes the screen in 1.5 seconds, eliminating sudden glare shocks.'
      }
    ],

    // Footer
    footerCopyright: '© 2026 Luna Dimmer. Released under MIT License.',
    footerPrivacy: '🛡️ 100% Offline · Zero Telemetry · Zero Tracking',

    // Preferences Modal
    prefSidebarTitle: 'Preferences',
    prefTabs: ['General & Launch', 'Optics & Eye-Care', 'Global Hotkeys', 'Safety & Reset'],
    macLblThemeTitle: 'Appearance Theme',
    macLblThemeSub: 'Seamlessly toggle between Dark, Light, and Liquid Glass',
    macThemeDark: '🌙 Dark',
    macThemeLight: '☀️ Light',
    macThemeGlass: '💧 Liquid Glass',
    macLblLang: 'Interface Language',
    macLblLangSub: 'Real-time dynamic redraw, no restart required',
    macLblAutostart: 'Start silently in background on system boot',
    macLblAutostartSub: 'Silently minimize to system tray after Windows login',
    macLblRememberPos: 'Remember last dragged panel position',
    macLblRememberPosSub: 'When disabled, auto-docks above system tray upon launch',
    macLblAutoUpdate: 'Automatically check for updates on launch',
    macLblAutoUpdateSub: 'Silently checks for updates in the background',
    macLblFullscreenGuard: 'Suppress focus stealing during full-screen games/apps',
    macLblFullscreenGuardSub: 'Hotkeys adjust brightness smoothly without interrupting games or video',
    macLblCloudVer: 'Current Version: V1.0.0',
    macLblOfficialSite: 'Official Website',
    macBtnVisitSite: '🌐 Visit Website',
    macLblContactQQ: 'Developer QQ / Contact',
    macBtnCopyQQ: '📋 Copy',
    btnMacCheckUpdate: '🔄 Check Updates',

    // Tab 1: Optics
    macLblHwChannel: 'Current Display Dimming Method:',
    macLblHwChannelSub: 'Directly controls display backlight via DDC/CI I2C hardware bus',
    macLblHwReady: '🟢 Hardware Physical Backlight (DDC/CI Supported)',
    macLblSmoothWake: 'Enable 1.5s smooth fade-in on screen wake (anti-glare)',
    macLblSmoothWakeSub: 'Gradually increases brightness on wake to prevent blinding glare',

    // Tab 2: Hotkeys
    macLblHkGroup: 'Global Hotkey Settings (Click keycap to record)',
    macBtnResetHk: '↺ Restore Default Hotkeys',
    macHkList: {
      up: '☀️ Quick Brighten (+5%)',
      down: '🌙 Quick Dim (-5%)',
      sleep: '🛌 Toggle Sleep Mode (5%)',
      stealth: '🎧 Toggle Screen Blackout',
      spotlight: '🔦 Toggle Spotlight Flashlight',
      panel: '🎛️ Toggle Control Panel',
      settings: '⚙️ Open Preferences Panel',
      emergency: '🚨 Emergency 100% Daylight (Panic Failsafe)'
    },

    // Tab 3: Safety & Reset
    macLblSafetyTitle: 'Clean & Non-Destructive Operation Guarantee',
    macLblSafety: 'Safe & non-destructive: Upon exit or crash, original physical brightness and warmth are 100% restored automatically without modifying registry. Independent watchdog process monitors main PID for millisecond self-healing.',
    macLblFbTitle: 'Feedback & Bug Reports',
    macLblFbSub: 'Encountered an issue or have suggestions? Reach out anytime',
    macBtnOpenFb: 'Submit Feedback',
    macLblSponsorTitle: 'Developer Support & Care',
    macLblSponsorSub: 'A heartfelt letter written late at night from the dev team',
    macBtnOpenSponsor: '☕ Support Devs',
    macLblResetTitle: 'Reset to Factory Defaults',
    macLblResetSub: 'Reset all optics, preferences, autostart, and hotkeys to factory defaults',
    macBtnResetAll: 'Restore Defaults',
    macLblAutoSave: '✓ Preferences active and auto-saved',
    macBtnDone: 'Done',

    // Preset Customizer Modal
    webPresetModalTitle: '🎨 Customize Scene Presets',
    webPresetTabs: ['☀️ Work', '🌙 Night', '🛌 Sleep', '☕ Break', '🎨 Custom 1', '🌟 Custom 2'],
    webPresetLblName: 'Preset Display Name',
    webPresetLblNameSub: 'Label shown in main control panel and menus',
    webPresetLblBright: 'Target Brightness',
    webPresetLblBrightSub: 'Display physical backlight and micro-glow for this scene',
    webPresetLblWarmth: 'Night Shift Warmth',
    webPresetLblWarmthSub: 'Warm amber tint filtering high-energy short-wave blue light',
    webPresetLblBoost: '2x Boost Deep Filter',
    webPresetLblBoostSub: 'Breaks hardware physical minimum for night micro-aperture',
    webPresetBtnCapture: '📍 Capture Current Screen',
    webPresetBtnPreview: '👁️ Live Preview',
    webPresetBtnReset: '↺ Restore Factory Defaults',
    webPresetTip: '✓ Changes will sync to the main panel automatically',
    webPresetBtnCancel: 'Cancel',
    webPresetBtnSave: '💾 Save & Apply',

    // Feedback Modal
    webFbModalTitle: '💬 Feedback & Bug Report (V1.0.0)',
    webFbLblCategory: 'Category:',
    webFbOptions: [
      '🐛 Bug Report',
      '💡 Feature Request',
      '🖥️ Monitor Hardware Issue'
    ],
    webFbDescPlaceholder: 'Please describe the scenario, monitor model, or suggestions (10~500 chars)...',
    webFbContactPlaceholder: 'Contact info (Optional: Email, for follow-up)',
    webFbMathLabel: '🛡️ Human Verification:',
    webFbSnapshotLabel: 'Attach read-only environment snapshot (privacy-safe)',
    webBtnSubmitFb: '🚀 Submit Feedback Safely',

    // Reset Confirm Modal
    webResetConfirmTitle: 'Restore Factory Defaults?',
    webResetConfirmDesc: 'This is a dangerous operation. All custom preferences and configurations will be permanently reset:',
    webResetBulletHk: '• All global hotkeys will be reset to default bindings',
    webResetBulletPresets: '• All 6 scene presets (including custom presets) will be reset',
    webResetBulletPrefs: '• Autostart, window memory, and smooth transitions will reset',
    webResetBulletTheme: '• Appearance theme will reset to Dark, and language to Simplified Chinese',
    webResetBtnCancel: 'Cancel',
    webResetBtnOk: 'Reset All Settings'
  }
};

/**
 * 切换中英双语核心函数 (100% 全要素动态无缝热重绘)
 */
function toggleLanguage() {
  // 语言切换唯一实现：委托给 setMacLanguage，避免两套状态变更路径
  setMacLanguage(currentLang === 'zh' ? 'en' : 'zh');
}

function setMacLanguage(lang) {
  if (currentLang !== lang) {
    currentLang = lang;
    applyLanguage(lang);
  }
  const zhBtn = document.getElementById('macLangZhBtn');
  const enBtn = document.getElementById('macLangEnBtn');
  if (zhBtn && enBtn) {
    zhBtn.classList.toggle('active', lang === 'zh');
    enBtn.classList.toggle('active', lang === 'en');
  }
}

function applyLanguage(lang) {
  document.documentElement.lang = lang === 'zh' ? 'zh-CN' : 'en-US';
  const d = I18N_DATA[lang];
  if (!d) return;

  // 1. Document Title
  if (d.docTitle) document.title = d.docTitle;

  // 2. Stage Header
  const brandTitle = document.getElementById('brandTitle');
  if (brandTitle) brandTitle.textContent = d.appTitle;
  const stageTitle = document.getElementById('stageMainTitle') || document.querySelector('.stage-main-title');
  if (stageTitle) stageTitle.textContent = d.stageTitle;

  // 4. Control Mockup Card
  const appTitle = document.getElementById('luminaryTitle');
  if (appTitle) appTitle.textContent = d.appTitle;

  const btnSettings = document.getElementById('btnMockSettings') || document.querySelector('.ctrl-settings');
  if (btnSettings) btnSettings.title = d.ctrlSettingsTip;
  const btnMin = document.getElementById('btnMockMin') || document.querySelector('.ctrl-min');
  if (btnMin) btnMin.title = d.ctrlMinTip;
  const btnClose = document.getElementById('btnMockClose') || document.querySelector('.ctrl-close');
  if (btnClose) btnClose.title = d.ctrlCloseTip;

  const pillTheme = document.getElementById('btnThemeTogglePill');
  if (pillTheme) {
    const curTheme = (typeof window.currentWebTheme === 'string') ? window.currentWebTheme : 'dark';
    if (curTheme === 'light') pillTheme.textContent = d.themeLight;
    else if (curTheme === 'liquid_glass') pillTheme.textContent = d.themeGlass;
    else pillTheme.textContent = d.themeDark;
    pillTheme.title = d.themeToggleTip;
  }

  const btnReset = document.getElementById('btnMockReset') || document.querySelector('.btn-mock-reset');
  if (btnReset) {
    btnReset.textContent = d.mockReset;
    btnReset.title = d.mockResetTip;
  }

  // Brightness & Warmth Meta
  const brightMeta = document.getElementById('lblBrightMeta');
  if (brightMeta) brightMeta.textContent = d.sliderBrightTitle;
  const chip2xSpan = document.querySelector('#boostChip span');
  if (chip2xSpan) chip2xSpan.textContent = d.boostChipText;

  const warmthMeta = document.getElementById('lblWarmthMeta');
  if (warmthMeta) warmthMeta.textContent = d.warmthTitle;
  const warmthChipSpan = document.querySelector('#warmthChip span');
  if (warmthChipSpan) warmthChipSpan.textContent = d.warmthChipText;
  const warmthChip = document.getElementById('warmthChip');
  if (warmthChip) warmthChip.title = d.warmthChipTip;

  // Presets Header & Pills
  const presetsHeader = document.getElementById('lblPresetsHeader');
  if (presetsHeader) presetsHeader.textContent = d.presetsTitle;
  const presetsCustomBtn = document.getElementById('btnPresetsCustomize') || document.querySelector('.btn-mock-custom');
  if (presetsCustomBtn) {
    presetsCustomBtn.textContent = d.presetsCustomizeBtn;
    presetsCustomBtn.title = d.presetsCustomizeTip;
  }

  const pills = document.querySelectorAll('.presets-row .preset-pill');
  if (pills && pills.length >= 6 && d.presetPills) {
    for (let i = 0; i < 6; i++) {
      if (pills[i] && d.presetPills[i]) {
        pills[i].textContent = d.presetPills[i].text;
        pills[i].title = d.presetPills[i].tip;
      }
    }
  }

  // Stealth Action Card
  const stealthTitle = document.querySelector('.stealth-action-title');
  if (stealthTitle) stealthTitle.textContent = d.stealthTitle;
  const stealthSub = document.querySelector('.stealth-action-sub');
  if (stealthSub) stealthSub.textContent = d.stealthSub;

  const guideBar = document.getElementById('keyboardGuideBar') || document.querySelector('.keyboard-guide-bar');
  if (guideBar) guideBar.innerHTML = d.keyboardGuideBar;

  // 5. Telemetry Panel
  const telemTitle = document.querySelector('.telemetry-title');
  if (telemTitle) telemTitle.textContent = d.telemetryTitle;
  const telemTag = document.querySelector('.telemetry-tag');
  if (telemTag) telemTag.textContent = d.telemetryTag;

  const metricPowerLabel = document.getElementById('metricPowerLabel');
  if (metricPowerLabel) metricPowerLabel.textContent = d.metricPowerLabel;
  const metricHwBusStatus = document.getElementById('metricHwBusStatus');
  if (metricHwBusStatus) metricHwBusStatus.textContent = d.metricPowerBus;

  const metricLuxLabel = document.getElementById('metricLuxLabel');
  if (metricLuxLabel) metricLuxLabel.textContent = d.metricLuxLabel;
  const metricLuxBadge = document.getElementById('metricLuxBadge');
  if (metricLuxBadge) metricLuxBadge.textContent = d.metricLuxBadge;

  const metricOverlayLabel = document.getElementById('metricOverlayLabel');
  if (metricOverlayLabel) metricOverlayLabel.textContent = d.metricOverlayLabel;
  const metricOverlaySub = document.getElementById('metricOverlaySub');
  if (metricOverlaySub) metricOverlaySub.textContent = d.metricOverlaySub;

  const metricTempLabel = document.getElementById('metricTempLabel');
  if (metricTempLabel) metricTempLabel.textContent = d.metricTempLabel;
  const metricTempBadge = document.getElementById('metricTempBadge');
  if (metricTempBadge) metricTempBadge.textContent = d.metricTempBadge;

  const gammaHeaderTitle = document.getElementById('gammaHeaderTitle');
  if (gammaHeaderTitle) gammaHeaderTitle.textContent = d.gammaHeader;

  const pipe01 = document.getElementById('pipe01Label');
  if (pipe01) pipe01.textContent = d.pipe01Label;
  const pipe02 = document.getElementById('pipe02Label');
  if (pipe02) pipe02.textContent = d.pipe02Label;
  const pipe03 = document.getElementById('pipe03Label');
  if (pipe03) pipe03.textContent = d.pipe03Label;
  const pipe04 = document.getElementById('pipe04Label');
  if (pipe04) pipe04.textContent = d.pipe04Label;
  const pipeSentinel = document.getElementById('pipeSentinelStatus');
  if (pipeSentinel) pipeSentinel.textContent = d.pipe04Status;

  // 6. Bento Features Matrix
  const secFeaturesTitle = document.getElementById('secFeaturesTitle');
  if (secFeaturesTitle) secFeaturesTitle.textContent = d.secFeaturesTitle;
  const secFeaturesDesc = document.getElementById('secFeaturesDesc');
  if (secFeaturesDesc) secFeaturesDesc.textContent = d.secFeaturesDesc;

  const b1Title = document.getElementById('bento1Title');
  if (b1Title) b1Title.textContent = d.bento1Title;
  const b1Desc = document.getElementById('bento1Desc');
  if (b1Desc) b1Desc.textContent = d.bento1Desc;
  const b1BadT = document.getElementById('bento1BadTitle');
  if (b1BadT) b1BadT.textContent = d.bento1BadTitle;
  const b1BadD = document.getElementById('bento1BadDesc');
  if (b1BadD) b1BadD.textContent = d.bento1BadDesc;
  const b1GoodT = document.getElementById('bento1GoodTitle');
  if (b1GoodT) b1GoodT.textContent = d.bento1GoodTitle;
  const b1GoodD = document.getElementById('bento1GoodDesc');
  if (b1GoodD) b1GoodD.textContent = d.bento1GoodDesc;

  const b2Title = document.getElementById('bento2Title');
  if (b2Title) b2Title.textContent = d.bento2Title;
  const b2Desc = document.getElementById('bento2Desc');
  if (b2Desc) b2Desc.textContent = d.bento2Desc;

  const b3Title = document.getElementById('bento3Title');
  if (b3Title) b3Title.textContent = d.bento3Title;
  const b3Desc = document.getElementById('bento3Desc');
  if (b3Desc) b3Desc.innerHTML = d.bento3Desc;

  const b4Title = document.getElementById('bento4Title');
  if (b4Title) b4Title.textContent = d.bento4Title;
  const b4Desc = document.getElementById('bento4Desc');
  if (b4Desc) b4Desc.textContent = d.bento4Desc;

  const b5Title = document.getElementById('bento5Title');
  if (b5Title) b5Title.textContent = d.bento5Title;
  const b5Desc = document.getElementById('bento5Desc');
  if (b5Desc) b5Desc.textContent = d.bento5Desc;

  // 7. Global Hotkeys Section
  const secHotkeysTitle = document.getElementById('secHotkeysTitle');
  if (secHotkeysTitle) secHotkeysTitle.textContent = d.secHotkeysTitle;
  const secHotkeysDesc = document.getElementById('secHotkeysDesc');
  if (secHotkeysDesc) secHotkeysDesc.textContent = d.secHotkeysDesc;

  const thCombo = document.getElementById('thCombo');
  if (thCombo) thCombo.textContent = d.thCombo;
  const thAction = document.getElementById('thAction');
  if (thAction) thAction.textContent = d.thAction;
  const thIntent = document.getElementById('thIntent');
  if (thIntent) thIntent.textContent = d.thIntent;

  if (d.hotkeyRows) {
    for (let r = 1; r <= 8; r++) {
      const rowData = d.hotkeyRows[r - 1];
      if (rowData) {
        const actEl = document.getElementById(`hkRow${r}Act`);
        if (actEl) actEl.innerHTML = rowData.act;
        const intentEl = document.getElementById(`hkRow${r}Intent`);
        if (intentEl) intentEl.textContent = rowData.intent;
      }
    }
  }

  // 8. FAQ Section
  const secFaqTitle = document.getElementById('secFaqTitle');
  if (secFaqTitle) secFaqTitle.textContent = d.secFaqTitle;
  const secFaqDesc = document.getElementById('secFaqDesc');
  if (secFaqDesc) secFaqDesc.textContent = d.secFaqDesc;

  if (d.faqList) {
    for (let f = 1; f <= 3; f++) {
      const item = d.faqList[f - 1];
      if (item) {
        const qEl = document.getElementById(`faqQ${f}`);
        if (qEl) qEl.innerHTML = item.q;
        const aEl = document.getElementById(`faqA${f}`);
        if (aEl) aEl.innerHTML = item.a;
      }
    }
  }

  // 9. Preferences Modal Elements
  const sideTitle = document.getElementById('webSidebarTitle');
  if (sideTitle) sideTitle.textContent = d.prefSidebarTitle;

  for (let i = 0; i < 4; i++) {
    const navTxt = document.getElementById(`macNavTxt${i}`);
    if (navTxt && d.prefTabs && d.prefTabs[i]) navTxt.textContent = d.prefTabs[i];
  }

  const themeTitle = document.getElementById('macLblThemeTitle');
  if (themeTitle) themeTitle.textContent = d.macLblThemeTitle;
  const themeSub = document.getElementById('macLblThemeSub');
  if (themeSub) themeSub.textContent = d.macLblThemeSub;
  const themeDarkBtn = document.getElementById('macThemeDarkBtn');
  if (themeDarkBtn) themeDarkBtn.textContent = d.macThemeDark;
  const themeLightBtn = document.getElementById('macThemeLightBtn');
  if (themeLightBtn) themeLightBtn.textContent = d.macThemeLight;
  const themeGlassBtn = document.getElementById('macThemeGlassBtn');
  if (themeGlassBtn) themeGlassBtn.textContent = d.macThemeGlass;

  const langTitle = document.getElementById('macLblLang');
  if (langTitle) langTitle.textContent = d.macLblLang;
  const langSub = document.getElementById('macLblLangSub');
  if (langSub) langSub.textContent = d.macLblLangSub;

  const autostart = document.getElementById('macLblAutostart');
  if (autostart) autostart.textContent = d.macLblAutostart;
  const autostartSub = document.getElementById('macLblAutostartSub');
  if (autostartSub) autostartSub.textContent = d.macLblAutostartSub;

  const rememberPos = document.getElementById('macLblRememberPos');
  if (rememberPos) rememberPos.textContent = d.macLblRememberPos;
  const rememberPosSub = document.getElementById('macLblRememberPosSub');
  if (rememberPosSub) rememberPosSub.textContent = d.macLblRememberPosSub;

  const autoUpdate = document.getElementById('macLblAutoUpdate');
  if (autoUpdate) autoUpdate.textContent = d.macLblAutoUpdate;
  const autoUpdateSub = document.getElementById('macLblAutoUpdateSub');
  if (autoUpdateSub) autoUpdateSub.textContent = d.macLblAutoUpdateSub;

  const fsGuard = document.getElementById('macLblFullscreenGuard');
  if (fsGuard) fsGuard.textContent = d.macLblFullscreenGuard;
  const fsGuardSub = document.getElementById('macLblFullscreenGuardSub');
  if (fsGuardSub) fsGuardSub.textContent = d.macLblFullscreenGuardSub;

  const cloudVer = document.getElementById('macLblCloudVer');
  if (cloudVer) cloudVer.textContent = d.macLblCloudVer;
  const btnCheckUp = document.getElementById('btnMacCheckUpdate');
  if (btnCheckUp) btnCheckUp.textContent = d.btnMacCheckUpdate;
  const siteLbl = document.getElementById('macLblOfficialSite');
  if (siteLbl) siteLbl.textContent = d.macLblOfficialSite;
  const siteBtn = document.getElementById('btnMacVisitSite');
  if (siteBtn) siteBtn.textContent = d.macBtnVisitSite;
  const qqLbl = document.getElementById('macLblContactQQ');
  if (qqLbl) qqLbl.textContent = d.macLblContactQQ;
  const qqBtn = document.getElementById('btnMacCopyQQ');
  if (qqBtn) qqBtn.textContent = d.macBtnCopyQQ;

  // Preferences Tab 1
  const hwChan = document.getElementById('macLblHwChannel');
  if (hwChan) hwChan.textContent = d.macLblHwChannel;
  const hwChanSub = document.getElementById('macLblHwChannelSub');
  if (hwChanSub) hwChanSub.textContent = d.macLblHwChannelSub;
  const hwReady = document.getElementById('macLblHwReady');
  if (hwReady) hwReady.textContent = d.macLblHwReady;
  const smoothWake = document.getElementById('macLblSmoothWake');
  if (smoothWake) smoothWake.textContent = d.macLblSmoothWake;
  const smoothWakeSub = document.getElementById('macLblSmoothWakeSub');
  if (smoothWakeSub) smoothWakeSub.textContent = d.macLblSmoothWakeSub;

  // Preferences Tab 2
  const hkGroup = document.getElementById('macLblHkGroup');
  if (hkGroup) hkGroup.textContent = d.macLblHkGroup;
  const btnResetHk = document.getElementById('macBtnResetHk');
  if (btnResetHk) btnResetHk.textContent = d.macBtnResetHk;

  const hkUp = document.getElementById('macHkUp');
  if (hkUp) hkUp.textContent = d.macHkList.up;
  const hkDown = document.getElementById('macHkDown');
  if (hkDown) hkDown.textContent = d.macHkList.down;
  const hkSleep = document.getElementById('macHkSleep');
  if (hkSleep) hkSleep.textContent = d.macHkList.sleep;
  const hkStealth = document.getElementById('macHkStealth');
  if (hkStealth) hkStealth.textContent = d.macHkList.stealth;
  const hkSpotlight = document.getElementById('macHkSpotlight');
  if (hkSpotlight) hkSpotlight.textContent = d.macHkList.spotlight;
  const hkPanel = document.getElementById('macHkPanel');
  if (hkPanel) hkPanel.textContent = d.macHkList.panel;
  const hkSettings = document.getElementById('macHkSettings');
  if (hkSettings) hkSettings.textContent = d.macHkList.settings;
  const hkEmergency = document.getElementById('macHkEmergency');
  if (hkEmergency) hkEmergency.textContent = d.macHkList.emergency;

  // Preferences Tab 3
  const safetyTitle = document.getElementById('macLblSafetyTitle');
  if (safetyTitle) safetyTitle.textContent = d.macLblSafetyTitle;
  const safety = document.getElementById('macLblSafety');
  if (safety) safety.textContent = d.macLblSafety;
  const fbTitle = document.getElementById('macLblFbTitle');
  if (fbTitle) fbTitle.textContent = d.macLblFbTitle;
  const fbSub = document.getElementById('macLblFbSub');
  if (fbSub) fbSub.textContent = d.macLblFbSub;
  const btnFb = document.getElementById('macBtnOpenFb');
  if (btnFb) btnFb.textContent = d.macBtnOpenFb;
  const spTitle = document.getElementById('macLblSponsorTitle');
  if (spTitle) spTitle.textContent = d.macLblSponsorTitle;
  const spSub = document.getElementById('macLblSponsorSub');
  if (spSub) spSub.textContent = d.macLblSponsorSub;
  const btnSp = document.getElementById('macBtnOpenSponsor');
  if (btnSp) btnSp.textContent = d.macBtnOpenSponsor;
  const resetTitle = document.getElementById('macLblResetTitle');
  if (resetTitle) resetTitle.textContent = d.macLblResetTitle;
  const resetSub = document.getElementById('macLblResetSub');
  if (resetSub) resetSub.textContent = d.macLblResetSub;
  const btnResetAll = document.getElementById('macBtnResetAll');
  if (btnResetAll) btnResetAll.textContent = d.macBtnResetAll;

  const autoSave = document.getElementById('macLblAutoSave');
  if (autoSave) autoSave.textContent = d.macLblAutoSave;
  const btnDone = document.getElementById('macBtnDone');
  if (btnDone) btnDone.textContent = d.macBtnDone;

  // Preset Customizer Modal
  const modalPresetTitle = document.getElementById('webPresetModalTitle');
  if (modalPresetTitle) modalPresetTitle.textContent = d.webPresetModalTitle;

  const presetTabKeys = ['Work', 'Night', 'Sleep', 'Noon', 'Custom1', 'Custom2'];
  for (let p = 0; p < 6; p++) {
    const tabBtn = document.getElementById(`webPresetTab${presetTabKeys[p]}`);
    if (tabBtn && d.webPresetTabs && d.webPresetTabs[p]) {
      tabBtn.textContent = d.webPresetTabs[p];
    }
  }

  const pName = document.getElementById('webPresetLblName');
  if (pName) pName.textContent = d.webPresetLblName;
  const pNameSub = document.getElementById('webPresetLblNameSub');
  if (pNameSub) pNameSub.textContent = d.webPresetLblNameSub;
  const pBright = document.getElementById('webPresetLblBright');
  if (pBright) pBright.textContent = d.webPresetLblBright;
  const pBrightSub = document.getElementById('webPresetLblBrightSub');
  if (pBrightSub) pBrightSub.textContent = d.webPresetLblBrightSub;
  const pWarmth = document.getElementById('webPresetLblWarmth');
  if (pWarmth) pWarmth.textContent = d.webPresetLblWarmth;
  const pWarmthSub = document.getElementById('webPresetLblWarmthSub');
  if (pWarmthSub) pWarmthSub.textContent = d.webPresetLblWarmthSub;
  const pBoost = document.getElementById('webPresetLblBoost');
  if (pBoost) pBoost.textContent = d.webPresetLblBoost;
  const pBoostSub = document.getElementById('webPresetLblBoostSub');
  if (pBoostSub) pBoostSub.textContent = d.webPresetLblBoostSub;

  const pBtnCap = document.getElementById('webPresetBtnCapture');
  if (pBtnCap) pBtnCap.textContent = d.webPresetBtnCapture;
  const pBtnPrev = document.getElementById('webPresetBtnPreview');
  if (pBtnPrev) pBtnPrev.textContent = d.webPresetBtnPreview;
  const pBtnReset = document.getElementById('webPresetBtnReset');
  if (pBtnReset) pBtnReset.textContent = d.webPresetBtnReset;
  const pTip = document.getElementById('webPresetCustomizerTip');
  if (pTip) pTip.textContent = d.webPresetTip;
  const pBtnCancel = document.getElementById('webPresetBtnCancel');
  if (pBtnCancel) pBtnCancel.textContent = d.webPresetBtnCancel;
  const pBtnSave = document.getElementById('webPresetBtnSave');
  if (pBtnSave) pBtnSave.textContent = d.webPresetBtnSave;

  // Feedback Modal
  const fbModalTitle = document.getElementById('webFbModalTitle');
  if (fbModalTitle) fbModalTitle.textContent = d.webFbModalTitle;
  const fbCategory = document.getElementById('webFbLblCategory');
  if (fbCategory) fbCategory.textContent = d.webFbLblCategory;
  const optBug = document.getElementById('webFbOptBug');
  if (optBug && d.webFbOptions) optBug.textContent = d.webFbOptions[0];
  const optReq = document.getElementById('webFbOptReq');
  if (optReq && d.webFbOptions) optReq.textContent = d.webFbOptions[1];
  const optHw = document.getElementById('webFbOptHw');
  if (optHw && d.webFbOptions) optHw.textContent = d.webFbOptions[2];

  const fbDesc = document.getElementById('webFbDesc');
  if (fbDesc) fbDesc.placeholder = d.webFbDescPlaceholder;
  const fbContact = document.getElementById('webFbContact');
  if (fbContact) fbContact.placeholder = d.webFbContactPlaceholder;
  const fbMath = document.getElementById('webFbMathLabel');
  if (fbMath) fbMath.textContent = d.webFbMathLabel;
  const fbSnap = document.getElementById('webFbSnapshotLabel');
  if (fbSnap) fbSnap.textContent = d.webFbSnapshotLabel;
  const btnSubFb = document.getElementById('webBtnSubmitFb');
  if (btnSubFb) btnSubFb.textContent = d.webBtnSubmitFb;

  // Reset Confirm Modal
  const rTitle = document.getElementById('webResetConfirmTitle');
  if (rTitle) rTitle.textContent = d.webResetConfirmTitle;
  const rDesc = document.getElementById('webResetConfirmDesc');
  if (rDesc) rDesc.textContent = d.webResetConfirmDesc;
  const rHk = document.getElementById('webResetBulletHk');
  if (rHk) rHk.textContent = d.webResetBulletHk;
  const rPresets = document.getElementById('webResetBulletPresets');
  if (rPresets) rPresets.textContent = d.webResetBulletPresets;
  const rPrefs = document.getElementById('webResetBulletPrefs');
  if (rPrefs) rPrefs.textContent = d.webResetBulletPrefs;
  const rTheme = document.getElementById('webResetBulletTheme');
  if (rTheme) rTheme.textContent = d.webResetBulletTheme;
  const rCancel = document.getElementById('webResetBtnCancel');
  if (rCancel) rCancel.textContent = d.webResetBtnCancel;
  const rOk = document.getElementById('webResetBtnOk');
  if (rOk) rOk.textContent = d.webResetBtnOk;

  // Footer / any element marked with data-i18n
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    if (key && d[key]) el.textContent = d[key];
  });

  // Re-sync Preferences Active Tab Header
  if (typeof switchMacPrefTab === 'function') {
    switchMacPrefTab(typeof currentMacTab !== 'undefined' ? currentMacTab : 0);
  }

  // Update Telemetry & Luminary Display with Current Language
  if (typeof updateDisplay === 'function') {
    updateDisplay();
  }
}

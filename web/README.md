# Luna Dimmer - 网页端前端工程化与资源管理

本目录为 **Luna Dimmer** 官方 Web 演示与遥测平台的前端工程化模块目录。  
前端核心样式表、JavaScript 逻辑模块以及静态资源均存放于此，页面主入口为项目根目录的 [`index.html`](../index.html)。

---

## 目录结构

```
LunaDimmer/
├── index.html            # 🌟 全项目唯一前端主入口 (引入 web/css/ 与 web/js/)
└── web/                  # 网页端核心资产与逻辑层
    ├── css/              # 样式层 (CSS Stylesheets)
    │   ├── style.css     # 全局骨架：重置、排版与基础按钮
    │   ├── themes.css    # 🌙 深色 (Dark)、☀️ 浅色 (Light)、💧 液态玻璃 (Liquid Glass) 三套主题
    │   ├── modals.css    # 设置/赞赏/反馈/场景预设/危险确认等模态卡片
    │   ├── animations.css# 滚动入场、微光掠影、聚光跟随等动效
    │   └── luna.css      # ⭐ Moonlight Optical Stage 版式 + 1:1 原生控制面板 + 月光主题（最后加载，最终权威）
    ├── js/               # 行为逻辑层 (JavaScript Modules)
    │   ├── i18n.js       # 简体中文 (zh-CN) 与英文 (en-US) 国际化字典与即时切换
    │   ├── simulator.js  # 双轨调光仿真、Gamma 曲线、1:1 面板滑块交互、主题与 Toast 唯一入口
    │   ├── presets.js    # 6 组场景预设与自定义管理器
    │   ├── modals.js     # 偏好设置、赞赏、反馈、出厂重置与唯一键盘入口
    │   └── interactions.js# 滚动视差、星尘画布、聚光跟随、程序化音效
    ├── assets/           # 静态资源层 (Assets)
    │   └── icon.png      # 高清应用超椭圆图标
    └── README.md         # 本工程化架构设计与管理说明文档
```

> **首屏规范（RFC-30 / RFC-32）**：打开 `index.html` 第一屏即为「左侧 1:1 还原 Windows 原生高刷微晶控制面板」，
> 面板严格按 474 × 608 桌面窗口占位（446 × 576 卡片 + 14/16 外窗留白）等比缩放；**右侧为实时工程遥测控制台，与面板等高并置**，
> 拖动滑块即可同步看到功耗 / 光通量 / 遮罩 / 色温与 Gamma 曲线变化；窄屏按「页头 → 面板 → 遥测」堆叠。
> 主题三态由 `window.currentWebTheme` 单一状态驱动，`web/css/luna.css` 为页面外观的最终权威。

---

## 模块职责说明

### 1. 样式层 (`css/`)
- **`style.css`**：
  - 定义全局重置、CSS 变量与苹果超细发丝分割线；
  - 承载全局重置、CSS 变量与基础按钮骨架（不再负责导航、页脚、首屏工作台与遥测组件）；
  - 不再 `@import` 其他样式表，全部由 `index.html` 显式 `<link>` 按顺序加载。
- **`themes.css`**：
  - 独立管理 **🌙 深色 (Dark)**、**☀️ 浅色 (Light)** 与 **💧 液态玻璃 (Liquid Glass)** 主题色盘；
  - 涵盖卡片背景渐变、文字对比度、发光高亮、磨砂微透与阴影阶梯。
- **`modals.css`**：
  - 封装 Apple macOS Ventura / Sonoma 原生风格弹出卡片与毛玻璃遮罩；
  - 包含三色信号灯、左侧胶囊导航、微动开关、分段选择器与通知 Toast 样式。
- **`luna.css`**：
  - 首屏 App-First 双栏版式：左侧 1:1 面板、右侧品牌叙事 + 遥测；
  - 月光主题设计代币（深空 / 月晕 / 星尘 / 琥珀月华）与浅色、液态玻璃三态；
  - 面板组件严格对齐 PyQt 桌面端：44px 胶囊轨道、24px 芯片、38px 场景药丸、54px 挂机磁贴、24px 圆角。
- **`animations.css`**：
  - `[data-reveal]` 双向滚动入场、`.has-spotlight` 鼠标微光跟随、滚动吸顶过渡。

### 2. 行为逻辑层 (`js/`)
- **`i18n.js`**：
  - 提供全局 `I18N_DATA` 字典与 `currentLang` 语言状态；
  - 语言切换唯一入口 `setMacLanguage(lang)`；`toggleLanguage()` 只负责委托，不复制状态变更逻辑。
- **`simulator.js`**：
  - 承载 `currentBrightness`、`currentWarmth`、`isBoost` 等全局状态；
  - 实现真实物理亮度与软件叠加穿透的双轨衰减算法仿真；
  - 绘制 60FPS RGB Gamma 动态校准曲线与 Living Luminary 昼夜灵动光球；
  - **全站唯一通知** `showWebToast()` 与**唯一主题入口** `setWebTheme()`（写入 `window.currentWebTheme`，同步 `body` 与 `.luna-control-card`）；
  - 方向键仅在指针悬停 / 面板聚焦时调光，避免劫持页面滚动。
- **`presets.js`**：
  - 管理 6 个场景预设（白天办公 90%、夜间阅读 30%、睡前极暗 5%、午间休息 65%、自定义 1、自定义 2）；
  - 参数读取、实时预览、右键捕获与修改持久化；
  - **药丸渲染唯一入口** `renderPresetPills()`，与 `saveWebPreset()` 一并供弹窗复用。
- **`modals.js`**：
  - 控制系统偏好设置、全局快捷键捕获录制；
  - 昼夜节律 5 阶段心意信、防刷人机验证反馈、恢复出厂二次确认；
  - **唯一键盘入口**：一个 `keydown` 监听同时处理录制捕获与 Esc 分层关闭；
  - 不再定义主题切换、Toast、预设保存等已由其他模块负责的能力。
- **`interactions.js`**：
  - 滚动状态、锚点平滑滚动、滚动入场、微光跟随、星尘 Canvas、程序化音效。

> **单一实现铁律**：同一能力只允许一份实现（详见 `docs/DESIGN.md` §6.3）。
> 多入口（面板快捷按钮 / 设置弹窗）必须复用同一个函数，禁止复制函数体或维护第二份状态。

---

## 访问与运行方式

1. **直接双击访问**：
   - 直接在浏览器中双击打开根目录下的 `index.html` 即可完整离线脱机运行。
2. **静态服务器托管**：
   - 支持通过任意 HTTP 服务托管（如 VS Code Live Server、Python `python -m http.server`、GitHub Pages 等）。

/**
 * Luna Dimmer - 创新交互与高定动效引擎 (Next-Gen Interactive Suite)
 * Inspired by Apple HIG, Linear.app, Raycast, and OpenAI Astra Dynamics
 */

(function () {
  'use strict';

  // =========================================================================
  // 1. 顶栏滚动流光感知与全域光影视差 (Scroll Dynamics & Parallax)
  // =========================================================================
  function initNavAndScrollProgress() {
    const ambientEl = document.getElementById('ambientGlow');
    let ticking = false;

    function updateScrollState() {
      const scrollTop = window.pageYOffset || document.documentElement.scrollTop;

      // 1. 吸顶导航背景与阴影融合
      if (scrollTop > 24) {
        document.body.classList.add('scrolled');
      } else {
        document.body.classList.remove('scrolled');
      }

      // 2. 背景环境光微视差深潜 (Cosmic Ambient Parallax)
      if (ambientEl) {
        const yOffset = Math.min(65, scrollTop * 0.12);
        ambientEl.style.setProperty('--ambient-y', `${yOffset.toFixed(1)}px`);
      }

      ticking = false;
    }

    function onScroll() {
      if (!ticking) {
        requestAnimationFrame(updateScrollState);
        ticking = true;
      }
    }

    window.addEventListener('scroll', onScroll, { passive: true });
    updateScrollState();

    // 导航栏锚点点击精准平滑滚动（完全规避吸顶导航遮挡内容）
    document.querySelectorAll('.nav-actions a[href^="#"]').forEach(anchor => {
      anchor.addEventListener('click', function (e) {
        const targetId = this.getAttribute('href');
        if (!targetId || targetId === '#') return;
        const targetEl = document.querySelector(targetId);
        if (targetEl) {
          e.preventDefault();
          const headerOffset = 76;
          const elementPosition = targetEl.getBoundingClientRect().top;
          const offsetPosition = elementPosition + window.pageYOffset - headerOffset;

          window.scrollTo({
            top: offsetPosition,
            behavior: 'smooth'
          });

          // 同步更新 URL hash，不触发突变
          try {
            history.pushState(null, '', targetId);
          } catch (_) {}
        }
      });
    });
  }

  // =========================================================================
  // 2. 双向滚动微距进出场系统 (GPU-Accelerated Zero-Blur Reveal System)
  // =========================================================================
  function initScrollReveal() {
    const revealEls = document.querySelectorAll('[data-reveal]');
    if (!revealEls.length) return;

    if (!('IntersectionObserver' in window)) {
      revealEls.forEach(el => el.classList.add('is-revealed'));
      return;
    }

    const observer = new IntersectionObserver((entries, obs) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-revealed');
          
          // 首次进入视口为卡片注入微光掠影初始坐标
          if (entry.target.classList.contains('has-spotlight') && !entry.target.dataset.spotlightInit) {
            entry.target.dataset.spotlightInit = '1';
            entry.target.style.setProperty('--mouse-x', '50%');
            entry.target.style.setProperty('--mouse-y', '20px');
          }
        }
      });
    }, {
      threshold: 0.12,
      rootMargin: '0px 0px -30px 0px'
    });

    revealEls.forEach(el => {
      // 若元素在首屏视口内直接无延迟激活，杜绝白屏等待
      const rect = el.getBoundingClientRect();
      if (rect.top < window.innerHeight && rect.bottom > 0) {
        el.classList.add('is-revealed');
      }
      observer.observe(el);
    });
  }

  // =========================================================================
  // 3. Linear / Raycast 级光感鼠标动态追踪与微晶边框折射 (Spotlight Tracking)
  // =========================================================================
  function initSpotlightTracking() {
    const spotlightTargets = document.querySelectorAll('.has-spotlight');
    if (!spotlightTargets.length) return;

    spotlightTargets.forEach(card => {
      let isHovered = false;

      card.addEventListener('pointerenter', () => {
        isHovered = true;
      });

      card.addEventListener('pointermove', e => {
        if (!isHovered) return;
        const rect = card.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        card.style.setProperty('--mouse-x', `${x.toFixed(1)}px`);
        card.style.setProperty('--mouse-y', `${y.toFixed(1)}px`);
      }, { passive: true });

      card.addEventListener('pointerleave', () => {
        isHovered = false;
        card.style.setProperty('--mouse-x', `-999px`);
        card.style.setProperty('--mouse-y', `-999px`);
      });
    });
  }

  // =========================================================================
  // 3.5. 纯算法 Web Audio 触觉音效合成器 (Zero-Asset Procedural Audio Synthesizer)
  // =========================================================================
  const SoundFX = {
    ctx: null,
    enabled: true,
    lastTickTime: 0,
    init() {
      if (!this.ctx && (window.AudioContext || window.webkitAudioContext)) {
        const AudioCtx = window.AudioContext || window.webkitAudioContext;
        this.ctx = new AudioCtx();
      }
      if (this.ctx && this.ctx.state === 'suspended') {
        this.ctx.resume();
      }
    },
    tick(freq = 1350) {
      if (!this.enabled) return;
      const now = performance.now();
      if (now - this.lastTickTime < 45) return; // 节流防撕裂
      this.lastTickTime = now;
      try {
        this.init();
        if (!this.ctx) return;
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();
        osc.type = 'sine';
        osc.frequency.setValueAtTime(freq, this.ctx.currentTime);
        gain.gain.setValueAtTime(0.016, this.ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.0001, this.ctx.currentTime + 0.035);
        osc.connect(gain);
        gain.connect(this.ctx.destination);
        osc.start();
        osc.stop(this.ctx.currentTime + 0.038);
      } catch (_) {}
    },
    preset() {
      if (!this.enabled) return;
      try {
        this.init();
        if (!this.ctx) return;
        const t = this.ctx.currentTime;
        [587.33, 880.00].forEach((freq, i) => {
          const osc = this.ctx.createOscillator();
          const gain = this.ctx.createGain();
          osc.type = 'sine';
          osc.frequency.setValueAtTime(freq, t + i * 0.045);
          gain.gain.setValueAtTime(0.022, t + i * 0.045);
          gain.gain.exponentialRampToValueAtTime(0.0001, t + i * 0.045 + 0.22);
          osc.connect(gain);
          gain.connect(this.ctx.destination);
          osc.start(t + i * 0.045);
          osc.stop(t + i * 0.045 + 0.23);
        });
      } catch (_) {}
    },
    stealth() {
      if (!this.enabled) return;
      try {
        this.init();
        if (!this.ctx) return;
        const t = this.ctx.currentTime;
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();
        osc.type = 'sine';
        osc.frequency.setValueAtTime(110, t);
        osc.frequency.exponentialRampToValueAtTime(28, t + 0.45);
        gain.gain.setValueAtTime(0.038, t);
        gain.gain.exponentialRampToValueAtTime(0.0001, t + 0.5);
        osc.connect(gain);
        gain.connect(this.ctx.destination);
        osc.start(t);
        osc.stop(t + 0.52);
      } catch (_) {}
    },
    wake() {
      if (!this.enabled) return;
      try {
        this.init();
        if (!this.ctx) return;
        const t = this.ctx.currentTime;
        [440, 659.25, 880].forEach((freq, i) => {
          const osc = this.ctx.createOscillator();
          const gain = this.ctx.createGain();
          osc.type = 'sine';
          osc.frequency.setValueAtTime(freq, t + i * 0.05);
          gain.gain.setValueAtTime(0.024, t + i * 0.05);
          gain.gain.exponentialRampToValueAtTime(0.0001, t + i * 0.05 + 0.26);
          osc.connect(gain);
          gain.connect(this.ctx.destination);
          osc.start(t + i * 0.05);
          osc.stop(t + i * 0.05 + 0.28);
        });
      } catch (_) {}
    }
  };
  window.LunaSound = SoundFX;

  window.toggleWebSound = function() {
    if (!window.LunaSound) return;
    window.LunaSound.enabled = !window.LunaSound.enabled;
    const btn = document.getElementById('btn-sound-toggle');
    if (btn) {
      const isZh = (typeof currentLang === 'undefined' || currentLang === 'zh');
      if (window.LunaSound.enabled) {
        btn.textContent = isZh ? '🔊 触感音效' : '🔊 Audio FX';
        window.LunaSound.wake();
      } else {
        btn.textContent = isZh ? '🔇 静音模式' : '🔇 Muted';
      }
    }
  };

  // =========================================================================
  // 4. 静谧星尘背景画布 (Ambient Starlight Background Canvas)
  // =========================================================================
  function initHeroCosmicCanvas() {
    const canvas = document.getElementById('heroCosmicCanvas');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let width = 0;
    let height = 0;
    let particles = [];
    let animationFrameId = null;
    let isVisible = true;

    function resize() {
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
      initParticles();
    }

    function initParticles() {
      particles = [];
      const count = Math.floor(Math.min(48, Math.max(22, width / 34)));
      for (let i = 0; i < count; i++) {
        particles.push({
          x: Math.random() * width,
          y: Math.random() * height,
          vx: (Math.random() - 0.5) * 0.15,
          vy: -(Math.random() * 0.22 + 0.08),
          radius: Math.random() * 1.5 + 0.5,
          baseAlpha: Math.random() * 0.35 + 0.12,
          alpha: 0.2,
          pulseSpeed: Math.random() * 0.015 + 0.006,
          pulseVal: Math.random() * Math.PI * 2
        });
      }
    }

    function render() {
      if (!isVisible) return;

      ctx.clearRect(0, 0, width, height);

      // 读取当前全局调光状态，动态计算星尘能量密度与色谱
      const bRatio = (typeof window.currentBrightness === 'number' ? window.currentBrightness : 100) / 100.0;
      const wRatio = (typeof window.currentWarmth === 'number' ? window.currentWarmth : 0) / 100.0;
      const energyFactor = 0.35 + bRatio * 0.65;

      const r = Math.round(56 + (245 - 56) * wRatio);
      const g = Math.round(189 + (179 - 189) * wRatio);
      const b = Math.round(248 + (56 - 248) * wRatio);
      const colorPrefix = `rgba(${r}, ${g}, ${b}, `;

      const pLen = particles.length;

      for (let i = 0; i < pLen; i++) {
        const p = particles[i];
        p.pulseVal += p.pulseSpeed;
        p.alpha = (p.baseAlpha + Math.sin(p.pulseVal) * 0.10) * energyFactor;

        p.x += p.vx * energyFactor;
        p.y += p.vy * energyFactor;

        if (p.y < -15) {
          p.y = height + 10;
          p.x = Math.random() * width;
        }
        if (p.x < -15) p.x = width + 10;
        if (p.x > width + 15) p.x = -10;

        const safeAlpha = Math.max(0, p.alpha);

        // 外层微光晕
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.radius * 2.0, 0, Math.PI * 2);
        ctx.fillStyle = colorPrefix + (safeAlpha * 0.18).toFixed(3) + ')';
        ctx.fill();

        // 核心星尘粒子
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(255, 255, 255, ${(safeAlpha * 0.85).toFixed(3)})`;
        ctx.fill();
      }

      animationFrameId = requestAnimationFrame(render);
    }

    if ('IntersectionObserver' in window) {
      const obs = new IntersectionObserver(([entry]) => {
        isVisible = entry.isIntersecting;
        if (isVisible && !animationFrameId) {
          render();
        } else if (!isVisible && animationFrameId) {
          cancelAnimationFrame(animationFrameId);
          animationFrameId = null;
        }
      });
      obs.observe(canvas);
    }

    window.addEventListener('resize', resize, { passive: true });
    resize();
    render();
  }

  // =========================================================================
  // 5. 动态获取最新 Release 下载链接 (Dynamic Latest Release Download)
  // =========================================================================
  async function initDynamicReleaseDownload() {
    const btn = document.getElementById('btnHeroDownload');
    if (!btn) return;

    const isZh = (navigator.language || '').toLowerCase().startsWith('zh');

    // 辅助函数：统一设置下载按钮
    function applyDownloadLink(versionTag, rawUrl, filename) {
      const cleanVer = versionTag.replace(/^v/, '');
      const fastUrl = isZh ? `https://ghfast.top/${rawUrl}` : rawUrl;
      btn.href = fastUrl;
      btn.setAttribute('download', filename || `LunaDimmer_v${cleanVer}.exe`);
      const label = document.getElementById('btnHeroDownloadLabel') || btn.querySelector('.dl-label');
      if (label) {
        label.textContent = isZh ? `下载 Windows 免安装版 (v${cleanVer})` : `Download for Windows (v${cleanVer})`;
      }
      btn.title = `Luna Dimmer v${cleanVer} · Windows 10 / 11 · 免安装 · 100% 纯净`;
    }

    // 优先级 1：直接从 GitHub API 获取真实最新发布的 Release（永不落后）
    try {
      const ghController = new AbortController();
      const ghTimeout = setTimeout(() => ghController.abort(), 3500);
      const ghRes = await fetch('https://api.github.com/repos/Fugui-Dai/LunaDimmer/releases/latest', {
        signal: ghController.signal,
        headers: { 'Accept': 'application/vnd.github.v3+json' }
      });
      clearTimeout(ghTimeout);

      if (ghRes.ok) {
        const ghData = await ghRes.json();
        const assets = ghData.assets || [];
        const exeAsset = assets.find(a => a.name && a.name.endsWith('.exe')) || assets[0];
        if (exeAsset && exeAsset.browser_download_url) {
          applyDownloadLink(ghData.tag_name || 'v1.0.4', exeAsset.browser_download_url, exeAsset.name);
          return;
        }
      }
    } catch (e) {
      // 官方接口超时，降级到 CDN 镜像探测
    }

    // 优先级 2：同源部署的 version.json 静态高可用配置
    try {
      const res = await fetch('./version.json?t=' + Date.now(), { cache: 'no-cache' });
      if (res.ok) {
        const data = await res.json();
        if (data && data.version) {
          const rawUrl = data.download_url || `https://github.com/Fugui-Dai/LunaDimmer/releases/download/v${data.version}/LunaDimmer_v${data.version}.exe`;
          applyDownloadLink(data.version, rawUrl, `LunaDimmer_v${data.version}.exe`);
          return;
        }
      }
    } catch (e) {
      // 降级到镜像探测
    }

    // 优先级 3：国内加速镜像 API 容灾探测
    try {
      const mirrorRes = await fetch('https://ghfast.top/https://api.github.com/repos/Fugui-Dai/LunaDimmer/releases/latest');
      if (mirrorRes.ok) {
        const ghData = await mirrorRes.json();
        const assets = ghData.assets || [];
        const exeAsset = assets.find(a => a.name && a.name.endsWith('.exe')) || assets[0];
        if (exeAsset && exeAsset.browser_download_url) {
          applyDownloadLink(ghData.tag_name || 'v1.0.4', exeAsset.browser_download_url, exeAsset.name);
          return;
        }
      }
    } catch (e) {
      // 忽略，降级到终极兜底
    }

    // 优先级 3：终极保底（直接提供稳定直链，绝不跳网页）
    const fallbackUrl = isZh
      ? 'https://ghfast.top/https://github.com/Fugui-Dai/LunaDimmer/releases/download/v1.0.1/LunaDimmer_v1.0.4.exe'
      : 'https://github.com/Fugui-Dai/LunaDimmer/releases/download/v1.0.1/LunaDimmer_v1.0.4.exe';
    btn.href = fallbackUrl;
    btn.setAttribute('download', 'LunaDimmer_v1.0.4.exe');
  }

  // =========================================================================
  // 6. 初始化引导 (Bootstrap)
  // =========================================================================
  document.addEventListener('DOMContentLoaded', () => {
    initNavAndScrollProgress();
    initScrollReveal();
    initSpotlightTracking();
    initHeroCosmicCanvas();
    initDynamicReleaseDownload();
  });

})();

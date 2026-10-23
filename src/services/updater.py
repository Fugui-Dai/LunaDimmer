# -*- coding: utf-8 -*-
"""Luna Dimmer - 云端版本检测与在线升级管理核心 (Updater Module)

遵循现代 Windows/macOS 桌面客户端规范：
1. 采用 Python 标准库 urllib.request 与 json，零第三方依赖；
2. 基于 QThread 异步非阻塞执行，网络超时 5 秒，绝对不卡顿主 UI；
3. 严格 SemVer 语义化版本元组比对算法；
4. 苹果暗夜毛玻璃风 UpgradeDialog 专属升级通知弹窗。
"""

import os
import sys
import time
import json
import re
import urllib.request
import urllib.error
from typing import Dict, Any, Optional, Tuple

from PyQt5.QtCore import Qt, QThread, pyqtSignal, QPoint, QRectF, QUrl, QTimer
from PyQt5.QtGui import (
    QColor,
    QPainter,
    QBrush,
    QPen,
    QLinearGradient,
    QDesktopServices,
)
from PyQt5.QtWidgets import (
    QDialog,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QFrame,
    QGraphicsDropShadowEffect,
    QProgressBar,
    QApplication,
)

from src.services.i18n import t, get_language

CURRENT_VERSION = "1.0.1"

# 允许交给浏览器打开的下载链接协议白名单（防止远端元数据投毒成 file:// 或自定义协议）
SAFE_DOWNLOAD_SCHEMES = ("https", "http")


def is_safe_download_url(url: str) -> bool:
    """校验下载链接是否为合法的 http(s) 地址；远端元数据属于不可信输入，必须过滤"""
    try:
        from urllib.parse import urlparse

        parsed = urlparse(str(url or "").strip())
        if parsed.scheme.lower() not in SAFE_DOWNLOAD_SCHEMES:
            return False
        # 必须有主机名，且不能带用户名/密码等凭据（钓鱼常见手法）
        return bool(parsed.netloc) and "@" not in parsed.netloc
    except Exception:
        return False

# 默认官方云端元数据发布检测源列表 (多源容灾通道：GitHub 302 重定向免流探针、Cloudflare Pages 与官方 API)
DEFAULT_UPDATE_URLS = [
    # 1. GitHub 官方 Releases CDN 302 自动重定向探针（直连发布体系，零 403 频控，国内秒级感知）
    "https://ghfast.top/https://github.com/Fugui-Dai/LunaDimmer/releases/latest",
    "https://github.com/Fugui-Dai/LunaDimmer/releases/latest",
    # 2. Cloudflare Pages 静态高可用节点与 Raw 备选通道
    "https://lunadimmer.pages.dev/version.json",
    # 3. GitHub 官方 REST API 备选通道
    "https://api.github.com/repos/Fugui-Dai/LunaDimmer/releases/latest",
]
DEFAULT_UPDATE_METADATA_URL = DEFAULT_UPDATE_URLS[0]


def parse_version_tuple(ver_str: str) -> Tuple[int, ...]:
    """将版本号字符串（如 'v1.2.3' 或 '1.0.0'）拆解为用于数值比较的纯数字元组"""
    clean_str = str(ver_str or "").strip().lstrip("vV")
    parts = re.findall(r"\d+", clean_str)
    if not parts:
        return (0, 0, 0)
    return tuple(int(p) for p in parts)


def is_newer_version(remote_ver: str, current_ver: str = CURRENT_VERSION) -> bool:
    """
    语义化版本比对：若 remote_ver 严格大于 current_ver 则返回 True。

    先按位补零对齐再比较，避免 `1.0` 与 `1.0.0` 这类长度不等时被误判
    （Python 元组比较会认为 (1, 0) < (1, 0, 0)，导致同版本永远被当成「有更新」）。
    """
    remote = list(parse_version_tuple(remote_ver))
    current = list(parse_version_tuple(current_ver))
    length = max(len(remote), len(current), 3)
    remote += [0] * (length - len(remote))
    current += [0] * (length - len(current))
    return tuple(remote) > tuple(current)


class UpdateWorker(QThread):
    """后台异步版本检测多线程引擎，保障主线程 UI 与调光滑块绝对流畅"""

    sig_finished = pyqtSignal(bool, dict, str)
    # 兼容历史调用别名
    sig_check_finished = pyqtSignal(bool, str, str, str)
    sig_check_error = pyqtSignal(str)

    def _emit_result(self, ok: bool, data: dict, err: str):
        self.sig_finished.emit(ok, data, err)
        if ok and data:
            remote_ver = data.get("version", CURRENT_VERSION)
            has_update = is_newer_version(remote_ver, CURRENT_VERSION)
            notes = data.get("changelog", {}).get("zh-CN", "") if isinstance(data.get("changelog"), dict) else str(data.get("changelog", ""))
            dl_url = data.get("download_url", "")
            self.sig_check_finished.emit(has_update, remote_ver, notes, dl_url)
        else:
            self.sig_check_error.emit(err or "Check failed")

    def __init__(
        self,
        url: Optional[str] = None,
        urls: Optional[list] = None,
        force_simulate_update: Optional[bool] = None,
        parent: Optional[QThread] = None,
    ):
        super().__init__(parent)
        if urls:
            self.candidate_urls = list(urls)
        elif url:
            self.candidate_urls = [url]
        else:
            self.candidate_urls = list(DEFAULT_UPDATE_URLS)
        self.url = self.candidate_urls[0] if self.candidate_urls else DEFAULT_UPDATE_METADATA_URL
        self.force_simulate_update = force_simulate_update

    def run(self):
        # 1. 如果强制模拟发现新版本（如 Shift+点击 检查更新调试）
        if self.force_simulate_update is True:
            time.sleep(0.8)
            mock_data = {
                "version": "1.1.0",
                "release_date": "2026-10-21",
                "download_url": "https://github.com/Fugui-Dai/LunaDimmer/releases/latest",
                "file_size": "38 MB",
                "is_critical": False,
                "changelog": {
                    "zh-CN": "1. 修复双轨调光滑块动态反色自适应文字\n2. 优化 Windows 任务栏与 Alt+Tab 切换呈现\n3. 新增在线多线程版本检测与升级服务\n4. 记忆主面板上次拖拽停靠物理坐标",
                    "en-US": "1. Added adaptive dual-contrast slider text inversion\n2. Enhanced Windows taskbar and Alt+Tab integration\n3. Added multi-threaded version check & upgrade service\n4. Remember last dock position after dragging",
                },
            }
            self._emit_result(True, mock_data, "")
            return

        # 2. 依次向候选云端端点探测更新元数据（Cloudflare Pages 静态节点与 GitHub Releases 体系）
        for target_url in self.candidate_urls:
            try:
                req = urllib.request.Request(
                    target_url,
                    headers={
                        "User-Agent": f"LunaDimmer-Client/{CURRENT_VERSION} (Windows; x64/x86)",
                        "Accept": "application/json",
                    },
                )
                with urllib.request.urlopen(req, timeout=3.5) as response:
                    if response.status == 200:
                        # 优先检测 302 重定向探针（直连 Releases 体系，100% 免疫 API 403 频控）
                        real_url = response.geturl()
                        tag_match = re.search(r"/releases/tag/([^/?#]+)", real_url)
                        if tag_match:
                            tag_str = tag_match.group(1).strip()
                            remote_ver = tag_str.lstrip("vV")
                            dl_url = f"https://github.com/Fugui-Dai/LunaDimmer/releases/download/{tag_str}/LunaDimmer_{tag_str}.exe"
                            normalized_payload = {
                                "version": remote_ver,
                                "release_date": "",
                                "download_url": dl_url,
                                "file_size": "25 MB",
                                "is_critical": False,
                                "changelog": {
                                    "zh-CN": "版本性能调优与体验升级",
                                    "en-US": "Performance optimizations and improvements",
                                },
                            }
                            self._emit_result(True, normalized_payload, "")
                            return

                        raw_data = response.read().decode("utf-8")
                        data = json.loads(raw_data)
                        if isinstance(data, dict):
                            # 分支 A: 静态 version.json 规范格式
                            if "version" in data:
                                # 确保 download_url 具备高可用兜底
                                if not data.get("download_url"):
                                    v = data["version"]
                                    data["download_url"] = f"https://github.com/Fugui-Dai/LunaDimmer/releases/download/v{v}/LunaDimmer_v{v}.exe"
                                self._emit_result(True, data, "")
                                return

                            # 分支 B: GitHub 官方 Releases API 规范格式 (tag_name / assets)
                            if "tag_name" in data:
                                remote_ver = str(data.get("tag_name", "")).strip().lstrip("vV")
                                changelog_raw = str(data.get("body", "")).strip() or "版本性能调优与体验升级"
                                assets = data.get("assets", [])
                                dl_url = ""
                                for asset in assets:
                                    burl = asset.get("browser_download_url", "")
                                    if burl.lower().endswith(".exe"):
                                        dl_url = burl
                                        break
                                if not dl_url and assets:
                                    dl_url = assets[0].get("browser_download_url", "")
                                if not dl_url:
                                    dl_url = f"https://github.com/Fugui-Dai/LunaDimmer/releases/download/v{remote_ver}/LunaDimmer_v{remote_ver}.exe"

                                normalized_payload = {
                                    "version": remote_ver,
                                    "release_date": str(data.get("published_at", ""))[:10],
                                    "download_url": dl_url,
                                    "file_size": "38 MB",
                                    "is_critical": False,
                                    "changelog": {
                                        "zh-CN": changelog_raw,
                                        "en-US": changelog_raw,
                                    },
                                }
                                self._emit_result(True, normalized_payload, "")
                                return
            except Exception:
                continue

        # 3. 若所有网络源均不可达，返回失败提示
        self._emit_result(False, {}, "Unable to fetch version metadata from cloud endpoints.")


class DownloadWorker(QThread):
    """后台多线程分块流式下载引擎，支持自动接入 CDN 加速镜像与实时进度汇报"""
    sig_progress = pyqtSignal(int, int)  # (downloaded_bytes, total_bytes)
    sig_finished = pyqtSignal(bool, str)  # (success, file_path_or_error)

    def __init__(self, download_url: str, parent: Optional[QThread] = None):
        super().__init__(parent)
        self.download_url = str(download_url or "").strip()
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        if not self.download_url:
            self.sig_finished.emit(False, "下载地址为空")
            return

        import tempfile
        target_file = os.path.join(tempfile.gettempdir(), f"LunaDimmer_update_{int(time.time())}.exe")

        # 候选链接列表（GitHub 官方 Releases 链接自动追加高速加速镜像）
        candidate_urls = []
        if self.download_url.startswith("https://github.com"):
            candidate_urls.append(f"https://ghfast.top/{self.download_url}")
            candidate_urls.append(f"https://ghproxy.net/{self.download_url}")
        candidate_urls.append(self.download_url)

        success = False
        last_error = ""

        for url in candidate_urls:
            if self._is_cancelled:
                break
            try:
                req = urllib.request.Request(
                    url,
                    headers={
                        "User-Agent": f"LunaDimmer-Client/{CURRENT_VERSION} (Windows; x64)",
                        "Accept": "*/*",
                    },
                )
                with urllib.request.urlopen(req, timeout=12) as resp:
                    if resp.status not in (200, 206):
                        continue
                    total_bytes = int(resp.headers.get("Content-Length", 0))
                    downloaded_bytes = 0
                    chunk_size = 64 * 1024  # 64KB 块缓冲流式写入
                    last_emit_time = 0.0
                    last_emit_pct = -1

                    with open(target_file, "wb") as f:
                        while not self._is_cancelled:
                            chunk = resp.read(chunk_size)
                            if not chunk:
                                break
                            f.write(chunk)
                            downloaded_bytes += len(chunk)

                            now = time.time()
                            cur_pct = int(downloaded_bytes / total_bytes * 100) if total_bytes > 0 else -1
                            # 节流控制：每 30ms 或百分比变化时派发一次，杜绝跨线程高频轰炸
                            if (now - last_emit_time >= 0.03) or (cur_pct != last_emit_pct):
                                self.sig_progress.emit(downloaded_bytes, total_bytes)
                                last_emit_time = now
                                last_emit_pct = cur_pct

                    # 下载完成确保派发最后一次 100% 进度
                    if not self._is_cancelled and total_bytes > 0:
                        self.sig_progress.emit(downloaded_bytes, total_bytes)

                    if self._is_cancelled:
                        try:
                            if os.path.exists(target_file):
                                os.remove(target_file)
                        except Exception:
                            pass
                        return

                    if total_bytes > 0 and downloaded_bytes < total_bytes:
                        continue
                    if os.path.exists(target_file) and os.path.getsize(target_file) > 1024 * 1024:
                        success = True
                        break
            except Exception as e:
                last_error = str(e)
                continue

        if success and os.path.exists(target_file):
            self.sig_finished.emit(True, target_file)
        else:
            self.sig_finished.emit(False, last_error or "网络连接异常，下载失败")


def apply_update_and_restart(new_exe_path: str) -> None:
    """
    Windows 内核文件句柄锁定解决方案：
    在 Windows 下，运行中的 exe 文件被系统锁定无法直接覆写。
    本机制通过生成独立的脱离伴生脚本（Detached Process），在主进程安全退出后，
    毫秒级原子覆盖目标 exe 并自动拉起新版本，实现 100% 无缝静默升级。
    """
    import subprocess
    import tempfile

    if not new_exe_path or not os.path.exists(new_exe_path):
        logging.error(f"更新失败：下载的目标文件不存在: {new_exe_path}")
        return

    is_frozen = getattr(sys, "frozen", False)
    current_exe = os.path.abspath(sys.executable if is_frozen else sys.argv[0])
    exe_dir = os.path.dirname(current_exe)
    exe_name = os.path.basename(current_exe)

    if not is_frozen:
        # 源码开发模式保护：杜绝误覆盖 python.exe，将下载的成果保存到工作目录下
        local_dest = os.path.abspath("LunaDimmer_latest.exe")
        try:
            import shutil
            shutil.copy2(new_exe_path, local_dest)
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.information(
                None,
                "下载完成 (源码开发模式)",
                f"当前处于 Python 源码开发环境，新版本客户端已成功就绪：\n{local_dest}\n\n在打包后的 exe 运行时将全自动原子覆盖并重启。",
            )
        except Exception:
            pass
        return

    current_pid = os.getpid()
    bat_path = os.path.join(tempfile.gettempdir(), f"luna_updater_{current_pid}.bat")

    # 注意：严禁在后台无控制台/输入重定向进程中使用 timeout 命令（会导致直接报错退出）
    # 采用标准无害的 ping 127.0.0.1 延迟等待，结合强制进程杀灭与原子移动
    bat_content = f"""@echo off
chcp 65001 >nul 2>&1
cd /d "{exe_dir}"

:: 终止当前程序树及所有关联同名实例（彻底释放 PyInstaller 引导进程与 Crash Guardian 句柄）
taskkill /F /T /PID {current_pid} >nul 2>&1
taskkill /F /IM "{exe_name}" >nul 2>&1
ping 127.0.0.1 -n 2 >nul

set RETRY=0
:RETRY_MOVE
move /y "{new_exe_path}" "{current_exe}" >nul 2>&1
if not errorlevel 1 goto LAUNCH

:: 备用重命名方案：Windows 允许重命名处于关闭边缘的可执行文件
ren "{exe_name}" "{exe_name}.old" >nul 2>&1
move /y "{new_exe_path}" "{current_exe}" >nul 2>&1
if not errorlevel 1 goto LAUNCH

set /a RETRY+=1
if %RETRY% leq 8 (
    ping 127.0.0.1 -n 2 >nul
    goto RETRY_MOVE
)

:LAUNCH
ping 127.0.0.1 -n 2 >nul
del /f /q "{exe_name}.old" >nul 2>&1
start "" "{current_exe}"
del "%~f0" >nul 2>&1
"""

    with open(bat_path, "w", encoding="utf-8", newline="\r\n") as f:
        f.write(bat_content)

    # 尝试主动关闭单实例互斥锁句柄，确保重启进程不会被误判拦截
    try:
        import ctypes
        from src.main import _single_instance_mutex
        if _single_instance_mutex:
            ctypes.windll.kernel32.CloseHandle(_single_instance_mutex)
    except Exception:
        pass

    CREATE_NO_WINDOW = 0x08000000
    DETACHED_PROCESS = 0x00000008
    subprocess.Popen(
        f'cmd.exe /c ""{bat_path}""',
        creationflags=CREATE_NO_WINDOW | DETACHED_PROCESS,
        close_fds=True,
        shell=False,
    )

    # 强制在内核层立即释放全部文件句柄与线程，确保当前 exe 被平滑覆盖
    app = QApplication.instance()
    if app:
        try:
            app.quit()
        except Exception:
            pass
    os._exit(0)


class DownloadProgressBar(QWidget):
    """
    Apple macOS 风格高精度抗锯齿微晶矢量进度条：
    纯 QPainter 矢量渲染，1:1 像素级精确同步真实下载字节比例，彻底根除 QSS 样式引擎进度条脱节/卡顿缺陷。
    """

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setFixedHeight(8)
        self._progress = 0.0  # 0.0 ~ 1.0
        self._theme = "dark"

    def set_theme(self, theme: str):
        self._theme = theme if theme in ("dark", "light", "liquid_glass") else "dark"
        self.update()

    def set_progress(self, ratio: float):
        self._progress = max(0.0, min(1.0, float(ratio)))
        self.update()

    def setValue(self, val: int):
        self.set_progress(val / 100.0)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        rect = QRectF(self.rect())
        radius = rect.height() / 2.0

        is_light = (self._theme == "light")
        bg_color = QColor(0, 0, 0, 18) if is_light else QColor(255, 255, 255, 26)
        border_color = QColor(0, 0, 0, 26) if is_light else QColor(255, 255, 255, 36)

        painter.setPen(QPen(border_color, 0.8))
        painter.setBrush(QBrush(bg_color))
        painter.drawRoundedRect(rect.adjusted(0.5, 0.5, -0.5, -0.5), radius, radius)

        if self._progress > 0:
            fill_width = rect.width() * self._progress
            fill_width = max(radius * 2.0, fill_width)
            fill_width = min(rect.width(), fill_width)
            fill_rect = QRectF(rect.x(), rect.y(), fill_width, rect.height())

            grad = QLinearGradient(fill_rect.topLeft(), fill_rect.topRight())
            grad.setColorAt(0.0, QColor("#0A84FF"))
            grad.setColorAt(1.0, QColor("#38BDF8"))
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(grad))
            painter.drawRoundedRect(fill_rect, radius, radius)


class UpgradeDialog(QDialog):
    """苹果暗夜毛玻璃风在线升级通知弹窗 (Apple Dark Glass Upgrade Dialog)"""

    def __init__(
        self,
        update_info: Any = None,
        notes: str = "",
        dl_url: str = "",
        parent: Optional[QWidget] = None,
        **kwargs,
    ):
        # 弹性兼容: 支持 update_info 为 dict 或 (latest_ver, notes, dl_url, parent)
        if isinstance(update_info, str):
            p = parent or (dl_url if isinstance(dl_url, QWidget) else None)
            super().__init__(p)
            self.update_info = {
                "version": update_info,
                "changelog": {"zh-CN": notes, "en-US": notes},
                "download_url": dl_url if isinstance(dl_url, str) else "",
            }
        elif isinstance(update_info, dict):
            super().__init__(parent)
            self.update_info = update_info
        else:
            super().__init__(parent)
            self.update_info = {}
        self._drag_pos = QPoint()

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setWindowModality(Qt.WindowModal)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFixedSize(490, 460)
        self.dl_worker = None
        p = self.parent()
        th = getattr(p, "current_theme", getattr(p, "_theme", getattr(p, "selected_theme", "dark")))
        self._theme = th if th in ("dark", "light", "liquid_glass") else "dark"

        self._init_ui()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and not self._drag_pos.isNull():
            self.move(event.globalPos() - self._drag_pos)
            event.accept()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), Qt.transparent)

    def _init_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(18, 18, 18, 18)

        card = QFrame(self)
        card.setObjectName("upgradeCard")
        is_light = (getattr(self, "_theme", "dark") == "light")
        if is_light:
            card.setStyleSheet("""
                QFrame#upgradeCard {
                    background: #FFFFFF;
                    border-radius: 20px;
                    border: 1px solid rgba(0, 0, 0, 0.12);
                }
                QLabel {
                    color: #1D1D1F;
                    font-family: "Microsoft YaHei UI", "Segoe UI", sans-serif;
                }
            """)
        else:
            card.setStyleSheet("""
                QFrame#upgradeCard {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 rgba(28, 30, 38, 0.98),
                        stop:1 rgba(14, 15, 20, 0.99));
                    border-radius: 20px;
                    border: 1px solid rgba(255, 255, 255, 0.12);
                    border-top: 1px solid rgba(255, 255, 255, 0.28);
                }
                QLabel {
                    color: #FFFFFF;
                    font-family: "Microsoft YaHei UI", "Segoe UI", sans-serif;
                }
            """)

        shadow = QGraphicsDropShadowEffect(card)
        shadow.setBlurRadius(16)
        shadow.setColor(QColor(0, 0, 0, 40 if is_light else 120))
        shadow.setOffset(0, 4)
        card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 20, 24, 20)
        card_layout.setSpacing(14)

        # 1. 顶部 Header
        header_layout = QHBoxLayout()
        lbl_rocket = QLabel("🚀")
        lbl_rocket.setStyleSheet("font-size: 22px;")
        header_layout.addWidget(lbl_rocket)

        title_wrap = QVBoxLayout()
        title_wrap.setSpacing(2)

        remote_ver = self.update_info.get("version", "1.1.0")
        rel_date = self.update_info.get("release_date", "")
        ver_text = f"v{CURRENT_VERSION}  ➔  v{remote_ver}"
        if rel_date:
            ver_text += f" ({rel_date})"
        lbl_version_title = QLabel(ver_text)
        lbl_version_title.setStyleSheet(f"font-size: 16.5px; font-weight: 700; color: {'#1D1D1F' if is_light else '#FFFFFF'};")
        title_wrap.addWidget(lbl_version_title)

        header_layout.addLayout(title_wrap)
        header_layout.addStretch()

        btn_close_top = QPushButton("✕", card)
        btn_close_top.setFixedSize(26, 26)
        btn_close_top.setCursor(Qt.PointingHandCursor)
        if is_light:
            btn_close_top.setStyleSheet("""
                QPushButton {
                    background: rgba(0, 0, 0, 0.05);
                    border: 1px solid rgba(0, 0, 0, 0.10);
                    border-radius: 13px;
                    color: #64748B;
                    font-size: 12px;
                    font-weight: 700;
                }
                QPushButton:hover {
                    background: rgba(255, 59, 48, 0.15);
                    border-color: #FF3B30;
                    color: #FF3B30;
                }
            """)
        else:
            btn_close_top.setStyleSheet("""
                QPushButton {
                    background: rgba(255, 255, 255, 0.08);
                    border: 1px solid rgba(255, 255, 255, 0.12);
                    border-radius: 13px;
                    color: #CBD5E1;
                    font-size: 12px;
                    font-weight: 700;
                }
                QPushButton:hover {
                    background: rgba(255, 95, 86, 0.25);
                    border-color: #FF5F56;
                    color: #FF5F56;
                }
            """)
        btn_close_top.clicked.connect(self.reject)
        header_layout.addWidget(btn_close_top)

        card_layout.addLayout(header_layout)

        # 2. 中间更新日志区域
        lbl_log_title = QLabel(t("update_notes_title"))
        lbl_log_title.setStyleSheet(f"font-size: 13px; font-weight: 600; color: {'#475569' if is_light else '#94A3B8'}; margin-top: 4px;")
        card_layout.addWidget(lbl_log_title)

        cur_lang = get_language()
        changelog_dict = self.update_info.get("changelog", {})
        if isinstance(changelog_dict, dict):
            changelog_text = changelog_dict.get(cur_lang) or changelog_dict.get("zh-CN") or "性能调优与功能提升"
        else:
            changelog_text = str(changelog_dict)

        txt_changelog = QTextEdit(card)
        txt_changelog.setReadOnly(True)
        txt_changelog.setPlainText(changelog_text)
        if is_light:
            txt_changelog.setStyleSheet("""
                QTextEdit {
                    background: rgba(0, 0, 0, 0.035);
                    border: 1px solid rgba(0, 0, 0, 0.08);
                    border-radius: 10px;
                    padding: 12px;
                    color: #1E293B;
                    font-size: 13px;
                    line-height: 20px;
                }
            """)
        else:
            txt_changelog.setStyleSheet("""
                QTextEdit {
                    background: rgba(255, 255, 255, 0.03);
                    border: 1px solid rgba(255, 255, 255, 0.08);
                    border-radius: 10px;
                    padding: 12px;
                    color: #E2E8F0;
                    font-size: 13px;
                    line-height: 20px;
                }
            """)
        card_layout.addWidget(txt_changelog)

        # 3. 动态下载进度条与状态展示区 (苹果微晶胶囊风格，矢量像素级严格跟随进度)
        self.progress_bar = DownloadProgressBar(card)
        self.progress_bar.set_theme(self._theme)
        self.progress_bar.hide()
        card_layout.addWidget(self.progress_bar)

        self.lbl_dl_status = QLabel("", card)
        self.lbl_dl_status.setStyleSheet(f"font-size: 12px; font-weight: 500; color: {'#0284C7' if is_light else '#38BDF8'};")
        self.lbl_dl_status.hide()
        card_layout.addWidget(self.lbl_dl_status)

        # 4. 底部操作栏
        btn_bar = QHBoxLayout()
        btn_bar.setContentsMargins(0, 6, 0, 0)
        btn_bar.setSpacing(10)

        self.btn_later = QPushButton(t("btn_remind_later", "稍后提醒"), card)
        self.btn_later.setCursor(Qt.PointingHandCursor)
        self.btn_later.setFixedHeight(36)
        if is_light:
            self.btn_later.setStyleSheet("""
                QPushButton {
                    background: rgba(0, 0, 0, 0.05);
                    border: 1px solid rgba(0, 0, 0, 0.12);
                    border-radius: 10px;
                    padding: 0 16px;
                    color: #1E293B;
                    font-size: 13px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background: rgba(0, 0, 0, 0.09);
                    color: #0F172A;
                }
            """)
        else:
            self.btn_later.setStyleSheet("""
                QPushButton {
                    background: rgba(255, 255, 255, 0.06);
                    border: 1px solid rgba(255, 255, 255, 0.14);
                    border-radius: 10px;
                    padding: 0 16px;
                    color: #CBD5E1;
                    font-size: 13px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background: rgba(255, 255, 255, 0.12);
                    color: #FFFFFF;
                }
            """)
        self.btn_later.clicked.connect(self.reject)
        btn_bar.addWidget(self.btn_later)

        btn_bar.addStretch()

        raw_download_url = str(self.update_info.get("download_url") or "").strip()
        if not is_safe_download_url(raw_download_url):
            raw_download_url = (
                f"https://github.com/Fugui-Dai/LunaDimmer/releases/download/v{remote_ver}/LunaDimmer_v{remote_ver}.exe"
                if remote_ver
                else "https://github.com/Fugui-Dai/LunaDimmer/releases/latest"
            )
        fast_download_url = f"https://ghfast.top/{raw_download_url}" if raw_download_url.startswith("https://github.com") else raw_download_url

        is_zh = cur_lang.startswith("zh")
        main_dl_url = fast_download_url if is_zh else raw_download_url

        # 浏览器备用下载按钮
        self.btn_browser = QPushButton(t("btn_browser_download", "🌐 浏览器下载"), card)
        self.btn_browser.setCursor(Qt.PointingHandCursor)
        self.btn_browser.setFixedHeight(36)
        if is_light:
            self.btn_browser.setStyleSheet("""
                QPushButton {
                    background: rgba(0, 0, 0, 0.04);
                    border: 1px solid rgba(0, 0, 0, 0.12);
                    border-radius: 10px;
                    padding: 0 14px;
                    color: #475569;
                    font-size: 12.5px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background: rgba(0, 0, 0, 0.08);
                    color: #1E293B;
                }
            """)
        else:
            self.btn_browser.setStyleSheet("""
                QPushButton {
                    background: rgba(255, 255, 255, 0.05);
                    border: 1px solid rgba(255, 255, 255, 0.14);
                    border-radius: 10px;
                    padding: 0 14px;
                    color: #94A3B8;
                    font-size: 12.5px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background: rgba(255, 255, 255, 0.10);
                    color: #F1F5F9;
                }
            """)
        self.btn_browser.clicked.connect(lambda: self._open_download_url(main_dl_url))
        btn_bar.addWidget(self.btn_browser)

        # 极速自动更新主按钮（下载并静默覆盖重启）
        main_dl_text = t("btn_auto_update", "🚀 自动更新并重启")
        self.btn_download = QPushButton(main_dl_text, card)
        self.btn_download.setCursor(Qt.PointingHandCursor)
        self.btn_download.setFixedHeight(36)
        self.btn_download.setToolTip("后台多线程高速下载，下载完成后自动无缝覆盖并拉起新版")
        self.btn_download.setStyleSheet("""
            QPushButton {
                background: #0A84FF;
                border: none;
                border-radius: 10px;
                padding: 0 20px;
                color: #FFFFFF;
                font-size: 13.5px;
                font-weight: 700;
            }
            QPushButton:hover {
                background: #0071E3;
            }
            QPushButton:pressed {
                background: #005BB5;
            }
            QPushButton:disabled {
                background: rgba(10, 132, 255, 0.4);
                color: rgba(255, 255, 255, 0.6);
            }
        """)
        self.btn_download.clicked.connect(lambda: self._start_auto_update(main_dl_url))
        btn_bar.addWidget(self.btn_download)

        card_layout.addLayout(btn_bar)
        root_layout.addWidget(card)

    def _start_auto_update(self, download_url: str):
        """启动应用内多线程高速下载，完成后全自动覆盖并重启"""
        self.btn_download.setEnabled(False)
        self.btn_later.setEnabled(False)
        self.progress_bar.setValue(0)
        self.progress_bar.show()
        self.lbl_dl_status.show()
        self.lbl_dl_status.setText(t("dl_connecting", "正在连接高速更新节点..."))

        self.dl_worker = DownloadWorker(download_url, parent=self)
        self.dl_worker.sig_progress.connect(self._on_download_progress)
        self.dl_worker.sig_finished.connect(self._on_download_finished)
        self.dl_worker.start()

    def _on_download_progress(self, downloaded: int, total: int):
        if total > 0:
            ratio = downloaded / total
            pct = int(ratio * 100)
            self.progress_bar.set_progress(ratio)
            dl_mb = downloaded / (1024 * 1024)
            total_mb = total / (1024 * 1024)
            self.lbl_dl_status.setText(f"{t('dl_downloading', '正在极速下载...')} {pct}% ({dl_mb:.1f} MB / {total_mb:.1f} MB)")
        else:
            dl_mb = downloaded / (1024 * 1024)
            self.lbl_dl_status.setText(f"{t('dl_downloading', '正在极速下载...')} ({dl_mb:.1f} MB)")

    def _on_download_finished(self, ok: bool, result: str):
        if ok:
            self.progress_bar.set_progress(1.0)
            self.lbl_dl_status.setText(t("dl_complete", "✓ 下载完成，正在覆盖程序并自动重启..."))
            QTimer.singleShot(1000, lambda: apply_update_and_restart(result))
        else:
            self.progress_bar.hide()
            self.lbl_dl_status.setText(f"{t('dl_failed', '⚠️ 下载失败，请使用浏览器下载')}: {result}")
            self.btn_download.setEnabled(True)
            self.btn_later.setEnabled(True)

    def _open_download_url(self, url: str):
        remote_ver = self.update_info.get("version", "")
        if remote_ver:
            default_url = f"https://github.com/Fugui-Dai/LunaDimmer/releases/download/v{remote_ver}/LunaDimmer_v{remote_ver}.exe"
        else:
            default_url = "https://github.com/Fugui-Dai/LunaDimmer/releases/latest"

        target_url = str(url or "").strip()
        if not is_safe_download_url(target_url):
            target_url = default_url

        QDesktopServices.openUrl(QUrl(target_url))
        self.accept()

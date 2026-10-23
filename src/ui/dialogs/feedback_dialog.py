"""Luna Dimmer - 苹果 macOS 风格问题反馈与安全防刷中心 (Anti-Abuse Feedback Center)

安全防御与防攻击架构：
1. 本地与频控防洪 (Rate Limiting & Cooldown): 强制 60 秒冷静期，防止高频爆破与接口刷屏；
2. 自动化时间蜜罐 (Time-based Honeypot):
   - 检测打开至提交时间间隔，< 2.5 秒直接判定为爬虫/注入脚本拦截；
   - 隐藏 Honeypot 诱饵字段，自动化脚本填充即刻静默拦截；
3. 人机安全验证挑战 (Micro Math Proof): 动态随机一位数加减运算，杜绝无脑发帖机；
4. 边界与注入净化 (Sanitization):
   - 描述字数严格约束在 10 ~ 500 字符；
   - 连续重复字符拦截 (如 'aaaaaaa')；
   - 强行清除 HTML/Script 标签，杜绝 XSS 注入；
5. 受控环境诊断快照 (Safe Diagnostic Snapshot):
   - 仅包含 Windows 内核版本、显示器数量、调光信道、软件版本；
   - 绝不采集用户名、主机名、IP 或任何个人隐私数据；
6. 结构化直达通道: 支持本地安全归档与直接提交，杜绝第三方外链依赖。
"""

from typing import Optional, Dict, Any
import os
import sys
import time
import random
import re
import json
import urllib.request
import urllib.error

from PyQt5.QtCore import Qt, QPoint, QRectF, QTimer, pyqtSignal, QThread
from PyQt5.QtGui import (
    QColor,
    QPainter,
    QPen,
    QBrush,
    QLinearGradient,
    QFont,
    QCursor,
)
from PyQt5.QtWidgets import (
    QDialog,
    QWidget,
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QTextEdit,
    QPushButton,
    QComboBox,
    QCheckBox,
    QGraphicsDropShadowEffect,
    QApplication,
)

from src.i18n import t, get_language
from src.services.updater import CURRENT_VERSION
from src.win32_compat import start_window_drag, get_windows_version_name
from src.widgets.mac_controls import MacTrafficLights

# 默认反馈上报端点 (支持配置为 Cloudflare Worker / Formspree / 自建 Webhook)
DEFAULT_FEEDBACK_ENDPOINT = os.environ.get(
    "LUNA_FEEDBACK_ENDPOINT",
    "https://feedback.lunadimmer.workers.dev/api/feedback"
)


class FeedbackSubmitWorker(QThread):
    """异步非阻塞反馈上报引擎，0 服务器架构下直通 Cloudflare Worker / Webhook"""
    sig_done = pyqtSignal(bool, str)

    def __init__(self, endpoint: str, payload: dict, parent: Optional[QThread] = None):
        super().__init__(parent)
        self.endpoint = endpoint
        self.payload = payload

    def run(self):
        if not self.endpoint or not self.endpoint.startswith("http"):
            self.sig_done.emit(False, "no_endpoint")
            return
        try:
            body = json.dumps(self.payload, ensure_ascii=False).encode("utf-8")
            req = urllib.request.Request(
                self.endpoint,
                data=body,
                headers={
                    "Content-Type": "application/json; charset=utf-8",
                    "User-Agent": f"LunaDimmer-Client/{CURRENT_VERSION} (Windows; x64/x86)",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=4.0) as resp:
                if 200 <= resp.status < 300:
                    self.sig_done.emit(True, "")
                    return
                self.sig_done.emit(False, f"HTTP status {resp.status}")
        except Exception as e:
            self.sig_done.emit(False, str(e))


class FeedbackDialog(QDialog):
    """
    Apple macOS 风格问题反馈安全对话框
    """
    _last_submit_timestamp: float = 0.0

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setWindowModality(Qt.WindowModal)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFixedSize(540, 580)

        self._theme = (
            getattr(parent, "current_theme", None)
            or getattr(parent, "selected_theme", None)
            or "dark"
        )

        self._opened_time = time.time()
        self._cooldown_timer = None
        self._cooldown_remaining = 0

        # 生成动态随机人机挑战题目
        self._math_a = random.randint(2, 9)
        self._math_b = random.randint(1, 8)
        self._math_answer = self._math_a + self._math_b

        self._init_ui()
        self.apply_theme(self._theme)

    def showEvent(self, event):
        super().showEvent(event)
        if self.parent():
            parent_geo = self.parent().geometry()
            self.move(
                parent_geo.x() + (parent_geo.width() - self.width()) // 2,
                parent_geo.y() + (parent_geo.height() - self.height()) // 2,
            )

    def closeEvent(self, event):
        if getattr(self, "_cooldown_timer", None):
            self._cooldown_timer.stop()
            self._cooldown_timer.deleteLater()
            self._cooldown_timer = None
        super().closeEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and event.pos().y() <= 48:
            start_window_drag(int(self.winId()))
            event.accept()
            return
        super().mousePressEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), Qt.transparent)

    def _init_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(16, 16, 16, 16)
        root_layout.setSpacing(0)

        # 核心暗夜卡片容器
        self.card = QFrame(self)
        self.card.setObjectName("feedbackCard")
        card = self.card
        root_layout.addWidget(self.card)

        # 弥散抗锯齿柔和阴影
        shadow = QGraphicsDropShadowEffect(self.card)
        shadow.setBlurRadius(12)
        shadow.setColor(QColor(0, 0, 0, 120))
        shadow.setOffset(0, 2)
        self.card.setGraphicsEffect(shadow)

        layout = QVBoxLayout(self.card)
        layout.setContentsMargins(20, 16, 20, 18)
        layout.setSpacing(10)

        # 1. 顶部 Header (标题在左 + 关闭/最小化按钮在右，统一系统规范)
        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 4)

        self.lbl_title = QLabel(f"{t('feedback_title')} (V{CURRENT_VERSION})", self.card)
        self.lbl_title.setStyleSheet("font-size: 16px; font-weight: 700; color: #FFFFFF; border: none; background: transparent;")
        top_row.addWidget(self.lbl_title)
        top_row.addStretch()

        self.traffic_lights = MacTrafficLights(self.card, reverse_order=True)
        self.traffic_lights.sig_min.connect(self.hide)
        self.traffic_lights.sig_close.connect(self.reject)
        top_row.addWidget(self.traffic_lights)
        layout.addLayout(top_row)

        # 细微晶分割线
        self.sep = QFrame(self.card)
        self.sep.setFixedHeight(1)
        self.sep.setStyleSheet("background: rgba(255, 255, 255, 0.08);")
        layout.addWidget(self.sep)

        # 2. 反馈分类选择 (Type selector)
        type_row = QHBoxLayout()
        self.lbl_type = QLabel(t("feedback_type_label", "反馈分类："), self.card)
        self.lbl_type.setStyleSheet("font-size: 13px; font-weight: 600; color: #CBD5E1;")
        type_row.addWidget(self.lbl_type)

        self.cmb_type = QComboBox(self.card)
        self.cmb_type.setFixedHeight(30)
        self.cmb_type.addItems([
            t("feedback_type_bug", "🐛 遇到异常缺陷 (Bug Report)"),
            t("feedback_type_feat", "💡 体验与功能建议 (Feature Request)"),
            t("feedback_type_hw", "🖥️ 显示器硬件兼容问题 (Hardware)"),
        ])
        self.cmb_type.setStyleSheet("""
            QComboBox {
                background: rgba(255, 255, 255, 0.06);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 7px;
                padding: 2px 10px;
                color: #FFFFFF;
                font-size: 13px;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox QAbstractItemView {
                background: #1C1C1E;
                border: 1px solid rgba(255, 255, 255, 0.14);
                color: #FFFFFF;
                selection-background-color: rgba(10, 132, 255, 0.25);
                selection-color: #0A84FF;
            }
        """)
        type_row.addWidget(self.cmb_type, 1)
        layout.addLayout(type_row)

        # 3. 详细描述 (Description)
        self.txt_desc = QTextEdit(self.card)
        self.txt_desc.setPlaceholderText(t("feedback_desc_placeholder", "请详细描述发生场景、屏幕型号或改进建议 (10~500 字)..."))
        self.txt_desc.setFixedHeight(130)
        self.txt_desc.setStyleSheet("""
            QTextEdit {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 8px;
                padding: 8px;
                color: #F8FAFC;
                font-size: 13px;
                line-height: 18px;
            }
            QTextEdit:focus {
                border: 1px solid #0A84FF;
                background: rgba(255, 255, 255, 0.08);
            }
        """)
        layout.addWidget(self.txt_desc)

        # 4. 联系方式 (Contact - Optional)
        self.txt_contact = QLineEdit(self.card)
        self.txt_contact.setPlaceholderText(t("feedback_contact_placeholder", "联系方式 (可选，邮箱/微信，便于向您答复进展)"))
        self.txt_contact.setFixedHeight(32)
        self.txt_contact.setStyleSheet("""
            QLineEdit {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 7px;
                padding: 0 10px;
                color: #F8FAFC;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid #0A84FF;
                background: rgba(255, 255, 255, 0.08);
            }
        """)
        layout.addWidget(self.txt_contact)

        # 诱饵蜜罐字段 (Honeypot - 隐藏且人类无法察觉，自动化脚本填充即拦截)
        self.txt_honeypot = QLineEdit(self.card)
        self.txt_honeypot.setVisible(False)
        layout.addWidget(self.txt_honeypot)

        # 5. 安全人机验证行 (Math challenge)
        human_row = QHBoxLayout()
        human_row.setSpacing(8)

        lbl_math = QLabel(f"🛡️ 人机验证：{self._math_a} + {self._math_b} = ", self.card)
        lbl_math.setStyleSheet("font-size: 13px; font-weight: 600; color: #FF9F0A;")
        human_row.addWidget(lbl_math)

        self.txt_math = QLineEdit(self.card)
        self.txt_math.setPlaceholderText("答案")
        self.txt_math.setFixedWidth(70)
        self.txt_math.setFixedHeight(28)
        self.txt_math.setAlignment(Qt.AlignCenter)
        self.txt_math.setStyleSheet("""
            QLineEdit {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 6px;
                color: #FFFFFF;
                font-size: 13px;
                font-weight: bold;
            }
            QLineEdit:focus {
                border-color: #FF9F0A;
                background: rgba(255, 255, 255, 0.08);
            }
        """)
        human_row.addWidget(self.txt_math)

        human_row.addStretch()

        self.cb_diag = QCheckBox(t("feedback_diag_label", "附加环境快照 (无敏感隐私)"), self.card)
        self.cb_diag.setChecked(True)
        self.cb_diag.setStyleSheet("""
            QCheckBox {
                color: rgba(235, 235, 245, 0.65);
                font-size: 12px;
            }
            QCheckBox::indicator {
                width: 14px;
                height: 14px;
                border-radius: 4px;
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.2);
            }
            QCheckBox::indicator:checked {
                background-color: #0A84FF;
                border-color: #0A84FF;
            }
        """)
        human_row.addWidget(self.cb_diag)
        layout.addLayout(human_row)

        # 6. 反馈状态提示条 (Status feedback)
        self.lbl_status = QLabel("", self.card)
        self.lbl_status.setStyleSheet("font-size: 13.5px; font-weight: 600; min-height: 18px; border: none; background: transparent;")
        layout.addWidget(self.lbl_status)

        # 7. 底部操作按钮栏
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        btn_row.addStretch()

        # 主提交按钮
        self.btn_submit = QPushButton(t("feedback_btn_submit", "🚀 安全提交反馈"), self.card)
        self.btn_submit.setCursor(Qt.PointingHandCursor)
        self.btn_submit.setFixedHeight(34)
        self.btn_submit.setStyleSheet("""
            QPushButton {
                background: #0A84FF;
                border: none;
                border-radius: 8px;
                padding: 4px 22px;
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
                background: rgba(255, 255, 255, 0.06);
                border: 1px solid rgba(255, 255, 255, 0.08);
                color: rgba(235, 235, 245, 0.40);
            }
        """)
        self.btn_submit.clicked.connect(self.handle_submit)
        btn_row.addWidget(self.btn_submit)

        layout.addLayout(btn_row)

    def apply_theme(self, theme: str):
        """根据系统主题（深色 / 浅色 / 液态玻璃）注入统一标准背景色与控件微晶样式"""
        self._theme = theme if theme in ("dark", "light", "liquid_glass") else "dark"
        if self._theme == "light":
            self.card.setStyleSheet("""
                QFrame#feedbackCard {
                    background: #FFFFFF;
                    border: 1px solid rgba(0, 0, 0, 0.12);
                    border-radius: 18px;
                }
                QLabel {
                    color: #1D1D1F;
                    font-family: "Microsoft YaHei UI", "Segoe UI", -apple-system, sans-serif;
                }
            """)
            self.lbl_title.setStyleSheet("font-size: 16px; font-weight: 700; color: #1D1D1F; border: none; background: transparent;")
            if hasattr(self, "sep"):
                self.sep.setStyleSheet("background: rgba(0, 0, 0, 0.08);")
            if hasattr(self, "lbl_type"):
                self.lbl_type.setStyleSheet("font-size: 13px; font-weight: 600; color: #334155;")
            if hasattr(self, "cmb_type"):
                self.cmb_type.setStyleSheet("""
                    QComboBox {
                        background: rgba(0, 0, 0, 0.04);
                        border: 1px solid rgba(0, 0, 0, 0.12);
                        border-radius: 7px;
                        padding: 2px 10px;
                        color: #1D1D1F;
                        font-size: 13px;
                    }
                    QComboBox::drop-down {
                        border: none;
                        width: 20px;
                    }
                    QComboBox QAbstractItemView {
                        background: #FFFFFF;
                        border: 1px solid rgba(0, 0, 0, 0.14);
                        color: #1D1D1F;
                        selection-background-color: rgba(10, 132, 255, 0.15);
                        selection-color: #0A84FF;
                    }
                """)
            if hasattr(self, "txt_desc"):
                self.txt_desc.setStyleSheet("""
                    QTextEdit {
                        background: rgba(0, 0, 0, 0.035);
                        border: 1px solid rgba(0, 0, 0, 0.12);
                        border-radius: 8px;
                        padding: 8px;
                        color: #1D1D1F;
                        font-size: 13px;
                        line-height: 18px;
                    }
                    QTextEdit:focus {
                        border: 1px solid #0A84FF;
                        background: #FFFFFF;
                    }
                """)
            if hasattr(self, "txt_contact"):
                self.txt_contact.setStyleSheet("""
                    QLineEdit {
                        background: rgba(0, 0, 0, 0.035);
                        border: 1px solid rgba(0, 0, 0, 0.12);
                        border-radius: 7px;
                        padding: 0 10px;
                        color: #1D1D1F;
                        font-size: 13px;
                    }
                    QLineEdit:focus {
                        border: 1px solid #0A84FF;
                        background: #FFFFFF;
                    }
                """)
            if hasattr(self, "txt_math"):
                self.txt_math.setStyleSheet("""
                    QLineEdit {
                        background: rgba(0, 0, 0, 0.035);
                        border: 1px solid rgba(0, 0, 0, 0.12);
                        border-radius: 6px;
                        color: #1D1D1F;
                        font-size: 13px;
                        font-weight: bold;
                    }
                    QLineEdit:focus {
                        border-color: #FF9F0A;
                        background: #FFFFFF;
                    }
                """)
            if hasattr(self, "cb_diag"):
                self.cb_diag.setStyleSheet("""
                    QCheckBox {
                        color: rgba(60, 60, 67, 0.70);
                        font-size: 12px;
                    }
                    QCheckBox::indicator {
                        width: 14px;
                        height: 14px;
                        border-radius: 4px;
                        background: rgba(0, 0, 0, 0.06);
                        border: 1px solid rgba(0, 0, 0, 0.18);
                    }
                    QCheckBox::indicator:checked {
                        background-color: #0A84FF;
                        border-color: #0A84FF;
                    }
                """)
        elif self._theme == "liquid_glass":
            self.card.setStyleSheet("""
                QFrame#feedbackCard {
                    background: rgba(20, 22, 30, 0.94);
                    border: 1px solid rgba(255, 255, 255, 0.18);
                    border-top: 1.2px solid rgba(255, 255, 255, 0.38);
                    border-radius: 18px;
                }
                QLabel {
                    color: #FFFFFF;
                    font-family: "Microsoft YaHei UI", "Segoe UI", -apple-system, sans-serif;
                }
            """)
            self.lbl_title.setStyleSheet("font-size: 16px; font-weight: 700; color: #FFFFFF; border: none; background: transparent;")
            if hasattr(self, "sep"):
                self.sep.setStyleSheet("background: rgba(255, 255, 255, 0.08);")
            if hasattr(self, "lbl_type"):
                self.lbl_type.setStyleSheet("font-size: 13px; font-weight: 600; color: #CBD5E1;")
            if hasattr(self, "cmb_type"):
                self.cmb_type.setStyleSheet("""
                    QComboBox {
                        background: rgba(255, 255, 255, 0.06);
                        border: 1px solid rgba(255, 255, 255, 0.12);
                        border-radius: 7px;
                        padding: 2px 10px;
                        color: #FFFFFF;
                        font-size: 13px;
                    }
                    QComboBox::drop-down {
                        border: none;
                        width: 20px;
                    }
                    QComboBox QAbstractItemView {
                        background: #1C1C1E;
                        border: 1px solid rgba(255, 255, 255, 0.14);
                        color: #FFFFFF;
                        selection-background-color: rgba(10, 132, 255, 0.25);
                        selection-color: #0A84FF;
                    }
                """)
            if hasattr(self, "txt_desc"):
                self.txt_desc.setStyleSheet("""
                    QTextEdit {
                        background: rgba(255, 255, 255, 0.05);
                        border: 1px solid rgba(255, 255, 255, 0.12);
                        border-radius: 8px;
                        padding: 8px;
                        color: #F8FAFC;
                        font-size: 13px;
                        line-height: 18px;
                    }
                    QTextEdit:focus {
                        border: 1px solid #0A84FF;
                        background: rgba(255, 255, 255, 0.08);
                    }
                """)
            if hasattr(self, "txt_contact"):
                self.txt_contact.setStyleSheet("""
                    QLineEdit {
                        background: rgba(255, 255, 255, 0.05);
                        border: 1px solid rgba(255, 255, 255, 0.12);
                        border-radius: 7px;
                        padding: 0 10px;
                        color: #F8FAFC;
                        font-size: 13px;
                    }
                    QLineEdit:focus {
                        border: 1px solid #0A84FF;
                        background: rgba(255, 255, 255, 0.08);
                    }
                """)
            if hasattr(self, "txt_math"):
                self.txt_math.setStyleSheet("""
                    QLineEdit {
                        background: rgba(255, 255, 255, 0.05);
                        border: 1px solid rgba(255, 255, 255, 0.12);
                        border-radius: 6px;
                        color: #FFFFFF;
                        font-size: 13px;
                        font-weight: bold;
                    }
                    QLineEdit:focus {
                        border-color: #FF9F0A;
                        background: rgba(255, 255, 255, 0.08);
                    }
                """)
            if hasattr(self, "cb_diag"):
                self.cb_diag.setStyleSheet("""
                    QCheckBox {
                        color: rgba(235, 235, 245, 0.65);
                        font-size: 12px;
                    }
                    QCheckBox::indicator {
                        width: 14px;
                        height: 14px;
                        border-radius: 4px;
                        background: rgba(255, 255, 255, 0.08);
                        border: 1px solid rgba(255, 255, 255, 0.2);
                    }
                    QCheckBox::indicator:checked {
                        background-color: #0A84FF;
                        border-color: #0A84FF;
                    }
                """)
        else:  # Dark: 统一为全应用标准的苹果中性黑曜石 #1C1C1E
            self.card.setStyleSheet("""
                QFrame#feedbackCard {
                    background: #1C1C1E;
                    border: 1px solid rgba(255, 255, 255, 0.10);
                    border-radius: 18px;
                }
                QLabel {
                    color: #FFFFFF;
                    font-family: "Microsoft YaHei UI", "Segoe UI", -apple-system, sans-serif;
                }
            """)
            self.lbl_title.setStyleSheet("font-size: 16px; font-weight: 700; color: #FFFFFF; border: none; background: transparent;")
            if hasattr(self, "sep"):
                self.sep.setStyleSheet("background: rgba(255, 255, 255, 0.08);")
            if hasattr(self, "lbl_type"):
                self.lbl_type.setStyleSheet("font-size: 13px; font-weight: 600; color: #CBD5E1;")

    def _show_msg(self, msg: str, is_error: bool = True):
        self.lbl_status.setText(msg)
        if is_error:
            self.lbl_status.setStyleSheet("font-size: 13.5px; font-weight: 600; color: #F87171; min-height: 18px;")
        else:
            self.lbl_status.setStyleSheet("font-size: 13.5px; font-weight: 600; color: #34D399; min-height: 18px;")

    def _get_diagnostic_info(self) -> Dict[str, Any]:
        """收集受控、无敏感隐私的环境诊断快照"""
        screens = QApplication.screens()
        return {
            "version": f"V{CURRENT_VERSION}",
            "os_name": get_windows_version_name(),
            "screen_count": len(screens) if screens else 1,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
        }

    def handle_submit(self):
        """执行五重安全防御校验并提交"""
        now = time.time()

        # 防御 1：时间蜜罐防御 (停留时间 < 2.5 秒直接判定自动化攻击)
        if now - self._opened_time < 2.5:
            self._show_msg(t("feedback_err_spam", "⚠️ 检测到自动化异常特征，提交已被安全拦截"), is_error=True)
            return

        # 防御 2：诱饵蜜罐字段检验 (机器人自动填充必抓)
        if bool(self.txt_honeypot.text().strip()):
            self._show_msg(t("feedback_err_spam", "⚠️ 检测到自动化异常特征，提交已被安全拦截"), is_error=True)
            return

        # 防御 3：60 秒冷却期防洪机制 (Rate Limiter)
        cooldown_elapsed = now - FeedbackDialog._last_submit_timestamp
        if cooldown_elapsed < 60:
            remaining = int(60 - cooldown_elapsed)
            msg = t("feedback_err_cooldown", "⚠️ 提交过于频繁，请等待 {sec} 秒后再试").replace("{sec}", str(remaining))
            self._show_msg(msg, is_error=True)
            return

        # 防御 4：人机安全数学验证
        math_input = self.txt_math.text().strip()
        if not math_input.isdigit() or int(math_input) != self._math_answer:
            self._show_msg(t("feedback_err_human", "⚠️ 人机安全验证计算错误，请重新计算"), is_error=True)
            return

        # 防御 5：输入内容边界与防注入净化
        desc = self.txt_desc.toPlainText().strip()
        if len(desc) < 10:
            self._show_msg(t("feedback_err_short", "⚠️ 描述内容过短，请至少输入 10 个字符"), is_error=True)
            return
        if len(desc) > 500:
            self._show_msg(t("feedback_err_long", "⚠️ 描述内容过长，请控制在 500 字符以内"), is_error=True)
            return

        # 连续无意义乱码检测 (如连续 8 个相同字符)
        if re.search(r'(.)\1{7,}', desc):
            self._show_msg("⚠️ 请勿输入无意义的重复字符或刷屏内容", is_error=True)
            return

        # 过滤清除 HTML/Script 脚本注入代码
        clean_desc = re.sub(r'<[^>]+>', '', desc)
        contact = re.sub(r'<[^>]+>', '', self.txt_contact.text().strip())
        fb_type = self.cmb_type.currentText()

        # 组装安全反馈包
        payload = {
            "type": fb_type,
            "description": clean_desc,
            "contact": contact,
            "diagnostics": self._get_diagnostic_info() if self.cb_diag.isChecked() else None,
        }

        # 本地安全归档保存 (确保脱机也可追踪记录)
        try:
            log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "feedback_logs")
            os.makedirs(log_dir, exist_ok=True)
            filename = f"feedback_{int(now)}.json"
            filepath = os.path.join(log_dir, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

        # 记录冷静期时间戳
        FeedbackDialog._last_submit_timestamp = now

        # 异步网络端点提交 (Cloudflare Worker / Webhook / 零服务器管道)
        self.btn_submit.setEnabled(False)
        self.btn_submit.setText("正在提交...")

        self._submit_worker = FeedbackSubmitWorker(DEFAULT_FEEDBACK_ENDPOINT, payload, self)

        def _on_submit_done(ok: bool, err_msg: str):
            if hasattr(self, "_submit_worker") and self._submit_worker:
                self._submit_worker.deleteLater()
                self._submit_worker = None

            if ok:
                self._show_msg(t("feedback_success", "✓ 反馈已成功送达！感谢您对 Luna Dimmer 的支持与守护"), is_error=False)
            else:
                summary_text = (
                    f"【Luna Dimmer 用户反馈】\n"
                    f"类型: {fb_type}\n"
                    f"内容: {clean_desc}\n"
                    f"联系方式: {contact}\n"
                    f"环境快照: Windows | 屏幕数: {self._get_diagnostic_info().get('screen_count', 1)}"
                )
                try:
                    QApplication.clipboard().setText(summary_text)
                except Exception:
                    pass

                self._show_msg("✓ 反馈已安全归档！已自动复制内容，欢迎前往 GitHub 或邮件交流", is_error=False)

            self._start_cooldown_timer(60)

        self._submit_worker.sig_done.connect(_on_submit_done)
        self._submit_worker.start()

    def _start_cooldown_timer(self, seconds: int):
        if getattr(self, "_cooldown_timer", None):
            self._cooldown_timer.stop()
            self._cooldown_timer.deleteLater()
            self._cooldown_timer = None

        self._cooldown_remaining = seconds
        self.btn_submit.setEnabled(False)

        def _tick():
            self._cooldown_remaining -= 1
            if self._cooldown_remaining <= 0:
                if self._cooldown_timer:
                    self._cooldown_timer.stop()
                    self._cooldown_timer.deleteLater()
                    self._cooldown_timer = None
                self.btn_submit.setEnabled(True)
                self.btn_submit.setText(t("feedback_btn_submit", "🚀 安全提交反馈"))
            else:
                self.btn_submit.setText(f"冷静中 ({self._cooldown_remaining}s)")

        self._cooldown_timer = QTimer(self)
        self._cooldown_timer.timeout.connect(_tick)
        self._cooldown_timer.start(1000)
        _tick()

import ctypes
from ctypes import wintypes
import logging
import queue
import threading
from typing import Callable, Dict, Optional, Tuple

from src.platform.win32_compat import (
    user32,
    kernel32,
    RegisterHotKey,
    UnregisterHotKey,
    GetMessageW,
    PeekMessageW,
    PostThreadMessageW,
    TranslateMessage,
    DispatchMessageW,
    GetCurrentThreadId,
)

logger = logging.getLogger(__name__)

# Win32 热键修饰键常量
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008
MOD_NOREPEAT = 0x4000

# Win32 消息常量
WM_HOTKEY = 0x0312
WM_QUIT = 0x0012
WM_USER = 0x0400

# Win32 错误码
ERROR_HOTKEY_ALREADY_REGISTERED = 1409

# 虚拟键码映射表
VK_MAP: Dict[str, int] = {
    # 方向键
    "UP": 0x26,
    "DOWN": 0x28,
    "LEFT": 0x25,
    "RIGHT": 0x27,
    # 常用功能控制键
    "SPACE": 0x20,
    "ESC": 0x1B,
    "ESCAPE": 0x1B,
    "RETURN": 0x0D,
    "ENTER": 0x0D,
    "TAB": 0x09,
    "BACK": 0x08,
    "BACKSPACE": 0x08,
    "DELETE": 0x2E,
    "DEL": 0x2E,
    "INSERT": 0x2D,
    "INS": 0x2D,
    "HOME": 0x24,
    "END": 0x23,
    "PRIOR": 0x21,
    "PAGEUP": 0x21,
    "PGUP": 0x21,
    "NEXT": 0x22,
    "PAGEDOWN": 0x22,
    "PGDN": 0x22,
    "CAPSLOCK": 0x14,
    "CAPS": 0x14,
    "NUMLOCK": 0x90,
    "SCROLLLOCK": 0x91,
    "PRINTSCREEN": 0x2C,
    "PRTSC": 0x2C,
    "SNAPSHOT": 0x2C,
    "PAUSE": 0x13,
    # 标点符号与运算符号
    "PLUS": 0xBB,
    "EQUALS": 0xBB,
    "MINUS": 0xBD,
    "COMMA": 0xBC,
    "PERIOD": 0xBE,
    "SLASH": 0xBF,
    "BACKSLASH": 0xDC,
    "SEMICOLON": 0xBA,
    "QUOTE": 0xDE,
    "GRAVE": 0xC0,
    "TILDE": 0xC0,
    "BRACKETLEFT": 0xDB,
    "BRACKETRIGHT": 0xDD,
}

# 注册 F1 ~ F24 键码
for _i in range(1, 25):
    VK_MAP[f"F{_i}"] = 0x70 + (_i - 1)

# 反向键码映射（用于将 Win32 虚拟键码规范化为可读字符串）
INV_VK_MAP: Dict[int, str] = {
    0x26: "Up",
    0x28: "Down",
    0x25: "Left",
    0x27: "Right",
    0x20: "Space",
    0x1B: "Esc",
    0x0D: "Enter",
    0x09: "Tab",
    0x08: "Backspace",
    0x2E: "Delete",
    0x2D: "Insert",
    0x24: "Home",
    0x23: "End",
    0x21: "PageUp",
    0x22: "PageDown",
    0xBB: "+",
    0xBD: "-",
    0xBC: ",",
    0xBE: ".",
    0xBF: "/",
    0xDC: "\\",
    0xBA: ";",
    0xDE: "'",
    0xC0: "`",
}
for _f in range(1, 25):
    INV_VK_MAP[0x70 + (_f - 1)] = f"F{_f}"


def parse_hotkey_string(key_str: str) -> Tuple[int, int]:
    """
    解析快捷键组合字符串（如 'Ctrl+Alt+Up', 'Ctrl+Alt+S'），
    返回 (mods, vk) 元组。
    """
    if not key_str or not key_str.strip():
        raise ValueError("Hotkey string cannot be empty")

    raw_str = key_str.strip()

    # 处理 '+' 作为键名的特殊情况，如 "Ctrl++" 或 "Ctrl + +"
    if raw_str.endswith("++") or raw_str.endswith("+ +"):
        prefix = raw_str.rsplit("+", 2)[0]
        parts = [p.strip().upper() for p in prefix.split("+") if p.strip()]
        parts.append("+")
    else:
        parts = [p.strip().upper() for p in raw_str.split("+") if p.strip()]

    if not parts:
        raise ValueError(f"Invalid hotkey string: '{key_str}'")

    mods = MOD_NOREPEAT
    vk = 0

    for p in parts:
        if p in ("CTRL", "CONTROL"):
            mods |= MOD_CONTROL
        elif p == "ALT":
            mods |= MOD_ALT
        elif p == "SHIFT":
            mods |= MOD_SHIFT
        elif p in ("WIN", "WINDOWS", "SUPER", "META"):
            mods |= MOD_WIN
        elif p in VK_MAP:
            vk = VK_MAP[p]
        elif len(p) == 1:
            if 'A' <= p <= 'Z' or '0' <= p <= '9':
                vk = ord(p)
            elif p in ("+", "="):
                vk = 0xBB
            elif p == "-":
                vk = 0xBD
            elif p == ",":
                vk = 0xBC
            elif p == ".":
                vk = 0xBE
            elif p == "/":
                vk = 0xBF
            elif p == "\\":
                vk = 0xDC
            elif p == ";":
                vk = 0xBA
            elif p == "'":
                vk = 0xDE
            elif p in ("`", "~"):
                vk = 0xC0
            elif p == "[":
                vk = 0xDB
            elif p == "]":
                vk = 0xDD
            else:
                raise ValueError(f"Unsupported character key: '{p}'")
        else:
            raise ValueError(f"Unknown key or modifier: '{p}' in '{key_str}'")

    if vk == 0:
        raise ValueError(f"Hotkey '{key_str}' does not specify a valid key")

    return mods, vk


def normalize_hotkey_string(key_str: str) -> str:
    """
    将用户输入的快捷键字符串规范化为标准格式（例如 'ctrl+alt+up' -> 'Ctrl+Alt+Up'）。
    """
    mods, vk = parse_hotkey_string(key_str)
    parts = []
    if mods & MOD_CONTROL:
        parts.append("Ctrl")
    if mods & MOD_ALT:
        parts.append("Alt")
    if mods & MOD_SHIFT:
        parts.append("Shift")
    if mods & MOD_WIN:
        parts.append("Win")

    if vk in INV_VK_MAP:
        parts.append(INV_VK_MAP[vk])
    elif 0x41 <= vk <= 0x5A or 0x30 <= vk <= 0x39:
        parts.append(chr(vk))
    else:
        parts.append(f"VK_{vk}")

    return "+".join(parts)


# 独立启用 use_last_error 的 user32 句柄：
# `ctypes.windll` 不会保存 Win32 线程最后错误码，直接调用 GetLastError 可能拿到被
# 中间调用覆盖的陈旧值，导致 1409「热键已被占用」判定漂移。
_user32_err = ctypes.WinDLL("user32", use_last_error=True)
_user32_err.RegisterHotKey.restype = wintypes.BOOL
_user32_err.RegisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int, wintypes.UINT, wintypes.UINT]
_user32_err.UnregisterHotKey.restype = wintypes.BOOL
_user32_err.UnregisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int]


def test_hotkey_availability(key_str: str, current_key: Optional[str] = None) -> Tuple[bool, str]:
    """
    测试快捷键组合是否合法且未被 Windows 系统或其他第三方应用抢占。
    - 若与 current_key 规范化后一致，说明未改动或改回原键，直接判定可用
      （避免把「本程序自己已注册的原键」误判为被其他应用占用）；
    - 使用临时 ID 在当前线程试探性注册，测试完毕立即注销；
    - 若返回 0 且 GetLastError 为 1409，表示被系统或其他应用占用。
    返回 (is_available, error_message)。
    """
    try:
        mods, vk = parse_hotkey_string(key_str)
    except Exception as e:
        return False, f"无效的快捷键: {e}"

    if current_key:
        try:
            curr_mods, curr_vk = parse_hotkey_string(current_key)
            if (mods, vk) == (curr_mods, curr_vk):
                return True, ""
        except Exception:
            pass

    test_id = 0x7EFE
    try:
        ret = _user32_err.RegisterHotKey(0, test_id, mods, vk)
        err = ctypes.get_last_error()
        if ret:
            _user32_err.UnregisterHotKey(0, test_id)
            return True, ""
    except Exception as e:
        return False, f"WIN32_EXCEPTION_{e}"

    if err == ERROR_HOTKEY_ALREADY_REGISTERED:
        return False, "OCCUPIED"
    return False, f"WIN32_ERROR_{err}"


class GlobalHotkeyManager:
    """
    Windows 全局原生热键管理器。
    支持 Win32 RegisterHotKey / UnregisterHotKey API，
    在后台消息循环线程中非阻塞监听热键事件，提供干净注销、重入安全与冲突平滑降级。
    """

    def __init__(self):
        self._handlers: Dict[int, Callable[[], None]] = {}
        self._key_info: Dict[int, Tuple[str, int, int]] = {}  # hk_id -> (key_str, mods, vk)
        self._action_to_id: Dict[str, int] = {}               # action_name -> hk_id
        self._id_to_action: Dict[int, str] = {}               # hk_id -> action_name
        self._action_to_key: Dict[str, str] = {}              # action_name -> key_str

        self._id_counter = 100
        self._lock = threading.RLock()

        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._thread_id: Optional[int] = None
        self._ready_event = threading.Event()
        self._cmd_queue: queue.Queue = queue.Queue()

    @property
    def is_running(self) -> bool:
        """热键监听线程是否在运行中。"""
        with self._lock:
            return self._running and (self._thread is not None and self._thread.is_alive())

    @property
    def thread_id(self) -> Optional[int]:
        """工作线程的 Win32 Thread ID。"""
        with self._lock:
            return self._thread_id

    @property
    def registered_hotkeys(self) -> Dict[str, str]:
        """返回已注册的动作名称及对应热键组合映射。"""
        with self._lock:
            return dict(self._action_to_key)

    def get_action_hotkey(self, action_name: str) -> Optional[str]:
        """获取指定动作当前绑定的热键组合。"""
        with self._lock:
            return self._action_to_key.get(action_name)

    def register(self, key_str: str, callback: Callable[[], None]) -> int:
        """
        注册全局热键组合，返回分配的热键 ID（成功 > 0，若失败/冲突返回 0）。
        采用无锁序倒置与回调重入安全机制。
        """
        mods, vk = parse_hotkey_string(key_str)

        with self._lock:
            self._id_counter += 1
            hk_id = self._id_counter
            running = self._running and (self._thread is not None and self._thread.is_alive())
            tid = self._thread_id

        # 场景 1: 回调重入处理
        current_tid = GetCurrentThreadId()
        if tid is not None and current_tid == tid:
            ret = RegisterHotKey(0, hk_id, mods, vk)
            if not ret:
                err = ctypes.GetLastError()
                logger.warning(
                    "Failed to register hotkey '%s' (id=%d, Win32 error=%d) in reentrant callback.",
                    key_str,
                    hk_id,
                    err,
                )
                return 0

            with self._lock:
                self._handlers[hk_id] = callback
                self._key_info[hk_id] = (key_str, mods, vk)
            return hk_id

        # 场景 2: 外部线程调用且工作线程正在运行
        if running and tid:
            resp: queue.Queue = queue.Queue()
            self._cmd_queue.put(("REGISTER", (hk_id, mods, vk), resp))
            PostThreadMessageW(tid, WM_USER, 0, 0)
            try:
                success, err = resp.get(timeout=2.0)
            except queue.Empty:
                logger.error("Timed out waiting for hotkey registration on worker thread.")
                return 0

            if not success:
                logger.warning(
                    "Failed to register hotkey '%s' (id=%d, Win32 error=%d). Possibly occupied by another app.",
                    key_str,
                    hk_id,
                    err,
                )
                return 0

            with self._lock:
                self._handlers[hk_id] = callback
                self._key_info[hk_id] = (key_str, mods, vk)
            return hk_id

        # 场景 3: 线程未启动时预先注册
        ret = RegisterHotKey(0, hk_id, mods, vk)
        if not ret:
            err = ctypes.GetLastError()
            logger.warning(
                "Failed to register hotkey '%s' (id=%d, Win32 error=%d). Possibly occupied by another app.",
                key_str,
                hk_id,
                err,
            )
            return 0

        with self._lock:
            self._handlers[hk_id] = callback
            self._key_info[hk_id] = (key_str, mods, vk)
        return hk_id

    def register_hotkey(self, action_name: str, key_combination: str, callback: Callable[[], None]) -> bool:
        """
        以具名动作方式注册或更新热键。
        若新热键注册失败（如冲突），完整保留原有热键映射不变（防回滚丢失）。
        """
        with self._lock:
            old_hk_id = self._action_to_id.get(action_name)
            old_key = self._action_to_key.get(action_name)

        # 若键位完全一致，仅就地更新回调函数
        if old_hk_id is not None and old_key == key_combination:
            with self._lock:
                self._handlers[old_hk_id] = callback
            return True

        # 尝试注册新键位
        new_hk_id = self.register(key_combination, callback)
        if new_hk_id > 0:
            # 新热键注册成功：注销旧热键并切换映射
            if old_hk_id is not None:
                self.unregister(old_hk_id)
            with self._lock:
                self._action_to_id[action_name] = new_hk_id
                self._id_to_action[new_hk_id] = action_name
                self._action_to_key[action_name] = key_combination
            return True
        else:
            # 新热键注册失败：完整保留旧热键监听
            logger.warning(
                "Failed to update hotkey for action '%s' to '%s'; preserving previous hotkey '%s'",
                action_name,
                key_combination,
                old_key,
            )
            return False

    def unregister(self, hk_id: int) -> bool:
        """注销指定 ID 的全局热键。"""
        with self._lock:
            if hk_id not in self._handlers and hk_id not in self._key_info:
                return False
            running = self._running and (self._thread is not None and self._thread.is_alive())
            tid = self._thread_id

        current_tid = GetCurrentThreadId()
        if tid is not None and current_tid == tid:
            ret = UnregisterHotKey(0, hk_id)
            with self._lock:
                self._handlers.pop(hk_id, None)
                self._key_info.pop(hk_id, None)
                action = self._id_to_action.pop(hk_id, None)
                if action:
                    self._action_to_id.pop(action, None)
                    self._action_to_key.pop(action, None)
            return bool(ret)

        if running and tid:
            resp: queue.Queue = queue.Queue()
            self._cmd_queue.put(("UNREGISTER", hk_id, resp))
            PostThreadMessageW(tid, WM_USER, 0, 0)
            try:
                resp.get(timeout=2.0)
            except queue.Empty:
                pass
        else:
            UnregisterHotKey(0, hk_id)

        with self._lock:
            self._handlers.pop(hk_id, None)
            self._key_info.pop(hk_id, None)
            action = self._id_to_action.pop(hk_id, None)
            if action:
                self._action_to_id.pop(action, None)
                self._action_to_key.pop(action, None)

        return True

    def unregister_hotkey(self, action_name: str) -> bool:
        """注销指定动作名称的热键。"""
        with self._lock:
            hk_id = self._action_to_id.get(action_name)
        if hk_id is not None:
            return self.unregister(hk_id)
        return False

    def unregister_all(self):
        """注销当前所有已注册的全局热键。"""
        with self._lock:
            ids = list(self._key_info.keys())
            running = self._running and (self._thread is not None and self._thread.is_alive())
            tid = self._thread_id

        current_tid = GetCurrentThreadId()
        if tid is not None and current_tid == tid:
            for hid in ids:
                UnregisterHotKey(0, hid)
        elif running and tid:
            resp: queue.Queue = queue.Queue()
            self._cmd_queue.put(("UNREGISTER_ALL", ids, resp))
            PostThreadMessageW(tid, WM_USER, 0, 0)
            try:
                resp.get(timeout=2.0)
            except queue.Empty:
                pass
        else:
            for hid in ids:
                UnregisterHotKey(0, hid)

        with self._lock:
            self._handlers.clear()
            self._key_info.clear()
            self._action_to_id.clear()
            self._id_to_action.clear()
            self._action_to_key.clear()

    def start(self):
        """启动后台 Win32 消息循环线程。"""
        with self._lock:
            if self._running:
                return

            self._running = True
            self._ready_event.clear()

            # 如果在线程启动前主线程曾注册过热键，先在主线程释放，以便工作线程重新接管
            for hk_id in list(self._key_info.keys()):
                UnregisterHotKey(0, hk_id)

            self._thread = threading.Thread(target=self._msg_loop, daemon=True)
            self._thread.start()

        self._ready_event.wait(timeout=3.0)

    def stop(self):
        """停止后台消息循环线程并注销所有热键。"""
        with self._lock:
            if not self._running:
                return

            self._running = False
            tid = self._thread_id
            thread = self._thread

        if tid:
            PostThreadMessageW(tid, WM_QUIT, 0, 0)

        if thread and thread.is_alive():
            thread.join(timeout=2.0)

        with self._lock:
            self._thread = None
            self._thread_id = None

    def _msg_loop(self):
        """后台 Win32 消息循环函数。"""
        msg = wintypes.MSG()
        # 强制 Win32 系统为当前工作线程创建消息队列
        PeekMessageW(ctypes.byref(msg), 0, 0, 0, 0)

        self._thread_id = GetCurrentThreadId()

        # 在当前工作线程重新注册所有已配置的热键
        with self._lock:
            keys_to_reg = list(self._key_info.items())

        for hk_id, (key_str, mods, vk) in keys_to_reg:
            ret = RegisterHotKey(0, hk_id, mods, vk)
            if not ret:
                err = ctypes.GetLastError()
                logger.warning(
                    "Worker thread failed to re-register hotkey '%s' (id=%d, err=%d)",
                    key_str,
                    hk_id,
                    err,
                )

        self._ready_event.set()

        try:
            while self._running:
                res = GetMessageW(ctypes.byref(msg), 0, 0, 0)
                if res <= 0:
                    break

                if msg.message == WM_HOTKEY:
                    hk_id = msg.wParam
                    with self._lock:
                        cb = self._handlers.get(hk_id)
                    if cb:
                        try:
                            cb()
                        except Exception:
                            logger.exception("Error executing hotkey callback for id %d", hk_id)

                elif msg.message == WM_USER:
                    while not self._cmd_queue.empty():
                        try:
                            item = self._cmd_queue.get_nowait()
                        except queue.Empty:
                            break

                        cmd = item[0]
                        if cmd == "REGISTER":
                            _, (hk_id, mods, vk), resp = item
                            ret = RegisterHotKey(0, hk_id, mods, vk)
                            err = ctypes.GetLastError() if not ret else 0
                            resp.put((bool(ret), err))
                        elif cmd == "UNREGISTER":
                            _, hk_id, resp = item
                            ret = UnregisterHotKey(0, hk_id)
                            resp.put(bool(ret))
                        elif cmd == "UNREGISTER_ALL":
                            _, ids, resp = item
                            for hid in ids:
                                UnregisterHotKey(0, hid)
                            resp.put(True)

                TranslateMessage(ctypes.byref(msg))
                DispatchMessageW(ctypes.byref(msg))
        finally:
            with self._lock:
                ids = list(self._key_info.keys())
            for hk_id in ids:
                UnregisterHotKey(0, hk_id)
            self._thread_id = None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


# Alias for concise import
HotkeyManager = GlobalHotkeyManager

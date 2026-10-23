"""Luna Dimmer - Win32 原生兼容层 (Windows 7 / 8 / 10 / 11, 32 位 / 64 位)

职责：
1. 窗口分层穿透、无激活工具窗样式（32/64 位指针自适应）；
2. Gamma 色温 LUT 的备份 / 应用 / 还原，**覆盖全部已连接显示器**；
3. DWM 毛玻璃、原生拖拽、开机自启、全屏窗口感知。

健壮性约定：
- 所有 Win32 函数均显式声明 argtypes / restype，避免 64 位下句柄与返回值被截断；
- 所有 GDI 句柄统一走 try/finally 释放，绝不泄漏 DC；
- 对外接口永不抛异常（失败返回 False/None），由调用方决定降级策略。
"""

import ctypes
import os
import sys
from ctypes import wintypes
from typing import Dict, List, Optional, Tuple

# ----------------------------------------------------------------------
# Win32 常量
# ----------------------------------------------------------------------
GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x00080000
WS_EX_TRANSPARENT = 0x00000020
WS_EX_NOACTIVATE = 0x08000000
WS_EX_TOOLWINDOW = 0x00000080

REQUIRED_TRANSPARENT_STYLES = WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW

DISPLAY_DEVICE_ATTACHED_TO_DESKTOP = 0x00000001
PRIMARY_DC_KEY = "__primary_dc__"
GAMMA_LUT_SIZE = 768

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32
kernel32 = ctypes.windll.kernel32

# 指针位宽判断 (32位系统为4字节，64位系统为8字节)
POINTER_SIZE = ctypes.sizeof(ctypes.c_void_p)

# 32/64位兼容 SetWindowLong / GetWindowLong 函数签名配置
if POINTER_SIZE == 8:
    GetWindowLong = getattr(user32, "GetWindowLongPtrW", user32.GetWindowLongW)
    SetWindowLong = getattr(user32, "SetWindowLongPtrW", user32.SetWindowLongW)
    GetWindowLong.restype = ctypes.c_int64
    GetWindowLong.argtypes = [wintypes.HWND, ctypes.c_int]
    SetWindowLong.restype = ctypes.c_int64
    SetWindowLong.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_int64]
else:
    GetWindowLong = user32.GetWindowLongW
    SetWindowLong = user32.SetWindowLongW
    GetWindowLong.restype = ctypes.c_long
    GetWindowLong.argtypes = [wintypes.HWND, ctypes.c_int]
    SetWindowLong.restype = ctypes.c_long
    SetWindowLong.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_long]

# DC 与 GDI 函数签名配置
user32.GetDC.restype = wintypes.HDC
user32.GetDC.argtypes = [wintypes.HWND]
user32.ReleaseDC.restype = ctypes.c_int
user32.ReleaseDC.argtypes = [wintypes.HWND, wintypes.HDC]

gdi32.GetDeviceGammaRamp.restype = wintypes.BOOL
gdi32.GetDeviceGammaRamp.argtypes = [wintypes.HDC, ctypes.c_void_p]
gdi32.SetDeviceGammaRamp.restype = wintypes.BOOL
gdi32.SetDeviceGammaRamp.argtypes = [wintypes.HDC, ctypes.c_void_p]

gdi32.CreateDCW.restype = wintypes.HDC
gdi32.CreateDCW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.LPCWSTR, ctypes.c_void_p]
gdi32.DeleteDC.restype = wintypes.BOOL
gdi32.DeleteDC.argtypes = [wintypes.HDC]

# Thread & Hotkey Win32 API 签名配置 (32位与64位系统兼容)
kernel32.GetCurrentThreadId.restype = wintypes.DWORD
kernel32.GetCurrentThreadId.argtypes = []

user32.RegisterHotKey.restype = wintypes.BOOL
user32.RegisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int, wintypes.UINT, wintypes.UINT]

user32.UnregisterHotKey.restype = wintypes.BOOL
user32.UnregisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int]

user32.PeekMessageW.restype = wintypes.BOOL
user32.PeekMessageW.argtypes = [ctypes.POINTER(wintypes.MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT, wintypes.UINT]

user32.GetMessageW.restype = wintypes.BOOL
user32.GetMessageW.argtypes = [ctypes.POINTER(wintypes.MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT]

user32.PostThreadMessageW.restype = wintypes.BOOL
user32.PostThreadMessageW.argtypes = [wintypes.DWORD, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]

user32.TranslateMessage.restype = wintypes.BOOL
user32.TranslateMessage.argtypes = [ctypes.POINTER(wintypes.MSG)]

user32.DispatchMessageW.restype = wintypes.LPARAM
user32.DispatchMessageW.argtypes = [ctypes.POINTER(wintypes.MSG)]

user32.ReleaseCapture.restype = wintypes.BOOL
user32.ReleaseCapture.argtypes = []

user32.SendMessageW.restype = wintypes.LPARAM
user32.SendMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]

user32.GetForegroundWindow.restype = wintypes.HWND
user32.GetForegroundWindow.argtypes = []

user32.GetShellWindow.restype = wintypes.HWND
user32.GetShellWindow.argtypes = []

user32.GetWindowRect.restype = wintypes.BOOL
user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]

user32.MonitorFromWindow.restype = ctypes.c_void_p
user32.MonitorFromWindow.argtypes = [wintypes.HWND, wintypes.DWORD]


class MONITORINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("rcMonitor", wintypes.RECT),
        ("rcWork", wintypes.RECT),
        ("dwFlags", wintypes.DWORD),
    ]


user32.GetMonitorInfoW.restype = wintypes.BOOL
user32.GetMonitorInfoW.argtypes = [ctypes.c_void_p, ctypes.POINTER(MONITORINFO)]


class DISPLAY_DEVICEW(ctypes.Structure):
    """ENUM 显示设备结构（多显示器 Gamma 逐个适配所必需）"""

    _fields_ = [
        ("cb", wintypes.DWORD),
        ("DeviceName", wintypes.WCHAR * 32),
        ("DeviceString", wintypes.WCHAR * 128),
        ("StateFlags", wintypes.DWORD),
        ("DeviceID", wintypes.WCHAR * 128),
        ("DeviceKey", wintypes.WCHAR * 128),
    ]


user32.EnumDisplayDevicesW.restype = wintypes.BOOL
user32.EnumDisplayDevicesW.argtypes = [
    wintypes.LPCWSTR,
    wintypes.DWORD,
    ctypes.POINTER(DISPLAY_DEVICEW),
    wintypes.DWORD,
]


# 导出原生 API 句柄与函数
GetCurrentThreadId = kernel32.GetCurrentThreadId
RegisterHotKey = user32.RegisterHotKey
UnregisterHotKey = user32.UnregisterHotKey
PeekMessageW = user32.PeekMessageW
GetMessageW = user32.GetMessageW
PostThreadMessageW = user32.PostThreadMessageW
TranslateMessage = user32.TranslateMessage
DispatchMessageW = user32.DispatchMessageW
ReleaseCapture = user32.ReleaseCapture
SendMessageW = user32.SendMessageW


def get_system_pointer_size() -> int:
    """返回当前 Python 运行时的指针大小（字节数）。"""
    return POINTER_SIZE


def get_windows_version_name() -> str:
    """
    跨平台精准探测 Windows 版本：
    - Windows 7: major=6, minor=1
    - Windows 8 / 8.1: major=6, minor=2/3
    - Windows 10: major=10, build < 22000
    - Windows 11: major=10, build >= 22000 或 major >= 11
    """
    if sys.platform != "win32":
        return "non_windows"
    try:
        ver = sys.getwindowsversion()
        if ver.major == 6 and ver.minor == 1:
            return "win7"
        elif ver.major == 6:
            return "win8"
        elif ver.major == 10:
            if getattr(ver, "build", 0) >= 22000:
                return "win11"
            return "win10"
        elif ver.major > 10:
            return "win11"
    except Exception:
        pass
    return "win10"


def is_dwm_composition_enabled() -> bool:
    """检测 Windows DWM 桌面窗口合成是否启用 (Windows 7 Aero 状态感知)"""
    if sys.platform != "win32":
        return False
    try:
        dwmapi = ctypes.windll.dwmapi
        enabled = ctypes.c_bool(False)
        res = dwmapi.DwmIsCompositionEnabled(ctypes.byref(enabled))
        if res == 0:
            return bool(enabled.value)
    except Exception:
        pass
    return True


def set_window_transparent_clickthrough(hwnd: int) -> bool:
    """
    将指定窗口设置为完全穿透（不接收任何鼠标事件、分层窗口、ToolWindow且无激活边框）。
    通过二次读取 GetWindowLong 确认样式是否已包含目标属性，避免旧样式为 0 时误判。
    """
    try:
        ex_style = GetWindowLong(hwnd, GWL_EXSTYLE)
        target_style = ex_style | REQUIRED_TRANSPARENT_STYLES
        SetWindowLong(hwnd, GWL_EXSTYLE, target_style)
        updated_style = GetWindowLong(hwnd, GWL_EXSTYLE)
        return (updated_style & REQUIRED_TRANSPARENT_STYLES) == REQUIRED_TRANSPARENT_STYLES
    except Exception:
        return False


# ----------------------------------------------------------------------
# 多显示器 Gamma 通道
# ----------------------------------------------------------------------
def _acquire_display_dcs() -> List[Tuple[str, int]]:
    """
    枚举所有接管桌面的显示设备并为其创建独立 DC。
    返回 [(device_name, hdc), ...]；全部失败时回退到 `GetDC(0)` 主屏 DC。
    调用方必须通过 `_release_display_dcs` 释放。
    """
    dcs: List[Tuple[str, int]] = []
    try:
        index = 0
        while index < 64:
            device = DISPLAY_DEVICEW()
            device.cb = ctypes.sizeof(DISPLAY_DEVICEW)
            if not user32.EnumDisplayDevicesW(None, index, ctypes.byref(device), 0):
                break
            index += 1
            if not (device.StateFlags & DISPLAY_DEVICE_ATTACHED_TO_DESKTOP):
                continue
            hdc = gdi32.CreateDCW(str(device.DeviceName), None, None, None)
            if hdc:
                dcs.append((str(device.DeviceName), hdc))
    except Exception:
        dcs = []

    if not dcs:
        try:
            hdc = user32.GetDC(0)
            if hdc:
                dcs.append((PRIMARY_DC_KEY, hdc))
        except Exception:
            pass
    return dcs


def _release_display_dcs(dcs: List[Tuple[str, int]]) -> None:
    """释放由 `_acquire_display_dcs` 创建的全部 DC，绝不泄漏 GDI 句柄"""
    for name, hdc in dcs:
        try:
            if name == PRIMARY_DC_KEY:
                user32.ReleaseDC(0, hdc)
            else:
                gdi32.DeleteDC(hdc)
        except Exception:
            pass


def calculate_gamma_ramp(warmth: int, brightness_factor: float = 1.0) -> List[List[int]]:
    """
    计算三通道伽马查找表 (LUT)。
    warmth: 0 ~ 100 琥珀色温加权 (0 为中性白平衡，100 为深度烛光护眼)
    brightness_factor: 0.05 ~ 1.0 伽马亮度加权
    返回: [red_list, green_list, blue_list]，每个列表包含 256 个 WORD (0~65535)
    """
    warmth = max(0, min(100, int(warmth)))
    brightness_factor = max(0.05, min(1.0, float(brightness_factor)))

    r_factor = 1.0 * brightness_factor
    g_factor = (1.0 - (warmth / 100.0) * 0.15) * brightness_factor
    b_factor = (1.0 - (warmth / 100.0) * 0.50) * brightness_factor

    red = [min(65535, int((i / 255.0) * 65535 * r_factor)) for i in range(256)]
    green = [min(65535, int((i / 255.0) * 65535 * g_factor)) for i in range(256)]
    blue = [min(65535, int((i / 255.0) * 65535 * b_factor)) for i in range(256)]

    return [red, green, blue]


# 主屏原始曲线（兼容旧接口 / 旧版崩溃守护备份文件）
_original_gamma_ramp: Optional[List[int]] = None
# 每台显示器各自独立的原始曲线（多屏无痕还原的关键）
_original_gamma_ramps: Dict[str, List[int]] = {}


def _apply_ramps_to_displays(ramps: Dict[str, List[int]]) -> bool:
    """把给定曲线应用到全部显示器；缺失的设备名回退使用字典中的任意一条曲线"""
    if not ramps:
        return False
    fallback = next(iter(ramps.values()))
    dcs = _acquire_display_dcs()
    if not dcs:
        return False

    applied = False
    try:
        for name, hdc in dcs:
            ramp_data = ramps.get(name) or fallback
            if not ramp_data or len(ramp_data) != GAMMA_LUT_SIZE:
                continue
            try:
                ramp = (wintypes.WORD * GAMMA_LUT_SIZE)(*[max(0, min(65535, int(v))) for v in ramp_data])
                if gdi32.SetDeviceGammaRamp(hdc, ctypes.byref(ramp)):
                    applied = True
            except Exception:
                continue
    finally:
        _release_display_dcs(dcs)
    return applied


def backup_system_gamma() -> bool:
    """备份系统当前**每台显示器**的原始 Gamma 曲线，确保退出或异常时可无损还原"""
    global _original_gamma_ramp, _original_gamma_ramps

    dcs = _acquire_display_dcs()
    if not dcs:
        return False

    ramps: Dict[str, List[int]] = {}
    try:
        for name, hdc in dcs:
            try:
                ramp = (wintypes.WORD * GAMMA_LUT_SIZE)()
                if gdi32.GetDeviceGammaRamp(hdc, ctypes.byref(ramp)):
                    ramps[name] = [int(ramp[i]) for i in range(GAMMA_LUT_SIZE)]
            except Exception:
                continue
    finally:
        _release_display_dcs(dcs)

    if not ramps:
        # 极端驱动环境下 GetDeviceGammaRamp 可能全部失败：退化为「标准中性曲线」备份，
        # 保证退出/崩溃时仍能把屏幕从暖色 LUT 拉回中性，而不是无备份可还原。
        identity_channel = [min(65535, int((i / 255.0) * 65535)) for i in range(256)]
        ramps = {PRIMARY_DC_KEY: identity_channel * 3}

    _original_gamma_ramps = ramps
    _original_gamma_ramp = next(iter(ramps.values()))
    return True


def restore_system_gamma() -> bool:
    """恢复之前备份的系统原始 Gamma 曲线（多屏逐一还原）"""
    if _original_gamma_ramps:
        return _apply_ramps_to_displays(_original_gamma_ramps)
    if _original_gamma_ramp is not None:
        return restore_gamma_from_data(_original_gamma_ramp)
    return False


def get_backup_gamma() -> Optional[List[int]]:
    """获取当前内存中已备份的主屏原始 Gamma 曲线数组"""
    return _original_gamma_ramp


def get_backup_gamma_map() -> Dict[str, List[int]]:
    """获取当前内存中已备份的全部显示器 Gamma 曲线映射"""
    return dict(_original_gamma_ramps)


def restore_gamma_from_data(ramp_list: List[int]) -> bool:
    """根据给定的 768 长度 Gamma 数组向系统底层恢复色彩曲线（应用到所有显示器）"""
    if not ramp_list or len(ramp_list) != GAMMA_LUT_SIZE:
        return False
    return _apply_ramps_to_displays({PRIMARY_DC_KEY: list(ramp_list)})


def save_backup_gamma_to_file(filepath: str) -> bool:
    """将系统原始 Gamma 备份保存至磁盘临时文件，供独立崩溃守护进程使用（多屏映射格式）"""
    global _original_gamma_ramp
    if not _original_gamma_ramps:
        if not backup_system_gamma():
            return False
    try:
        import json
        payload = {
            "version": 2,
            "primary": _original_gamma_ramp,
            "ramps": _original_gamma_ramps,
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(payload, f)
        return True
    except Exception:
        return False


def restore_gamma_from_file(filepath: str) -> bool:
    """从磁盘文件读取原始 Gamma 并向系统恢复（同时兼容 v1 纯数组与 v2 多屏映射）"""
    try:
        import json
        if not os.path.exists(filepath):
            return False
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, dict):
            ramps = data.get("ramps")
            if isinstance(ramps, dict) and ramps:
                parsed = {
                    str(k): [int(v) for v in values]
                    for k, values in ramps.items()
                    if isinstance(values, list) and len(values) == GAMMA_LUT_SIZE
                }
                if parsed:
                    return _apply_ramps_to_displays(parsed)
            primary = data.get("primary")
            if isinstance(primary, list):
                return restore_gamma_from_data(primary)
            return False

        if isinstance(data, list):
            return restore_gamma_from_data(data)
        return False
    except Exception:
        return False


def set_display_gamma_ramp(warmth_percent: int, brightness_percent: float = 100.0) -> bool:
    """
    计算并向**所有已连接显示器**应用 Gamma 曲线。
    若尚未备份原始 Gamma，则自动先进行备份。
    warmth_percent: 0 ~ 100
    brightness_percent: 0.0 ~ 1.0 浮点因子，或 >1.0 时的 0~100 百分比
    """
    if not _original_gamma_ramps:
        backup_system_gamma()

    if brightness_percent > 1.0:
        b_factor = brightness_percent / 100.0
    else:
        b_factor = brightness_percent

    red, green, blue = calculate_gamma_ramp(warmth_percent, b_factor)
    return _apply_ramps_to_displays({PRIMARY_DC_KEY: red + green + blue})


# ----------------------------------------------------------------------
# DWM 毛玻璃 / 原生拖拽
# ----------------------------------------------------------------------
class ACCENT_POLICY(ctypes.Structure):
    _fields_ = [
        ("AccentState", ctypes.c_int),
        ("AccentFlags", ctypes.c_int),
        ("GradientColor", ctypes.c_int),
        ("AnimationId", ctypes.c_int),
    ]


class WINCOMPATTRDATA(ctypes.Structure):
    _fields_ = [
        ("Attribute", ctypes.c_int),
        ("Data", ctypes.c_void_p),
        ("SizeOfData", ctypes.c_size_t),
    ]


_wca_configured = False
_set_window_composition_attribute = None


def enable_acrylic_blur(hwnd: int, gradient_color: int = 0xAA14151A) -> bool:
    """
    为窗口句柄启用 Windows 10/11 真实物理光学毛玻璃模糊 (DWM Acrylic / BlurBehind)。
    透视桌面背后的实际壁纸与窗口，呈现深邃磨砂质感。
    """
    global _wca_configured, _set_window_composition_attribute
    try:
        if not _wca_configured:
            _set_window_composition_attribute = getattr(user32, "SetWindowCompositionAttribute", None)
            if _set_window_composition_attribute is not None:
                _set_window_composition_attribute.restype = wintypes.BOOL
                _set_window_composition_attribute.argtypes = [wintypes.HWND, ctypes.POINTER(WINCOMPATTRDATA)]
            _wca_configured = True

        if _set_window_composition_attribute is None:
            return False

        accent = ACCENT_POLICY()
        accent.AccentState = 3  # ACCENT_ENABLE_BLURBEHIND (平滑光学漫反射毛玻璃)
        accent.AccentFlags = 2
        accent.GradientColor = gradient_color
        accent.AnimationId = 0

        data = WINCOMPATTRDATA()
        data.Attribute = 19  # WCA_ACCENT_POLICY
        data.Data = ctypes.cast(ctypes.pointer(accent), ctypes.c_void_p)
        data.SizeOfData = ctypes.sizeof(accent)

        return bool(_set_window_composition_attribute(int(hwnd), ctypes.byref(data)))
    except Exception:
        return False


def start_window_drag(hwnd: int) -> None:
    """
    调用 Win32 原生 WM_NCLBUTTONDOWN + HTCAPTION，启用 DWM 内核硬件加速拖拽。
    彻底消灭软拖拽在半透明窗口下的掉帧、撕裂与鼠标粘滞卡顿。
    """
    try:
        user32.ReleaseCapture()
        user32.SendMessageW(wintypes.HWND(hwnd), 0x00A1, 2, 0)
    except Exception:
        pass


# ----------------------------------------------------------------------
# 开机自启
# ----------------------------------------------------------------------
def resolve_autostart_command() -> str:
    """
    构造开机自启命令行。

    - 冻结（PyInstaller）运行：直接指向 exe 本体；
    - 源码运行：必须显式带上 `src/main.py` 的**绝对路径**，
      否则注册表 Run 项会以 `C:\\Windows\\System32` 作为工作目录，
      `-m src.main` 会因找不到包而静默失败（注册成一个空转的 python 进程）。
    """
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}" --silent'

    # __file__ = <root>/src/platform/win32_compat.py → 向上三级才是工程根目录
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    entry_script = os.path.join(project_root, "src", "main.py")
    python_exe = sys.executable
    # 源码模式优先使用 pythonw.exe，避免登录时闪出黑色控制台窗口
    pythonw = os.path.join(os.path.dirname(python_exe), "pythonw.exe")
    if os.path.exists(pythonw):
        python_exe = pythonw
    return f'"{python_exe}" "{entry_script}" --silent'


def set_windows_autostart(app_name: str = "LunaDimmer", enabled: bool = True) -> bool:
    """在 Windows 当前用户注册表 Run 项中安全配置开机自启"""
    import winreg

    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
        try:
            if enabled:
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, resolve_autostart_command())
            else:
                try:
                    winreg.DeleteValue(key, app_name)
                except FileNotFoundError:
                    pass
        finally:
            winreg.CloseKey(key)
        return True
    except Exception:
        return False


def is_autostart_enabled(app_name: str = "LunaDimmer") -> Optional[str]:
    """读取当前注册表中的自启命令行；未配置时返回 None"""
    import winreg

    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_QUERY_VALUE)
        try:
            value, _ = winreg.QueryValueEx(key, app_name)
            return str(value)
        finally:
            winreg.CloseKey(key)
    except FileNotFoundError:
        return None
    except Exception:
        return None


# ----------------------------------------------------------------------
# 全屏窗口感知
# ----------------------------------------------------------------------
def is_fullscreen_window_active() -> bool:
    """
    检测当前前台焦点窗口是否处于全屏独占模式（如全屏 3D 游戏、全屏电影播放或 PPT 演讲）。
    当处于全屏独占时，快捷键自动降级为平滑后台调光，绝不强制弹出主面板抢夺键鼠焦点。
    """
    try:
        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return False
        shell_hwnd = user32.GetShellWindow()
        if hwnd == shell_hwnd:
            return False

        rect = wintypes.RECT()
        if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
            return False

        h_mon = user32.MonitorFromWindow(hwnd, 2)  # MONITOR_DEFAULTTONEAREST
        if not h_mon:
            return False

        mi = MONITORINFO()
        mi.cbSize = ctypes.sizeof(MONITORINFO)
        if not user32.GetMonitorInfoW(h_mon, ctypes.byref(mi)):
            return False

        m = mi.rcMonitor
        # 前台窗口完全覆盖或超出所在屏幕显示区域
        return (rect.left <= m.left and rect.top <= m.top and
                rect.right >= m.right and rect.bottom >= m.bottom)
    except Exception:
        return False

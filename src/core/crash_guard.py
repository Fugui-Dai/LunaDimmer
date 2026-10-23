"""
Luna Dimmer - 崩溃自愈与急救防护守护进程 (Crash Guardian Sentinel)

设计原则与责任：
1. 作为一个轻量级、零界面的后台守护子进程，监听主进程 PID。
2. 阻塞在 Windows 内核级 WaitForSingleObject 上，不消耗 CPU。
3. 若主进程发生异常崩溃、闪退或被非正常终止（clean_flag 文件未生成）：
   - 守护进程在毫秒级感知，立即调用硬件接口还原屏幕初始硬件物理亮度；
   - 恢复系统原始 Gamma 色温曲线，确保所有软件调光设置全部失效；
   - 清理临时凭证，自毁退出。
4. 若主进程正常退出（检测到 clean_flag），守护进程静默退出并清理标志。

健壮性保障：
- 所有 Win32 调用均显式声明 argtypes/restype（64 位下 HANDLE 不再被截断）；
- 严格判断 WaitForSingleObject 返回值，`WAIT_FAILED` 时退化为轮询探测，
  绝不在主程序仍存活时误判「已崩溃」而提前还原屏幕；
- 单进程内复用同一份 768 长度 LUT，避免重复读取磁盘。
"""

import ctypes
import os
import sys
import time
from ctypes import wintypes

SYNCHRONIZE = 0x00100000
WAIT_OBJECT_0 = 0x00000000
WAIT_ABANDONED = 0x00000080
WAIT_TIMEOUT = 0x00000102
WAIT_FAILED = 0xFFFFFFFF
INFINITE = 0xFFFFFFFF
ERROR_INVALID_PARAMETER = 87

_kernel32 = ctypes.windll.kernel32
_kernel32.OpenProcess.restype = wintypes.HANDLE
_kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
_kernel32.WaitForSingleObject.restype = wintypes.DWORD
_kernel32.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
_kernel32.CloseHandle.restype = wintypes.BOOL
_kernel32.CloseHandle.argtypes = [wintypes.HANDLE]


def _open_process(pid: int):
    """以 SYNCHRONIZE 权限打开目标进程句柄，失败返回 None"""
    try:
        handle = _kernel32.OpenProcess(SYNCHRONIZE, False, int(pid))
        return handle or None
    except Exception:
        return None


def _is_process_alive(pid: int) -> bool:
    """轻量探测目标 PID 是否仍存活（不消耗 CPU，无需轮询全部进程）"""
    handle = _open_process(pid)
    if not handle:
        return False
    _kernel32.CloseHandle(handle)
    return True


def restore_screen(initial_brightness: int, gamma_file: str) -> None:
    """系统崩溃或异常闪退时：恢复屏幕之前的物理亮度和色温，所有软件设置全部失效"""
    # 1. 恢复物理背光亮度
    try:
        import screen_brightness_control as sbc
        sbc.set_brightness(initial_brightness)
    except Exception:
        pass

    # 2. 恢复系统原始 Gamma 色温曲线
    try:
        from src.platform.win32_compat import restore_gamma_from_file
        if os.path.exists(gamma_file):
            restore_gamma_from_file(gamma_file)
    except Exception:
        pass


def _cleanup_files(clean_flag_file: str, gamma_file: str) -> None:
    for path in (clean_flag_file, gamma_file):
        if path and os.path.exists(path):
            try:
                os.remove(path)
            except Exception:
                pass


def run_guard(args: list) -> None:
    """守护主循环，阻塞等待主进程退出"""
    if len(args) < 4:
        sys.exit(0)

    try:
        target_pid = int(args[0])
        initial_brightness = int(args[1])
        gamma_file = args[2]
        clean_flag_file = args[3]
    except Exception:
        sys.exit(1)

    if sys.platform != "win32":
        sys.exit(0)

    handle = _open_process(target_pid)
    if not handle:
        # 主进程若在此前已不存在，检查是否为干净退出
        if not os.path.exists(clean_flag_file):
            restore_screen(initial_brightness, gamma_file)
        _cleanup_files(clean_flag_file, gamma_file)
        sys.exit(0)

    exited = False
    try:
        # 无限等待主进程句柄（Windows 内核挂起，不占 CPU）
        wait_result = _kernel32.WaitForSingleObject(handle, INFINITE)
        if wait_result in (WAIT_OBJECT_0, WAIT_ABANDONED):
            exited = True
        elif wait_result == WAIT_FAILED:
            # 等待失败（极端环境/句柄异常）：退化为低频轮询，绝不误判为已崩溃
            deadline = time.time() + 24 * 3600
            while time.time() < deadline:
                if not _is_process_alive(target_pid):
                    exited = True
                    break
                time.sleep(0.25)
    finally:
        try:
            _kernel32.CloseHandle(handle)
        except Exception:
            pass

    if not exited:
        # 探测超时仍未确认退出：不做任何破坏性还原，直接静默退出
        sys.exit(0)

    # 短暂让步 100ms，以确保主进程正常退出流程（写入 clean_flag）执行完毕
    time.sleep(0.1)

    if not os.path.exists(clean_flag_file):
        # 主进程异常崩溃或强行终止！立刻恢复屏幕初始物理亮度和色温，使软件设置全部失效！
        restore_screen(initial_brightness, gamma_file)

    # 清理 clean_flag 与 Gamma 备份文件
    _cleanup_files(clean_flag_file, gamma_file)


def main():
    run_guard(sys.argv[1:])


if __name__ == "__main__":
    main()

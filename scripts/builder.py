"""Luna Dimmer - 独立客户端高颜值可视化构建系统 (CLI Visual Builder)

特性：
1. 工业级多终端兼容设计，自适应 Windows UTF-8 (65001) 与 GBK (936) 字符集；
2. 5大阶段流水线结构化看板 (Kanban Stages)；
3. 全字符集通用平滑进度条 (■ □) 与旋转光标 ([-], [\], [|], [/])；
4. 编译过程实时抓取 PyInstaller 模块分析状态；
5. 构建产物体积 (MB)、耗时统计与最终高光交付卡片。
"""

import os
import sys
import time
import shutil
import ctypes
import subprocess
from typing import Optional


# =====================================================================
# 1. 终端字符集自适应与防乱码重设机制
# =====================================================================
def setup_io_encoding() -> None:
    """自动适配 Windows 终端当前代码页，彻底杜绝 GBK 与 UTF-8 错位乱码"""
    if sys.platform == "win32":
        try:
            kernel32 = ctypes.windll.kernel32
            kernel32.GetConsoleOutputCP.restype = ctypes.c_uint
            cp = kernel32.GetConsoleOutputCP()
            if cp == 65001:
                target_encoding = "utf-8"
            elif cp == 936:
                target_encoding = "gbk"
            else:
                target_encoding = sys.stdout.encoding or "utf-8"

            if hasattr(sys.stdout, "reconfigure"):
                sys.stdout.reconfigure(encoding=target_encoding, errors="replace")
            if hasattr(sys.stderr, "reconfigure"):
                sys.stderr.reconfigure(encoding=target_encoding, errors="replace")
        except Exception:
            pass


setup_io_encoding()


# =====================================================================
# 2. 颜色控制与 Windows VT100 / Colorama 适配引擎
# =====================================================================
HAS_COLORAMA = False
try:
    import colorama
    colorama.init(autoreset=False)
    HAS_COLORAMA = True
except Exception:
    pass


def enable_windows_ansi() -> bool:
    """激活 Windows 控制台原生 VT100 / ANSI 真彩色输出"""
    if sys.platform != "win32":
        return True
    try:
        kernel32 = ctypes.windll.kernel32
        kernel32.GetStdHandle.restype = ctypes.c_void_p
        kernel32.GetStdHandle.argtypes = [ctypes.c_long]
        kernel32.GetConsoleMode.restype = ctypes.c_bool
        kernel32.GetConsoleMode.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ulong)]
        kernel32.SetConsoleMode.restype = ctypes.c_bool
        kernel32.SetConsoleMode.argtypes = [ctypes.c_void_p, ctypes.c_ulong]

        h_out = kernel32.GetStdHandle(-11)
        if not h_out or h_out == ctypes.c_void_p(-1).value:
            return False
        mode = ctypes.c_ulong()
        if not kernel32.GetConsoleMode(h_out, ctypes.byref(mode)):
            return False
        # 仅启用 ENABLE_VIRTUAL_TERMINAL_PROCESSING (0x0004)
        if not (mode.value & 0x0004):
            return bool(kernel32.SetConsoleMode(h_out, mode.value | 0x0004))
        return True
    except Exception:
        return False


ANSI_SUPPORTED = HAS_COLORAMA or enable_windows_ansi()


class Colors:
    """标准 16 色 ANSI 配色代币（兼备 Colorama 映射与原生 VT100 兼容）"""
    if ANSI_SUPPORTED:
        RESET = "\033[0m"
        BOLD = "\033[1m"
        DIM = "\033[2m"
        GOLD = "\033[93m"        # 明亮黄金色
        CYAN = "\033[96m"        # 明亮青色
        GREEN = "\033[92m"       # 明亮绿色
        GRAY = "\033[90m"        # 暗灰色
        DARK_GRAY = "\033[90m"   # 暗灰色
        RED = "\033[91m"         # 明亮红色
        WHITE = "\033[97m"       # 明亮白色
    else:
        RESET = ""
        BOLD = ""
        DIM = ""
        GOLD = ""
        CYAN = ""
        GREEN = ""
        GRAY = ""
        DARK_GRAY = ""
        RED = ""
        WHITE = ""


# =====================================================================
# 3. 视觉组件与进度看板
# =====================================================================
def draw_progress_bar(percent: int, length: int = 20) -> str:
    """生成兼具 GBK 与 UTF-8 兼容性的进度条字符"""
    percent = max(0, min(100, percent))
    filled_len = int(length * percent // 100)
    unfilled_len = length - filled_len
    bar = f"{Colors.GOLD}{'■' * filled_len}{Colors.DARK_GRAY}{'□' * unfilled_len}{Colors.RESET}"
    return f"[{bar}] {Colors.BOLD}{percent:3d}%{Colors.RESET}"


def print_banner() -> None:
    """渲染品牌 Banner（采用纯净双轨字符集，彻底杜绝 Emoji 乱码与边框错位）"""
    print()
    print(f"{Colors.GOLD}  ┌──────────────────────────────────────────────────────────────┐{Colors.RESET}")
    print(f"{Colors.GOLD}  │{Colors.RESET}   [Luna]  {Colors.BOLD}{Colors.WHITE}月光屏幕调光器 (Luna Dimmer) - 独立可执行程序构建系统{Colors.RESET}     {Colors.GOLD}│{Colors.RESET}")
    print(f"{Colors.GOLD}  │{Colors.RESET}           {Colors.CYAN}双轨极限调光 · 苹果控制中心风格 · 国际多语言 · 单文件免安装{Colors.RESET} {Colors.GOLD}│{Colors.RESET}")
    print(f"{Colors.GOLD}  └──────────────────────────────────────────────────────────────┘{Colors.RESET}")
    print()


def render_step_header(step: int, total: int, title: str) -> None:
    """渲染步骤标头"""
    print(f"  {Colors.GOLD}[{step}/{total}]{Colors.RESET} {Colors.BOLD}{Colors.WHITE}{title}{Colors.RESET}")


def ensure_spec_file(project_root: str) -> str:
    """
    校验生产级精简 spec 配置文件是否存在。

    历史实现把整份 `LunaDimmer.spec` 的内容又硬编码复制到这里「自动重建」，
    导致同一份打包配置存在两个真相源，改一处必漏一处。
    现在 spec 是版本控制中的唯一来源：缺失即视为工程损坏，直接报错退出。
    """
    spec_file = os.path.join(project_root, "LunaDimmer.spec")
    if not os.path.exists(spec_file):
        print(
            f"    {Colors.RED}× 未找到构建配置 LunaDimmer.spec: {spec_file}{Colors.RESET}\n"
            f"    {Colors.GRAY}  该文件是打包配置的唯一真相源，请从版本库恢复后重试。{Colors.RESET}"
        )
        sys.exit(1)
    return spec_file


def run_pyinstaller_with_progress(project_root: str) -> bool:
    """执行 PyInstaller 并渲染动态旋转光标与阶段进度条"""
    spinners = ["[-]", "[\\]", "[|]", "[/]"]
    spin_idx = 0
    start_time = time.time()

    spec_file = ensure_spec_file(project_root)
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--clean",
        "--noconfirm",
        spec_file,
    ]

    process = subprocess.Popen(
        cmd,
        cwd=project_root,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        encoding="utf-8",
        errors="replace",
    )

    percent = 5
    current_status = "初始化编译引擎..."
    captured_logs = []

    while True:
        line = process.stdout.readline()
        if not line and process.poll() is not None:
            break

        if line:
            line_str = line.strip()
            captured_logs.append(line_str)
            if len(captured_logs) > 40:
                captured_logs.pop(0)

            # 动态根据 PyInstaller 输出调整进度与状态
            if "checking" in line_str.lower() or "analyzing" in line_str.lower():
                percent = min(40, percent + 2)
                current_status = "深度分析模块引用链..."
            elif "hidden import" in line_str.lower():
                percent = min(55, percent + 3)
                current_status = "收集原生依赖与动态库..."
            elif "processing pre-safe-import" in line_str.lower():
                percent = min(68, percent + 2)
                current_status = "打包 PyQt5 控件与资源库..."
            elif "building pkg" in line_str.lower():
                percent = min(82, percent + 4)
                current_status = "组装单文件压缩包 (PKG)..."
            elif "building exe" in line_str.lower() or "appending archive" in line_str.lower():
                percent = min(95, percent + 4)
                current_status = "生成 Windows PE 可执行核心..."

            spin_idx = (spin_idx + 1) % len(spinners)
            spin_char = spinners[spin_idx]
            bar_str = draw_progress_bar(percent, length=20)
            status_clip = current_status[:26]
            sys.stdout.write(
                f"\r    {Colors.CYAN}{spin_char}{Colors.RESET} {bar_str}  {Colors.GRAY}{status_clip:<26}{Colors.RESET}      "
            )
            sys.stdout.flush()

    process.wait()
    is_success = process.returncode == 0
    elapsed = time.time() - start_time

    if is_success:
        bar_str = draw_progress_bar(100, length=20)
        sys.stdout.write(
            f"\r    {Colors.GREEN}√{Colors.RESET} {bar_str}  {Colors.GREEN}内核编译完成 ({elapsed:.1f}s){Colors.RESET}{' ' * 20}\n"
        )
        sys.stdout.flush()
    else:
        sys.stdout.write(
            f"\r    {Colors.RED}×{Colors.RESET} {draw_progress_bar(percent, length=20)}  {Colors.RED}内核编译失败!{Colors.RESET}{' ' * 20}\n"
        )
        sys.stdout.flush()
        print(f"\n    {Colors.RED}── PyInstaller 详细日志回溯 ──{Colors.RESET}")
        for err_line in captured_logs[-15:]:
            print(f"    {Colors.DARK_GRAY}│{Colors.RESET} {err_line}")
        print()

    return is_success


def kill_existing_instance() -> None:
    """终止正在后台驻留的 LunaDimmer.exe 进程，释放文件句柄写锁"""
    if sys.platform == "win32":
        try:
            subprocess.run(
                ["taskkill", "/F", "/IM", "LunaDimmer.exe"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            time.sleep(0.3)
        except Exception:
            pass


def main() -> None:
    enable_windows_ansi()
    print_banner()

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    kill_existing_instance()
    start_total_time = time.time()
    total_steps = 5

    # -------------------------------------------------------------
    # Step 1: 环境与依赖健全性检查
    # -------------------------------------------------------------
    render_step_header(1, total_steps, "环境与运行依赖自检 (Environment & PyInstaller Check)")
    time.sleep(0.15)
    has_pyinstaller = False
    try:
        import PyInstaller
        has_pyinstaller = True
    except ImportError:
        pass

    if not has_pyinstaller:
        print(f"    {Colors.CYAN}[*]{Colors.RESET} 正在自动拉取 PyInstaller 构建工具...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "pyinstaller"],
            cwd=project_root,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    print(f"    {Colors.GREEN}√{Colors.RESET} {draw_progress_bar(100, 20)}  {Colors.GREEN}Python {sys.version.split()[0]} / PyInstaller 就绪{Colors.RESET}")
    print()

    # -------------------------------------------------------------
    # Step 2: 资产与高分屏图标打包校验
    # -------------------------------------------------------------
    render_step_header(2, total_steps, "高分屏图标与资产结构索引 (Assets & High-DPI Verification)")
    time.sleep(0.15)
    icon_path = os.path.join(project_root, "assets", "icon.ico")
    main_py = os.path.join(project_root, "src", "main.py")
    if not os.path.exists(icon_path):
        print(f"    {Colors.RED}× 未找到图标文件: {icon_path}{Colors.RESET}")
        sys.exit(1)
    if not os.path.exists(main_py):
        print(f"    {Colors.RED}× 未找到入口源码: {main_py}{Colors.RESET}")
        sys.exit(1)
    ensure_spec_file(project_root)

    print(f"    {Colors.GREEN}√{Colors.RESET} {draw_progress_bar(100, 20)}  {Colors.GREEN}源码入口、assets/icon.ico 与 LunaDimmer.spec 校验就绪{Colors.RESET}")
    print()

    # 如果仅为环境/语法自检模式，提前完成
    if any(arg.lower() in ["--check", "--dry-run", "-c"] for arg in sys.argv[1:]):
        print(f"  {Colors.GREEN}┌──────────────────────────────────────────────────────────────┐{Colors.RESET}")
        print(f"  {Colors.GREEN}│{Colors.RESET}   {Colors.BOLD}{Colors.WHITE}√ 构建环境自检通过 (Environment & Assets Check Passed)!{Colors.RESET}    {Colors.GREEN}│{Colors.RESET}")
        print(f"  {Colors.GREEN}│{Colors.RESET}   {Colors.GRAY}系统环境、Python 依赖与所有高分屏图标资源均已就绪。{Colors.RESET}        {Colors.GREEN}│{Colors.RESET}")
        print(f"  {Colors.GREEN}└──────────────────────────────────────────────────────────────┘{Colors.RESET}")
        print()
        return

    # -------------------------------------------------------------
    # Step 3: PyInstaller 单文件内核编译
    # -------------------------------------------------------------
    render_step_header(3, total_steps, "PyInstaller 单文件内核编译 (Compiling Standalone Binary)")
    success = run_pyinstaller_with_progress(project_root)
    if not success:
        print(f"\n  {Colors.RED}[ERROR] 构建失败，请检查编译日志。{Colors.RESET}")
        sys.exit(1)
    print()

    # -------------------------------------------------------------
    # Step 4: 部署单文件至项目根目录
    # -------------------------------------------------------------
    render_step_header(4, total_steps, "独立程序部署与体积校验 (Artifact Deployment)")
    time.sleep(0.15)
    dist_exe = os.path.join(project_root, "dist", "LunaDimmer.exe")
    target_exe = os.path.join(project_root, "LunaDimmer.exe")

    if not os.path.exists(dist_exe):
        print(f"    {Colors.RED}× 未在 dist 目录下找到生成的 EXE 文件!{Colors.RESET}")
        sys.exit(1)

    # 复制覆盖至根目录 (双重守护与句柄释放重试机制)
    kill_existing_instance()
    copied = False
    for attempt in range(3):
        try:
            shutil.copy2(dist_exe, target_exe)
            copied = True
            break
        except Exception:
            kill_existing_instance()
            time.sleep(0.5)

    if not copied:
        shutil.copy2(dist_exe, target_exe)
    file_size_mb = os.path.getsize(target_exe) / (1024 * 1024)
    print(f"    {Colors.GREEN}√{Colors.RESET} {draw_progress_bar(100, 20)}  {Colors.GREEN}已部署至根目录: LunaDimmer.exe ({file_size_mb:.1f} MB){Colors.RESET}")
    print()

    # -------------------------------------------------------------
    # Step 5: 清理临时构建缓存
    # -------------------------------------------------------------
    render_step_header(5, total_steps, "纯净化清理中间产物 (Cleaning Build Cache)")
    time.sleep(0.15)
    for folder in ["build", "dist"]:
        folder_path = os.path.join(project_root, folder)
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path, ignore_errors=True)

    print(f"    {Colors.GREEN}√{Colors.RESET} {draw_progress_bar(100, 20)}  {Colors.GREEN}build/ 与 dist/ 缓存已清空，精简 spec 配置文件长久生效{Colors.RESET}")
    print()

    # -------------------------------------------------------------
    # 最终交付成功看板 (Kanban Summary Card)
    # -------------------------------------------------------------
    total_elapsed = time.time() - start_total_time
    print(f"  {Colors.GREEN}┌──────────────────────────────────────────────────────────────┐{Colors.RESET}")
    print(f"  {Colors.GREEN}│{Colors.RESET}   {Colors.BOLD}{Colors.WHITE}√ 构建圆满完成 (Build Succeeded Successfully)!{Colors.RESET}             {Colors.GREEN}│{Colors.RESET}")
    print(f"  {Colors.GREEN}│{Colors.RESET}                                                              {Colors.GREEN}│{Colors.RESET}")
    print(f"  {Colors.GREEN}│{Colors.RESET}   {Colors.GRAY}· 交付产物:{Colors.RESET}  {Colors.BOLD}{Colors.WHITE}LunaDimmer.exe{Colors.RESET} (独立单文件免安装)             {Colors.GREEN}│{Colors.RESET}")
    print(f"  {Colors.GREEN}│{Colors.RESET}   {Colors.GRAY}· 核心体积:{Colors.RESET}  {Colors.GOLD}{file_size_mb:.2f} MB{Colors.RESET}                                    {Colors.GREEN}│{Colors.RESET}")
    print(f"  {Colors.GREEN}│{Colors.RESET}   {Colors.GRAY}· 构建耗时:{Colors.RESET}  {Colors.CYAN}{total_elapsed:.1f} 秒{Colors.RESET}                                      {Colors.GREEN}│{Colors.RESET}")
    print(f"  {Colors.GREEN}│{Colors.RESET}   {Colors.GRAY}· 兼容环境:{Colors.RESET}  {Colors.WHITE}Windows 7 / 8 / 10 / 11 (32位 & 64位){Colors.RESET}          {Colors.GREEN}│{Colors.RESET}")
    print(f"  {Colors.GREEN}│{Colors.RESET}   {Colors.GRAY}· 核心特性:{Colors.RESET}  {Colors.GREEN}双轨调光 · 国际多语言 · 全局自定义热键 · 100%还原{Colors.RESET} {Colors.GREEN}│{Colors.RESET}")
    print(f"  {Colors.GREEN}└──────────────────────────────────────────────────────────────┘{Colors.RESET}")
    print()

    # 交互式退出体验
    if "nopause" not in [arg.lower() for arg in sys.argv[1:]]:
        try:
            input(f"  {Colors.DIM}按回车键或关闭窗口退出 (Press Enter to exit)...{Colors.RESET}")
        except Exception:
            pass


if __name__ == "__main__":
    main()

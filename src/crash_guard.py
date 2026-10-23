"""Luna Dimmer - CrashGuard 门面 (Facade for Backward Compatibility)"""

from src.core.crash_guard import run_guard, restore_screen, main

if __name__ == "__main__":
    main()

__all__ = ["run_guard", "restore_screen", "main"]

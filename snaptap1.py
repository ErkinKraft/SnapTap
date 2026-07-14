from __future__ import annotations

import ctypes
import sys
import threading

try:
    import keyboard
except ImportError:
    print("Установите: pip install keyboard")
    sys.exit(1)

SCAN = {"w": 0x11, "a": 0x1E, "s": 0x1F, "d": 0x20}
SCAN_TO_KEY = {v: k for k, v in SCAN.items()}
OPPOSITE = {"a": "d", "d": "a", "w": "s", "s": "w"}
AXIS = {"a": "x", "d": "x", "w": "y", "s": "y"}

_lock = threading.Lock()
_held: set[str] = set()
_active: dict[str, str | None] = {"x": None, "y": None}


def is_admin() -> bool:
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def relaunch_as_admin() -> None:
    params = " ".join(f'"{a}"' if " " in a else a for a in sys.argv)
    rc = ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, params, None, 1
    )
    if rc <= 32:
        print("Запустите скрипт от имени администратора вручную.")
        sys.exit(1)
    sys.exit(0)


def on_down(key: str) -> None:
    action = None 
    with _lock:
        axis = AXIS[key]
        if key in _held:
            if _active[axis] != key:
                action = ("release", key)
        else:
            _held.add(key)
            opp = OPPOSITE[key]
            if opp in _held and _active[axis] == opp:
                action = ("release", opp)
            _active[axis] = key

    if action:
        keyboard.release(SCAN[action[1]])


def on_up(key: str) -> None:
    action = None 
    with _lock:
        if key not in _held:
            return
        _held.discard(key)

        axis = AXIS[key]
        opp = OPPOSITE[key]

        if _active[axis] != key:
       
            return

        if opp in _held:
            _active[axis] = opp
            action = ("press", opp)
        else:
            _active[axis] = None

    if action:
        keyboard.press(SCAN[action[1]])


def _hook(event) -> None:
    scan = (event.scan_code or 0) & 0xFF
    key = SCAN_TO_KEY.get(scan)
    if key is None:
        return
    if event.event_type == keyboard.KEY_DOWN:
        on_down(key)
    elif event.event_type == keyboard.KEY_UP:
        on_up(key)


def start_snap_tap() -> None:
    print("SnapTap активен (WASD).")
    print("Выход: F9")
    keyboard.hook(_hook)
    keyboard.wait("f9")
    keyboard.unhook_all()
    for key in ("a", "d", "w", "s"):
        try:
            keyboard.release(SCAN[key])
        except Exception:
            pass
    print("SnapTap выключен.")


def main() -> None:
    if sys.platform != "win32":
        print("Только Windows.")
        sys.exit(1)

    if not is_admin():
        print("Нужны права администратора, запрашиваю...")
        relaunch_as_admin()
        return

    print("=" * 40)
    print("  SnapTap 1.1.0")
    print("  https://github.com/ErkinKraft")
    print("=" * 40)
    print()

    command = input("Введите команду (start): ").strip().lower()
    if command == "start":
        start_snap_tap()
    else:
        print("Неизвестная команда. Нужно: start")


if __name__ == "__main__":
    main()

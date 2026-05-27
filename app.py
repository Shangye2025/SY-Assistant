from __future__ import annotations

import ctypes
import json
import os
import sys
import threading
import time
import winsound
from ctypes import wintypes
from dataclasses import asdict, dataclass
from pathlib import Path

from PySide6.QtCore import QObject, QPoint, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QIcon, QKeySequence, QPainter, QPen
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListView,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSlider,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


APP_TITLE = "SY连招助手"
PRODUCT_ID = "shiyian_combo_coach"
COMBO_FILTER = "JSON 连招文件 (*.combo.json *.json);;所有文件 (*.*)"


def app_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def resource_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", app_base_dir()))
    return app_base_dir()


APP_BASE_DIR = app_base_dir()
RESOURCE_BASE_DIR = resource_base_dir()
SETTINGS_FILE = APP_BASE_DIR / "combo_coach_settings.json"


def find_existing_path(*candidates: Path) -> Path:
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


APP_ICON = find_existing_path(
    RESOURCE_BASE_DIR / "assets" / "combo_coach.ico",
    APP_BASE_DIR.parent / "连招助手_" / "_internal" / "assets" / "combo_coach.ico",
)
HIT_SOUND_FILE = find_existing_path(
    RESOURCE_BASE_DIR / "assets" / "hit.wav",
    APP_BASE_DIR.parent / "连招助手_" / "_internal" / "assets" / "hit.wav",
)


def default_combo_dir() -> Path:
    bundled = APP_BASE_DIR / "连招"
    sibling = APP_BASE_DIR.parent / "连招助手_" / "连招"
    if bundled.exists():
        return bundled
    if sibling.exists():
        return sibling
    return bundled


WH_KEYBOARD_LL = 13
WH_MOUSE_LL = 14
HC_ACTION = 0
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
WM_SYSKEYDOWN = 0x0104
WM_SYSKEYUP = 0x0105
WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP = 0x0202
WM_RBUTTONDOWN = 0x0204
WM_RBUTTONUP = 0x0205
WM_MBUTTONDOWN = 0x0207
WM_MBUTTONUP = 0x0208
WM_MOUSEWHEEL = 0x020A
WM_XBUTTONDOWN = 0x020B
WM_XBUTTONUP = 0x020C
WM_QUIT = 0x0012
LLKHF_INJECTED = 0x10
LLMHF_INJECTED = 0x01
VK_ESCAPE = 0x1B
KEYEVENTF_KEYUP = 0x0002
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP = 0x0040
MOUSEEVENTF_XDOWN = 0x0080
MOUSEEVENTF_XUP = 0x0100
MOUSEEVENTF_WHEEL = 0x0800
WHEEL_DELTA = 120
XBUTTON1 = 0x0001
XBUTTON2 = 0x0002

MOUSE_LEFT = "鼠标左键"
MOUSE_RIGHT = "鼠标右键"
MOUSE_MIDDLE = "鼠标中键"
MOUSE_SIDE_1 = "鼠标侧键1"
MOUSE_SIDE_2 = "鼠标侧键2"
WHEEL_UP = "滚轮上"
WHEEL_DOWN = "滚轮下"
ACTION_KEYBOARD = "键盘"
ACTION_MOUSE = "鼠标"

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32


class POINT(ctypes.Structure):
    _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]


class MSG(ctypes.Structure):
    _fields_ = [
        ("hwnd", wintypes.HWND),
        ("message", wintypes.UINT),
        ("wParam", wintypes.WPARAM),
        ("lParam", wintypes.LPARAM),
        ("time", wintypes.DWORD),
        ("pt", POINT),
    ]


class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("vkCode", wintypes.DWORD),
        ("scanCode", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_size_t),
    ]


class MSLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("pt", POINT),
        ("mouseData", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_size_t),
    ]


LowLevelProc = ctypes.WINFUNCTYPE(
    wintypes.LPARAM,
    ctypes.c_int,
    wintypes.WPARAM,
    wintypes.LPARAM,
)

user32.SetWindowsHookExW.argtypes = [
    ctypes.c_int,
    LowLevelProc,
    wintypes.HINSTANCE,
    wintypes.DWORD,
]
user32.SetWindowsHookExW.restype = wintypes.HHOOK
user32.CallNextHookEx.argtypes = [
    wintypes.HHOOK,
    ctypes.c_int,
    wintypes.WPARAM,
    wintypes.LPARAM,
]
user32.CallNextHookEx.restype = wintypes.LPARAM
user32.UnhookWindowsHookEx.argtypes = [wintypes.HHOOK]
user32.UnhookWindowsHookEx.restype = wintypes.BOOL
user32.PostThreadMessageW.argtypes = [
    wintypes.DWORD,
    wintypes.UINT,
    wintypes.WPARAM,
    wintypes.LPARAM,
]
user32.PostThreadMessageW.restype = wintypes.BOOL
user32.keybd_event.argtypes = [
    ctypes.c_ubyte,
    ctypes.c_ubyte,
    wintypes.DWORD,
    ctypes.c_size_t,
]
user32.keybd_event.restype = None
user32.mouse_event.argtypes = [
    wintypes.DWORD,
    wintypes.DWORD,
    wintypes.DWORD,
    wintypes.DWORD,
    ctypes.c_size_t,
]
user32.mouse_event.restype = None
user32.MapVirtualKeyW.argtypes = [wintypes.UINT, wintypes.UINT]
user32.MapVirtualKeyW.restype = wintypes.UINT
user32.GetAsyncKeyState.argtypes = [ctypes.c_int]
user32.GetAsyncKeyState.restype = ctypes.c_short
kernel32.GetCurrentThreadId.restype = wintypes.DWORD
kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
kernel32.GetModuleHandleW.restype = wintypes.HMODULE


@dataclass
class ComboStep:
    action: str
    key: str
    delay_ms: int = 0
    hold_ms: int = 80

    @classmethod
    def from_dict(cls, data: dict) -> "ComboStep":
        return cls(
            action=str(data.get("action", ACTION_KEYBOARD)),
            key=str(data.get("key", "Space")),
            delay_ms=max(0, int(data.get("delay_ms", 0) or 0)),
            hold_ms=max(0, int(data.get("hold_ms", 0) or 0)),
        )


@dataclass
class HotkeyConfig:
    start_recording: str = "F6"
    stop_recording: str = "F7"
    replay_combo: str = "F8"
    toggle_overlay: str = "F9"
    toggle_practice: str = "F10"

    @classmethod
    def from_dict(cls, data: dict) -> "HotkeyConfig":
        defaults = cls()
        return cls(
            start_recording=str(data.get("start_recording", defaults.start_recording)),
            stop_recording=str(data.get("stop_recording", defaults.stop_recording)),
            replay_combo=str(data.get("replay_combo", defaults.replay_combo)),
            toggle_overlay=str(data.get("toggle_overlay", defaults.toggle_overlay)),
            toggle_practice=str(data.get("toggle_practice", defaults.toggle_practice)),
        )

    def ignored_vks(self) -> set[int]:
        return {
            vk
            for vk in (
                vk_from_label(self.start_recording),
                vk_from_label(self.stop_recording),
                vk_from_label(self.replay_combo),
                vk_from_label(self.toggle_overlay),
                vk_from_label(self.toggle_practice),
            )
            if vk
        }


class EventBus(QObject):
    recorded = Signal(object)
    updated = Signal(int, object)
    input_event = Signal(str, bool)
    hotkey_start_recording = Signal()
    hotkey_stop_recording = Signal()
    hotkey_replay_combo = Signal()
    hotkey_toggle_overlay = Signal()
    hotkey_toggle_practice = Signal()
    stop_recording = Signal()


VK_LABELS: dict[int, str] = {
    0x08: "Backspace",
    0x09: "Tab",
    0x0D: "Enter",
    0x10: "Shift",
    0x11: "Ctrl",
    0x12: "Alt",
    0x14: "CapsLock",
    0x1B: "Esc",
    0x20: "Space",
    0x21: "PageUp",
    0x22: "PageDown",
    0x23: "End",
    0x24: "Home",
    0x25: "Left",
    0x26: "Up",
    0x27: "Right",
    0x28: "Down",
    0x2D: "Insert",
    0x2E: "Delete",
    0x5B: "Win",
    0x5C: "Win",
    0x5D: "Menu",
    0x6A: "Num*",
    0x6B: "Num+",
    0x6D: "Num-",
    0x6E: "Num.",
    0x6F: "Num/",
    0xBA: ";",
    0xBB: "=",
    0xBC: ",",
    0xBD: "-",
    0xBE: ".",
    0xBF: "/",
    0xC0: "`",
    0xDB: "[",
    0xDC: "\\",
    0xDD: "]",
    0xDE: "'",
}
for code in range(0x30, 0x3A):
    VK_LABELS[code] = chr(code)
for code in range(0x41, 0x5B):
    VK_LABELS[code] = chr(code)
for offset in range(24):
    VK_LABELS[0x70 + offset] = f"F{offset + 1}"
for offset in range(10):
    VK_LABELS[0x60 + offset] = f"Num{offset}"

LABEL_VKS = {label.upper(): vk for vk, label in VK_LABELS.items()}


def friendly_vk(vk_code: int) -> str:
    return VK_LABELS.get(int(vk_code), f"VK{int(vk_code)}")


def vk_from_label(label: str) -> int | None:
    text = str(label).strip()
    if not text:
        return None
    if text.upper().startswith("VK") and text[2:].isdigit():
        return int(text[2:])
    return LABEL_VKS.get(text.upper())


def is_escape_down() -> bool:
    return bool(user32.GetAsyncKeyState(VK_ESCAPE) & 0x8000)


def wait_or_cancel(duration_ms: int, stop_event: threading.Event | None = None) -> bool:
    deadline = time.perf_counter() + max(0, duration_ms) / 1000
    while time.perf_counter() < deadline:
        if stop_event and stop_event.is_set():
            return False
        if is_escape_down():
            return False
        time.sleep(min(0.015, max(0, deadline - time.perf_counter())))
    return True


def press_keyboard_key(vk_code: int) -> None:
    scan_code = user32.MapVirtualKeyW(vk_code, 0)
    user32.keybd_event(vk_code, scan_code, 0, 0)


def release_keyboard_key(vk_code: int) -> None:
    scan_code = user32.MapVirtualKeyW(vk_code, 0)
    user32.keybd_event(vk_code, scan_code, KEYEVENTF_KEYUP, 0)


def mouse_button_flags(label: str) -> tuple[int, int, int] | None:
    mapping = {
        MOUSE_LEFT: (MOUSEEVENTF_LEFTDOWN, MOUSEEVENTF_LEFTUP, 0),
        MOUSE_RIGHT: (MOUSEEVENTF_RIGHTDOWN, MOUSEEVENTF_RIGHTUP, 0),
        MOUSE_MIDDLE: (MOUSEEVENTF_MIDDLEDOWN, MOUSEEVENTF_MIDDLEUP, 0),
        MOUSE_SIDE_1: (MOUSEEVENTF_XDOWN, MOUSEEVENTF_XUP, XBUTTON1),
        MOUSE_SIDE_2: (MOUSEEVENTF_XDOWN, MOUSEEVENTF_XUP, XBUTTON2),
    }
    return mapping.get(label)


def press_mouse_button(label: str) -> bool:
    if label == WHEEL_UP:
        user32.mouse_event(MOUSEEVENTF_WHEEL, 0, 0, WHEEL_DELTA, 0)
        return True
    if label == WHEEL_DOWN:
        user32.mouse_event(MOUSEEVENTF_WHEEL, 0, 0, -WHEEL_DELTA, 0)
        return True
    flags = mouse_button_flags(label)
    if not flags:
        return False
    down_flag, _, data = flags
    user32.mouse_event(down_flag, 0, 0, data, 0)
    return True


def release_mouse_button(label: str) -> bool:
    if label in (WHEEL_UP, WHEEL_DOWN):
        return True
    flags = mouse_button_flags(label)
    if not flags:
        return False
    _, up_flag, data = flags
    user32.mouse_event(up_flag, 0, 0, data, 0)
    return True


class ComboReplayer(QObject):
    started = Signal()
    progress = Signal(int, object)
    finished = Signal(bool, str)

    def __init__(self) -> None:
        super().__init__()
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self.is_running = False

    def play(self, steps: list[ComboStep], speed: float = 1.0) -> None:
        if self.is_running:
            self.stop()
            return
        if not steps:
            self.finished.emit(False, "没有可回放的连招。")
            return
        self._stop_event.clear()
        copied = [ComboStep(step.action, step.key, step.delay_ms, step.hold_ms) for step in steps]
        self._thread = threading.Thread(target=self._run, args=(copied, max(0.1, speed)), daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()

    def _run(self, steps: list[ComboStep], speed: float) -> None:
        self.is_running = True
        self.started.emit()
        success = True
        message = "回放完成。"
        try:
            for index, step in enumerate(steps):
                if not wait_or_cancel(int(step.delay_ms / speed), self._stop_event):
                    success = False
                    message = "回放已停止。"
                    break
                self.progress.emit(index, step)
                if step.action == ACTION_MOUSE:
                    pressed = press_mouse_button(step.key)
                    if pressed and HIT_SOUND_FILE.exists():
                        winsound.PlaySound(str(HIT_SOUND_FILE), winsound.SND_FILENAME | winsound.SND_ASYNC)
                    if not wait_or_cancel(int(step.hold_ms / speed), self._stop_event):
                        success = False
                        message = "回放已停止。"
                        release_mouse_button(step.key)
                        break
                    release_mouse_button(step.key)
                    continue

                vk_code = vk_from_label(step.key)
                if not vk_code:
                    continue
                press_keyboard_key(vk_code)
                if not wait_or_cancel(int(step.hold_ms / speed), self._stop_event):
                    success = False
                    message = "回放已停止。"
                    release_keyboard_key(vk_code)
                    break
                release_keyboard_key(vk_code)
        except Exception as exc:
            success = False
            message = f"回放失败：{exc}"
        finally:
            self.is_running = False
            self._stop_event.clear()
            self.finished.emit(success, message)


class ComboRecorder:
    def __init__(self, bus: EventBus) -> None:
        self.bus = bus
        self.is_recording = False
        self.ignored_vks: set[int] = set()
        self.steps: list[ComboStep] = []
        self._pressed: dict[str, tuple[float, int]] = {}
        self._last_step_time: float | None = None

    def set_ignored_hotkeys(self, hotkeys: set[int]) -> None:
        self.ignored_vks = set(hotkeys)

    def start(self) -> None:
        if self.is_recording:
            return
        self.steps = []
        self._pressed = {}
        self._last_step_time = time.perf_counter()
        self.is_recording = True

    def stop(self) -> None:
        self.is_recording = False
        self._pressed = {}

    def key_event(self, vk_code: int, pressed: bool) -> None:
        if vk_code in self.ignored_vks:
            return
        label = friendly_vk(vk_code)
        if pressed:
            if label == "Esc" and self.is_recording:
                self.bus.stop_recording.emit()
                return
            self._start_step(f"k:{label}", ACTION_KEYBOARD, label)
            return
        self._finish_step(f"k:{label}")

    def mouse_event(self, label: str, pressed: bool) -> None:
        token = f"m:{label}"
        if pressed:
            self._start_step(token, ACTION_MOUSE, label)
            return
        self._finish_step(token)

    def wheel_event(self, label: str) -> None:
        if not self.is_recording:
            return
        now = time.perf_counter()
        previous = self._last_step_time or now
        delay_ms = int((now - previous) * 1000)
        self._last_step_time = now
        step = ComboStep(ACTION_MOUSE, label, max(0, delay_ms), 20)
        self.steps.append(step)
        self.bus.recorded.emit(step)

    def _start_step(self, token: str, action: str, key: str) -> None:
        if not self.is_recording or token in self._pressed:
            return
        now = time.perf_counter()
        previous = self._last_step_time or now
        delay_ms = int((now - previous) * 1000)
        self._last_step_time = now
        step = ComboStep(action, key, max(0, delay_ms), 0)
        self.steps.append(step)
        self._pressed[token] = (now, len(self.steps) - 1)
        self.bus.recorded.emit(step)

    def _finish_step(self, token: str) -> None:
        if not self.is_recording:
            return
        started, index = self._pressed.pop(token, (time.perf_counter(), -1))
        if index < 0 or index >= len(self.steps):
            return
        step = self.steps[index]
        step.hold_ms = max(0, int((time.perf_counter() - started) * 1000))
        self.bus.updated.emit(index, step)


class WindowsInputHook:
    def __init__(self, recorder: ComboRecorder, hotkey_handler, bus: EventBus) -> None:
        self.recorder = recorder
        self.hotkey_handler = hotkey_handler
        self.bus = bus
        self.running = False
        self.thread: threading.Thread | None = None
        self.thread_id = 0
        self.keyboard_hook = None
        self.mouse_hook = None
        self._hotkey_down: set[int] = set()
        self._keyboard_proc = LowLevelProc(self._handle_keyboard)
        self._mouse_proc = LowLevelProc(self._handle_mouse)

    def start(self) -> None:
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def stop(self) -> None:
        self.running = False
        if self.thread_id:
            user32.PostThreadMessageW(self.thread_id, WM_QUIT, 0, 0)
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1)

    def _run(self) -> None:
        self.thread_id = kernel32.GetCurrentThreadId()
        module = kernel32.GetModuleHandleW(None)
        self.keyboard_hook = user32.SetWindowsHookExW(WH_KEYBOARD_LL, self._keyboard_proc, module, 0)
        self.mouse_hook = user32.SetWindowsHookExW(WH_MOUSE_LL, self._mouse_proc, module, 0)
        msg = MSG()
        while self.running and user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))
        if self.keyboard_hook:
            user32.UnhookWindowsHookEx(self.keyboard_hook)
            self.keyboard_hook = None
        if self.mouse_hook:
            user32.UnhookWindowsHookEx(self.mouse_hook)
            self.mouse_hook = None

    def _handle_keyboard(self, n_code: int, w_param: int, l_param: int) -> int:
        if n_code == HC_ACTION:
            data = ctypes.cast(l_param, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
            vk_code = int(data.vkCode)
            injected = bool(data.flags & LLKHF_INJECTED)
            pressed = w_param in (WM_KEYDOWN, WM_SYSKEYDOWN)
            released = w_param in (WM_KEYUP, WM_SYSKEYUP)
            if pressed:
                if not injected and self.hotkey_handler(vk_code):
                    self._hotkey_down.add(vk_code)
                    return 1
                if not injected:
                    self.bus.input_event.emit(friendly_vk(vk_code), True)
                    self.recorder.key_event(vk_code, True)
            elif released:
                if vk_code in self._hotkey_down:
                    self._hotkey_down.discard(vk_code)
                    return 1
                if not injected:
                    self.bus.input_event.emit(friendly_vk(vk_code), False)
                    self.recorder.key_event(vk_code, False)
        return user32.CallNextHookEx(self.keyboard_hook, n_code, w_param, l_param)

    def _handle_mouse(self, n_code: int, w_param: int, l_param: int) -> int:
        if n_code == HC_ACTION:
            data = ctypes.cast(l_param, ctypes.POINTER(MSLLHOOKSTRUCT)).contents
            if not data.flags & LLMHF_INJECTED:
                label, pressed = self._mouse_event_from_message(w_param, data.mouseData)
                if label:
                    self.bus.input_event.emit(label, pressed)
                    if label in (WHEEL_UP, WHEEL_DOWN):
                        self.recorder.wheel_event(label)
                    else:
                        self.recorder.mouse_event(label, pressed)
        return user32.CallNextHookEx(self.mouse_hook, n_code, w_param, l_param)

    def _mouse_event_from_message(self, message: int, mouse_data: int) -> tuple[str | None, bool]:
        if message == WM_LBUTTONDOWN:
            return MOUSE_LEFT, True
        if message == WM_LBUTTONUP:
            return MOUSE_LEFT, False
        if message == WM_RBUTTONDOWN:
            return MOUSE_RIGHT, True
        if message == WM_RBUTTONUP:
            return MOUSE_RIGHT, False
        if message == WM_MBUTTONDOWN:
            return MOUSE_MIDDLE, True
        if message == WM_MBUTTONUP:
            return MOUSE_MIDDLE, False
        if message in (WM_XBUTTONDOWN, WM_XBUTTONUP):
            button = (mouse_data >> 16) & 0xFFFF
            label = MOUSE_SIDE_1 if button == XBUTTON1 else MOUSE_SIDE_2
            return label, message == WM_XBUTTONDOWN
        if message == WM_MOUSEWHEEL:
            delta = ctypes.c_short((mouse_data >> 16) & 0xFFFF).value
            return (WHEEL_UP if delta > 0 else WHEEL_DOWN), True
        return None, False


class NoteLaneWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.steps: list[ComboStep] = []
        self.progress_index = -1
        self.setMinimumHeight(86)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def set_steps(self, steps: list[ComboStep]) -> None:
        self.steps = steps
        self.update()

    def set_progress(self, index: int) -> None:
        self.progress_index = index
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(12, 12, -12, -12)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#101820"))
        painter.drawRoundedRect(rect, 8, 8)

        if not self.steps:
            painter.setPen(QColor("#7f8b98"))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "等待录制或载入连招")
            return

        total = max(1, sum(step.delay_ms + max(18, step.hold_ms) for step in self.steps))
        x = rect.left() + 10
        usable = rect.width() - 20
        font = QFont()
        font.setPointSize(9)
        painter.setFont(font)

        for index, step in enumerate(self.steps):
            delay_width = max(4, int(usable * step.delay_ms / total))
            hold_width = max(18, int(usable * max(18, step.hold_ms) / total))
            x += delay_width
            color = QColor("#32d296") if step.action == ACTION_KEYBOARD else QColor("#4ea1ff")
            if index == self.progress_index:
                color = QColor("#f9c74f")
            bar = QRectF(x, rect.top() + 18, hold_width, 28)
            painter.setBrush(color)
            painter.drawRoundedRect(bar, 5, 5)
            painter.setPen(QColor("#071018"))
            painter.drawText(bar, Qt.AlignmentFlag.AlignCenter, step.key)
            painter.setPen(QColor("#354555"))
            painter.drawLine(x, rect.bottom() - 12, x, rect.bottom() - 5)
            x += hold_width

        painter.setPen(QColor("#7f8b98"))
        painter.drawText(
            QRectF(rect.left() + 10, rect.bottom() - 22, rect.width() - 20, 18),
            Qt.AlignmentFlag.AlignLeft,
            f"{len(self.steps)} 步 / {total / 1000:.2f} 秒",
        )


class OverlayWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("练习悬浮窗")
        self.setWindowFlags(
            Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(520, 150)

        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        panel = QFrame()
        panel.setObjectName("OverlayPanel")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(16, 12, 16, 12)
        self.title = QLabel("连招助手")
        self.title.setObjectName("OverlayTitle")
        self.input_label = QLabel("等待输入")
        self.input_label.setObjectName("OverlayInput")
        self.lane = NoteLaneWidget()
        self.lane.setMinimumHeight(64)
        panel_layout.addWidget(self.title)
        panel_layout.addWidget(self.input_label)
        panel_layout.addWidget(self.lane)
        root.addWidget(panel)

        self.setStyleSheet(
            """
            #OverlayPanel {
                background: rgba(12, 18, 24, 222);
                border: 1px solid rgba(255, 255, 255, 45);
                border-radius: 10px;
            }
            #OverlayTitle { color: #d7e2ed; font-size: 13px; font-weight: 700; }
            #OverlayInput { color: #f9c74f; font-size: 18px; font-weight: 800; }
            """
        )

    def update_combo(self, name: str, steps: list[ComboStep]) -> None:
        self.title.setText(name or "未命名连招")
        self.lane.set_steps(steps)

    def update_input(self, label: str, pressed: bool) -> None:
        state = "按下" if pressed else "抬起"
        self.input_label.setText(f"{label}  {state}")

    def update_progress(self, index: int) -> None:
        self.lane.set_progress(index)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(f"{APP_TITLE} - 本地版")
        self.resize(1180, 760)

        self.settings = self.load_settings()
        self.hotkeys = HotkeyConfig.from_dict(self.settings.get("hotkeys", {}))
        self.combo_dir = Path(self.settings.get("combo_dir") or default_combo_dir())
        self.current_file: Path | None = None
        self.combo_name = "未命名连招"
        self.steps: list[ComboStep] = []
        self.practice_mode = False
        self.practice_index = 0
        self._loading_table = False

        self.bus = EventBus()
        self.recorder = ComboRecorder(self.bus)
        self.recorder.set_ignored_hotkeys(self.hotkeys.ignored_vks())
        self.replayer = ComboReplayer()
        self.overlay = OverlayWindow()

        self.build_ui()
        self.connect_events()
        self.apply_style()
        self.refresh_combo_list()
        self.refresh_table()
        self.update_summary()

        self.input_hook = WindowsInputHook(self.recorder, self.handle_hotkey, self.bus)
        self.input_hook.start()
        QTimer.singleShot(400, self._report_hook_state)

    def build_ui(self) -> None:
        central = QWidget()
        root = QHBoxLayout(central)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(16)
        self.setCentralWidget(central)
        self.setStatusBar(QStatusBar())

        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(285)
        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(16, 16, 16, 16)
        side_layout.setSpacing(12)

        title = QLabel("连招助手")
        title.setObjectName("AppTitle")
        subtitle = QLabel("本地运行 / 无联网校验")
        subtitle.setObjectName("Subtitle")
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("搜索连招")
        self.combo_list = QListWidget()
        self.combo_list.setObjectName("ComboList")

        dir_row = QHBoxLayout()
        self.dir_label = QLabel()
        self.dir_label.setObjectName("TinyText")
        self.dir_label.setWordWrap(True)
        choose_dir_btn = QPushButton("目录")
        choose_dir_btn.setObjectName("GhostButton")
        choose_dir_btn.clicked.connect(self.choose_combo_dir)
        dir_row.addWidget(self.dir_label, 1)
        dir_row.addWidget(choose_dir_btn)

        side_layout.addWidget(title)
        side_layout.addWidget(subtitle)
        side_layout.addWidget(self.search_edit)
        side_layout.addWidget(self.combo_list, 1)
        side_layout.addLayout(dir_row)
        root.addWidget(sidebar)

        content = QFrame()
        content.setObjectName("Content")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(18, 18, 18, 18)
        content_layout.setSpacing(14)
        root.addWidget(content, 1)

        header = QFrame()
        header.setObjectName("Header")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 14, 16, 14)
        self.combo_title = QLabel(self.combo_name)
        self.combo_title.setObjectName("ComboTitle")
        self.combo_meta = QLabel("0 步 / 0.00 秒")
        self.combo_meta.setObjectName("Subtitle")
        title_block = QVBoxLayout()
        title_block.addWidget(self.combo_title)
        title_block.addWidget(self.combo_meta)
        header_layout.addLayout(title_block, 1)

        self.new_btn = QPushButton("新建")
        self.open_btn = QPushButton("打开")
        self.save_btn = QPushButton("保存")
        self.save_as_btn = QPushButton("另存")
        for button in (self.new_btn, self.open_btn, self.save_btn, self.save_as_btn):
            button.setObjectName("GhostButton")
            header_layout.addWidget(button)
        content_layout.addWidget(header)

        controls = QFrame()
        controls.setObjectName("Controls")
        controls_layout = QGridLayout(controls)
        controls_layout.setContentsMargins(14, 12, 14, 12)
        controls_layout.setHorizontalSpacing(10)
        controls_layout.setVerticalSpacing(10)

        self.record_btn = QPushButton("● 录制")
        self.stop_btn = QPushButton("■ 停止")
        self.play_btn = QPushButton("▶ 回放")
        self.overlay_check = QCheckBox("悬浮窗")
        self.practice_check = QCheckBox("练习模式")
        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setRange(25, 200)
        self.speed_slider.setValue(int(self.settings.get("speed", 100)))
        self.speed_label = QLabel("100%")
        self.last_input_label = QLabel("最近输入：-")
        self.last_input_label.setObjectName("TinyText")

        controls_layout.addWidget(self.record_btn, 0, 0)
        controls_layout.addWidget(self.stop_btn, 0, 1)
        controls_layout.addWidget(self.play_btn, 0, 2)
        controls_layout.addWidget(self.overlay_check, 0, 3)
        controls_layout.addWidget(self.practice_check, 0, 4)
        controls_layout.addWidget(QLabel("速度"), 0, 5)
        controls_layout.addWidget(self.speed_slider, 0, 6)
        controls_layout.addWidget(self.speed_label, 0, 7)
        controls_layout.addWidget(self.last_input_label, 1, 0, 1, 8)
        controls_layout.setColumnStretch(6, 1)
        content_layout.addWidget(controls)

        self.lane = NoteLaneWidget()
        content_layout.addWidget(self.lane)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["#", "类型", "按键", "延迟 ms", "按住 ms"])
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        content_layout.addWidget(self.table, 1)

        bottom = QFrame()
        bottom.setObjectName("Footer")
        bottom_layout = QHBoxLayout(bottom)
        bottom_layout.setContentsMargins(14, 12, 14, 12)

        self.add_step_btn = QPushButton("添加步骤")
        self.delete_step_btn = QPushButton("删除")
        self.up_step_btn = QPushButton("上移")
        self.down_step_btn = QPushButton("下移")
        for button in (self.add_step_btn, self.delete_step_btn, self.up_step_btn, self.down_step_btn):
            button.setObjectName("GhostButton")
            bottom_layout.addWidget(button)

        bottom_layout.addStretch(1)
        hotkey_layout = QHBoxLayout()
        self.hotkey_boxes: dict[str, QComboBox] = {}
        hotkey_defs = [
            ("start_recording", "录制"),
            ("stop_recording", "停止"),
            ("replay_combo", "回放"),
            ("toggle_overlay", "悬浮"),
            ("toggle_practice", "练习"),
        ]
        for field, label in hotkey_defs:
            hotkey_layout.addWidget(QLabel(label))
            combo = QComboBox()
            combo.addItems([f"F{i}" for i in range(1, 13)])
            combo.setView(QListView())
            combo.setMaxVisibleItems(8)
            combo.setCurrentText(getattr(self.hotkeys, field))
            combo.currentTextChanged.connect(self.update_hotkeys)
            self.hotkey_boxes[field] = combo
            hotkey_layout.addWidget(combo)
        bottom_layout.addLayout(hotkey_layout)
        content_layout.addWidget(bottom)

    def connect_events(self) -> None:
        self.search_edit.textChanged.connect(self.refresh_combo_list)
        self.combo_list.itemActivated.connect(self.load_combo_from_item)
        self.combo_list.currentItemChanged.connect(lambda item, _: self.load_combo_from_item(item))
        self.new_btn.clicked.connect(self.new_combo)
        self.open_btn.clicked.connect(self.open_combo)
        self.save_btn.clicked.connect(self.save_combo)
        self.save_as_btn.clicked.connect(self.save_combo_as)
        self.record_btn.clicked.connect(self.start_recording)
        self.stop_btn.clicked.connect(self.stop_recording)
        self.play_btn.clicked.connect(self.play_combo)
        self.overlay_check.toggled.connect(self.toggle_overlay)
        self.practice_check.toggled.connect(self.toggle_practice)
        self.speed_slider.valueChanged.connect(self.update_speed_label)
        self.add_step_btn.clicked.connect(self.add_step)
        self.delete_step_btn.clicked.connect(self.delete_selected_steps)
        self.up_step_btn.clicked.connect(lambda: self.move_selected_step(-1))
        self.down_step_btn.clicked.connect(lambda: self.move_selected_step(1))
        self.table.itemChanged.connect(self.on_table_item_changed)

        self.bus.recorded.connect(self.on_step_recorded)
        self.bus.updated.connect(self.on_step_updated)
        self.bus.input_event.connect(self.on_input_event)
        self.bus.hotkey_start_recording.connect(self.start_recording)
        self.bus.hotkey_stop_recording.connect(self.stop_recording)
        self.bus.hotkey_replay_combo.connect(self.play_combo)
        self.bus.hotkey_toggle_overlay.connect(lambda: self.overlay_check.toggle())
        self.bus.hotkey_toggle_practice.connect(lambda: self.practice_check.toggle())
        self.bus.stop_recording.connect(self.stop_recording)

        self.replayer.started.connect(lambda: self.statusBar().showMessage("正在回放，按 Esc 可停止。"))
        self.replayer.progress.connect(self.on_replay_progress)
        self.replayer.finished.connect(self.on_replay_finished)

    def apply_style(self) -> None:
        QApplication.instance().setStyle("Fusion")
        self.setStyleSheet(
            """
            QMainWindow { background: #0b1117; color: #dce6ef; }
            #Sidebar, #Content, #Header, #Controls, #Footer {
                background: #111a23;
                border: 1px solid #22303d;
                border-radius: 8px;
            }
            #Header, #Controls, #Footer { background: #0f1821; }
            #AppTitle { color: #ffffff; font-size: 24px; font-weight: 800; }
            #ComboTitle { color: #ffffff; font-size: 22px; font-weight: 800; }
            #Subtitle, #TinyText { color: #8ea1b3; }
            QLabel { color: #dce6ef; }
            QLineEdit, QComboBox {
                color: #e7eef6;
                background: #0b1219;
                border: 1px solid #263747;
                border-radius: 6px;
                padding: 7px 9px;
            }
            QComboBox {
                padding-right: 26px;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 24px;
                border-left: 1px solid #263747;
                border-top-right-radius: 6px;
                border-bottom-right-radius: 6px;
                background: #101b25;
            }
            QComboBox::down-arrow {
                width: 0;
                height: 0;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid #9fb1c2;
                margin-right: 8px;
            }
            QComboBox QAbstractItemView {
                color: #e7eef6;
                background: #0b1219;
                border: 1px solid #2a3b4c;
                border-radius: 4px;
                outline: 0;
                padding: 4px;
                selection-background-color: #1d6fd1;
                selection-color: #ffffff;
            }
            QComboBox QAbstractItemView::item {
                min-height: 24px;
                padding: 4px 8px;
            }
            QComboBox QAbstractItemView::item:hover {
                background: #203044;
            }
            QListWidget, QTableWidget {
                color: #e7eef6;
                background: #0c141c;
                alternate-background-color: #101b25;
                border: 1px solid #22303d;
                border-radius: 8px;
                selection-background-color: #1d6fd1;
                selection-color: #ffffff;
                gridline-color: #1e2a35;
            }
            QHeaderView::section {
                color: #a9b8c7;
                background: #121e28;
                border: none;
                border-right: 1px solid #22303d;
                padding: 8px;
                font-weight: 700;
            }
            QPushButton {
                color: #041018;
                background: #32d296;
                border: none;
                border-radius: 6px;
                padding: 8px 13px;
                font-weight: 800;
            }
            QPushButton:hover { background: #46e3a7; }
            QPushButton:pressed { background: #27b982; }
            QPushButton#GhostButton {
                color: #dbe8f4;
                background: #172330;
                border: 1px solid #2a3b4c;
            }
            QPushButton#GhostButton:hover { background: #203044; }
            QCheckBox { color: #dce6ef; spacing: 8px; }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 1px solid #3b4d5f;
                border-radius: 4px;
                background: #0b1219;
            }
            QCheckBox::indicator:checked {
                background: #4ea1ff;
                border-color: #4ea1ff;
            }
            QSlider::groove:horizontal {
                height: 6px;
                background: #22303d;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                width: 16px;
                margin: -6px 0;
                border-radius: 8px;
                background: #f9c74f;
            }
            QScrollBar:vertical {
                background: #0b1219;
                width: 12px;
                margin: 0;
                border-left: 1px solid #22303d;
            }
            QScrollBar::handle:vertical {
                background: #34485b;
                border-radius: 5px;
                min-height: 28px;
            }
            QScrollBar::handle:vertical:hover { background: #466078; }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical,
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {
                background: transparent;
                height: 0;
            }
            QScrollBar:horizontal {
                background: #0b1219;
                height: 12px;
                margin: 0;
                border-top: 1px solid #22303d;
            }
            QScrollBar::handle:horizontal {
                background: #34485b;
                border-radius: 5px;
                min-width: 28px;
            }
            QScrollBar::handle:horizontal:hover { background: #466078; }
            QScrollBar::add-line:horizontal,
            QScrollBar::sub-line:horizontal,
            QScrollBar::add-page:horizontal,
            QScrollBar::sub-page:horizontal {
                background: transparent;
                width: 0;
            }
            QStatusBar { color: #9fb1c2; background: #0b1117; }
            """
        )

    def load_settings(self) -> dict:
        try:
            return json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def save_settings(self) -> None:
        data = {
            "combo_dir": str(self.combo_dir),
            "speed": self.speed_slider.value(),
            "hotkeys": asdict(self.hotkeys),
        }
        SETTINGS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def refresh_combo_list(self, *_args) -> None:
        self.combo_list.clear()
        self.dir_label.setText(str(self.combo_dir))
        query = self.search_edit.text().strip().lower() if hasattr(self, "search_edit") else ""
        if not self.combo_dir.exists():
            return
        files = sorted(
            {path for pattern in ("*.combo.json", "*.json") for path in self.combo_dir.rglob(pattern)}
        )
        for path in files:
            rel = str(path.relative_to(self.combo_dir))
            if query and query not in rel.lower():
                continue
            item = QListWidgetItem(rel)
            item.setData(Qt.ItemDataRole.UserRole, str(path))
            self.combo_list.addItem(item)

    def choose_combo_dir(self) -> None:
        selected = QFileDialog.getExistingDirectory(self, "选择连招目录", str(self.combo_dir))
        if not selected:
            return
        self.combo_dir = Path(selected)
        self.refresh_combo_list()
        self.save_settings()

    def load_combo_from_item(self, item: QListWidgetItem | None) -> None:
        if not item:
            return
        path = Path(item.data(Qt.ItemDataRole.UserRole))
        self.load_combo(path)

    def load_combo(self, path: Path) -> None:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            steps = [ComboStep.from_dict(step) for step in data.get("steps", [])]
        except Exception as exc:
            QMessageBox.warning(self, "载入失败", f"无法读取连招文件：\n{exc}")
            return
        self.current_file = path
        self.combo_name = str(data.get("name") or path.stem)
        self.steps = steps
        self.practice_index = 0
        self.refresh_table()
        self.update_summary()
        self.statusBar().showMessage(f"已载入：{path.name}", 4000)

    def new_combo(self) -> None:
        self.current_file = None
        self.combo_name = "未命名连招"
        self.steps = []
        self.practice_index = 0
        self.refresh_table()
        self.update_summary()
        self.statusBar().showMessage("已新建空连招。", 3000)

    def open_combo(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "打开连招", str(self.combo_dir), COMBO_FILTER)
        if path:
            self.load_combo(Path(path))

    def save_combo(self) -> None:
        if not self.current_file:
            self.save_combo_as()
            return
        self.write_combo(self.current_file)

    def save_combo_as(self) -> None:
        self.combo_dir.mkdir(parents=True, exist_ok=True)
        default_name = self.combo_name if self.combo_name != "未命名连招" else "新连招.combo"
        path, _ = QFileDialog.getSaveFileName(
            self,
            "保存连招",
            str(self.combo_dir / f"{Path(default_name).stem}.combo.json"),
            COMBO_FILTER,
        )
        if not path:
            return
        target = Path(path)
        if target.suffix.lower() != ".json":
            target = target.with_suffix(".combo.json")
        self.current_file = target
        self.combo_name = target.stem
        self.write_combo(target)
        self.refresh_combo_list()

    def write_combo(self, path: Path) -> None:
        self.sync_steps_from_table()
        data = {
            "name": self.combo_name,
            "version": 1,
            "created_at": int(time.time()),
            "steps": [asdict(step) for step in self.steps],
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        self.statusBar().showMessage(f"已保存：{path.name}", 4000)
        self.update_summary()

    def start_recording(self) -> None:
        self.replayer.stop()
        self.recorder.start()
        self.steps = self.recorder.steps
        self.practice_index = 0
        self.refresh_table()
        self.update_summary()
        self.statusBar().showMessage("录制中：按 Esc 或停止键结束。", 0)

    def stop_recording(self) -> None:
        if not self.recorder.is_recording:
            self.replayer.stop()
            return
        self.recorder.stop()
        self.steps = list(self.recorder.steps)
        self.refresh_table()
        self.update_summary()
        self.statusBar().showMessage(f"录制完成，共 {len(self.steps)} 步。", 4000)

    def play_combo(self) -> None:
        if self.replayer.is_running:
            self.replayer.stop()
            return
        self.sync_steps_from_table()
        self.practice_index = 0
        self.lane.set_progress(-1)
        self.overlay.update_progress(-1)
        self.replayer.play(self.steps, self.speed_slider.value() / 100)

    def toggle_overlay(self, checked: bool) -> None:
        if checked:
            self.overlay.update_combo(self.combo_name, self.steps)
            anchor = self.geometry().topRight() + QPoint(-560, 40)
            self.overlay.move(anchor)
            self.overlay.show()
        else:
            self.overlay.hide()

    def toggle_practice(self, checked: bool) -> None:
        self.practice_mode = checked
        self.practice_index = 0
        self.lane.set_progress(-1)
        self.overlay.update_progress(-1)
        message = "练习模式已开启，按顺序输入高亮步骤。" if checked else "练习模式已关闭。"
        self.statusBar().showMessage(message, 4000)

    def update_speed_label(self, value: int) -> None:
        self.speed_label.setText(f"{value}%")
        self.settings["speed"] = value

    def update_hotkeys(self, *_args) -> None:
        for field, combo in self.hotkey_boxes.items():
            setattr(self.hotkeys, field, combo.currentText())
        self.recorder.set_ignored_hotkeys(self.hotkeys.ignored_vks())
        self.save_settings()

    def handle_hotkey(self, vk_code: int) -> bool:
        label = friendly_vk(vk_code)
        if label == self.hotkeys.start_recording:
            self.bus.hotkey_start_recording.emit()
            return True
        if label == self.hotkeys.stop_recording:
            self.bus.hotkey_stop_recording.emit()
            return True
        if label == self.hotkeys.replay_combo:
            self.bus.hotkey_replay_combo.emit()
            return True
        if label == self.hotkeys.toggle_overlay:
            self.bus.hotkey_toggle_overlay.emit()
            return True
        if label == self.hotkeys.toggle_practice:
            self.bus.hotkey_toggle_practice.emit()
            return True
        return False

    def on_step_recorded(self, step: ComboStep) -> None:
        self.append_step_row(step, len(self.steps) - 1)
        self.update_summary()

    def on_step_updated(self, index: int, step: ComboStep) -> None:
        if 0 <= index < self.table.rowCount():
            self._loading_table = True
            self.table.item(index, 4).setText(str(step.hold_ms))
            self._loading_table = False
            self.update_summary()

    def on_input_event(self, label: str, pressed: bool) -> None:
        self.last_input_label.setText(f"最近输入：{label} {'按下' if pressed else '抬起'}")
        self.overlay.update_input(label, pressed)
        if not self.practice_mode or not pressed or not self.steps:
            return
        expected = self.steps[self.practice_index]
        if label == expected.key:
            self.lane.set_progress(self.practice_index)
            self.overlay.update_progress(self.practice_index)
            self.practice_index += 1
            if self.practice_index >= len(self.steps):
                self.statusBar().showMessage("练习完成。", 4000)
                self.practice_index = 0
            else:
                next_step = self.steps[self.practice_index]
                self.statusBar().showMessage(f"下一步：{next_step.key}", 2500)
        else:
            self.statusBar().showMessage(f"当前应输入：{expected.key}", 2500)

    def on_replay_progress(self, index: int, step: ComboStep) -> None:
        self.lane.set_progress(index)
        self.overlay.update_progress(index)
        self.statusBar().showMessage(f"回放：{step.key}", 1000)

    def on_replay_finished(self, success: bool, message: str) -> None:
        self.lane.set_progress(-1)
        self.overlay.update_progress(-1)
        self.statusBar().showMessage(message, 4000)

    def add_step(self) -> None:
        step = ComboStep(ACTION_KEYBOARD, "Space", 80, 80)
        row = self.table.currentRow()
        index = row + 1 if row >= 0 else len(self.steps)
        self.steps.insert(index, step)
        self.refresh_table()
        self.table.selectRow(index)
        self.update_summary()

    def delete_selected_steps(self) -> None:
        rows = sorted({item.row() for item in self.table.selectedItems()}, reverse=True)
        for row in rows:
            if 0 <= row < len(self.steps):
                del self.steps[row]
        self.refresh_table()
        self.update_summary()

    def move_selected_step(self, direction: int) -> None:
        row = self.table.currentRow()
        target = row + direction
        if row < 0 or target < 0 or target >= len(self.steps):
            return
        self.steps[row], self.steps[target] = self.steps[target], self.steps[row]
        self.refresh_table()
        self.table.selectRow(target)
        self.update_summary()

    def refresh_table(self) -> None:
        self._loading_table = True
        self.table.setRowCount(0)
        for index, step in enumerate(self.steps):
            self.append_step_row(step, index)
        self._loading_table = False
        self.lane.set_steps(self.steps)
        self.overlay.update_combo(self.combo_name, self.steps)

    def append_step_row(self, step: ComboStep, index: int) -> None:
        row = self.table.rowCount()
        self.table.insertRow(row)
        values = [str(index + 1), step.action, step.key, str(step.delay_ms), str(step.hold_ms)]
        for column, value in enumerate(values):
            item = QTableWidgetItem(value)
            if column == 0:
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            elif column in (3, 4):
                item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, column, item)

    def on_table_item_changed(self, item: QTableWidgetItem) -> None:
        if self._loading_table:
            return
        row = item.row()
        if not 0 <= row < len(self.steps):
            return
        step = self.steps[row]
        try:
            if item.column() == 1:
                step.action = item.text().strip() or ACTION_KEYBOARD
            elif item.column() == 2:
                step.key = item.text().strip() or "Space"
            elif item.column() == 3:
                step.delay_ms = max(0, int(item.text() or 0))
            elif item.column() == 4:
                step.hold_ms = max(0, int(item.text() or 0))
        except ValueError:
            self.refresh_table()
            return
        self.update_summary()

    def sync_steps_from_table(self) -> None:
        for row in range(min(self.table.rowCount(), len(self.steps))):
            self.steps[row] = ComboStep(
                action=self.table.item(row, 1).text().strip() or ACTION_KEYBOARD,
                key=self.table.item(row, 2).text().strip() or "Space",
                delay_ms=max(0, int(self.table.item(row, 3).text() or 0)),
                hold_ms=max(0, int(self.table.item(row, 4).text() or 0)),
            )

    def update_summary(self) -> None:
        total_ms = sum(step.delay_ms + step.hold_ms for step in self.steps)
        self.combo_title.setText(self.combo_name)
        self.combo_meta.setText(f"{len(self.steps)} 步 / {total_ms / 1000:.2f} 秒")
        self.lane.set_steps(self.steps)
        self.overlay.update_combo(self.combo_name, self.steps)

    def _report_hook_state(self) -> None:
        if self.input_hook.keyboard_hook and self.input_hook.mouse_hook:
            self.statusBar().showMessage("本地版已就绪：无需登录、无需联网。", 5000)
        else:
            self.statusBar().showMessage("输入钩子未完全启用，请尝试以管理员身份运行。", 8000)

    def closeEvent(self, event) -> None:
        self.save_settings()
        self.replayer.stop()
        self.input_hook.stop()
        self.overlay.close()
        super().closeEvent(event)


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName(APP_TITLE)
    if APP_ICON.exists():
        app.setWindowIcon(QIcon(str(APP_ICON)))
    window = MainWindow()
    if APP_ICON.exists():
        window.setWindowIcon(QIcon(str(APP_ICON)))
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import ctypes
import math
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import font as tkfont

try:
    import keyboard
except ImportError:
    print("Установите: pip install keyboard")
    sys.exit(1)

APP_NAME = "SnapTap"
APP_VERSION = "1.1.1"
APP_AUTHOR = "ErkinKraft"
APP_LICENSE = "MIT License"


def _resource_dir() -> Path:
   
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent


BASE_DIR = _resource_dir()
LOGO_PATH = BASE_DIR / "logoW.png"



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


def release_wasd() -> None:
    for key in ("a", "d", "w", "s"):
        try:
            keyboard.release(SCAN[key])
        except Exception:
            pass




BG = "#0A0A0A"
BG_PANEL = "#111111"
BG_KEY = "#161616"
BG_KEY_EDGE = "#1F1F1F"
RED = "#E10600"
RED_DIM = "#7A0300"
RED_GLOW = "#FF2A1A"
RED_SOFT = "#2A0505"
TEXT = "#F2F2F2"
TEXT_MUTED = "#7A7A7A"
LINE = "#222222"


def lerp_color(c1: str, c2: str, t: float) -> str:
    def hex_to_rgb(h: str) -> tuple[int, int, int]:
        h = h.lstrip("#")
        return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)

    r1, g1, b1 = hex_to_rgb(c1)
    r2, g2, b2 = hex_to_rgb(c2)
    t = max(0.0, min(1.0, t))
    return "#{:02x}{:02x}{:02x}".format(
        int(r1 + (r2 - r1) * t),
        int(g1 + (g2 - g1) * t),
        int(b1 + (b2 - b1) * t),
    )




class SnapTapApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("SnapTap")
        self.geometry("442x652")
        self.configure(bg=RED)
        self.resizable(False, False)
        self.overrideredirect(True)
        self.attributes("-topmost", False)

        self._active = False
        self._pulse = 0.0
        self._btn_hover = False
        self._shutdown = False
        self._drag_x = 0
        self._drag_y = 0
        self._snap_hook = None
        self._about_win = None
        self._key_widgets: dict[str, dict] = {}
        self._key_lit: dict[str, float] = {"w": 0.0, "a": 0.0, "s": 0.0, "d": 0.0}

        self._setup_fonts()
        self._build_ui()
        self._center()
        self.after(10, self._ensure_taskbar)
        self._animate()

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.bind("<Escape>", lambda _e: self._on_close())
        self.bind_all("<F10>", self._on_f10)
        self.bind("<Map>", self._on_map)

        try:
            self.iconbitmap(default="")
        except Exception:
            pass

    def _setup_fonts(self) -> None:
        families = set(tkfont.families())
        display = "Segoe UI" if "Segoe UI" in families else "Arial"
        mono = "Consolas" if "Consolas" in families else display
        self.font_brand = tkfont.Font(family=display, size=28, weight="bold")
        self.font_tag = tkfont.Font(family=display, size=9, weight="bold")
        self.font_body = tkfont.Font(family=display, size=10)
        self.font_key = tkfont.Font(family=mono, size=16, weight="bold")
        self.font_btn = tkfont.Font(family=display, size=12, weight="bold")
        self.font_status = tkfont.Font(family=mono, size=9)
        self.font_hint = tkfont.Font(family=display, size=8)
        self.font_title = tkfont.Font(family=display, size=9, weight="bold")
        self.font_winbtn = tkfont.Font(family=display, size=11)
        self.font_about_name = tkfont.Font(family=display, size=18, weight="bold")
        self.font_about_author = tkfont.Font(family=display, size=13, weight="bold")
        self.font_about_meta = tkfont.Font(family=mono, size=9)

    def _center(self) -> None:
        self.update_idletasks()
        w, h = 442, 652
        x = (self.winfo_screenwidth() - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _build_ui(self) -> None:
    
        shell = tk.Frame(self, bg=BG, highlightthickness=0)
        shell.pack(fill="both", expand=True, padx=1, pady=1)

   
        titlebar = tk.Frame(shell, bg=BG_PANEL, height=36)
        titlebar.pack(fill="x")
        titlebar.pack_propagate(False)

        title_left = tk.Frame(titlebar, bg=BG_PANEL)
        title_left.pack(side="left", fill="y", padx=(14, 0))

        mark = tk.Canvas(
            title_left, width=10, height=10, bg=BG_PANEL, highlightthickness=0, bd=0
        )
        mark.pack(side="left", pady=13)
        mark.create_rectangle(0, 0, 10, 10, fill=RED, outline="")

        title_lbl = tk.Label(
            title_left,
            text="SNAPTAP",
            font=self.font_title,
            fg=TEXT,
            bg=BG_PANEL,
        )
        title_lbl.pack(side="left", padx=(8, 0), pady=8)

        for widget in (titlebar, title_left, title_lbl, mark):
            widget.bind("<ButtonPress-1>", self._start_drag)
            widget.bind("<B1-Motion>", self._on_drag)
            widget.bind("<Double-Button-1>", lambda _e: None)

        btns = tk.Frame(titlebar, bg=BG_PANEL)
        btns.pack(side="right")

        self._min_btn = self._make_win_btn(
            btns, "─", self._minimize, hover_bg="#1C1C1C", hover_fg=TEXT
        )
        self._close_btn = self._make_win_btn(
            btns, "✕", self._on_close, hover_bg=RED, hover_fg=TEXT
        )

 
        self.glow_canvas = tk.Canvas(
            shell, width=440, height=3, bg=BG, highlightthickness=0, bd=0
        )
        self.glow_canvas.pack(fill="x")
        self._glow_rect = self.glow_canvas.create_rectangle(
            0, 0, 440, 3, fill=RED, outline=""
        )

        root = tk.Frame(shell, bg=BG)
        root.pack(fill="both", expand=True, padx=28, pady=(16, 24))

    
        header = tk.Frame(root, bg=BG)
        header.pack(fill="x")

        brand_row = tk.Frame(header, bg=BG)
        brand_row.pack(fill="x")

        tk.Label(
            brand_row, text="SNAP", font=self.font_brand, fg=TEXT, bg=BG
        ).pack(side="left")
        tk.Label(
            brand_row, text="TAP", font=self.font_brand, fg=RED, bg=BG
        ).pack(side="left")

        self.live_dot = tk.Canvas(
            brand_row, width=14, height=14, bg=BG, highlightthickness=0, bd=0
        )
        self.live_dot.pack(side="right", pady=10)
        self._dot_id = self.live_dot.create_oval(3, 3, 11, 11, fill=TEXT_MUTED, outline="")

        tk.Label(
            header,
            text="LAST INPUT WINS  ·  WASD",
            font=self.font_tag,
            fg=TEXT_MUTED,
            bg=BG,
        ).pack(anchor="w", pady=(2, 0))

  
        div = tk.Canvas(root, height=2, bg=BG, highlightthickness=0, bd=0)
        div.pack(fill="x", pady=18)
        self._div_line = div.create_rectangle(0, 0, 20, 2, fill=RED, outline="")
        div.create_rectangle(24, 0, 384, 2, fill=LINE, outline="")
        self._div_canvas = div

    
        tk.Label(
            root,
            text="Противоположные направления не конфликтуют.\n"
            "Приоритет у последней нажатой клавиши.",
            font=self.font_body,
            fg=TEXT_MUTED,
            bg=BG,
            justify="left",
        ).pack(anchor="w")

   
        panel = tk.Frame(root, bg=BG_PANEL, highlightbackground=LINE, highlightthickness=1)
        panel.pack(fill="x", pady=(22, 0), ipady=8)

        panel_inner = tk.Frame(panel, bg=BG_PANEL)
        panel_inner.pack(pady=22)

        keys_grid = tk.Frame(panel_inner, bg=BG_PANEL)
        keys_grid.pack()

        self._key_widgets["w"] = self._make_key(keys_grid, "W", 1, 0)
        self._key_widgets["a"] = self._make_key(keys_grid, "A", 0, 1)
        self._key_widgets["s"] = self._make_key(keys_grid, "S", 1, 1)
        self._key_widgets["d"] = self._make_key(keys_grid, "D", 2, 1)

        tk.Label(
            panel_inner,
            text="АКТИВНЫЕ ОСИ",
            font=self.font_hint,
            fg=TEXT_MUTED,
            bg=BG_PANEL,
        ).pack(pady=(16, 0))


        self.btn_frame = tk.Frame(root, bg=BG)
        self.btn_frame.pack(fill="x", pady=(28, 0))

        self.btn_canvas = tk.Canvas(
            self.btn_frame,
            height=52,
            bg=BG,
            highlightthickness=0,
            bd=0,
            cursor="hand2",
        )
        self.btn_canvas.pack(fill="x")
        self.btn_canvas.bind("<Enter>", self._btn_enter)
        self.btn_canvas.bind("<Leave>", self._btn_leave)
        self.btn_canvas.bind("<Button-1>", lambda _e: self.toggle())

        self._btn_bg = self.btn_canvas.create_rectangle(
            0, 0, 384, 52, fill=RED, outline="", tags="btn"
        )
        self._btn_inner = self.btn_canvas.create_rectangle(
            2, 2, 382, 50, fill=RED, outline="", tags="btn"
        )
        self._btn_text = self.btn_canvas.create_text(
            192,
            26,
            text="Активировать",
            fill=TEXT,
            font=self.font_btn,
            tags="btn",
        )
        self.btn_canvas.bind("<Configure>", self._resize_btn)

  
        status_box = tk.Frame(root, bg=BG)
        status_box.pack(fill="x", pady=(20, 0))

        left = tk.Frame(status_box, bg=BG)
        left.pack(side="left")

        tk.Label(
            left, text="СТАТУС", font=self.font_hint, fg=TEXT_MUTED, bg=BG
        ).pack(anchor="w")
        self.status_label = tk.Label(
            left, text="STANDBY", font=self.font_status, fg=TEXT_MUTED, bg=BG
        )
        self.status_label.pack(anchor="w")

        right = tk.Frame(status_box, bg=BG)
        right.pack(side="right")

        tk.Label(
            right, text="ВЫХОД · О ПРОГРАММЕ", font=self.font_hint, fg=TEXT_MUTED, bg=BG
        ).pack(anchor="e")
        tk.Label(
            right, text="F9 / ESC · F10", font=self.font_status, fg=TEXT, bg=BG
        ).pack(anchor="e")

      
        footer = tk.Frame(root, bg=BG)
        footer.pack(side="bottom", fill="x", pady=(16, 0))

        tk.Label(
            footer,
            text=f"v{APP_VERSION}  ·  {APP_AUTHOR}",
            font=self.font_hint,
            fg="#444444",
            bg=BG,
        ).pack(side="left")
        tk.Label(
            footer,
            text="ADMIN MODE",
            font=self.font_hint,
            fg=RED_DIM,
            bg=BG,
        ).pack(side="right")

    def _make_win_btn(
        self,
        parent: tk.Frame,
        text: str,
        command,
        hover_bg: str,
        hover_fg: str,
    ) -> tk.Label:
        btn = tk.Label(
            parent,
            text=text,
            font=self.font_winbtn,
            fg=TEXT_MUTED,
            bg=BG_PANEL,
            width=4,
            cursor="hand2",
        )
        btn.pack(side="left", fill="y")

        def on_enter(_e, b=btn, hb=hover_bg, hf=hover_fg):
            b.configure(bg=hb, fg=hf)

        def on_leave(_e, b=btn):
            b.configure(bg=BG_PANEL, fg=TEXT_MUTED)

        def on_click(_e, cmd=command):
            cmd()

        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        btn.bind("<Button-1>", on_click)
        return btn

    def _start_drag(self, event) -> None:
        self._drag_x = event.x_root - self.winfo_x()
        self._drag_y = event.y_root - self.winfo_y()

    def _on_drag(self, event) -> None:
        x = event.x_root - self._drag_x
        y = event.y_root - self._drag_y
        self.geometry(f"+{x}+{y}")

    def _minimize(self) -> None:
      
        self.overrideredirect(False)
        self.iconify()

    def _on_map(self, _event=None) -> None:
        if self.state() == "normal":
            self.overrideredirect(True)
            self._apply_taskbar_style()
            self.lift()

    def _apply_taskbar_style(self) -> None:
        try:
            hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
            if not hwnd:
                hwnd = self.winfo_id()
            gwl_exstyle = -20
            ws_ex_appwindow = 0x00040000
            ws_ex_toolwindow = 0x00000080
            style = ctypes.windll.user32.GetWindowLongW(hwnd, gwl_exstyle)
            style = (style & ~ws_ex_toolwindow) | ws_ex_appwindow
            ctypes.windll.user32.SetWindowLongW(hwnd, gwl_exstyle, style)
        except Exception:
            pass

    def _ensure_taskbar(self) -> None:
        """Keep frameless window visible on the Windows taskbar."""
        if getattr(self, "_taskbar_ready", False):
            return
        try:
            self._apply_taskbar_style()
            self._taskbar_ready = True
            self.wm_withdraw()
            self.after(1, self.wm_deiconify)
        except Exception:
            pass

    def _make_key(self, parent: tk.Frame, label: str, col: int, row: int) -> dict:
        wrap = tk.Frame(parent, bg=BG_PANEL)
        wrap.grid(row=row, column=col, padx=6, pady=6)

        canvas = tk.Canvas(
            wrap, width=72, height=72, bg=BG_PANEL, highlightthickness=0, bd=0
        )
        canvas.pack()

      
        glow = canvas.create_rectangle(4, 4, 68, 68, fill=RED_SOFT, outline="", width=0)
        body = canvas.create_rectangle(
            8, 8, 64, 64, fill=BG_KEY, outline=BG_KEY_EDGE, width=2
        )
        accent = canvas.create_rectangle(8, 8, 64, 11, fill=LINE, outline="")
        text = canvas.create_text(
            36, 38, text=label, fill=TEXT_MUTED, font=self.font_key
        )

        return {
            "canvas": canvas,
            "glow": glow,
            "body": body,
            "accent": accent,
            "text": text,
            "label": label.lower(),
        }

    def _resize_btn(self, event) -> None:
        w = event.width
        self.btn_canvas.coords(self._btn_bg, 0, 0, w, 52)
        self.btn_canvas.coords(self._btn_inner, 2, 2, w - 2, 50)
        self.btn_canvas.coords(self._btn_text, w / 2, 26)
        self._div_canvas.coords(self._div_line, 0, 0, max(20, int(w * 0.12)), 2)

    def _btn_enter(self, _e=None) -> None:
        self._btn_hover = True

    def _btn_leave(self, _e=None) -> None:
        self._btn_hover = False

    def toggle(self) -> None:
        if self._active:
            self.stop()
        else:
            self.start()

    def start(self) -> None:
        if self._active:
            return
        with _lock:
            _held.clear()
            _active["x"] = None
            _active["y"] = None

        self._snap_hook = keyboard.hook(_hook)
        keyboard.add_hotkey("f9", self._hotkey_stop, suppress=False)
        self._active = True
        self.status_label.configure(text="ACTIVE", fg=RED_GLOW)
        self.btn_canvas.itemconfigure(self._btn_text, text="Деактивировать")

    def stop(self) -> None:
        if not self._active:
            return
        self._active = False
        if self._snap_hook is not None:
            try:
                keyboard.unhook(self._snap_hook)
            except Exception:
                pass
            self._snap_hook = None
        try:
            keyboard.remove_hotkey("f9")
        except Exception:
            pass
        release_wasd()
        with _lock:
            _held.clear()
            _active["x"] = None
            _active["y"] = None
        for k in self._key_lit:
            self._key_lit[k] = 0.0
        self.status_label.configure(text="STANDBY", fg=TEXT_MUTED)
        self.btn_canvas.itemconfigure(self._btn_text, text="Активировать")

    def _hotkey_stop(self) -> None:
        self.after(0, self.stop)

    def _on_f10(self, _event=None):
   
        try:
            focused = self.focus_get()
        except tk.TclError:
            return "break"
        if focused is None:
            return "break"
        top = focused.winfo_toplevel()
        if top not in (self, self._about_win):
            return "break"
        if self._about_win is not None and self._about_win.winfo_exists():
            self._about_win._close()
        else:
            self.open_about()
        return "break"

    def open_about(self) -> None:
        if self._about_win is not None and self._about_win.winfo_exists():
            self._about_win.lift()
            self._about_win.focus_force()
            return
        self._about_win = AboutWindow(self)

    def _on_close(self) -> None:
        self._shutdown = True
        self.stop()
        if self._about_win is not None and self._about_win.winfo_exists():
            self._about_win.destroy()
        self.destroy()

    def _animate(self) -> None:
        if self._shutdown:
            return

        self._pulse = (self._pulse + 0.045) % (math.pi * 2)
        pulse = (math.sin(self._pulse) + 1) / 2  

        
        top_color = lerp_color(RED_DIM, RED_GLOW, 0.35 + pulse * 0.65)
        self.glow_canvas.itemconfigure(self._glow_rect, fill=top_color)

      
        if self._active:
            dot_c = lerp_color(RED_DIM, RED_GLOW, pulse)
            self.live_dot.itemconfigure(self._dot_id, fill=dot_c)
        else:
            self.live_dot.itemconfigure(self._dot_id, fill=TEXT_MUTED)

       
        if self._active:
            fill = lerp_color(RED_DIM, "#4A0000", pulse * 0.5)
            border = lerp_color(RED, RED_GLOW, pulse)
            if self._btn_hover:
                fill = lerp_color(fill, RED, 0.25)
        else:
            fill = RED_GLOW if self._btn_hover else RED
            border = RED_GLOW if self._btn_hover else RED
            if self._btn_hover:
                fill = lerp_color(RED, "#FF4A3A", 0.35)

        self.btn_canvas.itemconfigure(self._btn_inner, fill=fill)
        self.btn_canvas.itemconfigure(self._btn_bg, fill=border)

        
        with _lock:
            held = set(_held)
            active_keys = {k for k in (_active["x"], _active["y"]) if k}

        for key, widget in self._key_widgets.items():
            target = 0.0
            if key in active_keys:
                target = 1.0
            elif key in held:
                target = 0.35
            current = self._key_lit[key]
            self._key_lit[key] = current + (target - current) * 0.22
            self._paint_key(widget, self._key_lit[key], pulse)

        self.after(33, self._animate)

    def _paint_key(self, widget: dict, lit: float, pulse: float) -> None:
        canvas = widget["canvas"]
        if lit < 0.02:
            canvas.itemconfigure(widget["glow"], fill=BG_PANEL)
            canvas.itemconfigure(widget["body"], fill=BG_KEY, outline=BG_KEY_EDGE)
            canvas.itemconfigure(widget["accent"], fill=LINE)
            canvas.itemconfigure(widget["text"], fill=TEXT_MUTED)
            return

        glow_mix = lit * (0.55 + pulse * 0.45)
        glow_c = lerp_color(BG_PANEL, RED_SOFT, glow_mix)
        body_c = lerp_color(BG_KEY, "#2A0808", lit)
        edge_c = lerp_color(BG_KEY_EDGE, RED, lit)
        accent_c = lerp_color(LINE, RED_GLOW, lit * (0.7 + pulse * 0.3))
        text_c = lerp_color(TEXT_MUTED, TEXT, min(1.0, lit * 1.4))

        canvas.itemconfigure(widget["glow"], fill=glow_c)
        canvas.itemconfigure(widget["body"], fill=body_c, outline=edge_c)
        canvas.itemconfigure(widget["accent"], fill=accent_c)
        canvas.itemconfigure(widget["text"], fill=text_c)


class AboutWindow(tk.Toplevel):
    def __init__(self, master: SnapTapApp) -> None:
        super().__init__(master)
        self.master_app = master
        self.title(f"О программе — {APP_NAME}")
        self.geometry("360x480")
        self.resizable(False, False)
        self.configure(bg=RED)
        self.overrideredirect(True)
        self.attributes("-topmost", True)

        self._drag_x = 0
        self._drag_y = 0
        self._pulse = 0.0
        self._shutdown = False
        self._logo_img = None

        self._build()
        self._center_on_parent()
        self._animate()

        self.bind("<Escape>", lambda _e: self._close())
        self.protocol("WM_DELETE_WINDOW", self._close)
        self.focus_force()

    def _build(self) -> None:
        shell = tk.Frame(self, bg=BG)
        shell.pack(fill="both", expand=True, padx=1, pady=1)

        titlebar = tk.Frame(shell, bg=BG_PANEL, height=36)
        titlebar.pack(fill="x")
        titlebar.pack_propagate(False)

        title_left = tk.Frame(titlebar, bg=BG_PANEL)
        title_left.pack(side="left", fill="y", padx=(14, 0))

        mark = tk.Canvas(
            title_left, width=10, height=10, bg=BG_PANEL, highlightthickness=0, bd=0
        )
        mark.pack(side="left", pady=13)
        mark.create_rectangle(0, 0, 10, 10, fill=RED, outline="")

        title_lbl = tk.Label(
            title_left,
            text="О ПРОГРАММЕ",
            font=self.master_app.font_title,
            fg=TEXT,
            bg=BG_PANEL,
        )
        title_lbl.pack(side="left", padx=(8, 0), pady=8)

        for widget in (titlebar, title_left, title_lbl, mark):
            widget.bind("<ButtonPress-1>", self._start_drag)
            widget.bind("<B1-Motion>", self._on_drag)

        close = tk.Label(
            titlebar,
            text="✕",
            font=self.master_app.font_winbtn,
            fg=TEXT_MUTED,
            bg=BG_PANEL,
            width=4,
            cursor="hand2",
        )
        close.pack(side="right", fill="y")
        close.bind("<Enter>", lambda _e: close.configure(bg=RED, fg=TEXT))
        close.bind("<Leave>", lambda _e: close.configure(bg=BG_PANEL, fg=TEXT_MUTED))
        close.bind("<Button-1>", lambda _e: self._close())

        self.glow = tk.Canvas(shell, height=3, bg=BG, highlightthickness=0, bd=0)
        self.glow.pack(fill="x")
        self._glow_rect = self.glow.create_rectangle(0, 0, 360, 3, fill=RED, outline="")

        body = tk.Frame(shell, bg=BG)
        body.pack(fill="both", expand=True, padx=28, pady=(24, 22))

   
        logo_frame = tk.Frame(body, bg=BG)
        logo_frame.pack()
        self._logo_img = self._load_logo()
        if self._logo_img is not None:
            tk.Label(logo_frame, image=self._logo_img, bg=BG, bd=0).pack()
        else:
            canvas = tk.Canvas(
                logo_frame, width=120, height=120, bg=BG, highlightthickness=0, bd=0
            )
            canvas.pack()
            canvas.create_rectangle(20, 20, 100, 100, fill=BG_KEY, outline=RED, width=2)
            canvas.create_text(60, 60, text="EK", fill=TEXT, font=self.master_app.font_about_name)

 
        tk.Label(
            body,
            text=APP_AUTHOR,
            font=self.master_app.font_about_author,
            fg=RED_GLOW,
            bg=BG,
        ).pack(pady=(12, 0))

   
        div = tk.Canvas(body, height=2, bg=BG, highlightthickness=0, bd=0)
        div.pack(fill="x", pady=20)
        div.create_rectangle(0, 0, 40, 2, fill=RED, outline="")
        div.create_rectangle(48, 0, 304, 2, fill=LINE, outline="")

    
        lic = tk.Frame(body, bg=BG_PANEL, highlightbackground=LINE, highlightthickness=1)
        lic.pack(fill="x", ipady=12)

        tk.Label(
            lic,
            text="ЛИЦЕНЗИЯ",
            font=self.master_app.font_hint,
            fg=TEXT_MUTED,
            bg=BG_PANEL,
        ).pack()
        tk.Label(
            lic,
            text=APP_LICENSE,
            font=self.master_app.font_about_meta,
            fg=TEXT,
            bg=BG_PANEL,
        ).pack(pady=(4, 0))

     
        name_row = tk.Frame(body, bg=BG)
        name_row.pack(pady=(22, 0))
        tk.Label(
            name_row, text="SNAP", font=self.master_app.font_about_name, fg=TEXT, bg=BG
        ).pack(side="left")
        tk.Label(
            name_row, text="TAP", font=self.master_app.font_about_name, fg=RED, bg=BG
        ).pack(side="left")

        tk.Label(
            body,
            text=f"VERSION  {APP_VERSION}",
            font=self.master_app.font_about_meta,
            fg=TEXT_MUTED,
            bg=BG,
        ).pack(pady=(6, 0))

    def _load_logo(self) -> tk.PhotoImage | None:
        if not LOGO_PATH.is_file():
            return None
        try:
            img = tk.PhotoImage(file=str(LOGO_PATH))
          
            w = img.width()
            if w > 140:
                factor = max(1, math.ceil(w / 120))
                img = img.subsample(factor, factor)
            return img
        except Exception:
            return None

    def _center_on_parent(self) -> None:
        self.update_idletasks()
        px = self.master_app.winfo_rootx()
        py = self.master_app.winfo_rooty()
        pw = self.master_app.winfo_width()
        ph = self.master_app.winfo_height()
        w, h = 360, 480
        x = px + (pw - w) // 2
        y = py + (ph - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _start_drag(self, event) -> None:
        self._drag_x = event.x_root - self.winfo_x()
        self._drag_y = event.y_root - self.winfo_y()

    def _on_drag(self, event) -> None:
        self.geometry(f"+{event.x_root - self._drag_x}+{event.y_root - self._drag_y}")

    def _animate(self) -> None:
        if self._shutdown or not self.winfo_exists():
            return
        self._pulse = (self._pulse + 0.045) % (math.pi * 2)
        pulse = (math.sin(self._pulse) + 1) / 2
        self.glow.itemconfigure(
            self._glow_rect,
            fill=lerp_color(RED_DIM, RED_GLOW, 0.35 + pulse * 0.65),
        )
        self.after(33, self._animate)

    def _close(self) -> None:
        self._shutdown = True
        if self.master_app._about_win is self:
            self.master_app._about_win = None
        self.destroy()


def main() -> None:
    if sys.platform != "win32":
        print("Только Windows.")
        sys.exit(1)

    if not is_admin():
        print("Нужны права администратора, запрашиваю...")
        relaunch_as_admin()
        return

    app = SnapTapApp()
    app.mainloop()


if __name__ == "__main__":
    main()

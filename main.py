"""
剪贴板历史保存管理软件 — Python 版
系统托盘 + 剪贴板监控 + 历史面板
"""
import os
import sys
import json
import time
import ctypes
import hashlib
import sqlite3
import threading
import webbrowser
from datetime import datetime, timedelta
from pathlib import Path
from io import BytesIO

# ==================== 配置 ====================
DATA_DIR = Path("E:/剪切板历史保存")
IMAGES_DIR = DATA_DIR / "images"
DB_PATH = DATA_DIR / "history.db"
POLL_INTERVAL = 500  # 毫秒
DEFAULT_RETENTION = 3  # 天

DATA_DIR.mkdir(parents=True, exist_ok=True)
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

# ==================== 数据库 ====================
class Database:
    def __init__(self):
        self.conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        self._init_tables()

    def _init_tables(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS clipboard_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL CHECK(type IN ('text','image')),
                content TEXT,
                image_path TEXT,
                pinned INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            )
        """)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        self.conn.execute(
            "INSERT OR IGNORE INTO settings (key, value) VALUES ('retention_days', ?)",
            (str(DEFAULT_RETENTION),)
        )
        self.conn.commit()

    def get_all(self, keyword=None):
        if keyword:
            rows = self.conn.execute(
                "SELECT * FROM clipboard_history WHERE type='text' AND content LIKE ? "
                "ORDER BY pinned DESC, created_at DESC LIMIT 300",
                (f"%{keyword}%",)
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT * FROM clipboard_history ORDER BY pinned DESC, created_at DESC LIMIT 300"
            ).fetchall()
        return [dict(zip(['id','type','content','image_path','pinned','created_at'], r)) for r in rows]

    def add_text(self, text):
        now = datetime.now().isoformat()
        existing = self.conn.execute(
            "SELECT id FROM clipboard_history WHERE type='text' AND content=? ORDER BY id DESC LIMIT 1",
            (text,)
        ).fetchone()
        if existing:
            self.conn.execute("UPDATE clipboard_history SET created_at=? WHERE id=?", (now, existing[0]))
        else:
            self.conn.execute(
                "INSERT INTO clipboard_history (type, content, pinned, created_at) VALUES ('text',?,0,?)",
                (text, now)
            )
        self.conn.commit()

    def add_image(self, filepath):
        now = datetime.now().isoformat()
        self.conn.execute(
            "INSERT INTO clipboard_history (type, image_path, pinned, created_at) VALUES ('image',?,0,?)",
            (str(filepath), now)
        )
        self.conn.commit()

    def toggle_pin(self, rid):
        self.conn.execute("UPDATE clipboard_history SET pinned = CASE WHEN pinned=1 THEN 0 ELSE 1 END WHERE id=?", (rid,))
        self.conn.commit()
        return self.conn.execute("SELECT pinned FROM clipboard_history WHERE id=?", (rid,)).fetchone()[0]

    def delete(self, rid):
        row = self.conn.execute("SELECT type, image_path FROM clipboard_history WHERE id=?", (rid,)).fetchone()
        if row and row[0] == 'image' and row[1]:
            try: os.remove(row[1])
            except OSError: pass
        self.conn.execute("DELETE FROM clipboard_history WHERE id=?", (rid,))
        self.conn.commit()

    def get_setting(self, key, default=None):
        row = self.conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return row[0] if row else default

    def set_setting(self, key, value):
        self.conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?,?)", (key, str(value)))
        self.conn.commit()

    def cleanup(self):
        days = int(self.get_setting('retention_days', DEFAULT_RETENTION))
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        rows = self.conn.execute(
            "SELECT image_path FROM clipboard_history WHERE type='image' AND created_at < ?", (cutoff,)
        ).fetchall()
        for (p,) in rows:
            if p and os.path.exists(p):
                try: os.remove(p)
                except OSError: pass
        self.conn.execute("DELETE FROM clipboard_history WHERE created_at < ?", (cutoff,))
        self.conn.commit()

db = Database()

# ==================== 剪贴板监控 ====================
last_text = ""
last_image_hash = ""

def get_clipboard_image():
    """获取剪贴板中的图片，返回 PNG bytes 或 None"""
    try:
        import win32clipboard
        from PIL import Image
        win32clipboard.OpenClipboard()
        if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_DIB):
            data = win32clipboard.GetClipboardData(win32clipboard.CF_DIB)
            win32clipboard.CloseClipboard()
            img = Image.open(BytesIO(data))
            buf = BytesIO()
            img.save(buf, format='PNG')
            return buf.getvalue()
        win32clipboard.CloseClipboard()
    except Exception:
        pass
    return None

def monitor_clipboard():
    """后台轮询剪贴板"""
    global last_text, last_image_hash
    while True:
        try:
            import pyperclip
            text = pyperclip.paste()
            if text and text != last_text and text.strip():
                last_text = text
                db.add_text(text)

            img_data = get_clipboard_image()
            if img_data:
                h = hashlib.md5(img_data).hexdigest()
                if h != last_image_hash:
                    last_image_hash = h
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    fname = f"{ts}_{h[:8]}.png"
                    fpath = IMAGES_DIR / fname
                    fpath.write_bytes(img_data)
                    db.add_image(fpath)
        except Exception:
            pass
        time.sleep(POLL_INTERVAL / 1000.0)

# ==================== UI 窗口 ====================
import tkinter as tk
from tkinter import ttk, messagebox
import ttkbootstrap as tb

main_window = None
search_var = None
card_frame = None
settings_open = False

def toggle_window():
    """切换窗口显示/隐藏（线程安全）"""
    global main_window, settings_open
    if main_window is None:
        return
    # 使用 after 确保 UI 操作在主线程执行
    main_window.after(0, _toggle_window_ui)

def _toggle_window_ui():
    global main_window, settings_open
    if settings_open:
        return
    if main_window is None:
        return
    try:
        if main_window.state() == 'withdrawn':
            main_window.deiconify()
            main_window.lift()
            main_window.focus_force()
            load_cards()
        else:
            main_window.withdraw()
    except Exception:
        pass

def create_window():
    global main_window, search_var, card_frame
    if main_window is not None:
        return

    root = tb.Window(themename="cosmo")
    root.title("剪贴板历史保存")
    root.resizable(True, True)
    root.overrideredirect(False)
    root.withdraw()  # 先隐藏，布局完成后再显示，避免左上角闪现

    # 标题栏
    titlebar = tb.Frame(root, bootstyle="primary")
    titlebar.pack(fill=tk.X)
    title_lbl = tb.Label(titlebar, text="  Catn1p  ", font=("Microsoft YaHei", 11, "bold"),
                         bootstyle="inverse-primary")
    title_lbl.pack(side=tk.LEFT, pady=6)

    # 搜索栏 + 设置按钮
    search_frame = tb.Frame(root, bootstyle="light")
    search_frame.pack(fill=tk.X, padx=12, pady=(10, 4))

    search_var = tk.StringVar()
    search_var.trace_add('write', lambda *a: load_cards())
    search_entry = tb.Entry(search_frame, textvariable=search_var, font=("Microsoft YaHei", 11))
    search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4)

    settings_btn = tb.Button(search_frame, text="⚙", bootstyle="outline-secondary",
                             command=open_settings, width=3)
    settings_btn.pack(side=tk.RIGHT, padx=(8, 0))

    # 卡片区域
    card_container = tb.Frame(root, bootstyle="light")
    card_container.pack(fill=tk.BOTH, expand=True, padx=12, pady=(4, 12))

    canvas = tk.Canvas(card_container, highlightthickness=0, bg="#f5f5f5")
    scrollbar = tb.Scrollbar(card_container, orient=tk.VERTICAL, command=canvas.yview, bootstyle="round")
    card_frame = tb.Frame(canvas, bootstyle="light")

    card_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=card_frame, anchor="nw", tags="card_frame")
    canvas.configure(yscrollcommand=scrollbar.set)

    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_canvas_resize(event):
        canvas.itemconfig("card_frame", width=event.width)

    canvas.bind("<Configure>", _on_canvas_resize)
    canvas.bind_all("<MouseWheel>", _on_mousewheel)
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # 右键退出

    main_window = root
    load_cards()

    # 窗口居中后再显示
    root.update_idletasks()
    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    root.geometry(f"+{(sw-420)//2}+{(sh-640)//2}")
    # 关闭窗口 = 最小化到托盘，不退出
    def hide_window():
        root.withdraw()
    root.protocol('WM_DELETE_WINDOW', hide_window)

    root.deiconify()

def load_cards():
    global card_frame
    if card_frame is None:
        return
    for w in card_frame.winfo_children():
        w.destroy()

    keyword = search_var.get() if search_var else ""
    records = db.get_all(keyword=keyword.strip() if keyword.strip() else None)

    if not records:
        empty_lbl = tb.Label(card_frame, text="📋\nCatn1p\n\n复制文字或图片后即可在此查看",
                             font=("Microsoft YaHei", 12), bootstyle="secondary",
                             justify=tk.CENTER)
        empty_lbl.pack(pady=60)
        return

    for r in records:
        card = tb.Frame(card_frame, bootstyle="default", padding=10)
        card.pack(fill=tk.X, pady=(0, 6))

        # 置顶指示条
        if r['pinned']:
            pin_bar = tk.Frame(card, bg="#FF9800", width=3)
            pin_bar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 8))

        # 内容区
        content_frame = tb.Frame(card, bootstyle="default")
        content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        if r['type'] == 'text':
            preview = (r['content'] or '').replace('\n', ' ')[:100]
            text_lbl = tb.Label(content_frame, text=preview, font=("Microsoft YaHei", 11),
                                bootstyle="default", anchor=tk.W, wraplength=260, cursor="hand2")
            text_lbl.pack(anchor=tk.W)
            text_lbl.bind("<Button-1>", lambda e, rid=r['id']: copy_record(rid))
        else:
            img_frame = tb.Frame(content_frame, bootstyle="default", cursor="hand2")
            img_frame.pack(anchor=tk.W)
            try:
                from PIL import Image, ImageTk
                img = Image.open(r['image_path'])
                img.thumbnail((48, 48), Image.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                img_lbl = tk.Label(img_frame, image=photo, bg="white")
                img_lbl.image = photo
                img_lbl.pack(side=tk.LEFT)
                img_lbl.bind("<Button-1>", lambda e, rid=r['id']: copy_record(rid))
            except Exception:
                pass
            tb.Label(img_frame, text=" 图片", font=("Microsoft YaHei", 10),
                     bootstyle="secondary").pack(side=tk.LEFT, padx=4)

        # 时间
        try:
            t = datetime.fromisoformat(r['created_at'])
            now = datetime.now()
            diff = now - t
            if diff < timedelta(minutes=1): time_str = "刚刚"
            elif diff < timedelta(hours=1): time_str = f"{int(diff.total_seconds()/60)} 分钟前"
            elif diff < timedelta(hours=24): time_str = f"{int(diff.total_seconds()/3600)} 小时前"
            else: time_str = t.strftime("%m-%d %H:%M")
        except Exception:
            time_str = ""
        tb.Label(content_frame, text=time_str, font=("Microsoft YaHei", 9),
                 bootstyle="secondary").pack(anchor=tk.W)

        # 操作按钮
        btn_frame = tb.Frame(card, bootstyle="default")
        btn_frame.pack(side=tk.RIGHT, padx=(8, 0))

        pin_text = "📌" if r['pinned'] else "📍"
        pin_btn = tb.Button(btn_frame, text=pin_text, bootstyle="link",
                            command=lambda rid=r['id']: toggle_pin(rid), width=2)
        pin_btn.pack()
        del_btn = tb.Button(btn_frame, text="🗑", bootstyle="link danger",
                            command=lambda rid=r['id']: delete_record(rid), width=2)
        del_btn.pack()

def copy_record(rid):
    """复制到剪贴板"""
    from pyperclip import copy as pyperclip_copy
    row = db.conn.execute("SELECT type, content, image_path FROM clipboard_history WHERE id=?", (rid,)).fetchone()
    if not row:
        return
    if row[0] == 'text' and row[1]:
        pyperclip_copy(row[1])
        show_toast("已复制到剪贴板")
    elif row[0] == 'image' and row[2] and os.path.exists(row[2]):
        try:
            from PIL import Image
            from io import BytesIO
            import win32clipboard
            img = Image.open(row[2])
            output = BytesIO()
            img.convert("RGB").save(output, "BMP")
            data = output.getvalue()[14:]
            output.close()
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
            win32clipboard.CloseClipboard()
            show_toast("图片已复制到剪贴板")
        except Exception as e:
            show_toast(f"复制失败: {e}")
    time.sleep(0.3)
    if main_window:
        main_window.withdraw()

def toggle_pin(rid):
    pinned = db.toggle_pin(rid)
    load_cards()

def delete_record(rid):
    db.delete(rid)
    load_cards()
    show_toast("已删除")

def show_toast(msg):
    """简单提示"""
    if main_window:
        toast = tb.Toplevel(main_window)
        toast.overrideredirect(True)
        toast.attributes('-topmost', True)
        lbl = tb.Label(toast, text=msg, font=("Microsoft YaHei", 11),
                       bootstyle="dark-inverse", padding=(20, 10))
        lbl.pack()
        toast.update_idletasks()
        w, h = toast.winfo_width(), toast.winfo_height()
        mw, mh = main_window.winfo_width(), main_window.winfo_height()
        mx, my = main_window.winfo_x(), main_window.winfo_y()
        toast.geometry(f"+{mx+(mw-w)//2}+{my+mh-h-60}")
        toast.after(1500, toast.destroy)

# ==================== 设置面板 ====================
def open_settings():
    global settings_open
    if settings_open:
        return
    settings_open = True
    dialog = tb.Toplevel(main_window)
    dialog.title("设置")
    dialog.geometry("300x220")
    dialog.resizable(False, False)
    dialog.transient(main_window)

    dialog.update_idletasks()
    mx, my = main_window.winfo_x(), main_window.winfo_y()
    mw, mh = main_window.winfo_width(), main_window.winfo_height()
    dialog.geometry(f"+{mx+(mw-300)//2}+{my+(mh-220)//2}")

    tb.Label(dialog, text="保留天数设置", font=("Microsoft YaHei", 14, "bold"),
             bootstyle="default").pack(pady=(16, 4))
    tb.Label(dialog, text="自动删除超过以下天数的记录：",
             font=("Microsoft YaHei", 10), bootstyle="secondary").pack()

    current = int(db.get_setting('retention_days', str(DEFAULT_RETENTION)))
    retention_var = tk.IntVar(value=current)

    radio_frame = tb.Frame(dialog, bootstyle="default")
    radio_frame.pack(pady=12)
    for val, label in [(1, "1 天"), (3, "3 天"), (5, "5 天")]:
        tb.Radiobutton(radio_frame, text=label, variable=retention_var,
                       value=val, bootstyle="primary").pack(side=tk.LEFT, padx=8)

    def save_and_close():
        db.set_setting('retention_days', str(retention_var.get()))
        global settings_open
        settings_open = False
        dialog.destroy()
        show_toast(f"已设置为保留 {retention_var.get()} 天")

    dialog.protocol('WM_DELETE_WINDOW', save_and_close)
    tb.Button(dialog, text="保存", bootstyle="primary", command=save_and_close,
              width=10).pack(pady=8)

# ==================== 系统托盘 ====================
def create_tray():
    import pystray
    from PIL import Image, ImageDraw

    # 创建托盘图标
    icon_img = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
    draw = ImageDraw.Draw(icon_img)
    draw.rounded_rectangle([2, 2, 30, 30], radius=6, fill=(66, 165, 245))
    draw.text((10, 6), "📋", fill=(255, 255, 255))

    def on_open(icon, item):
        main_window.after(0, toggle_window)

    def on_settings(icon, item):
        main_window.after(0, open_settings)

    def on_exit(icon, item):
        icon.stop()
        if main_window:
            main_window.destroy()
        os._exit(0)

    menu = pystray.Menu(
        pystray.MenuItem("打开历史记录", on_open, default=True),
        pystray.MenuItem("设置", on_settings),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("退出", on_exit),
    )

    tray_icon = pystray.Icon("clipboard_history", icon_img, "剪贴板历史保存", menu)
    return tray_icon

# ==================== 启动 ====================
def main():
    # 设置 DPI 感知
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

    # 启动剪贴板监控线程
    monitor_thread = threading.Thread(target=monitor_clipboard, daemon=True)
    monitor_thread.start()

    # 启动时清理过期记录
    db.cleanup()

    # 创建窗口（必须在主线程，先于托盘）
    create_window()  # 直接显示窗口

    # 设置定时清理
    def periodic_cleanup():
        db.cleanup()
        if main_window:
            main_window.after(3600000, periodic_cleanup)
    main_window.after(60000, periodic_cleanup)

    # 创建系统托盘（在独立线程运行）
    tray = create_tray()
    tray_thread = threading.Thread(target=tray.run, daemon=True)
    tray_thread.start()

    # 主线程运行 Tkinter 事件循环
    main_window.mainloop()

if __name__ == "__main__":
    main()

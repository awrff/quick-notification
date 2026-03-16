import asyncio
import json
import logging
import os
import socket
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional

import customtkinter as ctk
import websockets
from websockets.exceptions import ConnectionClosed

try:
    import pystray
    from PIL import Image as PILImage
    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

CONFIG_DIR = Path.home() / ".quick-message"
CONFIG_FILE = CONFIG_DIR / "config.json"


class Config:
    def __init__(self):
        self.minimize_to_tray = False
        self.popup_notification = True
        self.auto_copy = False
        self.load()
    
    def load(self):
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.minimize_to_tray = data.get('minimize_to_tray', False)
                    self.popup_notification = data.get('popup_notification', True)
                    self.auto_copy = data.get('auto_copy', False)
            except Exception as e:
                logger.error(f"加载配置失败: {e}")
    
    def save(self):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump({
                    'minimize_to_tray': self.minimize_to_tray,
                    'popup_notification': self.popup_notification,
                    'auto_copy': self.auto_copy
                }, f)
        except Exception as e:
            logger.error(f"保存配置失败: {e}")


class SMSPopup(ctk.CTkToplevel):
    def __init__(self, master, sender: str, content: str, timestamp: str, 
                 auto_copied: bool = False, on_copy=None):
        super().__init__(master)
        
        self.sender = sender
        self.content = content
        self.timestamp = timestamp
        self.on_copy = on_copy
        self.auto_copied = auto_copied
        
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        
        self.configure(
            fg_color=("#FFFFFF", "#1F1F1F"),
            corner_radius=12
        )
        
        self._setup_ui()
        self._position_window()
        
        if auto_copied:
            self.after(500, self._show_copied_state)
        
        self.after(15000, self._auto_dismiss)
    
    def _setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 8))
        header_frame.grid_columnconfigure(1, weight=1)
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="新短信",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=("#1A73E8", "#4DA3FF")
        )
        title_label.grid(row=0, column=0, sticky="w")
        
        time_label = ctk.CTkLabel(
            header_frame,
            text=self.timestamp,
            font=ctk.CTkFont(size=11),
            text_color=("#666666", "#888888")
        )
        time_label.grid(row=0, column=1, sticky="e")
        
        sender_label = ctk.CTkLabel(
            self,
            text=f"来自: {self.sender}",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=("#333333", "#E0E0E0"),
            anchor="w"
        )
        sender_label.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 4))
        
        display_content = self.content
        if len(display_content) > 100:
            display_content = display_content[:100] + "..."
        
        content_label = ctk.CTkLabel(
            self,
            text=display_content,
            font=ctk.CTkFont(size=13),
            text_color=("#333333", "#E0E0E0"),
            wraplength=280,
            justify="left",
            anchor="w"
        )
        content_label.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 12))
        
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.grid(row=3, column=0, sticky="ew", padx=16, pady=(0, 16))
        button_frame.grid_columnconfigure((0, 1), weight=1)
        
        self.copy_btn = ctk.CTkButton(
            button_frame,
            text="Copy" if not self.auto_copied else "Copied",
            font=ctk.CTkFont(size=12),
            fg_color=("#E8F0FE", "#1E3A5F"),
            text_color=("#1A73E8", "#4DA3FF"),
            hover_color=("#D2E3FC", "#2D4A6F"),
            height=32,
            corner_radius=8,
            command=self._on_copy_click
        )
        self.copy_btn.grid(row=0, column=0, sticky="ew", padx=(0, 4))
        
        if self.auto_copied:
            self.copy_btn.configure(state="disabled")
        
        dismiss_btn = ctk.CTkButton(
            button_frame,
            text="Dismiss",
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            text_color=("#666666", "#888888"),
            hover_color=("#EEEEEE", "#333333"),
            height=32,
            corner_radius=8,
            command=self._dismiss
        )
        dismiss_btn.grid(row=0, column=1, sticky="ew", padx=(4, 0))
    
    def _position_window(self):
        self.update_idletasks()
        
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        window_width = 320
        window_height = self.winfo_reqheight()
        
        x = screen_width - window_width - 20
        y = screen_height - window_height - 60
        
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")
    
    def _on_copy_click(self):
        self._copy_to_clipboard()
        self._show_copied_state()
        self.after(800, self._dismiss)
    
    def _copy_to_clipboard(self):
        self.clipboard_clear()
        self.clipboard_append(self.content)
        self.update()
        if self.on_copy:
            self.on_copy()
    
    def _show_copied_state(self):
        self.copy_btn.configure(text="Copied", state="disabled")
    
    def _dismiss(self):
        self.destroy()
    
    def _auto_dismiss(self):
        try:
            self.destroy()
        except:
            pass


class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, master, config: Config, on_save=None):
        super().__init__(master)
        
        self.config = config
        self.on_save = on_save
        
        self.title("设置")
        self.geometry("360x400")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        
        self.configure(fg_color=("#FFFFFF", "#1F1F1F"))
        
        self._setup_ui()
        self._center_window()
        
        self.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def _center_window(self):
        self.update_idletasks()
        
        master_x = self.master.winfo_x()
        master_y = self.master.winfo_y()
        master_width = self.master.winfo_width()
        master_height = self.master.winfo_height()
        
        window_width = 360
        window_height = 400
        
        x = master_x + (master_width - window_width) // 2
        y = master_y + (master_height - window_height) // 2
        
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")
    
    def _setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        
        title_label = ctk.CTkLabel(
            self,
            text="设置",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=("#1A1A1A", "#FFFFFF")
        )
        title_label.grid(row=0, column=0, sticky="w", padx=20, pady=(20, 16))
        
        settings_frame = ctk.CTkFrame(self, fg_color="transparent")
        settings_frame.grid(row=1, column=0, sticky="ew", padx=20)
        settings_frame.grid_columnconfigure(0, weight=1)
        
        self.minimize_var = ctk.BooleanVar(value=self.config.minimize_to_tray)
        self.popup_var = ctk.BooleanVar(value=self.config.popup_notification)
        self.auto_copy_var = ctk.BooleanVar(value=self.config.auto_copy)
        
        self._add_setting_row(
            settings_frame, 0,
            "退出到托盘",
            "关闭窗口时最小化到系统托盘",
            self.minimize_var
        )
        
        self._add_setting_row(
            settings_frame, 1,
            "启用弹窗通知",
            "收到短信时弹出通知窗口",
            self.popup_var
        )
        
        self._add_setting_row(
            settings_frame, 2,
            "自动复制",
            "收到短信时自动复制到剪贴板",
            self.auto_copy_var
        )
        
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=20)
        button_frame.grid_columnconfigure(0, weight=1)
        
        save_btn = ctk.CTkButton(
            button_frame,
            text="保存",
            font=ctk.CTkFont(size=14),
            height=36,
            corner_radius=8,
            command=self._save_and_close
        )
        save_btn.grid(row=0, column=0, sticky="ew")
    
    def _add_setting_row(self, parent, row: int, title: str, description: str, var: ctk.BooleanVar):
        row_frame = ctk.CTkFrame(parent, fg_color=("#F5F5F5", "#2D2D2D"), corner_radius=8)
        row_frame.grid(row=row, column=0, sticky="ew", pady=4)
        row_frame.grid_columnconfigure(0, weight=1)
        
        text_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
        text_frame.grid(row=0, column=0, sticky="ew", padx=12, pady=10)
        text_frame.grid_columnconfigure(0, weight=1)
        
        title_label = ctk.CTkLabel(
            text_frame,
            text=title,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=("#1A1A1A", "#FFFFFF"),
            anchor="w"
        )
        title_label.grid(row=0, column=0, sticky="w")
        
        desc_label = ctk.CTkLabel(
            text_frame,
            text=description,
            font=ctk.CTkFont(size=11),
            text_color=("#666666", "#888888"),
            anchor="w"
        )
        desc_label.grid(row=1, column=0, sticky="w")
        
        switch = ctk.CTkSwitch(
            row_frame,
            text="",
            variable=var,
            width=44,
            switch_width=44,
            switch_height=24,
            corner_radius=12,
            fg_color=("#CCCCCC", "#444444"),
            progress_color=("#1A73E8", "#4DA3FF"),
            button_color=("#FFFFFF", "#FFFFFF"),
            button_hover_color=("#F0F0F0", "#F0F0F0")
        )
        switch.grid(row=0, column=1, padx=12, pady=10)
    
    def _save_and_close(self):
        self.config.minimize_to_tray = self.minimize_var.get()
        self.config.popup_notification = self.popup_var.get()
        self.config.auto_copy = self.auto_copy_var.get()
        self.config.save()
        
        if self.on_save:
            self.on_save()
        
        self.destroy()
    
    def _on_close(self):
        self.destroy()


class MessageCard(ctk.CTkFrame):
    def __init__(self, master, sender: str, content: str, timestamp: str, **kwargs):
        super().__init__(master, **kwargs)
        
        self.configure(
            fg_color=("#F5F5F5", "#2D2D2D"),
            corner_radius=12,
            border_width=0
        )
        
        self.grid_columnconfigure(0, weight=1)
        
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 4))
        header_frame.grid_columnconfigure(1, weight=1)
        
        sender_label = ctk.CTkLabel(
            header_frame,
            text=sender,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=("#1A73E8", "#4DA3FF")
        )
        sender_label.grid(row=0, column=0, sticky="w")
        
        time_label = ctk.CTkLabel(
            header_frame,
            text=timestamp,
            font=ctk.CTkFont(size=11),
            text_color=("#666666", "#888888")
        )
        time_label.grid(row=0, column=1, sticky="e")
        
        content_label = ctk.CTkLabel(
            self,
            text=content,
            font=ctk.CTkFont(size=13),
            text_color=("#333333", "#E0E0E0"),
            wraplength=400,
            justify="left",
            anchor="w"
        )
        content_label.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 12))


class QuickMessageApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.config = Config()
        
        self.title("Quick Message")
        self.geometry("500x700")
        self.minsize(400, 500)
        
        self._center_window()
        
        self.configure(window_bg_color=("#FFFFFF", "#1A1A1A"))
        
        self.host = "0.0.0.0"
        self.port: int = 0
        self.server: Optional[websockets.serve] = None
        self.server_loop: Optional[asyncio.AbstractEventLoop] = None
        self.server_thread: Optional[threading.Thread] = None
        self.broadcast_thread: Optional[threading.Thread] = None
        self.is_running = False
        self.message_count = 0
        self.connected_device: Optional[str] = None
        
        self.tray_icon = None
        self.is_hidden = False
        
        self._setup_ui()
        self._start_server()
        self._setup_tray()
        
        self.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _center_window(self):
        self.update_idletasks()
        
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        window_width = 500
        window_height = 700
        
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")
    
    def _setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        header_frame.grid_columnconfigure(0, weight=1)
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="Quick Message",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=("#1A1A1A", "#FFFFFF")
        )
        title_label.grid(row=0, column=0, sticky="w")
        
        settings_btn = ctk.CTkButton(
            header_frame,
            text="",
            font=ctk.CTkFont(size=14),
            fg_color="transparent",
            text_color=("#666666", "#888888"),
            hover_color=("#EEEEEE", "#333333"),
            width=36,
            height=36,
            corner_radius=8,
            command=self._show_settings
        )
        settings_btn.grid(row=0, column=1)
        
        try:
            settings_btn.configure(text="⚙")
        except:
            settings_btn.configure(text="S")
        
        status_frame = ctk.CTkFrame(
            self,
            fg_color=("#E8F0FE", "#1E3A5F"),
            corner_radius=12
        )
        status_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=10)
        status_frame.grid_columnconfigure(1, weight=1)
        
        self.status_indicator = ctk.CTkLabel(
            status_frame,
            text="●",
            font=ctk.CTkFont(size=16),
            text_color=("#4CAF50", "#4CAF50")
        )
        self.status_indicator.grid(row=0, column=0, padx=(16, 8), pady=12)
        
        status_text_frame = ctk.CTkFrame(status_frame, fg_color="transparent")
        status_text_frame.grid(row=0, column=1, sticky="ew", pady=12)
        status_text_frame.grid_rowconfigure(1, weight=1)
        
        self.status_label = ctk.CTkLabel(
            status_text_frame,
            text="正在启动服务器...",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=("#1A73E8", "#4DA3FF"),
            anchor="w"
        )
        self.status_label.grid(row=0, column=0, sticky="w")
        
        self.device_label = ctk.CTkLabel(
            status_text_frame,
            text="等待设备连接",
            font=ctk.CTkFont(size=11),
            text_color=("#666666", "#888888"),
            anchor="w"
        )
        self.device_label.grid(row=1, column=0, sticky="w")
        
        self.count_label = ctk.CTkLabel(
            status_frame,
            text="0 条消息",
            font=ctk.CTkFont(size=12),
            text_color=("#666666", "#888888")
        )
        self.count_label.grid(row=0, column=2, padx=16, pady=12)
        
        messages_frame = ctk.CTkFrame(self, fg_color="transparent")
        messages_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 10))
        messages_frame.grid_columnconfigure(0, weight=1)
        messages_frame.grid_rowconfigure(1, weight=1)
        
        messages_header = ctk.CTkFrame(messages_frame, fg_color="transparent")
        messages_header.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        messages_header.grid_columnconfigure(0, weight=1)
        
        messages_title = ctk.CTkLabel(
            messages_header,
            text="消息",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=("#1A1A1A", "#FFFFFF")
        )
        messages_title.grid(row=0, column=0, sticky="w")
        
        clear_btn = ctk.CTkButton(
            messages_header,
            text="清空",
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            text_color=("#666666", "#888888"),
            hover_color=("#EEEEEE", "#333333"),
            width=60,
            height=28,
            corner_radius=8,
            command=self._clear_messages
        )
        clear_btn.grid(row=0, column=1)
        
        self.scrollable_frame = ctk.CTkScrollableFrame(
            messages_frame,
            fg_color="transparent",
            scrollbar_button_color=("#CCCCCC", "#444444"),
            scrollbar_button_hover_color=("#AAAAAA", "#555555")
        )
        self.scrollable_frame.grid(row=1, column=0, sticky="nsew")
        self.scrollable_frame.grid_columnconfigure(0, weight=1)
        
        self.empty_label = ctk.CTkLabel(
            self.scrollable_frame,
            text="暂无消息\n\n请确保手机和电脑在同一网络下\n然后在手机端点击连接按钮",
            font=ctk.CTkFont(size=13),
            text_color=("#999999", "#666666"),
            justify="center"
        )
        self.empty_label.grid(row=0, column=0, pady=50)
    
    def _show_settings(self):
        SettingsWindow(self, self.config, self._on_settings_saved)
    
    def _on_settings_saved(self):
        pass
    
    def _setup_tray(self):
        if not TRAY_AVAILABLE:
            return
        
        def create_icon():
            return PILImage.new('RGB', (64, 64), color='#1A73E8')
        
        def on_show(icon, item):
            self.after(0, self._show_window)
        
        def on_exit(icon, item):
            self.after(0, self._quit_app)
        
        menu = pystray.Menu(
            pystray.MenuItem("显示", on_show, default=True),
            pystray.MenuItem("退出", on_exit)
        )
        
        self.tray_icon = pystray.Icon("quick_message", create_icon(), "Quick Message", menu)
    
    def _show_window(self):
        self.is_hidden = False
        self.deiconify()
        self.lift()
        self.focus_force()
    
    def _hide_window(self):
        self.is_hidden = True
        self.withdraw()
        if self.tray_icon and not self.tray_icon.visible:
            threading.Thread(target=self.tray_icon.run, daemon=True).start()
    
    def _start_server(self):
        def run_server():
            self.server_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.server_loop)
            
            try:
                self.server_loop.run_until_complete(self._run_server_async())
            except Exception as e:
                logger.exception(f"服务器错误: {e}")
                self.after(0, lambda: self._update_status(f"服务器错误: {e}", False))
        
        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()
    
    async def _run_server_async(self):
        try:
            async with websockets.serve(
                self._handle_connection,
                self.host,
                self.port,
                ping_interval=20,
                ping_timeout=60
            ) as server:
                self.server = server
                self.port = server.sockets[0].getsockname()[1]
                self.is_running = True
                
                logger.info(f"服务器启动在 ws://{self.host}:{self.port}")
                self.after(0, lambda: self._update_status(
                    f"服务器已启动 (端口: {self.port})", True
                ))
                
                self.broadcast_thread = threading.Thread(
                    target=self._broadcast_port, daemon=True
                )
                self.broadcast_thread.start()
                
                await asyncio.Future()
        except Exception as e:
            logger.exception(f"服务器启动失败: {e}")
            self.after(0, lambda: self._update_status(f"启动失败: {e}", False))
    
    def _broadcast_port(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.settimeout(1)
        
        while self.is_running:
            try:
                message = f"SMS_FORWARDER_PORT:{self.port}"
                data = message.encode('utf-8')
                sock.sendto(data, ('255.255.255.255', 12345))
            except Exception as e:
                logger.debug(f"广播失败: {e}")
            import time
            time.sleep(5)
        
        sock.close()
    
    async def _handle_connection(self, websocket):
        remote = websocket.remote_address
        logger.info(f"新连接: {remote}")
        
        self.connected_device = f"{remote[0]}:{remote[1]}"
        self.after(0, lambda: self._update_device_status(
            f"设备已连接 ({remote[0]})", True
        ))
        
        try:
            async for message in websocket:
                logger.debug(f"收到消息: {message}")
                await self._process_message(message)
        except ConnectionClosed as e:
            logger.info(f"连接关闭: {e}")
        except Exception as e:
            logger.exception(f"连接错误: {e}")
        finally:
            self.connected_device = None
            self.after(0, lambda: self._update_device_status("等待设备连接", False))
    
    async def _process_message(self, message: str):
        try:
            data = json.loads(message)
            sender = data.get("sender", "未知")
            content = data.get("content", "")
            timestamp = data.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            
            self.message_count += 1
            
            auto_copied = False
            if self.config.auto_copy:
                self.after(0, lambda c=content: self._copy_to_clipboard(c))
                auto_copied = True
            
            self.after(0, lambda: self._add_message(sender, content, timestamp))
            
            if self.config.popup_notification:
                self.after(0, lambda: self._show_popup(sender, content, timestamp, auto_copied))
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析错误: {e}")
    
    def _copy_to_clipboard(self, content: str):
        self.clipboard_clear()
        self.clipboard_append(content)
        self.update()
    
    def _show_popup(self, sender: str, content: str, timestamp: str, auto_copied: bool):
        SMSPopup(self, sender, content, timestamp, auto_copied)
    
    def _update_status(self, status: str, is_ok: bool):
        self.status_label.configure(text=status)
        color = "#4CAF50" if is_ok else "#F44336"
        self.status_indicator.configure(text_color=color)
    
    def _update_device_status(self, status: str, connected: bool):
        self.device_label.configure(text=status)
        color = "#4CAF50" if connected else ("#666666", "#888888")
        self.device_label.configure(text_color=color)
    
    def _add_message(self, sender: str, content: str, timestamp: str):
        if self.message_count == 1:
            self.empty_label.grid_forget()
        
        card = MessageCard(
            self.scrollable_frame,
            sender=sender,
            content=content,
            timestamp=timestamp
        )
        card.grid(row=self.message_count - 1, column=0, sticky="ew", pady=(0, 8))
        
        self.count_label.configure(text=f"{self.message_count} 条消息")
        
        self.after(100, lambda: self.scrollable_frame._parent_canvas.yview_moveto(1.0))
    
    def _clear_messages(self):
        for widget in self.scrollable_frame.winfo_children():
            if isinstance(widget, MessageCard):
                widget.destroy()
        
        self.message_count = 0
        self.count_label.configure(text="0 条消息")
        
        self.empty_label = ctk.CTkLabel(
            self.scrollable_frame,
            text="暂无消息\n\n请确保手机和电脑在同一网络下\n然后在手机端点击连接按钮",
            font=ctk.CTkFont(size=13),
            text_color=("#999999", "#666666"),
            justify="center"
        )
        self.empty_label.grid(row=0, column=0, pady=50)
    
    def _on_closing(self):
        if self.config.minimize_to_tray and TRAY_AVAILABLE:
            self._hide_window()
        else:
            self._quit_app()
    
    def _quit_app(self):
        self.is_running = False
        
        if self.tray_icon:
            self.tray_icon.stop()
        
        if self.server_loop and self.server_loop.is_running():
            self.server_loop.call_soon_threadsafe(self.server_loop.stop)
        
        self.destroy()


def main():
    app = QuickMessageApp()
    app.mainloop()


if __name__ == "__main__":
    main()

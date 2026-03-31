import logging
import sys
import threading
from typing import Optional, List

import customtkinter as ctk

try:
    import pystray
    from PIL import Image as PILImage
    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False

from .config import Config, SMSMessage, MessageStorage
from .server import SMSServer
from .ui import SMSPopup, SettingsWindow, MessageCard, FilterWindow
from .filter_config import FilterSettings, apply_filter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


def get_icon_path():
    from pathlib import Path
    if getattr(sys, 'frozen', False):
        base_path = Path(sys._MEIPASS)
    else:
        base_path = Path(__file__).parent.parent.parent.parent
    return base_path / "assets" / "quick-notification.ico"


def load_button_icon(icon_name: str, size: int = 20, color: tuple = (100, 100, 100)):
    from pathlib import Path
    from PIL import Image, ImageOps
    
    if getattr(sys, 'frozen', False):
        base_path = Path(sys._MEIPASS)
    else:
        base_path = Path(__file__).parent.parent.parent.parent
    
    icon_path = base_path / "assets" / icon_name
    if icon_path.exists():
        try:
            img = Image.open(icon_path).convert("RGBA")
            
            datas = img.getdata()
            new_data = []
            for item in datas:
                if item[3] > 0:
                    brightness = (item[0] + item[1] + item[2]) / 3
                    if brightness < 128:
                        new_data.append((color[0], color[1], color[2], item[3]))
                    else:
                        new_data.append(item)
                else:
                    new_data.append(item)
            img.putdata(new_data)
            
            return ctk.CTkImage(img, size=(size, size))
        except Exception:
            pass
    return None


class QuickNotificationApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.config = Config()
        self.message_storage = MessageStorage()
        self.filter_settings = FilterSettings()
        
        self.title("Quick Notification")
        self.geometry("500x700")
        self.minsize(400, 500)
        
        self._set_window_icon()
        
        self._center_window()
        
        self.configure(window_bg_color=("#FFFFFF", "#1A1A1A"))
        
        self.messages: List[SMSMessage] = []
        self.message_count = 0
        self.connected_device: Optional[str] = None
        
        self.tray_icon = None
        self.is_hidden = False
        
        self._setup_thread_safe_events()
        
        self.server = SMSServer(
            on_message=self._on_new_message,
            on_device_connected=self._on_device_connected,
            on_device_disconnected=self._on_device_disconnected,
            on_status_update=self._on_status_update
        )
        
        self._setup_ui()
        self._load_saved_messages()
        self.server.start()
        self._setup_tray()
        
        self.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _setup_thread_safe_events(self):
        self._pending_callbacks = {}
        self._callback_id = 0
        
        self.bind("<<ThreadCallback>>", self._process_thread_callback)
    
    def _schedule_callback(self, callback):
        self._callback_id += 1
        callback_id = self._callback_id
        self._pending_callbacks[callback_id] = callback
        self.event_generate("<<ThreadCallback>>")
        return callback_id
    
    def _process_thread_callback(self, event):
        callbacks_to_process = list(self._pending_callbacks.values())
        self._pending_callbacks.clear()
        for callback in callbacks_to_process:
            callback()
    
    def _center_window(self):
        self.update_idletasks()
        
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        window_width = 500
        window_height = 700
        
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")
    
    def _set_window_icon(self):
        try:
            icon_path = get_icon_path()
            if icon_path.exists():
                self.iconbitmap(str(icon_path))
        except Exception as e:
            logger.warning(f"无法加载窗口图标: {e}")
    
    def _setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        header_frame.grid_columnconfigure(0, weight=1)
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="Quick Notification",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=("#1A1A1A", "#FFFFFF")
        )
        title_label.grid(row=0, column=0, sticky="w")
        
        btn_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        btn_frame.grid(row=0, column=1)
        
        filter_btn = ctk.CTkButton(
            btn_frame,
            text="",
            image=load_button_icon("filter.png", 20, (136, 136, 136)),
            fg_color="transparent",
            text_color=("#666666", "#888888"),
            hover_color=("#EEEEEE", "#333333"),
            width=36,
            height=36,
            corner_radius=8,
            command=self._show_filter
        )
        filter_btn.grid(row=0, column=0, padx=(0, 4))
        
        settings_btn = ctk.CTkButton(
            btn_frame,
            text="",
            image=load_button_icon("settings.png", 20, (136, 136, 136)),
            fg_color="transparent",
            text_color=("#666666", "#888888"),
            hover_color=("#EEEEEE", "#333333"),
            width=36,
            height=36,
            corner_radius=8,
            command=self._show_settings
        )
        settings_btn.grid(row=0, column=1)
        
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
    
    def _load_saved_messages(self):
        if self.config.save_messages:
            saved_messages = self.message_storage.load()
            if saved_messages:
                self.empty_label.grid_forget()
                self.messages = saved_messages
                self.message_count = len(saved_messages)
                for i, msg in enumerate(saved_messages):
                    self._add_message_card_at_end(msg, i)
    
    def _add_message_card_at_end(self, message: SMSMessage, row: int):
        card = MessageCard(
            self.scrollable_frame,
            sender=message.sender,
            content=message.content,
            timestamp=message.timestamp,
            on_copy=self._copy_to_clipboard,
            on_delete=self._delete_message
        )
        card.grid(row=row, column=0, sticky="ew", pady=(0, 8))
        self.count_label.configure(text=f"{self.message_count} 条消息")
    
    def _show_settings(self):
        self._settings_window = SettingsWindow(self, self.config, self._on_settings_saved)
    
    def _show_filter(self):
        self._filter_window = FilterWindow(self, self.filter_settings, self._on_filter_saved)
    
    def _on_filter_saved(self):
        pass
    
    def _on_settings_saved(self):
        pass
    
    def _setup_tray(self):
        if not TRAY_AVAILABLE:
            return
        
        icon_path = get_icon_path()
        if not icon_path.exists():
            return
        
        icon = PILImage.open(icon_path)
        
        def on_show(icon, item):
            self.after(0, self._show_window)
        
        def on_exit(icon, item):
            self.after(0, self._quit_app)
        
        menu = pystray.Menu(
            pystray.MenuItem("显示", on_show, default=True),
            pystray.MenuItem("退出", on_exit)
        )
        
        self.tray_icon = pystray.Icon("quick_notification", icon, "Quick Notification", menu)
        threading.Thread(target=self.tray_icon.run, daemon=True).start()
    
    def _show_window(self):
        self.is_hidden = False
        self.deiconify()
        self.lift()
        self.focus_force()
    
    def _hide_window(self):
        self.is_hidden = True
        self.withdraw()
    
    def _on_new_message(self, sender: str, content: str, timestamp: str):
        copy_content = content
        
        if self.filter_settings.filter_enabled:
            rules = self.filter_settings.get_all_enabled_rules()
            if rules:
                should_show, extracted_content = apply_filter(content, rules)
                if not should_show:
                    return
                copy_content = extracted_content
        
        message = SMSMessage(sender=sender, content=content, timestamp=timestamp)
        
        if self.config.save_messages:
            self.message_storage.add_message(message)
            self.messages = self.message_storage.messages
        else:
            self.messages.insert(0, message)
        
        self.message_count = len(self.messages)
        
        auto_copied = False
        if self.config.auto_copy:
            self._schedule_callback(lambda c=content: self._copy_to_clipboard(c))
            auto_copied = True
        
        self._schedule_callback(lambda: self._add_message_card(message, scroll_to_top=True))
        
        if self.config.popup_notification:
            self._schedule_callback(lambda: self._show_popup(sender, content, timestamp, auto_copied))
    
    def _on_device_connected(self, device: str):
        self.connected_device = device
        ip = device.split(':')[0]
        self._schedule_callback(lambda: self._update_device_status(f"设备已连接 ({ip})", True))
    
    def _on_device_disconnected(self):
        self.connected_device = None
        self._schedule_callback(lambda: self._update_device_status("等待设备连接", False))
    
    def _on_status_update(self, status: str, is_ok: bool):
        self._schedule_callback(lambda: self._update_status(status, is_ok))
    
    def _copy_to_clipboard(self, content: str):
        self.clipboard_clear()
        self.clipboard_append(content)
        self.update()
    
    def _show_popup(self, sender: str, content: str, timestamp: str, auto_copied: bool, copy_content: str = None):
        if copy_content is None:
            copy_content = content
        SMSPopup(self, sender, content, timestamp, auto_copied, on_dismiss_all=self._dismiss_all_popups, copy_content=copy_content)
    
    def _dismiss_all_popups(self):
        pass
    
    def _update_status(self, status: str, is_ok: bool):
        self.status_label.configure(text=status)
        color = "#4CAF50" if is_ok else "#F44336"
        self.status_indicator.configure(text_color=color)
    
    def _update_device_status(self, status: str, connected: bool):
        self.device_label.configure(text=status)
        color = "#4CAF50" if connected else ("#666666", "#888888")
        self.device_label.configure(text_color=color)
    
    def _add_message_card(self, message: SMSMessage, scroll_to_top: bool = False, copy_content: str = None):
        for widget in self.scrollable_frame.winfo_children():
            if isinstance(widget, MessageCard):
                current_row = int(widget.grid_info().get('row', 0))
                widget.grid(row=current_row + 1, column=0, sticky="ew", pady=(0, 8))
        
        if copy_content is None:
            copy_content = message.content
        
        card = MessageCard(
            self.scrollable_frame,
            sender=message.sender,
            content=message.content,
            timestamp=message.timestamp,
            on_copy=self._copy_to_clipboard,
            on_delete=self._delete_message,
            copy_content=copy_content
        )
        card.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        
        self.count_label.configure(text=f"{self.message_count} 条消息")
        
        if scroll_to_top:
            self.after(100, lambda: self.scrollable_frame._parent_canvas.yview_moveto(0.0))
    
    def _clear_messages(self):
        for widget in self.scrollable_frame.winfo_children():
            if isinstance(widget, MessageCard):
                widget.destroy()
        
        self.messages = []
        self.message_count = 0
        self.count_label.configure(text="0 条消息")
        
        if self.config.save_messages:
            self.message_storage.clear_all()
        
        self.empty_label = ctk.CTkLabel(
            self.scrollable_frame,
            text="暂无消息\n\n请确保手机和电脑在同一网络下\n然后在手机端点击连接按钮",
            font=ctk.CTkFont(size=13),
            text_color=("#999999", "#666666"),
            justify="center"
        )
        self.empty_label.grid(row=0, column=0, pady=50)
    
    def _delete_message(self, card: MessageCard):
        for msg in self.messages:
            if msg.sender == card.sender and msg.content == card.content and msg.timestamp == card.timestamp:
                if self.config.save_messages:
                    self.message_storage.remove_message(msg)
                    self.messages = self.message_storage.messages
                else:
                    self.messages.remove(msg)
                break
        
        card.destroy()
        
        remaining_cards = [w for w in self.scrollable_frame.winfo_children() 
                          if isinstance(w, MessageCard)]
        self.message_count = len(remaining_cards)
        self.count_label.configure(text=f"{self.message_count} 条消息")
        
        for i, c in enumerate(remaining_cards):
            c.grid(row=i, column=0, sticky="ew", pady=(0, 8))
        
        if self.message_count == 0:
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
        self.server.stop()
        
        if self.tray_icon:
            self.tray_icon.stop()
        
        self.destroy()


def main():
    app = QuickNotificationApp()
    app.mainloop()


if __name__ == "__main__":
    main()

import customtkinter as ctk

from .config import Config


class SMSPopup(ctk.CTkToplevel):
    _instance = None
    
    def __init__(self, master, sender: str, content: str, timestamp: str, 
                 auto_copied: bool = False, on_copy=None, on_dismiss_all=None):
        super().__init__(master)
        
        if SMSPopup._instance and SMSPopup._instance.winfo_exists():
            SMSPopup._instance.destroy()
        
        SMSPopup._instance = self
        
        self.sender = sender
        self.content = content
        self.timestamp = timestamp
        self.on_copy = on_copy
        self.on_dismiss_all = on_dismiss_all
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
        if self.on_dismiss_all:
            self.on_dismiss_all()
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
        self.geometry("360x480")
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
        window_height = 480
        
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
        self.save_messages_var = ctk.BooleanVar(value=self.config.save_messages)
        
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
        
        self._add_setting_row(
            settings_frame, 3,
            "保存短信",
            "保存短信记录（30天循环）",
            self.save_messages_var
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
        self.config.save_messages = self.save_messages_var.get()
        self.config.save()
        
        if self.on_save:
            self.on_save()
        
        self.destroy()
    
    def _on_close(self):
        self.destroy()


class MessageCard(ctk.CTkFrame):
    def __init__(self, master, sender: str, content: str, timestamp: str, 
                 on_copy=None, on_delete=None, **kwargs):
        super().__init__(master, **kwargs)
        
        self.sender = sender
        self.content = content
        self.timestamp = timestamp
        self.on_copy = on_copy
        self.on_delete = on_delete
        
        self.configure(
            fg_color=("#F5F5F5", "#2D2D2D"),
            corner_radius=12,
            border_width=0
        )
        
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=0)
        
        sender_frame = ctk.CTkFrame(self, fg_color="transparent")
        sender_frame.grid(row=0, column=0, sticky="ns", padx=(12, 8), pady=12)
        
        sender_label = ctk.CTkLabel(
            sender_frame,
            text=sender,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=("#1A73E8", "#4DA3FF"),
            width=80,
            anchor="w"
        )
        sender_label.grid(row=0, column=0, sticky="w")
        
        time_label = ctk.CTkLabel(
            sender_frame,
            text=timestamp,
            font=ctk.CTkFont(size=10),
            text_color=("#666666", "#888888"),
            width=80,
            anchor="w"
        )
        time_label.grid(row=1, column=0, sticky="w", pady=(2, 0))
        
        content_label = ctk.CTkLabel(
            self,
            text=content,
            font=ctk.CTkFont(size=13),
            text_color=("#333333", "#E0E0E0"),
            wraplength=280,
            justify="left",
            anchor="w"
        )
        content_label.grid(row=0, column=1, sticky="ew", padx=8, pady=12)
        
        self.button_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.button_frame.grid(row=0, column=2, sticky="ns", padx=(8, 12), pady=12)
        
        self.copy_btn = ctk.CTkButton(
            self.button_frame,
            text="复制",
            font=ctk.CTkFont(size=11),
            fg_color="transparent",
            text_color=("#1A73E8", "#4DA3FF"),
            hover_color=("#E8F0FE", "#1A3A5C"),
            width=50,
            height=24,
            corner_radius=6,
            command=self._on_copy_click
        )
        self.copy_btn.grid(row=0, column=0, pady=(0, 4))
        
        self.delete_btn = ctk.CTkButton(
            self.button_frame,
            text="删除",
            font=ctk.CTkFont(size=11),
            fg_color="transparent",
            text_color=("#E53935", "#FF6B6B"),
            hover_color=("#FFEBEE", "#4A2020"),
            width=50,
            height=24,
            corner_radius=6,
            command=self._on_delete_click
        )
        self.delete_btn.grid(row=1, column=0)
        
        self.button_frame.grid_remove()
        
        self._hide_timer = None
        
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        
        for child in self.winfo_children():
            child.bind("<Enter>", self._on_enter)
            child.bind("<Leave>", self._on_leave)
            if isinstance(child, ctk.CTkFrame):
                for subchild in child.winfo_children():
                    subchild.bind("<Enter>", self._on_enter)
                    subchild.bind("<Leave>", self._on_leave)
    
    def _on_enter(self, event=None):
        if self._hide_timer:
            self.after_cancel(self._hide_timer)
            self._hide_timer = None
        self.button_frame.grid()
    
    def _on_leave(self, event=None):
        if self._hide_timer:
            self.after_cancel(self._hide_timer)
        self._hide_timer = self.after(100, self._do_hide)
    
    def _do_hide(self):
        self.button_frame.grid_remove()
        self._hide_timer = None
    
    def _on_copy_click(self):
        if self.on_copy:
            self.on_copy(self.content)
        else:
            self.clipboard_clear()
            self.clipboard_append(self.content)
        
        self.copy_btn.configure(text="已复制", state="disabled")
        self.after(1000, lambda: self.copy_btn.configure(text="复制", state="normal"))
    
    def _on_delete_click(self):
        if self.on_delete:
            self.on_delete(self)

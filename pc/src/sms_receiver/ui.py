import customtkinter as ctk

from .config import Config


class SMSPopup(ctk.CTkToplevel):
    _instance = None
    
    def __init__(self, master, sender: str, content: str, timestamp: str, 
                 auto_copied: bool = False, on_copy=None, on_dismiss_all=None, copy_content: str = None):
        super().__init__(master)
        
        if SMSPopup._instance and SMSPopup._instance.winfo_exists():
            SMSPopup._instance.destroy()
        
        SMSPopup._instance = self
        
        self.sender = sender
        self.content = content
        self.copy_content = copy_content if copy_content is not None else content
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
        self.clipboard_append(self.copy_content)
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
        
        self.transient(master)
        
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
                 on_copy=None, on_delete=None, copy_content: str = None, **kwargs):
        super().__init__(master, **kwargs)
        
        self.sender = sender
        self.content = content
        self.copy_content = copy_content if copy_content is not None else content
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
            self.on_copy(self.copy_content)
        else:
            self.clipboard_clear()
            self.clipboard_append(self.copy_content)
        
        self.copy_btn.configure(text="已复制", state="disabled")
        self.after(1000, lambda: self.copy_btn.configure(text="复制", state="normal"))
    
    def _on_delete_click(self):
        if self.on_delete:
            self.on_delete(self)


class FilterRuleCard(ctk.CTkFrame):
    def __init__(self, master, rule, on_toggle=None, on_edit=None, on_delete=None, **kwargs):
        super().__init__(master, **kwargs)
        
        self.rule = rule
        self.on_toggle = on_toggle
        self.on_edit = on_edit
        self.on_delete = on_delete
        
        self.configure(
            fg_color=("#F5F5F5", "#2D2D2D"),
            corner_radius=12,
            border_width=0
        )
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        
        info_frame = ctk.CTkFrame(self, fg_color="transparent")
        info_frame.grid(row=0, column=0, sticky="ew", padx=12, pady=12)
        info_frame.grid_columnconfigure(0, weight=1)
        
        name_label = ctk.CTkLabel(
            info_frame,
            text=rule.name,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=("#1A73E8", "#4DA3FF"),
            anchor="w"
        )
        name_label.grid(row=0, column=0, sticky="w")
        
        action_frame = ctk.CTkFrame(self, fg_color="transparent")
        action_frame.grid(row=0, column=1, sticky="ns", padx=(8, 12), pady=12)
        
        self.enabled_switch = ctk.CTkSwitch(
            action_frame,
            text="",
            variable=ctk.BooleanVar(value=rule.enabled),
            width=44,
            switch_width=44,
            switch_height=24,
            corner_radius=12,
            fg_color=("#CCCCCC", "#444444"),
            progress_color=("#1A73E8", "#4DA3FF"),
            button_color=("#FFFFFF", "#FFFFFF"),
            button_hover_color=("#F0F0F0", "#F0F0F0"),
            command=self._on_toggle
        )
        self.enabled_switch.grid(row=0, column=0, pady=(0, 4))
        
        if not rule.is_builtin:
            btn_frame = ctk.CTkFrame(action_frame, fg_color="transparent")
            btn_frame.grid(row=1, column=0)
            
            edit_btn = ctk.CTkButton(
                btn_frame,
                text="编辑",
                font=ctk.CTkFont(size=10),
                fg_color="transparent",
                text_color=("#1A73E8", "#4DA3FF"),
                hover_color=("#E8F0FE", "#1A3A5C"),
                width=40,
                height=20,
                corner_radius=4,
                command=self._on_edit
            )
            edit_btn.grid(row=0, column=0, padx=(0, 2))
            
            delete_btn = ctk.CTkButton(
                btn_frame,
                text="删除",
                font=ctk.CTkFont(size=10),
                fg_color="transparent",
                text_color=("#E53935", "#FF6B6B"),
                hover_color=("#FFEBEE", "#4A2020"),
                width=40,
                height=20,
                corner_radius=4,
                command=self._on_delete_click
            )
            delete_btn.grid(row=0, column=1)
    
    def _on_toggle(self):
        if self.on_toggle:
            self.on_toggle(self.rule, self.enabled_switch.get())
    
    def _on_edit(self):
        if self.on_edit:
            self.on_edit(self.rule)
    
    def _on_delete_click(self):
        if self.on_delete:
            self.on_delete(self.rule)


class AddRuleDialog(ctk.CTkToplevel):
    def __init__(self, master, rule=None, on_save=None):
        super().__init__(master)
        
        self.rule = rule
        self.on_save = on_save
        self.is_edit = rule is not None
        
        self.title("编辑规则" if self.is_edit else "添加规则")
        self.geometry("400x420")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()
        
        self.configure(fg_color=("#FFFFFF", "#1F1F1F"))
        
        self._error_dialog = None
        
        self._setup_ui()
        self._center_window()
        
        self.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def _center_window(self):
        self.update_idletasks()
        
        master_x = self.master.winfo_x()
        master_y = self.master.winfo_y()
        master_width = self.master.winfo_width()
        master_height = self.master.winfo_height()
        
        window_width = 400
        window_height = 420
        
        x = master_x + (master_width - window_width) // 2
        y = master_y + (master_height - window_height) // 2
        
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")
    
    def _setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        
        title_label = ctk.CTkLabel(
            self,
            text="编辑规则" if self.is_edit else "添加规则",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=("#1A1A1A", "#FFFFFF")
        )
        title_label.grid(row=0, column=0, sticky="w", padx=20, pady=(20, 16))
        
        form_frame = ctk.CTkFrame(self, fg_color="transparent")
        form_frame.grid(row=1, column=0, sticky="ew", padx=20)
        form_frame.grid_columnconfigure(0, weight=1)
        
        name_label = ctk.CTkLabel(
            form_frame,
            text="规则名称 *",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=("#1A1A1A", "#FFFFFF"),
            anchor="w"
        )
        name_label.grid(row=0, column=0, sticky="w", pady=(0, 4))
        
        self.name_entry = ctk.CTkEntry(
            form_frame,
            placeholder_text="输入规则名称",
            height=36,
            corner_radius=8
        )
        self.name_entry.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        
        filter_label = ctk.CTkLabel(
            form_frame,
            text="过滤规则 *",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=("#1A1A1A", "#FFFFFF"),
            anchor="w"
        )
        filter_label.grid(row=2, column=0, sticky="w", pady=(0, 4))
        
        filter_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        filter_frame.grid(row=3, column=0, sticky="ew", pady=(0, 12))
        filter_frame.grid_columnconfigure(1, weight=1)
        
        self.filter_type_var = ctk.StringVar(value="keyword")
        filter_type_seg = ctk.CTkSegmentedButton(
            filter_frame,
            values=["keyword", "regex"],
            variable=self.filter_type_var,
            height=36,
            corner_radius=8
        )
        filter_type_seg.grid(row=0, column=0, padx=(0, 8))
        
        self.filter_entry = ctk.CTkEntry(
            filter_frame,
            placeholder_text="输入过滤关键字或正则表达式",
            height=36,
            corner_radius=8
        )
        self.filter_entry.grid(row=0, column=1, sticky="ew")
        
        copy_label = ctk.CTkLabel(
            form_frame,
            text="拷贝规则（可选）",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=("#1A1A1A", "#FFFFFF"),
            anchor="w"
        )
        copy_label.grid(row=4, column=0, sticky="w", pady=(0, 4))
        
        copy_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        copy_frame.grid(row=5, column=0, sticky="ew", pady=(0, 8))
        copy_frame.grid_columnconfigure(1, weight=1)
        
        self.copy_type_var = ctk.StringVar(value="full")
        copy_type_seg = ctk.CTkSegmentedButton(
            copy_frame,
            values=["full", "regex"],
            variable=self.copy_type_var,
            height=36,
            corner_radius=8,
            command=self._on_copy_type_change
        )
        copy_type_seg.grid(row=0, column=0, padx=(0, 8))
        
        self.copy_frame = copy_frame
        self.copy_entry = None
        
        self.copy_hint_label = ctk.CTkLabel(
            copy_frame,
            text="当前模式将拷贝整条消息",
            font=ctk.CTkFont(size=13),
            text_color=("#666666", "#888888"),
            height=36,
            anchor="w"
        )
        
        hint_label = ctk.CTkLabel(
            form_frame,
            text="示例：验证码.*?(\\d{6}) 可从\"验证码是：123456\"中提取\"123456\"",
            font=ctk.CTkFont(size=11),
            text_color=("#666666", "#888888"),
            anchor="w"
        )
        hint_label.grid(row=6, column=0, sticky="w", pady=(0, 12))
        
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=20)
        button_frame.grid_columnconfigure((0, 1), weight=1)
        
        cancel_btn = ctk.CTkButton(
            button_frame,
            text="取消",
            font=ctk.CTkFont(size=14),
            fg_color="transparent",
            text_color=("#666666", "#888888"),
            hover_color=("#EEEEEE", "#333333"),
            height=36,
            corner_radius=8,
            command=self._on_close
        )
        cancel_btn.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        
        save_btn = ctk.CTkButton(
            button_frame,
            text="保存",
            font=ctk.CTkFont(size=14),
            height=36,
            corner_radius=8,
            command=self._on_save
        )
        save_btn.grid(row=0, column=1, sticky="ew", padx=(8, 0))
        
        if self.rule:
            self.name_entry.insert(0, self.rule.name)
            self.filter_entry.insert(0, self.rule.filter_pattern)
            self.filter_type_var.set(self.rule.filter_type)
            copy_type = self.rule.copy_type if self.rule.copy_type in ["full", "regex"] else "full"
            self.copy_type_var.set(copy_type)
            self._update_copy_entry_state()
            if copy_type == "regex" and self.copy_entry:
                self.copy_entry.insert(0, self.rule.copy_pattern)
        else:
            self._update_copy_entry_state()
    
    def _on_copy_type_change(self, value):
        self._update_copy_entry_state()
    
    def _update_copy_entry_state(self):
        if self.copy_type_var.get() == "full":
            if self.copy_entry:
                self.copy_entry.destroy()
                self.copy_entry = None
            self.copy_hint_label.grid(row=0, column=1, sticky="ew")
        else:
            self.copy_hint_label.grid_remove()
            if self.copy_entry:
                self.copy_entry.destroy()
            self.copy_entry = ctk.CTkEntry(
                self.copy_frame,
                placeholder_text="输入正则表达式提取内容",
                height=36,
                corner_radius=8
            )
            self.copy_entry.grid(row=0, column=1, sticky="ew")

    def _on_save(self):
        name = self.name_entry.get().strip()
        filter_pattern = self.filter_entry.get().strip()
        
        if not name:
            self._show_error("请输入规则名称")
            return
        
        if not filter_pattern:
            self._show_error("请输入过滤规则")
            return
        
        copy_type = self.copy_type_var.get()
        copy_pattern = "" if copy_type == "full" else self.copy_entry.get().strip()
        
        if self.on_save:
            self.on_save(
                name=name,
                filter_pattern=filter_pattern,
                filter_type=self.filter_type_var.get(),
                copy_pattern=copy_pattern,
                copy_type=copy_type
            )
        
        self.destroy()
    
    def _show_error(self, message: str):
        if self._error_dialog and self._error_dialog.winfo_exists():
            self._error_dialog.destroy()
        
        self._error_dialog = ctk.CTkToplevel(self)
        self._error_dialog.title("错误")
        self._error_dialog.geometry("300x120")
        self._error_dialog.resizable(False, False)
        self._error_dialog.transient(self)
        self._error_dialog.grab_set()
        self._error_dialog.configure(fg_color=("#FFFFFF", "#1F1F1F"))
        
        self._center_error_dialog()
        
        error_label = ctk.CTkLabel(
            self._error_dialog,
            text=message,
            font=ctk.CTkFont(size=13),
            text_color=("#333333", "#E0E0E0")
        )
        error_label.pack(pady=20)
        
        ok_btn = ctk.CTkButton(
            self._error_dialog,
            text="确定",
            width=80,
            command=self._error_dialog.destroy
        )
        ok_btn.pack()
    
    def _center_error_dialog(self):
        if not self._error_dialog:
            return
        
        self._error_dialog.update_idletasks()
        
        dialog_width = 300
        dialog_height = 120
        
        x = self.winfo_x() + (self.winfo_width() - dialog_width) // 2
        y = self.winfo_y() + (self.winfo_height() - dialog_height) // 2
        
        self._error_dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
    
    def _on_close(self):
        self.destroy()


class FilterWindow(ctk.CTkToplevel):
    def __init__(self, master, filter_settings, on_save=None):
        super().__init__(master)
        
        self.filter_settings = filter_settings
        self.on_save = on_save
        
        self.title("过滤设置")
        self.geometry("360x480")
        self.resizable(False, False)
        
        self.transient(master)
        
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
        self.grid_rowconfigure(2, weight=1)
        
        title_label = ctk.CTkLabel(
            self,
            text="过滤设置",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=("#1A1A1A", "#FFFFFF")
        )
        title_label.grid(row=0, column=0, sticky="w", padx=20, pady=(20, 12))
        
        enable_frame = ctk.CTkFrame(
            self,
            fg_color=("#E8F0FE", "#1E3A5F"),
            corner_radius=12
        )
        enable_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 12))
        enable_frame.grid_columnconfigure(0, weight=1)
        
        enable_text_frame = ctk.CTkFrame(enable_frame, fg_color="transparent")
        enable_text_frame.grid(row=0, column=0, sticky="ew", padx=16, pady=12)
        
        enable_title = ctk.CTkLabel(
            enable_text_frame,
            text="启用过滤",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=("#1A73E8", "#4DA3FF"),
            anchor="w"
        )
        enable_title.grid(row=0, column=0, sticky="w")
        
        enable_desc = ctk.CTkLabel(
            enable_text_frame,
            text="仅显示符合规则的短信",
            font=ctk.CTkFont(size=11),
            text_color=("#666666", "#888888"),
            anchor="w"
        )
        enable_desc.grid(row=1, column=0, sticky="w")
        
        self.filter_enabled_var = ctk.BooleanVar(value=self.filter_settings.filter_enabled)
        enable_switch = ctk.CTkSwitch(
            enable_frame,
            text="",
            variable=self.filter_enabled_var,
            width=44,
            switch_width=44,
            switch_height=24,
            corner_radius=12,
            fg_color=("#CCCCCC", "#444444"),
            progress_color=("#1A73E8", "#4DA3FF"),
            button_color=("#FFFFFF", "#FFFFFF"),
            button_hover_color=("#F0F0F0", "#F0F0F0"),
            command=self._on_toggle_filter
        )
        enable_switch.grid(row=0, column=1, padx=16, pady=12)
        
        rules_frame = ctk.CTkFrame(self, fg_color="transparent")
        rules_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 12))
        rules_frame.grid_columnconfigure(0, weight=1)
        rules_frame.grid_rowconfigure(0, weight=1)
        
        self.scrollable_frame = ctk.CTkScrollableFrame(
            rules_frame,
            fg_color="transparent",
            scrollbar_button_color=("#CCCCCC", "#444444"),
            scrollbar_button_hover_color=("#AAAAAA", "#555555")
        )
        self.scrollable_frame.grid(row=0, column=0, sticky="nsew")
        self.scrollable_frame.grid_columnconfigure(0, weight=1)
        
        self._refresh_rules()
        
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 20))
        button_frame.grid_columnconfigure((0, 1), weight=1)
        
        add_btn = ctk.CTkButton(
            button_frame,
            text="添加规则",
            font=ctk.CTkFont(size=14),
            height=36,
            corner_radius=8,
            command=self._show_add_rule_dialog
        )
        add_btn.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        
        close_btn = ctk.CTkButton(
            button_frame,
            text="关闭",
            font=ctk.CTkFont(size=14),
            fg_color="transparent",
            text_color=("#666666", "#888888"),
            hover_color=("#EEEEEE", "#333333"),
            height=36,
            corner_radius=8,
            command=self._on_close
        )
        close_btn.grid(row=0, column=1, sticky="ew", padx=(8, 0))
    
    def _refresh_rules(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        builtin_label = ctk.CTkLabel(
            self.scrollable_frame,
            text="内嵌规则",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=("#666666", "#888888"),
            anchor="w"
        )
        builtin_label.grid(row=0, column=0, sticky="w", pady=(0, 8))
        
        row = 1
        for rule in self.filter_settings.builtin_rules:
            card = FilterRuleCard(
                self.scrollable_frame,
                rule=rule,
                on_toggle=self._on_toggle_rule
            )
            card.grid(row=row, column=0, sticky="ew", pady=(0, 8))
            row += 1
        
        custom_label = ctk.CTkLabel(
            self.scrollable_frame,
            text="自定义规则",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=("#666666", "#888888"),
            anchor="w"
        )
        custom_label.grid(row=row, column=0, sticky="w", pady=(16, 8))
        row += 1
        
        for rule in self.filter_settings.custom_rules:
            card = FilterRuleCard(
                self.scrollable_frame,
                rule=rule,
                on_toggle=self._on_toggle_rule,
                on_edit=self._on_edit_rule,
                on_delete=self._on_delete_rule
            )
            card.grid(row=row, column=0, sticky="ew", pady=(0, 8))
            row += 1
        
        if not self.filter_settings.custom_rules:
            empty_label = ctk.CTkLabel(
                self.scrollable_frame,
                text="暂无自定义规则",
                font=ctk.CTkFont(size=12),
                text_color=("#999999", "#666666")
            )
            empty_label.grid(row=row, column=0, pady=8)
    
    def _on_toggle_filter(self):
        self.filter_settings.filter_enabled = self.filter_enabled_var.get()
        self.filter_settings.save()
        if self.on_save:
            self.on_save()
    
    def _on_toggle_rule(self, rule, enabled):
        self.filter_settings.toggle_rule(rule.id, enabled)
        if self.on_save:
            self.on_save()
    
    def _show_add_rule_dialog(self):
        self._add_rule_dialog = AddRuleDialog(self, on_save=self._on_add_rule)
    
    def _on_add_rule(self, name, filter_pattern, filter_type, copy_pattern, copy_type):
        from .filter_config import FilterRule
        rule = FilterRule(
            id="",
            name=name,
            description="",
            filter_pattern=filter_pattern,
            filter_type=filter_type,
            copy_pattern=copy_pattern,
            copy_type=copy_type,
            enabled=True,
            is_builtin=False
        )
        self.filter_settings.add_custom_rule(rule)
        self._refresh_rules()
        if self.on_save:
            self.on_save()
    
    def _on_edit_rule(self, rule):
        self._edit_rule_dialog = AddRuleDialog(self, rule=rule, on_save=lambda **kwargs: self._on_update_rule(rule.id, **kwargs))
    
    def _on_update_rule(self, rule_id, name, filter_pattern, filter_type, copy_pattern, copy_type):
        from .filter_config import FilterRule
        rule = FilterRule(
            id=rule_id,
            name=name,
            description="",
            filter_pattern=filter_pattern,
            filter_type=filter_type,
            copy_pattern=copy_pattern,
            copy_type=copy_type,
            enabled=True,
            is_builtin=False
        )
        self.filter_settings.update_custom_rule(rule)
        self._refresh_rules()
        if self.on_save:
            self.on_save()
    
    def _on_delete_rule(self, rule):
        self.filter_settings.delete_custom_rule(rule.id)
        self._refresh_rules()
        if self.on_save:
            self.on_save()
    
    def _on_close(self):
        self.destroy()

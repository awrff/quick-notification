import asyncio
import json
import logging
import socket
import threading
from datetime import datetime
from typing import Optional

import customtkinter as ctk
import websockets
from websockets.exceptions import ConnectionClosed

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


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
        
        self.title("Quick Message")
        self.geometry("500x700")
        self.minsize(400, 500)
        
        if self.winfo_screenwidth() > 1920:
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
        
        self._setup_ui()
        self._start_server()
        
        self.protocol("WM_DELETE_WINDOW", self._on_closing)
    
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
            self.after(0, lambda: self._add_message(sender, content, timestamp))
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析错误: {e}")
    
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
        self.is_running = False
        
        if self.server_loop and self.server_loop.is_running():
            self.server_loop.call_soon_threadsafe(self.server_loop.stop)
        
        self.destroy()


def main():
    app = QuickMessageApp()
    app.mainloop()


if __name__ == "__main__":
    main()

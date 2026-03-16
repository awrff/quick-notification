import asyncio
import json
import logging
import socket
from datetime import datetime
from textual.app import App, ComposeResult
from textual.containers import Container, VerticalScroll
from textual.widgets import Header, Footer, Static, Label
from textual.reactive import reactive
import websockets
from websockets.exceptions import ConnectionClosed

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class SMSMessage(Static):
    def __init__(self, sender: str, content: str, timestamp: str, **kwargs):
        super().__init__(**kwargs)
        self.sender = sender
        self.content = content
        self.timestamp = timestamp

    def compose(self) -> ComposeResult:
        yield Label(f"[{self.timestamp}] 来自: {self.sender}", classes="sms-header")
        yield Label(self.content, classes="sms-content")


class SMSReceiverApp(App):
    CSS = """
    Screen {
        layout: vertical;
    }
    
    .sms-container {
        height: 1fr;
        overflow-y: auto;
    }
    
    SMSMessage {
        margin: 1;
        padding: 1;
        border: solid green;
        background: $surface;
    }
    
    .sms-header {
        color: $primary;
        text-style: bold;
    }
    
    .sms-content {
        color: $text;
        margin-top: 1;
    }
    
    .status-bar {
        dock: bottom;
        height: 3;
        background: $primary;
        color: $text;
        padding: 1;
    }
    """
    
    BINDINGS = [
        ("q", "quit", "退出"),
        ("c", "clear_messages", "清空"),
    ]
    
    message_count = reactive(0)
    status = reactive("等待连接...")
    
    def __init__(self, host: str = "0.0.0.0", port: int = 0):
        super().__init__()
        self.host = host
        self.port = port  # 0表示随机端口
        self.messages_container = None
        self.server = None
        self.pending_messages = []
        self.broadcast_task = None
    
    def compose(self) -> ComposeResult:
        yield Header()
        with Container(classes="sms-container"):
            yield VerticalScroll(id="messages")
        yield Label(f"状态: {self.status} | 消息数: {self.message_count}", classes="status-bar")
        yield Footer()
    
    def on_mount(self) -> None:
        self.messages_container = self.query_one("#messages")
        self.run_worker(self.start_server(), name="server", exclusive=True)
    
    async def start_server(self):
        try:
            async with websockets.serve(
                self.handle_connection,
                self.host,
                self.port,
                ping_interval=20,
                ping_timeout=60
            ) as server:
                self.port = server.sockets[0].getsockname()[1]
                logger.info(f"服务器启动在 ws://{self.host}:{self.port}")
                self.status = f"服务器启动在 ws://{self.host}:{self.port}"
                self._update_status_safe()
                
                # 启动UDP广播
                self.broadcast_task = asyncio.create_task(self.broadcast_port())
                
                await asyncio.Future()
        except Exception as e:
            logger.exception("服务器错误")
            self.status = f"服务器错误: {e}"
            self._update_status_safe()
    
    async def broadcast_port(self):
        """UDP广播端口号"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.settimeout(1)
            
            while True:
                message = f"SMS_FORWARDER_PORT:{self.port}"
                data = message.encode('utf-8')
                sock.sendto(data, ('255.255.255.255', 12345))
                logger.debug(f"广播端口: {self.port}")
                await asyncio.sleep(5)
        except Exception as e:
            logger.error(f"广播失败: {e}")
    
    def _update_status_safe(self):
        try:
            self.query_one(".status-bar").update(f"状态: {self.status} | 消息数: {self.message_count}")
        except Exception as e:
            logger.error(f"更新状态失败: {e}")
    
    async def handle_connection(self, websocket):
        remote = websocket.remote_address
        logger.info(f"新连接: {remote}")
        self.status = f"设备已连接: {remote}"
        self._update_status_safe()
        
        try:
            async for message in websocket:
                logger.debug(f"收到消息: {message}")
                await self.process_message(message)
        except ConnectionClosed as e:
            logger.info(f"连接关闭: {e}")
            self.status = f"设备已断开: {remote}"
            self._update_status_safe()
        except Exception as e:
            logger.exception(f"连接错误: {e}")
            self.status = f"连接错误: {e}"
            self._update_status_safe()
    
    async def process_message(self, message: str):
        try:
            data = json.loads(message)
            sender = data.get("sender", "未知")
            content = data.get("content", "")
            timestamp = data.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            
            self.message_count += 1
            
            sms_widget = SMSMessage(sender, content, timestamp)
            self.pending_messages.append(sms_widget)
            
            self.call_later(self._mount_pending_messages)
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析错误: {e}")
            self.status = "收到无效消息格式"
            self._update_status_safe()
    
    def _mount_pending_messages(self):
        while self.pending_messages:
            widget = self.pending_messages.pop(0)
            self.messages_container.mount(widget)
        self.messages_container.scroll_end(animate=False)
        self._update_status_safe()
    
    def action_clear_messages(self) -> None:
        self.messages_container.remove_children()
        self.message_count = 0
        self._update_status_safe()


def main():
    app = SMSReceiverApp()
    app.run()


if __name__ == "__main__":
    main()
import asyncio
import json
import logging
import socket
import threading
from datetime import datetime
from typing import Optional, Callable

import websockets
from websockets.exceptions import ConnectionClosed

logger = logging.getLogger(__name__)


class SMSServer:
    def __init__(self, on_message: Callable[[str, str, str], None], 
                 on_device_connected: Callable[[str], None],
                 on_device_disconnected: Callable[[], None],
                 on_status_update: Callable[[str, bool], None]):
        self.host = "0.0.0.0"
        self.port: int = 0
        self.server: Optional[websockets.serve] = None
        self.server_loop: Optional[asyncio.AbstractEventLoop] = None
        self.server_thread: Optional[threading.Thread] = None
        self.broadcast_thread: Optional[threading.Thread] = None
        self.is_running = False
        
        self.on_message = on_message
        self.on_device_connected = on_device_connected
        self.on_device_disconnected = on_device_disconnected
        self.on_status_update = on_status_update
    
    def start(self):
        def run_server():
            self.server_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.server_loop)
            
            try:
                self.server_loop.run_until_complete(self._run_server_async())
            except Exception as e:
                logger.exception(f"服务器错误: {e}")
                self.on_status_update(f"服务器错误: {e}", False)
        
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
                self.on_status_update(f"服务器已启动 (端口: {self.port})", True)
                
                self.broadcast_thread = threading.Thread(
                    target=self._broadcast_port, daemon=True
                )
                self.broadcast_thread.start()
                
                await asyncio.Future()
        except Exception as e:
            logger.exception(f"服务器启动失败: {e}")
            self.on_status_update(f"启动失败: {e}", False)
    
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
        
        self.on_device_connected(f"{remote[0]}:{remote[1]}")
        
        try:
            async for message in websocket:
                logger.debug(f"收到消息: {message}")
                await self._process_message(message)
        except ConnectionClosed as e:
            logger.info(f"连接关闭: {e}")
        except Exception as e:
            logger.exception(f"连接错误: {e}")
        finally:
            self.on_device_disconnected()
    
    async def _process_message(self, message: str):
        try:
            data = json.loads(message)
            sender = data.get("sender", "未知")
            content = data.get("content", "")
            timestamp = data.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            
            self.on_message(sender, content, timestamp)
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析错误: {e}")
    
    def stop(self):
        self.is_running = False
        
        if self.server_loop and self.server_loop.is_running():
            self.server_loop.call_soon_threadsafe(self.server_loop.stop)

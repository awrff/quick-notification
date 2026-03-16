import json
import logging
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List
from datetime import datetime

logger = logging.getLogger(__name__)

CONFIG_DIR = Path.home() / ".quick-message"
CONFIG_FILE = CONFIG_DIR / "config.json"
MESSAGES_FILE = CONFIG_DIR / "messages.json"


@dataclass
class SMSMessage:
    sender: str
    content: str
    timestamp: str
    
    def to_dict(self):
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'SMSMessage':
        return cls(
            sender=data.get("sender", "未知"),
            content=data.get("content", ""),
            timestamp=data.get("timestamp", "")
        )


class Config:
    def __init__(self):
        self.minimize_to_tray = False
        self.popup_notification = True
        self.auto_copy = False
        self.save_messages = True
        self.load()
    
    def load(self):
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.minimize_to_tray = data.get('minimize_to_tray', False)
                    self.popup_notification = data.get('popup_notification', True)
                    self.auto_copy = data.get('auto_copy', False)
                    self.save_messages = data.get('save_messages', True)
            except Exception as e:
                logger.error(f"加载配置失败: {e}")
    
    def save(self):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump({
                    'minimize_to_tray': self.minimize_to_tray,
                    'popup_notification': self.popup_notification,
                    'auto_copy': self.auto_copy,
                    'save_messages': self.save_messages
                }, f)
        except Exception as e:
            logger.error(f"保存配置失败: {e}")


class MessageStorage:
    MAX_DAYS = 30
    
    def __init__(self):
        self.messages: List[SMSMessage] = []
    
    def load(self) -> List[SMSMessage]:
        if MESSAGES_FILE.exists():
            try:
                with open(MESSAGES_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.messages = [SMSMessage.from_dict(m) for m in data.get('messages', [])]
                    self._cleanup_old_messages()
                    return self.messages
            except Exception as e:
                logger.error(f"加载消息失败: {e}")
        return []
    
    def save(self):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        try:
            self._cleanup_old_messages()
            with open(MESSAGES_FILE, 'w', encoding='utf-8') as f:
                json.dump({
                    'messages': [m.to_dict() for m in self.messages]
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存消息失败: {e}")
    
    def _cleanup_old_messages(self):
        cutoff = datetime.now()
        from datetime import timedelta
        cutoff_date = cutoff - timedelta(days=self.MAX_DAYS)
        cutoff_str = cutoff_date.strftime("%Y-%m-%d %H:%M:%S")
        
        self.messages = [m for m in self.messages if m.timestamp >= cutoff_str]
    
    def add_message(self, message: SMSMessage):
        self.messages.insert(0, message)
        self.save()
    
    def remove_message(self, message: SMSMessage):
        if message in self.messages:
            self.messages.remove(message)
            self.save()
    
    def clear_all(self):
        self.messages = []
        self.save()

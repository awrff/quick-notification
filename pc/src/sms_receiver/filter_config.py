import json
import logging
import re
import uuid
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)

CONFIG_DIR = Path.home() / ".quick-notification"
FILTER_SETTINGS_FILE = CONFIG_DIR / "filter-rules.json"


class PatternType(Enum):
    KEYWORD = "keyword"
    REGEX = "regex"


@dataclass
class FilterRule:
    id: str
    name: str
    description: str
    filter_pattern: str
    filter_type: str
    copy_pattern: str
    copy_type: str
    enabled: bool
    is_builtin: bool
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'FilterRule':
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            description=data.get("description", ""),
            filter_pattern=data.get("filter_pattern", ""),
            filter_type=data.get("filter_type", "keyword"),
            copy_pattern=data.get("copy_pattern", ""),
            copy_type=data.get("copy_type", "keyword"),
            enabled=data.get("enabled", True),
            is_builtin=data.get("is_builtin", False)
        )


def extract_otp_code(content: str) -> Optional[str]:
    otp_patterns = [
        r'验证码[是为：:\s]*(\d{4,8})',
        r'验证码.*?(\d{4,8})',
        r'动态码[是为：:\s]*(\d{4,8})',
        r'动态密码[是为：:\s]*(\d{4,8})',
        r'安全码[是为：:\s]*(\d{4,8})',
        r'校验码[是为：:\s]*(\d{4,8})',
        r'确认码[是为：:\s]*(\d{4,8})',
        r'code[是为：:\s]*(\d{4,8})',
        r'Code[是为：:\s]*(\d{4,8})',
        r'CODE[是为：:\s]*(\d{4,8})',
        r'(\d{4,8})\s*(?:为|是|作为)?验证码',
        r'(\d{6})',
    ]
    
    for pattern in otp_patterns:
        match = re.search(pattern, content)
        if match:
            code = match.group(1)
            if 4 <= len(code) <= 8:
                return code
    
    return None


def is_otp_message(content: str) -> bool:
    otp_keywords = [
        '验证码', '动态码', '动态密码', '安全码', '校验码', '确认码',
        'code', 'Code', 'CODE', 'OTP', 'otp'
    ]
    
    content_lower = content.lower()
    for keyword in otp_keywords:
        if keyword in content_lower or keyword in content:
            if extract_otp_code(content):
                return True
    
    return False


def create_builtin_otp_rule() -> FilterRule:
    return FilterRule(
        id="builtin-otp-filter",
        name="一次性验证码过滤",
        description="自动检测短信中的一次性验证码，仅显示验证码短信，复制时仅复制验证码",
        filter_pattern="builtin_otp_detect",
        filter_type="regex",
        copy_pattern="builtin_otp_extract",
        copy_type="regex",
        enabled=True,
        is_builtin=True
    )


def get_builtin_rules() -> List[FilterRule]:
    return [create_builtin_otp_rule()]


class FilterSettings:
    def __init__(self):
        self.builtin_rules: List[FilterRule] = get_builtin_rules()
        self.custom_rules: List[FilterRule] = []
        self.filter_enabled: bool = False
        self.load()
    
    def load(self):
        if FILTER_SETTINGS_FILE.exists():
            try:
                with open(FILTER_SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.filter_enabled = data.get('filter_enabled', False)
                    
                    saved_builtin = data.get('builtin_rules', [])
                    builtin_map = {r.id: r for r in self.builtin_rules}
                    for rule_data in saved_builtin:
                        rule = FilterRule.from_dict(rule_data)
                        if rule.id in builtin_map:
                            builtin_map[rule.id].enabled = rule.enabled
                    
                    self.custom_rules = [
                        FilterRule.from_dict(r) for r in data.get('custom_rules', [])
                    ]
                    
            except Exception as e:
                logger.error(f"加载过滤设置失败: {e}")
    
    def save(self):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        try:
            with open(FILTER_SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump({
                    'filter_enabled': self.filter_enabled,
                    'builtin_rules': [r.to_dict() for r in self.builtin_rules],
                    'custom_rules': [r.to_dict() for r in self.custom_rules]
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存过滤设置失败: {e}")
    
    def get_all_enabled_rules(self) -> List[FilterRule]:
        rules = []
        for rule in self.builtin_rules:
            if rule.enabled:
                rules.append(rule)
        for rule in self.custom_rules:
            if rule.enabled:
                rules.append(rule)
        return rules
    
    def add_custom_rule(self, rule: FilterRule):
        if not rule.id:
            rule.id = str(uuid.uuid4())
        rule.is_builtin = False
        self.custom_rules.append(rule)
        self.save()
    
    def update_custom_rule(self, rule: FilterRule):
        for i, r in enumerate(self.custom_rules):
            if r.id == rule.id:
                self.custom_rules[i] = rule
                self.save()
                return
    
    def delete_custom_rule(self, rule_id: str):
        self.custom_rules = [r for r in self.custom_rules if r.id != rule_id]
        self.save()
    
    def toggle_rule(self, rule_id: str, enabled: bool):
        for rule in self.builtin_rules:
            if rule.id == rule_id:
                rule.enabled = enabled
                self.save()
                return
        for rule in self.custom_rules:
            if rule.id == rule_id:
                rule.enabled = enabled
                self.save()
                return


def match_pattern(text: str, pattern: str, pattern_type: str) -> bool:
    if not pattern:
        return True
    
    if pattern_type == "keyword":
        return pattern in text
    elif pattern_type == "regex":
        try:
            return bool(re.search(pattern, text))
        except re.error:
            return False
    return False


def extract_with_pattern(text: str, pattern: str, pattern_type: str) -> str:
    if not pattern:
        return text
    
    if pattern_type == "keyword":
        return pattern
    elif pattern_type == "regex":
        try:
            match = re.search(pattern, text)
            if match:
                if match.groups():
                    return match.group(1)
                return match.group(0)
        except re.error:
            pass
    return text


def apply_filter(content: str, rules: List[FilterRule]) -> Tuple[bool, str]:
    if not rules:
        return True, content
    
    for rule in rules:
        if not rule.enabled:
            continue
        
        if rule.filter_pattern == "builtin_otp_detect":
            if is_otp_message(content):
                if rule.copy_pattern == "builtin_otp_extract":
                    code = extract_otp_code(content)
                    if code:
                        return True, code
                return True, content
            continue
        
        if match_pattern(content, rule.filter_pattern, rule.filter_type):
            copy_content = extract_with_pattern(content, rule.copy_pattern, rule.copy_type)
            return True, copy_content
    
    return False, content

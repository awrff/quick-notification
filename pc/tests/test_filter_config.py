import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sms_receiver.filter_config import (
    extract_otp_code,
    is_otp_message,
    match_pattern,
    extract_with_pattern,
    apply_filter,
    FilterRule,
    FilterSettings,
    create_builtin_otp_rule,
)


class TestExtractOTPCode:
    def test_extract_otp_code_standard_format(self):
        content = "您的验证码是：123456，请勿泄露。"
        assert extract_otp_code(content) == "123456"
    
    def test_extract_otp_code_with_colon(self):
        content = "验证码：654321"
        assert extract_otp_code(content) == "654321"
    
    def test_extract_otp_code_with_space(self):
        content = "验证码 888888"
        assert extract_otp_code(content) == "888888"
    
    def test_extract_otp_code_english_format(self):
        content = "Your code is 123456"
        assert extract_otp_code(content) == "123456"
    
    def test_extract_otp_code_dynamic_password(self):
        content = "动态密码：999999"
        assert extract_otp_code(content) == "999999"
    
    def test_extract_otp_code_security_code(self):
        content = "安全码为 111111"
        assert extract_otp_code(content) == "111111"
    
    def test_extract_otp_code_no_match(self):
        content = "这是一条普通短信"
        assert extract_otp_code(content) is None
    
    def test_extract_otp_code_short_code(self):
        content = "验证码：123"
        result = extract_otp_code(content)
        assert result == "123" or result is None
    
    def test_extract_otp_code_long_code(self):
        content = "验证码：12345678"
        assert extract_otp_code(content) == "12345678"
    
    def test_extract_otp_code_too_long(self):
        content = "验证码：123456789"
        result = extract_otp_code(content)
        assert result is None or len(result) <= 8


class TestIsOTPMessage:
    def test_is_otp_message_true(self):
        content = "您的验证码是：123456，请勿泄露。"
        assert is_otp_message(content) is True
    
    def test_is_otp_message_english(self):
        content = "Your verification code is 654321"
        assert is_otp_message(content) is True
    
    def test_is_otp_message_dynamic_code(self):
        content = "动态码：888888"
        assert is_otp_message(content) is True
    
    def test_is_otp_message_false(self):
        content = "明天下午三点开会"
        assert is_otp_message(content) is False
    
    def test_is_otp_message_no_code(self):
        content = "验证码已发送"
        assert is_otp_message(content) is False
    
    def test_is_otp_message_mixed(self):
        content = "【某银行】您尾号1234的卡消费100元，验证码：666666"
        assert is_otp_message(content) is True


class TestMatchPattern:
    def test_match_pattern_keyword_match(self):
        text = "这是一条测试短信"
        assert match_pattern(text, "测试", "keyword") is True
    
    def test_match_pattern_keyword_no_match(self):
        text = "这是一条测试短信"
        assert match_pattern(text, "验证码", "keyword") is False
    
    def test_match_pattern_regex_match(self):
        text = "验证码：123456"
        assert match_pattern(text, r"验证码[是为：:\s]*(\d{4,8})", "regex") is True
    
    def test_match_pattern_regex_no_match(self):
        text = "这是一条普通短信"
        assert match_pattern(text, r"验证码[是为：:\s]*(\d{4,8})", "regex") is False
    
    def test_match_pattern_empty_pattern(self):
        text = "任意文本"
        assert match_pattern(text, "", "keyword") is True
    
    def test_match_pattern_invalid_regex(self):
        text = "验证码：123456"
        assert match_pattern(text, r"[invalid", "regex") is False


class TestExtractWithPattern:
    def test_extract_with_pattern_regex_with_group(self):
        text = "验证码：123456"
        assert extract_with_pattern(text, r"验证码[是为：:\s]*(\d{4,8})", "regex") == "123456"
    
    def test_extract_with_pattern_regex_no_group(self):
        text = "验证码：123456"
        assert extract_with_pattern(text, r"\d{6}", "regex") == "123456"
    
    def test_extract_with_pattern_empty(self):
        text = "验证码：123456"
        assert extract_with_pattern(text, "", "full") == text
    
    def test_extract_with_pattern_no_match(self):
        text = "普通短信"
        assert extract_with_pattern(text, r"验证码[是为：:\s]*(\d{4,8})", "regex") == text


class TestApplyFilter:
    def test_apply_filter_builtin_otp(self):
        content = "验证码：123456"
        rule = create_builtin_otp_rule()
        rule.enabled = True
        should_show, copy_content = apply_filter(content, [rule])
        assert should_show is True
        assert copy_content == "123456"
    
    def test_apply_filter_builtin_otp_not_match(self):
        content = "明天下午三点开会"
        rule = create_builtin_otp_rule()
        rule.enabled = True
        should_show, copy_content = apply_filter(content, [rule])
        assert should_show is False
    
    def test_apply_filter_custom_keyword(self):
        content = "【银行】您的账户有变动"
        rule = FilterRule(
            id="test-1",
            name="银行短信",
            description="银行相关短信",
            filter_pattern="银行",
            filter_type="keyword",
            copy_pattern="",
            copy_type="full",
            enabled=True,
            is_builtin=False
        )
        should_show, copy_content = apply_filter(content, [rule])
        assert should_show is True
        assert copy_content == content
    
    def test_apply_filter_custom_regex(self):
        content = "订单号：ABC123456 已发货"
        rule = FilterRule(
            id="test-2",
            name="订单号提取",
            description="提取订单号",
            filter_pattern=r"订单号[是为：:\s]*([A-Z0-9]+)",
            filter_type="regex",
            copy_pattern=r"订单号[是为：:\s]*([A-Z0-9]+)",
            copy_type="regex",
            enabled=True,
            is_builtin=False
        )
        should_show, copy_content = apply_filter(content, [rule])
        assert should_show is True
        assert copy_content == "ABC123456"
    
    def test_apply_filter_no_rules(self):
        content = "任意短信"
        should_show, copy_content = apply_filter(content, [])
        assert should_show is True
        assert copy_content == content
    
    def test_apply_filter_disabled_rule(self):
        content = "验证码：123456"
        rule = create_builtin_otp_rule()
        rule.enabled = False
        should_show, copy_content = apply_filter(content, [rule])
        assert should_show is False


class TestFilterRule:
    def test_filter_rule_to_dict(self):
        rule = FilterRule(
            id="test-id",
            name="测试规则",
            description="测试描述",
            filter_pattern="测试",
            filter_type="keyword",
            copy_pattern="",
            copy_type="full",
            enabled=True,
            is_builtin=False
        )
        data = rule.to_dict()
        assert data["id"] == "test-id"
        assert data["name"] == "测试规则"
        assert data["filter_pattern"] == "测试"
    
    def test_filter_rule_from_dict(self):
        data = {
            "id": "test-id",
            "name": "测试规则",
            "description": "测试描述",
            "filter_pattern": "测试",
            "filter_type": "keyword",
            "copy_pattern": "",
            "copy_type": "keyword",
            "enabled": True,
            "is_builtin": False
        }
        rule = FilterRule.from_dict(data)
        assert rule.id == "test-id"
        assert rule.name == "测试规则"
        assert rule.filter_pattern == "测试"


class TestFilterSettings:
    def test_filter_settings_default(self, tmp_path, monkeypatch):
        monkeypatch.setattr("sms_receiver.filter_config.CONFIG_DIR", tmp_path)
        monkeypatch.setattr("sms_receiver.filter_config.FILTER_SETTINGS_FILE", tmp_path / "filter-rules.json")
        
        settings = FilterSettings()
        assert settings.filter_enabled is False
        assert len(settings.builtin_rules) == 1
        assert len(settings.custom_rules) == 0
    
    def test_filter_settings_save_and_load(self, tmp_path, monkeypatch):
        monkeypatch.setattr("sms_receiver.filter_config.CONFIG_DIR", tmp_path)
        monkeypatch.setattr("sms_receiver.filter_config.FILTER_SETTINGS_FILE", tmp_path / "pattern-settings.json")
        
        settings = FilterSettings()
        settings.filter_enabled = True
        settings.builtin_rules[0].enabled = False
        settings.save()
        
        settings2 = FilterSettings()
        assert settings2.filter_enabled is True
        assert settings2.builtin_rules[0].enabled is False
    
    def test_filter_settings_add_custom_rule(self, tmp_path, monkeypatch):
        monkeypatch.setattr("sms_receiver.filter_config.CONFIG_DIR", tmp_path)
        monkeypatch.setattr("sms_receiver.filter_config.FILTER_SETTINGS_FILE", tmp_path / "pattern-settings.json")
        
        settings = FilterSettings()
        rule = FilterRule(
            id="",
            name="自定义规则",
            description="测试",
            filter_pattern="测试",
            filter_type="keyword",
            copy_pattern="",
            copy_type="full",
            enabled=True,
            is_builtin=False
        )
        settings.add_custom_rule(rule)
        
        assert len(settings.custom_rules) == 1
        assert settings.custom_rules[0].name == "自定义规则"
        assert settings.custom_rules[0].id != ""
    
    def test_filter_settings_delete_custom_rule(self, tmp_path, monkeypatch):
        monkeypatch.setattr("sms_receiver.filter_config.CONFIG_DIR", tmp_path)
        monkeypatch.setattr("sms_receiver.filter_config.FILTER_SETTINGS_FILE", tmp_path / "pattern-settings.json")
        
        settings = FilterSettings()
        rule = FilterRule(
            id="test-delete-id",
            name="待删除规则",
            description="测试",
            filter_pattern="测试",
            filter_type="keyword",
            copy_pattern="",
            copy_type="full",
            enabled=True,
            is_builtin=False
        )
        settings.custom_rules.append(rule)
        
        settings.delete_custom_rule("test-delete-id")
        assert len(settings.custom_rules) == 0
    
    def test_filter_settings_toggle_rule(self, tmp_path, monkeypatch):
        monkeypatch.setattr("sms_receiver.filter_config.CONFIG_DIR", tmp_path)
        monkeypatch.setattr("sms_receiver.filter_config.FILTER_SETTINGS_FILE", tmp_path / "pattern-settings.json")
        
        settings = FilterSettings()
        builtin_id = settings.builtin_rules[0].id
        settings.toggle_rule(builtin_id, False)
        
        assert settings.builtin_rules[0].enabled is False
    
    def test_filter_settings_get_all_enabled_rules(self, tmp_path, monkeypatch):
        monkeypatch.setattr("sms_receiver.filter_config.CONFIG_DIR", tmp_path)
        monkeypatch.setattr("sms_receiver.filter_config.FILTER_SETTINGS_FILE", tmp_path / "pattern-settings.json")
        
        settings = FilterSettings()
        settings.builtin_rules[0].enabled = True
        
        rule = FilterRule(
            id="custom-1",
            name="自定义规则",
            description="测试",
            filter_pattern="测试",
            filter_type="keyword",
            copy_pattern="",
            copy_type="full",
            enabled=True,
            is_builtin=False
        )
        settings.custom_rules.append(rule)
        
        enabled_rules = settings.get_all_enabled_rules()
        assert len(enabled_rules) == 2


class TestCreateBuiltinOTPRule:
    def test_create_builtin_otp_rule(self):
        rule = create_builtin_otp_rule()
        assert rule.id == "builtin-otp-filter"
        assert rule.is_builtin is True
        assert rule.enabled is True
        assert "验证码" in rule.name or "OTP" in rule.name.lower() or "一次性" in rule.name

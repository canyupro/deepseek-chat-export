"""
DeepSeek Chat Export 自动化测试脚本
"""

import os
import sys
import json
import argparse
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from deepseek_export import (
    DeepSeekChatExporter,
    ExportConfig,
    ExportFormat,
    ExportResult,
    ChatSession,
    ChatMessage,
    load_env_from_file,
    _safe_filename,
)


class TestRunner:
    """测试运行器"""
    
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests = []
    
    def test(self, name: str):
        """测试装饰器"""
        def decorator(func):
            self.tests.append((name, func))
            return func
        return decorator
    
    def run(self):
        """运行所有测试"""
        print("=" * 60)
        print("DeepSeek Chat Export 自动化测试")
        print("=" * 60)
        print()
        
        for name, func in self.tests:
            try:
                print(f"[测试] {name}...", end=" ")
                func()
                print("✓ 通过")
                self.passed += 1
            except AssertionError as e:
                print(f"✗ 失败: {e}")
                self.failed += 1
            except Exception as e:
                print(f"✗ 错误: {e}")
                self.failed += 1
        
        print()
        print("=" * 60)
        print(f"测试结果: {self.passed} 通过, {self.failed} 失败")
        print("=" * 60)
        
        return self.failed == 0


# 创建测试运行器实例
runner = TestRunner()


@runner.test("加载 .env 文件")
def test_load_env():
    """测试 .env 文件加载"""
    # 创建临时 .env 文件
    env_content = "TEST_VAR=test_value\n# 注释\n\nANOTHER_VAR=another_value\n"
    env_path = Path(".env")
    
    # 备份原文件
    backup = None
    if env_path.exists():
        backup = env_path.read_text(encoding="utf-8")
    
    try:
        env_path.write_text(env_content, encoding="utf-8")
        
        # 清除环境变量
        if "TEST_VAR" in os.environ:
            del os.environ["TEST_VAR"]
        
        # 加载
        load_env_from_file()
        
        # 验证
        assert os.environ.get("TEST_VAR") == "test_value", "TEST_VAR 未正确加载"
        assert os.environ.get("ANOTHER_VAR") == "another_value", "ANOTHER_VAR 未正确加载"
        
    finally:
        # 恢复
        if backup:
            env_path.write_text(backup, encoding="utf-8")
        else:
            env_path.unlink(missing_ok=True)


@runner.test("安全文件名转换")
def test_safe_filename():
    """测试文件名安全转换"""
    test_cases = [
        ("正常标题", "正常标题"),
        ("标题<>:\"/\\|?*测试", "标题_________测试"),
        ("  前后空格  ", "前后空格"),
        ("非常长的标题" * 20, "非常长的标题" * 10 + "非常长的标"),  # 截断
        ("", "untitled"),  # 空字符串
        ("...", "untitled"),  # 只有点号
    ]
    
    for input_name, expected in test_cases:
        result = _safe_filename(input_name, max_length=100)
        assert result == expected or len(result) <= 100, f"转换失败: {input_name} -> {result}"


@runner.test("导出配置创建")
def test_export_config():
    """测试导出配置"""
    config = ExportConfig(
        cookie="test_cookie",
        output_dir="./test_output",
        target_date="2026-05-30",
        format=ExportFormat.JSON,
    )
    
    assert config.cookie == "test_cookie"
    assert config.output_dir == "./test_output"
    assert config.target_date == "2026-05-30"
    assert config.format == ExportFormat.JSON


@runner.test("ChatSession 数据类")
def test_chat_session():
    """测试 ChatSession 数据类"""
    session = ChatSession(
        id="test_id",
        title="测试对话",
        create_time=1234567890,
    )
    
    assert session.id == "test_id"
    assert session.title == "测试对话"
    assert session.create_time == 1234567890
    assert session.messages == []  # 默认空列表


@runner.test("ChatMessage 数据类")
def test_chat_message():
    """测试 ChatMessage 数据类"""
    msg = ChatMessage(
        role="user",
        content="测试消息",
        create_time=1234567890,
    )
    
    assert msg.role == "user"
    assert msg.content == "测试消息"
    assert msg.create_time == 1234567890


@runner.test("Markdown 导出格式")
def test_markdown_export():
    """测试 Markdown 导出"""
    config = ExportConfig(cookie="test")
    exporter = DeepSeekChatExporter(config)
    
    session = ChatSession(
        id="test_id",
        title="测试对话",
        create_time=1234567890000,  # 毫秒时间戳
    )
    session.messages = [
        ChatMessage(role="user", content="你好"),
        ChatMessage(role="assistant", content="你好！有什么可以帮助你？"),
    ]
    
    md_content = exporter.export_to_markdown(session)
    
    assert "# 测试对话" in md_content
    assert "test_id" in md_content
    assert "你好" in md_content
    assert "你好！有什么可以帮助你？" in md_content


@runner.test("JSON 导出格式")
def test_json_export():
    """测试 JSON 导出"""
    config = ExportConfig(cookie="test")
    exporter = DeepSeekChatExporter(config)
    
    session = ChatSession(
        id="test_id",
        title="测试对话",
        create_time=1234567890,
    )
    session.messages = [
        ChatMessage(role="user", content="测试"),
    ]
    
    json_content = exporter.export_to_json(session)
    data = json.loads(json_content)
    
    assert data["id"] == "test_id"
    assert data["title"] == "测试对话"
    assert len(data["messages"]) == 1
    assert data["messages"][0]["role"] == "user"


@runner.test("HTML 导出格式")
def test_html_export():
    """测试 HTML 导出"""
    config = ExportConfig(cookie="test")
    exporter = DeepSeekChatExporter(config)
    
    session = ChatSession(
        id="test_id",
        title="测试对话",
    )
    session.messages = [
        ChatMessage(role="user", content='<script>alert("x")</script> & 测试'),
    ]
    
    html_content = exporter.export_to_html(session)
    
    assert "<!DOCTYPE html>" in html_content
    assert "测试对话" in html_content
    assert "&lt;script&gt;" in html_content
    assert "&amp;" in html_content
    assert "<html>" in html_content


@runner.test("日期解析")
def test_date_parsing():
    """测试日期解析"""
    config = ExportConfig(cookie="test")
    exporter = DeepSeekChatExporter(config)
    
    # 测试毫秒时间戳
    chat_info_ms = {"create_time": 1717036800000}  # 2024-05-30
    date_str = exporter._get_date_from_chat(chat_info_ms)
    assert date_str == "2024-05-30", f"毫秒时间戳解析失败: {date_str}"
    
    # 测试秒时间戳
    chat_info_s = {"create_time": 1717036800}  # 2024-05-30
    date_str = exporter._get_date_from_chat(chat_info_s)
    assert date_str == "2024-05-30", f"秒时间戳解析失败: {date_str}"


@runner.test("时间戳格式化")
def test_timestamp_formatting():
    """测试时间戳格式化"""
    config = ExportConfig(cookie="test")
    exporter = DeepSeekChatExporter(config)
    
    # 毫秒时间戳
    result = exporter._format_timestamp(1717036800000)
    assert "2024-05-30" in result
    
    # 秒时间戳
    result = exporter._format_timestamp(1717036800)
    assert "2024-05-30" in result
    
    # None
    result = exporter._format_timestamp(None)
    assert result == "未知"


@runner.test("导出结果数据类")
def test_export_result():
    """测试导出结果数据类"""
    result = ExportResult(
        success=True,
        date="2026-05-30",
        exported=5,
        files=[{"title": "测试", "filename": "01_测试.md"}],
    )
    
    assert result.success is True
    assert result.date == "2026-05-30"
    assert result.exported == 5
    assert len(result.files) == 1


@runner.test("完整导出流程（模拟）")
def test_full_export_flow():
    """测试完整导出流程"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config = ExportConfig(
            cookie="test_cookie",
            output_dir=tmpdir,
            format=ExportFormat.MARKDOWN,
        )
        exporter = DeepSeekChatExporter(config)
        
        # 模拟对话数据
        chat_info = {
            "id": "test_chat_1",
            "title": "测试对话1",
            "create_time": int(datetime.now().timestamp() * 1000),
        }
        
        # 解析会话
        session = exporter.parse_chat_session(chat_info)
        assert session.id == "test_chat_1"
        assert session.title == "测试对话1"
        
        # 添加消息
        session.messages = [
            ChatMessage(role="user", content="你好"),
            ChatMessage(role="assistant", content="你好！"),
        ]
        
        # 导出
        output_path = Path(tmpdir) / "test.md"
        success = exporter.export_session(session, output_path)
        assert success is True
        assert output_path.exists()
        
        # 验证内容
        content = output_path.read_text(encoding="utf-8")
        assert "测试对话1" in content
        assert "你好" in content


def run_integration_test():
    """运行集成测试（需要真实 Cookie）"""
    print("\n" + "=" * 60)
    print("集成测试（需要真实 Cookie）")
    print("=" * 60)
    
    # 尝试加载 .env
    load_env_from_file()
    
    cookie = os.environ.get("DEEPSEEK_COOKIE", "")
    if not cookie:
        print("\n跳过集成测试: 未设置 DEEPSEEK_COOKIE")
        print("请在 .env 文件中设置 Cookie 以运行集成测试")
        return True
    
    print("\n检测到 Cookie，开始集成测试...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config = ExportConfig(
            cookie=cookie,
            output_dir=tmpdir,
            format=ExportFormat.MARKDOWN,
            request_delay=0.5,
        )
        
        exporter = DeepSeekChatExporter(config)
        
        # 测试认证
        print("\n[测试] 认证检查...", end=" ")
        if not exporter.check_auth():
            print("✗ 失败: Cookie 无效")
            return False
        print("✓ 通过")
        
        # 测试获取对话列表
        print("[测试] 获取对话列表...", end=" ")
        try:
            chats, has_more = exporter.get_chat_list(limit=5)
            print(f"✓ 通过 (获取到 {len(chats)} 条)")
        except Exception as e:
            print(f"✗ 失败: {e}")
            return False
        
        if chats:
            # 测试获取对话详情
            print("[测试] 获取对话详情...", end=" ")
            try:
                chat_id = chats[0]["id"]
                detail = exporter.get_chat_detail(chat_id)
                if detail:
                    print("✓ 通过")
                else:
                    print("⚠ 警告: 未获取到详情")
            except Exception as e:
                print(f"✗ 失败: {e}")
                return False
            
            # 测试导出单个对话
            print("[测试] 导出单个对话...", end=" ")
            try:
                session = exporter.parse_chat_session(chats[0])
                biz_data = detail.get("biz_data", {}) or {}
                messages_data = (
                    biz_data.get("chat_messages", [])
                    or detail.get("chat", {}).get("messages", [])
                )
                session.messages = exporter.parse_messages(messages_data)
                
                output_path = Path(tmpdir) / "test_export.md"
                if exporter.export_session(session, output_path):
                    print("✓ 通过")
                else:
                    print("✗ 失败")
                    return False
            except Exception as e:
                print(f"✗ 失败: {e}")
                return False
    
    print("\n集成测试完成!")
    return True


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="DeepSeek Chat Export 自动化测试"
    )
    parser.add_argument(
        "--run-integration",
        action="store_true",
        help="运行需要真实 Cookie 的联网集成测试"
    )
    args = parser.parse_args()

    # 运行单元测试
    success = runner.run()
    
    # 运行集成测试
    if success and args.run_integration:
        integration_success = run_integration_test()
        success = success and integration_success
    
    # 返回退出码
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

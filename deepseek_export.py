"""
DeepSeek 对话记录自动导出工具
从 chat.deepseek.com 获取每日对话，按日期存储为 Markdown 文件

使用方式:
    python deepseek_export.py [--date YYYY-MM-DD] [--output-dir ./output] [--cookie "your_cookie"]

依赖:
    pip install requests beautifulsoup4

作者: SOLO Skill - deepseek-chat-export
版本: 1.0.0
"""

import os
import re
import json
import time
import argparse
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict
from enum import Enum

try:
    import requests
except ImportError:
    print("[错误] 请先安装 requests: pip install requests")
    raise


def load_env_from_file():
    """
    从 .env 文件加载环境变量
    支持 .env 和 .env.local 文件
    """
    env_files = [".env.local", ".env"]
    loaded = False
    
    for env_file in env_files:
        env_path = Path(env_file)
        if env_path.exists():
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        # 跳过空行和注释
                        if not line or line.startswith("#"):
                            continue
                        # 解析 KEY=VALUE
                        if "=" in line:
                            key, value = line.split("=", 1)
                            key = key.strip()
                            value = value.strip()
                            # 去除引号
                            if (value.startswith('"') and value.endswith('"')) or \
                               (value.startswith("'") and value.endswith("'")):
                                value = value[1:-1]
                            # 只设置未存在的环境变量
                            if key and key not in os.environ:
                                os.environ[key] = value
                loaded = True
                print(f"[INFO] 已加载环境变量: {env_file}")
            except Exception as e:
                print(f"[WARN] 加载 {env_file} 失败: {e}")
    
    return loaded


# 启动时自动加载 .env 文件
load_env_from_file()


# ============================================================
# 配置
# ============================================================
BASE_URL = "https://chat.deepseek.com"
API_BASE = f"{BASE_URL}/api/v0"

# 请求头模板（基于实际抓包数据）
HEADERS_TEMPLATE = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36 Edg/139.0.0.0",
    "Accept": "*/*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Content-Type": "application/json",
    "Origin": BASE_URL,
    "Referer": f"{BASE_URL}/",
    "x-app-version": "2.0.0",
    "x-client-locale": "zh_CN",
    "x-client-platform": "web",
    "x-client-timezone-offset": "28800",
    "x-client-version": "2.0.0",
}

# 文件名安全字符替换映射
UNSAFE_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def _safe_filename(name: str, max_length: int = 80) -> str:
    """
    将标题转换为安全的文件名（模块级函数，便于测试）

    Args:
        name: 原始标题
        max_length: 最大长度

    Returns:
        安全的文件名字符串
    """
    # 替换不安全字符
    safe = UNSAFE_FILENAME_CHARS.sub("_", name.strip())
    # 去除首尾空白和点号
    safe = safe.strip(". ")
    # 截断过长文件名
    if len(safe) > max_length:
        safe = safe[:max_length].rstrip(". ")
    return safe or "untitled"


class ExportFormat(Enum):
    """导出格式枚举"""
    MARKDOWN = "md"
    JSON = "json"
    HTML = "html"


@dataclass
class ExportConfig:
    """导出配置数据类"""
    cookie: str
    bearer_token: str = ""
    output_dir: str = "./deepseek_chats"
    target_date: Optional[str] = None
    export_all: bool = False
    format: ExportFormat = ExportFormat.MARKDOWN
    include_system_prompt: bool = False
    request_delay: float = 0.3
    timeout: int = 20


@dataclass
class ChatMessage:
    """对话消息数据类"""
    role: str
    content: str
    create_time: Optional[int] = None


@dataclass
class ChatSession:
    """对话会话数据类"""
    id: str
    title: str
    create_time: Optional[int] = None
    update_time: Optional[int] = None
    messages: List[ChatMessage] = None
    
    def __post_init__(self):
        if self.messages is None:
            self.messages = []


@dataclass
class ExportResult:
    """导出结果数据类"""
    success: bool
    date: str
    exported: int
    files: List[Dict[str, Any]] = None
    error: Optional[str] = None
    
    def __post_init__(self):
        if self.files is None:
            self.files = []


class DeepSeekAPIError(Exception):
    """DeepSeek API 错误"""
    pass


class AuthenticationError(DeepSeekAPIError):
    """认证错误"""
    pass


class RateLimitError(DeepSeekAPIError):
    """频率限制错误"""
    pass


class DeepSeekChatExporter:
    """DeepSeek 网页端对话导出器"""

    def __init__(self, config: ExportConfig):
        """
        初始化导出器

        Args:
            config: 导出配置对象
        """
        self.config = config
        self.cookie = config.cookie.strip()
        self.bearer_token = config.bearer_token.strip()
        self.output_dir = Path(config.output_dir).resolve()
        self.session = requests.Session()
        self.session.headers.update(HEADERS_TEMPLATE)
        self.session.headers["Cookie"] = self.cookie
        # 设置 Bearer Token（关键认证信息）
        if self.bearer_token:
            self.session.headers["Authorization"] = f"Bearer {self.bearer_token}"
        self.logger = self._setup_logger()
        self._auth_checked = False
        self._user_info = None

    def _setup_logger(self) -> logging.Logger:
        """配置日志"""
        logger = logging.getLogger("DeepSeekExporter")
        logger.setLevel(logging.INFO)
        
        # 清除已有处理器
        logger.handlers.clear()
        
        # 控制台处理器
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s", datefmt="%H:%M:%S")
        )
        logger.addHandler(handler)
        
        return logger

    def _safe_filename(self, name: str, max_length: int = 80) -> str:
        """
        将标题转换为安全的文件名（实例方法，调用模块级函数）

        Args:
            name: 原始标题
            max_length: 最大长度

        Returns:
            安全的文件名字符串
        """
        return _safe_filename(name, max_length)

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        发送 HTTP 请求并处理响应

        Args:
            method: HTTP 方法
            endpoint: API 端点
            **kwargs: 请求参数

        Returns:
            响应数据字典

        Raises:
            DeepSeekAPIError: API 错误
            AuthenticationError: 认证错误
            RateLimitError: 频率限制错误
        """
        url = f"{API_BASE}{endpoint}"
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                timeout=self.config.timeout,
                **kwargs
            )
            
            # 处理 HTTP 错误状态
            if response.status_code == 401:
                raise AuthenticationError("Cookie 无效或已过期")
            elif response.status_code == 429:
                raise RateLimitError("请求过于频繁，请稍后再试")
            elif response.status_code >= 500:
                raise DeepSeekAPIError(f"服务器错误: {response.status_code}")
            elif response.status_code != 200:
                raise DeepSeekAPIError(f"请求失败: {response.status_code}")
            
            # 解析 JSON 响应
            try:
                data = response.json()
            except json.JSONDecodeError as e:
                raise DeepSeekAPIError(f"响应解析失败: {e}")
            
            # 检查业务错误码
            if data.get("code") != 0:
                error_msg = data.get("msg", "未知错误")
                if "unauthorized" in error_msg.lower() or "未登录" in error_msg:
                    raise AuthenticationError(error_msg)
                raise DeepSeekAPIError(f"API 错误: {error_msg}")
            
            return data
            
        except requests.exceptions.Timeout:
            raise DeepSeekAPIError(f"请求超时 ({self.config.timeout}秒)")
        except requests.exceptions.RequestException as e:
            raise DeepSeekAPIError(f"网络请求失败: {e}")

    def check_auth(self) -> bool:
        """
        检查 Cookie 和 Bearer Token 是否有效

        Returns:
            是否认证成功
        """
        if self._auth_checked:
            return True
            
        try:
            # 使用 client/settings 接口验证认证（基于实际抓包）
            data = self._make_request("GET", "/client/settings?scope=model")
            self._user_info = data.get("data", {})
            self.logger.info("认证成功")
            self._auth_checked = True
            return True
        except AuthenticationError as e:
            self.logger.error(f"认证失败: {e}")
            return False
        except DeepSeekAPIError as e:
            self.logger.error(f"认证检查失败: {e}")
            return False

    def get_chat_list(self, offset: int = 0, limit: int = 50, cursor: str = "") -> tuple:
        """
        获取对话列表

        Args:
            offset: 分页偏移量（保留兼容）
            limit: 每页数量
            cursor: 分页游标

        Returns:
            (对话列表, has_more)
        """
        try:
            # 使用真实的 API 路径: /api/v0/chat_session/fetch_page
            if cursor:
                query_string = f"lte_cursor={cursor}"
            else:
                query_string = "lte_cursor.pinned=false"
            
            data = self._make_request("GET", f"/chat_session/fetch_page?{query_string}")
            
            # 解析响应结构: data.biz_data.chat_sessions
            biz_data = data.get("data", {}).get("biz_data", {})
            chats = biz_data.get("chat_sessions", [])
            has_more = biz_data.get("has_more", False)
            
            self.logger.info(f"获取到 {len(chats)} 条对话 (has_more={has_more})")
            return chats, has_more
        except DeepSeekAPIError as e:
            self.logger.error(f"获取对话列表失败: {e}")
            return [], False

    def get_all_chats(self) -> List[Dict[str, Any]]:
        """
        获取所有对话（自动分页，带去重）

        Returns:
            全部对话列表
        """
        all_chats = []
        seen_ids = set()
        cursor = ""
        page_num = 0
        max_pages = 5000  # 安全限制
        same_count = 0    # 连续相同结果计数
        last_count = -1
        
        while page_num < max_pages:
            page_num += 1
            try:
                chats, has_more = self.get_chat_list(cursor=cursor)
                if not chats:
                    break
                
                # 去重：只添加未见过的对话
                new_count = 0
                for chat in chats:
                    chat_id = chat.get("id", "")
                    if chat_id and chat_id not in seen_ids:
                        seen_ids.add(chat_id)
                        all_chats.append(chat)
                        new_count += 1
                
                # 检测是否陷入循环（连续返回相同数量的已见对话）
                if new_count == 0:
                    same_count += 1
                    if same_count >= 3:
                        self.logger.info(f"连续 {same_count} 页无新数据，停止获取")
                        break
                else:
                    same_count = 0
                
                if not has_more:
                    break
                
                # 使用最后一条的 updated_at 作为下一页游标
                last_chat = chats[-1]
                last_time = last_chat.get("updated_at", 0)
                if last_time:
                    cursor = str(last_time)
                else:
                    break
                    
                if page_num % 50 == 0:
                    self.logger.info(f"第 {page_num} 页完成，共 {len(all_chats)} 条唯一对话，继续获取下一页...")
                time.sleep(self.config.request_delay)
            except RateLimitError:
                self.logger.warning("触发频率限制，等待 5 秒后重试...")
                time.sleep(5)
                continue

        self.logger.info(f"共获取到 {len(all_chats)} 条唯一对话（{page_num} 页）")
        return all_chats

    def get_chat_detail(self, chat_id: str) -> Optional[Dict[str, Any]]:
        """
        获取单个对话的详细内容

        Args:
            chat_id: 对话 ID

        Returns:
            对话详情或 None
        """
        try:
            # 使用真实的 API 路径: /api/v0/chat/history_messages
            data = self._make_request(
                "GET",
                f"/chat/history_messages?chat_session_id={chat_id}"
            )
            return data.get("data", {})
        except DeepSeekAPIError as e:
            self.logger.warning(f"获取对话 {chat_id} 详情失败: {e}")
            return None

    def parse_chat_session(self, chat_info: Dict[str, Any]) -> ChatSession:
        """
        解析对话信息为 ChatSession 对象

        Args:
            chat_info: 原始对话信息

        Returns:
            ChatSession 对象
        """
        return ChatSession(
            id=chat_info.get("id", ""),
            title=chat_info.get("title", "无标题对话"),
            create_time=chat_info.get("created_at"),
            update_time=chat_info.get("updated_at"),
        )

    def parse_messages(self, messages_data: List[Dict[str, Any]]) -> List[ChatMessage]:
        """
        解析消息列表（适配 DeepSeek v0 API 的 fragments 结构）

        Args:
            messages_data: 原始消息数据 (chat_messages 列表)

        Returns:
            ChatMessage 列表
        """
        messages = []
        for msg_data in messages_data:
            role = msg_data.get("role", "unknown").lower()
            inserted_at = msg_data.get("inserted_at")
            
            # 从 fragments 中提取内容
            fragments = msg_data.get("fragments", [])
            content_parts = []
            for frag in fragments:
                frag_type = frag.get("type", "")
                frag_content = frag.get("content", "")
                
                if frag_type == "REQUEST" and role == "user":
                    content_parts.append(frag_content)
                elif frag_type == "RESPONSE" and role == "assistant":
                    content_parts.append(frag_content)
                elif frag_type == "THINK" and role == "assistant":
                    # 思考过程，可选是否包含
                    pass  # 跳过思考过程
                elif frag_type == "TOOL_SEARCH":
                    pass  # 跳过搜索工具调用
            
            content = "\n".join(content_parts).strip()
            if content:
                messages.append(ChatMessage(
                    role=role,
                    content=content,
                    create_time=inserted_at,
                ))
        return messages

    def _format_timestamp(self, ts: Optional[int]) -> str:
        """格式化时间戳"""
        if not ts:
            return "未知"
        try:
            if isinstance(ts, (int, float)):
                if ts > 1e12:
                    ts = ts / 1000
                return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
            return str(ts)
        except (ValueError, OSError):
            return str(ts)

    def _format_message_to_markdown(self, message: ChatMessage) -> str:
        """将单条消息转换为 Markdown 格式"""
        role_icons = {
            "user": "👤",
            "assistant": "🤖",
            "system": "⚙️",
        }
        icon = role_icons.get(message.role, "❓")
        
        return f"## {icon} {message.role.capitalize()}\n\n{message.content}\n"

    def export_to_markdown(self, session: ChatSession) -> str:
        """
        将对话导出为 Markdown 格式

        Args:
            session: 对话会话对象

        Returns:
            Markdown 文档字符串
        """
        lines = [
            f"# {session.title}",
            "",
            f"> **对话ID**: `{session.id}`",
            f"> **创建时间**: {self._format_timestamp(session.create_time)}",
            f"> **更新时间**: {self._format_timestamp(session.update_time)}",
            "",
            "---",
            "",
        ]

        for msg in session.messages:
            lines.append(self._format_message_to_markdown(msg))
            lines.append("")

        return "\n".join(lines)

    def export_to_json(self, session: ChatSession) -> str:
        """将对话导出为 JSON 格式"""
        data = {
            "id": session.id,
            "title": session.title,
            "create_time": session.create_time,
            "update_time": session.update_time,
            "messages": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "create_time": msg.create_time,
                }
                for msg in session.messages
            ],
        }
        return json.dumps(data, ensure_ascii=False, indent=2)

    def export_to_html(self, session: ChatSession) -> str:
        """将对话导出为 HTML 格式"""
        html_parts = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            f"<title>{session.title}</title>",
            "<meta charset=\"UTF-8\">",
            "<style>",
            "body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; line-height: 1.6; }",
            ".header { background: #f5f5f5; padding: 15px; border-radius: 8px; margin-bottom: 20px; }",
            ".message { margin: 20px 0; padding: 15px; border-radius: 8px; }",
            ".user { background: #e3f2fd; }",
            ".assistant { background: #f3e5f5; }",
            ".role { font-weight: bold; margin-bottom: 10px; }",
            ".content { white-space: pre-wrap; }",
            "</style>",
            "</head>",
            "<body>",
            f"<h1>{session.title}</h1>",
            "<div class=\"header\">",
            f"<p><strong>对话ID:</strong> {session.id}</p>",
            f"<p><strong>创建时间:</strong> {self._format_timestamp(session.create_time)}</p>",
            f"<p><strong>更新时间:</strong> {self._format_timestamp(session.update_time)}</p>",
            "</div>",
        ]

        for msg in session.messages:
            role_class = "user" if msg.role == "user" else "assistant" if msg.role == "assistant" else "system"
            html_parts.append(f'<div class="message {role_class}">')
            html_parts.append(f'<div class="role">{msg.role.capitalize()}</div>')
            html_parts.append(f'<div class="content">{msg.content}</div>')
            html_parts.append('</div>')

        html_parts.extend(["</body>", "</html>"])
        return "\n".join(html_parts)

    def export_session(self, session: ChatSession, output_path: Path) -> bool:
        """
        导出单个对话到文件

        Args:
            session: 对话会话
            output_path: 输出文件路径

        Returns:
            是否成功
        """
        try:
            if self.config.format == ExportFormat.JSON:
                content = self.export_to_json(session)
            elif self.config.format == ExportFormat.HTML:
                content = self.export_to_html(session)
            else:
                content = self.export_to_markdown(session)

            output_path.write_text(content, encoding="utf-8")
            return True
        except Exception as e:
            self.logger.error(f"导出文件失败 {output_path}: {e}")
            return False

    def _get_date_from_chat(self, chat_info: Dict[str, Any]) -> str:
        """从对话信息中提取日期"""
        update_time = chat_info.get("updated_at") or chat_info.get("create_time") or 0
        try:
            if isinstance(update_time, (int, float)):
                if update_time > 1e12:
                    update_time = update_time / 1000
                return datetime.fromtimestamp(update_time).strftime("%Y-%m-%d")
            return "unknown"
        except (ValueError, OSError):
            return "unknown"

    def export_by_date(self, target_date: Optional[str] = None) -> ExportResult:
        """
        按日期导出对话

        Args:
            target_date: 目标日期 (YYYY-MM-DD)，默认为今天

        Returns:
            导出结果
        """
        # 解析目标日期
        if target_date:
            try:
                target_dt = datetime.strptime(target_date, "%Y-%m-%d")
            except ValueError:
                return ExportResult(
                    success=False,
                    date=target_date,
                    exported=0,
                    error="日期格式错误，请使用 YYYY-MM-DD 格式"
                )
        else:
            target_dt = datetime.now()

        date_str = target_dt.strftime("%Y-%m-%d")
        date_folder = self.output_dir / date_str
        date_folder.mkdir(parents=True, exist_ok=True)

        self.logger.info(f"目标日期: {date_str}，输出目录: {date_folder}")

        # 获取所有对话
        all_chats = self.get_all_chats()
        if not all_chats:
            self.logger.warning("没有获取到任何对话")
            self._generate_date_readme(date_folder, date_str, [])
            return ExportResult(success=True, date=date_str, exported=0)

        # 筛选目标日期的对话
        target_chats = [c for c in all_chats if self._get_date_from_chat(c) == date_str]
        self.logger.info(f"筛选到 {len(target_chats)} 条 {date_str} 的对话")

        if not target_chats:
            self.logger.info(f"{date_str} 没有对话记录")
            self._generate_date_readme(date_folder, date_str, [])
            return ExportResult(success=True, date=date_str, exported=0)

        # 导出每个对话
        exported_files = []
        for idx, chat_info in enumerate(target_chats, 1):
            session = self.parse_chat_session(chat_info)
            self.logger.info(f"[{idx}/{len(target_chats)}] 正在导出: {session.title}")

            # 获取对话详情
            detail = self.get_chat_detail(session.id)
            if not detail:
                self.logger.warning(f"  跳过（无法获取详情）: {session.title}")
                continue

            # 解析消息（适配 v0 API 结构: data.biz_data.chat_messages）
            biz_data = detail.get("biz_data", {})
            messages_data = biz_data.get("chat_messages", [])
            if not messages_data:
                self.logger.warning(f"  跳过（无消息内容）: {session.title}")
                continue

            session.messages = self.parse_messages(messages_data)

            # 生成文件名
            safe_title = self._safe_filename(session.title)
            ext = self.config.format.value
            filename = f"{idx:02d}_{safe_title}.{ext}"
            filepath = date_folder / filename

            # 导出
            if self.export_session(session, filepath):
                exported_files.append({
                    "title": session.title,
                    "filename": filename,
                    "message_count": len(session.messages),
                })
                self.logger.info(f"  已保存: {filename} ({len(session.messages)} 条消息)")
            else:
                self.logger.error(f"  导出失败: {session.title}")

            time.sleep(self.config.request_delay)

        # 生成 README
        self._generate_date_readme(date_folder, date_str, exported_files)

        return ExportResult(
            success=True,
            date=date_str,
            exported=len(exported_files),
            files=exported_files,
        )

    def export_all(self) -> List[ExportResult]:
        """
        导出所有对话（按日期分组）

        Returns:
            导出结果列表
        """
        all_chats = self.get_all_chats()
        if not all_chats:
            self.logger.warning("没有获取到任何对话")
            return []

        # 按日期分组
        date_groups: Dict[str, List[Dict[str, Any]]] = {}
        for chat in all_chats:
            date_str = self._get_date_from_chat(chat)
            if date_str not in date_groups:
                date_groups[date_str] = []
            date_groups[date_str].append(chat)

        # 逐日导出
        results = []
        for date_str in sorted(date_groups.keys(), reverse=True):
            self.config.target_date = date_str
            result = self.export_by_date(date_str)
            results.append(result)
            time.sleep(1)

        # 生成总 README
        self._generate_master_readme(date_groups)

        return results

    def _generate_date_readme(self, date_folder: Path, date_str: str, exported_files: List[Dict[str, Any]]):
        """生成日期文件夹的 README"""
        lines = [
            f"# DeepSeek 对话记录 - {date_str}",
            "",
            f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"对话数量: {len(exported_files)}",
            f"导出格式: {self.config.format.value.upper()}",
            "",
        ]

        if exported_files:
            lines.append("## 对话列表")
            lines.append("")
            lines.append("| 序号 | 标题 | 消息数 | 文件 |")
            lines.append("|------|------|--------|------|")
            for idx, f in enumerate(exported_files, 1):
                lines.append(f"| {idx} | {f['title']} | {f['message_count']} | [{f['filename']}]({f['filename']}) |")
            lines.append("")

        readme_path = date_folder / "README.md"
        readme_path.write_text("\n".join(lines), encoding="utf-8")
        self.logger.info(f"已生成: {readme_path.name}")

    def _generate_master_readme(self, date_groups: Dict[str, List]):
        """生成总 README"""
        total_chats = sum(len(v) for v in date_groups.values())
        
        lines = [
            "# DeepSeek 对话记录汇总",
            "",
            f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"覆盖日期数: {len(date_groups)}",
            f"总对话数: {total_chats}",
            f"导出格式: {self.config.format.value.upper()}",
            "",
            "## 按日期浏览",
            "",
            "| 日期 | 对话数 | 链接 |",
            "|------|--------|------|",
        ]

        for date_str in sorted(date_groups.keys(), reverse=True):
            count = len(date_groups[date_str])
            lines.append(f"| {date_str} | {count} | [{date_str}/]({date_str}/README.md) |")

        lines.extend([
            "",
            "---",
            "",
            "*由 [deepseek_export.py](deepseek_export.py) 自动生成*",
        ])

        readme_path = self.output_dir / "README.md"
        readme_path.write_text("\n".join(lines), encoding="utf-8")
        self.logger.info(f"已生成总 README: {readme_path}")


def get_cookie_from_browser():
    """显示 Cookie 获取帮助"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                  如何获取 DeepSeek Cookie                    ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  1. 打开浏览器，访问 https://chat.deepseek.com               ║
║  2. 确保已登录您的 DeepSeek 账号                              ║
║  3. 按 F12 打开开发者工具                                     ║
║  4. 切换到 "Network" (网络) 标签                              ║
║  5. 刷新页面或进行任意操作                                    ║
║  6. 找到任意一个发往 chat.deepseek.com 的请求                   ║
║  7. 在请求头中找到 "Cookie" 字段                               ║
║  8. 复制完整的 Cookie 值                                      ║
║                                                              ║
║  ⚠️  注意：Cookie 包含您的登录凭据，请勿泄露给他人！            ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
""")


def create_parser() -> argparse.ArgumentParser:
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        description="DeepSeek 对话记录导出工具 v1.0.0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 导出今天的对话（使用 .env 文件）
  python deepseek_export.py

  # 导出指定日期
  python deepseek_export.py --date 2026-05-30

  # 导出所有对话
  python deepseek_export.py --all

  # 导出为 JSON 格式
  python deepseek_export.py --all --format json

  # 指定输出目录
  python deepseek_export.py --all --output-dir ./my_chats

配置方式（优先级从高到低）:
  1. 命令行参数 --cookie / --token
  2. 环境变量 DEEPSEEK_COOKIE / DEEPSEEK_BEARER_TOKEN
  3. .env.local 文件
  4. .env 文件

注意: Bearer Token 是必需的认证信息，请通过 --token 参数或
      DEEPSEEK_BEARER_TOKEN 环境变量 / .env 文件设置。
        """,
    )
    
    parser.add_argument(
        "--cookie", "-c",
        type=str,
        default=None,
        help="chat.deepseek.com 的登录 Cookie",
    )
    parser.add_argument(
        "--token", "-t",
        type=str,
        default=None,
        help="Bearer Token（必需，从请求头 authorization 中获取）",
    )
    parser.add_argument(
        "--date", "-d",
        type=str,
        default=None,
        help="目标日期 (YYYY-MM-DD)，默认为今天",
    )
    parser.add_argument(
        "--all", "-a",
        action="store_true",
        default=False,
        help="导出所有对话（按日期分组）",
    )
    parser.add_argument(
        "--output-dir", "-o",
        type=str,
        default="./deepseek_chats",
        help="输出目录 (默认: ./deepseek_chats)",
    )
    parser.add_argument(
        "--format", "-f",
        type=str,
        choices=["md", "json", "html"],
        default="md",
        help="导出格式: md=Markdown, json=JSON, html=HTML (默认: md)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.3,
        help="请求间隔秒数，避免频率限制 (默认: 0.3)",
    )
    parser.add_argument(
        "--show-cookie-help",
        action="store_true",
        default=False,
        help="显示如何获取 Cookie 的帮助信息",
    )
    parser.add_argument(
        "--version", "-v",
        action="version",
        version="%(prog)s 1.0.0",
        help="显示版本信息",
    )
    
    return parser


def main():
    parser = create_parser()
    args = parser.parse_args()

    if args.show_cookie_help:
        get_cookie_from_browser()
        return

    # 获取 Cookie（优先级：命令行 > 环境变量 > .env）
    cookie = args.cookie or os.environ.get("DEEPSEEK_COOKIE", "")
    if not cookie:
        print("错误: 未提供 Cookie。请通过以下方式之一设置：")
        print("  1. --cookie 命令行参数")
        print("  2. DEEPSEEK_COOKIE 环境变量")
        print("  3. .env 或 .env.local 文件（添加一行：DEEPSEEK_COOKIE=your_cookie_here）")
        print("\n运行 --show-cookie-help 查看如何获取 Cookie。")
        sys.exit(1)

    # 获取 Bearer Token（优先级：命令行 > 环境变量 > .env）
    bearer_token = args.token or os.environ.get("DEEPSEEK_BEARER_TOKEN", "")
    if not bearer_token:
        print("错误: 未提供 Bearer Token。请通过以下方式之一设置：")
        print("  1. --token 命令行参数")
        print("  2. DEEPSEEK_BEARER_TOKEN 环境变量")
        print("  3. .env 或 .env.local 文件（添加一行：DEEPSEEK_BEARER_TOKEN=your_token_here）")
        print("\n获取方法: F12 → Network → 找到请求 → 复制 authorization 头中 Bearer 后面的值")
        sys.exit(1)

    # 创建配置
    config = ExportConfig(
        cookie=cookie,
        bearer_token=bearer_token,
        output_dir=args.output_dir,
        target_date=args.date,
        export_all=args.all,
        format=ExportFormat(args.format),
        request_delay=args.delay,
    )

    # 创建导出器
    exporter = DeepSeekChatExporter(config)

    # 检查认证
    print("=" * 60)
    print("DeepSeek 对话记录导出工具 v1.0.0")
    print("=" * 60)

    if not exporter.check_auth():
        print("\nCookie 无效或已过期，请重新获取。")
        print("运行 --show-cookie-help 查看如何获取 Cookie。")
        sys.exit(1)

    # 执行导出
    try:
        if args.all:
            print("\n开始导出所有对话...\n")
            results = exporter.export_all()
            total_exported = sum(r.exported for r in results)
            result_data = {
                "success": True,
                "total_exported": total_exported,
                "dates": {r.date: r.exported for r in results},
            }
        else:
            print(f"\n开始导出对话...\n")
            result = exporter.export_by_date(target_date=args.date)
            result_data = asdict(result)

        # 输出结果
        print("\n" + "=" * 60)
        print("导出完成!")
        print("=" * 60)
        print(json.dumps(result_data, ensure_ascii=False, indent=2))
        
        # 返回退出码
        sys.exit(0 if result_data.get("success") else 1)
        
    except KeyboardInterrupt:
        print("\n\n操作已取消")
        sys.exit(130)
    except Exception as e:
        print(f"\n导出过程中发生错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

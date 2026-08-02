---
name: "deepseek-chat-export"
description: "从 DeepSeek 网页端自动导出每日对话记录并按日期存储为 Markdown/JSON/HTML 文件。当用户需要导出、备份、归档 DeepSeek 对话记录，或需要按日期整理 AI 对话时调用此 Skill。支持 .env 配置、多格式导出和自动化测试。"
version: "1.0.0"
author: "SOLO"
tags: ["deepseek", "export", "backup", "chat", "automation"]
---

# DeepSeek 对话记录自动导出

## 概述

此 Skill 用于从 chat.deepseek.com 自动获取用户的每日对话记录，并按日期存储为独立的文件。支持 Markdown、JSON、HTML 三种导出格式，每个对话以标题命名，自动生成索引文件。

## 核心脚本

- **主脚本**: `deepseek_export.py` — Python 自动化导出工具
- **安装脚本**: `scripts/install_skill.py` — Skill 安装程序
- **测试脚本**: `tests/test_export.py` — 自动化测试

## 功能特性

- ✅ 自动获取 chat.deepseek.com 的全部对话列表
- ✅ 按日期自动分组存储
- ✅ 支持 Markdown / JSON / HTML 三种导出格式
- ✅ 每个对话保存为独立文件（以对话标题命名）
- ✅ 自动生成每日 README 索引文件
- ✅ 支持导出指定日期或全部对话
- ✅ 自动处理文件名安全字符
- ✅ 支持 .env 文件配置
- ✅ 完整的错误处理和日志记录
- ✅ 自动化测试套件

## 使用前提

1. **Python 3.7+** 已安装
2. 依赖已安装: `pip install -r requirements.txt`
3. 已获取 chat.deepseek.com 的登录 Cookie

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 Cookie

创建 `.env` 文件：

```bash
cp .env.example .env
# 编辑 .env 文件，填入你的 Cookie
DEEPSEEK_COOKIE="your_cookie_here"
```

### 3. 运行导出

```bash
# 导出今天的对话
python deepseek_export.py

# 导出所有对话
python deepseek_export.py --all

# 导出为 JSON 格式
python deepseek_export.py --all --format json
```

## 获取 Cookie 的方法

1. 打开浏览器，访问 https://chat.deepseek.com 并登录
2. 按 `F12` 打开开发者工具 → 切换到 **Network（网络）** 标签
3. 刷新页面，找到任意发往 `chat.deepseek.com` 的请求
4. 复制请求头中的 `Cookie` 字段值

> **安全提示**：Cookie 包含您的登录凭据，请勿泄露给他人！

## Cookie 配置方式（优先级从高到低）

1. **命令行参数** `--cookie`
2. **环境变量** `DEEPSEEK_COOKIE`
3. **.env.local 文件**
4. **.env 文件**

## 命令行参数

| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `--cookie` | `-c` | 登录 Cookie | 从 `.env` 文件或环境变量读取 |
| `--date` | `-d` | 目标日期 (YYYY-MM-DD) | 今天 |
| `--all` | `-a` | 导出所有对话 | 仅导出当天 |
| `--output-dir` | `-o` | 输出目录 | `./deepseek_chats` |
| `--format` | `-f` | 导出格式: md/json/html | `md` |
| `--delay` | - | 请求间隔秒数 | `0.3` |
| `--show-cookie-help` | - | 显示 Cookie 获取帮助 | - |
| `--version` | `-v` | 显示版本信息 | - |

## 输出结构

```
deepseek_chats/
├── README.md                    # 总索引
├── 2026-05-30/                  # 日期文件夹
│   ├── README.md                # 当日索引
│   ├── 01_对话标题1.md
│   ├── 02_对话标题2.md
│   └── 03_对话标题3.md
└── 2026-05-29/
    ├── README.md
    └── ...
```

## 安装到 SOLO/Qclaw

### 自动安装

```bash
python scripts/install_skill.py
```

### 检查安装状态

```bash
python scripts/install_skill.py --check
```

### 卸载

```bash
python scripts/install_skill.py --uninstall
```

## 运行测试

### 运行所有测试

```bash
# 运行本地单元测试
python tests/test_export.py

# 需要真实 Cookie 时，显式运行联网集成测试
python tests/test_export.py --run-integration
```

### 测试内容

- `.env` 文件加载
- 文件名安全转换
- 数据类创建
- Markdown / JSON / HTML 导出格式
- 日期解析和时间戳格式化
- 完整导出流程
- 集成测试（需要真实 Cookie）

## Qclaw 自动化操作指南

当 Qclaw 需要执行此任务时，按以下步骤操作：

### 步骤 1：确认环境

```bash
# 检查 Python 是否可用
python --version

# 检查依赖是否已安装
pip show requests
```

如果缺少依赖，执行：
```bash
pip install -r requirements.txt
```

### 步骤 2：配置 .env 文件

```bash
# 创建 .env 文件
cp .env.example .env

# 编辑 .env 文件，填入用户提供的 Cookie
# DEEPSEEK_COOKIE="用户提供的Cookie值"
```

### 步骤 3：执行导出

```bash
# 导出今天
python deepseek_export.py --output-dir "d:\warehouse\deepseek\deepseek-chat-export\output"

# 或导出所有
python deepseek_export.py --all --output-dir "d:\warehouse\deepseek\deepseek-chat-export\output"

# 或导出为 JSON
python deepseek_export.py --all --format json --output-dir "d:\warehouse\deepseek\deepseek-chat-export\output"
```

### 步骤 4：验证结果

```bash
# 查看导出的文件
ls "d:\warehouse\deepseek\deepseek-chat-export\output"

# 运行测试验证
python tests/test_export.py
```

## API 参考

### DeepSeekChatExporter 类

```python
from deepseek_export import DeepSeekChatExporter, ExportConfig, ExportFormat

config = ExportConfig(
    cookie="your_cookie",
    output_dir="./output",
    format=ExportFormat.MARKDOWN,
)

exporter = DeepSeekChatExporter(config)

# 检查认证
if exporter.check_auth():
    # 导出今天
    result = exporter.export_by_date()
    
    # 导出所有
    results = exporter.export_all()
```

### 数据类

- `ExportConfig` - 导出配置
- `ChatSession` - 对话会话
- `ChatMessage` - 对话消息
- `ExportResult` - 导出结果

## 注意事项

- **Cookie 过期**：Cookie 可能会过期，需要定期更新。如果脚本提示认证失败，请重新获取 Cookie。
- **请求频率**：脚本内置了请求间隔（默认 0.3 秒），避免触发频率限制。可通过 `--delay` 参数调整。
- **隐私安全**：Cookie 是敏感信息，建议使用 `.env` 文件或环境变量传递，不要硬编码在脚本中。
- **网络要求**：需要能正常访问 chat.deepseek.com。

## 故障排除

### Cookie 无效

- 重新获取 Cookie
- 检查 Cookie 是否完整（包含所有字段）
- 确认账号未过期

### 导出失败

- 检查网络连接
- 增加请求间隔：`--delay 1.0`
- 查看日志输出

### 缺少依赖

```bash
pip install -r requirements.txt
```

## 更新日志

### v1.0.0
- 初始版本发布
- 支持 Markdown / JSON / HTML 导出
- 支持 .env 文件配置
- 完整的错误处理
- 自动化测试套件

## 许可证

MIT License

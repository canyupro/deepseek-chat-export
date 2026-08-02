# DeepSeek 对话记录自动导出工具

从 chat.deepseek.com 自动获取每日对话记录，按日期存储为 Markdown 文件。

## 功能特性

- 自动获取 chat.deepseek.com 的全部对话列表
- 按日期自动分组存储
- 每个对话保存为独立的 `.md` 文件（以对话标题命名）
- 自动生成每日 README 索引文件
- 支持导出指定日期或全部对话
- 自动处理文件名安全字符

## 目录结构

导出后的目录结构如下：

```
deepseek_chats/
├── README.md                    # 总索引（所有日期汇总）
├── 2026-05-30/                  # 按日期分组的文件夹
│   ├── README.md                # 当日对话索引
│   ├── 01_Python爬虫开发.md     # 对话1
│   ├── 02_API接口调试.md        # 对话2
│   └── 03_数据分析讨论.md       # 对话3
├── 2026-05-29/
│   ├── README.md
│   ├── 01_机器学习入门.md
│   └── 02_代码审查.md
└── ...
```

## 快速开始

### 1. 安装依赖

```bash
pip install requests beautifulsoup4 python-dotenv
```

### 2. 获取 Cookie

1. 打开浏览器，访问 https://chat.deepseek.com
2. 确保已登录您的 DeepSeek 账号
3. 按 `F12` 打开开发者工具
4. 切换到 **Network（网络）** 标签
5. 刷新页面
6. 找到任意发往 `chat.deepseek.com` 的请求
7. 在请求头中找到 `Cookie` 字段，复制完整值

> **安全提示**：Cookie 包含您的登录凭据，请勿泄露给他人！

### 3. 配置 Cookie（三种方式）

#### 方式一：使用 .env 文件（推荐）

```bash
# 复制示例文件
cp .env.example .env

# 编辑 .env 文件，填入你的 Cookie
# DEEPSEEK_COOKIE="your_cookie_here"
```

#### 方式二：使用环境变量

```bash
# Windows PowerShell
$env:DEEPSEEK_COOKIE = "your_cookie_here"

# Linux / macOS
export DEEPSEEK_COOKIE="your_cookie_here"
```

#### 方式三：命令行参数

```bash
python deepseek_export.py --cookie "your_cookie_here"
```

### 4. 运行脚本

#### 导出今天的对话

```bash
python deepseek_export.py --cookie "your_cookie_here"
```

#### 导出指定日期的对话

```bash
python deepseek_export.py --date 2026-05-30 --cookie "your_cookie_here"
```

#### 导出所有对话

```bash
python deepseek_export.py --all --cookie "your_cookie_here"
```

#### 指定输出目录

```bash
python deepseek_export.py --output-dir ./my_chats --cookie "your_cookie_here"
```

#### 使用 .env 文件（推荐用于自动化）

```bash
# 配置好 .env 文件后，直接运行
python deepseek_export.py --all

# 或导出指定日期
python deepseek_export.py --date 2026-05-30
```

## 命令行参数

| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `--cookie` | `-c` | 登录 Cookie 字符串 | 从 `.env` 文件或 `DEEPSEEK_COOKIE` 环境变量读取 |
| `--date` | `-d` | 目标日期 (YYYY-MM-DD) | 今天 |
| `--all` | `-a` | 导出所有对话 | 仅导出当天 |
| `--output-dir` | `-o` | 输出目录 | `./deepseek_chats` |
| `--show-cookie-help` | - | 显示 Cookie 获取帮助 | - |

## 自动化配置

### 定时任务（Windows 任务计划程序）

每天自动导出当天对话：

```powershell
# 创建定时执行脚本 (auto_export.ps1)
$env:DEEPSEEK_COOKIE = "your_cookie_here"
python deepseek_export.py --date (Get-Date -Format "yyyy-MM-dd") --output-dir "D:\deepseek_chats"
```

### 定时任务（Linux crontab）

```bash
# 每天晚上 23:00 自动导出
0 23 * * * DEEPSEEK_COOKIE="your_cookie" /usr/bin/python3 /path/to/deepseek_export.py --output-dir /path/to/deepseek_chats
```

## 注意事项

1. **Cookie 有效期**：Cookie 可能会过期，需要定期更新。如果脚本提示认证失败，请重新获取 Cookie。
2. **请求频率**：脚本内置了请求间隔（0.3-1秒），避免触发频率限制。
3. **隐私安全**：Cookie 包含敏感信息，建议使用环境变量而非命令行参数传递。
4. **网络环境**：需要能够正常访问 chat.deepseek.com。

## 技术说明

- **数据来源**：通过 chat.deepseek.com 网页端内部 API 获取对话数据
- **认证方式**：使用浏览器 Cookie 进行身份验证
- **输出格式**：标准 Markdown 格式，兼容所有 Markdown 编辑器
- **Python 版本**：需要 Python 3.7+

## 依赖

- `requests` - HTTP 请求库
- `beautifulsoup4` - HTML 解析库（备用）
- `python-dotenv` - .env 文件支持（可选，脚本内置基础支持）

## 许可证

MIT License

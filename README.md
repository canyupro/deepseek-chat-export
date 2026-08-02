# DeepSeek Chat Export / DeepSeek 对话导出工具

> Export DeepSeek web conversations as Markdown, JSON, or HTML by date.
> 自动导出 DeepSeek 网页对话，并按日期保存为 Markdown、JSON 或 HTML 文件。

## English

DeepSeek Chat Export fetches conversation history from `chat.deepseek.com`, groups it by date, and saves every conversation as an independent file. It also generates daily index files so the exported archive is easy to browse.

### Features

- Export today, a specific date, or all conversations
- Markdown, JSON, and HTML output formats
- Automatic daily `README.md` index
- Safe filename handling for conversation titles
- `.env` configuration support
- Request delay to reduce API pressure
- Local unit tests; optional integration tests with real credentials

### Install

```bash
pip install -r requirements.txt
cp .env.example .env
```

### Get Credentials

1. Open `https://chat.deepseek.com` in a browser and sign in.
2. Press `F12` and open the Network tab.
3. Reload the page and select any request sent to `chat.deepseek.com`.
4. Copy the `Cookie` header value and the `authorization` token after `Bearer `.

Keep credentials in `.env` or environment variables:

```bash
DEEPSEEK_COOKIE="your_cookie_here"
DEEPSEEK_BEARER_TOKEN="your_token_here"
```

### Usage

```bash
# Export today
python deepseek_export.py

# Export one date
python deepseek_export.py --date 2026-05-30

# Export all conversations
python deepseek_export.py --all

# Export as JSON
python deepseek_export.py --all --format json

# Custom output directory
python deepseek_export.py --output-dir ./my_chats
```

### CLI Options

| Option | Short | Description | Default |
|---|---|---|---|
| `--cookie` | `-c` | Login Cookie | `.env` or `DEEPSEEK_COOKIE` |
| `--token` | `-t` | Bearer token | `.env` or `DEEPSEEK_BEARER_TOKEN` |
| `--date` | `-d` | Target date `YYYY-MM-DD` | today |
| `--all` | `-a` | Export all conversations | current date only |
| `--output-dir` | `-o` | Output directory | `./deepseek_chats` |
| `--format` | `-f` | `md`, `json`, or `html` | `md` |
| `--delay` | - | Request interval in seconds | `0.3` |
| `--show-cookie-help` | - | Show Cookie help | - |
| `--version` | `-v` | Show version | - |

### Tests

```bash
# Local unit tests
python tests/test_export.py

# Integration tests with a real account
python tests/test_export.py --run-integration
```

### Notes

- Cookies expire; refresh them when authentication fails.
- The tool uses the non-official web API. Keep request frequency low.
- Credentials are sensitive. Prefer `.env` or environment variables over command-line arguments.
- Python 3.7+ and `requests` are required.

### License

MIT License.

---

## 中文

DeepSeek Chat Export 是一个自动导出工具，从 `chat.deepseek.com` 获取对话历史，按日期分组，并将每条对话保存为独立文件。它还会生成每日索引文件，方便后续浏览和归档。

### 功能特性

- 导出今天、指定日期或全部对话
- 支持 Markdown、JSON、HTML 三种格式
- 自动生成每日 `README.md` 索引
- 对话标题自动处理为安全文件名
- 支持 `.env` 配置
- 内置请求间隔，降低接口压力
- 默认本地单元测试，可显式运行联网集成测试

### 安装依赖

```bash
pip install -r requirements.txt
cp .env.example .env
```

### 获取认证信息

1. 打开浏览器访问 `https://chat.deepseek.com` 并登录
2. 按 `F12` 打开开发者工具，切换到 Network 标签
3. 刷新页面，选择任意发往 `chat.deepseek.com` 的请求
4. 复制请求头中的 `Cookie`，以及 `authorization` 中 `Bearer ` 后面的 Token

将凭证写入 `.env`：

```bash
DEEPSEEK_COOKIE="your_cookie_here"
DEEPSEEK_BEARER_TOKEN="your_token_here"
```

### 使用方法

```bash
# 导出今天的对话
python deepseek_export.py

# 导出指定日期
python deepseek_export.py --date 2026-05-30

# 导出全部对话
python deepseek_export.py --all

# 导出为 JSON
python deepseek_export.py --all --format json

# 指定输出目录
python deepseek_export.py --output-dir ./my_chats
```

### 命令行参数

| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `--cookie` | `-c` | 登录 Cookie | `.env` 或 `DEEPSEEK_COOKIE` |
| `--token` | `-t` | Bearer Token | `.env` 或 `DEEPSEEK_BEARER_TOKEN` |
| `--date` | `-d` | 目标日期 `YYYY-MM-DD` | 今天 |
| `--all` | `-a` | 导出全部对话 | 仅当天 |
| `--output-dir` | `-o` | 输出目录 | `./deepseek_chats` |
| `--format` | `-f` | `md`、`json` 或 `html` | `md` |
| `--delay` | - | 请求间隔秒数 | `0.3` |
| `--show-cookie-help` | - | 显示 Cookie 获取帮助 | - |
| `--version` | `-v` | 显示版本 | - |

### 运行测试

```bash
# 默认只运行本地单元测试
python tests/test_export.py

# 使用真实账号运行联网集成测试
python tests/test_export.py --run-integration
```

### 注意事项

- Cookie 会过期，认证失败时重新获取
- 工具使用非官方网页接口，请控制请求频率
- 凭证属于敏感信息，建议使用 `.env` 或环境变量，不要写在命令行里
- 需要 Python 3.7+ 和 `requests`

### 许可证

MIT License。

# DeepSeek 对话手动导出指南

由于 Cookie 认证失败，以下是替代方案：

## 方案一：使用浏览器扩展（推荐）

1. 安装 **DeepSeek Chat Exporter** 浏览器扩展
   - Chrome 商店搜索 "DeepSeek Chat Exporter"
   - 或访问：https://chromewebstore.google.com/detail/deepseek-chat-exporter

2. 在 chat.deepseek.com 页面点击扩展图标
3. 选择导出格式（Markdown/JSON/HTML）
4. 保存文件

## 方案二：手动复制（简单）

1. 打开 https://chat.deepseek.com
2. 进入需要导出的对话
3. 逐条复制对话内容
4. 粘贴到 Markdown 文件中

## 方案三：使用 Playwright 自动化

我已为您准备了一个浏览器自动化脚本：

```bash
# 安装依赖
pip install playwright
playwright install chromium

# 运行自动化脚本（需要您手动登录一次）
python export_with_browser.py
```

## 方案四：更新 Cookie

您的 Cookie 可能已过期，请重新获取：

1. 打开 https://chat.deepseek.com 并登录
2. 按 F12 → Network 标签
3. 刷新页面
4. 找到任意请求，复制最新的 Cookie
5. 更新 .env 文件

---

**注意**：由于 DeepSeek 的安全机制，API 方式的 Cookie 有效期很短。建议：
- 使用浏览器扩展（最稳定）
- 或定期更新 Cookie

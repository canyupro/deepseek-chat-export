"""检查 fetch_page 返回的完整结构以找到分页游标"""
import requests
import os
import json
from pathlib import Path

for line in Path('.env').read_text(encoding='utf-8').splitlines():
    line = line.strip()
    if line and not line.startswith('#') and '=' in line:
        k, v = line.split('=', 1)
        k, v = k.strip(), v.strip()
        if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
            v = v[1:-1]
        os.environ.setdefault(k, v)

cookie = os.environ['DEEPSEEK_COOKIE']
token = os.environ['DEEPSEEK_BEARER_TOKEN']

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36 Edg/139.0.0.0',
    'Accept': '*/*',
    'Authorization': f'Bearer {token}',
    'Cookie': cookie,
    'Origin': 'https://chat.deepseek.com',
    'Referer': 'https://chat.deepseek.com/',
    'x-app-version': '2.0.0',
    'x-client-locale': 'zh_CN',
    'x-client-platform': 'web',
    'x-client-timezone-offset': '28800',
    'x-client-version': '2.0.0',
}

session = requests.Session()
session.headers.update(headers)

# 获取第一页
r = session.get('https://chat.deepseek.com/api/v0/chat_session/fetch_page?lte_cursor.pinned=false', timeout=15)
data = r.json()
biz_data = data.get("data", {}).get("biz_data", {})

# 打印 biz_data 的所有 key
print("biz_data keys:", list(biz_data.keys()))
print()

# 打印 chat_sessions 的最后一条
sessions = biz_data.get("chat_sessions", [])
if sessions:
    last = sessions[-1]
    print(f"Total sessions: {len(sessions)}")
    print(f"Last session updated_at: {last.get('updated_at')}")
    print(f"Last session id: {last.get('id')}")
    print()

# 检查是否有 cursor 相关字段
for key in biz_data:
    if 'cursor' in key.lower() or 'page' in key.lower() or 'next' in key.lower() or 'has' in key.lower():
        print(f"  {key}: {biz_data[key]}")

# 打印完整 biz_data 结构（排除 chat_sessions）
print("\nbiz_data structure (excluding chat_sessions):")
for key, val in biz_data.items():
    if key != 'chat_sessions':
        print(f"  {key}: {val}")

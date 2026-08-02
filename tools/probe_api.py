"""探测 DeepSeek chat API - 扩大范围"""
import requests
import os
import json
from pathlib import Path

# 加载 .env
for line in Path('.env').read_text(encoding='utf-8').splitlines():
    line = line.strip()
    if line and not line.startswith('#') and '=' in line:
        k, v = line.split('=', 1)
        k = k.strip()
        v = v.strip()
        if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
            v = v[1:-1]
        os.environ.setdefault(k, v)

cookie = os.environ['DEEPSEEK_COOKIE']
token = os.environ['DEEPSEEK_BEARER_TOKEN']

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36 Edg/139.0.0.0',
    'Accept': '*/*',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br, zstd',
    'Authorization': f'Bearer {token}',
    'Cookie': cookie,
    'Content-Type': 'application/json',
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

# 先测试哪些 v0 路径返回 JSON
print("=== 探测所有 v0 API 路径 ===")
v0_paths = [
    ('GET', '/api/v0/client/settings?scope=model'),
    ('GET', '/api/v0/client/settings'),
    ('GET', '/api/v0/client/user'),
    ('GET', '/api/v0/user'),
    ('GET', '/api/v0/user/info'),
    ('GET', '/api/v0/user/profile'),
    ('POST', '/api/v0/chat/list'),
    ('POST', '/api/v0/chat/list', {'offset': 0, 'limit': 20, 'category': 'all', 'is_new': True}),
    ('POST', '/api/v0/chat/list', {'offset': 0, 'limit': 20, 'is_new': True}),
    ('POST', '/api/v0/chat/list', {'offset': 0, 'limit': 20, 'cursor': None}),
    ('POST', '/api/v0/chat/list', {'aff': '0'}),
    ('POST', '/api/v0/chat/list', {'by': 'create_time', 'order': 'desc', 'offset': 0, 'limit': 20}),
    ('GET', '/api/v0/chat'),
    ('POST', '/api/v0/chat'),
    ('GET', '/api/v0/conversations'),
    ('POST', '/api/v0/conversations'),
    ('GET', '/api/v0/conversations/list'),
    ('POST', '/api/v0/conversations/list'),
    ('GET', '/api/v0/message/list'),
    ('POST', '/api/v0/message/list'),
]

for item in v0_paths:
    method = item[0]
    path = item[1]
    body = item[2] if len(item) > 2 else None
    url = f'https://chat.deepseek.com{path}'
    try:
        if method == 'GET':
            r = session.get(url, timeout=10)
        else:
            r = session.post(url, json=body, timeout=10)
        
        ct = r.headers.get('content-type', '')
        is_json = 'json' in ct
        
        if is_json:
            try:
                data = r.json()
                keys = list(data.keys()) if isinstance(data, dict) else type(data).__name__
                print(f'  ✓ {method} {path} -> JSON [{keys}]')
                if data.get('code') == 0 and data.get('data'):
                    print(f'    DATA: {json.dumps(data, ensure_ascii=False)[:300]}')
            except:
                print(f'  ~ {method} {path} -> JSON parse err')
    except Exception as e:
        pass  # 静默跳过错误

print()
print("=== 探测非 v0 路径 ===")
other_paths = [
    ('POST', '/api/chat/list', {'offset': 0, 'limit': 20}),
    ('POST', '/api/chat/session/list', {}),
    ('POST', '/api/chat/session/list', {'offset': 0, 'limit': 20}),
    ('GET', '/api/chat/session/list'),
    ('POST', '/api/v1/chat/list', {'offset': 0, 'limit': 20}),
    ('POST', '/api/v1/chat/sessions', {}),
    ('POST', '/api/v2/chat/list', {'offset': 0, 'limit': 20}),
    ('GET', '/api/v0/client/chat/list'),
    ('POST', '/api/v0/client/chat/list', {'offset': 0, 'limit': 20}),
]

for item in other_paths:
    method = item[0]
    path = item[1]
    body = item[2] if len(item) > 2 else None
    url = f'https://chat.deepseek.com{path}'
    try:
        if method == 'GET':
            r = session.get(url, timeout=10)
        else:
            r = session.post(url, json=body, timeout=10)
        
        ct = r.headers.get('content-type', '')
        is_json = 'json' in ct
        
        if is_json:
            try:
                data = r.json()
                keys = list(data.keys()) if isinstance(data, dict) else type(data).__name__
                print(f'  ✓ {method} {path} -> JSON [{keys}]')
                if data.get('code') == 0 and data.get('data'):
                    print(f'    DATA: {json.dumps(data, ensure_ascii=False)[:300]}')
            except:
                print(f'  ~ {method} {path} -> JSON parse err')
    except Exception as e:
        pass

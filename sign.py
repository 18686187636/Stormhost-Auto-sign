#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import asyncio
import time
import base64
from urllib.parse import urlparse
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.network.connection.tcpabridged import ConnectionTcpAbridged

# 读取环境变量
API_ID = int(os.environ.get('TG_API_ID', '0').strip())
API_HASH = os.environ.get('TG_API_HASH', '').strip()
SESSION_B64 = os.environ.get('TG_SESSION_STRING_B64', '').strip()
PROXY_SERVER = os.environ.get('PROXY_SERVER', '').strip()  # 如 http://127.0.0.1:1081

if not all([API_ID, API_HASH, SESSION_B64]):
    print("❌ 缺少必要的环境变量，退出。")
    sys.exit(1)

print(f"API_ID 长度: {len(str(API_ID))}, API_HASH 长度: {len(API_HASH)}, SESSION_B64 长度: {len(SESSION_B64)}")

# 解码 Base64 得到原始 SESSION_STRING
try:
    session_str = base64.b64decode(SESSION_B64).decode()
except Exception as e:
    print(f"❌ Base64 解码失败: {e}")
    sys.exit(1)

print(f"解码后 SESSION_STRING 长度: {len(session_str)} 字符")
if len(session_str) < 50:
    print("⚠️ SESSION_STRING 过短，可能无效")
    sys.exit(1)

# 解析代理（支持 http 和 socks5）
proxy = None
if PROXY_SERVER:
    parsed = urlparse(PROXY_SERVER)
    if parsed.scheme in ('http', 'https'):
        proxy = ('http', parsed.hostname, parsed.port)
    elif parsed.scheme == 'socks5':
        proxy = ('socks5', parsed.hostname, parsed.port)
    else:
        print(f"⚠️ 未知代理协议: {parsed.scheme}，忽略")
    if proxy:
        print(f"🔌 使用代理: {PROXY_SERVER}")

# 创建客户端（传入代理）
client = TelegramClient(
    StringSession(session_str),
    API_ID,
    API_HASH,
    proxy=proxy,
    connection=ConnectionTcpAbridged
)

async def main():
    try:
        await client.start()
        print("✅ 登录成功")
        me = await client.get_me()
        print(f"👤 登录用户: {me.first_name} (@{me.username or '无用户名'})")
    except Exception as e:
        print(f"❌ 登录失败: {e}")
        sys.exit(1)

    # 获取机器人
    bot = await client.get_entity("@stormuser_bot")
    print(f"📌 找到机器人: {bot.first_name} (ID: {bot.id})")

    send_time = time.time()
    await client.send_message(bot, "/sign")
    print("📤 已发送 /sign 命令")

    print("⏳ 等待机器人回复...")
    timeout = 15
    reply_received = False
    while time.time() - send_time < timeout:
        messages = await client.get_messages(bot, limit=5)
        for msg in messages:
            if not msg.out and msg.date.timestamp() >= send_time:
                print(f"📩 机器人回复:\n{msg.text}")
                reply_received = True
                break
        if reply_received:
            break
        await asyncio.sleep(1)

    if not reply_received:
        print("⏰ 超时未收到回复，签到可能已成功但未回复")

    await client.disconnect()
    print("🔒 连接已断开")

if __name__ == "__main__":
    asyncio.run(main())

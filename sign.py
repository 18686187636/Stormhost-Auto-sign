#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import asyncio
import time
from urllib.parse import urlparse
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.network.connection.tcpabridged import ConnectionTcpAbridged

API_ID = int(os.environ.get('TG_API_ID', '0').strip())
API_HASH = os.environ.get('TG_API_HASH', '').strip()
SESSION_STRING = os.environ.get('TG_SESSION_STRING', '').strip()
PROXY_SERVER = os.environ.get('PROXY_SERVER', '').strip()

if not all([API_ID, API_HASH, SESSION_STRING]):
    print("❌ 缺少必要的环境变量：请设置 TG_API_ID, TG_API_HASH, TG_SESSION_STRING")
    sys.exit(1)

print(f"API_ID 长度: {len(str(API_ID))}, API_HASH 长度: {len(API_HASH)}")
print(f"SESSION_STRING 长度: {len(SESSION_STRING)} 字符")
if len(SESSION_STRING) < 50:
    print("⚠️ SESSION_STRING 过短，可能无效")
    sys.exit(1)

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

client = TelegramClient(
    StringSession(SESSION_STRING),
    API_ID,
    API_HASH,
    proxy=proxy,
    connection=ConnectionTcpAbridged
)

async def main():
    try:
        await client.connect()
        if not await client.is_user_authorized():
            print("❌ 会话未授权。")
            print("可能原因：")
            print("  1. SESSION_STRING 已过期或无效")
            print("  2. API_ID / API_HASH 与生成时不一致")
            print("  3. 代理未生效，导致无法验证授权")
            sys.exit(1)
        print("✅ 会话授权检查通过")

        await client.start()
        print("✅ 登录成功")
        me = await client.get_me()
        print(f"👤 登录用户: {me.first_name} (@{me.username or '无用户名'})")
    except Exception as e:
        print(f"❌ 登录失败: {e}")
        sys.exit(1)

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

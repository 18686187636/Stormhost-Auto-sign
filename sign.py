#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import asyncio
import time
from telethon import TelegramClient
from telethon.sessions import StringSession

API_ID = int(os.environ.get('TG_API_ID', 0))
API_HASH = os.environ.get('TG_API_HASH', '')
SESSION_STRING = os.environ.get('TG_SESSION_STRING', '')

if not all([API_ID, API_HASH, SESSION_STRING]):
    print("❌ 缺少必要的环境变量，退出。")
    sys.exit(1)

if len(SESSION_STRING) < 50:
    print(f"⚠️ SESSION_STRING 过短（{len(SESSION_STRING)} 字符），可能无效")
    sys.exit(1)

print(f"🔍 SESSION_STRING 长度: {len(SESSION_STRING)} 字符")
print(f"首 5 字符: {SESSION_STRING[:5]}... 尾 5 字符: ...{SESSION_STRING[-5:]}")

client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

async def main():
    try:
        await client.start()
        print("✅ 登录成功")
        me = await client.get_me()
        print(f"👤 登录用户: {me.first_name} (@{me.username or '无用户名'})")
    except Exception as e:
        print(f"❌ 登录失败: {e}")
        sys.exit(1)

    # 获取机器人实体
    bot = await client.get_entity("@stormuser_bot")
    print(f"📌 找到机器人: {bot.first_name} (ID: {bot.id})")

    # 发送签到命令
    send_time = time.time()
    await client.send_message(bot, "/sign")
    print("📤 已发送 /sign 命令")

    # 等待机器人回复（最多 15 秒）
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

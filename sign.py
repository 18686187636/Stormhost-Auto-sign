import os
import sys
import asyncio
import time
from telethon import TelegramClient
from telethon.sessions import StringSession

async def main():
    # 从环境变量读取配置
    api_id_str = os.environ.get("TG_API_ID")
    api_hash = os.environ.get("TG_API_HASH")
    session_str = os.environ.get("TG_SESSION_STRING")

    if not api_id_str or not api_hash or not session_str:
        print("❌ 错误: 请设置环境变量 TG_API_ID, TG_API_HASH, TG_SESSION_STRING")
        sys.exit(1)

    try:
        api_id = int(api_id_str)
    except ValueError:
        print("❌ 错误: TG_API_ID 必须是数字")
        sys.exit(1)

    # 使用字符串会话恢复登录
    client = TelegramClient(StringSession(session_str), api_id, api_hash)

    try:
        await client.start()
        print("✅ 登录成功")

        # 获取目标机器人实体
        bot = await client.get_entity("@stormuser_bot")
        print(f"📌 找到机器人: {bot.first_name} (ID: {bot.id})")

        # 记录发送前的时间戳
        send_time = time.time()

        # 发送签到命令
        await client.send_message(bot, "/sign")
        print("📤 已发送 /sign 命令")

        # 等待机器人回复（最多 15 秒）
        print("⏳ 等待机器人回复...")
        timeout = 15
        reply_received = False

        while time.time() - send_time < timeout:
            # 获取最近的消息（最多 5 条）
            messages = await client.get_messages(bot, limit=5)
            for msg in messages:
                # 判断条件：不是自己发的、时间在发送之后、且不是命令本身（以防万一）
                if not msg.out and msg.date.timestamp() >= send_time:
                    print(f"📩 机器人回复:\n{msg.text}")
                    reply_received = True
                    break
            if reply_received:
                break
            await asyncio.sleep(1)   # 每秒轮询一次

        if not reply_received:
            print("⏰ 超时未收到机器人回复，签到可能已成功但未回复")

    except Exception as e:
        print(f"❌ 发生错误: {e}")
        sys.exit(1)
    finally:
        await client.disconnect()
        print("🔒 连接已断开")

if __name__ == "__main__":
    asyncio.run(main())

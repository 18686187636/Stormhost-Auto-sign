import os
import sys
import asyncio
import time
from telethon import TelegramClient
from telethon.sessions import StringSession

async def main():
    api_id_str = os.environ.get("TG_API_ID")
    api_hash = os.environ.get("TG_API_HASH")
    session_str = os.environ.get("TG_SESSION_STRING")

    if not all([api_id_str, api_hash, session_str]):
        print("❌ 错误: 请设置环境变量 TG_API_ID, TG_API_HASH, TG_SESSION_STRING")
        sys.exit(1)

    try:
        api_id = int(api_id_str)
    except ValueError:
        print("❌ 错误: TG_API_ID 必须是数字")
        sys.exit(1)

    # 打印长度帮助调试（不泄露完整内容）
    print(f"🔍 SESSION_STRING 长度: {len(session_str)} 字符")
    if len(session_str) < 50:
        print("⚠️ SESSION_STRING 过短，可能无效")
        sys.exit(1)

    client = TelegramClient(StringSession(session_str), api_id, api_hash)

    try:
        # 直接调用 start()，它内部会 connect() 并验证授权
        await client.start()
        print("✅ 登录成功")

        # 可选：获取当前用户信息确认
        me = await client.get_me()
        print(f"👤 登录用户: {me.first_name} (@{me.username or '无用户名'})")

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

    except ValueError as e:
        # start() 因需要手机号而失败 -> 会话无效
        print(f"❌ 会话无效或已过期: {e}")
        print("请重新生成 SESSION_STRING 并更新 Secret（注意不要有空格/换行）")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 发生错误: {e}")
        sys.exit(1)
    finally:
        await client.disconnect()
        print("🔒 连接已断开")

if __name__ == "__main__":
    asyncio.run(main())

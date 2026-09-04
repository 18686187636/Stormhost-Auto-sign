```markdown
# Telegram Auto Sign Bot 🤖

通过 GitHub Actions 定时使用你的 Telegram 个人账号向 `@stormuser_bot` 发送 `/sign` 命令，实现每日自动签到。

---

## ✨ 功能特点

- 🔐 使用你的真实 Telegram 账号（非 Bot）完成签到
- ⏰ 每天自动运行（默认北京时间 09:00）
- 📩 捕获并记录机器人的签到回复结果
- 🛠️ 支持手动触发，方便测试和调试
- 🔒 敏感信息通过 GitHub Secrets 加密存储

---

## 📖 工作原理

本项目使用 [Telethon](https://github.com/LonamiWebs/Telethon) 库，基于 Telegram **MTProto 协议**模拟你的个人账号登录，然后向指定的机器人发送私聊消息。

由于 GitHub Actions 运行环境是无状态的，我们需要预先在本地生成一个**会话字符串（StringSession）**，它相当于你的登录凭证，将其存储在 GitHub Secrets 中。每次运行脚本时，通过该字符串恢复会话，无需重复输入验证码。

---

## 🚀 快速开始

### 1. 前置条件

- 一个 Telegram 个人账号
- 你的账号需要已经和 `@stormuser_bot` 建立过对话（即你曾主动向该机器人发送过消息，否则机器人无法回复你）
- GitHub 仓库（公开或私有均可）

### 2. 获取 Telegram API 凭证

访问 [my.telegram.org/apps](https://my.telegram.org/apps)，登录你的账号，创建一个应用（名称随意），获得：

- `api_id`（整数）
- `api_hash`（字符串）

### 3. 生成会话字符串（在本地执行）

在你的电脑上安装 `telethon`：

```bash
pip install telethon
```

创建一个 Python 文件（例如 `generate_session.py`），填入你的 `api_id` 和 `api_hash`：

```python
from telethon import TelegramClient
from telethon.sessions import StringSession
import asyncio

API_ID = 你的api_id        # 替换为你的数字 ID
API_HASH = '你的api_hash'  # 替换为你的字符串

async def main():
    async with TelegramClient(StringSession(), API_ID, API_HASH) as client:
        await client.start()
        print('SESSION_STRING =', client.session.save())

asyncio.run(main())
```

运行该脚本：

```bash
python generate_session.py
```

按照提示输入你的手机号（国际格式，如 `+8613812345678`）、收到的验证码，如果开启了两步验证还需输入密码。登录成功后，会打印出一长串字符串，类似：

```
SESSION_STRING = 1AZX12345...
```

**⚠️ 请妥善保管该字符串，它等同于你的账号密码，切勿公开！**

### 4. 配置 GitHub Secrets

进入你的 GitHub 仓库，点击 `Settings` → `Secrets and variables` → `Actions`，点击 `New repository secret`，添加以下三个密钥：

| Secret 名称 | 值 |
|------------|-----|
| `TG_API_ID` | 你的 `api_id`（纯数字） |
| `TG_API_HASH` | 你的 `api_hash` |
| `TG_SESSION_STRING` | 上一步生成的 `SESSION_STRING` |

### 5. 将脚本文件放入仓库

在你的仓库根目录下创建以下文件：

- `.github/workflows/telegram-sign.yml`（GitHub Actions 工作流）
- `sign.py`（签到脚本）

内容请参考本仓库提供的文件（见下文“文件说明”）。

### 6. 提交并触发

将代码推送到 GitHub 仓库，等待定时任务自动执行，或手动进入仓库的 `Actions` 标签页，选择 `Telegram Auto Sign` 工作流，点击 `Run workflow` 手动触发测试。

---

## 📁 文件说明

### `.github/workflows/telegram-sign.yml`

```yaml
name: Telegram Auto Sign

on:
  schedule:
    - cron: '0 1 * * *'          # 每天 UTC 01:00 = 北京时间 09:00
  workflow_dispatch:             # 允许手动触发

jobs:
  sign:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: pip install telethon
      - name: Run sign-in
        env:
          TG_API_ID: ${{ secrets.TG_API_ID }}
          TG_API_HASH: ${{ secrets.TG_API_HASH }}
          TG_SESSION_STRING: ${{ secrets.TG_SESSION_STRING }}
        run: python sign.py
```

### `sign.py`

完整的签到脚本，功能包括：

- 从环境变量读取凭证并恢复会话
- 向 `@stormuser_bot` 发送 `/sign`
- 等待并捕获机器人的回复（超时 15 秒）
- 打印签到结果

```python
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
        print("❌ 请设置环境变量 TG_API_ID, TG_API_HASH, TG_SESSION_STRING")
        sys.exit(1)

    try:
        api_id = int(api_id_str)
    except ValueError:
        print("❌ TG_API_ID 必须为数字")
        sys.exit(1)

    client = TelegramClient(StringSession(session_str), api_id, api_hash)

    try:
        await client.start()
        print("✅ 登录成功")

        bot = await client.get_entity("@stormuser_bot")
        send_time = time.time()
        await client.send_message(bot, "/sign")
        print("📤 已发送 /sign")

        print("⏳ 等待机器人回复...")
        timeout = 15
        replied = False
        while time.time() - send_time < timeout:
            messages = await client.get_messages(bot, limit=5)
            for msg in messages:
                if not msg.out and msg.date.timestamp() >= send_time:
                    print(f"📩 机器人回复:\n{msg.text}")
                    replied = True
                    break
            if replied:
                break
            await asyncio.sleep(1)

        if not replied:
            print("⏰ 超时未收到回复，签到可能已成功")

    except Exception as e:
        print(f"❌ 错误: {e}")
        sys.exit(1)
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 🧪 本地测试（可选）

你也可以在本地直接运行脚本（需要设置相应的环境变量），以验证会话字符串是否有效：

```bash
export TG_API_ID=你的api_id
export TG_API_HASH=你的api_hash
export TG_SESSION_STRING=你的会话字符串
python sign.py
```

---

## ⚠️ 注意事项

1. **账号安全**  
   - `SESSION_STRING` 相当于你的登录凭证，请务必保密。不要在公开场合（如日志、截图）中暴露它。
   - 如果怀疑会话泄露，可以在 Telegram 设置中终止所有会话，然后重新生成。

2. **会话有效期**  
   - 正常使用下会话长期有效，但如果你在其它设备上主动登出账号、修改密码或 Telegram 强制重新登录，会话会失效，需要重新生成并更新 Secret。

3. **机器人交互**  
   - 你的账号需要已经和 `@stormuser_bot` 有过对话（即你曾主动向它发送过消息），否则机器人可能无法主动向你发送回复。建议在首次使用前手动给该机器人发一条消息（如 `/start`）。

4. **运行频率**  
   - GitHub Actions 免费版有使用限制（每月 2000 分钟），但每天运行一次完全在限制内。

5. **时区**  
   - 工作流中的 `cron` 使用 UTC 时间，示例中 `0 1 * * *` 对应北京时间 09:00。如需调整，请自行修改。

6. **错误处理**  
   - 脚本会捕获异常并退出，同时 GitHub Actions 会标记为失败。你可以查看 Actions 日志定位问题。

---

## 📄 许可证

本项目采用 MIT 许可证，详情请见 [LICENSE](LICENSE) 文件。

---

## 🤝 贡献

欢迎提交 Issue 或 Pull Request 改进此工具。

---

**Happy Signing! 🎉**
```
